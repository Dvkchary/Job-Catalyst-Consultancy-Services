import io
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.auth import User
from app.models.profile import AccountSettings, UserProfile
from app.schemas.profile import (
    AccountSettingsUpdate,
    CertificationSchema,
    EducationSchema,
    ExperienceSchema,
    PreferredSalarySchema,
    SocialLinksSchema,
    UserProfileCreate,
    UserProfileUpdate,
)
from app.services.completion import ProfileCompletionEngine
from app.services.profile import ProfileService
from app.services.settings import SettingsService
from app.services.validation import ValidationService


# ==============================================================================
# 1. Validation Service Tests
# ==============================================================================

def test_validation_service_date_ranges():
    # Valid date formats
    ok, err = ValidationService.validate_date_range("2020-01-01", "2023-12-31")
    assert ok is True
    assert err is None

    # Valid short formats (YYYY-MM)
    ok, err = ValidationService.validate_date_range("2020-01", "2023-12")
    assert ok is True

    # Start date later than end date
    ok, err = ValidationService.validate_date_range("2025-01-01", "2023-12-31")
    assert ok is False
    assert "cannot be later" in err

    # Malformed formats
    ok, err = ValidationService.validate_date_range("invalid-date", None)
    assert ok is False
    assert "Invalid start date format" in err


def test_validation_service_salary_ranges():
    # Valid salary
    ok, err = ValidationService.validate_salary_range(50000, 120000)
    assert ok is True

    # Negative salaries
    ok, err = ValidationService.validate_salary_range(-10, 100)
    assert ok is False
    assert "cannot be negative" in err

    # Min salary exceeding Max salary
    ok, err = ValidationService.validate_salary_range(150000, 100000)
    assert ok is False
    assert "cannot exceed" in err


def test_validation_service_social_urls():
    # Valid LinkedIn
    ok, err = ValidationService.validate_social_url("https://www.linkedin.com/in/john-doe-123/", "linkedin")
    assert ok is True

    # Invalid LinkedIn
    ok, err = ValidationService.validate_social_url("https://linkedin.com/not-a-profile", "linkedin")
    assert ok is False

    # Valid GitHub
    ok, err = ValidationService.validate_social_url("https://github.com/torvalds", "github")
    assert ok is True

    # Valid Portfolio
    ok, err = ValidationService.validate_social_url("https://myportfolio.io/projects", "portfolio")
    assert ok is True


def test_validation_service_avatar_files():
    # Valid JPG image
    ok, err = ValidationService.validate_avatar_file("me.jpg", "image/jpeg", 2 * 1024 * 1024)
    assert ok is True

    # Size limit exceeded (6MB)
    ok, err = ValidationService.validate_avatar_file("photo.png", "image/png", 6 * 1024 * 1024)
    assert ok is False
    assert "exceeds" in err

    # Invalid mime format
    ok, err = ValidationService.validate_avatar_file("file.pdf", "application/pdf", 100 * 1024)
    assert ok is False
    assert "Unsupported media format" in err

    # Malicious double extension defense
    ok, err = ValidationService.validate_avatar_file("image.jpg.exe", "image/jpeg", 100 * 1024)
    assert ok is False
    assert "extension" in err or "structure" in err


# ==============================================================================
# 2. Profile Completion Engine Tests
# ==============================================================================

def test_profile_completion_percentage_calculation():
    # Create an empty mock profile
    empty_profile = UserProfile(
        first_name=None,
        last_name=None,
        phone_number=None,
        headline=None,
        bio=None,
        skills=[],
        education=[],
        experience=[],
        certifications=[],
        social_links={},
        preferred_roles=[],
        preferred_job_locations=[],
        preferred_salary={}
    )

    status = ProfileCompletionEngine.evaluate(empty_profile)
    assert status.completion_percentage == 0
    assert len(status.missing_fields) > 0

    # Populated Profile
    fully_populated_profile = UserProfile(
        first_name="Jane",
        last_name="Doe",
        phone_number="12345678",
        headline="Software Craftsman",
        bio="Passionate engineer developing cloud backends.",
        skills=["Python", "FastAPI", "PostgreSQL"],
        education=[{"school": "MIT", "degree": "BS", "field_of_study": "CS", "start_date": "2016", "end_date": "2020"}],
        experience=[{"company": "Google", "title": "SWE", "start_date": "2021-01-01", "current": True}],
        certifications=[{"name": "AWS Pro", "issuer": "Amazon"}],
        social_links={"linkedin": "https://www.linkedin.com/in/janedoe/"},
        preferred_roles=["Senior Backend Engineer"],
        preferred_job_locations=["Remote", "Seattle"],
        preferred_salary={"min_salary": 140000, "max_salary": 180000}
    )

    full_status = ProfileCompletionEngine.evaluate(fully_populated_profile)
    # Check that score reaches 100%
    assert full_status.completion_percentage == 100
    assert len(full_status.missing_fields) == 0


# ==============================================================================
# 3. Profile & Settings Services Integration Tests (Mocks)
# ==============================================================================

@pytest.mark.asyncio
async def test_profile_service_creation_and_business_rules():
    mock_repo = MagicMock()
    mock_repo.get_by_user_id = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock(return_value=UserProfile(id=uuid.uuid4()))

    profile_svc = ProfileService(profile_repo=mock_repo)
    user_id = uuid.uuid4()

    # Valid creation payload
    create_payload = UserProfileCreate(
        first_name="Alice",
        last_name="Smith",
        headline="Senior DevOps Engineer",
        bio="Designing robust CI/CD infrastructures.",
        skills=["Terraform", "Docker", "AWS"],
        education=[
            EducationSchema(school="Stanford", degree="MS", field_of_study="CS", start_date="2018", end_date="2020")
        ],
        experience=[
            ExperienceSchema(company="Meta", title="DevOps Eng", start_date="2021-01-01", current=True)
        ],
        social_links=SocialLinksSchema(github="https://github.com/alice")
    )

    profile = await profile_svc.create_profile(user_id=user_id, payload=create_payload)
    assert profile is not None
    mock_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_profile_service_invalid_experience_date_raises():
    mock_repo = MagicMock()
    mock_repo.get_by_user_id = AsyncMock(return_value=None)
    profile_svc = ProfileService(profile_repo=mock_repo)

    # Invalid chronological range: start date occurs after end date
    invalid_payload = UserProfileCreate(
        first_name="Alice",
        last_name="Smith",
        experience=[
            ExperienceSchema(company="Meta", title="DevOps", start_date="2023-01-01", end_date="2021-12-31")
        ]
    )

    with pytest.raises(ValueError, match="Experience Validation"):
        await profile_svc.create_profile(user_id=uuid.uuid4(), payload=invalid_payload)


@pytest.mark.asyncio
async def test_settings_service_lazy_initialization():
    mock_repo = MagicMock()
    mock_repo.get_by_user_id = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock(side_effect=lambda payload: AccountSettings(**payload))

    settings_svc = SettingsService(settings_repo=mock_repo)
    user_id = uuid.uuid4()

    # Call get_by_user_id, which should trigger lazy-creation of defaults
    settings = await settings_svc.get_by_user_id(user_id)
    assert settings is not None
    assert settings.user_id == user_id
    assert settings.theme == "light"
    assert settings.language == "en"
    
    mock_repo.create.assert_called_once()
