import re
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime

from app.db.ats_repositories import ATSRepository
from app.db.resume_repositories import ResumeRepository
from app.models.ats import ATSReport
from app.models.resume import Resume
from app.schemas.ats import (
    ATSReportData,
    KeywordMatchDetails,
    FormattingDetails,
    ReadabilityDetails,
    GrammarDetails,
    ActionVerbDetails,
    SectionCompletenessDetails,
    BenchmarkDetails,
    ResumeComparisonResponse,
    ScoreMetricComparison
)

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "of", "to", "in", "for", "on", "with",
    "at", "by", "from", "up", "about", "into", "over", "after", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "shall", "should", "can", "could", "may", "might", "must", "us", "we", "you", "they",
    "he", "she", "it", "our", "their", "his", "her", "its", "this", "that", "these",
    "those", "as", "such", "than", "not", "no", "only", "other", "some", "any", "all",
    "more", "most", "own", "same", "so", "too", "very", "just", "now", "here", "there",
    "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very"
}

ACTION_VERBS = {
    "spearheaded", "designed", "implemented", "optimized", "managed", "led", "developed",
    "architected", "orchestrated", "engineered", "coordinated", "delivered", "executed",
    "formulated", "established", "facilitated", "supervised", "directed", "authored",
    "mentored", "collaborated", "built", "created", "analyzed", "reduced", "increased",
    "maximized", "minimized", "improved", "streamlined", "accelerated", "pioneered",
    "restructured", "revitalized", "administered", "integrated", "negotiated", "resolved"
}


class ATSService:
    """
    ATS Analysis Engine Service handling the logic for keyword parsing, ATS scores (0-100),
    formatting checks, readability, action verb density, comparison, and improvement reports.
    """

    def __init__(self, ats_repo: ATSRepository, resume_repo: ResumeRepository):
        self.ats_repo = ats_repo
        self.resume_repo = resume_repo

    def clean_text_to_words(self, text: str) -> List[str]:
        """
        Tokenizes and cleans a text string into downcased words without punctuation.
        """
        if not text:
            return []
        # Replace non-alphabetic characters with space
        words = re.findall(r"\b[a-zA-Z-]{2,}\b", text.lower())
        return [w for w in words if w not in STOP_WORDS]

    def extract_keywords(self, text: str, max_keywords: int = 40) -> Set[str]:
        """
        Extracts highly relevant keywords based on frequency and context.
        """
        words = self.clean_text_to_words(text)
        freq: Dict[str, int] = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        
        # Sort by frequency and return top keys
        sorted_keys = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return {item[0] for item in sorted_keys[:max_keywords]}

    def extract_all_resume_text(self, resume: Resume) -> str:
        """
        Aggregates all text fields in a Resume schema/dict into a single searchable text blob.
        """
        content = resume.content or {}
        text_parts = []

        # 1. Personal Info
        personal = content.get("personal_info", {})
        if personal:
            text_parts.append(personal.get("name", ""))
            text_parts.append(personal.get("title", ""))
            text_parts.append(personal.get("summary", ""))

        # 2. Experience
        experience = content.get("experience", [])
        for exp in experience:
            text_parts.append(exp.get("role", ""))
            text_parts.append(exp.get("company", ""))
            text_parts.append(exp.get("description", ""))
            highlights = exp.get("highlights", [])
            if isinstance(highlights, list):
                text_parts.extend(highlights)

        # 3. Education
        education = content.get("education", [])
        for edu in education:
            text_parts.append(edu.get("degree", ""))
            text_parts.append(edu.get("field_of_study", ""))
            text_parts.append(edu.get("institution", ""))
            text_parts.append(edu.get("description", ""))

        # 4. Projects
        projects = content.get("projects", [])
        for proj in projects:
            text_parts.append(proj.get("name", ""))
            text_parts.append(proj.get("role", ""))
            text_parts.append(proj.get("description", ""))
            highlights = proj.get("highlights", [])
            if isinstance(highlights, list):
                text_parts.extend(highlights)

        # 5. Skills
        skills = content.get("skills", [])
        if isinstance(skills, list):
            for s in skills:
                if isinstance(s, dict):
                    text_parts.append(s.get("name", ""))
                    keywords = s.get("keywords", [])
                    if isinstance(keywords, list):
                        text_parts.extend(keywords)
                elif isinstance(s, str):
                    text_parts.append(s)

        # 6. Certifications
        certs = content.get("certifications", [])
        for cert in certs:
            text_parts.append(cert.get("name", ""))
            text_parts.append(cert.get("issuer", ""))

        return " ".join([p for p in text_parts if p])

    def count_syllables_in_word(self, word: str) -> int:
        """
        Heuristic syllable counter for English words.
        """
        word = word.lower().strip()
        if not word:
            return 0
        if len(word) <= 3:
            return 1
        
        vowels = "aeiouy"
        count = 0
        if word[0] in vowels:
            count += 1
            
        for i in range(1, len(word)):
            if word[i] in vowels and word[i-1] not in vowels:
                count += 1
                
        if word.endswith("e"):
            # skip final e unless it's "-le" or similar
            if not word.endswith("le"):
                count -= 1
                
        return max(1, count)

    def analyze_readability(self, text: str) -> ReadabilityDetails:
        """
        Calculates Flesh Reading Ease score and estimated grade level.
        """
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        words = [w for w in re.split(r"\s+", text) if w.strip()]
        
        num_sentences = max(1, len(sentences))
        num_words = max(1, len(words))
        
        # Count syllables
        total_syllables = sum(self.count_syllables_in_word(w) for w in words)
        
        # Flesch Reading Ease Formula
        score = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (total_syllables / num_words)
        score = max(0.0, min(100.0, score))
        
        # Categorize
        if score >= 90:
            rating = "EASY"
            grade = "5th Grade"
        elif score >= 80:
            rating = "EASY"
            grade = "6th Grade"
        elif score >= 70:
            rating = "EASY"
            grade = "7th Grade"
        elif score >= 60:
            rating = "STANDARD"
            grade = "8th-9th Grade"
        elif score >= 50:
            rating = "STANDARD"
            grade = "10th-12th Grade"
        elif score >= 30:
            rating = "DIFFICULT"
            grade = "College Level"
        else:
            rating = "VERY_DIFFICULT"
            grade = "Graduate Level"
            
        return ReadabilityDetails(
            flesch_reading_ease=round(score, 1),
            grade_level=grade,
            readability_rating=rating
        )

    def analyze_grammar(self, text: str) -> GrammarDetails:
        """
        Scans text for typical resume grammar or mechanical issues.
        """
        issues = []
        suggestions = []
        errors_count = 0

        # Check for isolated lowercase 'i'
        i_matches = re.findall(r"\bi\b", text)
        if i_matches:
            errors_count += len(i_matches)
            issues.append(f"Found {len(i_matches)} occurrences of isolated lowercase 'i'.")
            suggestions.append("Always capitalize the personal pronoun 'I'. Better yet, rewrite bullet points to begin with strong active verbs instead of pronouns.")

        # Check for double spaces
        double_spaces = len(re.findall(r" {2,}", text))
        if double_spaces > 0:
            errors_count += double_spaces
            issues.append(f"Detected {double_spaces} places with double-spacing.")
            suggestions.append("Remove redundant spaces for consistent word formatting and ATS alignment.")

        # Check passive voice indicators (e.g. "was responsible for", "worked on")
        passive_patterns = ["was responsible for", "were responsible for", "assisted in", "helped with", "worked on"]
        found_passives = []
        for p in passive_patterns:
            matches = len(re.findall(r"\b" + p + r"\b", text.lower()))
            if matches > 0:
                found_passives.append(f"'{p}' ({matches}x)")
                errors_count += matches
                
        if found_passives:
            issues.append(f"Identified passive/weak phrases: {', '.join(found_passives)}.")
            suggestions.append("Replace passive helper expressions (like 'responsible for') with powerful direct action verbs to strengthen impacts.")

        # Bullets punctuation consistency check
        # We can look for bullets starting with a dash or bullet symbol that don't end with a period, or vice versa
        # This is a soft style check
        return GrammarDetails(
            errors_detected=errors_count,
            issues=issues if issues else ["No major mechanical or formatting grammar errors identified."],
            suggestions=suggestions if suggestions else ["Your resume demonstrates clean typography and professional voice composition."]
        )

    def analyze_action_verbs(self, text: str) -> ActionVerbDetails:
        """
        Evaluates the count and variety of powerful action verbs in the text.
        """
        words = [w.lower().strip() for w in re.findall(r"\b[a-zA-Z]+\b", text)]
        verbs_used = [w for w in words if w in ACTION_VERBS]
        unique_verbs = list(set(verbs_used))
        
        suggestions = []
        if len(verbs_used) < 5:
            suggestions.append("Add more powerful action verbs (e.g., 'Spearheaded', 'Orchestrated', 'Optimized') at the start of experience bullet points to emphasize ownership.")
        if len(unique_verbs) < (len(verbs_used) * 0.6) and len(verbs_used) > 5:
            suggestions.append("Vary your choice of action verbs. Avoid repeating the same lead word (e.g., 'Developed') across multiple achievements.")

        return ActionVerbDetails(
            action_verbs_count=len(verbs_used),
            verbs_used=unique_verbs,
            suggestions=suggestions if suggestions else ["Outstanding usage of rich, diverse action verbs to launch professional achievements."]
        )

    def analyze_formatting(self, resume: Resume) -> FormattingDetails:
        """
        Analyzes the resume schema for potentially non-compliant ATS formatting.
        """
        issues = []
        content = resume.content or {}

        # Look for indicators of images/charts or tables in layout
        personal = content.get("personal_info", {})
        photo = personal.get("photo_url") or personal.get("photo")
        if photo:
            issues.append("Contains photo or profile image URL. Images are unreadable to older ATS systems and can introduce compliance bias.")

        # Margins check simulation (based on standard layouts)
        if "layout" in content:
            margins = content.get("layout", {}).get("margins", "standard")
            if str(margins).lower() in ["narrow", "very_narrow", "tight", "0.25", "0.25in"]:
                issues.append("Narrow or microscopic page margins detected (< 0.5 in). This might break PDF generation alignment or look overly dense.")

        # Standard scannable font check simulation
        template_code = resume.template_code or ""
        if template_code.lower() in ["creative_fancy", "comic_sans", "brutalist_terminal"]:
            issues.append(f"Non-standard template/font structure detected ('{template_code}'). Stick to scannable modern standards like Arial, Calibri, or Inter.")

        # Check for complex multi-column grid layouts
        # Highly modern ATS handles 2-column layouts fine, but we can warn the user
        layout_grid = content.get("layout", {}).get("grid", "single")
        if layout_grid in ["multi", "three-column"]:
            issues.append("Complex multi-column grid layout detected. Single-column layouts are generally safest for linear parser execution.")

        return FormattingDetails(
            has_unsupported_fonts=any("font" in iss.lower() for iss in issues),
            has_poor_margins=any("margin" in iss.lower() for iss in issues),
            has_complex_tables=any("table" in iss.lower() for iss in issues),
            has_charts_or_images=bool(photo),
            issues=issues if issues else ["Formatting complies beautifully with typical ATS parser expectations."]
        )

    def analyze_section_completeness(self, resume: Resume) -> SectionCompletenessDetails:
        """
        Validates completeness of core resume sections.
        """
        content = resume.content or {}
        essential = ["personal_info", "experience", "education", "skills"]
        present = []
        missing = []

        for section in essential:
            sec_data = content.get(section)
            if sec_data:
                # check if non-empty
                if isinstance(sec_data, dict) and any(sec_data.values()):
                    present.append(section)
                elif isinstance(sec_data, list) and len(sec_data) > 0:
                    present.append(section)
                else:
                    missing.append(section)
            else:
                missing.append(section)

        # check optional sections
        optional = ["projects", "certifications", "awards", "volunteer"]
        for section in optional:
            sec_data = content.get(section)
            if sec_data and len(sec_data) > 0:
                present.append(section)

        # normalize section names for professional display
        def display_name(name: str) -> str:
            return name.replace("_", " ").title()

        return SectionCompletenessDetails(
            present_sections=[display_name(s) for s in present],
            missing_essential_sections=[display_name(s) for s in missing],
            completeness_percentage=round((len(present) / (len(present) + len(missing))) * 100, 1) if (present or missing) else 0.0
        )

    def generate_ai_suggestions(self, resume: Resume, job_description: str) -> List[str]:
        """
        Hook generating highly practical tailored bullet recommendations and strategic optimizations.
        """
        suggestions = []
        resume_text = self.extract_all_resume_text(resume).lower()
        jd_keywords = self.extract_keywords(job_description)

        # Check for key tech gap
        gap_keywords = [kw for kw in jd_keywords if kw not in resume_text]
        if gap_keywords:
            suggestions.append(
                f"Core JD Keyword Gap: Your resume is missing target skills found in the JD: {', '.join(gap_keywords[:5])}. Integrate these keywords directly into your Professional Summary or Skills section."
            )

        # General impact advice
        suggestions.append(
            "Quantitative Achievements: Strengthen your Work Experience bullets by anchoring achievements with business metrics (e.g., 'reduced system latency by 24%', 'led a team of 4 engineers', 'saved $12K annually')."
        )
        suggestions.append(
            "Tailored Summary: Craft a targeted headline at the top matching the precise role title specified in the Job Description to instantly capture reviewer attention."
        )

        return suggestions

    def generate_benchmark(self, ats_score: int) -> BenchmarkDetails:
        """
        Returns simulated performance stats comparing this ATS score with standard historical aggregates.
        """
        ind_avg = 66.5
        # compute percentile based on standard normal curve scaling
        diff = ats_score - ind_avg
        percentile = 50.0 + (diff * 1.6)
        percentile = max(5.0, min(99.0, round(percentile, 1)))

        if ats_score >= 85:
            rating = "OUTSTANDING"
        elif ats_score >= 70:
            rating = "ABOVE_AVERAGE"
        elif ats_score >= 55:
            rating = "AVERAGE"
        else:
            rating = "BELOW_AVERAGE"

        return BenchmarkDetails(
            industry_average_score=ind_avg,
            user_percentile=percentile,
            rating=rating
        )

    def analyze_resume_against_jd(self, resume: Resume, job_description: str, job_title: Optional[str] = None) -> ATSReportData:
        """
        Runs complete parser calculations and aggregates ratings into a unified ATSReportData payload.
        """
        resume_text = self.extract_all_resume_text(resume)
        jd_keywords = self.extract_keywords(job_description)
        resume_words = set(self.clean_text_to_words(resume_text))

        # 1. Keyword Matching
        matched = list(jd_keywords.intersection(resume_words))
        missing = list(jd_keywords.difference(resume_words))
        
        kw_match_pct = (len(matched) / max(1, len(jd_keywords))) * 100
        keyword_details = KeywordMatchDetails(
            matched_keywords=matched,
            missing_keywords=missing,
            keyword_match_percentage=round(kw_match_pct, 1)
        )

        # 2. Formatting Details
        formatting_details = self.analyze_formatting(resume)
        formatting_score = 100.0 - (len(formatting_details.issues) * 15.0)
        formatting_score = max(30.0, formatting_score)

        # 3. Readability details
        readability_details = self.analyze_readability(resume_text)

        # 4. Grammar details
        grammar_details = self.analyze_grammar(resume_text)
        grammar_score = 100.0 - (grammar_details.errors_detected * 5.0)
        grammar_score = max(40.0, grammar_score)

        # 5. Action verbs details
        action_verbs_details = self.analyze_action_verbs(resume_text)

        # 6. Section completeness
        section_details = self.analyze_section_completeness(resume)

        # Aggregate Overall ATS Score (weighted average)
        # Weights: Keyword Match (40%), Section Completeness (20%), Grammar (15%), Formatting (15%), Readability (10%)
        keyword_weight = 0.40
        completeness_weight = 0.20
        grammar_weight = 0.15
        formatting_weight = 0.15
        readability_weight = 0.10

        weighted_score = (
            (kw_match_pct * keyword_weight) +
            (section_details.completeness_percentage * completeness_weight) +
            (grammar_score * grammar_weight) +
            (formatting_score * formatting_weight) +
            (readability_details.flesch_reading_ease * readability_weight)
        )
        ats_score = max(10, min(100, int(round(weighted_score))))

        # 7. AI suggestions
        ai_suggestions = self.generate_ai_suggestions(resume, job_description)

        # 8. Benchmark comparisons
        benchmark_details = self.generate_benchmark(ats_score)

        return ATSReportData(
            ats_score=ats_score,
            keyword_matching=keyword_details,
            formatting_analysis=formatting_details,
            readability_analysis=readability_details,
            grammar_analysis=grammar_details,
            action_verb_analysis=action_verbs_details,
            section_completeness=section_details,
            ai_suggestions=ai_suggestions,
            benchmark=benchmark_details
        )

    async def create_ats_report(
        self,
        user_id: uuid.UUID,
        resume_id: uuid.UUID,
        job_description: str,
        job_title: Optional[str] = None
    ) -> ATSReport:
        """
        Conducts evaluation against JD and persists the generated ATSReport into SQL database.
        """
        # Fetch actual resume content
        resume = await self.resume_repo.get(resume_id)
        if not resume:
            raise ValueError(f"Resume with ID {resume_id} does not exist.")

        # Run parser algorithms
        report_data_obj = self.analyze_resume_against_jd(resume, job_description, job_title)

        # Create SQLAlchemy schema model dictionary
        db_input = {
            "user_id": user_id,
            "resume_id": resume_id,
            "job_title": job_title or "Target Job Role",
            "job_description": job_description,
            "ats_score": report_data_obj.ats_score,
            "report_data": report_data_obj.model_dump()
        }

        # Create record in database
        db_report = await self.ats_repo.create(db_input, creator_id=str(user_id))
        return db_report

    async def get_report(self, report_id: uuid.UUID) -> Optional[ATSReport]:
        """
        Retrieves an ATS report by ID.
        """
        return await self.ats_repo.get(report_id)

    async def get_user_reports(self, user_id: uuid.UUID) -> List[ATSReport]:
        """
        Retrieves all historical reports generated by/for a specific user.
        """
        return await self.ats_repo.get_by_user_id(user_id)

    async def get_resume_history(self, resume_id: uuid.UUID) -> List[ATSReport]:
        """
        Retrieves historical performance records of a single resume to track score improvements over time.
        """
        return await self.ats_repo.get_by_resume_id(resume_id)

    async def delete_report(self, report_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        Deletes a report by marking deleted_at or removing it.
        """
        report = await self.ats_repo.get(report_id)
        if not report or report.user_id != user_id:
            return False
        return await self.ats_repo.delete(report_id, soft=True, initiator=str(user_id))

    async def compare_two_resumes(
        self,
        resume_a_id: uuid.UUID,
        resume_b_id: uuid.UUID,
        job_description: str
    ) -> ResumeComparisonResponse:
        """
        Runs side-by-side comparison of two distinct resumes against a target job description.
        """
        resume_a = await self.resume_repo.get(resume_a_id)
        resume_b = await self.resume_repo.get(resume_b_id)

        if not resume_a or not resume_b:
            raise ValueError("One or both resumes do not exist.")

        # Evaluate individual profiles
        analysis_a = self.analyze_resume_against_jd(resume_a, job_description)
        analysis_b = self.analyze_resume_against_jd(resume_b, job_description)

        # Skill and keyword intersection mapping
        keywords_a = set(analysis_a.keyword_matching.matched_keywords)
        keywords_b = set(analysis_b.keyword_matching.matched_keywords)

        common_skills = list(keywords_a.intersection(keywords_b))
        unique_a = list(keywords_a.difference(keywords_b))
        unique_b = list(keywords_b.difference(keywords_a))

        # Comparative analytics mapping
        score_comp = {
            "overall": ScoreMetricComparison(
                score_a=float(analysis_a.ats_score),
                score_b=float(analysis_b.ats_score),
                comparison_notes="Resume A scores higher overall." if analysis_a.ats_score > analysis_b.ats_score else "Resume B scores higher overall." if analysis_b.ats_score > analysis_a.ats_score else "Both resumes score identically."
            ),
            "keywords": ScoreMetricComparison(
                score_a=analysis_a.keyword_matching.keyword_match_percentage,
                score_b=analysis_b.keyword_matching.keyword_match_percentage,
                comparison_notes=f"Resume A matched {len(keywords_a)} keywords, Resume B matched {len(keywords_b)}."
            ),
            "readability": ScoreMetricComparison(
                score_a=analysis_a.readability_analysis.flesch_reading_ease,
                score_b=analysis_b.readability_analysis.flesch_reading_ease,
                comparison_notes=f"Resume A rating is {analysis_a.readability_analysis.readability_rating}, Resume B is {analysis_b.readability_analysis.readability_rating}."
            ),
            "completeness": ScoreMetricComparison(
                score_a=analysis_a.section_completeness.completeness_percentage,
                score_b=analysis_b.section_completeness.completeness_percentage,
                comparison_notes=f"Resume A present: {len(analysis_a.section_completeness.present_sections)} sections. Resume B present: {len(analysis_b.section_completeness.present_sections)}."
            )
        }

        winner = "Resume A" if analysis_a.ats_score > analysis_b.ats_score else "Resume B" if analysis_b.ats_score > analysis_a.ats_score else "Both resumes"
        summary = f"Comparative evaluation complete. {winner} shows better keyword integration and style metrics alignment for this target position."

        return ResumeComparisonResponse(
            resume_a_id=resume_a_id,
            resume_b_id=resume_b_id,
            common_skills=common_skills,
            unique_skills_a=unique_a,
            unique_skills_b=unique_b,
            ats_score_a=analysis_a.ats_score,
            ats_score_b=analysis_b.ats_score,
            score_comparison=score_comp,
            comparison_summary=summary
        )
