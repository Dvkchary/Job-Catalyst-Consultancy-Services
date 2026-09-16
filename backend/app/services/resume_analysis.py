import re
import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.resume_analysis import (
    ResumeQualityReport,
    ValidationIssue,
    SectionStatus,
    ChronologyIssue,
    DateAnalysis,
    KeywordMatch,
    SkillNormalizationResult,
    ResumeStats,
    QualityScoreBreakdown
)

logger = logging.getLogger("app.services.resume_analysis")


class ResumeAnalysisService:
    """
    Algorithmic and heuristic validation/analysis engine for resume quality checks.
    Evaluates completeness, formatting, date chronology, duplicates, spelling checks,
    and returns comprehensive statistics and health scores.
    """

    # Skill Normalization Dictionary
    SKILL_NORMALIZATION_MAP = {
        "js": "JavaScript",
        "javascript": "JavaScript",
        "ts": "TypeScript",
        "typescript": "TypeScript",
        "py": "Python",
        "python": "Python",
        "python3": "Python",
        "postgres": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "aws": "AWS",
        "docker": "Docker",
        "fastapi": "FastAPI",
        "react": "React",
        "reactjs": "React",
        "node": "Node.js",
        "nodejs": "Node.js",
        "sql": "SQL",
        "html": "HTML",
        "css": "CSS",
    }

    # High-impact keywords categories
    KEYWORD_BANK = {
        "TECHNICAL": [
            "FastAPI", "Docker", "AWS", "Python", "React", "PostgreSQL", "SQL",
            "Kubernetes", "CI/CD", "Redis", "TypeScript", "JavaScript", "NoSQL",
            "Git", "API", "GraphQL", "Django", "Flask", "Pydantic", "SQLAlchemy"
        ],
        "LEADERSHIP": [
            "Led", "Managed", "Designed", "Architected", "Mentored", "Directed",
            " Spearheaded", "Oversaw", "Coordinated", "Owned", "Supervised", "Established"
        ],
        "METHODOLOGY": [
            "Agile", "Scrum", "TDD", "BDD", "Microservices", "RESTful", "DevOps",
            "OAuth", "RBAC", "SDLC", "Refactoring", "Clean Architecture"
        ],
        "BUSINESS": [
            "Optimized", "Improved", "Reduced", "Increased", "Delivered", "Launched",
            "Scaled", "Collaborated", "Acquired", "Analyzed", "Revenue", "Conversion"
        ]
    }

    @classmethod
    def parse_date(cls, date_str: Optional[str]) -> Optional[datetime]:
        """
        Safely parse standard resume dates: YYYY-MM-DD, YYYY-MM, YYYY.
        """
        if not date_str:
            return None
        
        cleaned = date_str.strip()
        if cleaned.lower() in ["present", "current", "ongoing", ""]:
            return datetime.now()

        # Try various formats
        for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
            try:
                return datetime.strptime(cleaned, fmt)
            except ValueError:
                continue
        
        # Heuristic search for 4-digit year
        year_match = re.search(r"\b(19|20)\d{2}\b", cleaned)
        if year_match:
            try:
                return datetime(int(year_match.group(0)), 1, 1)
            except ValueError:
                pass
                
        return None

    @classmethod
    def calculate_duration_years(cls, start: Optional[datetime], end: Optional[datetime]) -> float:
        """
        Calculates duration in fractional years between two datetimes.
        """
        if not start or not end:
            return 0.0
        diff = end - start
        return max(0.0, diff.days / 365.25)

    @classmethod
    def analyze_resume_quality(cls, content: Dict[str, Any], resume_id: Optional[uuid.UUID] = None) -> ResumeQualityReport:
        """
        Primary analyzer pipeline generating quality reports, validation statuses,
        statistics, and health scores for a resume document content.
        """
        issues: List[ValidationIssue] = []
        sections_statuses: List[SectionStatus] = []

        # 1. Section Validation & Completeness Extraction
        personal_info = content.get("personal_info") or {}
        education = content.get("education") or []
        experience = content.get("experience") or []
        skills = content.get("skills") or []
        projects = content.get("projects") or []
        certifications = content.get("certifications") or []

        # Personal Info Status
        pi_issues = []
        pi_present = bool(personal_info)
        pi_word_count = 0
        if pi_present:
            summary = personal_info.get("summary") or ""
            pi_word_count = len(summary.split()) if summary else 0
            
            if not personal_info.get("first_name") or not personal_info.get("last_name"):
                pi_issues.append(ValidationIssue(
                    category="COMPLETENESS",
                    severity="ERROR",
                    section="personal_info",
                    message="First name or last name is missing.",
                    suggestion="Add your full name to make your resume identifiable."
                ))
            if not personal_info.get("email"):
                pi_issues.append(ValidationIssue(
                    category="COMPLETENESS",
                    severity="ERROR",
                    section="personal_info",
                    message="Email address is missing.",
                    suggestion="Add a professional email address so recruiters can contact you."
                ))
            elif "@" not in personal_info.get("email", ""):
                pi_issues.append(ValidationIssue(
                    category="FORMATTING",
                    severity="WARNING",
                    section="personal_info",
                    message="Email format seems invalid.",
                    suggestion="Verify that your email address is correctly formatted (e.g. user@domain.com)."
                ))
            if not personal_info.get("phone"):
                pi_issues.append(ValidationIssue(
                    category="COMPLETENESS",
                    severity="WARNING",
                    section="personal_info",
                    message="Phone number is missing.",
                    suggestion="Provide a contact number to speed up interview scheduling."
                ))
            if not personal_info.get("summary") or len(personal_info.get("summary", "").strip()) < 20:
                pi_issues.append(ValidationIssue(
                    category="COMPLETENESS",
                    severity="WARNING",
                    section="personal_info",
                    message="Professional summary is missing or too short.",
                    suggestion="Write a 2-3 sentence summary detailing your experience and top skills."
                ))
        else:
            pi_issues.append(ValidationIssue(
                category="COMPLETENESS",
                severity="ERROR",
                section="personal_info",
                message="Personal information section is entirely missing.",
                suggestion="Fill in your name, contact details, and professional headline."
            ))

        pi_completeness = 0.0
        if pi_present:
            pi_fields = ["first_name", "last_name", "email", "phone", "summary", "job_title"]
            pi_completeness = sum(1.0 for f in pi_fields if personal_info.get(f)) / len(pi_fields) * 100

        sections_statuses.append(SectionStatus(
            section_name="personal_info",
            is_present=pi_present,
            word_count=pi_word_count,
            completeness_percentage=pi_completeness,
            issues=pi_issues
        ))

        # Education Status
        edu_issues = []
        edu_present = len(education) > 0
        edu_word_count = 0
        if edu_present:
            for idx, edu in enumerate(education):
                desc = edu.get("description") or ""
                edu_word_count += len(desc.split()) if desc else 0
                if not edu.get("school"):
                    edu_issues.append(ValidationIssue(
                        category="COMPLETENESS",
                        severity="ERROR",
                        section=f"education[{idx}]",
                        message="School or University name is missing.",
                        suggestion="Add the name of the institution you attended."
                    ))
                if not edu.get("degree"):
                    edu_issues.append(ValidationIssue(
                        category="COMPLETENESS",
                        severity="ERROR",
                        section=f"education[{idx}]",
                        message="Degree type is missing.",
                        suggestion="Specify the degree you received (e.g., Bachelor of Science)."
                    ))
        else:
            edu_issues.append(ValidationIssue(
                category="COMPLETENESS",
                severity="ERROR",
                section="education",
                message="Education section is missing.",
                suggestion="Add your academic background (university, degree, dates)."
            ))

        edu_completeness = 100.0 if edu_present and all(e.get("school") and e.get("degree") for e in education) else (50.0 if edu_present else 0.0)
        sections_statuses.append(SectionStatus(
            section_name="education",
            is_present=edu_present,
            word_count=edu_word_count,
            completeness_percentage=edu_completeness,
            issues=edu_issues
        ))

        # Experience Status
        exp_issues = []
        exp_present = len(experience) > 0
        exp_word_count = 0
        if exp_present:
            for idx, exp in enumerate(experience):
                desc = exp.get("description") or ""
                desc_words = len(desc.split()) if desc else 0
                exp_word_count += desc_words

                if not exp.get("company"):
                    exp_issues.append(ValidationIssue(
                        category="COMPLETENESS",
                        severity="ERROR",
                        section=f"experience[{idx}]",
                        message="Company name is missing.",
                        suggestion="Add the employer or company name."
                    ))
                if not exp.get("title"):
                    exp_issues.append(ValidationIssue(
                        category="COMPLETENESS",
                        severity="ERROR",
                        section=f"experience[{idx}]",
                        message="Job title is missing.",
                        suggestion="Provide your role title (e.g., Software Engineer)."
                    ))
                if desc_words < 15:
                    exp_issues.append(ValidationIssue(
                        category="FORMATTING",
                        severity="WARNING",
                        section=f"experience[{idx}]",
                        message="Job description is too sparse.",
                        suggestion="Expand your experience detail with bullet points emphasizing achievements and tools used."
                    ))
                # Formatting validation check: Empty bullet check
                if desc and any(line.strip() in ["-", "*", "•", "- ", "* ", "• "] for line in desc.split("\n")):
                    exp_issues.append(ValidationIssue(
                        category="FORMATTING",
                        severity="WARNING",
                        section=f"experience[{idx}]",
                        message="Empty bullet points or stray bullets detected.",
                        suggestion="Remove empty list markers from your description text."
                    ))
        else:
            exp_issues.append(ValidationIssue(
                category="COMPLETENESS",
                severity="ERROR",
                section="experience",
                message="Work experience section is missing.",
                suggestion="Add your professional career history (roles, achievements, dates)."
            ))

        exp_completeness = 100.0 if exp_present and all(x.get("company") and x.get("title") and x.get("description") for x in experience) else (40.0 if exp_present else 0.0)
        sections_statuses.append(SectionStatus(
            section_name="experience",
            is_present=exp_present,
            word_count=exp_word_count,
            completeness_percentage=exp_completeness,
            issues=exp_issues
        ))

        # Skills Status
        skills_issues = []
        skills_present = len(skills) > 0
        if skills_present:
            if len(skills) < 5:
                skills_issues.append(ValidationIssue(
                    category="COMPLETENESS",
                    severity="INFO",
                    section="skills",
                    message="Fewer than 5 skills listed.",
                    suggestion="Expand your list of core technical and soft skills (recommend 6-12)."
                ))
        else:
            skills_issues.append(ValidationIssue(
                category="COMPLETENESS",
                severity="ERROR",
                section="skills",
                message="No skills listed.",
                suggestion="Add core competencies, programming languages, and industry domains."
            ))

        skills_completeness = min(100.0, len(skills) * 10.0) if skills_present else 0.0
        sections_statuses.append(SectionStatus(
            section_name="skills",
            is_present=skills_present,
            word_count=0,
            completeness_percentage=skills_completeness,
            issues=skills_issues
        ))

        # Aggregate issues list
        for s_status in sections_statuses:
            issues.extend(s_status.issues)

        # 2. Date Validation & Chronological Consistency
        date_issues: List[ChronologyIssue] = []
        total_exp_years = 0.0
        overlapping_intervals = []
        
        # Experience dates
        parsed_exp_intervals: List[Tuple[int, datetime, datetime, str, str]] = []
        for idx, exp in enumerate(experience):
            s_date = cls.parse_date(exp.get("start_date"))
            e_date = cls.parse_date(exp.get("end_date")) if not exp.get("current") else datetime.now()
            
            if s_date and e_date:
                if e_date < s_date:
                    date_issues.append(ChronologyIssue(
                        section="experience",
                        entry_index=idx,
                        message=f"End date is before start date for {exp.get('company')}.",
                        severity="ERROR"
                    ))
                
                # Check for unrealistic future dates
                now = datetime.now()
                if s_date.year > now.year + 1 or e_date.year > now.year + 1:
                    date_issues.append(ChronologyIssue(
                        section="experience",
                        entry_index=idx,
                        message=f"Future dates detected for {exp.get('company')}.",
                        severity="WARNING"
                    ))

                parsed_exp_intervals.append((idx, s_date, e_date, exp.get("company", ""), exp.get("title", "")))
                total_exp_years += cls.calculate_duration_years(s_date, e_date)
            else:
                if exp.get("start_date"):
                    date_issues.append(ChronologyIssue(
                        section="experience",
                        entry_index=idx,
                        message=f"Could not parse dates correctly for {exp.get('company')}.",
                        severity="WARNING"
                    ))

        # Check overlapping experience
        # Sort intervals by start date to check overlapping
        sorted_intervals = sorted(parsed_exp_intervals, key=lambda x: x[1])
        for i in range(len(sorted_intervals) - 1):
            curr_idx, curr_start, curr_end, curr_comp, curr_title = sorted_intervals[i]
            next_idx, next_start, next_end, next_comp, next_title = sorted_intervals[i+1]
            
            # If the next experience starts before the current one ends
            if next_start < curr_end:
                # Calculate overlapping percentage or overlap duration
                overlap_end = min(curr_end, next_end)
                overlap_days = (overlap_end - next_start).days
                
                # If overlap is significant (e.g., > 30 days), flag it
                if overlap_days > 30:
                    overlapping_intervals.append({
                        "company_a": curr_comp,
                        "title_a": curr_title,
                        "company_b": next_comp,
                        "title_b": next_title,
                        "overlap_days": overlap_days
                    })
                    date_issues.append(ChronologyIssue(
                        section="experience",
                        entry_index=next_idx,
                        message=f"Overlapping experience dates between {curr_comp} and {next_comp} ({overlap_days} days).",
                        severity="INFO"
                    ))

        # Chronology order check (most recent should be first)
        is_chronological = True
        for i in range(len(parsed_exp_intervals) - 1):
            # We expect the input array to be in reverse-chronological order (newest first).
            # So index i end_date should be >= index i+1 end_date
            _, _, e_curr, comp_curr, _ = parsed_exp_intervals[i]
            _, _, e_next, comp_next, _ = parsed_exp_intervals[i+1]
            if e_curr < e_next:
                is_chronological = False
                date_issues.append(ChronologyIssue(
                    section="experience",
                    entry_index=i+1,
                    message="Work experience entries are not listed in reverse chronological order.",
                    severity="WARNING"
                ))
                break

        date_analysis = DateAnalysis(
            is_chronological=is_chronological,
            total_years_experience=round(total_exp_years, 1),
            overlapping_intervals=overlapping_intervals,
            issues=date_issues
        )

        # Map Date issues to ValidationIssues
        for di in date_issues:
            issues.append(ValidationIssue(
                category="DATE",
                severity=di.severity,
                section=f"{di.section}[{di.entry_index}]" if di.entry_index >= 0 else di.section,
                message=di.message,
                suggestion="Re-verify the dates and ensure the most recent position is listed first."
            ))

        # 3. Duplicate Detection
        duplicate_entries = []
        # Check experience duplicates
        seen_exp = set()
        for idx, exp in enumerate(experience):
            comp = (exp.get("company") or "").strip().lower()
            title = (exp.get("title") or "").strip().lower()
            if comp and title:
                key = f"{comp}||{title}"
                if key in seen_exp:
                    duplicate_entries.append({
                        "section": "experience",
                        "index": idx,
                        "key_fields": {"company": exp.get("company"), "title": exp.get("title")},
                        "message": f"Duplicate work experience entry found for '{exp.get('title')}' at '{exp.get('company')}'."
                    })
                seen_exp.add(key)

        # Check education duplicates
        seen_edu = set()
        for idx, edu in enumerate(education):
            school = (edu.get("school") or "").strip().lower()
            deg = (edu.get("degree") or "").strip().lower()
            if school and deg:
                key = f"{school}||{deg}"
                if key in seen_edu:
                    duplicate_entries.append({
                        "section": "education",
                        "index": idx,
                        "key_fields": {"school": edu.get("school"), "degree": edu.get("degree")},
                        "message": f"Duplicate education entry found for '{edu.get('degree')}' at '{edu.get('school')}'."
                    })
                seen_edu.add(key)

        # Check skills duplicates
        seen_skills = set()
        for idx, s in enumerate(skills):
            s_name = (s.get("name") or "").strip().lower()
            if s_name:
                if s_name in seen_skills:
                    duplicate_entries.append({
                        "section": "skills",
                        "index": idx,
                        "key_fields": {"name": s.get("name")},
                        "message": f"Duplicate skill entry found: '{s.get('name')}'."
                    })
                seen_skills.add(s_name)

        # Map duplicates to ValidationIssues
        for dup in duplicate_entries:
            issues.append(ValidationIssue(
                category="DUPLICATE",
                severity="WARNING",
                section=dup["section"],
                message=dup["message"],
                suggestion="Consolidate duplicate sections or remove repeated entries."
            ))

        # 4. Grammar and Spelling Hooks (Local Heuristic / Dictionary based)
        # Check casing of words
        text_for_spelling = ""
        if personal_info.get("summary"):
            text_for_spelling += " " + personal_info.get("summary")
        for exp in experience:
            text_for_spelling += " " + (exp.get("description") or "")
        for proj in projects:
            text_for_spelling += " " + (proj.get("description") or "")

        # Heuristic rules:
        # Check lowercase 'i' used in description/summary
        i_matches = re.findall(r"\bi\b", text_for_spelling)
        if len(i_matches) > 0:
            issues.append(ValidationIssue(
                category="GRAMMAR",
                severity="WARNING",
                section="content",
                message="Lower-cased isolated personal pronoun 'i' detected.",
                suggestion="Capitalize personal pronouns ('I') for formal resume writing."
            ))

        # Missing trailing period on bullet lists or descriptions
        bullet_period_errors = 0
        for idx, exp in enumerate(experience):
            desc = (exp.get("description") or "").strip()
            if desc:
                # If there are bullet lines, check if they don't end in punctuation
                lines = [l.strip() for l in desc.split("\n") if l.strip().startswith(("-", "*", "•"))]
                for l in lines:
                    cleaned_line = l.rstrip("•*- ")
                    if cleaned_line and cleaned_line[-1] not in [".", "!", "?", ";"]:
                        bullet_period_errors += 1
        
        if bullet_period_errors > 2:
            issues.append(ValidationIssue(
                category="FORMATTING",
                severity="INFO",
                section="experience",
                message="Multiple bullet items do not end with terminal punctuation (periods).",
                suggestion="Add periods to the end of your descriptive accomplishments to maintain consistent grammar."
            ))

        # Check consecutive spaces
        if len(re.findall(r"[ ][ ]+", text_for_spelling)) > 0:
            issues.append(ValidationIssue(
                category="FORMATTING",
                severity="INFO",
                section="content",
                message="Multiple consecutive spaces detected.",
                suggestion="Review typography spacing for clean visual alignment."
            ))

        # 5. Skill Normalization and Mentions
        normalized_skills: List[SkillNormalizationResult] = []
        for s in skills:
            orig = s.get("name", "")
            orig_cleaned = orig.strip().lower()
            if orig_cleaned in cls.SKILL_NORMALIZATION_MAP:
                norm_val = cls.SKILL_NORMALIZATION_MAP[orig_cleaned]
                if orig != norm_val:
                    normalized_skills.append(SkillNormalizationResult(
                        original=orig,
                        normalized=norm_val,
                        category=s.get("category")
                    ))
                    issues.append(ValidationIssue(
                        category="SPELLING",
                        severity="INFO",
                        section="skills",
                        message=f"Standard normalization found for '{orig}' -> '{norm_val}'.",
                        suggestion=f"Update spelling of '{orig}' to professional standard casing '{norm_val}'."
                    ))

        # 6. Keyword Extraction
        keyword_counts: Dict[str, int] = {}
        keyword_categories: Dict[str, str] = {}
        
        text_lower = text_for_spelling.lower()
        # Scan skills too
        for s in skills:
            text_lower += " " + s.get("name", "").lower()

        for category, words in cls.KEYWORD_BANK.items():
            for w in words:
                pattern = r"\b" + re.escape(w.lower()) + r"\b"
                matches = re.findall(pattern, text_lower)
                if matches:
                    keyword_counts[w] = keyword_counts.get(w, 0) + len(matches)
                    keyword_categories[w] = category

        # Sort extracted keywords by occurrences
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        keywords_matched = [
            KeywordMatch(keyword=k, count=c, category=keyword_categories[k])
            for k, c in sorted_keywords[:12]
        ]

        # 7. Resume Statistics
        all_text = (
            f"{(personal_info.get('first_name') or '')} "
            f"{(personal_info.get('last_name') or '')} "
            f"{(personal_info.get('summary') or '')} "
            f"{(personal_info.get('job_title') or '')} "
        )
        for exp in experience:
            all_text += f" {(exp.get('company') or '')} {(exp.get('title') or '')} {(exp.get('description') or '')}"
        for edu in education:
            all_text += f" {(edu.get('school') or '')} {(edu.get('degree') or '')} {(edu.get('description') or '')}"
        for proj in projects:
            all_text += f" {(proj.get('name') or '')} {(proj.get('description') or '')}"

        words_list = all_text.split()
        total_words = len(words_list)
        
        # Sentences split by . ! ?
        sentences_list = [s for s in re.split(r"[.!?]+", all_text) if s.strip()]
        total_sentences = len(sentences_list)

        # Average bullet length (in words)
        bullet_lengths = []
        for exp in experience:
            desc = exp.get("description") or ""
            bullets = [b.strip() for b in desc.split("\n") if b.strip().startswith(("-", "*", "•"))]
            for b in bullets:
                cleaned_b = b.lstrip("-*• ").strip()
                if cleaned_b:
                    bullet_lengths.append(len(cleaned_b.split()))
        
        avg_bullet = sum(bullet_lengths) / len(bullet_lengths) if bullet_lengths else 0.0

        section_word_counts = {
            "personal_info": pi_word_count,
            "education": edu_word_count,
            "experience": exp_word_count,
            "projects": sum(len((p.get("description") or "").split()) for p in projects)
        }

        stats = ResumeStats(
            total_words=total_words,
            total_sentences=total_sentences,
            avg_bullet_length=round(avg_bullet, 1),
            section_word_counts=section_word_counts
        )

        # 8. Resume Completeness Percentage
        # Calibrate overall completeness weight
        completeness_percentage = (pi_completeness * 0.25) + (edu_completeness * 0.25) + (exp_completeness * 0.35) + (skills_completeness * 0.15)
        completeness_percentage = round(min(100.0, max(0.0, completeness_percentage)), 1)

        # 9. Health Score Logic
        # Completeness component (0 to 100)
        score_completeness = completeness_percentage

        # Structure component (starts at 100, drops for date mismatch, duplicates)
        score_structure = 100.0
        # Deduct for not chronological
        if not is_chronological:
            score_structure -= 15.0
        # Deduct for overlapping experience
        score_structure -= min(25.0, len(overlapping_intervals) * 8.0)
        # Deduct for missing essential sections
        if not pi_present:
            score_structure -= 20.0
        if not edu_present:
            score_structure -= 15.0
        if not exp_present:
            score_structure -= 20.0
        if not skills_present:
            score_structure -= 10.0
        # Deduct for duplicates
        score_structure -= min(15.0, len(duplicate_entries) * 5.0)
        score_structure = max(0.0, score_structure)

        # Formatting component (starts at 100, drops for errors)
        score_formatting = 100.0
        # Deduct for bullet issues
        score_formatting -= min(15.0, bullet_period_errors * 3.0)
        # Deduct for consecutive spaces
        if len(re.findall(r"[ ][ ]+", text_for_spelling)) > 0:
            score_formatting -= 5.0
        # Deduct for formatting issues flagged
        fmt_issues_count = sum(1 for i in issues if i.category == "FORMATTING")
        score_formatting -= min(20.0, fmt_issues_count * 4.0)
        score_formatting = max(0.0, score_formatting)

        # Impact component (0 to 100)
        # Starts at 40, gains points for keywords matched, years of experience, bullet detail
        score_impact = 40.0
        score_impact += min(30.0, len(keywords_matched) * 3.0)
        score_impact += min(20.0, total_exp_years * 2.0)
        # Bonus for healthy bullet word density
        if avg_bullet >= 12.0 and avg_bullet <= 25.0:
            score_impact += 10.0
        elif avg_bullet > 0:
            score_impact += 5.0
        score_impact = min(100.0, max(0.0, score_impact))

        # Overall weighted Health Score
        health_score = (
            (score_completeness * 0.30) +
            (score_structure * 0.30) +
            (score_formatting * 0.20) +
            (score_impact * 0.20)
        )
        health_score = round(min(100.0, max(0.0, health_score)), 1)

        # Rating selection
        if health_score >= 85.0:
            rating = "EXCELLENT"
        elif health_score >= 70.0:
            rating = "GOOD"
        elif health_score >= 50.0:
            rating = "IMPROVEMENT_NEEDED"
        else:
            rating = "CRITICAL"

        breakdown = QualityScoreBreakdown(
            completeness=round(score_completeness, 1),
            structure=round(score_structure, 1),
            formatting=round(score_formatting, 1),
            impact=round(score_impact, 1)
        )

        return ResumeQualityReport(
            resume_id=resume_id,
            health_score=health_score,
            rating=rating,
            score_breakdown=breakdown,
            completeness_percentage=completeness_percentage,
            sections=sections_statuses,
            date_analysis=date_analysis,
            issues=issues,
            keywords=keywords_matched,
            normalized_skills=normalized_skills,
            statistics=stats,
            duplicate_entries_detected=[d["key_fields"] for d in duplicate_entries]
        )
