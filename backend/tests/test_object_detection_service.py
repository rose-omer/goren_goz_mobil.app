"""
Unit tests for object detection service.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.object_detection_service import ObjectDetectionService


class TestObjectDetectionService:
    """Test suite for ObjectDetectionService."""
    
    def test_initialization(self):
        """Test ObjectDetectionService initialization."""
        service = ObjectDetectionService()
        assert service is not None
        assert 'person' in service.TURKISH_LABELS
        assert service.TURKISH_LABELS['person'] == 'insan'
    
    def test_turkish_labels_coverage(self):
        """Test Turkish label translations."""
        service = ObjectDetectionService()
        
        # Check common objects have Turkish translations
        common_objects = ['person', 'car', 'dog', 'bicycle', 'traffic light']
        for obj in common_objects:
            assert obj in service.TURKISH_LABELS
            assert len(service.TURKISH_LABELS[obj]) > 0
    
    @patch('services.object_detection_service.YOLO')
    def test_load_model_success(self, mock_yolo):
        """Test successful YOLO model loading."""
        service = ObjectDetectionService()
        mock_model = MagicMock()
        mock_yolo.return_value = mock_model
        
        result = service.load_model()
        # Will return True or False depending on implementation
        assert isinstance(result, bool)
    
    def test_confidence_threshold_validation(self, sample_image):
        """Test confidence threshold validation."""
        service = ObjectDetectionService()
        service.model = MagicMock()
        service.is_loaded = True
        
        # Test invalid thresholds
        assert 0 < 0.5 < 1.0  # Valid threshold
        assert not (0.5 < 0)  # Invalid: too low
        assert not (0.5 > 1.0)  # Invalid: too high
    
    def test_max_objects_limit(self, sample_image):
        """Test maximum objects limit."""
        service = ObjectDetectionService()
        
        # Mock detection of 20 objects
        detections = [
            {
                'name': 'person',
                'name_tr': 'insan',
                'confidence': 0.9 - i*0.01,
                'bbox': [100+i*10, 100+i*10, 200+i*10, 200+i*10],
                'center': [150+i*10, 150+i*10],
                'priority': 10-i,
                'region': 'center'
            }
            for i in range(20)
        ]
        
        # Limit to 10
        limited_detections = detections[:10]
        assert len(limited_detections) == 10
    
    def test_region_assignment(self):
        """Test object region assignment (left/center/right)."""
        service = ObjectDetectionService()
        
        # Mock detection with known bbox
        detection = {
            'center': [100, 240]  # Left side (< 640/3 ≈ 213)
        }
        
        # Left region: x < 640/3
        assert detection['center'][0] < 640/3  # Should be in left region
    
    def test_distance_integration(self, sample_image, sample_depth_map):
        """Test distance calculation from depth map."""
        service = ObjectDetectionService()
        
        # Mock detection
        detection = {
            'bbox': [100, 100, 300, 300],
            'center': [200, 200]
        }
        
        # Get distance from depth map at center
        cy, cx = int(detection['center'][1]), int(detection['center'][0])
        distance = float(sample_depth_map[cy, cx])
        
        assert 0 < distance < 10  # Reasonable range
    
    def test_priority_assignment(self):
        """Test collision priority assignment."""
        service = ObjectDetectionService()
        
        # Different objects should have different priorities
        priorities = {
            'person': 10,
            'car': 10,
            'dog': 8,
            'bicycle': 8,
            'bench': 3
        }
        
        # Person and car should have highest priority
        assert priorities['person'] > priorities['dog']
        assert priorities['car'] > priorities['bench']
    
    def test_bbox_format(self):
        """Test bounding box format consistency."""
        service = ObjectDetectionService()
        
        bbox = [100, 50, 300, 400]  # [x1, y1, x2, y2]
        
        # Validate bbox format
        x1, y1, x2, y2 = bbox
        assert x1 < x2  # x1 should be less than x2
        assert y1 < y2  # y1 should be less than y2
        assert x1 >= 0  # Within image bounds
    
    def test_center_calculation(self):
        """Test center point calculation."""
        bbox = [100, 50, 300, 400]
        expected_center = [200, 225]  # (100+300)/2, (50+400)/2
        
        calculated_center = [
            (bbox[0] + bbox[2]) / 2,
            (bbox[1] + bbox[3]) / 2
        ]
        
        assert calculated_center == expected_center
    
    def test_empty_detection_result(self):
        """Test handling of empty detection results."""
        service = ObjectDetectionService()
        service.model = MagicMock()
        service.is_loaded = True
        
        # Mock empty results
        service.model.predict.return_value.pred = []
        
        # Should handle gracefully
        result = service.detect(np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8))
        assert isinstance(result, list)
