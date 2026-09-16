import logging
import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_active_user, get_workflow_service
from app.models.auth import User
from app.schemas.workflow import (
    WorkflowResponse,
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowExecutionResponse,
    WorkflowExecuteRequest,
    WorkflowTemplateResponse,
    WorkflowLogResponse
)
from app.services.workflow_service import WorkflowService

logger = logging.getLogger("app.api.workflow")

router = APIRouter(prefix="/workflow", tags=["Enterprise AI Workflows & Automation Engine"])


# ==============================================================================
# Workflow definitions endpoints (CRUD)
# ==============================================================================
@router.get("/list", response_model=List[WorkflowResponse], status_code=status.HTTP_200_OK)
async def list_workflows(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    wf_svc: WorkflowService = Depends(get_workflow_service)
) -> Any:
    """
    Retrieves all active workflows configured by the current enterprise user.
    """
    try:
        return await wf_svc.get_workflows(user_id=current_user.id, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error fetching workflows: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve custom workflows."
        )


@router.post("/create", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    payload: WorkflowCreate,
    current_user: User = Depends(get_current_active_user),
    wf_svc: WorkflowService = Depends(get_workflow_service)
) -> Any:
    """
    Creates a custom workflow schema/definition mapping triggers and sequential execution actions.
    """
    try:
        return await wf_svc.create_workflow(user_id=current_user.id, obj_in=payload.model_dump())
    except Exception as e:
        logger.error(f"Error creating workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize new workflow definition."
        )


@router.get("/{workflow_id}", response_model=WorkflowResponse, status_code=status.HTTP_200_OK)
async def get_workflow(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    wf_svc: WorkflowService = Depends(get_workflow_service)
) -> Any:
    """
    Retrieves a single workflow structure by its unique UUID.
    """
    wf = await wf_svc.get_workflow(workflow_id)
    if not wf or wf.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found or access denied."
        )
    return wf


@router.put("/{workflow_id}", response_model=WorkflowResponse, status_code=status.HTTP_200_OK)
async def update_workflow(
    workflow_id: uuid.UUID,
    payload: WorkflowUpdate,
    current_user: User = Depends(get_current_active_user),
    wf_svc: WorkflowService = Depends(get_workflow_service)
) -> Any:
    """
    Updates properties or step action configurations on a custom workflow definition.
    """
    wf = await wf_svc.get_workflow(workflow_id)
    if not wf or wf.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found or access denied."
        )
    
    updated = await wf_svc.update_workflow(workflow_id, payload.model_dump(exclude_unset=True))
    return updated


@router.delete("/{workflow_id}", status_code=status.HTTP_200_OK)
async def delete_workflow(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    wf_svc: WorkflowService = Depends(get_workflow_service)
) -> Any:
    """
    Soft-deletes an existing custom workflow definition.
    """
    wf = await wf_svc.get_workflow(workflow_id)
    if not wf or wf.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found or access denied."
        )
        
    await wf_svc.delete_workflow(workflow_id)
    return {"success": True, "message": "Workflow successfully deleted."}


# ==============================================================================
# Workflow Templates endpoints
# ==============================================================================
@router.get("/templates/list", response_model=List[WorkflowTemplateResponse], status_code=status.HTTP_200_OK)
async def list_templates(
    current_user: User = Depends(get_current_active_user),
    wf_svc: WorkflowService = Depends(get_workflow_service)
) -> Any:
    """
    Retrieves a collection of ready-to-use professional workflow templates.
    """
    try:
        return await wf_svc.get_templates()
    except Exception as e:
        logger.error(f"Error fetching templates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve pre-packaged templates."
        )


@router.post("/templates/import/{template_id}", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def import_from_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    wf_svc: WorkflowService = Depends(get_workflow_service)
) -> Any:
    """
    Imports and instantiates a workflow template into active user definition catalogs.
    """
    wf = await wf_svc.import_workflow_from_template(user_id=current_user.id, template_id=template_id)
    if not wf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or could not be loaded."
        )
    return wf


# ==============================================================================
# Workflow execution trigger endpoints
# ==============================================================================
@router.post("/trigger/{workflow_id}", response_model=WorkflowExecutionResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_workflow(
    workflow_id: uuid.UUID,
    payload: WorkflowExecuteRequest,
    current_user: User = Depends(get_current_active_user),
    wf_svc: WorkflowService = Depends(get_workflow_service)
) -> Any:
    """
    Spawns a background asynchronous execution instance of the custom workflow.
    """
    wf = await wf_svc.get_workflow(workflow_id)
    if not wf or wf.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found or access denied."
        )
        
    execution = await wf_svc.trigger_workflow(
        workflow_id=workflow_id,
        user_id=current_user.id,
        initial_context=payload.initial_context,
        trigger_source=payload.trigger_source
    )
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow is inactive or failed to execute."
        )
    return execution


# ==============================================================================
# Execution history / state monitoring endpoints
# ==============================================================================
@router.get("/execution/history", response_model=List[WorkflowExecutionResponse], status_code=status.HTTP_200_OK)
async def list_execution_history(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    wf_svc: WorkflowService = Depends(get_workflow_service)
) -> Any:
    """
    Retrieves full execution audit history records.
    """
    try:
        return await wf_svc.get_execution_history(user_id=current_user.id, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error fetching execution history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve execution runs history."
        )


@router.get("/execution/{execution_id}", response_model=WorkflowExecutionResponse, status_code=status.HTTP_200_OK)
async def get_execution_status(
    execution_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    wf_svc: WorkflowService = Depends(get_workflow_service)
) -> Any:
    """
    Fetches real-time execution status indices, progress indices, and state variables.
    """
    exec_obj = await wf_svc.get_execution(execution_id)
    if not exec_obj or exec_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found or access denied."
        )
    return exec_obj


@router.get("/execution/{execution_id}/logs", response_model=List[WorkflowLogResponse], status_code=status.HTTP_200_OK)
async def get_execution_logs(
    execution_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    wf_svc: WorkflowService = Depends(get_workflow_service)
) -> Any:
    """
    Retrieves sequential logging messages compiled during execution.
    """
    exec_obj = await wf_svc.get_execution(execution_id)
    if not exec_obj or exec_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found or access denied."
        )
    return await wf_svc.get_execution_logs(execution_id)


@router.post("/execution/{execution_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_execution(
    execution_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    wf_svc: WorkflowService = Depends(get_workflow_service)
) -> Any:
    """
    Instructs the runtime scheduler to halt/cancel active execution sequences.
    """
    exec_obj = await wf_svc.get_execution(execution_id)
    if not exec_obj or exec_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found or access denied."
        )
        
    success = await wf_svc.cancel_execution(execution_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Execution cannot be cancelled (either already completed or not active)."
        )
    return {"success": True, "message": "Execution cancellation requested successfully."}


@router.post("/execution/{execution_id}/approve/{step_id}", status_code=status.HTTP_200_OK)
async def approve_step_approval(
    execution_id: uuid.UUID,
    step_id: str,
    approved: bool,
    current_user: User = Depends(get_current_active_user),
    wf_svc: WorkflowService = Depends(get_workflow_service)
) -> Any:
    """
    Resolves a paused approval condition block, directing the engine to resume remaining steps.
    """
    exec_obj = await wf_svc.get_execution(execution_id)
    if not exec_obj or exec_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found or access denied."
        )
        
    success = await wf_svc.approve_step(execution_id, step_id, approved)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to process approval (execution is not in paused/approval state)."
        )
    return {"success": True, "message": "Step resolution saved. Execution resumed."}
