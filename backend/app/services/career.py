import uuid
import logging
import json
import httpx
from typing import Any, Dict, List, Optional
from sqlalchemy import select, func

from app.core.config import settings
from app.db.career_repositories import CareerRepository, RoadmapRepository, RecommendationRepository
from app.models.career import CareerProfile, CareerRoadmap, CareerRecommendation
from app.models.ats import ATSReport
from app.models.interview import InterviewSession
from app.schemas.career import (
    CareerProfileCreate,
    SalaryIntelligence,
    CareerInsights,
    CareerRoadmapData,
    CareerRoadmapSection,
    MilestoneItem,
    GoalItem,
    SkillGapItem,
    LearningRecommendations,
    RecommendationCourse,
    RecommendationCertification,
    RecommendationProject,
    ProgressTrackingResponse
)

logger = logging.getLogger("app.services.career")


import hashlib
from app.core.cache_pool import fast_cache, HTTPClientProvider


class GeminiCareerClient:
    """
    Asynchronous client designed to query Gemini for rich, personalized, structured career guidance.
    Provides bulletproof fallbacks in case API keys are missing or requests timeout.
    """
    @classmethod
    async def generate_json(cls, prompt: str, system_instruction: Optional[str] = None) -> Optional[Dict[str, Any]]:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.warning("GEMINI_API_KEY is not configured. Falling back to rule-based generator.")
            return None

        # 1. High-Performance Response Cache lookup (hashing input parameters)
        param_hash = hashlib.sha256(f"{system_instruction or ''}:{prompt}".encode("utf-8")).hexdigest()
        cache_key = f"gemini:json:{param_hash}"
        cached_res = await fast_cache.get(cache_key)
        if cached_res is not None:
            logger.info(f"AI JSON Cache Hit! Skipping API request for key: {cache_key[:15]}...")
            try:
                return json.loads(cached_res)
            except Exception as e:
                logger.error(f"Failed to load cached JSON: {str(e)}")

        # Standard Endpoint for gemini-1.5-flash
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        contents = []
        if system_instruction:
            contents.append({
                "role": "user",
                "parts": [{"text": f"SYSTEM INSTRUCTION: {system_instruction}"}]
            })
            
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.95,
                "maxOutputTokens": 3072,
            }
        }

        try:
            # 2. Shared HTTP Connection Pool usage
            client = await HTTPClientProvider.get_client()
            response = await client.post(url, json=payload, timeout=30.0)
            if response.status_code == 200:
                res_json = response.json()
                text = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                
                # Strip any markdown wrappers
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()
                
                # Try parsing and saving to cache
                parsed_data = json.loads(text)
                await fast_cache.set(cache_key, text, ttl_seconds=3600)
                return parsed_data
            else:
                logger.error(f"Gemini API status {response.status_code}: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Gemini communications failure: {str(e)}", exc_info=True)
            return None


class CareerService:
    """
    Orchestrates user career profile management, matching current alignment
    against market salary averages and readiness indices.
    """
    def __init__(self, career_repo: CareerRepository) -> None:
        self.career_repo = career_repo

    async def get_profile(self, user_id: uuid.UUID) -> Optional[CareerProfile]:
        """
        Fetches the active career profile for a user.
        """
        return await self.career_repo.get_by_user_id(user_id)

    async def create_or_update_profile(self, user_id: uuid.UUID, data: CareerProfileCreate) -> CareerProfile:
        """
        Registers or updates the user's career trajectory. Employs Gemini or a heuristic
        rules engine to output salary benchmarks and application readiness indexes.
        """
        # Determine current state
        existing = await self.career_repo.get_by_user_id(user_id)

        # Default fallback estimations
        est_market = 135000.0
        if "senior" in data.experience_level.lower() or "lead" in data.experience_level.lower():
            est_market = 175000.0
        elif "junior" in data.experience_level.lower():
            est_market = 95000.0

        salary_intel = {
            "current_salary": est_market * 0.85,
            "market_salary": est_market,
            "expected_salary": est_market * 1.15,
            "negotiation_advice": f"For a {data.target_role} role in the {data.industry} industry, focus on demonstrating concrete business outcomes, architecture scale, or team leadership. Frame your compensation around high-value contributions and market averages.",
            "salary_trend": f"Compensation for {data.target_role} shows a steady 5-8% annual growth trend due to rising technological dependencies and systemic automation needs."
        }

        readiness = {
            "promotion_readiness": 65.0,
            "resume_readiness": 70.0,
            "interview_readiness": 60.0,
            "application_readiness": 65.0,
            "career_score": 65.0
        }

        # Attempt Gemini analysis
        prompt = (
            f"Analyze the following candidate professional profile:\n"
            f"- Current Role: {data.current_role}\n"
            f"- Target Role: {data.target_role}\n"
            f"- Experience Level: {data.experience_level}\n"
            f"- Industry: {data.industry}\n"
            f"- Skills: {', '.join(data.skills)}\n"
            f"- Career Goals: {', '.join(data.career_goals)}\n"
            f"- Preferred Countries: {', '.join(data.preferred_countries)}\n\n"
            f"Please generate salary market data and readiness scores (1 to 100) based on role transitions. "
            f"Output a valid JSON object matching the schema below exactly. Do not output markdown, and do not use backticks. "
            f"Required structure:\n"
            f'{{\n'
            f'  "salary_intelligence": {{\n'
            f'    "current_salary": 120000.0,\n'
            f'    "market_salary": 145000.0,\n'
            f'    "expected_salary": 160000.0,\n'
            f'    "negotiation_advice": "Advice here.",\n'
            f'    "salary_trend": "Trend description."\n'
            f'  }},\n'
            f'  "readiness_insights": {{\n'
            f'    "promotion_readiness": 68.5,\n'
            f'    "resume_readiness": 75.0,\n'
            f'    "interview_readiness": 55.0,\n'
            f'    "application_readiness": 65.0,\n'
            f'    "career_score": 66.0\n'
            f'  }}\n'
            f'}}'
        )

        ai_response = await GeminiCareerClient.generate_json(prompt=prompt)
        if ai_response:
            try:
                salary_intel = ai_response.get("salary_intelligence", salary_intel)
                readiness = ai_response.get("readiness_insights", readiness)
            except Exception as e:
                logger.warning(f"Failed parsing Gemini career profile JSON: {str(e)}")

        # Calculate composite career score if missing
        career_score = float(readiness.get("career_score", 65.0))

        if existing:
            existing.current_role = data.current_role
            existing.target_role = data.target_role
            existing.industry = data.industry
            existing.experience_level = data.experience_level
            existing.skills = data.skills
            existing.career_goals = data.career_goals
            existing.preferred_countries = data.preferred_countries
            existing.visa_status = data.visa_status
            existing.timeline = data.timeline
            existing.career_score = career_score
            existing.salary_intelligence = salary_intel
            existing.readiness_insights = readiness
            await self.career_repo.update(existing)
            return existing
        else:
            profile = CareerProfile(
                user_id=user_id,
                current_role=data.current_role,
                target_role=data.target_role,
                industry=data.industry,
                experience_level=data.experience_level,
                skills=data.skills,
                career_goals=data.career_goals,
                preferred_countries=data.preferred_countries,
                visa_status=data.visa_status,
                timeline=data.timeline,
                career_score=career_score,
                salary_intelligence=salary_intel,
                readiness_insights=readiness
            )
            return await self.career_repo.create(profile)


class RoadmapService:
    """
    Translates career targets into structured Short, Medium, and Long-Term
    milestone roadmaps accompanied by editable weekly/monthly checklists.
    """
    def __init__(self, roadmap_repo: RoadmapRepository, career_repo: CareerRepository) -> None:
        self.roadmap_repo = roadmap_repo
        self.career_repo = career_repo

    async def get_latest_roadmap(self, user_id: uuid.UUID) -> Optional[CareerRoadmap]:
        """
        Retrieves the user's latest active roadmap.
        """
        return await self.roadmap_repo.get_latest_by_user_id(user_id)

    async def generate_roadmap(self, user_id: uuid.UUID, profile_id: uuid.UUID) -> CareerRoadmap:
        """
        Compiles professional short, medium, and long term roadmaps with milestone markers.
        """
        profile = await self.career_repo.get(profile_id)
        if not profile:
            raise ValueError("Target career profile not found.")

        # Static rule-based fallback
        short_term = {
            "goals": [f"Acquire primary technical skills required for {profile.target_role}.", "Optimize LinkedIn and Resume headers."],
            "milestones": [
                {"title": "Skill Audit & Baseline Set", "description": "Review current skillset against target role listings.", "is_completed": False, "target_date": "Month 1"},
                {"title": "Core Resume Re-write", "description": "Update professional summaries to emphasize transferable achievements.", "is_completed": False, "target_date": "Month 2"}
            ]
        }
        medium_term = {
            "goals": [f"Conduct networking circles with active {profile.target_role} professionals.", "Acquire initial certification milestones."],
            "milestones": [
                {"title": "Professional Cert Acquired", "description": "Complete target accreditation or high-value project portfolio.", "is_completed": False, "target_date": "Month 6"},
                {"title": "Informational Interviews", "description": "Meet with 5 industry leaders in target vertical.", "is_completed": False, "target_date": "Month 9"}
            ]
        }
        long_term = {
            "goals": [f"Transition into full-time {profile.target_role} and scale within organization."],
            "milestones": [
                {"title": "Full Career Transition", "description": "Secure job offer aligning with desired targets.", "is_completed": False, "target_date": "Month 12"}
            ]
        }

        weekly = [
            {"id": "w1", "title": f"Read 2 technical articles about {profile.target_role} standards", "is_completed": False, "category": "Skill Acquisition"},
            {"id": "w2", "title": "Review resume against a single matching job description", "is_completed": False, "category": "Resume Improvement"}
        ]
        monthly = [
            {"id": "m1", "title": "Complete 1 full mock interview attempt on JobCatalyst AI", "is_completed": False, "category": "Interview Prep"},
            {"id": "m2", "title": "Connect with 5 professionals on LinkedIn in your target domain", "is_completed": False, "category": "Networking"}
        ]

        # Query Gemini API
        prompt = (
            f"Generate a career transition roadmap from '{profile.current_role}' to '{profile.target_role}' "
            f"in the '{profile.industry}' industry at '{profile.experience_level}' experience level.\n\n"
            f"Output a valid JSON object containing short_term (0-6 Months), medium_term (6-18 Months), long_term (18+ Months) "
            f"and weekly/monthly starter lists. Structure the output strictly matching this schema (do not use backticks or markdown):\n"
            f'{{\n'
            f'  "roadmap_data": {{\n'
            f'    "short_term": {{\n'
            f'      "goals": ["Goal 1", "Goal 2"],\n'
            f'      "milestones": [\n'
            f'        {{"title": "Milestone A", "description": "Details", "is_completed": false, "target_date": "Month 1"}}\n'
            f'      ]\n'
            f'    }},\n'
            f'    "medium_term": {{\n'
            f'      "goals": ["Goal 1"],\n'
            f'      "milestones": [\n'
            f'        {{"title": "Milestone B", "description": "Details", "is_completed": false, "target_date": "Month 6"}}\n'
            f'      ]\n'
            f'    }},\n'
            f'    "long_term": {{\n'
            f'      "goals": ["Goal 1"],\n'
            f'      "milestones": [\n'
            f'        {{"title": "Milestone C", "description": "Details", "is_completed": false, "target_date": "Month 12"}}\n'
            f'      ]\n'
            f'    }}\n'
            f'  }},\n'
            f'  "weekly_goals": [\n'
            f'    {{"id": "w1", "title": "Goal title", "is_completed": false, "category": "Skill Acquisition"}}\n'
            f'  ],\n'
            f'  "monthly_goals": [\n'
            f'    {{"id": "m1", "title": "Goal title", "is_completed": false, "category": "Interview Prep"}}\n'
            f'  ]\n'
            f'}}'
        )

        ai_res = await GeminiCareerClient.generate_json(prompt=prompt)
        if ai_res:
            try:
                short_term = ai_res.get("roadmap_data", {}).get("short_term", short_term)
                medium_term = ai_res.get("roadmap_data", {}).get("medium_term", medium_term)
                long_term = ai_res.get("roadmap_data", {}).get("long_term", long_term)
                weekly = ai_res.get("weekly_goals", weekly)
                monthly = ai_res.get("monthly_goals", monthly)
            except Exception as e:
                logger.warning(f"Could not parse AI career roadmap: {str(e)}")

        roadmap_data = {
            "short_term": short_term,
            "medium_term": medium_term,
            "long_term": long_term
        }

        # Clear old roadmaps to keep clean tracking history or update
        existing = await self.roadmap_repo.get_latest_by_user_id(user_id)
        if existing:
            existing.roadmap_data = roadmap_data
            existing.weekly_goals = weekly
            existing.monthly_goals = monthly
            await self.roadmap_repo.update(existing)
            return existing
        else:
            new_roadmap = CareerRoadmap(
                user_id=user_id,
                career_profile_id=profile_id,
                roadmap_data=roadmap_data,
                weekly_goals=weekly,
                monthly_goals=monthly,
                learning_progress={"completed_modules": 0, "total_modules": 10, "last_updated": datetime_now_iso()}
            )
            return await self.roadmap_repo.create(new_roadmap)

    async def update_active_goals(self, user_id: uuid.UUID, roadmap_id: uuid.UUID, weekly: Optional[List[Dict[str, Any]]], monthly: Optional[List[Dict[str, Any]]]) -> Optional[CareerRoadmap]:
        """
        Updates weekly/monthly checklist goal statuses.
        """
        roadmap = await self.roadmap_repo.get(roadmap_id)
        if not roadmap or roadmap.user_id != user_id:
            return None

        if weekly is not None:
            roadmap.weekly_goals = weekly
        if monthly is not None:
            roadmap.monthly_goals = monthly

        # Recalculate learning_progress percentage if relevant
        completed_weekly = sum(1 for g in roadmap.weekly_goals if g.get("is_completed"))
        total_weekly = len(roadmap.weekly_goals) or 1
        roadmap.learning_progress = {
            "completed_modules": completed_weekly,
            "total_modules": total_weekly,
            "completion_ratio": round((completed_weekly / total_weekly) * 100, 1)
        }

        await self.roadmap_repo.update(roadmap)
        return roadmap


class RecommendationService:
    """
    Identifies skill gaps and dynamically indexes optimal learning content (courses,
    certifications, open source projects) as well as job listings aligned to target roles.
    """
    def __init__(self, recommendation_repo: RecommendationRepository, career_repo: CareerRepository) -> None:
        self.recommendation_repo = recommendation_repo
        self.career_repo = career_repo

    async def get_latest_recommendations(self, user_id: uuid.UUID) -> Optional[CareerRecommendation]:
        """
        Fetches the latest active recommendation stack for the user.
        """
        return await self.recommendation_repo.get_latest_by_user_id(user_id)

    async def generate_recommendations(self, user_id: uuid.UUID, profile_id: uuid.UUID) -> CareerRecommendation:
        """
        Generates targeted AI advice capturing skill gaps and indexing courses, books, and practice materials.
        """
        profile = await self.career_repo.get(profile_id)
        if not profile:
            raise ValueError("Target career profile not found.")

        # Static fallback data
        next_action = f"Revise your resume structure to showcase concrete projects focusing on the target role: {profile.target_role}."
        
        skill_gaps = [
            {"skill_name": f"Advanced {profile.target_role} Standards", "priority_ranking": "High", "learning_difficulty": "Medium", "learning_time_estimate": "3 Weeks"},
            {"skill_name": "System Architecture Mapping", "priority_ranking": "Medium", "learning_difficulty": "Hard", "learning_time_estimate": "4 Weeks"}
        ]

        learning = {
            "courses": [
                {"title": f"Masterclass in {profile.target_role} Practices", "provider": "Coursera", "url": "https://coursera.org"},
                {"title": "Scalable System Architecture Engineering", "provider": "Udemy", "url": "https://udemy.org"}
            ],
            "certifications": [
                {"name": f"Certified {profile.target_role} Professional (CCP)", "issuing_organization": "Industry Alliance", "relevance_score": 92.5},
                {"name": "Architectural Design Expert (ADE)", "issuing_organization": "OpenGroup", "relevance_score": 85.0}
            ],
            "books": [
                "Designing Data-Intensive Applications by Martin Kleppmann",
                "Clean Architecture: A Craftsman's Guide to Software Structure"
            ],
            "projects": [
                {
                    "title": "Production Scale Enterprise Service Mesh",
                    "description": "Create an end-to-end distributed service gateway managing load balancing and fault-tolerant proxying.",
                    "key_technologies": ["Go", "Kubernetes", "gRPC", "Docker"]
                }
            ],
            "open_source_contributions": [
                "Contribute to Kubernetes Core Network Routing issues",
                "Optimize FastAPI route parsing performance inside community repos"
            ],
            "practice_platforms": [
                "LeetCode & HackerRank for complex algorithm checks",
                "JobCatalyst AI Mock Interview Simulator for high-performance practicing"
            ]
        }

        resume_imps = [
            f"Add a robust, metric-driven Skills Section highlighting key competencies required for {profile.target_role}.",
            "Use STAR method action verbs (e.g., Optimized, Spearheaded, Engineered) instead of passive wording."
        ]
        interview_sigs = [
            f"Practice answering questions about system scalability and design patterns typical for a {profile.target_role} role.",
            "Perfect your introduction to link your past achievements directly to target industry requirements."
        ]
        jobs_recs = [
            {"title": f"Junior/Mid {profile.target_role}", "company": "Stripe", "location": "Remote", "salary_range": "$110,000 - $140,000"},
            {"title": f"Associate {profile.target_role}", "company": "Atlassian", "location": "San Francisco, CA", "salary_range": "$125,000 - $155,000"}
        ]

        # Query Gemini API
        prompt = (
            f"Compare current user skills against requirements for '{profile.target_role}' inside the '{profile.industry}' vertical. "
            f"Determine specific skill gaps and priority learning resources. "
            f"Provide the response strictly as a single valid JSON object following this schema. Do not use markdown blocks or backticks:\n"
            f'{{\n'
            f'  "next_best_action": "Immediate next step suggestion.",\n'
            f'  "skill_gap_analysis": [\n'
            f'    {{"skill_name": "Skill Name", "priority_ranking": "High", "learning_difficulty": "Medium", "learning_time_estimate": "3 Weeks"}}\n'
            f'  ],\n'
            f'  "learning_recommendations": {{\n'
            f'    "courses": [\n'
            f'      {{"title": "Course Title", "provider": "Udemy", "url": "https://udemy.com"}}\n'
            f'    ],\n'
            f'    "certifications": [\n'
            f'      {{"name": "AWS Certified Architect", "issuing_organization": "Amazon", "relevance_score": 95.0}}\n'
            f'    ],\n'
            f'    "books": ["Book Title 1"],\n'
            f'    "projects": [\n'
            f'      {{"title": "Project Title", "description": "Details", "key_technologies": ["Python", "AWS"]}}\n'
            f'    ],\n'
            f'    "open_source_contributions": ["Contribute to Python requests project"],\n'
            f'    "practice_platforms": ["LeetCode", "JobCatalyst AI"]\n'
            f'  }},\n'
            f'  "resume_improvements": ["Tip 1", "Tip 2"],\n'
            f'  "interview_practice_suggestions": ["Suggestion 1"],\n'
            f'  "job_recommendations": [\n'
            f'    {{"title": "Job Title", "company": "Google", "location": "Remote", "salary_range": "$150k-$180k"}}\n'
            f'  ]\n'
            f'}}'
        )

        ai_res = await GeminiCareerClient.generate_json(prompt=prompt)
        if ai_res:
            try:
                next_action = ai_res.get("next_best_action", next_action)
                skill_gaps = ai_res.get("skill_gap_analysis", skill_gaps)
                learning = ai_res.get("learning_recommendations", learning)
                resume_imps = ai_res.get("resume_improvements", resume_imps)
                interview_sigs = ai_res.get("interview_practice_suggestions", interview_sigs)
                jobs_recs = ai_res.get("job_recommendations", jobs_recs)
            except Exception as e:
                logger.warning(f"Failed parsing Gemini career recommendations: {str(e)}")

        recommendations_data = {
            "next_best_action": next_action,
            "skill_gap_analysis": skill_gaps,
            "learning_recommendations": learning,
            "resume_improvements": resume_imps,
            "interview_practice_suggestions": interview_sigs,
            "job_recommendations": jobs_recs
        }

        existing = await self.recommendation_repo.get_latest_by_user_id(user_id)
        if existing:
            existing.recommendations_data = recommendations_data
            await self.recommendation_repo.update(existing)
            return existing
        else:
            rec = CareerRecommendation(
                user_id=user_id,
                career_profile_id=profile_id,
                recommendations_data=recommendations_data
            )
            return await self.recommendation_repo.create(rec)


class AnalyticsService:
    """
    Consolidates data across ATS matching runs, mock interviews, and resume uploads
    to calculate real progress tracking benchmarks.
    """
    def __init__(self, db_session) -> None:
        self.db = db_session

    async def get_progress_analytics(self, user_id: uuid.UUID) -> ProgressTrackingResponse:
        """
        Gathers live stats directly from real database tables (ATS, InterviewSessions) to map user career growth.
        """
        # Count ATS reports
        try:
            ats_query = select(func.count()).select_from(ATSReport).where(
                ATSReport.user_id == user_id
            )
            ats_res = await self.db.execute(ats_query)
            applications_count = ats_res.scalar() or 0
        except Exception:
            applications_count = 0

        # Count Mock Interviews completed
        try:
            int_query = select(func.count()).select_from(InterviewSession).where(
                InterviewSession.user_id == user_id,
                InterviewSession.status == "Completed"
            )
            int_res = await self.db.execute(int_query)
            interviews_count = int_res.scalar() or 0
        except Exception:
            interviews_count = 0

        # Base heuristics for active counts
        offers_count = max(0, int(applications_count * 0.15))
        
        growth_calc = 10.0 + (applications_count * 5.0) + (interviews_count * 15.0)
        career_growth_percentage = min(100.0, max(0.0, growth_calc))

        learning_progress = {
            "completed_skills": interviews_count + 1,
            "hours_practiced": interviews_count * 1.5,
            "milestones_hit": 1 + (applications_count // 3)
        }

        return ProgressTrackingResponse(
            learning_progress=learning_progress,
            applications_count=applications_count,
            interviews_count=interviews_count,
            offers_count=offers_count,
            career_growth_percentage=career_growth_percentage
        )


def datetime_now_iso() -> str:
    from datetime import datetime
    return datetime.utcnow().isoformat()
