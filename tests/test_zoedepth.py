"""
Standalone test for ZoeDepth (Metric Depth)
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

from services.zoedepth_service import ZoeDepthService

def test_zoedepth():
    print("="*60)
    print("ZoeDepth (Metric Depth) - Standalone Test")
    print("="*60)
    
    # Initialize service
    print("\n1. Initializing ZoeDepth Service...")
    service = ZoeDepthService()
    
    # Load model (will download ~100MB on first run)
    print("\n2. Loading ZoeDepth model...")
    print("   NOTE: First run will download ~100MB from PyTorch Hub")
    print("   This may take a few minutes...")
    
    success = service.load_model()
    
    if not success:
        print("❌ Failed to load model!")
        return False
    
    print("✓ Model loaded successfully")
    
    # Create dummy image (or use real test image)
    print("\n3. Creating test image...")
    # Simple gradient image for testing
    test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    print(f"   Image shape: {test_image.shape}")
    
    # Estimate depth
    print("\n4. Running metric depth estimation...")
    try:
        depth_map = service.estimate(test_image)
        print(f"✓ Depth map generated")
        print(f"   Shape: {depth_map.shape}")
        print(f"   Min: {depth_map.min():.2f} meters")
        print(f"   Max: {depth_map.max():.2f} meters")
        print(f"   Mean: {depth_map.mean():.2f} meters")
        
        # Test specific point
        h, w = depth_map.shape
        center_x, center_y = w // 2, h // 2
        center_distance = service.get_distance_at_point(depth_map, center_x, center_y)
        print(f"   Center point distance: {center_distance:.2f} meters")
        
    except Exception as e:
        print(f"❌ Depth estimation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Stats
    print("\n5. Performance stats:")
    stats = service.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nNOTE: Depth values are in METERS (absolute distance)")
    print("Example: 2.5 means the object is 2.5 meters away")
    
    return True

if __name__ == "__main__":
    success = test_zoedepth()
    sys.exit(0 if success else 1)
