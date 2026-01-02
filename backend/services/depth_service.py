"""
Depth Estimation Service with OpenVINO Support
================================================

Wrapper for MiDaS depth estimation model with OpenVINO optimization.
Provides 3-5x speedup on Intel GPUs/CPUs.
"""

import torch
import cv2
import numpy as np
import logging
import time
from typing import Optional, Tuple
from pathlib import Path

from core.config import get_settings

logger = logging.getLogger(__name__)

# Try to import OpenVINO
try:
    import openvino as ov
    OPENVINO_AVAILABLE = True
except ImportError:
    OPENVINO_AVAILABLE = False
    logger.warning("OpenVINO not available. Install with: pip install openvino")


class DepthService:
    """
    Singleton service for depth estimation using MiDaS.
    
    Supports both PyTorch and OpenVINO backends.
    OpenVINO provides 3-5x speedup on Intel hardware.
    """
    
    SUPPORTED_MODELS = {
        "DPT_Large": "DPT_Large",
        "DPT_Hybrid": "DPT_Hybrid",
        "MiDaS_small": "MiDaS_small"
    }
    
    def __init__(self):
        """Initialize depth service."""
        self.settings = get_settings()
        self.model_type = self.settings.model_type
        self.min_depth = self.settings.min_depth
        self.max_depth = self.settings.max_depth
        self.use_openvino = self.settings.use_openvino and OPENVINO_AVAILABLE
        
        # Device selection
        if self.use_openvino:
            self.backend = "openvino"
            self.device = self.settings.openvino_device  # GPU, CPU, AUTO (string for OpenVINO)
            self.pytorch_device = None  # Not used
            logger.info(f"Using OpenVINO backend with device: {self.device}")
        else:
            self.backend = "pytorch"
            device_setting = self.settings.model_device
            if device_setting == "auto":
                self.pytorch_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            else:
                self.pytorch_device = torch.device(device_setting)
            self.device = str(self.pytorch_device)  # String representation
            logger.info(f"Using PyTorch backend with device: {self.device}")
        
        # Model (lazy loading)
        self.model = None
        self.transform = None
        self.is_loaded = False
        
        # OpenVINO specific
        self.ov_model = None
        self.ov_compiled_model = None
        self.input_layer = None
        self.output_layer = None
        
        # Statistics
        self.inference_count = 0
        self.total_inference_time = 0.0
    
    def load_model(self) -> bool:
        """
        Load MiDaS model (PyTorch or OpenVINO).
        
        Returns:
            bool: Success status
        """
        if self.is_loaded:
            return True
        
        try:
            logger.info(f"Loading MiDaS model: {self.model_type} ({self.backend})...")
            start_time = time.time()
            
            if self.use_openvino:
                success = self._load_openvino_model()
            else:
                success = self._load_pytorch_model()
            
            if success:
                load_time = time.time() - start_time
                self.is_loaded = True
                logger.info(
                    f"✓ Model loaded successfully! "
                    f"Backend: {self.backend}, Time: {load_time:.2f}s, Device: {self.device}"
                )
            
            return success
        
        except Exception as e:
            logger.error(f"Model loading failed: {e}", exc_info=True)
            self.is_loaded = False
            return False
    
    def _load_pytorch_model(self) -> bool:
        """Load PyTorch MiDaS model."""
        try:
            # Load MiDaS model
            self.model = torch.hub.load(
                "intel-isl/MiDaS",
                self.model_type,
                pretrained=True,
                skip_validation=True
            )
            
            # Load transform
            midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
            
            if self.model_type in ["DPT_Large", "DPT_Hybrid"]:
                self.transform = midas_transforms.dpt_transform
            else:
                self.transform = midas_transforms.small_transform
            
            # Move to device
            self.model.to(self.pytorch_device)
            self.model.eval()
            
            return True
        except Exception as e:
            logger.error(f"PyTorch model loading failed: {e}")
            return False
    
    def _load_openvino_model(self) -> bool:
        """Load OpenVINO optimized model."""
        if not OPENVINO_AVAILABLE:
            logger.error("OpenVINO not available")
            return False
        
        try:
            # Check if converted model exists
            model_dir = Path("models/openvino")
            model_dir.mkdir(parents=True, exist_ok=True)
            
            model_xml = model_dir / f"{self.model_type}.xml"
            model_bin = model_dir / f"{self.model_type}.bin"
            
            if not model_xml.exists():
                logger.info("OpenVINO model not found, converting from PyTorch...")
                success = self._convert_to_openvino()
                if not success:
                    logger.warning("OpenVINO conversion failed, falling back to PyTorch")
                    self.use_openvino = False
                    self.backend = "pytorch"
                    return self._load_pytorch_model()
            
            # Load OpenVINO model
            logger.info(f"Loading OpenVINO model from {model_xml}")
            core = ov.Core()
            self.ov_model = core.read_model(model=str(model_xml))
            
            # Compile model
            self.ov_compiled_model = core.compile_model(self.ov_model, self.device)
            
            # Get input/output layers
            self.input_layer = self.ov_compiled_model.input(0)
            self.output_layer = self.ov_compiled_model.output(0)
            
            logger.info(f"✓ OpenVINO model compiled for {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"OpenVINO model loading failed: {e}", exc_info=True)
            logger.warning("Falling back to PyTorch")
            self.use_openvino = False
            self.backend = "pytorch"
            return self._load_pytorch_model()
    
    def _convert_to_openvino(self) -> bool:
        """Convert PyTorch MiDaS model to OpenVINO IR format."""
        try:
            logger.info("Converting MiDaS to OpenVINO format...")
            
            # First load PyTorch model
            if not self._load_pytorch_model():
                return False
            
            # Prepare dummy input (MiDaS small uses 256x256)
            if self.model_type == "MiDaS_small":
                input_size = (1, 3, 256, 256)
            else:
                input_size = (1, 3, 384, 384)
            
            dummy_input = torch.randn(input_size)
            
            # Export to ONNX first
            onnx_path = Path("models/openvino") / f"{self.model_type}.onnx"
            onnx_path.parent.mkdir(parents=True, exist_ok=True)
            
            torch.onnx.export(
                self.model,
                dummy_input,
                str(onnx_path),
                input_names=['input'],
                output_names=['output'],
                opset_version=17,  # ✅ Updated from 11 to 17 for better OpenVINO compatibility
                dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
            )
            
            logger.info(f"✓ ONNX model saved to {onnx_path}")
            
            # Convert ONNX to OpenVINO IR (using new API)
            import openvino as ov
            
            model_xml = onnx_path.with_suffix('.xml')
            
            # New OpenVINO API (replaces deprecated mo.convert_model)
            ov_model = ov.convert_model(str(onnx_path))
            ov.save_model(ov_model, str(model_xml))
            
            logger.info(f"✓ OpenVINO IR model saved to {model_xml}")
            return True
            
        except Exception as e:
            logger.error(f"Model conversion failed: {e}", exc_info=True)
            return False
    
    def estimate(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Estimate depth map from image.
        
        Args:
            image: Input image (BGR, numpy array)
        
        Returns:
            Optional[np.ndarray]: Depth map in meters (float32) or None on error
        """
        # Ensure model is loaded
        if not self.is_loaded:
            if not self.load_model():
                return None
        
        if image is None or image.size == 0:
            logger.warning("Empty image received")
            return None
        
        try:
            start_time = time.time()
            
            if self.use_openvino:
                depth_map = self._estimate_openvino(image)
            else:
                depth_map = self._estimate_pytorch(image)
            
            # Update statistics
            inference_time = time.time() - start_time
            self.inference_count += 1
            self.total_inference_time += inference_time
            
            logger.debug(
                f"Depth estimation ({self.backend}): {inference_time*1000:.1f}ms"
            )
            
            return depth_map
        
        except Exception as e:
            logger.error(f"Depth estimation error: {e}", exc_info=True)
            return None
    
    def _estimate_pytorch(self, image: np.ndarray) -> Optional[np.ndarray]:
        """PyTorch inference."""
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Apply transform
        input_batch = self.transform(rgb_image).to(self.pytorch_device)
        
        # Inference
        with torch.no_grad():
            prediction = self.model(input_batch)
            prediction = prediction.squeeze().cpu().numpy()
        
        # Post-process
        return self._postprocess_depth(prediction, image.shape[:2])
    
    def _estimate_openvino(self, image: np.ndarray) -> Optional[np.ndarray]:
        """OpenVINO inference (3-5x faster!)."""
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Prepare input (resize and normalize)
        if self.model_type == "MiDaS_small":
            input_size = (256, 256)
        else:
            input_size = (384, 384)
        
        resized = cv2.resize(rgb_image, input_size)
        
        # Normalize to [-1, 1]
        normalized = (resized.astype(np.float32) / 127.5) - 1.0
        
        # CHW format
        input_data = np.transpose(normalized, (2, 0, 1))
        input_data = np.expand_dims(input_data, 0)
        
        # Inference
        result = self.ov_compiled_model([input_data])[self.output_layer]
        prediction = result.squeeze()
        
        # Post-process
        return self._postprocess_depth(prediction, image.shape[:2])
    
    def _postprocess_depth(self, prediction: np.ndarray, target_shape: Tuple[int, int]) -> np.ndarray:
        """Post-process depth map."""
        # Normalize to 0-1
        depth_min = prediction.min()
        depth_max = prediction.max()
        
        if depth_max - depth_min > 0:
            normalized_depth = (prediction - depth_min) / (depth_max - depth_min)
        else:
            normalized_depth = np.zeros_like(prediction)
        
        # Convert to metric depth (meters)
        depth_range = self.max_depth - self.min_depth
        metric_depth = self.max_depth - (normalized_depth * depth_range)
        
        # Resize to original image size
        if metric_depth.shape != target_shape:
            target_height, target_width = target_shape
            metric_depth = cv2.resize(
                metric_depth,
                (target_width, target_height),
                interpolation=cv2.INTER_CUBIC
            )
        
        return metric_depth
    
    def get_stats(self) -> dict:
        """Get performance statistics."""
        avg_time = (
            self.total_inference_time / self.inference_count
            if self.inference_count > 0
            else 0
        )
        
        return {
            "backend": self.backend,
            "model_type": self.model_type,
            "device": str(self.device),
            "is_loaded": self.is_loaded,
            "inference_count": self.inference_count,
            "avg_inference_time_ms": avg_time * 1000,
            "total_time_seconds": self.total_inference_time
        }
    
    def unload_model(self):
        """Unload model from memory."""
        if self.model is not None:
            del self.model
            self.model = None
        
        if self.transform is not None:
            del self.transform
            self.transform = None
        
        if self.ov_compiled_model is not None:
            del self.ov_compiled_model
            self.ov_compiled_model = None
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self.is_loaded = False
        logger.info("Model unloaded from memory")


# Singleton instance
_depth_service: Optional[DepthService] = None


def get_depth_service() -> DepthService:
    """Get or create depth service singleton."""
    global _depth_service
    if _depth_service is None:
        _depth_service = DepthService()
    return _depth_service
