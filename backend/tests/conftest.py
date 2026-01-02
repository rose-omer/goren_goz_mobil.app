"""
Pytest configuration and fixtures for backend tests.
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Configure test environment
@pytest.fixture(scope="session")
def test_data_dir():
    """Create temporary test data directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_image():
    """Create a sample image array for testing."""
    # Create a simple RGB image (480x640x3)
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)


@pytest.fixture
def sample_depth_map():
    """Create a sample depth map for testing."""
    # Create a depth map with values between 0.5 and 5.0 meters
    depth = np.random.uniform(0.5, 5.0, (480, 640)).astype(np.float32)
    return depth


@pytest.fixture
def sample_detection():
    """Create a sample object detection result."""
    return {
        'name': 'person',
        'name_tr': 'insan',
        'confidence': 0.95,
        'bbox': [100, 50, 300, 400],
        'center': [200, 225],
        'distance': 1.5,
        'priority': 10,
        'region': 'center'
    }


@pytest.fixture
def mock_depth_service():
    """Create a mock depth service."""
    service = MagicMock()
    service.is_loaded = True
    service.estimate = MagicMock(return_value=np.random.uniform(0.5, 5.0, (480, 640)).astype(np.float32))
    return service


@pytest.fixture
def mock_alert_service():
    """Create a mock alert service."""
    service = MagicMock()
    service.analyze_depth = MagicMock(return_value={
        'alert_level': 'SAFE',
        'distance_stats': {'min': 0.5, 'max': 5.0, 'avg': 2.0},
        'warnings': [],
        'area_percentages': {},
        'regional_alerts': {
            'left': {'alert_level': 'SAFE', 'min_distance': 0.5, 'has_obstacle': False, 'message': 'Safe'},
            'center': {'alert_level': 'SAFE', 'min_distance': 0.5, 'has_obstacle': False, 'message': 'Safe'},
            'right': {'alert_level': 'SAFE', 'min_distance': 0.5, 'has_obstacle': False, 'message': 'Safe'}
        }
    })
    return service


@pytest.fixture
def mock_object_detection_service():
    """Create a mock object detection service."""
    service = MagicMock()
    service.is_loaded = True
    service.detect = MagicMock(return_value=[
        {
            'name': 'person',
            'name_tr': 'insan',
            'confidence': 0.95,
            'bbox': [100, 50, 300, 400],
            'center': [200, 225],
            'distance': 1.5,
            'priority': 10,
            'region': 'center'
        }
    ])
    return service
