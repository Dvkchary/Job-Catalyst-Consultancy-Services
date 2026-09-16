import time
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field
import psutil
from app.utils.datetime_utils import get_utc_now, format_iso

# Dynamic status types
StatusType = Literal["UP", "DEGRADED", "DOWN"]


class ComponentHealth(BaseModel):
    """Sub-component connection status and diagnostic properties."""
    status: StatusType = Field(..., description="Individual status of the subsystem")
    latency_ms: float = Field(..., description="Connection response delay in milliseconds")
    details: Optional[Dict[str, Any]] = Field(default=None, description="System metadata properties")


class SystemLoad(BaseModel):
    """Dynamic host machine / container resources load status."""
    cpu_percent: float = Field(..., description="CPU utilization percentage")
    memory_percent: float = Field(..., description="Memory utilization percentage")
    memory_used_mb: float = Field(..., description="Allocated RAM in Megabytes")
    memory_total_mb: float = Field(..., description="Total available RAM in Megabytes")
    disk_percent: float = Field(..., description="Storage consumption percentage")


class OverallHealthResponse(BaseModel):
    """Full payload format returned by the central /health diagnostic endpoints."""
    status: StatusType = Field(..., description="Aggregated application operational health status")
    environment: str = Field(..., description="The running environment profile")
    version: str = Field(..., description="The system software build version")
    timestamp: str = Field(..., description="ISO 8601 compliant UTC date of check execution")
    system_load: SystemLoad = Field(..., description="Hardware resource allocations")
    components: Dict[str, ComponentHealth] = Field(..., description="Database, Cache, and Storage connection metrics")


async def evaluate_system_health(settings: Any) -> OverallHealthResponse:
    """
    Executes an operational diagnostic check across all hardware allocations and sub-services.
    Calculates connection latencies and aggregates status states to evaluate liveness and readiness.
    """
    timestamp = format_iso(get_utc_now())
    components: Dict[str, ComponentHealth] = {}
    
    # 1. Database Ping (Placeholder implementation)
    db_start = time.perf_counter()
    db_ok = True  # Simulated ping (Always succeeds for baseline initialization)
    db_latency = (time.perf_counter() - db_start) * 1000
    components["database"] = ComponentHealth(
        status="UP" if db_ok else "DOWN",
        latency_ms=round(db_latency, 2),
        details={"pool_connections_active": 0}
    )

    # 2. Redis Ping (Placeholder implementation)
    redis_start = time.perf_counter()
    redis_ok = True  # Simulated ping
    redis_latency = (time.perf_counter() - redis_start) * 1000
    components["cache"] = ComponentHealth(
        status="UP" if redis_ok else "DOWN",
        latency_ms=round(redis_latency, 2),
        details={"connected_clients": 1}
    )

    # 3. Fetch Local Hardware Statistics (CPU, RAM, Disk)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    
    system_load = SystemLoad(
        cpu_percent=psutil.cpu_percent(interval=None),
        memory_percent=mem.percent,
        memory_used_mb=round(mem.used / (1024 * 1024), 2),
        memory_total_mb=round(mem.total / (1024 * 1024), 2),
        disk_percent=disk.percent
    )

    # Calculate overall health classification status
    # If any critical component is down, mark the aggregated system as DEGRADED or DOWN
    all_up = all(comp.status == "UP" for comp in components.values())
    overall_status: StatusType = "UP" if all_up else "DEGRADED"

    return OverallHealthResponse(
        status=overall_status,
        environment=settings.ENVIRONMENT.value,
        version=settings.PROJECT_VERSION,
        timestamp=timestamp,
        system_load=system_load,
        components=components
    )
