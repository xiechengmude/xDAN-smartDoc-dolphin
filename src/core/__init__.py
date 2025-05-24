"""
Core modules for the SmartDoc Dolphin system.
"""

from .config import Settings, get_settings
from .logging import setup_logging
from .models import DocumentParseTask, DocumentParseResult

__all__ = [
    "Settings",
    "get_settings", 
    "setup_logging",
    "DocumentParseTask",
    "DocumentParseResult",
] 