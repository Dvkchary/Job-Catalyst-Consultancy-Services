import logging
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.resume_repositories import ResumeTemplateRepository
from app.models.resume import ResumeTemplate
from app.schemas.resume import ResumeTemplateCreate

logger = logging.getLogger("app.services.resume_template")


class ResumeTemplateService:
    """
    Template Management Service.
    Seeds, retrieves, and configures styling/layout schemas for Resume rendering.
    """

    DEFAULT_TEMPLATES = [
        {
            "name": "Professional Standard",
            "code": "PROFESSIONAL",
            "description": "Clean, traditional, and time-tested. Ideal for finance, legal, and standard corporate fields.",
            "category": "Corporate",
            "layout_config": {
                "font_family": "Georgia",
                "color_primary": "#1A365D",
                "color_text": "#2D3748",
                "spacing": "comfortable",
                "show_avatars": False,
                "section_order": ["personal_info", "experience", "education", "skills", "certifications"]
            }
        },
        {
            "name": "Modern Creative",
            "code": "MODERN",
            "description": "High-impact visual elements with subtle color offsets. Excellent for marketing, tech, and designers.",
            "category": "Creative",
            "layout_config": {
                "font_family": "Inter",
                "color_primary": "#0D9488",
                "color_text": "#1F2937",
                "spacing": "comfortable",
                "show_avatars": True,
                "section_order": ["personal_info", "skills", "experience", "projects", "education"]
            }
        },
        {
            "name": "Minimal Elegant",
            "code": "MINIMAL",
            "description": "Sleek, airy spacing with a focus on bold typography. Perfect for academics, minimalists, and engineers.",
            "category": "Standard",
            "layout_config": {
                "font_family": "Fira Code",
                "color_primary": "#111827",
                "color_text": "#374151",
                "spacing": "compact",
                "show_avatars": False,
                "section_order": ["personal_info", "experience", "education", "projects", "skills"]
            }
        },
        {
            "name": "Executive Elite",
            "code": "EXECUTIVE",
            "description": "Dignified displays highlighting strategic summary text and business metric outcomes.",
            "category": "Corporate",
            "layout_config": {
                "font_family": "Garamond",
                "color_primary": "#7C2D12",
                "color_text": "#1C1917",
                "spacing": "comfortable",
                "show_avatars": False,
                "section_order": ["personal_info", "experience", "education", "publications", "skills"]
            }
        },
        {
            "name": "Software Engineer Special",
            "code": "SOFTWARE_ENGINEER",
            "description": "Tailored layout optimizing project directories, GitHub profiles, and structured technical stack lists.",
            "category": "Technical",
            "layout_config": {
                "font_family": "JetBrains Mono",
                "color_primary": "#2563EB",
                "color_text": "#1E293B",
                "spacing": "compact",
                "show_avatars": False,
                "section_order": ["personal_info", "skills", "projects", "experience", "education"]
            }
        },
        {
            "name": "Data Scientist Core",
            "code": "DATA_SCIENTIST",
            "description": "Presents structured publications, technical awards, and academic statistics alongside engineering achievements.",
            "category": "Technical",
            "layout_config": {
                "font_family": "Outfit",
                "color_primary": "#4F46E5",
                "color_text": "#111827",
                "spacing": "comfortable",
                "show_avatars": False,
                "section_order": ["personal_info", "skills", "experience", "publications", "education"]
            }
        },
        {
            "name": "Business Analyst Pro",
            "code": "BUSINESS_ANALYST",
            "description": "Highlights professional certifications, project lists, and references prominently.",
            "category": "Corporate",
            "layout_config": {
                "font_family": "Inter",
                "color_primary": "#0369A1",
                "color_text": "#0F172A",
                "spacing": "comfortable",
                "show_avatars": False,
                "section_order": ["personal_info", "experience", "certifications", "education", "skills"]
            }
        },
        {
            "name": "Project Manager Suite",
            "code": "PROJECT_MANAGER",
            "description": "Focuses on strategic methodology keywords, agile certifications, and team size leadership accomplishments.",
            "category": "Corporate",
            "layout_config": {
                "font_family": "Inter",
                "color_primary": "#1E3A8A",
                "color_text": "#1F2937",
                "spacing": "comfortable",
                "show_avatars": False,
                "section_order": ["personal_info", "experience", "certifications", "skills", "education"]
            }
        }
    ]

    def __init__(self, template_repo: ResumeTemplateRepository) -> None:
        self.repo = template_repo

    async def seed_default_templates(self) -> List[ResumeTemplate]:
        """
        Populates default templates in the repository if they do not exist already.
        """
        logger.info("Checking template registrations...")
        seeded_templates = []
        for t_data in self.DEFAULT_TEMPLATES:
            existing = await self.repo.get_by_code(t_data["code"])
            if not existing:
                logger.info(f"Seeding template: '{t_data['name']}'...")
                seeded = await self.repo.create(t_data)
                seeded_templates.append(seeded)
            else:
                seeded_templates.append(existing)
        return seeded_templates

    async def list_templates(self) -> List[ResumeTemplate]:
        """
        Retrieves all active templates. Auto-seeds defaults if the DB list is empty.
        """
        templates = await self.repo.get_multi(limit=100)
        if not templates:
            # Lazy initialize templates
            return await self.seed_default_templates()
        return templates

    async def get_by_code(self, code: str) -> Optional[ResumeTemplate]:
        """
        Retrieves a single template by its unique identifier code, seeding defaults if missing.
        """
        template = await self.repo.get_by_code(code)
        if not template:
            # Auto seed and try again
            await self.seed_default_templates()
            template = await self.repo.get_by_code(code)
        return template

    async def create_custom_template(self, payload: ResumeTemplateCreate) -> ResumeTemplate:
        """
        Registers a new custom template design into the repository.
        """
        existing = await self.repo.get_by_code(payload.code)
        if existing:
            raise ValueError(f"Template with code '{payload.code}' already exists.")
        return await self.repo.create(payload.model_dump())
