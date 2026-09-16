import io
import json
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.auth import User
from app.models.resume import Resume, ResumeTemplate, ResumeVersion
from app.schemas.resume import ResumeCreate, ResumeUpdate, ResumeTemplateCreate
from app.services.resume import ResumeService
from app.services.resume_template import ResumeTemplateService
from app.services.resume_upload import ResumeUploadService
from app.services.resume_parser import ResumeParserService
from app.services.resume_export import ResumeExportService


# ==============================================================================
# 1. Resume Upload Service Tests
# ==============================================================================

def test_resume_upload_validation_logic():
    # Valid PDF
    ok, err = ResumeUploadService.validate_file("my_cv.pdf", "application/pdf", 1 * 1024 * 1024)
    assert ok is True
    assert err is None

    # Valid Word
    ok, err = ResumeUploadService.validate_file("resume.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 2 * 1024 * 1024)
    assert ok is True

    # Size limit exceeded (6MB)
    ok, err = ResumeUploadService.validate_file("big_portfolio.pdf", "application/pdf", 6 * 1024 * 1024)
    assert ok is False
    assert "exceeds" in err

    # Unsupported format
    ok, err = ResumeUploadService.validate_file("avatar.png", "image/png", 500 * 1024)
    assert ok is False
    assert "Unsupported file extension" in err

    # Malicious dual extension defense
    ok, err = ResumeUploadService.validate_file("resume.exe.pdf", "application/pdf", 100 * 1024)
    assert ok is False
    assert "dual-extension" in err or "structure" in err


@pytest.mark.asyncio
async def test_resume_upload_virus_scanner_hook():
    # Clean check
    clean_bytes = b"This is a standard PDF resume stream content."
    is_clean = await ResumeUploadService.run_virus_scan(clean_bytes, "cv.pdf")
    assert is_clean is True

    # Dangerous block string check (EICAR)
    eicar_sig = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    is_clean = await ResumeUploadService.run_virus_scan(eicar_sig, "eicar.pdf")
    assert is_clean is False


def test_resume_metadata_extraction():
    dummy_text = "Alex Johnson \n Email: alex@test.com \n Phone: 555-0199 \n Tech: Python, FastAPI, Docker."
    meta = ResumeUploadService.extract_metadata("johnson_cv.txt", "text/plain", dummy_text.encode("utf-8"))
    assert meta["filename"] == "johnson_cv.txt"
    assert meta["file_size_bytes"] == len(dummy_text)
    assert meta["estimated_word_count"] > 0


# ==============================================================================
# 2. Heuristic Resume Parser Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_resume_parser_heuristic_extraction():
    plain_text_resume = """
    Jane Miller
    jane.miller@example.com
    (555) 123-4567
    linkedin.com/in/janemiller
    
    EDUCATION
    Stanford University - Bachelor of Science in Computer Science, 2018 - 2022
    
    WORK EXPERIENCE
    Google
    Software Engineer, 2022 to Present
    Developed highly scalable backends using Python, FastAPI, and PostgreSQL.
    
    SKILLS
    Python, FastAPI, AWS, Docker, React, TypeScript
    """
    
    parsed = await ResumeParserService.parse_resume_content(
        plain_text_resume.encode("utf-8"),
        "miller_cv.txt",
        "text/plain"
    )
    
    assert parsed.first_name == "Jane"
    assert parsed.last_name == "Miller"
    assert parsed.email == "jane.miller@example.com"
    assert parsed.phone == "(555) 123-4567"
    assert "https://linkedin.com/in/janemiller" in parsed.linkedin
    assert "Python" in parsed.skills
    assert "FastAPI" in parsed.skills
    assert len(parsed.education) > 0
    assert "Stanford University" in parsed.education[0].school
    assert len(parsed.experience) > 0
    assert parsed.experience[0].company == "Google"


@pytest.mark.asyncio
async def test_resume_parser_fallback_on_unreadable_file():
    # Empty binary stream simulation
    parsed = await ResumeParserService.parse_resume_content(
        b"\x00\x01\x02\x03",
        "scanned_image.pdf",
        "application/pdf"
    )
    assert parsed.first_name == "Alex"
    assert parsed.email == "alex.johnson@jobcatalyst.ai"
    assert "Python" in parsed.skills


# ==============================================================================
# 3. Resume Template Service Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_resume_template_seeding_and_retrieval():
    mock_repo = MagicMock()
    mock_repo.get_by_code = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock(side_effect=lambda t_dict: ResumeTemplate(**t_dict))
    mock_repo.get_multi = AsyncMock(return_value=[])

    svc = ResumeTemplateService(template_repo=mock_repo)

    # 1. Seed defaults
    seeded = await svc.seed_default_templates()
    assert len(seeded) > 0
    assert seeded[0].code == "PROFESSIONAL"

    # 2. List templates
    templates = await svc.list_templates()
    # List was empty, so it lazy seeded
    assert len(templates) > 0


# ==============================================================================
# 4. Resume Export Service Tests
# ==============================================================================

def test_resume_export_formats():
    content = {
        "personal_info": {
            "first_name": "Bob",
            "last_name": "Builder",
            "email": "bob@build.com",
            "job_title": "Senior Solutions Builder",
            "summary": "Building resilient systems since decades."
        },
        "skills": [{"name": "SQLAlchemy", "level": "EXPERT"}],
        "experience": [
            {
                "company": "Construction Corp",
                "title": "Architect",
                "start_date": "2020-01-01",
                "description": "Led full-stack building blocks construction."
            }
        ]
    }

    # JSON export
    json_bytes = ResumeExportService.export_as_json("Bob Builder CV", content)
    decoded_json = json.loads(json_bytes.decode("utf-8"))
    assert decoded_json["resume_title"] == "Bob Builder CV"
    assert decoded_json["content"]["personal_info"]["first_name"] == "Bob"

    # Plain text / Print export
    print_str = ResumeExportService.export_as_print("Bob Builder CV", content)
    assert "BOB BUILDER" in print_str
    assert "Senior Solutions Builder" in print_str
    assert "SQLAlchemy" in print_str

    # PDF Simulated export
    pdf_bytes = ResumeExportService.export_as_pdf("Bob Builder CV", content)
    assert pdf_bytes.startswith(b"%PDF")

    # DOCX Simulated export
    docx_bytes = ResumeExportService.export_as_docx("Bob Builder CV", content)
    assert docx_bytes.startswith(b"PK")


# ==============================================================================
# 5. Core Resume Service Integration Tests (Mocks)
# ==============================================================================

@pytest.mark.asyncio
async def test_resume_crud_and_primary_toggles():
    mock_resume_repo = MagicMock()
    mock_template_repo = MagicMock()
    mock_version_repo = MagicMock()

    # Mocks setup
    mock_resume_repo.get_by_user_id = AsyncMock(return_value=[])
    mock_resume_repo.create = AsyncMock(side_effect=lambda payload: Resume(id=uuid.uuid4(), **payload))
    mock_template_repo.get_by_code = AsyncMock(return_value=None)
    mock_version_repo.create = AsyncMock(return_value=None)

    svc = ResumeService(
        resume_repo=mock_resume_repo,
        template_repo=mock_template_repo,
        version_repo=mock_version_repo
    )

    user_id = uuid.uuid4()
    create_payload = ResumeCreate(
        title="Software Engineer CV",
        description="Core technical summary",
        template_code="SOFTWARE_ENGINEER"
    )

    # Create Resume
    resume = await svc.create_resume(user_id=user_id, payload=create_payload)
    assert resume is not None
    assert resume.title == "Software Engineer CV"
    # First resume auto sets as primary
    assert resume.is_primary is True
    assert resume.resume_version == 1

    # Verify version snapshot v1 was generated
    mock_version_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_resume_duplication_mechanics():
    mock_resume_repo = MagicMock()
    mock_template_repo = MagicMock()
    mock_version_repo = MagicMock()

    source_id = uuid.uuid4()
    source_resume = Resume(
        id=source_id,
        user_id=uuid.uuid4(),
        title="Original Professional Resume",
        description="Standard template",
        content={"skills": [{"name": "Python"}]}
    )

    mock_resume_repo.get = AsyncMock(return_value=source_resume)
    mock_resume_repo.get_by_user_id = AsyncMock(return_value=[source_resume])  # Not empty, so copy won't auto-be primary
    mock_resume_repo.create = AsyncMock(side_effect=lambda r_dict: Resume(id=uuid.uuid4(), **r_dict))
    mock_template_repo.get_by_code = AsyncMock(return_value=None)
    mock_version_repo.create = AsyncMock(return_value=None)

    svc = ResumeService(
        resume_repo=mock_resume_repo,
        template_repo=mock_template_repo,
        version_repo=mock_version_repo
    )

    # Duplicate resume
    duplicated = await svc.duplicate_resume(user_id=source_resume.user_id, resume_id=source_id)
    assert duplicated is not None
    assert duplicated.title == "Copy of Original Professional Resume"
    assert duplicated.is_primary is False
    assert duplicated.content["skills"][0]["name"] == "Python"


@pytest.mark.asyncio
async def test_resume_version_timeline_restoration_and_diff():
    mock_resume_repo = MagicMock()
    mock_template_repo = MagicMock()
    mock_version_repo = MagicMock()

    resume_id = uuid.uuid4()
    user_id = uuid.uuid4()
    active_resume = Resume(
        id=resume_id,
        user_id=user_id,
        title="Dynamic CV",
        resume_version=2,
        content={"skills": [{"name": "Python"}, {"name": "FastAPI"}]}
    )

    historic_snapshot = ResumeVersion(
        id=uuid.uuid4(),
        resume_id=resume_id,
        version_number=1,
        title="Initial draft",
        content_snapshot={"skills": [{"name": "Python"}]},
        metadata_snapshot={"title": "Dynamic CV"}
    )

    mock_resume_repo.get = AsyncMock(return_value=active_resume)
    mock_version_repo.get_version = AsyncMock(return_value=historic_snapshot)
    mock_version_repo.create = AsyncMock(return_value=None)
    mock_resume_repo.update = AsyncMock(side_effect=lambda db_obj, obj_in: Resume(id=resume_id, **obj_in))

    svc = ResumeService(
        resume_repo=mock_resume_repo,
        template_repo=mock_template_repo,
        version_repo=mock_version_repo
    )

    # Restore version 1
    restored = await svc.restore_version(user_id=user_id, resume_id=resume_id, version_number=1)
    assert restored is not None
    assert restored.resume_version == 3  # increments current counter (2 + 1)
    # Content has gone back to snapshot content
    assert restored.content == historic_snapshot.content_snapshot

    # Compare versions
    mock_version_repo.get_version = AsyncMock(side_effect=lambda r_id, v_num: historic_snapshot if v_num == 1 else ResumeVersion(
        id=uuid.uuid4(),
        resume_id=resume_id,
        version_number=2,
        content_snapshot=active_resume.content,
        metadata_snapshot={"title": "Dynamic CV"}
    ))

    comparison = await svc.compare_versions(user_id=user_id, resume_id=resume_id, version_a=1, version_b=2)
    assert comparison.version_a == 1
    assert comparison.version_b == 2
    # Skill was added in version 2
    assert comparison.diff["skills_count_diff"] == 1
    assert comparison.diff["skills_modified"] is True
