from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

class AICareerAssistantMessageCreate(BaseModel):
    role: str
    content: str
    metadata_json: Optional[Dict[str, Any]] = None

class AICareerAssistantMessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class AICareerAssistantSessionCreate(BaseModel):
    title: str = "New Conversation"
    context_data: Optional[Dict[str, Any]] = None

class AICareerAssistantSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    context_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CareerMemoryCreate(BaseModel):
    key: str
    value: str
    category: str = "general"
    confidence: int = 100
    source: Optional[str] = None

class CareerMemoryResponse(BaseModel):
    id: uuid.UUID
    key: str
    value: str
    category: str
    confidence: int
    source: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class CareerGoalCreate(BaseModel):
    title: str
    description: Optional[str] = None
    target_date: Optional[datetime] = None
    status: str = "in_progress"
    progress_percentage: int = 0
    milestones: Optional[Dict[str, Any]] = None

class CareerGoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[datetime] = None
    status: Optional[str] = None
    progress_percentage: Optional[int] = None
    milestones: Optional[Dict[str, Any]] = None

class CareerGoalResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    target_date: Optional[datetime]
    status: str
    progress_percentage: int
    milestones: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CareerHabitCreate(BaseModel):
    title: str
    frequency: str = "daily"

class CareerHabitResponse(BaseModel):
    id: uuid.UUID
    title: str
    frequency: str
    streak: int
    last_completed: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class CareerTimelineEventCreate(BaseModel):
    event_date: datetime
    title: str
    description: Optional[str] = None
    category: str = "milestone"
    metadata_json: Optional[Dict[str, Any]] = None

class CareerTimelineEventResponse(BaseModel):
    id: uuid.UUID
    event_date: datetime
    title: str
    description: Optional[str]
    category: str
    metadata_json: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True

class CareerDocumentCreate(BaseModel):
    name: str
    document_type: str
    file_url: str
    size_bytes: int = 0

class CareerDocumentResponse(BaseModel):
    id: uuid.UUID
    name: str
    document_type: str
    file_url: str
    size_bytes: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class AIWorkspaceProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    workspace_data: Optional[Dict[str, Any]] = None

class AIWorkspaceProjectResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    workspace_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
