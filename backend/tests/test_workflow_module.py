import uuid
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.workflow import Workflow, WorkflowExecution, WorkflowTemplate, WorkflowLog
from app.services.workflow_service import WorkflowService, WorkflowExecutionEngine


@pytest.mark.asyncio
async def test_workflow_repository_operations():
    """
    Validates standard database operations and helpers on WorkflowRepository.
    """
    from app.db.workflow_repositories import WorkflowRepository
    
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    
    # Mocking standard returned database scalars
    mock_result = MagicMock()
    mock_wf = Workflow(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="Test Workflow",
        trigger_type="MANUAL",
        definition={"steps": []}
    )
    mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_wf])))
    mock_db.execute.return_value = mock_result
    
    repo = WorkflowRepository(db=mock_db)
    wfs = await repo.get_by_user(user_id=uuid.uuid4())
    
    assert len(wfs) == 1
    assert wfs[0].name == "Test Workflow"


@pytest.mark.asyncio
async def test_workflow_service_create():
    """
    Ensures that WorkflowService validates definitions and invokes repository.
    """
    mock_db = MagicMock()
    wf_svc = WorkflowService(db=mock_db)
    
    user_id = uuid.uuid4()
    workflow_payload = {
        "name": "ATS Scan Automator",
        "description": "Scans resumes automatically on upload",
        "trigger_type": "EVENT_DRIVEN",
        "trigger_config": {"event": "resume.uploaded"},
        "definition": {
            "steps": [
                {
                    "id": "step1",
                    "name": "Check ATS Score",
                    "type": "action",
                    "action_type": "call_ai",
                    "config": {"prompt": "Check compatibility score: {{context.resume}}"}
                }
            ]
        }
    }
    
    # Mock repo create to return a mock Workflow object
    wf_svc.wf_repo.create = AsyncMock(return_value=Workflow(id=uuid.uuid4(), **workflow_payload))
    
    result = await wf_svc.create_workflow(user_id=user_id, obj_in=workflow_payload)
    
    assert result is not None
    assert result.name == "ATS Scan Automator"
    assert result.trigger_type == "EVENT_DRIVEN"
    assert "steps" in result.definition


@pytest.mark.asyncio
@patch("app.services.workflow_service.asyncio.create_task")
async def test_workflow_service_trigger(mock_create_task):
    """
    Tests manual triggering of a workflow, creating an execution and launching background task.
    """
    mock_db = MagicMock()
    wf_svc = WorkflowService(db=mock_db)
    
    workflow_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    # Mock workflow retrieval
    mock_wf = Workflow(
        id=workflow_id,
        user_id=user_id,
        name="Scheduled Check",
        is_active=True,
        trigger_type="MANUAL",
        definition={"steps": []}
    )
    wf_svc.wf_repo.get = AsyncMock(return_value=mock_wf)
    
    # Mock execution creation
    mock_exec = WorkflowExecution(
        id=uuid.uuid4(),
        workflow_id=workflow_id,
        user_id=user_id,
        status="PENDING",
        trigger_source="MANUAL",
        context_data={"job_id": "123"},
        steps_state={}
    )
    wf_svc.exec_repo.create = AsyncMock(return_value=mock_exec)
    wf_svc.db.commit = AsyncMock()
    
    execution = await wf_svc.trigger_workflow(
        workflow_id=workflow_id,
        user_id=user_id,
        initial_context={"job_id": "123"}
    )
    
    assert execution is not None
    assert execution.workflow_id == workflow_id
    assert execution.context_data["job_id"] == "123"
    mock_create_task.assert_called_once()


@pytest.mark.asyncio
async def test_execution_engine_interpolation():
    """
    Tests recursive interpolation string compiler.
    """
    mock_db = MagicMock()
    execution_id = uuid.uuid4()
    
    engine = WorkflowExecutionEngine(db=mock_db, execution_id=execution_id)
    
    execution = WorkflowExecution(
        context_data={"target_title": "Fullstack Engineer"},
        steps_state={
            "step_1": {
                "status": "COMPLETED",
                "output": {"ats_score": 85}
            }
        }
    )
    
    step_definition = {
        "id": "step_2",
        "type": "action",
        "action_type": "call_ai",
        "config": {
            "prompt": "Evaluate applicant compatibility for {{context.target_title}}. Score: {{steps_state.step_1.output.ats_score}}."
        }
    }
    
    compiled = engine._interpolate_step(step_definition, execution)
    assert compiled["config"]["prompt"] == "Evaluate applicant compatibility for Fullstack Engineer. Score: 85."


@pytest.mark.asyncio
async def test_execution_engine_expression_evaluator():
    """
    Checks safe conditional mathematical expression parser.
    """
    mock_db = MagicMock()
    engine = WorkflowExecutionEngine(db=mock_db, execution_id=uuid.uuid4())
    
    assert engine._evaluate_expression("85 >= 70") is True
    assert engine._evaluate_expression("12.5 < 10") is False
    assert engine._evaluate_expression("True") is True
    assert engine._evaluate_expression('"Active" == "Active"') is True
    assert engine._evaluate_expression('"Active" != "Paused"') is True
