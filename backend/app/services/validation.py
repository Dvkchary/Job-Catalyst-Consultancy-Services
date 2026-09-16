import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class ValidationService:
    """
    Enterprise-grade input validation service for user profiles,
    experience date ranges, salary structures, social media URLs, and avatar constraints.
    """

    @staticmethod
    def validate_date_range(start_date_str: str, end_date_str: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validates that:
        1. Date formats match standard ISO layouts (YYYY-MM-DD or YYYY-MM).
        2. If end_date is provided, start_date must occur before or equal to end_date.
        3. Dates do not occur in the far future (sanity check, e.g., beyond 50 years).
        """
        date_formats = ["%Y-%m-%d", "%Y-%m", "%Y"]

        def parse_date(d_str: str) -> Optional[datetime]:
            for fmt in date_formats:
                try:
                    return datetime.strptime(d_str, fmt)
                except ValueError:
                    continue
            return None

        start_dt = parse_date(start_date_str)
        if not start_dt:
            return False, f"Invalid start date format '{start_date_str}'. Expected YYYY-MM-DD or YYYY-MM."

        if end_date_str:
            end_dt = parse_date(end_date_str)
            if not end_dt:
                return False, f"Invalid end date format '{end_date_str}'. Expected YYYY-MM-DD or YYYY-MM."

            if start_dt > end_dt:
                return False, f"Start date ({start_date_str}) cannot be later than end date ({end_date_str})."

        return True, None

    @staticmethod
    def validate_salary_range(min_sal: Optional[float], max_sal: Optional[float]) -> Tuple[bool, Optional[str]]:
        """
        Validates salary boundaries:
        1. Min salary must be non-negative.
        2. Max salary must be non-negative.
        3. Min salary cannot exceed max salary if both are populated.
        """
        if min_sal is not None and min_sal < 0:
            return False, "Minimum salary cannot be negative."

        if max_sal is not None and max_sal < 0:
            return False, "Maximum salary cannot be negative."

        if min_sal is not None and max_sal is not None:
            if min_sal > max_sal:
                return False, f"Minimum salary ({min_sal}) cannot exceed maximum salary ({max_sal})."

        return True, None

    @staticmethod
    def validate_social_url(url: str, platform: str) -> Tuple[bool, Optional[str]]:
        """
        Ensures social media profile links match platform patterns (LinkedIn, GitHub).
        """
        url = url.strip()
        if not url:
            return True, None

        patterns = {
            "linkedin": r"^(https?://)?(www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?$",
            "github": r"^(https?://)?(www\.)?github\.com/[a-zA-Z0-9_-]+/?$",
            "portfolio": r"^(https?://)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$"
        }

        pattern = patterns.get(platform.lower())
        if not pattern:
            return False, f"Unsupported platform validation requested: '{platform}'."

        if not re.match(pattern, url, re.IGNORECASE):
            return False, f"Invalid {platform} URL pattern format."

        return True, None

    @staticmethod
    def validate_avatar_file(filename: str, content_type: str, byte_size: int) -> Tuple[bool, Optional[str]]:
        """
        Strict asset validation:
        1. Limit allowed mime-types to JPEG, PNG, WEBP.
        2. Limit file sizes to a max of 5MB.
        3. Guard against malicious double-extension attempts (e.g. avatar.png.exe).
        """
        allowed_types = ["image/jpeg", "image/png", "image/webp"]
        allowed_extensions = [".jpg", ".jpeg", ".png", ".webp"]
        
        # 1. Check content type
        if content_type.lower() not in allowed_types:
            return False, "Unsupported media format. Allowed formats: JPEG, PNG, WEBP."

        # 2. Check file size limits (5 Megabytes)
        max_size = 5 * 1024 * 1024
        if byte_size > max_size:
            return False, f"Avatar file size exceeds the 5MB limit. Got {round(byte_size / (1024*1024), 2)}MB."

        # 3. Check filename extensions
        filename_lower = filename.lower()
        if not any(filename_lower.endswith(ext) for ext in allowed_extensions):
            return False, "Invalid file extension. Expected JPG, JPEG, PNG, or WEBP."

        # 4. Double extension mitigation
        if len(filename_lower.split(".")) > 2:
            # We must be careful if the double extension ends with something malicious
            last_part = filename_lower.split(".")[-1]
            if last_part not in ["jpg", "jpeg", "png", "webp"]:
                return False, "Suspicious file structure detected."

        return True, None
