# JobCatalyst AI - Database Foundation Layer Reference

This document serves as the **Database Architecture Specification, Migration Guide, and Developer Reference** for the JobCatalyst AI backend relational engine.

---

## 1. Architectural Overview

The relational persistence tier utilizes **PostgreSQL** as its enterprise-grade transactional engine, managed asynchronously in Python via **SQLAlchemy 2.x** and the high-performance **asyncpg** connection driver.

```
       ┌────────────────────────────────────────────────────────┐
       │                 FastAPI Request Lifespan               │
       └───────────────────────────┬────────────────────────────┘
                                   │
                    Injects Depends(get_db_session)
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                AsyncSession (Transaction)              │
       └───────────────────────────┬────────────────────────────┘
                                   │
                        Executes Repo CRUD Actions
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │             SQLAlchemy 2.x AsyncEngine                 │
       │     (Connection Pool, Timeout & Pre-Ping Controls)      │
       └───────────────────────────┬────────────────────────────┘
                                   │
                             pg_transport
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                 PostgreSQL Database                    │
       └────────────────────────────────────────────────────────┘
```

### Connection Pool Specification
To withstand erratic serverless scaling (such as Google Cloud Run context-swapping) and prevent stale sockets, the database engine is provisioned with defensive timeout boundaries:
- **Pool Size:** `20` concurrent connection units (scalable via `.env` parameter `POSTGRES_POOL_SIZE`).
- **Max Overflow:** `10` extra bursting units (`POSTGRES_MAX_OVERFLOW`).
- **Pool Recycle:** `1800` seconds (30 minutes). Prevents connection recycling from leaking resources.
- **Acquisition Timeout:** `30` seconds. Blocks requests if connections cannot be checkout within boundaries.
- **Connection Validation:** Enabled (`pool_pre_ping=True`). Runs a low-overhead heartbeat confirmation before checking out any connection.

---

## 2. Developer Guide

All domain entities (such as Users, Resumes, Jobs) created in subsequent modules must adhere strictly to these persistent conventions.

### Schema Modeling Protocol
Every entity must inherit from `Base` (from `app.db.base_class`) and integrate the `DatabaseModelMixin` (from `app.db.base_models`):

```python
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from app.db.base import Base
from app.db.base_models import DatabaseModelMixin

class UserProfile(Base, DatabaseModelMixin):
    # Primary Key, version, timestamps, created_by, and deleted_at are inherited!
    bio: Mapped[str] = mapped_column(String(1000), nullable=True)
```

#### Inherited Core Features:
1. **Time-Ordered Primary Key (`id`):** Generated using a high-resolution **UUIDv7** generator. Unlike UUIDv4, UUIDv7 incorporates unix epoch millisecond timestamps in its leading bits. This ensures index inserts remain sequential and local, improving write throughput in indexed PostgreSQL tables.
2. **Concurrency Safe Versioning (`version`):** Incorporates integer-based optimistic concurrency controls. Any modification step triggers a revision increment to prevent race conditions during parallel client saves.
3. **Audit Trails (`created_at`, `updated_at`):** Timestamps are locked to timezone-aware UTC datetime states.
4. **Audit Authorship (`created_by`, `updated_by`):** Optional fields tracking who triggered the mutation.
5. **Soft Delete Hooks (`deleted_at`):** Deleted records are not immediately pruned from tables. They are marked with a timezone-aware deletion timestamp, allowing for recovery.

### The Repository Pattern
Do not write raw queries in controllers. Business operations must use an extension of `BaseRepository[ModelType]`:

```python
from app.db.repository import BaseRepository
from app.models import UserProfile

class UserProfileRepository(BaseRepository[UserProfile]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=UserProfile, db=db)
        
    async def get_by_bio_keyword(self, keyword: str) -> list[UserProfile]:
        # Custom query logic goes here!
        ...
```

---

## 3. Database Migration Guide (Alembic)

Database schemas are strictly version-controlled using **Alembic**.

### Key Configurations
- **Version Table:** Schema versions are tracked securely in the `alembic_version` table inside the operational database schema.
- **Unified Metadata Registry:** The migration runner reads schemas compiled inside `/backend/app/db/base.py` to compile migration files.

### Workflow Commands

#### Run Pending Schema Upgrades
Apply all migrations to synchronize the database with the latest schema layout:
```bash
alembic upgrade head
```

#### Revert the Last Migration
To undo a recent database mutation:
```bash
alembic downgrade -1
```

#### Generate a New Schema Migration
When you create or modify an ORM entity model, generate a versioned script using automated diff checks:
```bash
alembic revision --autogenerate -m "describe_changes_here"
```

*Note: Always review the autogenerated script under the `/backend/alembic/versions/` path before applying it to verify correctness.*
