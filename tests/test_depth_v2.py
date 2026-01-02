"""
Standalone test for Depth Anything V2
Quick sanity check before integration
"""

import cv2
import numpy as np
import sys
from pathlib import Path

# Add backend to path
# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from services.depth_service_v2 import DepthServiceV2

def test_depth_anything_v2():
    print("="*60)
    print("Depth Anything V2 - Standalone Test")
    print("="*60)
    
    # Initialize service
    print("\n1. Initializing Depth Service V2...")
    service = DepthServiceV2()
    
    # Load model
    print("\n2. Loading model...")
    success = service.load_model()
    
    if not success:
        print("❌ Failed to load model!")
        return False
    
    print("✓ Model loaded successfully")
    
    # Create dummy image (or use real test image)
    print("\n3. Creating test image...")
    test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    print(f"   Image shape: {test_image.shape}")
    
    # Estimate depth
    print("\n4. Running depth estimation...")
    try:
        depth_map = service.estimate(test_image)
        print(f"✓ Depth map generated")
        print(f"   Shape: {depth_map.shape}")
        print(f"   Min: {depth_map.min():.4f}, Max: {depth_map.max():.4f}")
        print(f"   Mean: {depth_map.mean():.4f}")
    except Exception as e:
        print(f"❌ Depth estimation failed: {e}")
        return False
    
    # Stats
    print("\n5. Performance stats:")
    stats = service.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = test_depth_anything_v2()
    sys.exit(0 if success else 1)
