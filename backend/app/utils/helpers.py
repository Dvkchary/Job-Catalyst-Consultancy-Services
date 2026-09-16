from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIEnvelope(BaseModel, Generic[T]):
    """Standardized top-level response envelope mapping successful API executions."""
    success: bool = Field(default=True, description="True indicates a successful transaction")
    data: T = Field(..., description="Primary response entity, object, or array payload")


class PaginationMeta(BaseModel):
    """Metadata detailing list dimensions and page thresholds."""
    total_items: int = Field(..., description="Total records matching query criteria")
    limit: int = Field(..., description="Requested batch size limit")
    cursor: Optional[str] = Field(default=None, description="Cursor identifier pointing to next offset element")
    has_more: bool = Field(default=False, description="Flag indicating further paginated segments remain")


class PaginatedResponse(BaseModel, Generic[T]):
    """Unified layout for list/search endpoints."""
    success: bool = Field(default=True, description="Transaction status indicator")
    items: List[T] = Field(..., description="Target dataset segment")
    meta: PaginationMeta = Field(..., description="Cursor pagination contextual metadata")


def wrap_success_response(data: Any) -> Dict[str, Any]:
    """Wraps any return structure inside the global successful API envelope schema."""
    return {"success": True, "data": data}


def build_paginated_meta(
    total_items: int,
    limit: int,
    cursor: Optional[str],
    has_more: bool
) -> PaginationMeta:
    """Helper factory that constructs uniform pagination metadata payloads."""
    return PaginationMeta(
        total_items=total_items,
        limit=limit,
        cursor=cursor,
        has_more=has_more
    )
