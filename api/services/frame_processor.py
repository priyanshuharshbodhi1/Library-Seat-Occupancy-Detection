"""
Frame processing service for browser-captured video
Processes individual frames sent from frontend
"""
import time
import torch
import logging
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path

from models.experimental import attempt_load
from utils.general import check_img_size, non_max_suppression, scale_coords, set_logging
from utils.torch_utils import select_device, TracedModel
from sort import Sort

from api.config import settings
from api.services.database_service import get_database_service

logger = logging.getLogger(__name__)


class FrameProcessor:
    """Process individual frames for seat occupancy detection"""

    def __init__(
        self,
        weights_path: str = "yolov7.pt",
        img_size: int = 640,
        conf_threshold: float = 0.15,
        iou_threshold: float = 0.45,
        device: str = "",
        classes: Optional[List[int]] = None,
        occupancy_time_threshold: int = 10,
        proximity_threshold: int = 100
    ):
        """Initialize frame processor"""
        self.weights_path = Path(weights_path)
        self.img_size = img_size
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.device_name = device
        self.classes = classes if classes is not None else [0, 56]
        self.occupancy_time_threshold = occupancy_time_threshold
        self.proximity_threshold = proximity_threshold

        # State tracking
        self.global_identities: Dict = {}
        self.frame_count = 0
        self.last_process_time = time.time()

        # Initialize model
        self.device = None
        self.model = None
        self.names = None
        self.half = False
        self.stride = None

        self._initialize_model()

        # Initialize SORT tracker
        self.sort_tracker = Sort(max_age=5, min_hits=2, iou_threshold=0.2)

        # Initialize database service
        self.db_service = get_database_service()

        logger.info(f"FrameProcessor initialized with device: {self.device}")

    def _initialize_model(self):
        """Initialize the YOLO model"""
        set_logging()
        self.device = select_device(self.device_name)
        self.half = self.device.type != 'cpu'

        logger.info(f"Loading model from {self.weights_path}")
        self.model = attempt_load(str(self.weights_path), map_location=self.device)
        self.stride = int(self.model.stride.max())
        self.img_size = check_img_size(self.img_size, s=self.stride)

        if self.half:
            self.model.half()

        self.names = self.model.module.names if hasattr(self.model, 'module') else self.model.names

        # Warmup
        if self.device.type != 'cpu':
            self.model(torch.zeros(1, 3, self.img_size, self.img_size)
                      .to(self.device)
                      .type_as(next(self.model.parameters())))

        logger.info("Model loaded and warmed up")

    def _is_close(self, box_key: tuple, threshold: Optional[int] = None) -> tuple:
        """Check if bounding box is close to existing tracked seats"""
        if threshold is None:
            threshold = self.proximity_threshold

        if len(self.global_identities) == 0:
            return False, box_key, True

        for existing_box_coord, data in self.global_identities.items():
            existing_center = np.array([
                (existing_box_coord[0] + existing_box_coord[2]) / 2,
                (existing_box_coord[1] + existing_box_coord[3]) / 2
            ])
            current_center = np.array([
                (box_key[0] + box_key[2]) / 2,
                (box_key[1] + box_key[3]) / 2
            ])
            if np.linalg.norm(existing_center - current_center) < threshold:
                return True, existing_box_coord, False

        return False, box_key, False

    def process_frame(self, frame: np.ndarray) -> Dict:
        """
        Process a single frame and return detection results

        Args:
            frame: BGR image from OpenCV

        Returns:
            Dict with detections and occupancy statistics
        """
        import cv2

        self.frame_count += 1
        current_time = time.time()

        # Prepare image for inference
        img = cv2.resize(frame, (self.img_size, self.img_size))
        img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3xHxW
        img = np.ascontiguousarray(img)

        img_tensor = torch.from_numpy(img).to(self.device)
        img_tensor = img_tensor.half() if self.half else img_tensor.float()
        img_tensor /= 255.0
        if img_tensor.ndimension() == 3:
            img_tensor = img_tensor.unsqueeze(0)

        # Inference
        with torch.no_grad():
            pred = self.model(img_tensor, augment=False)[0]

        # Apply NMS
        pred = non_max_suppression(
            pred,
            self.conf_threshold,
            self.iou_threshold,
            classes=self.classes,
            agnostic=False
        )

        # Process detections
        detections = []
        person_count = 0
        chair_count = 0

        for i, det in enumerate(pred):
            if len(det):
                # Rescale boxes
                det[:, :4] = scale_coords(img_tensor.shape[2:], det[:, :4], frame.shape).round()

                # Prepare for SORT
                dets_to_sort = np.empty((0, 6))
                for x1, y1, x2, y2, conf, detclass in det.cpu().detach().numpy():
                    dets_to_sort = np.vstack((
                        dets_to_sort,
                        np.array([x1, y1, x2, y2, conf, detclass])
                    ))

                    # Count by class
                    class_id = int(detclass)
                    if class_id == 0:
                        person_count += 1
                    elif class_id == 56:
                        chair_count += 1

                    # Add to detections list
                    detections.append({
                        'bbox': [float(x1), float(y1), float(x2), float(y2)],
                        'confidence': float(conf),
                        'class': class_id,
                        'class_name': self.names[class_id] if class_id < len(self.names) else 'unknown'
                    })

                # Run SORT tracking
                tracked_dets = self.sort_tracker.update(dets_to_sort)

                # Update seat tracking
                for track in tracked_dets:
                    x1, y1, x2, y2 = track[:4]
                    class_id = int(track[4])

                    if class_id == 0:  # Person
                        box_key = (int(x1), int(y1), int(x2), int(y2))
                        box_exist, existing_box_coord, first_person = self._is_close(box_key)

                        if not box_exist and first_person:
                            obj_id = len(self.global_identities) + 1
                            self.global_identities[box_key] = {
                                'id': obj_id,
                                'start_time': current_time,
                                'is_occupied': True,
                                'last_seen': current_time
                            }
                        elif box_exist:
                            self.global_identities[existing_box_coord]['is_occupied'] = True
                            self.global_identities[existing_box_coord]['last_seen'] = current_time
            else:
                self.sort_tracker.update()

        # Clean up old seats (not seen for 10 seconds)
        seats_to_remove = []
        for seat_coords, data in self.global_identities.items():
            if current_time - data['last_seen'] > 10:
                seats_to_remove.append(seat_coords)

        for coords in seats_to_remove:
            del self.global_identities[coords]

        # Calculate occupancy stats
        total_seats = len(self.global_identities)
        occupied_seats = sum(1 for data in self.global_identities.values() if data.get('is_occupied', False))
        available_seats = total_seats - occupied_seats

        # Build seat details
        seats = []
        for bbox, data in self.global_identities.items():
            duration = current_time - data['start_time']
            seats.append({
                'id': data['id'],
                'occupied': data.get('is_occupied', False),
                'duration': duration,
                'time_exceeded': duration >= self.occupancy_time_threshold,
                'bbox': {
                    'x1': bbox[0],
                    'y1': bbox[1],
                    'x2': bbox[2],
                    'y2': bbox[3]
                }
            })

        # Reset occupied status for next frame
        for data in self.global_identities.values():
            data['is_occupied'] = False

        self.last_process_time = current_time

        # Save to database
        try:
            # Prepare seats data for database
            seats_for_db = []
            for seat in seats:
                bbox = seat['bbox']
                seats_for_db.append({
                    'seat_number': str(seat['id']),
                    'status': 'occupied' if seat['occupied'] else 'available',
                    'person_id': seat['id'] if seat['occupied'] else None,
                    'bbox': [bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2']],
                    'duration': int(seat['duration']),
                    'duration_exceeded': seat['time_exceeded']
                })

            # Update all seats in database
            self.db_service.update_all_seats(seats_for_db)

            # Save statistics snapshot
            self.db_service.save_stats({
                'total_seats': total_seats,
                'occupied_seats': occupied_seats,
                'available_seats': available_seats,
                'person_count': person_count
            })

            logger.debug(f"Saved {len(seats_for_db)} seats to database")
        except Exception as e:
            logger.error(f"Failed to save to database: {e}")

        return {
            'detections': detections,
            'occupancy': {
                'total_seats': total_seats,
                'occupied_seats': occupied_seats,
                'available_seats': available_seats,
                'person_count': person_count,
                'chair_count': chair_count,
                'seats': seats
            },
            'timestamp': current_time,
            'frame_count': self.frame_count
        }

    def get_current_stats(self) -> Dict:
        """Get current occupancy statistics without processing a frame"""
        current_time = time.time()

        total_seats = len(self.global_identities)
        occupied_seats = sum(1 for data in self.global_identities.values() if data.get('is_occupied', False))
        available_seats = total_seats - occupied_seats

        seats = []
        for bbox, data in self.global_identities.items():
            duration = current_time - data['start_time']
            seats.append({
                'id': data['id'],
                'occupied': data.get('is_occupied', False),
                'duration': duration,
                'time_exceeded': duration >= self.occupancy_time_threshold,
                'bbox': {
                    'x1': bbox[0],
                    'y1': bbox[1],
                    'x2': bbox[2],
                    'y2': bbox[3]
                }
            })

        return {
            'total_seats': total_seats,
            'occupied_seats': occupied_seats,
            'available_seats': available_seats,
            'person_count': 0,
            'chair_count': 0,
            'seats': seats
        }

    def reset(self):
        """Reset all tracking data"""
        self.global_identities = {}
        self.frame_count = 0
        self.sort_tracker = Sort(max_age=5, min_hits=2, iou_threshold=0.2)

        # Clear database
        try:
            self.db_service.clear_all_seats()
            logger.info("Frame processor reset (including database)")
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
            logger.info("Frame processor reset (memory only)")


# Global frame processor instance
_frame_processor: Optional[FrameProcessor] = None


def get_frame_processor() -> FrameProcessor:
    """Get or create global frame processor instance"""
    global _frame_processor
    if _frame_processor is None:
        _frame_processor = FrameProcessor(
            weights_path=str(settings.weights_path),
            img_size=settings.model_img_size,
            conf_threshold=settings.model_conf_threshold,
            iou_threshold=settings.model_iou_threshold,
            device=settings.model_device,
            classes=settings.detection_class_list,
            occupancy_time_threshold=settings.occupancy_time_threshold,
            proximity_threshold=settings.occupancy_proximity_threshold
        )
    return _frame_processor
