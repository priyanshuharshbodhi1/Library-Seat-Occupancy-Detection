"""
Detection service - Refactored seat occupancy detection logic
"""
import os
import cv2
import time
import torch
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from random import randint
import torch.backends.cudnn as cudnn

from models.experimental import attempt_load
from utils.datasets import LoadImages
from utils.general import (
    check_img_size, non_max_suppression, scale_coords,
    set_logging, increment_path
)
from utils.torch_utils import select_device, time_synchronized, TracedModel
from sort import Sort

from api.models.schemas import (
    DetectionResults, OccupancyEvent, BoundingBox,
    FrameStatistics
)

logger = logging.getLogger(__name__)


class SeatOccupancyDetector:
    """
    Seat occupancy detection and tracking service
    """

    def __init__(
        self,
        weights_path: str = "yolov7.pt",
        img_size: int = 640,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        device: str = "",
        classes: Optional[List[int]] = None,
        occupancy_time_threshold: int = 10,
        proximity_threshold: int = 100,
        trace: bool = True
    ):
        """
        Initialize the detector

        Args:
            weights_path: Path to model weights
            img_size: Input image size
            conf_threshold: Confidence threshold for detection
            iou_threshold: IOU threshold for NMS
            device: Device to run on ('' for auto, 'cpu', or '0' for GPU)
            classes: List of class IDs to detect (default: [0, 56] for person and chair)
            occupancy_time_threshold: Seconds before TIME EXCEEDED alert
            proximity_threshold: Pixel distance for seat matching
            trace: Whether to trace the model
        """
        self.weights_path = Path(weights_path)
        self.img_size = img_size
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.device_name = device
        self.classes = classes if classes is not None else [0, 56]
        self.occupancy_time_threshold = occupancy_time_threshold
        self.proximity_threshold = proximity_threshold
        self.trace = trace

        # State tracking
        self.global_identities: Dict = {}
        self.start_time: float = 0
        self.person_moved: int = 0
        self.occupancy_events: List[Dict] = []

        # Statistics
        self.total_detections = 0
        self.person_detections = 0
        self.chair_detections = 0
        self.frame_stats: List[FrameStatistics] = []

        # Initialize model
        self.device = None
        self.model = None
        self.names = None
        self.colors = None
        self.half = False
        self.stride = None

        self._initialize_model()

        # Initialize SORT tracker
        self.sort_tracker = Sort(max_age=5, min_hits=2, iou_threshold=0.2)

        logger.info(f"SeatOccupancyDetector initialized with device: {self.device}")

    def _initialize_model(self):
        """Initialize the YOLO model"""
        set_logging()
        self.device = select_device(self.device_name)
        self.half = self.device.type != 'cpu'

        # Load model
        logger.info(f"Loading model from {self.weights_path}")
        self.model = attempt_load(str(self.weights_path), map_location=self.device)
        self.stride = int(self.model.stride.max())
        self.img_size = check_img_size(self.img_size, s=self.stride)

        if self.trace:
            self.model = TracedModel(self.model, self.device, self.img_size)

        if self.half:
            self.model.half()

        # Get names and colors
        self.names = self.model.module.names if hasattr(self.model, 'module') else self.model.names
        self.colors = [[randint(0, 255) for _ in range(3)] for _ in self.names]

        # Run inference once for warmup
        if self.device.type != 'cpu':
            self.model(torch.zeros(1, 3, self.img_size, self.img_size)
                      .to(self.device)
                      .type_as(next(self.model.parameters())))

        logger.info("Model loaded and warmed up")

    def _is_close(self, box_key: Tuple, threshold: Optional[int] = None) -> Tuple[bool, Tuple, bool]:
        """
        Check if a bounding box is close to existing tracked seats

        Args:
            box_key: Bounding box coordinates (x1, y1, x2, y2)
            threshold: Distance threshold in pixels

        Returns:
            Tuple of (is_close, existing_box_coord, is_first_person)
        """
        if threshold is None:
            threshold = self.proximity_threshold

        if len(self.global_identities) == 0:
            return False, box_key, True

        for existing_box_coord, _ in self.global_identities.items():
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

    def _draw_boxes(
        self,
        img: np.ndarray,
        bbox: np.ndarray,
        identities: Optional[np.ndarray] = None,
        categories: Optional[np.ndarray] = None,
        offset: Tuple[int, int] = (0, 0)
    ) -> np.ndarray:
        """
        Draw bounding boxes on image

        Args:
            img: Image to draw on
            bbox: Bounding boxes
            identities: Object IDs
            categories: Object categories
            offset: Coordinate offset

        Returns:
            Image with drawn boxes
        """
        for i, box in enumerate(bbox):
            x1, y1, x2, y2 = [int(i) for i in box]
            x1 += offset[0]
            x2 += offset[0]
            y1 += offset[1]
            y2 += offset[1]
            cat = int(categories[i]) if categories is not None else 0

            if cat == 0:  # Person
                box_key = (x1, y1, x2, y2)
                box_exist, existing_box_coord, first_person = self._is_close(box_key)

                if not box_exist and first_person:
                    obj_id = len(self.global_identities) + 1
                    self.global_identities[box_key] = obj_id
                elif box_exist:
                    if self.person_moved == 1:
                        self.person_moved = 0
                    obj_id = self.global_identities[existing_box_coord]
                    label = f"{self.names[cat]} id:{obj_id}"
                    (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
                    cv2.rectangle(img, (existing_box_coord[0], existing_box_coord[1]),
                                (existing_box_coord[2], existing_box_coord[3]), (255, 0, 20), 2)
                    cv2.rectangle(img, (existing_box_coord[0], existing_box_coord[1] - 20),
                                (existing_box_coord[0] + w, existing_box_coord[1]), (255, 144, 30), -1)
                    cv2.putText(img, label, (existing_box_coord[0], existing_box_coord[1] - 5),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, [255, 255, 255], 1)
                elif not box_exist and not first_person:
                    logger.debug("Person moving")
                    self.person_moved = 1
                    self.start_time = time.time()

            elif self.person_moved == 1 and cat == 56:  # Chair
                for chair_coord, seat_id in self.global_identities.items():
                    duration = time.time() - self.start_time
                    time_exceeded = duration >= self.occupancy_time_threshold

                    if duration < self.occupancy_time_threshold:
                        label = f"Occupied for {duration:.2f} seconds"
                        color = (0, 0, 255)  # Red
                        fill = 2
                    else:
                        label = f"Occupied for {duration:.2f} seconds - TIME EXCEEDED"
                        color = (0, 0, 255)
                        fill = -1  # Filled

                    (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
                    cv2.rectangle(img, (chair_coord[0], chair_coord[1]),
                                (chair_coord[2], chair_coord[3]), color, fill)
                    cv2.rectangle(img, (chair_coord[0], chair_coord[1] - 20),
                                (chair_coord[0] + w, chair_coord[1]), color, -1)
                    cv2.putText(img, label, (chair_coord[0], chair_coord[1] - 5),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

        return img

    def detect_video(
        self,
        source_path: str,
        output_path: Optional[str] = None,
        save_video: bool = True,
        include_frame_stats: bool = False,
        progress_callback: Optional[callable] = None
    ) -> DetectionResults:
        """
        Detect and track objects in a video

        Args:
            source_path: Path to input video
            output_path: Path to save output video (optional)
            save_video: Whether to save the processed video
            include_frame_stats: Whether to include per-frame statistics
            progress_callback: Optional callback function for progress updates (frame_num, total_frames)

        Returns:
            DetectionResults object with all detection data
        """
        # Reset state
        self.global_identities = {}
        self.start_time = time.time()
        self.person_moved = 0
        self.occupancy_events = []
        self.total_detections = 0
        self.person_detections = 0
        self.chair_detections = 0
        self.frame_stats = []

        # Create dataset
        dataset = LoadImages(source_path, img_size=self.img_size, stride=self.stride)

        # Setup video writer
        vid_writer = None
        if save_video and output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        processing_start = time.time()
        total_frames = 0

        logger.info(f"Starting detection on video: {source_path}")

        # Process video frames
        for frame_idx, (path, img, im0s, vid_cap) in enumerate(dataset):
            img = torch.from_numpy(img).to(self.device)
            img = img.half() if self.half else img.float()
            img /= 255.0
            if img.ndimension() == 3:
                img = img.unsqueeze(0)

            # Inference
            pred = self.model(img, augment=False)[0]

            # Apply NMS
            pred = non_max_suppression(
                pred,
                self.conf_threshold,
                self.iou_threshold,
                classes=self.classes,
                agnostic=False
            )

            # Process detections
            for i, det in enumerate(pred):
                im0 = im0s.copy() if isinstance(im0s, np.ndarray) else im0s[i].copy()

                frame_person_count = 0
                frame_chair_count = 0

                if len(det):
                    # Rescale boxes
                    det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()

                    # Count detections
                    self.total_detections += len(det)

                    # Prepare for SORT
                    dets_to_sort = np.empty((0, 6))
                    for x1, y1, x2, y2, conf, detclass in det.cpu().detach().numpy():
                        dets_to_sort = np.vstack((
                            dets_to_sort,
                            np.array([x1, y1, x2, y2, conf, detclass])
                        ))

                        # Count by class
                        if int(detclass) == 0:
                            frame_person_count += 1
                            self.person_detections += 1
                        elif int(detclass) == 56:
                            frame_chair_count += 1
                            self.chair_detections += 1

                    # Run SORT
                    tracked_dets = self.sort_tracker.update(dets_to_sort)

                    # Draw boxes
                    if len(tracked_dets) > 0:
                        bbox_xyxy = tracked_dets[:, :4]
                        identities = tracked_dets[:, 8]
                        categories = tracked_dets[:, 4]
                        im0 = self._draw_boxes(im0, bbox_xyxy, identities, categories)
                else:
                    # Update SORT even with no detections
                    self.sort_tracker.update()

                # Collect frame statistics
                if include_frame_stats:
                    self.frame_stats.append(FrameStatistics(
                        frame_number=frame_idx,
                        total_detections=frame_person_count + frame_chair_count,
                        person_count=frame_person_count,
                        chair_count=frame_chair_count,
                        occupied_seats=len(self.global_identities)
                    ))

                # Save video
                if save_video and output_path:
                    if vid_writer is None and vid_cap:
                        fps = vid_cap.get(cv2.CAP_PROP_FPS)
                        w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        vid_writer = cv2.VideoWriter(
                            str(output_path),
                            cv2.VideoWriter_fourcc(*'mp4v'),
                            fps,
                            (w, h)
                        )
                    if vid_writer:
                        vid_writer.write(im0)

                total_frames += 1

                # Progress callback
                if progress_callback:
                    progress_callback(frame_idx + 1, dataset.nframes if hasattr(dataset, 'nframes') else total_frames)

        # Release video writer
        if vid_writer:
            vid_writer.release()

        processing_time = time.time() - processing_start
        fps = total_frames / processing_time if processing_time > 0 else 0

        logger.info(f"Detection completed: {total_frames} frames in {processing_time:.2f}s ({fps:.2f} FPS)")

        # Build occupancy events
        occupancy_events = []
        for seat_bbox, seat_id in self.global_identities.items():
            occupancy_events.append(OccupancyEvent(
                seat_id=seat_id,
                bbox=BoundingBox(x1=seat_bbox[0], y1=seat_bbox[1], x2=seat_bbox[2], y2=seat_bbox[3]),
                occupied_duration=0.0,  # Would need frame-by-frame tracking for accurate duration
                time_exceeded=False,
                first_detected_frame=0,
                last_detected_frame=total_frames - 1
            ))

        # Return results
        return DetectionResults(
            total_frames=total_frames,
            total_detections=self.total_detections,
            person_detections=self.person_detections,
            chair_detections=self.chair_detections,
            unique_tracked_objects=len(self.global_identities),
            occupancy_events=occupancy_events,
            processing_time=processing_time,
            fps=fps,
            frame_statistics=self.frame_stats if include_frame_stats else None
        )

    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'model'):
            del self.model
        torch.cuda.empty_cache()
