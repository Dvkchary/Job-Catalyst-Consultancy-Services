import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.utils import transaction_scope, verify_db_connection, with_retry


@pytest.mark.asyncio
async def test_transaction_scope_commit():
    """Verifies that transaction_scope commits successfully when no exceptions occur."""
    mock_session = AsyncMock(spec=AsyncSession)
    
    # Patch the session maker to return our mock_session
    with patch("app.db.utils.async_session_maker", return_value=mock_session):
        async with transaction_scope() as session:
            assert session == mock_session
            
        # Assert database actions are closed and committed
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.rollback.assert_not_called()


@pytest.mark.asyncio
async def test_transaction_scope_rollback_on_error():
    """Verifies that transaction_scope triggers an automatic rollback on exception."""
    mock_session = AsyncMock(spec=AsyncSession)
    
    with patch("app.db.utils.async_session_maker", return_value=mock_session):
        with pytest.raises(ValueError, match="Database error"):
            async with transaction_scope():
                raise ValueError("Database error")
                
        # Assert database actions are closed and rolled back on crash
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_verify_db_connection_success():
    """Verifies that connection verification returns True when the database ping succeeds."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar.return_value = 1
    mock_session.execute.return_value = mock_result

    with patch("app.db.utils.async_session_maker", return_value=mock_session):
        is_connected = await verify_db_connection()
        assert is_connected is True
        mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_verify_db_connection_failure():
    """Verifies that connection verification returns False on database failures."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute.side_effect = Exception("Connection Refused")

    with patch("app.db.utils.async_session_maker", return_value=mock_session):
        is_connected = await verify_db_connection()
        assert is_connected is False


@pytest.mark.asyncio
async def test_with_retry_success():
    """Verifies that the retry helper successfully returns value on the first attempt."""
    mock_func = AsyncMock(return_value="Success")
    result = await with_retry(mock_func, retries=3, initial_delay=0.01)
    
    assert result == "Success"
    assert mock_func.call_count == 1


@pytest.mark.asyncio
async def test_with_retry_failure_then_success():
    """Verifies that with_retry retries on failure and succeeds when downstream resolves."""
    call_count = 0
    
    async def transient_error_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Transient error")
        return "Recovered"

    result = await with_retry(transient_error_func, retries=3, initial_delay=0.01)
    assert result == "Recovered"
    assert call_count == 2


@pytest.mark.asyncio
async def test_with_retry_max_failures():
    """Verifies that with_retry exhausts retries and raises the final error on total failure."""
    mock_func = AsyncMock(side_effect=ValueError("Persistent error"))
    
    with pytest.raises(ValueError, match="Persistent error"):
        await with_retry(mock_func, retries=3, initial_delay=0.001, backoff_factor=1.1)
        
    assert mock_func.call_count == 3
