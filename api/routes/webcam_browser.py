"""
Browser-based webcam detection routes
Frontend captures video, backend processes frames
"""
import logging
import base64
import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional
import io
from PIL import Image

from api.services.frame_processor import get_frame_processor
from api.services.database_service import get_database_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/process", tags=["frame-processing"])


@router.post("/frame")
async def process_frame(
    frame_data: str = Form(..., description="Base64 encoded image frame")
):
    """
    Process a single frame from browser webcam

    Frontend captures video frame and sends as base64 image.
    Backend processes with YOLO and returns detections.

    - **frame_data**: Base64 encoded JPEG/PNG image

    Returns detection results including bounding boxes and occupancy stats.
    """
    try:
        # Decode base64 image
        if ',' in frame_data:
            # Remove data:image/jpeg;base64, prefix if present
            frame_data = frame_data.split(',')[1]

        image_bytes = base64.b64decode(frame_data)

        # Convert to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise ValueError("Failed to decode image")

        # Process frame with detection service
        processor = get_frame_processor()
        results = processor.process_frame(frame)

        return {
            "success": True,
            "detections": results['detections'],
            "occupancy": results['occupancy'],
            "timestamp": results['timestamp']
        }

    except Exception as e:
        logger.error(f"Error processing frame: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Frame processing error: {str(e)}")


@router.post("/frame-binary")
async def process_frame_binary(
    frame: UploadFile = File(..., description="Image file (JPEG/PNG)")
):
    """
    Process a single frame (binary upload)

    Alternative endpoint for binary image upload.
    """
    try:
        # Read image file
        contents = await frame.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("Failed to decode image")

        # Process frame
        processor = get_frame_processor()
        results = processor.process_frame(img)

        return {
            "success": True,
            "detections": results['detections'],
            "occupancy": results['occupancy'],
            "timestamp": results['timestamp']
        }

    except Exception as e:
        logger.error(f"Error processing frame: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Frame processing error: {str(e)}")


@router.get("/stats")
async def get_current_stats():
    """
    Get current occupancy statistics

    Returns the latest occupancy data without processing a new frame.
    """
    try:
        processor = get_frame_processor()
        stats = processor.get_current_stats()

        return {
            "success": True,
            "occupancy": stats,
            "message": "Current statistics retrieved"
        }

    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_tracking():
    """
    Reset seat tracking

    Clears all tracked seats and resets counters.
    """
    try:
        processor = get_frame_processor()
        processor.reset()

        return {
            "success": True,
            "message": "Tracking reset successfully"
        }

    except Exception as e:
        logger.error(f"Error resetting: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/seats")
async def get_all_seats():
    """
    Get all seats from database

    Returns complete list of all tracked seats with their current status.
    """
    try:
        db_service = get_database_service()
        occupancy = db_service.get_current_occupancy()

        return {
            "success": True,
            "seats": occupancy['seats'],
            "total_seats": occupancy['total_seats'],
            "occupied_seats": occupancy['occupied_seats'],
            "available_seats": occupancy['available_seats']
        }

    except Exception as e:
        logger.error(f"Error getting seats from database: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/seats/{seat_number}")
async def get_seat(seat_number: str):
    """
    Get specific seat by number

    Returns detailed information about a single seat.
    """
    try:
        db_service = get_database_service()
        seat = db_service.get_seat(seat_number)

        if not seat:
            raise HTTPException(status_code=404, detail=f"Seat {seat_number} not found")

        return {
            "success": True,
            "seat": seat.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting seat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_occupancy_history(
    seat_number: Optional[str] = None,
    limit: int = 100
):
    """
    Get occupancy history

    Returns historical occupancy events.

    - **seat_number**: Filter by specific seat (optional)
    - **limit**: Maximum number of records to return (default: 100)
    """
    try:
        db_service = get_database_service()
        history = db_service.get_seat_history(seat_number=seat_number, limit=limit)

        return {
            "success": True,
            "history": [h.to_dict() for h in history],
            "count": len(history)
        }

    except Exception as e:
        logger.error(f"Error getting history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/history")
async def get_stats_history(limit: int = 100):
    """
    Get statistics history

    Returns historical occupancy statistics snapshots.

    - **limit**: Maximum number of records to return (default: 100)
    """
    try:
        db_service = get_database_service()
        stats_history = db_service.get_stats_history(limit=limit)

        return {
            "success": True,
            "stats": [s.to_dict() for s in stats_history],
            "count": len(stats_history)
        }

    except Exception as e:
        logger.error(f"Error getting stats history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
