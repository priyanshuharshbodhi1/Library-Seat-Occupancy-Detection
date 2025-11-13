"""
Webcam detection API routes for real-time monitoring
"""
import logging
import asyncio
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional

from api.services.webcam_service import get_webcam_detector
from api.models.schemas import ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webcam", tags=["webcam"])


@router.post("/start")
async def start_webcam(camera_index: int = Query(0, ge=0, description="Camera index (0 for default camera)")):
    """
    Start webcam detection

    - **camera_index**: Camera index to use (default: 0)

    Returns success message if webcam started successfully.
    """
    try:
        detector = get_webcam_detector()

        if detector.is_running:
            return {
                "message": "Webcam is already running",
                "status": "running",
                "camera_index": camera_index
            }

        success = detector.start_webcam(camera_index)

        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start webcam on camera {camera_index}"
            )

        return {
            "message": f"Webcam started successfully on camera {camera_index}",
            "status": "running",
            "camera_index": camera_index
        }

    except Exception as e:
        logger.error(f"Error starting webcam: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_webcam():
    """
    Stop webcam detection

    Returns success message if webcam stopped successfully.
    """
    try:
        detector = get_webcam_detector()

        if not detector.is_running:
            return {
                "message": "Webcam is not running",
                "status": "stopped"
            }

        detector.stop_webcam()

        return {
            "message": "Webcam stopped successfully",
            "status": "stopped"
        }

    except Exception as e:
        logger.error(f"Error stopping webcam: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_webcam_status():
    """
    Get webcam status

    Returns current status of the webcam detection.
    """
    try:
        detector = get_webcam_detector()

        return {
            "status": "running" if detector.is_running else "stopped",
            "is_running": detector.is_running,
            "occupancy_stats": detector.get_occupancy_stats() if detector.is_running else None
        }

    except Exception as e:
        logger.error(f"Error getting webcam status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stream")
async def video_stream():
    """
    Stream video with real-time detection

    Returns MJPEG stream of the processed video with bounding boxes and occupancy information.

    Access this endpoint in an <img> tag or video player that supports MJPEG streams.
    Example: <img src="http://localhost:8000/api/webcam/stream" />
    """
    try:
        detector = get_webcam_detector()

        if not detector.is_running:
            raise HTTPException(
                status_code=400,
                detail="Webcam is not running. Start it first using POST /api/webcam/start"
            )

        return StreamingResponse(
            detector.generate_frames(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/occupancy")
async def get_occupancy():
    """
    Get current seat occupancy statistics

    Returns real-time occupancy data including:
    - Total seats
    - Occupied seats
    - Available seats
    - Individual seat status with duration and time exceeded alerts

    Poll this endpoint regularly to get updated occupancy information.
    """
    try:
        detector = get_webcam_detector()

        if not detector.is_running:
            return {
                "status": "stopped",
                "message": "Webcam is not running",
                "data": None
            }

        stats = detector.get_occupancy_stats()

        return {
            "status": "running",
            "message": "Occupancy data retrieved successfully",
            "data": stats,
            "timestamp": asyncio.get_event_loop().time()
        }

    except Exception as e:
        logger.error(f"Error getting occupancy data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-camera")
async def test_camera(camera_index: int = Query(0, ge=0, description="Camera index to test")):
    """
    Test if a camera is accessible

    - **camera_index**: Camera index to test (default: 0)

    Returns information about camera availability and details.
    """
    try:
        import cv2

        logger.info(f"Testing camera {camera_index}...")

        # Try to open the camera
        cap = cv2.VideoCapture(camera_index)

        if not cap.isOpened():
            # Try with DirectShow on Windows
            cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)

        if not cap.isOpened():
            return {
                "success": False,
                "camera_index": camera_index,
                "message": f"Camera {camera_index} could not be opened",
                "suggestions": [
                    "Check if camera is connected",
                    "Try a different camera index (0, 1, 2)",
                    "Close other applications using the camera",
                    "Check camera permissions in Windows Settings",
                    "Restart your computer"
                ]
            }

        # Get camera properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        # Try to read a frame
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return {
                "success": False,
                "camera_index": camera_index,
                "message": f"Camera {camera_index} opened but could not read frame",
                "camera_info": {
                    "width": width,
                    "height": height,
                    "fps": fps
                },
                "suggestions": [
                    "Camera might be in use by another application",
                    "Try restarting the application",
                    "Check camera drivers"
                ]
            }

        return {
            "success": True,
            "camera_index": camera_index,
            "message": f"Camera {camera_index} is working correctly!",
            "camera_info": {
                "width": width,
                "height": height,
                "fps": fps,
                "frame_shape": list(frame.shape) if frame is not None else None
            }
        }

    except Exception as e:
        logger.error(f"Error testing camera: {e}", exc_info=True)
        return {
            "success": False,
            "camera_index": camera_index,
            "message": "Error testing camera",
            "error": str(e),
            "suggestions": [
                "Install OpenCV: pip install opencv-python",
                "Check if camera is physically connected",
                "Try a different camera index"
            ]
        }
