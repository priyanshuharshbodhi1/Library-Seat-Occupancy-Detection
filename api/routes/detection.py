"""
Detection API routes
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import aiofiles
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse

from api.models.schemas import (
    JobCreateResponse, JobStatusResponse, JobListResponse,
    DetectionParameters, JobStatus
)
from api.services.job_manager import get_job_manager
from api.services.detection_service import SeatOccupancyDetector
from api.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["detection"])

# Global detector instance (lazy loaded)
_detector: Optional[SeatOccupancyDetector] = None


def get_detector() -> SeatOccupancyDetector:
    """Get or create global detector instance"""
    global _detector
    if _detector is None:
        logger.info("Initializing SeatOccupancyDetector")
        _detector = SeatOccupancyDetector(
            weights_path=str(settings.weights_path),
            img_size=settings.model_img_size,
            conf_threshold=settings.model_conf_threshold,
            iou_threshold=settings.model_iou_threshold,
            device=settings.model_device,
            classes=settings.detection_class_list,
            occupancy_time_threshold=settings.occupancy_time_threshold,
            proximity_threshold=settings.occupancy_proximity_threshold
        )
    return _detector


@router.post("/detect", response_model=JobCreateResponse)
async def create_detection_job(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(..., description="Video file to process"),
    conf_threshold: Optional[float] = Query(None, ge=0.0, le=1.0, description="Detection confidence threshold"),
    iou_threshold: Optional[float] = Query(None, ge=0.0, le=1.0, description="IOU threshold for NMS"),
    occupancy_time_threshold: Optional[int] = Query(None, gt=0, description="Occupancy time threshold in seconds"),
    save_video: Optional[bool] = Query(True, description="Whether to save processed video"),
    include_frame_stats: Optional[bool] = Query(False, description="Include per-frame statistics")
):
    """
    Upload a video and create a detection job

    - **video**: Video file (MP4, AVI, MOV, MKV, WEBM)
    - **conf_threshold**: Override default confidence threshold
    - **iou_threshold**: Override default IOU threshold
    - **occupancy_time_threshold**: Override default occupancy time threshold
    - **save_video**: Whether to save the processed video
    - **include_frame_stats**: Include detailed per-frame statistics

    Returns a job ID that can be used to check status and download results.
    """
    # Validate file extension
    file_ext = Path(video.filename).suffix.lower().lstrip('.')
    if file_ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(settings.allowed_extensions)}"
        )

    # Validate file size
    video.file.seek(0, 2)  # Seek to end
    file_size = video.file.tell()
    video.file.seek(0)  # Reset
    if file_size > settings.max_upload_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.max_upload_size / 1024 / 1024:.0f}MB"
        )

    # Save uploaded file
    job_manager = get_job_manager()
    upload_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{video.filename}"
    upload_path = settings.upload_path / upload_filename

    try:
        async with aiofiles.open(upload_path, 'wb') as f:
            content = await video.read()
            await f.write(content)
        logger.info(f"Saved uploaded file: {upload_path}")
    except Exception as e:
        logger.error(f"Failed to save upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    # Build parameters
    parameters = {
        'save_video': save_video,
        'include_frame_stats': include_frame_stats
    }
    if conf_threshold is not None:
        parameters['conf_threshold'] = conf_threshold
    if iou_threshold is not None:
        parameters['iou_threshold'] = iou_threshold
    if occupancy_time_threshold is not None:
        parameters['occupancy_time_threshold'] = occupancy_time_threshold

    # Create job
    job = job_manager.create_job(str(upload_path), parameters)

    # Submit job for background processing
    detector = get_detector()
    background_tasks.add_task(job_manager.submit_job_async, job, detector)

    return JobCreateResponse(
        job_id=job.job_id,
        status=job.status,
        message="Job created and submitted for processing",
        created_at=job.created_at
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the status and results of a detection job

    - **job_id**: The job ID returned when creating the job

    Returns the current status, progress, and results (if completed).
    """
    job_manager = get_job_manager()
    response = job_manager.get_job_status_response(job_id)

    if not response:
        raise HTTPException(status_code=404, detail="Job not found")

    return response


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of jobs to return"),
    status: Optional[JobStatus] = Query(None, description="Filter by job status")
):
    """
    List all detection jobs

    - **limit**: Maximum number of jobs to return (default: 100)
    - **status**: Optional filter by job status

    Returns a list of jobs with their current status.
    """
    job_manager = get_job_manager()
    jobs = job_manager.list_jobs(limit=limit, status_filter=status)

    job_responses = []
    for job in jobs:
        response = job_manager.get_job_status_response(job.job_id)
        if response:
            job_responses.append(response)

    return JobListResponse(
        jobs=job_responses,
        total=len(job_responses)
    )


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a job and its associated files

    - **job_id**: The job ID to delete

    Returns success message if deleted.
    """
    job_manager = get_job_manager()
    success = job_manager.delete_job(job_id)

    if not success:
        raise HTTPException(status_code=404, detail="Job not found")

    return {"message": f"Job {job_id} deleted successfully"}


@router.get("/download/{job_id}")
async def download_result_video(job_id: str):
    """
    Download the processed video for a completed job

    - **job_id**: The job ID

    Returns the processed video file.
    """
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job is not completed yet")

    output_path = Path(job.output_path)
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Output video not found")

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"detection_result_{job_id}.mp4"
    )


@router.post("/cleanup")
async def cleanup_old_jobs(max_age_hours: int = Query(24, ge=1, description="Maximum age in hours")):
    """
    Cleanup old completed/failed jobs

    - **max_age_hours**: Maximum age in hours for jobs to keep (default: 24)

    Returns the number of jobs cleaned up.
    """
    job_manager = get_job_manager()
    initial_count = len(job_manager.jobs)
    job_manager.cleanup_old_jobs(max_age_hours=max_age_hours)
    final_count = len(job_manager.jobs)
    cleaned = initial_count - final_count

    return {
        "message": f"Cleaned up {cleaned} old jobs",
        "jobs_cleaned": cleaned,
        "jobs_remaining": final_count
    }
