"""
Configuration management for the API
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    api_reload: bool = False

    # Model Configuration
    model_weights_path: str = "yolov7.pt"
    model_img_size: int = 640
    model_conf_threshold: float = 0.25
    model_iou_threshold: float = 0.45
    model_device: str = ""  # Empty for auto-detect

    # Detection Classes
    detection_classes: str = "0,56"  # person=0, chair=56

    # Tracking Configuration
    sort_max_age: int = 5
    sort_min_hits: int = 2
    sort_iou_threshold: float = 0.2

    # Occupancy Configuration
    occupancy_time_threshold: int = 10  # seconds
    occupancy_proximity_threshold: int = 100  # pixels

    # Storage Configuration
    upload_dir: str = "uploads"
    output_dir: str = "outputs"
    jobs_dir: str = "jobs"
    max_upload_size: int = 524288000  # 500MB
    allowed_video_extensions: str = "mp4,avi,mov,mkv,webm"

    # Job Configuration
    job_cleanup_after_hours: int = 24
    max_concurrent_jobs: int = 3
    job_timeout_minutes: int = 30

    # Logging
    log_level: str = "INFO"
    log_file: str = "api/logs/app.log"

    # Security
    api_key_enabled: bool = False
    api_key: Optional[str] = None

    # CORS Configuration
    cors_enabled: bool = True
    cors_origins: str = "*"

    # Redis Configuration
    redis_enabled: bool = False
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # Environment
    environment: str = "development"
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def base_dir(self) -> Path:
        """Get base directory of the project"""
        return Path(__file__).parent.parent

    @property
    def upload_path(self) -> Path:
        """Get upload directory path"""
        path = self.base_dir / self.upload_dir
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def output_path(self) -> Path:
        """Get output directory path"""
        path = self.base_dir / self.output_dir
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def jobs_path(self) -> Path:
        """Get jobs directory path"""
        path = self.base_dir / self.jobs_dir
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def log_path(self) -> Path:
        """Get log file path"""
        path = self.base_dir / self.log_file
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def weights_path(self) -> Path:
        """Get model weights path"""
        return self.base_dir / self.model_weights_path

    @property
    def allowed_extensions(self) -> List[str]:
        """Get list of allowed video extensions"""
        return [ext.strip() for ext in self.allowed_video_extensions.split(",")]

    @property
    def detection_class_list(self) -> List[int]:
        """Get list of detection classes as integers"""
        return [int(cls.strip()) for cls in self.detection_classes.split(",")]

    @property
    def cors_origins_list(self) -> List[str]:
        """Get list of CORS origins"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    def get_redis_url(self) -> str:
        """Get Redis connection URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
