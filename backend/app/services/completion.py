from typing import List
from app.models.profile import UserProfile
from app.schemas.profile import ProfileCompletionRecommendation, ProfileCompletionStatus


class ProfileCompletionEngine:
    """
    Decoupled logical engine responsible for evaluating Profile Completion strength,
    detecting missing fields, and generating priority-based actionable tips.
    """

    @staticmethod
    def evaluate(profile: UserProfile) -> ProfileCompletionStatus:
        """
        Calculates user profile completeness score based on predefined functional weights:
        - Personal identity (first/last name, phone)   : 10%
        - Professional intro (headline, bio)           : 15%
        - Work Experience (at least 1 record)          : 20%
        - Academic Education (at least 1 record)       : 15%
        - Core Technical Skills (at least 3 skill items): 15%
        - Certifications & Credentials (at least 1)    : 10%
        - Digital Social Footprint (Github/LinkedIn)    : 10%
        - Career Targets (roles, locations, salary)     : 5%
        Total: 100%
        """
        score = 0
        missing_fields: List[str] = []
        recommendations: List[ProfileCompletionRecommendation] = []

        # 1. Personal Identity (10%)
        has_name = bool(profile.first_name and profile.last_name)
        if has_name:
            score += 10
        else:
            missing_fields.append("first_name_and_last_name")
            recommendations.append(
                ProfileCompletionRecommendation(
                    section="Personal Info",
                    priority="HIGH",
                    tip="Add your real first and last name so recruiters can recognize you instantly."
                )
            )

        # 2. Professional Intro (15%)
        has_intro = bool(profile.headline and profile.bio)
        if has_intro:
            score += 15
        else:
            missing_fields.append("headline_and_bio")
            recommendations.append(
                ProfileCompletionRecommendation(
                    section="About Me",
                    priority="HIGH",
                    tip="Draft a professional headline and summary bio detailing your core career drive."
                )
            )

        # 3. Work Experience (20%)
        if profile.experience and len(profile.experience) > 0:
            score += 20
        else:
            missing_fields.append("experience")
            recommendations.append(
                ProfileCompletionRecommendation(
                    section="Experience",
                    priority="HIGH",
                    tip="List your previous employment experience to showcase your hands-on career achievements."
                )
            )

        # 4. Academic Education (15%)
        if profile.education and len(profile.education) > 0:
            score += 15
        else:
            missing_fields.append("education")
            recommendations.append(
                ProfileCompletionRecommendation(
                    section="Education",
                    priority="MEDIUM",
                    tip="Incorporate your academic background, degrees, and graduation institutions."
                )
            )

        # 5. Technical Skills (15%)
        skills_count = len(profile.skills) if profile.skills else 0
        if skills_count >= 3:
            score += 15
        else:
            score += min(15, skills_count * 5)  # 5% per skill up to 3
            missing_fields.append("skills")
            recommendations.append(
                ProfileCompletionRecommendation(
                    section="Skills",
                    priority="MEDIUM",
                    tip="Add at least 3 core technical skills to optimize your resume discovery match indexes."
                )
            )

        # 6. Certifications (10%)
        if profile.certifications and len(profile.certifications) > 0:
            score += 10
        else:
            missing_fields.append("certifications")
            recommendations.append(
                ProfileCompletionRecommendation(
                    section="Certifications",
                    priority="LOW",
                    tip="Feature your active industry certificates to stand out to matching recruiters."
                )
            )

        # 7. Social Links (10%)
        has_social = False
        if profile.social_links:
            has_social = bool(profile.social_links.get("linkedin") or profile.social_links.get("github"))
        
        if has_social:
            score += 10
        else:
            missing_fields.append("social_links")
            recommendations.append(
                ProfileCompletionRecommendation(
                    section="Socials",
                    priority="LOW",
                    tip="Connect your LinkedIn or GitHub accounts to present a validated engineering presence."
                )
            )

        # 8. Career Targets (5%)
        has_targets = bool(
            profile.preferred_roles and 
            profile.preferred_job_locations and 
            profile.preferred_salary and profile.preferred_salary.get("min_salary")
        )
        if has_targets:
            score += 5
        else:
            missing_fields.append("career_preferences")
            recommendations.append(
                ProfileCompletionRecommendation(
                    section="Preferences",
                    priority="LOW",
                    tip="Specify your role locations, salary ranges, and targeted titles to perfect recommendations."
                )
            )

        # Sort recommendations: HIGH, then MEDIUM, then LOW priority
        priority_map = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        recommendations.sort(key=lambda r: priority_map.get(r.priority, 3))

        return ProfileCompletionStatus(
            completion_percentage=score,
            missing_fields=missing_fields,
            recommendations=recommendations
        )
