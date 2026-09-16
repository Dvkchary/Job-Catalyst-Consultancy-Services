import logging
import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import (
    get_current_active_user,
    get_dashboard_service,
    get_platform_analytics_service,
    get_report_service,
    get_export_service
)
from app.models.auth import User
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    CompleteAnalyticsResponse,
    WidgetResponse,
    WidgetBulkLayoutUpdate,
    ReportGenerateRequest,
    ExecutiveReportResponse,
    ReportExportResponse
)
from app.services.dashboard import (
    DashboardService,
    PlatformAnalyticsService,
    ReportService,
    ExportService
)

logger = logging.getLogger("app.api.dashboard")

router = APIRouter(prefix="/dashboard", tags=["Enterprise Dashboard & Analytics"])


@router.get("/summary", response_model=DashboardSummaryResponse, status_code=status.HTTP_200_OK)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_active_user),
    dashboard_svc: DashboardService = Depends(get_dashboard_service)
) -> Any:
    """
    Retrieves the customized candidate dashboard welcome screen, status summaries,
    recent activity logs, and system recommended quick actions.
    """
    try:
        return await dashboard_svc.get_summary(user_id=current_user.id)
    except Exception as e:
        logger.error(f"Error fetching dashboard summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve enterprise dashboard summary."
        )


@router.get("/analytics", response_model=CompleteAnalyticsResponse, status_code=status.HTTP_200_OK)
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_active_user),
    analytics_svc: PlatformAnalyticsService = Depends(get_platform_analytics_service)
) -> Any:
    """
    Returns complete multi-module analytics datasets, calculating actual ATS trends,
    funnel response ratios, mock interview averages, and real-time AI spending.
    """
    try:
        return await analytics_svc.get_all_analytics(user_id=current_user.id)
    except Exception as e:
        logger.error(f"Error compiling analytics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not aggregate multi-module performance analytics."
        )


@router.get("/widgets", response_model=List[WidgetResponse], status_code=status.HTTP_200_OK)
async def get_dashboard_widgets(
    current_user: User = Depends(get_current_active_user),
    dashboard_svc: DashboardService = Depends(get_dashboard_service)
) -> Any:
    """
    Lists current customized dashboard widgets and initiates defaults if none exist.
    """
    try:
        return await dashboard_svc.get_or_create_widgets(user_id=current_user.id)
    except Exception as e:
        logger.error(f"Error loading widgets: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load customized workspace layouts."
        )


@router.put("/widgets/layout", response_model=List[WidgetResponse], status_code=status.HTTP_200_OK)
async def update_widget_layouts(
    payload: List[WidgetBulkLayoutUpdate],
    current_user: User = Depends(get_current_active_user),
    dashboard_svc: DashboardService = Depends(get_dashboard_service)
) -> Any:
    """
    Saves new drag-and-drop coordinate layouts for customized user dashboards in bulk.
    """
    try:
        updates = [item.model_dump() for item in payload]
        return await dashboard_svc.update_bulk_layouts(user_id=current_user.id, updates=updates)
    except Exception as e:
        logger.error(f"Error updating layout coordinates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save bulk workspace grid updates."
        )


@router.post("/reports", response_model=ExecutiveReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_executive_report(
    payload: ReportGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    report_svc: ReportService = Depends(get_report_service)
) -> Any:
    """
    Compiles and registers a new Weekly, Monthly, or Specialized coaching report.
    """
    try:
        return await report_svc.generate_report(user_id=current_user.id, payload=payload)
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not compile reporting metrics."
        )


@router.get("/reports", response_model=List[ExecutiveReportResponse], status_code=status.HTTP_200_OK)
async def list_executive_reports(
    current_user: User = Depends(get_current_active_user),
    report_svc: ReportService = Depends(get_report_service)
) -> Any:
    """
    Retrieves all historic Weekly, Monthly, and Coaching audits generated for the user.
    """
    try:
        return await report_svc.report_repo.get_by_user_id(user_id=current_user.id)
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not load historical reports."
        )


@router.get("/reports/{report_id}/export/pdf", response_model=ReportExportResponse, status_code=status.HTTP_200_OK)
async def export_report_to_pdf(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    export_svc: ExportService = Depends(get_export_service)
) -> Any:
    """
    Triggers formatting of an executive report into a downloadable PDF document stream.
    """
    try:
        return await export_svc.export_pdf_b64(user_id=current_user.id, report_id=report_id)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err)
        )
    except Exception as e:
        logger.error(f"Error exporting PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download for PDF format."
        )


@router.get("/reports/{report_id}/export/excel", response_model=ReportExportResponse, status_code=status.HTTP_200_OK)
async def export_report_to_excel(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    export_svc: ExportService = Depends(get_export_service)
) -> Any:
    """
    Triggers formatting of an executive report into a downloadable Excel/CSV sheet stream.
    """
    try:
        return await export_svc.export_excel_b64(user_id=current_user.id, report_id=report_id)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err)
        )
    except Exception as e:
        logger.error(f"Error exporting Excel: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download for Excel format."
        )
