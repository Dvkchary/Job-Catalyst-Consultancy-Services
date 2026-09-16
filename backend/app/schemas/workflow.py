import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ==============================================================================
# Workflow Log Schemas
# ==============================================================================
class WorkflowLogResponse(BaseModel):
    id: uuid.UUID
    execution_id: uuid.UUID
    step_name: str
    level: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# Workflow Execution Schemas
# ==============================================================================
class WorkflowExecutionResponse(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    user_id: uuid.UUID
    status: str
    trigger_source: str
    current_step_index: int
    context_data: Dict[str, Any]
    steps_state: Dict[str, Any]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkflowExecuteRequest(BaseModel):
    trigger_source: str = Field("MANUAL", description="The origin source initiating this run (MANUAL, API, SCHEDULED, EVENT)")
    initial_context: Dict[str, Any] = Field(default_factory=dict, description="Payload key-value parameters injected as initial context")


# ==============================================================================
# Workflow Definition Schemas
# ==============================================================================
class WorkflowBase(BaseModel):
    name: str = Field(..., max_length=150, description="Friendly identifier name for the custom workflow")
    description: Optional[str] = Field(None, max_length=500, description="Detailed statement explaining what automation this handles")
    trigger_type: str = Field("MANUAL", description="Trigger model types: MANUAL, SCHEDULED, EVENT_DRIVEN, API, WEBHOOK")
    trigger_config: Dict[str, Any] = Field(default_factory=dict, description="Configuration parameters mapping: e.g. {'cron': '0 9 * * 1'}")
    definition: Dict[str, Any] = Field(default_factory=dict, description="SaaS visual JSON flow definition representing actions/conditions block array")
    is_active: bool = Field(True, description="Toggle whether schedule triggers are active")
    status: str = Field("ACTIVE", description="DRAFT, ACTIVE, PAUSED lifecycle parameters")


class WorkflowCreate(WorkflowBase):
    pass


class WorkflowUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = Field(None, max_length=500)
    trigger_type: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    definition: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    status: Optional[str] = None


class WorkflowResponse(WorkflowBase):
    id: uuid.UUID
    user_id: uuid.UUID
    last_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# Workflow Template Schemas
# ==============================================================================
class WorkflowTemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    category: str
    trigger_type: str
    trigger_config: Dict[str, Any]
    definition: Dict[str, Any]
    is_system: bool

    class Config:
        from_attributes = True


class WorkflowTemplateCreate(BaseModel):
    name: str = Field(..., max_length=150)
    description: Optional[str] = Field(None, max_length=500)
    category: str
    trigger_type: str = "MANUAL"
    trigger_config: Dict[str, Any] = Field(default_factory=dict)
    definition: Dict[str, Any] = Field(default_factory=dict)
    is_system: bool = False


# ==============================================================================
# Import / Export DSL Schemas
# ==============================================================================
class WorkflowImportRequest(BaseModel):
    name: str = Field(..., max_length=150)
    description: Optional[str] = Field(None, max_length=500)
    trigger_type: str = "MANUAL"
    trigger_config: Dict[str, Any] = Field(default_factory=dict)
    definition: Dict[str, Any] = Field(default_factory=dict)


class WorkflowValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
