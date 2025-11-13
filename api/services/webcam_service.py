"""
Real-time webcam detection service with WebSocket support
"""
import cv2
import time
import torch
import logging
import asyncio
import numpy as np
from typing import Optional, Dict, List, Callable
from pathlib import Path

from models.experimental import attempt_load
from utils.general import check_img_size, non_max_suppression, scale_coords, set_logging
from utils.torch_utils import select_device, TracedModel
from sort import Sort

from api.config import settings

logger = logging.getLogger(__name__)


class WebcamDetector:
    """Real-time webcam detection with seat occupancy tracking"""

    def __init__(
        self,
        weights_path: str = "yolov7.pt",
        img_size: int = 640,
        conf_threshold: float = 0.4,
        iou_threshold: float = 0.45,
        device: str = "",
        classes: Optional[List[int]] = None,
        occupancy_time_threshold: int = 10,
        proximity_threshold: int = 100
    ):
        """Initialize webcam detector"""
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
        self.start_time: float = time.time()
        self.person_moved: int = 0
        self.occupancy_stats: Dict = {
            'total_seats': 0,
            'occupied_seats': 0,
            'available_seats': 0,
            'occupancy_events': []
        }

        # Initialize model
        self.device = None
        self.model = None
        self.names = None
        self.half = False
        self.stride = None

        self._initialize_model()

        # Initialize SORT tracker
        self.sort_tracker = Sort(max_age=5, min_hits=2, iou_threshold=0.2)

        # Webcam
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False

        logger.info(f"WebcamDetector initialized with device: {self.device}")

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

    def _draw_boxes(self, img: np.ndarray, bbox: np.ndarray, categories: Optional[np.ndarray] = None) -> np.ndarray:
        """Draw bounding boxes and occupancy status on image"""
        for i, box in enumerate(bbox):
            x1, y1, x2, y2 = [int(val) for val in box]
            cat = int(categories[i]) if categories is not None else 0

            if cat == 0:  # Person
                box_key = (x1, y1, x2, y2)
                box_exist, existing_box_coord, first_person = self._is_close(box_key)

                if not box_exist and first_person:
                    obj_id = len(self.global_identities) + 1
                    self.global_identities[box_key] = {
                        'id': obj_id,
                        'start_time': time.time(),
                        'is_occupied': True
                    }
                elif box_exist:
                    if self.person_moved == 1:
                        self.person_moved = 0
                    data = self.global_identities[existing_box_coord]
                    obj_id = data['id']
                    label = f"Seat {obj_id}: Occupied"
                    (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    cv2.rectangle(img, (existing_box_coord[0], existing_box_coord[1]),
                                (existing_box_coord[2], existing_box_coord[3]), (0, 255, 0), 2)
                    cv2.rectangle(img, (existing_box_coord[0], existing_box_coord[1] - 25),
                                (existing_box_coord[0] + w, existing_box_coord[1]), (0, 255, 0), -1)
                    cv2.putText(img, label, (existing_box_coord[0], existing_box_coord[1] - 5),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, [0, 0, 0], 2)

                    # Check occupancy duration
                    duration = time.time() - data['start_time']
                    if duration >= self.occupancy_time_threshold:
                        time_label = f"Time: {duration:.1f}s - EXCEEDED"
                        cv2.putText(img, time_label, (existing_box_coord[0], existing_box_coord[1] + 20),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, [0, 0, 255], 2)
                elif not box_exist and not first_person:
                    self.person_moved = 1

            elif cat == 56:  # Chair - mark as available if no person
                # Draw chairs
                cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(img, "Chair", (x1, y1 - 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, [255, 0, 0], 2)

        return img

    def start_webcam(self, camera_index: int = 0) -> bool:
        """Start webcam capture"""
        try:
            import sys

            logger.info(f"Attempting to open camera {camera_index}...")

            # Try normal approach first
            self.cap = cv2.VideoCapture(camera_index)

            # If failed, try DirectShow on Windows
            if not self.cap.isOpened() and sys.platform == 'win32':
                logger.info("Retrying with DirectShow backend...")
                self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)

            # If still failed, try MSMF backend on Windows
            if not self.cap.isOpened() and sys.platform == 'win32':
                logger.info("Retrying with MSMF backend...")
                self.cap = cv2.VideoCapture(camera_index, cv2.CAP_MSMF)

            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {camera_index} with all backends")
                logger.error("Possible causes:")
                logger.error("  1. Camera is not connected")
                logger.error("  2. Camera is being used by another application")
                logger.error("  3. Camera permissions not granted")
                logger.error("  4. Try a different camera index (0, 1, 2)")
                return False

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

            # Try to read a test frame
            ret, frame = self.cap.read()
            if not ret or frame is None:
                logger.error("Camera opened but cannot read frames")
                self.cap.release()
                self.cap = None
                return False

            logger.info(f"Successfully read test frame: {frame.shape}")

            self.is_running = True
            logger.info(f"Webcam started successfully on camera {camera_index}")
            return True
        except Exception as e:
            logger.error(f"Failed to start webcam: {e}", exc_info=True)
            if self.cap:
                self.cap.release()
                self.cap = None
            return False

    def stop_webcam(self):
        """Stop webcam capture"""
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        logger.info("Webcam stopped")

    def process_frame(self, frame: np.ndarray) -> tuple:
        """
        Process a single frame and return annotated frame + stats

        Returns:
            (annotated_frame, occupancy_stats)
        """
        # Prepare image
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

                    if int(detclass) == 0:
                        person_count += 1
                    elif int(detclass) == 56:
                        chair_count += 1

                # Run SORT
                tracked_dets = self.sort_tracker.update(dets_to_sort)

                # Draw boxes
                if len(tracked_dets) > 0:
                    bbox_xyxy = tracked_dets[:, :4]
                    categories = tracked_dets[:, 4]
                    frame = self._draw_boxes(frame, bbox_xyxy, categories)
            else:
                self.sort_tracker.update()

        # Calculate occupancy stats
        total_seats = len(self.global_identities)
        occupied_seats = sum(1 for data in self.global_identities.values() if data.get('is_occupied', False))
        available_seats = total_seats - occupied_seats

        # Add info overlay
        info_text = [
            f"Total Seats: {total_seats}",
            f"Occupied: {occupied_seats}",
            f"Available: {available_seats}",
            f"Person Count: {person_count}",
            f"Chair Count: {chair_count}"
        ]

        y_offset = 30
        for text in info_text:
            cv2.putText(frame, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX,
                       0.7, (255, 255, 255), 2, cv2.LINE_AA)
            y_offset += 30

        # Update stats
        self.occupancy_stats = {
            'total_seats': total_seats,
            'occupied_seats': occupied_seats,
            'available_seats': available_seats,
            'person_count': person_count,
            'chair_count': chair_count,
            'seats': [
                {
                    'id': data['id'],
                    'occupied': data.get('is_occupied', False),
                    'duration': time.time() - data['start_time'],
                    'time_exceeded': (time.time() - data['start_time']) >= self.occupancy_time_threshold
                }
                for bbox, data in self.global_identities.items()
            ]
        }

        return frame, self.occupancy_stats

    async def generate_frames(self):
        """Generator for video frames (for HTTP streaming)"""
        while self.is_running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                logger.warning("Failed to read frame from webcam")
                break

            # Process frame
            annotated_frame, stats = self.process_frame(frame)

            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            if not ret:
                continue

            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            await asyncio.sleep(0.033)  # ~30 FPS

    def get_occupancy_stats(self) -> Dict:
        """Get current occupancy statistics"""
        return self.occupancy_stats

    def cleanup(self):
        """Cleanup resources"""
        self.stop_webcam()
        if hasattr(self, 'model'):
            del self.model
        torch.cuda.empty_cache()


# Global webcam detector instance
_webcam_detector: Optional[WebcamDetector] = None


def get_webcam_detector() -> WebcamDetector:
    """Get or create global webcam detector instance"""
    global _webcam_detector
    if _webcam_detector is None:
        _webcam_detector = WebcamDetector(
            weights_path=str(settings.weights_path),
            img_size=settings.model_img_size,
            conf_threshold=settings.model_conf_threshold,
            iou_threshold=settings.model_iou_threshold,
            device=settings.model_device,
            classes=settings.detection_class_list,
            occupancy_time_threshold=settings.occupancy_time_threshold,
            proximity_threshold=settings.occupancy_proximity_threshold
        )
    return _webcam_detector
