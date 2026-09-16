import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base
from app.utils.uuid_utils import generate_uuidv7
from app.utils.datetime_utils import get_utc_now


class DatabaseModelMixin:
    """
    SQLAlchemy Base Mixin containing audit fields, time-ordered UUIDv7 identifiers,
    and built-in support for optimistic concurrency locking and soft deletes.
    """
    
    # Primary Key - Utilizes time-sortable UUIDv7
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=generate_uuidv7,
        index=True,
        nullable=False
    )

    # Concurrency Versioning - Mitigates overlapping update race conditions
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        onupdate=lambda ctx: ctx.current_parameters.get("version", 1) + 1 if ctx else 1
    )

    # Auditing Timestamps - Enforces timezone-aware UTC datetime tracking
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_utc_now,
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_utc_now,
        onupdate=get_utc_now,
        nullable=False
    )

    # Soft Delete Timestamp - Records when a row was marked deleted (null means active)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True
    )

    # Audit Ownership Tracks - Identifies which client initiated the record mutation
    created_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        default=None
    )
    
    updated_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        default=None
    )

    @property
    def is_deleted(self) -> bool:
        """Helper to check if the specific record has been soft-deleted."""
        return self.deleted_at is not None

    def soft_delete(self, initiator: Optional[str] = None) -> None:
        """
        Marks the record as deleted by populating the deleted_at timestamp.
        Optionally records the user/agent who initiated the deletion.
        """
        utc_now = get_utc_now()
        self.deleted_at = utc_now
        self.updated_at = utc_now
        if initiator:
            self.updated_by = initiator
            
    def restore(self) -> None:
        """Restores a soft-deleted record back to active status."""
        self.deleted_at = None
        self.updated_at = get_utc_now()
