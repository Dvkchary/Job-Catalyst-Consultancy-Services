import uuid
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from app.db.resume_repositories import ResumeRepository, ResumeTemplateRepository, ResumeVersionRepository
from app.models.resume import Resume, ResumeTemplate, ResumeVersion
from app.schemas.resume import ResumeCreate, ResumeUpdate, ResumeCompareResponse, ResumeContentSchema
from app.utils.datetime_utils import get_utc_now

logger = logging.getLogger("app.services.resume")


class ResumeService:
    """
    Core Resume Engine orchestrating CRUD operations, template binds,
    primary selection triggers, clean duplications, snapshot history,
    and historical diff generation.
    """

    def __init__(
        self,
        resume_repo: ResumeRepository,
        template_repo: ResumeTemplateRepository,
        version_repo: ResumeVersionRepository
    ) -> None:
        self.resume_repo = resume_repo
        self.template_repo = template_repo
        self.version_repo = version_repo

    async def get_by_id(self, resume_id: uuid.UUID) -> Optional[Resume]:
        """
        Retrieves a resume by its ID.
        """
        return await self.resume_repo.get(resume_id)

    async def list_user_resumes(self, user_id: uuid.UUID) -> List[Resume]:
        """
        Lists all active (non-soft-deleted) resumes for a user.
        """
        return await self.resume_repo.get_by_user_id(user_id)

    async def create_resume(self, user_id: uuid.UUID, payload: ResumeCreate) -> Resume:
        """
        Initializes and creates a new Resume.
        Sets default template association if specified, and sets up
        the initial section structures.
        """
        obj_data = payload.model_dump()
        obj_data["user_id"] = user_id
        obj_data["status"] = "DRAFT"
        obj_data["resume_version"] = 1

        # Check if first resume and make it primary automatically
        existing_resumes = await self.resume_repo.get_by_user_id(user_id)
        if not existing_resumes:
            obj_data["is_primary"] = True
        else:
            obj_data["is_primary"] = obj_data.get("is_primary", False)

        # Handle template matching
        template_id = None
        if payload.template_code:
            template = await self.template_repo.get_by_code(payload.template_code)
            if template:
                template_id = template.id
        obj_data["template_id"] = template_id

        # Coerce Pydantic subschemas to dictionary structures
        if "content" in obj_data and obj_data["content"] is not None:
            if hasattr(obj_data["content"], "model_dump"):
                obj_data["content"] = obj_data["content"].model_dump()

        resume = await self.resume_repo.create(obj_data)

        # Create initial Version Snapshot (v1)
        await self.create_version_snapshot(
            resume_id=resume.id,
            version_number=1,
            title="Initial Draft (v1)",
            description="System generated starting point snapshot.",
            content=resume.content,
            metadata={
                "template_code": resume.template_code,
                "language": resume.language,
                "visibility": resume.visibility,
                "title": resume.title,
                "description": resume.description
            }
        )

        return resume

    async def update_resume(self, user_id: uuid.UUID, resume_id: uuid.UUID, payload: ResumeUpdate) -> Resume:
        """
        Updates an existing resume.
        Automatically increments the resume_version tag and saves a historical snapshot.
        """
        resume = await self.resume_repo.get(resume_id)
        if not resume:
            raise ValueError("Resume not found.")
        if resume.user_id != user_id:
            raise ValueError("Unauthorized operation boundary. You do not own this resume.")

        update_data = payload.model_dump(exclude_unset=True)

        # If primary is being set, handle unsetting other primary records
        if update_data.get("is_primary") is True:
            await self.resume_repo.set_primary(user_id, resume_id)
            # Re-fetch updated object
            resume = await self.resume_repo.get(resume_id)

        # Coerce nested content to raw dict
        if "content" in update_data and update_data["content"] is not None:
            if hasattr(update_data["content"], "model_dump"):
                update_data["content"] = update_data["content"].model_dump()

        # Handle template updates
        if "template_code" in update_data and update_data["template_code"] is not None:
            template = await self.template_repo.get_by_code(update_data["template_code"])
            if template:
                update_data["template_id"] = template.id
            else:
                update_data["template_id"] = None

        # Auto increment version counts
        next_version = resume.resume_version + 1
        update_data["resume_version"] = next_version

        # Update core entity
        updated_resume = await self.resume_repo.update(db_obj=resume, obj_in=update_data)

        # Build Named Version snapshot title
        title_tag = payload.title or updated_resume.title
        snap_title = f"Auto snapshot - version {next_version}"

        # Write snapshot to version repository
        await self.create_version_snapshot(
            resume_id=updated_resume.id,
            version_number=next_version,
            title=snap_title,
            description=f"Snapshot generated automatically upon update sequence.",
            content=updated_resume.content,
            metadata={
                "template_code": updated_resume.template_code,
                "language": updated_resume.language,
                "visibility": updated_resume.visibility,
                "title": updated_resume.title,
                "description": updated_resume.description
            }
        )

        return updated_resume

    async def delete_resume(self, user_id: uuid.UUID, resume_id: uuid.UUID) -> bool:
        """
        Soft-deletes user resume record.
        """
        resume = await self.resume_repo.get(resume_id)
        if not resume:
            return False
        if resume.user_id != user_id:
            raise ValueError("Unauthorized operation boundary. You do not own this resume.")
        return await self.resume_repo.delete(resume_id, soft=True)

    async def set_primary_resume(self, user_id: uuid.UUID, resume_id: uuid.UUID) -> Resume:
        """
        Triggers primary toggle switches. Unsets previous primary, sets new target primary.
        """
        resume = await self.resume_repo.get(resume_id)
        if not resume:
            raise ValueError("Resume not found.")
        if resume.user_id != user_id:
            raise ValueError("Unauthorized operation boundary. You do not own this resume.")

        updated = await self.resume_repo.set_primary(user_id, resume_id)
        return updated

    async def duplicate_resume(self, user_id: uuid.UUID, resume_id: uuid.UUID, custom_title: Optional[str] = None) -> Resume:
        """
        Duplicates an existing resume. Copies all sections and sets appropriate default
        starting tags (DRAFT, not primary, version v1).
        """
        source = await self.resume_repo.get(resume_id)
        if not source:
            raise ValueError("Source resume not found.")
        if source.user_id != user_id:
            raise ValueError("Unauthorized. You do not own this resume.")

        # Build duplicate payload
        dup_title = custom_title or f"Copy of {source.title}"
        dup_payload = ResumeCreate(
            title=dup_title,
            description=source.description,
            template_code=source.template_code,
            language=source.language or "en",
            visibility="PRIVATE",
            content=source.content  # Deep copy structured dict content
        )

        # Create new resume sequence
        new_resume = await self.create_resume(user_id=user_id, payload=dup_payload)
        return new_resume

    # ==============================================================================
    # Resume Version Snapshots & Comparison
    # ==============================================================================

    async def create_version_snapshot(
        self,
        resume_id: uuid.UUID,
        version_number: int,
        title: str,
        description: Optional[str],
        content: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> ResumeVersion:
        """
        Directly saves a historical snapshot of the resume content and its metadata.
        """
        snapshot_data = {
            "resume_id": resume_id,
            "version_number": version_number,
            "title": title,
            "description": description,
            "content_snapshot": content,
            "metadata_snapshot": metadata
        }
        return await self.version_repo.create(snapshot_data)

    async def list_versions(self, user_id: uuid.UUID, resume_id: uuid.UUID) -> List[ResumeVersion]:
        """
        Retrieves all historic snapshots associated with a resume.
        """
        resume = await self.resume_repo.get(resume_id)
        if not resume:
            raise ValueError("Resume not found.")
        if resume.user_id != user_id:
            raise ValueError("Unauthorized. You do not own this resume.")
        return await self.version_repo.get_by_resume_id(resume_id)

    async def restore_version(self, user_id: uuid.UUID, resume_id: uuid.UUID, version_number: int) -> Resume:
        """
        Restores a resume's content state back to a historical version.
        Increments the resume_version and saves a new restored snapshot to the timeline.
        """
        resume = await self.resume_repo.get(resume_id)
        if not resume:
            raise ValueError("Resume not found.")
        if resume.user_id != user_id:
            raise ValueError("Unauthorized. You do not own this resume.")

        target_version = await self.version_repo.get_version(resume_id, version_number)
        if not target_version:
            raise ValueError(f"Version snapshot #{version_number} does not exist.")

        # Save updates based on restored snapshot
        next_ver = resume.resume_version + 1
        update_data = {
            "content": target_version.content_snapshot,
            "resume_version": next_ver,
            # Restore optional metadata tags
            "title": target_version.metadata_snapshot.get("title", resume.title),
            "description": target_version.metadata_snapshot.get("description", resume.description),
            "template_code": target_version.metadata_snapshot.get("template_code", resume.template_code),
            "language": target_version.metadata_snapshot.get("language", resume.language),
            "visibility": target_version.metadata_snapshot.get("visibility", resume.visibility),
        }

        # Handle template ID restore
        t_code = update_data["template_code"]
        if t_code:
            template = await self.template_repo.get_by_code(t_code)
            if template:
                update_data["template_id"] = template.id

        restored_resume = await self.resume_repo.update(db_obj=resume, obj_in=update_data)

        # Create new timeline snapshot reflecting the restore action
        await self.create_version_snapshot(
            resume_id=restored_resume.id,
            version_number=next_ver,
            title=f"Restored from version {version_number}",
            description=f"Automated roll-back trigger from version #{version_number} state.",
            content=restored_resume.content,
            metadata=target_version.metadata_snapshot
        )

        return restored_resume

    async def compare_versions(
        self,
        user_id: uuid.UUID,
        resume_id: uuid.UUID,
        version_a: int,
        version_b: int
    ) -> ResumeCompareResponse:
        """
        Compares two resume versions and returns a detailed difference diff dictionary.
        This provides clear insights into skill adjustments, text modifications, and education updates.
        """
        resume = await self.resume_repo.get(resume_id)
        if not resume:
            raise ValueError("Resume not found.")
        if resume.user_id != user_id:
            raise ValueError("Unauthorized. You do not own this resume.")

        v_a = await self.version_repo.get_version(resume_id, version_a)
        v_b = await self.version_repo.get_version(resume_id, version_b)

        if not v_a or not v_b:
            raise ValueError("One or both target version snapshots do not exist.")

        # Compute semantic/metric differences between snapshots
        c_a = v_a.content_snapshot or {}
        c_b = v_b.content_snapshot or {}

        diff = {}
        # Simple string compare checks on titles and key summary paragraphs
        p_a = c_a.get("personal_info") or {}
        p_b = c_b.get("personal_info") or {}
        
        diff["title_changed"] = v_a.metadata_snapshot.get("title") != v_b.metadata_snapshot.get("title")
        diff["summary_changed"] = p_a.get("summary") != p_b.get("summary")

        # Compare lists lengths or elements
        for category in ["skills", "experience", "education", "projects"]:
            list_a = c_a.get(category) or []
            list_b = c_b.get(category) or []
            
            diff[f"{category}_count_diff"] = len(list_b) - len(list_a)
            diff[f"{category}_modified"] = list_a != list_b

        return ResumeCompareResponse(
            version_a=version_a,
            version_b=version_b,
            diff=diff
        )
