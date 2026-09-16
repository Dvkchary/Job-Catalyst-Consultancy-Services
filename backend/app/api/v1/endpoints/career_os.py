import uuid
from typing import List, Any
from fastapi import APIRouter, Depends, status

from app.models.auth import User
from app.core.dependencies import get_current_active_user, get_career_os_service
from app.services.career_os import CareerOSService
from app.schemas.career_os import (
    AICareerAssistantSessionCreate, AICareerAssistantSessionResponse,
    AICareerAssistantMessageCreate, AICareerAssistantMessageResponse,
    CareerMemoryCreate, CareerMemoryResponse,
    CareerGoalCreate, CareerGoalUpdate, CareerGoalResponse,
    CareerHabitCreate, CareerHabitResponse,
    CareerTimelineEventCreate, CareerTimelineEventResponse,
    CareerDocumentCreate, CareerDocumentResponse,
    AIWorkspaceProjectCreate, AIWorkspaceProjectResponse
)

router = APIRouter(prefix="/career-os", tags=["AI Career OS"])

# --- AI Assistant ---
@router.post("/sessions", response_model=AICareerAssistantSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: AICareerAssistantSessionCreate,
    current_user: User = Depends(get_current_active_user),
    service: CareerOSService = Depends(get_career_os_service)
) -> Any:
    return await service.create_assistant_session(current_user.id, data)

@router.get("/sessions", response_model=List[AICareerAssistantSessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_active_user),
    service: CareerOSService = Depends(get_career_os_service)
) -> Any:
    return await service.get_assistant_sessions(current_user.id)

@router.post("/sessions/{session_id}/messages", response_model=AICareerAssistantMessageResponse)
async def add_message(
    session_id: uuid.UUID,
    data: AICareerAssistantMessageCreate,
    current_user: User = Depends(get_current_active_user),
    service: CareerOSService = Depends(get_career_os_service)
) -> Any:
    return await service.add_assistant_message(current_user.id, session_id, data)

# --- Career Memory ---
@router.post("/memories", response_model=CareerMemoryResponse, status_code=status.HTTP_201_CREATED)
async def add_memory(
    data: CareerMemoryCreate,
    current_user: User = Depends(get_current_active_user),
    service: CareerOSService = Depends(get_career_os_service)
) -> Any:
    return await service.add_memory(current_user.id, data)

@router.get("/memories", response_model=List[CareerMemoryResponse])
async def list_memories(
    current_user: User = Depends(get_current_active_user),
    service: CareerOSService = Depends(get_career_os_service)
) -> Any:
    return await service.get_memories(current_user.id)

# --- Goals ---
@router.post("/goals", response_model=CareerGoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    data: CareerGoalCreate,
    current_user: User = Depends(get_current_active_user),
    service: CareerOSService = Depends(get_career_os_service)
) -> Any:
    return await service.create_goal(current_user.id, data)

@router.get("/goals", response_model=List[CareerGoalResponse])
async def list_goals(
    current_user: User = Depends(get_current_active_user),
    service: CareerOSService = Depends(get_career_os_service)
) -> Any:
    return await service.get_goals(current_user.id)

@router.patch("/goals/{goal_id}", response_model=CareerGoalResponse)
async def update_goal(
    goal_id: uuid.UUID,
    data: CareerGoalUpdate,
    current_user: User = Depends(get_current_active_user),
    service: CareerOSService = Depends(get_career_os_service)
) -> Any:
    return await service.update_goal(current_user.id, goal_id, data)

# --- Habits ---
@router.post("/habits", response_model=CareerHabitResponse, status_code=status.HTTP_201_CREATED)
async def create_habit(
    data: CareerHabitCreate,
    current_user: User = Depends(get_current_active_user),
    service: CareerOSService = Depends(get_career_os_service)
) -> Any:
    return await service.create_habit(current_user.id, data)

@router.get("/habits", response_model=List[CareerHabitResponse])
async def list_habits(
    current_user: User = Depends(get_current_active_user),
    service: CareerOSService = Depends(get_career_os_service)
) -> Any:
    return await service.get_habits(current_user.id)

# --- Timeline ---
@router.post("/timeline", response_model=CareerTimelineEventResponse, status_code=status.HTTP_201_CREATED)
async def add_timeline_event(
    data: CareerTimelineEventCreate,
    current_user: User = Depends(get_current_active_user),
    service: CareerOSService = Depends(get_career_os_service)
) -> Any:
    return await service.add_timeline_event(current_user.id, data)

@router.get("/timeline", response_model=List[CareerTimelineEventResponse])
async def list_timeline(
    current_user: User = Depends(get_current_active_user),
    service: CareerOSService = Depends(get_career_os_service)
) -> Any:
    return await service.get_timeline(current_user.id)

# --- Documents ---
@router.post("/documents", response_model=CareerDocumentResponse, status_code=status.HTTP_201_CREATED)
async def add_document(
    data: CareerDocumentCreate,
    current_user: User = Depends(get_current_active_user),
    service: CareerOSService = Depends(get_career_os_service)
) -> Any:
    return await service.add_document(current_user.id, data)

@router.get("/documents", response_model=List[CareerDocumentResponse])
async def list_documents(
    current_user: User = Depends(get_current_active_user),
    service: CareerOSService = Depends(get_career_os_service)
) -> Any:
    return await service.get_documents(current_user.id)

# --- AI Workspace ---
@router.post("/workspace", response_model=AIWorkspaceProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace_project(
    data: AIWorkspaceProjectCreate,
    current_user: User = Depends(get_current_active_user),
    service: CareerOSService = Depends(get_career_os_service)
) -> Any:
    return await service.create_workspace(current_user.id, data)

@router.get("/workspace", response_model=List[AIWorkspaceProjectResponse])
async def list_workspaces(
    current_user: User = Depends(get_current_active_user),
    service: CareerOSService = Depends(get_career_os_service)
) -> Any:
    return await service.get_workspaces(current_user.id)
