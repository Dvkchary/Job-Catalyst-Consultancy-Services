import logging
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response

from app.core.dependencies import get_current_active_user, get_ats_service, get_resume_service
from app.models.auth import User
from app.schemas.ats import (
    ATSAnalysisRequest,
    ATSReportResponse,
    ResumeComparisonRequest,
    ResumeComparisonResponse,
    ATSReportData
)
from app.services.ats import ATSService
from app.services.resume import ResumeService
from app.utils.pdf import SimplePDFBuilder

logger = logging.getLogger("app.api.ats")

router = APIRouter(prefix="/ats", tags=["ATS Analysis Engine"])


def map_report_to_response(report) -> ATSReportResponse:
    """
    Utility mapper to translate raw ATSReport SQLAlchemy model back to structured Pydantic schemas.
    """
    raw_data = report.report_data
    # Re-validate dictionary payload through ATSReportData schema
    report_data_obj = ATSReportData.model_validate(raw_data)
    
    return ATSReportResponse(
        id=report.id,
        resume_id=report.resume_id,
        job_title=report.job_title,
        job_description=report.job_description,
        ats_score=report.ats_score,
        report_data=report_data_obj,
        created_at=report.created_at
    )


@router.post("/analyze", response_model=ATSReportResponse, status_code=status.HTTP_201_CREATED)
async def analyze_resume_against_job_description(
    payload: ATSAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    ats_svc: ATSService = Depends(get_ats_service),
    resume_svc: ResumeService = Depends(get_resume_service),
) -> ATSReportResponse:
    """
    Performs on-demand ATS scan of an existing resume against a target job description.
    Persists results as an ATSReport and returns the evaluated dashboard.
    """
    resume = await resume_svc.get_by_id(payload.resume_id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specified resume not found."
        )
    if resume.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to analyze this resume."
        )

    try:
        report = await ats_svc.create_ats_report(
            user_id=current_user.id,
            resume_id=payload.resume_id,
            job_description=payload.job_description,
            job_title=payload.job_title
        )
        return map_report_to_response(report)
    except Exception as e:
        logger.error(f"ATS Evaluation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ATS Engine analysis crash: {str(e)}"
        )


@router.post("/compare", response_model=ResumeComparisonResponse, status_code=status.HTTP_200_OK)
async def compare_two_resumes_side_by_side(
    payload: ResumeComparisonRequest,
    current_user: User = Depends(get_current_active_user),
    ats_svc: ATSService = Depends(get_ats_service),
    resume_svc: ResumeService = Depends(get_resume_service),
) -> ResumeComparisonResponse:
    """
    Evaluates two of the user's resumes against a target job description to match skills gaps side-by-side.
    """
    for rid in (payload.resume_a_id, payload.resume_b_id):
        resume = await resume_svc.get_by_id(rid)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume {rid} not found."
            )
        if resume.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Unauthorized access to resume {rid}."
            )

    try:
        comparison = await ats_svc.compare_two_resumes(
            resume_a_id=payload.resume_a_id,
            resume_b_id=payload.resume_b_id,
            job_description=payload.job_description
        )
        return comparison
    except Exception as e:
        logger.error(f"ATS Comparison failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ATS Engine comparison failure: {str(e)}"
        )


@router.get("/reports/{id}", response_model=ATSReportResponse, status_code=status.HTTP_200_OK)
async def get_ats_report_by_id(
    id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    ats_svc: ATSService = Depends(get_ats_service),
) -> ATSReportResponse:
    """
    Retrieves a previously generated ATS analysis report.
    """
    report = await ats_svc.get_report(id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ATS Report not found."
        )
    if report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this report."
        )

    return map_report_to_response(report)


@router.get("/reports/{id}/pdf", status_code=status.HTTP_200_OK)
async def export_ats_report_to_pdf(
    id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    ats_svc: ATSService = Depends(get_ats_service),
) -> Response:
    """
    Generates and returns an elegant downloadable PDF of the evaluated ATS report.
    """
    report = await ats_svc.get_report(id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ATS Report not found."
        )
    if report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to export this report."
        )

    # Map database payload
    rep_obj = map_report_to_response(report)
    data = rep_obj.report_data

    # Compile layout sections for PDF printing
    sections = [
        (
            "1. OVERALL EVALUATION PERFORMANCE SUMMARY",
            [
                f"Overall Score: {data.ats_score} out of 100",
                f"Target Role: {rep_obj.job_title or 'Target Job Role'}",
                f"Benchmark Rating: {data.benchmark.rating} (Percentile Rank: {data.benchmark.user_percentile}%)",
                f"Industry Score Average: {data.benchmark.industry_average_score} out of 100"
            ]
        ),
        (
            "2. KEYWORD & SKILLS GAP AUDIT",
            [
                f"Keyword Match Ratio: {data.keyword_matching.keyword_match_percentage}%",
                "Matched Keywords Found: " + (", ".join(data.keyword_matching.matched_keywords) if data.keyword_matching.matched_keywords else "None"),
                "Missing Keywords (In JD but missing in Resume): " + (", ".join(data.keyword_matching.missing_keywords[:20]) if data.keyword_matching.missing_keywords else "None")
            ]
        ),
        (
            "3. STRUCTURAL FORMATTING COMPLIANCE",
            [
                f"Unsupported Fonts Present: {'Yes' if data.formatting_analysis.has_unsupported_fonts else 'No'}",
                f"Marginal Spacing Issue: {'Yes' if data.formatting_analysis.has_poor_margins else 'No'}",
                f"Complex Tables Detected: {'Yes' if data.formatting_analysis.has_complex_tables else 'No'}",
                f"Embedded Charts/Images Detected: {'Yes' if data.formatting_analysis.has_charts_or_images else 'No'}",
                "Identified Formatting Issues: " + "; ".join(data.formatting_analysis.issues)
            ]
        ),
        (
            "4. READABILITY & CLARITY METRICS",
            [
                f"Flesch Reading Ease Index: {data.readability_analysis.flesch_reading_ease}",
                f"Equivalent Target Audience Grade: {data.readability_analysis.grade_level}",
                f"Overall Readability Classification: {data.readability_analysis.readability_rating}"
            ]
        ),
        (
            "5. WRITING AND ACHIEVEMENT ACTIONS ANALYSIS",
            [
                f"Powerful Action Verbs Discovered: {data.action_verb_analysis.action_verbs_count}",
                "Verbs Utilized: " + (", ".join(data.action_verb_analysis.verbs_used) if data.action_verb_analysis.verbs_used else "None"),
                "Mechanical Suggestions: " + "; ".join(data.action_verb_analysis.suggestions)
            ]
        ),
        (
            "6. GRAMMAR AND MECHANICS REVIEW",
            [
                f"Mechanical Grammar Flags: {data.grammar_analysis.errors_detected}",
                "Issues Detected: " + "; ".join(data.grammar_analysis.issues),
                "Mechanics Optimization Advice: " + "; ".join(data.grammar_analysis.suggestions)
            ]
        ),
        (
            "7. CORE SECTION COMPLETENESS AUDIT",
            [
                f"Overall Sections Complete: {data.section_completeness.completeness_percentage}%",
                "Present Sections Found: " + (", ".join(data.section_completeness.present_sections) if data.section_completeness.present_sections else "None"),
                "Missing Essential Sections: " + (", ".join(data.section_completeness.missing_essential_sections) if data.section_completeness.missing_essential_sections else "None")
            ]
        ),
        (
            "8. AI STRATEGIC REWRITE SUGGESTIONS",
            data.ai_suggestions
        )
    ]

    title = f"ATS EVALUATION REPORT: {rep_obj.job_title or 'Job Description Compare'}"

    # Generate raw bytes
    pdf_builder = SimplePDFBuilder()
    pdf_bytes = pdf_builder.build_report_pdf(title=title, sections=sections)

    # Send response stream
    filename = f"ATS-Report-{rep_obj.id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )


@router.get("/resumes/{resume_id}/history", response_model=List[ATSReportResponse], status_code=status.HTTP_200_OK)
async def get_ats_improvement_history(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    ats_svc: ATSService = Depends(get_ats_service),
    resume_svc: ResumeService = Depends(get_resume_service),
) -> List[ATSReportResponse]:
    """
    Retrieves chronological timeline of all reports ran on a resume to showcase formatting and matching progress.
    """
    resume = await resume_svc.get_by_id(resume_id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found."
        )
    if resume.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to view this resume's history."
        )

    reports = await ats_svc.get_resume_history(resume_id)
    return [map_report_to_response(r) for r in reports]


@router.delete("/reports/{id}", status_code=status.HTTP_200_OK)
async def delete_ats_report_by_id(
    id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    ats_svc: ATSService = Depends(get_ats_service),
) -> dict:
    """
    Deletes a previously generated report.
    """
    deleted = await ats_svc.delete_report(id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or unauthorized deletion request."
        )
    return {"status": "success", "message": "ATS Report removed successfully."}
