"""
Logging configuration for SmartDoc Dolphin system.
"""

import logging
import sys
from datetime import datetime
from typing import Any, Dict

import structlog
from structlog.stdlib import BoundLogger

from .config import settings


def setup_logging() -> None:
    """Setup structured logging with structlog."""
    
    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            add_timestamp,
            add_request_id,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def add_timestamp(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add timestamp to log events."""
    event_dict["timestamp"] = datetime.utcnow().isoformat()
    return event_dict


def add_request_id(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add request ID to log events if available."""
    # This can be enhanced to get request ID from context
    return event_dict


def get_logger(name: str = "") -> BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Application logger instances
app_logger = get_logger("smartdoc.app")
api_logger = get_logger("smartdoc.api")
worker_logger = get_logger("smartdoc.worker")
model_logger = get_logger("smartdoc.model")
storage_logger = get_logger("smartdoc.storage")
db_logger = get_logger("smartdoc.database") 