"""
Data models for SmartDoc Dolphin system.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ElementType(str, Enum):
    """Document element type enumeration."""
    TEXT = "text"
    TABLE = "table"
    FIGURE = "figure"
    FORMULA = "formula"


class StorageType(str, Enum):
    """Storage type enumeration."""
    LOCAL = "local"
    S3 = "s3"
    MINIO = "minio"


class DocumentElement(BaseModel):
    """Document element data model."""
    element_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    element_type: ElementType
    bbox: List[float] = Field(description="Bounding box coordinates [x1, y1, x2, y2]")
    text: str = Field(default="", description="Extracted text content")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reading_order: int = Field(default=0, ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class DocumentParseResult(BaseModel):
    """Document parsing result data model."""
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    elements: List[DocumentElement]
    markdown_content: str = Field(default="")
    json_content: Dict[str, Any] = Field(default_factory=dict)
    processing_time: float = Field(default=0.0, ge=0.0)
    total_elements: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class DocumentParseTask(BaseModel):
    """Document parsing task data model."""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    file_path: str
    file_name: str
    file_size: int = Field(ge=0)
    file_hash: str
    storage_type: StorageType
    status: TaskStatus = TaskStatus.PENDING
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    error_message: Optional[str] = None
    result: Optional[DocumentParseResult] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Processing configuration
    max_batch_size: int = Field(default=16, ge=1, le=64)
    enable_parallel: bool = Field(default=True)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class TaskCreateRequest(BaseModel):
    """Task creation request model."""
    file_name: str
    max_batch_size: int = Field(default=16, ge=1, le=64)
    enable_parallel: bool = Field(default=True)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    """Task response model."""
    task_id: str
    status: TaskStatus
    progress: float
    file_name: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[DocumentParseResult] = None

    class Config:
        use_enum_values = True


class TaskListResponse(BaseModel):
    """Task list response model."""
    tasks: List[TaskResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class SystemStatus(BaseModel):
    """System status model."""
    service_name: str
    version: str
    status: str
    uptime: float
    cpu_usage: float
    memory_usage: float
    gpu_usage: Optional[float] = None
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    queue_size: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    components: Dict[str, str] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None 