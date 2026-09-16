from datetime import datetime, timezone
from typing import Optional


def get_utc_now() -> datetime:
    """
    Acquires the current timezone-aware UTC datetime.
    Mandatory standard to ensure server consistency across dynamic container bounds.
    """
    return datetime.now(timezone.utc)


def format_iso(dt: datetime) -> str:
    """Formats a datetime object to an ISO 8601 compliant string with explicit Z indicator."""
    # Ensure timezone is normalized to UTC
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def parse_iso(dt_str: str) -> Optional[datetime]:
    """
    Safely parses an ISO 8601 string into a timezone-aware UTC datetime.
    Returns None if the format is invalid.
    """
    try:
        # Normalize trailing Z to timezone offsets
        if dt_str.endswith("Z"):
            dt_str = dt_str[:-1] + "+00:00"
        parsed = datetime.fromisoformat(dt_str)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def calculate_days_delta(start: datetime, end: datetime) -> int:
    """Calculates the exact integer day difference between two datetime instances."""
    return (end.astimezone(timezone.utc) - start.astimezone(timezone.utc)).days
