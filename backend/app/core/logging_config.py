import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict
from app.core.config import settings

# Thread-local storage placeholder for Correlation / Request IDs
import contextvars

# Context variables are thread-safe and async-safe context managers
correlation_id_ctx = contextvars.ContextVar("correlation_id", default="-")


class JSONFormatter(logging.Formatter):
    """
    Custom Logging Formatter to structure log outputs as single-line serialized JSON objects.
    Ensures seamless ingestion by Elasticsearch, Loki, Datadog, or cloud logging agents.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_ctx.get(),
            "module": record.module,
            "func_name": record.funcName,
            "line_no": record.lineno,
        }

        # Include traceback details if an exception is handled
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include extra attributes injected dynamically
        if hasattr(record, "extra_info"):
            log_data["extra_info"] = getattr(record, "extra_info")

        return json.dumps(log_data)


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable log formatter optimized for local developer terminal output.
    Uses clean tracking tabs and highlights core correlation attributes.
    """
    def format(self, record: logging.LogRecord) -> str:
        corr_id = correlation_id_ctx.get()
        corr_str = f" [RID:{corr_id}]" if corr_id != "-" else ""
        
        # Base log elements
        log_fmt = f"%(asctime)s | %(levelname)-8s | %(name)s{corr_str} | %(message)s"
        
        # Add simple exception stacktrace lines if available
        if record.exc_info:
            log_fmt += "\n%(exc_text)s"
            
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logging() -> None:
    """
    Bootstraps the unified logging pipeline across the entire system.
    Captures third-party loggers (uvicorn, fastapi) and configures rotation filters.
    """
    # Create logs directory if it does not exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file_path = log_dir / "app.log"

    # Resolve active log level from application settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Instantiate formatters
    if settings.LOG_JSON_FORMAT:
        formatter = JSONFormatter()
    else:
        formatter = ConsoleFormatter()

    # Create primary handlers: Stream (stdout) + Rotating File Handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        filename=str(log_file_path),
        maxBytes=10 * 1024 * 1024,  # 10MB per file
        backupCount=5,              # Keep up to 5 historical log files
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    # Configure root logger properties
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove any existing handlers to prevent duplicate outputs
    root_logger.handlers = []
    root_logger.addHandler(stdout_handler)
    root_logger.addHandler(file_handler)

    # Hook and override standard logging interfaces of our app framework servers (Uvicorn)
    uvicorn_loggers = [
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi"
    ]
    for logger_name in uvicorn_loggers:
        sub_logger = logging.getLogger(logger_name)
        sub_logger.handlers = []
        sub_logger.propagate = True  # Bubble up to root logger to use primary handlers
