#!/usr/bin/env python3
"""
VLM Server Testing Script
=========================

Test script to verify VLM (Ollama/llama.cpp) integration.
"""

import asyncio
import sys
from pathlib import Path
import numpy as np
import cv2

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from services.vlm_service import get_vlm_service
from services.image_service import get_image_service


async def test_vlm_connection():
    """Test 1: Check if VLM server is running."""
    print("\n" + "="*70)
    print("TEST 1: VLM Server Connection")
    print("="*70)
    
    vlm_service = get_vlm_service()
    is_ready = await vlm_service.is_server_ready()
    
    if is_ready:
        print("✅ VLM Server is READY")
        print(f"   Server URL: {vlm_service.server_url}")
        return True
    else:
        print("❌ VLM Server is NOT READY")
        print("   Make sure Ollama is running:")
        print("   $ ollama serve")
        return False


async def test_vlm_with_sample_image():
    """Test 2: Ask VLM a question about a sample image."""
    print("\n" + "="*70)
    print("TEST 2: VLM Image Analysis")
    print("="*70)
    
    # Create a simple test image
    print("\nCreating sample image...")
    img = np.ones((480, 640, 3), dtype=np.uint8) * 100
    cv2.putText(img, "Test Image", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
    
    _, img_bytes = cv2.imencode('.jpg', img)
    img_bytes = img_bytes.tobytes()
    
    print(f"✓ Sample image created ({len(img_bytes)} bytes)")
    
    # Ask VLM
    vlm_service = get_vlm_service()
    question = "Bu resimde ne var?"  # "What is in this image?"
    
    try:
        print(f"\nAsking VLM: '{question}'")
        answer, metadata = await vlm_service.ask_context(
            image_bytes=img_bytes,
            question=question
        )
        
        print("\n✅ VLM Response received:")
        print(f"   Answer: {answer}")
        print(f"   Processing time: {metadata['processing_time_ms']:.2f}ms")
        print(f"   Tokens generated: {metadata.get('tokens_generated', 'N/A')}")
        return True
        
    except Exception as e:
        print(f"❌ VLM Request failed: {e}")
        return False


async def test_vlm_with_detections():
    """Test 3: Ask VLM with object detection context."""
    print("\n" + "="*70)
    print("TEST 3: VLM with Detection Context")
    print("="*70)
    
    # Create test image
    img = np.ones((480, 640, 3), dtype=np.uint8) * 150
    cv2.circle(img, (320, 240), 50, (0, 255, 0), -1)
    cv2.putText(img, "Person detected", (200, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    _, img_bytes = cv2.imencode('.jpg', img)
    img_bytes = img_bytes.tobytes()
    
    # Mock detections
    detections = [
        {
            'name': 'person',
            'name_tr': 'insan',
            'confidence': 0.95,
            'distance': 2.5,
            'region': 'center'
        },
        {
            'name': 'car',
            'name_tr': 'araba',
            'confidence': 0.87,
            'distance': 10.0,
            'region': 'right'
        }
    ]
    
    vlm_service = get_vlm_service()
    question = "Hangi taraftan tehlike var?"  # "Where is the danger coming from?"
    
    try:
        print(f"\nDetected objects: {len(detections)}")
        for det in detections:
            print(f"  - {det['name_tr']} at {det['distance']}m ({det['region']})")
        
        print(f"\nAsking VLM: '{question}'")
        answer, metadata = await vlm_service.ask_context(
            image_bytes=img_bytes,
            question=question,
            detections=detections
        )
        
        print("\n✅ VLM Response received:")
        print(f"   Answer: {answer}")
        print(f"   Processing time: {metadata['processing_time_ms']:.2f}ms")
        return True
        
    except Exception as e:
        print(f"❌ VLM Request failed: {e}")
        return False


async def test_preset_questions():
    """Test 4: Get preset questions."""
    print("\n" + "="*70)
    print("TEST 4: Preset Questions")
    print("="*70)
    
    vlm_service = get_vlm_service()
    questions = vlm_service.get_preset_questions()
    
    print(f"\n✓ Retrieved {len(questions)} preset questions:")
    for key, question in questions.items():
        print(f"  - {key}: {question}")
    
    return True


async def main():
    """Run all tests."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "VLM (Vision Language Model) Integration Tests".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    results = []
    
    # Test 1: Connection
    try:
        result = await test_vlm_connection()
        results.append(("VLM Connection", result))
        if not result:
            print("\n⚠️  Cannot proceed without server. Please start Ollama:")
            print("    $ ollama serve")
            return
    except Exception as e:
        print(f"❌ Test failed: {e}")
        results.append(("VLM Connection", False))
        return
    
    # Test 2: Simple image analysis
    try:
        result = await test_vlm_with_sample_image()
        results.append(("Image Analysis", result))
    except Exception as e:
        print(f"❌ Test failed: {e}")
        results.append(("Image Analysis", False))
    
    # Test 3: With detections
    try:
        result = await test_vlm_with_detections()
        results.append(("With Detections", result))
    except Exception as e:
        print(f"❌ Test failed: {e}")
        results.append(("With Detections", False))
    
    # Test 4: Preset questions
    try:
        result = await test_preset_questions()
        results.append(("Preset Questions", result))
    except Exception as e:
        print(f"❌ Test failed: {e}")
        results.append(("Preset Questions", False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✨ All tests passed! VLM is working correctly.")
        print("\nYou can now use the /api/ask_context endpoint:")
        print("  curl -X POST http://localhost:8000/api/ask_context \\")
        print("    -F 'image=@scene.jpg' \\")
        print("    -F 'question=Önümde ne var?'")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above.")


if __name__ == "__main__":
    asyncio.run(main())
