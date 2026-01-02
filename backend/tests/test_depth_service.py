"""
Unit tests for depth estimation service.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from pathlib import Path

# Import after path setup
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.depth_service import DepthService


class TestDepthService:
    """Test suite for DepthService."""
    
    def test_initialization(self):
        """Test DepthService initialization."""
        service = DepthService()
        assert service is not None
        assert service.model_type in service.SUPPORTED_MODELS
        assert service.min_depth == 0.5
        assert service.max_depth == 5.0
    
    def test_supported_models(self):
        """Test all supported model types."""
        service = DepthService()
        assert 'DPT_Large' in service.SUPPORTED_MODELS
        assert 'DPT_Hybrid' in service.SUPPORTED_MODELS
        assert 'MiDaS_small' in service.SUPPORTED_MODELS
    
    @patch('services.depth_service.torch.hub.load')
    def test_load_pytorch_model_success(self, mock_hub_load):
        """Test successful PyTorch model loading."""
        service = DepthService()
        service.use_openvino = False
        
        # Mock model and transforms
        mock_model = MagicMock()
        mock_transforms = MagicMock()
        mock_hub_load.side_effect = [mock_model, mock_transforms]
        
        result = service._load_pytorch_model()
        assert result == True
        assert mock_hub_load.call_count >= 2
    
    @patch('services.depth_service.torch.hub.load')
    def test_load_pytorch_model_failure(self, mock_hub_load):
        """Test PyTorch model loading failure."""
        service = DepthService()
        service.use_openvino = False
        mock_hub_load.side_effect = Exception("Download failed")
        
        result = service._load_pytorch_model()
        assert result == False
    
    def test_depth_value_range(self, sample_image):
        """Test that depth estimation returns valid values."""
        service = DepthService()
        # Mock the model
        service.model = MagicMock()
        service.transform = MagicMock(return_value=sample_image)
        service.is_loaded = True
        
        # Mock depth prediction
        predicted_depth = np.random.uniform(0.5, 5.0, (480, 640))
        service.model.return_value = predicted_depth
        
        assert predicted_depth.min() >= service.min_depth
        assert predicted_depth.max() <= service.max_depth
    
    def test_statistics_tracking(self):
        """Test inference statistics tracking."""
        service = DepthService()
        assert service.inference_count == 0
        assert service.total_inference_time == 0.0
        
        # Simulate inference
        service.inference_count = 100
        service.total_inference_time = 15000.0  # 15 seconds
        
        avg_time = service.total_inference_time / service.inference_count
        assert avg_time == pytest.approx(150.0, rel=0.01)  # ~150ms per inference
    
    def test_device_selection_cpu(self):
        """Test CPU device selection."""
        service = DepthService()
        if service.backend == "pytorch":
            assert "cpu" in service.device.lower() or service.device == "cpu"
    
    def test_device_selection_cuda_if_available(self):
        """Test CUDA device selection if available."""
        import torch
        service = DepthService()
        if service.backend == "pytorch" and torch.cuda.is_available():
            assert "cuda" in service.device.lower()
