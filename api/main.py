"""
FastAPI main application for Library Seat Occupancy Detection
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.config import settings
from api.routes import detection, webcam, webcam_browser
from api.models.schemas import HealthResponse, ErrorResponse
from api.services.job_manager import get_job_manager
from api.models.database import init_db

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting API server...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Model weights: {settings.weights_path}")

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    # Initialize job manager
    job_manager = get_job_manager()
    logger.info(f"Job manager initialized with {job_manager.max_workers} workers")

    # Cleanup old jobs on startup
    job_manager.cleanup_old_jobs(max_age_hours=settings.job_cleanup_after_hours)

    yield

    # Shutdown
    logger.info("Shutting down API server...")
    job_manager.shutdown()


# Create FastAPI app
app = FastAPI(
    title="Library Seat Occupancy Detection API",
    description="""
    Real-time library seat occupancy detection API using YOLOv7 and SORT tracking.

    ## Features

    * 📹 Video upload and processing
    * 🔍 Person and chair detection
    * 📊 Seat occupancy tracking
    * ⏱️ Time-based occupancy alerts
    * 🎥 Processed video download
    * 📈 Detailed detection statistics

    ## Workflow

    1. Upload a video using POST /api/detect
    2. Receive a job_id to track progress
    3. Poll GET /api/jobs/{job_id} for status
    4. Download results when status is "completed"
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
if settings.cors_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"CORS enabled for origins: {settings.cors_origins_list}")

# Include routers
app.include_router(detection.router)
app.include_router(webcam.router)
app.include_router(webcam_browser.router)

# Mount static files
static_path = settings.base_dir / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    logger.info(f"Mounted static files from {static_path}")


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """
    Health check endpoint

    Returns the API status and basic information.
    """
    model_loaded = False
    try:
        from api.routes.detection import _detector
        model_loaded = _detector is not None
    except Exception:
        pass

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        model_loaded=model_loaded,
        timestamp=datetime.now()
    )


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint

    Serves the frontend monitoring dashboard or returns API information.
    """
    # Try new app first, fallback to old index
    static_app = settings.base_dir / "static" / "app.html"
    static_index = settings.base_dir / "static" / "index.html"

    if static_app.exists():
        return FileResponse(static_app)
    elif static_index.exists():
        return FileResponse(static_index)

    return {
        "message": "Library Seat Occupancy Detection API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "monitor": "/",
        "endpoints": {
            "detect": "POST /api/detect - Upload video for detection",
            "status": "GET /api/jobs/{job_id} - Get job status",
            "download": "GET /api/download/{job_id} - Download results",
            "list_jobs": "GET /api/jobs - List all jobs",
            "delete_job": "DELETE /api/jobs/{job_id} - Delete a job",
            "webcam_start": "POST /api/webcam/start - Start webcam detection",
            "webcam_stop": "POST /api/webcam/stop - Stop webcam detection",
            "webcam_stream": "GET /api/webcam/stream - Video stream",
            "webcam_occupancy": "GET /api/webcam/occupancy - Get occupancy data"
        }
    }


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTPException",
            message=exc.detail,
            timestamp=datetime.now()
        ).model_dump(mode='json')
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="ValidationError",
            message="Request validation failed",
            detail=str(exc),
            timestamp=datetime.now()
        ).model_dump(mode='json')
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            detail=str(exc) if settings.debug else None,
            timestamp=datetime.now()
        ).model_dump(mode='json')
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower()
    )
