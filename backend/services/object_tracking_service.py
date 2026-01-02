"""
Object Tracking Service
=======================

Tracks detected objects across frames to reduce false positives and
provide temporal smoothing for more reliable collision warnings.
"""

import logging
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TrackedObject:
    """Represents a tracked object across multiple frames."""
    
    object_id: str
    class_name: str
    first_seen: float
    last_seen: float
    
    # Position history (bbox center points)
    positions: deque = field(default_factory=lambda: deque(maxlen=10))
    
    # Confidence history
    confidences: deque = field(default_factory=lambda: deque(maxlen=10))
    
    # Distance history
    distances: deque = field(default_factory=lambda: deque(maxlen=10))
    
    # Detection count
    detection_count: int = 0
    
    # Stability score (0-1, higher = more stable)
    stability: float = 0.0
    
    def update(self, bbox_center: Tuple[float, float], confidence: float, distance: float):
        """Update tracked object with new detection."""
        self.last_seen = time.time()
        self.positions.append(bbox_center)
        self.confidences.append(confidence)
        self.distances.append(distance)
        self.detection_count += 1
        
        # Calculate stability based on position variance
        if len(self.positions) >= 3:
            positions_array = np.array(self.positions)
            variance = np.var(positions_array, axis=0).mean()
            # Lower variance = higher stability
            self.stability = max(0.0, min(1.0, 1.0 - variance / 100.0))
        else:
            self.stability = 0.5
    
    def get_velocity(self) -> Optional[Tuple[float, float]]:
        """Calculate object velocity (pixels/second) if enough history."""
        if len(self.positions) < 2:
            return None
        
        # Use last two positions
        p1 = np.array(self.positions[-2])
        p2 = np.array(self.positions[-1])
        
        # Time difference
        time_diff = self.last_seen - self.first_seen
        if time_diff < 0.1:  # Avoid division by zero
            return None
        
        # Velocity (pixels/second)
        velocity = (p2 - p1) / time_diff
        return tuple(velocity)
    
    def is_moving_towards_camera(self) -> bool:
        """Check if object is moving closer (distance decreasing)."""
        if len(self.distances) < 3:
            return False
        
        # Check if distance is decreasing over last 3 frames
        recent_distances = list(self.distances)[-3:]
        return recent_distances[0] > recent_distances[-1]
    
    def get_average_confidence(self) -> float:
        """Get average confidence over recent detections."""
        if not self.confidences:
            return 0.0
        return sum(self.confidences) / len(self.confidences)
    
    def get_average_distance(self) -> float:
        """Get average distance over recent detections."""
        if not self.distances:
            return 0.0
        return sum(self.distances) / len(self.distances)


class ObjectTrackingService:
    """
    Service for tracking detected objects across frames.
    
    Features:
    - Temporal smoothing to reduce false positives
    - Object persistence tracking
    - Movement direction detection
    - Stability scoring
    """
    
    def __init__(
        self,
        max_age: float = 2.0,           # Max seconds without detection before removal
        min_detections: int = 2,         # Min detections before considering object "confirmed"
        iou_threshold: float = 0.3,      # IoU threshold for matching
        position_threshold: float = 50.0  # Max pixel distance for matching
    ):
        """Initialize tracking service."""
        self.tracked_objects: Dict[str, TrackedObject] = {}
        self.max_age = max_age
        self.min_detections = min_detections
        self.iou_threshold = iou_threshold
        self.position_threshold = position_threshold
        self.next_id = 0
        
        logger.info(
            f"ObjectTrackingService initialized: "
            f"max_age={max_age}s, min_detections={min_detections}"
        )
    
    def _calculate_iou(self, box1: List[float], box2: List[float]) -> float:
        """Calculate Intersection over Union between two bounding boxes."""
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2
        
        # Intersection area
        inter_x_min = max(x1_min, x2_min)
        inter_y_min = max(y1_min, y2_min)
        inter_x_max = min(x1_max, x2_max)
        inter_y_max = min(y1_max, y2_max)
        
        if inter_x_max < inter_x_min or inter_y_max < inter_y_min:
            return 0.0
        
        inter_area = (inter_x_max - inter_x_min) * (inter_y_max - inter_y_min)
        
        # Union area
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = box1_area + box2_area - inter_area
        
        if union_area == 0:
            return 0.0
        
        return inter_area / union_area
    
    def _get_bbox_center(self, bbox: List[float]) -> Tuple[float, float]:
        """Get center point of bounding box."""
        x_min, y_min, x_max, y_max = bbox
        center_x = (x_min + x_max) / 2
        center_y = (y_min + y_max) / 2
        return (center_x, center_y)
    
    def _euclidean_distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points."""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def update(self, detections: List[Dict]) -> List[Dict]:
        """
        Update tracker with new detections.
        
        Args:
            detections: List of detected objects with keys:
                - class_name: str
                - bbox: [x_min, y_min, x_max, y_max]
                - confidence: float
                - distance: float
        
        Returns:
            List of tracked objects (filtered and smoothed)
        """
        current_time = time.time()
        
        # Match detections to existing tracks
        matched_tracks = set()
        matched_detections = set()
        
        for det_idx, detection in enumerate(detections):
            best_match_id = None
            best_match_score = 0.0
            
            bbox = detection.get('bbox', [0, 0, 0, 0])
            bbox_center = self._get_bbox_center(bbox)
            class_name = detection.get('name', 'unknown')  # ✅ Fixed: 'name' not 'class_name'
            
            # Find best matching track
            for track_id, track in self.tracked_objects.items():
                if track_id in matched_tracks:
                    continue
                
                # Must be same class
                if track.class_name != class_name:
                    continue
                
                # Check position distance
                if track.positions:
                    last_pos = track.positions[-1]
                    distance = self._euclidean_distance(bbox_center, last_pos)
                    
                    if distance < self.position_threshold:
                        # Use distance as matching score (closer = better)
                        score = 1.0 - (distance / self.position_threshold)
                        
                        if score > best_match_score:
                            best_match_score = score
                            best_match_id = track_id
            
            # Update matched track or create new one
            if best_match_id is not None and best_match_score > 0.5:
                # Update existing track
                track = self.tracked_objects[best_match_id]
                track.update(
                    bbox_center,
                    detection.get('confidence', 0.0),
                    detection.get('distance', 0.0)
                )
                matched_tracks.add(best_match_id)
                matched_detections.add(det_idx)
                
            else:
                # Create new track
                new_id = f"track_{self.next_id}"
                self.next_id += 1
                
                new_track = TrackedObject(
                    object_id=new_id,
                    class_name=class_name,
                    first_seen=current_time,
                    last_seen=current_time
                )
                new_track.update(
                    bbox_center,
                    detection.get('confidence', 0.0),
                    detection.get('distance', 0.0)
                )
                
                self.tracked_objects[new_id] = new_track
                matched_detections.add(det_idx)
        
        # Remove old tracks
        expired_tracks = []
        for track_id, track in self.tracked_objects.items():
            age = current_time - track.last_seen
            if age > self.max_age:
                expired_tracks.append(track_id)
        
        for track_id in expired_tracks:
            del self.tracked_objects[track_id]
        
        # Build output: only confirmed tracks
        confirmed_objects = []
        for track in self.tracked_objects.values():
            # Must have minimum detections to be confirmed
            if track.detection_count >= self.min_detections:
                confirmed_objects.append({
                    'track_id': track.object_id,
                    'name': track.class_name,  # ✅ Fixed: return 'name' not 'class_name'
                    'confidence': track.get_average_confidence(),
                    'distance': track.get_average_distance(),
                    'stability': track.stability,
                    'is_approaching': track.is_moving_towards_camera(),
                    'detection_count': track.detection_count,
                    'age': current_time - track.first_seen
                })
        
        logger.debug(
            f"Tracking: {len(detections)} detections → "
            f"{len(confirmed_objects)} confirmed objects "
            f"(total tracks: {len(self.tracked_objects)})"
        )
        
        # ✅ Proactive cleanup if too many tracks
        if len(self.tracked_objects) > 50:
            self._cleanup_old_tracks()
        
        return confirmed_objects
    
    def _cleanup_old_tracks(self):
        """Cleanup old tracks to prevent memory leak."""
        current_time = time.time()
        removed = 0
        
        # Remove tracks older than max_age
        expired = [
            track_id for track_id, track in self.tracked_objects.items()
            if (current_time - track.last_seen) > self.max_age
        ]
        
        for track_id in expired:
            del self.tracked_objects[track_id]
            removed += 1
        
        if removed > 0:
            logger.info(f"Cleaned up {removed} old tracks (total: {len(self.tracked_objects)})")
    
    def get_critical_objects(self) -> List[Dict]:
        """Get list of critical objects that are approaching."""
        critical = []
        for track in self.tracked_objects.values():
            if track.detection_count >= self.min_detections:
                if track.is_moving_towards_camera():
                    critical.append({
                        'track_id': track.object_id,
                        'name': track.class_name,  # ✅ Fixed
                        'distance': track.get_average_distance(),
                        'approaching': True
                    })
        return critical
    
    def reset(self):
        """Reset all tracking state."""
        self.tracked_objects.clear()
        self.next_id = 0
        logger.info("Tracking state reset")


# Singleton instance
_tracking_service: Optional[ObjectTrackingService] = None


def get_tracking_service() -> ObjectTrackingService:
    """Get or create the tracking service singleton."""
    global _tracking_service
    if _tracking_service is None:
        _tracking_service = ObjectTrackingService()
    return _tracking_service
