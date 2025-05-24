"""
Configuration management for SmartDoc Dolphin system.
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "SmartDoc Dolphin"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # API Server
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=1, env="API_WORKERS")
    api_reload: bool = Field(default=True, env="API_RELOAD")
    
    # Dolphin Model Configuration
    model_path: str = Field(default="./hf_model", env="MODEL_PATH")
    model_device: str = Field(default="cuda", env="MODEL_DEVICE")
    model_precision: str = Field(default="half", env="MODEL_PRECISION") # half, float
    max_batch_size: int = Field(default=16, env="MAX_BATCH_SIZE")
    max_sequence_length: int = Field(default=4096, env="MAX_SEQUENCE_LENGTH")
    
    # Database
    mongodb_url: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    mongodb_database: str = Field(default="smartdoc", env="MONGODB_DATABASE")
    
    # Redis Cache/Queue
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Celery Worker
    celery_broker_url: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    celery_worker_concurrency: int = Field(default=4, env="CELERY_WORKER_CONCURRENCY")
    celery_worker_prefetch_multiplier: int = Field(default=1, env="CELERY_WORKER_PREFETCH_MULTIPLIER")
    
    # File Storage
    storage_type: str = Field(default="local", env="STORAGE_TYPE")  # local, s3, minio
    local_storage_path: str = Field(default="./storage", env="LOCAL_STORAGE_PATH")
    
    # S3/MinIO Configuration
    s3_endpoint: Optional[str] = Field(default=None, env="S3_ENDPOINT")
    s3_access_key: Optional[str] = Field(default=None, env="S3_ACCESS_KEY")
    s3_secret_key: Optional[str] = Field(default=None, env="S3_SECRET_KEY")
    s3_bucket: Optional[str] = Field(default="smartdoc", env="S3_BUCKET")
    s3_region: Optional[str] = Field(default="us-east-1", env="S3_REGION")
    
    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60 * 24 * 7, env="JWT_EXPIRE_MINUTES")  # 7 days
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=60, env="RATE_LIMIT_PERIOD")  # seconds
    
    # Monitoring
    monitoring_enabled: bool = Field(default=False, env="MONITORING_ENABLED")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Performance Tuning
    max_concurrent_tasks: int = Field(default=10, env="MAX_CONCURRENT_TASKS")
    task_timeout: int = Field(default=300, env="TASK_TIMEOUT")  # seconds
    cleanup_interval: int = Field(default=3600, env="CLEANUP_INTERVAL")  # seconds
    
    # Image Processing
    max_image_size: int = Field(default=50 * 1024 * 1024, env="MAX_IMAGE_SIZE")  # 50MB
    allowed_image_formats: List[str] = Field(
        default=["jpeg", "jpg", "png", "pdf", "tiff"], 
        env="ALLOWED_IMAGE_FORMATS"
    )
    
    @validator("allowed_image_formats", pre=True)
    def parse_allowed_formats(cls, v):
        if isinstance(v, str):
            return [fmt.strip().lower() for fmt in v.split(",")]
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}")
        return v.upper()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings() 