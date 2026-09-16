import io
import logging
import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import Response, StreamingResponse

from app.core.dependencies import (
    get_current_active_user,
    get_resume_service,
    get_resume_template_service,
)
from app.models.auth import User
from app.schemas.resume import (
    ParsedResumeResponse,
    ResumeCreate,
    ResumeOut,
    ResumeTemplateOut,
    ResumeUpdate,
    ResumeVersionOut,
    ResumeCompareResponse,
)
from app.services.resume import ResumeService
from app.services.resume_template import ResumeTemplateService
from app.services.resume_upload import ResumeUploadService
from app.services.resume_parser import ResumeParserService
from app.services.resume_export import ResumeExportService

logger = logging.getLogger("app.api.resume")

router = APIRouter(prefix="/resumes", tags=["Resume Engine"])


# ==============================================================================
# 1. Resume Core CRUD Endpoints
# ==============================================================================

@router.post("", response_model=ResumeOut, status_code=status.HTTP_201_CREATED)
async def create_resume(
    payload: ResumeCreate,
    current_user: User = Depends(get_current_active_user),
    resume_svc: ResumeService = Depends(get_resume_service),
) -> Any:
    """
    Creates a new Resume record under the logged-in user account.
    Auto-seeds starting snapshot v1.
    """
    try:
        return await resume_svc.create_resume(user_id=current_user.id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("", response_model=List[ResumeOut])
async def list_resumes(
    current_user: User = Depends(get_current_active_user),
    resume_svc: ResumeService = Depends(get_resume_service),
) -> Any:
    """
    Lists all active (non-deleted) resumes owned by the current user.
    """
    return await resume_svc.list_user_resumes(user_id=current_user.id)


@router.get("/{resume_id}", response_model=ResumeOut)
async def get_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    resume_svc: ResumeService = Depends(get_resume_service),
) -> Any:
    """
    Retrieves the complete details of a specific resume.
    """
    resume = await resume_svc.get_by_id(resume_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to requested resource.")
    return resume


@router.put("/{resume_id}", response_model=ResumeOut)
async def update_resume(
    resume_id: uuid.UUID,
    payload: ResumeUpdate,
    current_user: User = Depends(get_current_active_user),
    resume_svc: ResumeService = Depends(get_resume_service),
) -> Any:
    """
    Mutates sections on an existing resume. Auto-saves next version snapshot.
    """
    try:
        return await resume_svc.update_resume(user_id=current_user.id, resume_id=resume_id, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, response_model=None)
async def delete_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    resume_svc: ResumeService = Depends(get_resume_service),
) -> None:
    """
    Soft-deletes an active resume record.
    """
    try:
        success = await resume_svc.delete_resume(user_id=current_user.id, resume_id=resume_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/{resume_id}/primary", response_model=ResumeOut)
async def set_primary_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    resume_svc: ResumeService = Depends(get_resume_service),
) -> Any:
    """
    Sets the target resume as primary and automatically unsets other resumes.
    """
    try:
        return await resume_svc.set_primary_resume(user_id=current_user.id, resume_id=resume_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/{resume_id}/duplicate", response_model=ResumeOut)
async def duplicate_resume(
    resume_id: uuid.UUID,
    title: Optional[str] = Query(None, description="Optional custom title for the duplicate copy"),
    current_user: User = Depends(get_current_active_user),
    resume_svc: ResumeService = Depends(get_resume_service),
) -> Any:
    """
    Creates a copy duplicate of an existing resume under the user account.
    """
    try:
        return await resume_svc.duplicate_resume(user_id=current_user.id, resume_id=resume_id, custom_title=title)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


# ==============================================================================
# 2. Template Endpoints
# ==============================================================================

@router.get("/templates", response_model=List[ResumeTemplateOut])
async def list_templates(
    template_svc: ResumeTemplateService = Depends(get_resume_template_service),
) -> Any:
    """
    Lists all available professional resume templates and layout styles.
    """
    return await template_svc.list_templates()


# ==============================================================================
# 3. Document Processing (Upload & Parse) Endpoints
# ==============================================================================

@router.post("/upload")
async def upload_resume_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Saves a resume document file, validating size and performing threat security scans.
    Returns extracted document metadata.
    """
    content = await file.read()
    byte_size = len(content)

    # 1. Validation
    is_valid, err_msg = ResumeUploadService.validate_file(file.filename, file.content_type, byte_size)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    # 2. Anti-Virus Scan
    is_clean = await ResumeUploadService.run_virus_scan(content, file.filename)
    if not is_clean:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Security Threat Detected. Upload rejected by safety scans."
        )

    # 3. Harvest metadata
    metadata = ResumeUploadService.extract_metadata(file.filename, file.content_type, content)
    return {
        "status": "success",
        "message": f"Document '{file.filename}' processed successfully.",
        "metadata": metadata
    }


@router.post("/parse", response_model=ParsedResumeResponse)
async def parse_resume_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Extracts core contact details, chronological events, and skill lists
    heuristically from PDF, DOCX, or Plain Text document files.
    """
    content = await file.read()
    byte_size = len(content)

    # Validate
    is_valid, err_msg = ResumeUploadService.validate_file(file.filename, file.content_type, byte_size)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    # Threats check
    is_clean = await ResumeUploadService.run_virus_scan(content, file.filename)
    if not is_clean:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Security Threat Detected. Upload rejected by safety scans."
        )

    # Run parser
    parsed_response = await ResumeParserService.parse_resume_content(
        content,
        file.filename,
        file.content_type
    )
    return parsed_response


# ==============================================================================
# 4. Exports & Downloads Endpoints
# ==============================================================================

@router.get("/{resume_id}/export")
async def export_resume_document(
    resume_id: uuid.UUID,
    format: str = Query("json", description="Export format: json, txt, pdf, docx, print"),
    current_user: User = Depends(get_current_active_user),
    resume_svc: ResumeService = Depends(get_resume_service)
) -> Any:
    """
    Renders and exports the resume into standard formats (JSON, TXT, PDF, DOCX, print).
    Returns file streams or raw text.
    """
    resume = await resume_svc.get_by_id(resume_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to requested resource.")

    format_lower = format.lower()
    content = resume.content or {}

    if format_lower == "json":
        json_bytes = ResumeExportService.export_as_json(resume.title, content)
        return StreamingResponse(
            io.BytesIO(json_bytes),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={resume.title.replace(' ', '_')}.json"}
        )

    elif format_lower in ["txt", "print"]:
        print_text = ResumeExportService.export_as_print(resume.title, content)
        return Response(content=print_text, media_type="text/plain")

    elif format_lower == "pdf":
        pdf_bytes = ResumeExportService.export_as_pdf(resume.title, content)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={resume.title.replace(' ', '_')}.pdf"}
        )

    elif format_lower == "docx":
        docx_bytes = ResumeExportService.export_as_docx(resume.title, content)
        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={resume.title.replace(' ', '_')}.docx"}
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format '{format}'. Supported: json, txt, pdf, docx, print"
        )


# ==============================================================================
# 5. Version Snapshot History Endpoints
# ==============================================================================

@router.get("/{resume_id}/versions", response_model=List[ResumeVersionOut])
async def list_resume_versions(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    resume_svc: ResumeService = Depends(get_resume_service)
) -> Any:
    """
    Lists the complete historical snapshot timeline of a specific resume.
    """
    try:
        return await resume_svc.list_versions(user_id=current_user.id, resume_id=resume_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/{resume_id}/versions/{version_number}/restore", response_model=ResumeOut)
async def restore_resume_version(
    resume_id: uuid.UUID,
    version_number: int,
    current_user: User = Depends(get_current_active_user),
    resume_svc: ResumeService = Depends(get_resume_service)
) -> Any:
    """
    Restores resume content to match a specific historic snapshot.
    Saves a new restored snapshot iteration on the timeline.
    """
    try:
        return await resume_svc.restore_version(
            user_id=current_user.id,
            resume_id=resume_id,
            version_number=version_number
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{resume_id}/versions/compare", response_model=ResumeCompareResponse)
async def compare_resume_versions(
    resume_id: uuid.UUID,
    version_a: int = Query(..., description="First version number to compare"),
    version_b: int = Query(..., description="Second version number to compare"),
    current_user: User = Depends(get_current_active_user),
    resume_svc: ResumeService = Depends(get_resume_service)
) -> Any:
    """
    Compares two historic version snapshots of a resume, detailing structural edits.
    """
    try:
        return await resume_svc.compare_versions(
            user_id=current_user.id,
            resume_id=resume_id,
            version_a=version_a,
            version_b=version_b
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
