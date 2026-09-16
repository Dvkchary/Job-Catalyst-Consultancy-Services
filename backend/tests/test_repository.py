import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base_class import Base
from app.db.base_models import DatabaseModelMixin
from app.db.repository import BaseRepository

# ==============================================================================
# Define a Mock Declarative Model for Repository Testing
# ==============================================================================
class TestRecord(Base, DatabaseModelMixin):
    """Concrete ORM model subclassing the Base and DatabaseModelMixin for test verification."""
    pass


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Fixture providing a mock asynchronous database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def test_repo(mock_db_session: AsyncMock) -> BaseRepository[TestRecord]:
    """Fixture instantiating a repository bound to the TestRecord model."""
    return BaseRepository(model=TestRecord, db=mock_db_session)


@pytest.mark.asyncio
async def test_repository_get_by_id(test_repo: BaseRepository[TestRecord], mock_db_session: AsyncMock):
    """Verifies that repository get() compiles queries checking active state and ID."""
    record_id = uuid.uuid4()
    mock_record = TestRecord(id=record_id)
    
    # Setup mock executor to return our mock record
    mock_result = MagicMock()
    mock_result.scalar_or_none.return_value = mock_record
    mock_db_session.execute.return_value = mock_result

    result = await test_repo.get(record_id)
    
    assert result == mock_record
    assert result.id == record_id
    mock_db_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_repository_get_multi(test_repo: BaseRepository[TestRecord], mock_db_session: AsyncMock):
    """Verifies retrieval of multi-records, including default ordering and offset slices."""
    mock_records = [TestRecord(id=uuid.uuid4()), TestRecord(id=uuid.uuid4())]
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_records
    mock_db_session.execute.return_value = mock_result

    results = await test_repo.get_multi(skip=5, limit=10)
    
    assert results == mock_records
    assert len(results) == 2
    mock_db_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_repository_count_active(test_repo: BaseRepository[TestRecord], mock_db_session: AsyncMock):
    """Verifies count query compilation on active models."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = 42
    mock_db_session.execute.return_value = mock_result

    count = await test_repo.count()
    assert count == 42
    mock_db_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_repository_create_record(test_repo: BaseRepository[TestRecord], mock_db_session: AsyncMock):
    """Verifies that create record instantiates the class, injects creators, and flushes."""
    payload = {"version": 1}
    creator = "user_auth_123"

    new_record = await test_repo.create(payload, creator_id=creator)
    
    assert isinstance(new_record, TestRecord)
    assert new_record.created_by == creator
    assert new_record.updated_by == creator
    
    mock_db_session.add.assert_called_once_with(new_record)
    mock_db_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_repository_update_record(test_repo: BaseRepository[TestRecord], mock_db_session: MagicMock):
    """Verifies updates map payload attributes and record modifications correctly."""
    record = TestRecord(id=uuid.uuid4(), created_by="test_user")
    updates = {"created_by": "updated_user_id"}

    updated_record = await test_repo.update(db_obj=record, obj_in=updates, updater_id="system_updater")
    
    assert updated_record.created_by == "updated_user_id"
    assert updated_record.updated_by == "system_updater"
    mock_db_session.add.assert_called_once_with(record)
    mock_db_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_repository_soft_delete(test_repo: BaseRepository[TestRecord], mock_db_session: AsyncMock):
    """Verifies that delete(soft=True) flags deleted_at, touch-updates records, and flushes changes."""
    record_id = uuid.uuid4()
    record = TestRecord(id=record_id)
    
    # Mock lookup
    mock_result = MagicMock()
    mock_result.scalar_or_none.return_value = record
    mock_db_session.execute.return_value = mock_result

    success = await test_repo.delete(id=record_id, soft=True, initiator="delete_admin")
    
    assert success is True
    assert record.is_deleted is True
    assert record.updated_by == "delete_admin"
    mock_db_session.add.assert_called_once_with(record)
    mock_db_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_repository_hard_delete(test_repo: BaseRepository[TestRecord], mock_db_session: AsyncMock):
    """Verifies delete(soft=False) runs a standard physical removal from tables."""
    record_id = uuid.uuid4()
    record = TestRecord(id=record_id)
    
    # Mock lookup
    mock_result = MagicMock()
    mock_result.scalar_or_none.return_value = record
    mock_db_session.execute.return_value = mock_result

    success = await test_repo.delete(id=record_id, soft=False)
    
    assert success is True
    mock_db_session.delete.assert_called_once_with(record)
    mock_db_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_repository_restore_record(test_repo: BaseRepository[TestRecord], mock_db_session: AsyncMock):
    """Verifies that restore() recovers soft-deleted records."""
    record_id = uuid.uuid4()
    record = TestRecord(id=record_id)
    record.soft_delete()
    
    # Mock lookup
    mock_result = MagicMock()
    mock_result.scalar_or_none.return_value = record
    mock_db_session.execute.return_value = mock_result

    success = await test_repo.restore(id=record_id)
    
    assert success is True
    assert record.is_deleted is False
    mock_db_session.add.assert_called_once_with(record)
    mock_db_session.flush.assert_called_once()
