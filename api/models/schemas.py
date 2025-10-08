"""
Pydantic models for API request/response schemas
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator


class JobStatus(str, Enum):
    """Job processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BoundingBox(BaseModel):
    """Bounding box coordinates"""
    x1: float = Field(..., description="Top-left x coordinate")
    y1: float = Field(..., description="Top-left y coordinate")
    x2: float = Field(..., description="Bottom-right x coordinate")
    y2: float = Field(..., description="Bottom-right y coordinate")


class Detection(BaseModel):
    """Single detection in a frame"""
    class_id: int = Field(..., description="Class ID (0=person, 56=chair)")
    class_name: str = Field(..., description="Class name")
    confidence: float = Field(..., description="Detection confidence score")
    bbox: BoundingBox = Field(..., description="Bounding box coordinates")
    track_id: Optional[int] = Field(None, description="Tracking ID")


class OccupancyEvent(BaseModel):
    """Seat occupancy event"""
    seat_id: int = Field(..., description="Unique seat identifier")
    bbox: BoundingBox = Field(..., description="Seat bounding box")
    occupied_duration: float = Field(..., description="Duration in seconds")
    time_exceeded: bool = Field(..., description="Whether time threshold was exceeded")
    first_detected_frame: int = Field(..., description="Frame when first detected")
    last_detected_frame: int = Field(..., description="Frame when last detected")


class FrameStatistics(BaseModel):
    """Statistics for a single frame"""
    frame_number: int
    total_detections: int
    person_count: int
    chair_count: int
    occupied_seats: int


class DetectionResults(BaseModel):
    """Complete detection results"""
    total_frames: int = Field(..., description="Total number of frames processed")
    total_detections: int = Field(..., description="Total detections across all frames")
    person_detections: int = Field(..., description="Total person detections")
    chair_detections: int = Field(..., description="Total chair detections")
    unique_tracked_objects: int = Field(..., description="Number of unique tracked objects")
    occupancy_events: List[OccupancyEvent] = Field(default_factory=list, description="Seat occupancy events")
    processing_time: float = Field(..., description="Total processing time in seconds")
    fps: float = Field(..., description="Processing frames per second")
    frame_statistics: Optional[List[FrameStatistics]] = Field(None, description="Per-frame statistics")


class DetectionParameters(BaseModel):
    """Optional detection parameters to override defaults"""
    conf_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence threshold")
    iou_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="IOU threshold")
    img_size: Optional[int] = Field(None, gt=0, description="Image size for inference")
    classes: Optional[List[int]] = Field(None, description="Classes to detect")
    occupancy_time_threshold: Optional[int] = Field(None, gt=0, description="Occupancy time threshold in seconds")
    save_video: Optional[bool] = Field(True, description="Whether to save processed video")
    include_frame_stats: Optional[bool] = Field(False, description="Include per-frame statistics")


class JobCreateResponse(BaseModel):
    """Response when creating a new detection job"""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    message: str = Field(..., description="Status message")
    created_at: datetime = Field(..., description="Job creation timestamp")


class JobStatusResponse(BaseModel):
    """Response for job status query"""
    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Current job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Processing start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Processing completion timestamp")
    progress: Optional[float] = Field(None, ge=0.0, le=100.0, description="Progress percentage")
    message: Optional[str] = Field(None, description="Status message or error")
    results: Optional[DetectionResults] = Field(None, description="Detection results if completed")
    output_video_url: Optional[str] = Field(None, description="URL to download processed video")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class JobListResponse(BaseModel):
    """Response for listing jobs"""
    jobs: List[JobStatusResponse] = Field(..., description="List of jobs")
    total: int = Field(..., description="Total number of jobs")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="API status")
    version: str = Field(..., description="API version")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    timestamp: datetime = Field(..., description="Current server timestamp")


class ErrorResponse(BaseModel):
    """Error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")


class DetectionRequest(BaseModel):
    """Request body for detection with URL or base64 video"""
    video_url: Optional[str] = Field(None, description="URL to video file")
    video_base64: Optional[str] = Field(None, description="Base64 encoded video")
    parameters: Optional[DetectionParameters] = Field(None, description="Detection parameters")

    @validator('video_url', 'video_base64')
    def check_video_input(cls, v, values):
        """Ensure at least one video input is provided"""
        if not v and 'video_url' not in values and 'video_base64' not in values:
            raise ValueError('Either video_url or video_base64 must be provided')
        return v
