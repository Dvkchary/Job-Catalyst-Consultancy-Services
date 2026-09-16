import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger("app.services.resume_export")


class ResumeExportService:
    """
    Unified Resume Export System.
    Generates standardized representations of resume structures across format boundaries:
    1. JSON: Machine-readable data structure.
    2. Print (TXT): Pure plaintext formatted representation with elegant dividers.
    3. PDF: Structured document format stream representation.
    4. DOCX: Standard word processor document representation.
    """

    @classmethod
    def export_as_json(cls, resume_title: str, content: Dict[str, Any]) -> bytes:
        """
        Serializes and packs the complete structured resume data into standard JSON bytes.
        """
        payload = {
            "exporter": "JobCatalyst AI Resume Engine v1",
            "exported_at": "2026-07-02T00:00:00Z",
            "resume_title": resume_title,
            "content": content
        }
        return json.dumps(payload, indent=2).encode("utf-8")

    @classmethod
    def export_as_print(cls, resume_title: str, content: Dict[str, Any]) -> str:
        """
        Renders a highly readable, elegantly formatted plaintext representation (Print Version)
        using structured headers, dynamic dividers, and aligned bullet matrices.
        """
        p_info = content.get("personal_info") or {}
        first_name = p_info.get("first_name", "Candidate")
        last_name = p_info.get("last_name", "Name")
        email = p_info.get("email", "")
        phone = p_info.get("phone", "")
        linkedin = p_info.get("linkedin", "")
        address = p_info.get("address", "")
        summary = p_info.get("summary", "")
        job_title = p_info.get("job_title", "")

        lines = []
        # Header block
        lines.append("=" * 80)
        lines.append(f"{first_name.upper()} {last_name.upper()}".center(80))
        if job_title:
            lines.append(job_title.center(80))
        
        contact_parts = [p for p in [phone, email, linkedin, address] if p]
        if contact_parts:
            lines.append(" | ".join(contact_parts).center(80))
        lines.append("=" * 80)
        lines.append("")

        if summary:
            lines.append("PROFESSIONAL SUMMARY")
            lines.append("-" * 20)
            lines.append(summary)
            lines.append("")

        # Experience Section
        experience = content.get("experience") or []
        if experience:
            lines.append("WORK EXPERIENCE")
            lines.append("-" * 15)
            for exp in experience:
                company = exp.get("company", "")
                title = exp.get("title", "")
                loc = exp.get("location") or "Remote"
                start = exp.get("start_date", "")
                end = exp.get("end_date") or "Present"
                desc = exp.get("description", "")
                
                header_line = f"{title} - {company} ({loc})"
                date_str = f"{start} to {end}"
                
                # Align left and right
                spacing = 80 - len(header_line) - len(date_str)
                if spacing > 0:
                    lines.append(f"{header_line}{' ' * spacing}{date_str}")
                else:
                    lines.append(f"{header_line} | {date_str}")
                
                if desc:
                    # Bullet points or paragraph formatting
                    for d_line in desc.split("\n"):
                        if d_line.strip():
                            lines.append(f"  • {d_line.strip()}")
                lines.append("")

        # Education Section
        education = content.get("education") or []
        if education:
            lines.append("EDUCATION")
            lines.append("-" * 9)
            for edu in education:
                school = edu.get("school", "")
                deg = edu.get("degree", "")
                field = edu.get("field_of_study", "")
                start = edu.get("start_date", "")
                end = edu.get("end_date") or "Ongoing"
                desc = edu.get("description", "")
                
                header_line = f"{deg} in {field} - {school}"
                date_str = f"{start} to {end}"
                
                spacing = 80 - len(header_line) - len(date_str)
                if spacing > 0:
                    lines.append(f"{header_line}{' ' * spacing}{date_str}")
                else:
                    lines.append(f"{header_line} | {date_str}")
                
                if desc:
                    lines.append(f"  {desc}")
                lines.append("")

        # Projects Section
        projects = content.get("projects") or []
        if projects:
            lines.append("PROJECTS")
            lines.append("-" * 8)
            for proj in projects:
                name = proj.get("name", "")
                role = proj.get("role") or "Developer"
                start = proj.get("start_date", "")
                end = proj.get("end_date") or "Ongoing"
                url = proj.get("url", "")
                desc = proj.get("description", "")
                techs = ", ".join(proj.get("technologies") or [])
                
                header_line = f"{name} ({role})"
                date_str = f"{start} to {end}"
                
                spacing = 80 - len(header_line) - len(date_str)
                if spacing > 0:
                    lines.append(f"{header_line}{' ' * spacing}{date_str}")
                else:
                    lines.append(f"{header_line} | {date_str}")
                
                if url:
                    lines.append(f"  URL: {url}")
                if desc:
                    lines.append(f"  Description: {desc}")
                if techs:
                    lines.append(f"  Technologies: {techs}")
                lines.append("")

        # Skills Section
        skills = content.get("skills") or []
        if skills:
            lines.append("SKILLS")
            lines.append("-" * 6)
            skill_strings = []
            for sk in skills:
                name = sk.get("name", "")
                level = sk.get("level", "INTERMEDIATE")
                skill_strings.append(f"{name} ({level})")
            lines.append(", ".join(skill_strings))
            lines.append("")

        # Certifications Section
        certs = content.get("certifications") or []
        if certs:
            lines.append("CERTIFICATIONS")
            lines.append("-" * 14)
            for cert in certs:
                name = cert.get("name", "")
                issuer = cert.get("issuer", "")
                issued = cert.get("issue_date") or ""
                lines.append(f"  • {name} - Issued by {issuer} ({issued})")
            lines.append("")

        # Languages Section
        languages = content.get("languages") or []
        if languages:
            lines.append("LANGUAGES")
            lines.append("-" * 9)
            lang_strings = [f"{l.get('language')} ({l.get('proficiency')})" for l in languages]
            lines.append(", ".join(lang_strings))
            lines.append("")

        lines.append("=" * 80)
        lines.append("Generated by JobCatalyst AI".center(80))
        lines.append("=" * 80)

        return "\n".join(lines)

    @classmethod
    def export_as_pdf(cls, resume_title: str, content: Dict[str, Any]) -> bytes:
        """
        Renders a simulated PDF document stream featuring PDF standard header headers,
        cross-reference structures, and readable content records.
        """
        logger.info(f"Generating PDF export stream for resume '{resume_title}'...")
        # PDF document headers and metadata markers
        pdf_header = (
            b"%PDF-1.4\n"
            b"%JobCatalyst AI Resume Engine Exporter v1.0\n"
            b"1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
            b"2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n"
            b"3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 595 842]\n/Resources << >>\n>>\nendobj\n"
        )
        
        # Serialize text data block representation
        text_rep = cls.export_as_print(resume_title, content)
        content_stream = f"stream\nBT\n/F1 12 Tf\n50 800 Td\n({resume_title} PDF Rendered Output)\nET\nendstream\n".encode("utf-8")
        
        footer = b"%%EOF\n"
        return pdf_header + content_stream + text_rep.encode("utf-8") + footer

    @classmethod
    def export_as_docx(cls, resume_title: str, content: Dict[str, Any]) -> bytes:
        """
        Renders a simulated DOCX Word stream with standard PK file-signatures
        and readable plain text metadata records.
        """
        logger.info(f"Generating DOCX export stream for resume '{resume_title}'...")
        # Zip/DOCX header standard PK signature
        pk_signature = b"PK\x03\x04\x14\x00\x08\x00\x08\x00\x00\x00\x00\x00"
        text_rep = cls.export_as_print(resume_title, content)
        
        docx_meta = f"\n[Content_Types].xml\nword/document.xml\nTitle: {resume_title}\n".encode("utf-8")
        return pk_signature + docx_meta + text_rep.encode("utf-8")
