"""
Job manager for handling background detection tasks
"""
import json
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List
from uuid import uuid4
import asyncio
from concurrent.futures import ThreadPoolExecutor

from api.models.schemas import JobStatus, JobStatusResponse, DetectionResults
from api.config import settings

logger = logging.getLogger(__name__)


class Job:
    """Represents a detection job"""

    def __init__(self, job_id: str, video_path: str, output_path: str, parameters: Optional[Dict] = None):
        self.job_id = job_id
        self.video_path = video_path
        self.output_path = output_path
        self.parameters = parameters or {}
        self.status = JobStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.progress: float = 0.0
        self.message: Optional[str] = None
        self.results: Optional[DetectionResults] = None
        self.error: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert job to dictionary"""
        return {
            "job_id": self.job_id,
            "video_path": self.video_path,
            "output_path": self.output_path,
            "parameters": self.parameters,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "message": self.message,
            "results": self.results.model_dump(mode='json') if self.results else None,
            "error": self.error
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Job':
        """Create job from dictionary"""
        job = cls(
            job_id=data["job_id"],
            video_path=data["video_path"],
            output_path=data["output_path"],
            parameters=data.get("parameters", {})
        )
        job.status = JobStatus(data["status"])
        job.created_at = datetime.fromisoformat(data["created_at"])
        job.started_at = datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None
        job.completed_at = datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        job.progress = data.get("progress", 0.0)
        job.message = data.get("message")
        job.error = data.get("error")
        if data.get("results"):
            job.results = DetectionResults(**data["results"])
        return job

    def save(self, jobs_dir: Path):
        """Save job state to disk"""
        job_file = jobs_dir / f"{self.job_id}.json"
        with open(job_file, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, job_id: str, jobs_dir: Path) -> Optional['Job']:
        """Load job from disk"""
        job_file = jobs_dir / f"{job_id}.json"
        if not job_file.exists():
            return None
        with open(job_file, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


class JobManager:
    """Manages background detection jobs"""

    def __init__(self, max_workers: int = 3):
        self.jobs: Dict[str, Job] = {}
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.jobs_dir = settings.jobs_path
        self.upload_dir = settings.upload_path
        self.output_dir = settings.output_path

        # Load existing jobs
        self._load_jobs()

        logger.info(f"JobManager initialized with {max_workers} workers")

    def _load_jobs(self):
        """Load existing jobs from disk"""
        for job_file in self.jobs_dir.glob("*.json"):
            try:
                with open(job_file, 'r') as f:
                    data = json.load(f)
                job = Job.from_dict(data)
                self.jobs[job.job_id] = job
                logger.info(f"Loaded job {job.job_id} with status {job.status}")
            except Exception as e:
                logger.error(f"Failed to load job from {job_file}: {e}")

    def create_job(self, video_path: str, parameters: Optional[Dict] = None) -> Job:
        """
        Create a new detection job

        Args:
            video_path: Path to uploaded video
            parameters: Optional detection parameters

        Returns:
            Created Job object
        """
        job_id = str(uuid4())
        output_filename = f"{job_id}_output.mp4"
        output_path = str(self.output_dir / output_filename)

        job = Job(
            job_id=job_id,
            video_path=video_path,
            output_path=output_path,
            parameters=parameters
        )
        job.message = "Job created, waiting to start"

        self.jobs[job_id] = job
        job.save(self.jobs_dir)

        logger.info(f"Created job {job_id}")
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        # Try memory first
        if job_id in self.jobs:
            return self.jobs[job_id]

        # Try loading from disk
        job = Job.load(job_id, self.jobs_dir)
        if job:
            self.jobs[job_id] = job
        return job

    def list_jobs(self, limit: int = 100, status_filter: Optional[JobStatus] = None) -> List[Job]:
        """
        List jobs with optional filtering

        Args:
            limit: Maximum number of jobs to return
            status_filter: Optional status to filter by

        Returns:
            List of Job objects
        """
        jobs = list(self.jobs.values())

        if status_filter:
            jobs = [j for j in jobs if j.status == status_filter]

        # Sort by creation time (newest first)
        jobs.sort(key=lambda x: x.created_at, reverse=True)

        return jobs[:limit]

    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job and its associated files

        Args:
            job_id: Job ID to delete

        Returns:
            True if deleted, False if not found
        """
        job = self.get_job(job_id)
        if not job:
            return False

        # Delete video files
        try:
            if Path(job.video_path).exists():
                Path(job.video_path).unlink()
            if Path(job.output_path).exists():
                Path(job.output_path).unlink()
        except Exception as e:
            logger.error(f"Error deleting files for job {job_id}: {e}")

        # Delete job file
        job_file = self.jobs_dir / f"{job_id}.json"
        if job_file.exists():
            job_file.unlink()

        # Remove from memory
        if job_id in self.jobs:
            del self.jobs[job_id]

        logger.info(f"Deleted job {job_id}")
        return True

    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """
        Clean up old completed/failed jobs

        Args:
            max_age_hours: Maximum age in hours for completed jobs
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        jobs_to_delete = []

        for job_id, job in self.jobs.items():
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                if job.completed_at and job.completed_at < cutoff_time:
                    jobs_to_delete.append(job_id)

        for job_id in jobs_to_delete:
            self.delete_job(job_id)
            logger.info(f"Cleaned up old job {job_id}")

        if jobs_to_delete:
            logger.info(f"Cleaned up {len(jobs_to_delete)} old jobs")

    def update_job_progress(self, job_id: str, progress: float, message: Optional[str] = None):
        """Update job progress"""
        job = self.get_job(job_id)
        if job:
            job.progress = min(100.0, max(0.0, progress))
            if message:
                job.message = message
            job.save(self.jobs_dir)

    def get_job_status_response(self, job_id: str) -> Optional[JobStatusResponse]:
        """
        Get job status as API response model

        Args:
            job_id: Job ID

        Returns:
            JobStatusResponse or None if not found
        """
        job = self.get_job(job_id)
        if not job:
            return None

        output_video_url = None
        if job.status == JobStatus.COMPLETED and Path(job.output_path).exists():
            output_video_url = f"/api/download/{job_id}"

        return JobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            progress=job.progress,
            message=job.message or job.error,
            results=job.results,
            output_video_url=output_video_url,
            metadata={
                "video_path": job.video_path,
                "parameters": job.parameters
            }
        )

    async def submit_job_async(self, job: Job, detector):
        """
        Submit a job for async processing

        Args:
            job: Job to process
            detector: SeatOccupancyDetector instance
        """
        loop = asyncio.get_event_loop()

        def run_detection():
            """Run detection in thread pool"""
            try:
                job.status = JobStatus.PROCESSING
                job.started_at = datetime.now()
                job.message = "Processing video..."
                job.save(self.jobs_dir)

                logger.info(f"Starting processing for job {job.job_id}")

                # Progress callback
                def progress_callback(current_frame, total_frames):
                    progress = (current_frame / total_frames * 100) if total_frames > 0 else 0
                    self.update_job_progress(job.job_id, progress, f"Processing frame {current_frame}/{total_frames}")

                # Run detection
                results = detector.detect_video(
                    source_path=job.video_path,
                    output_path=job.output_path,
                    save_video=job.parameters.get('save_video', True),
                    include_frame_stats=job.parameters.get('include_frame_stats', False),
                    progress_callback=progress_callback
                )

                # Update job
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
                job.progress = 100.0
                job.results = results
                job.message = f"Completed: processed {results.total_frames} frames"
                job.save(self.jobs_dir)

                logger.info(f"Completed job {job.job_id}")

            except Exception as e:
                logger.error(f"Job {job.job_id} failed: {e}", exc_info=True)
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now()
                job.error = str(e)
                job.message = f"Failed: {str(e)}"
                job.save(self.jobs_dir)

        # Submit to thread pool
        await loop.run_in_executor(self.executor, run_detection)

    def shutdown(self):
        """Shutdown the job manager"""
        logger.info("Shutting down JobManager")
        self.executor.shutdown(wait=True)


# Global job manager instance
_job_manager: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    """Get or create global job manager instance"""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager(max_workers=settings.max_concurrent_jobs)
    return _job_manager
