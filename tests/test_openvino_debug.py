"""
Debug script for OpenVINO conversion
Tests MiDaS to OpenVINO conversion with detailed logging
"""

import sys
import logging
from pathlib import Path

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG level for maximum detail
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add backend to path
# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from services.depth_service import DepthService

def test_openvino_conversion():
    print("="*60)
    print("OpenVINO Conversion Debug Test")
    print("="*60)
    
    print("\n1. Initializing DepthService...")
    service = DepthService()
    
    print(f"\n2. Config check:")
    print(f"   use_openvino: {service.use_openvino}")
    print(f"   backend: {service.backend}")
    print(f"   device: {service.device}")
    
    print("\n3. Loading model (will attempt OpenVINO conversion)...")
    try:
        success = service.load_model()
        print(f"\n✓ Model load returned: {success}")
    except Exception as e:
        print(f"\n❌ Model load failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n4. Final state:")
    print(f"   backend: {service.backend}")
    print(f"   use_openvino: {service.use_openvino}")
    print(f"   is_loaded: {service.is_loaded}")
    
    # Check if OpenVINO files exist
    openvino_dir = Path("backend/models/openvino")
    if openvino_dir.exists():
        files = list(openvino_dir.glob("*"))
        print(f"\n5. OpenVINO directory contents:")
        if files:
            for f in files:
                print(f"   - {f.name} ({f.stat().st_size} bytes)")
        else:
            print("   ❌ Empty directory!")
    else:
        print("\n5. ❌ OpenVINO directory doesn't exist!")
    
    print("\n" + "="*60)
    if service.backend == "openvino":
        print("✅ SUCCESS: OpenVINO is active!")
    else:
        print("⚠️ FALLBACK: Using PyTorch (OpenVINO failed)")
    print("="*60)
    
    return service.backend == "openvino"

if __name__ == "__main__":
    success = test_openvino_conversion()
    sys.exit(0 if success else 1)
