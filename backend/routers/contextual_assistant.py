"""
Contextual Assistant Router
============================

Handles /api/ask_context endpoint for VLM-based contextual assistance.
"""

import time
import logging
import base64
from datetime import datetime, timezone
from typing import Optional
from collections import deque

from fastapi import APIRouter, Request, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from services.vlm_service import get_vlm_service
from services.object_detection_service import get_object_detection_service
from core.config import get_settings
from core.state import app_state

logger = logging.getLogger(__name__)

# Router
router = APIRouter()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# History buffer for monitoring (last 50 requests)
request_history = deque(maxlen=50)

@router.post("/ask_context")
@limiter.limit("10/minute")  # Limit to prevent abuse
async def ask_context(
    request: Request,
    image: UploadFile = File(..., description="Image to analyze"),
    question: str = Form(..., description="Question in Turkish"),
    use_cached_detections: bool = Form(
        default=True,
        description="Use cached YOLO detections if available"
    )
) -> JSONResponse:
    """
    Ask VLM a contextual question about the scene.
    
    Args:
        request: FastAPI request object (for rate limiting)
        image: Uploaded image file
        question: User's question in Turkish
        use_cached_detections: Whether to use cached YOLO detections
        
    Returns:
        JSON response with answer and metadata
    """
    start_time = time.time()
    
    try:
        # Read image
        image_bytes = await image.read()
        logger.info(f"Received contextual question: '{question}' (image: {len(image_bytes)} bytes)")
        
        # Get VLM service with config
        settings = get_settings()
        vlm_config = settings.vlm if hasattr(settings, 'vlm') else {}
        vlm_server_url = vlm_config.get('server_url', 'http://localhost:8080')
        vlm_timeout = vlm_config.get('timeout', 60)
        vlm_service = get_vlm_service(
            server_url=vlm_server_url,
            timeout=vlm_timeout
        )
        
        # Check if server is ready
        is_ready = await vlm_service.is_server_ready()
        if not is_ready:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "VLM_SERVER_UNAVAILABLE",
                    "message": "VLM server is not available. Please ensure llama.cpp server is running."
                }
            )
        
        # Get YOLO detections (cached or new)
        detections = None
        if use_cached_detections:
            # Try to get from state
            cached_data = app_state.last_analysis
            if cached_data and cached_data.get('detections'):
                detections = cached_data['detections']
                logger.info(f"Using {len(detections)} cached detections")
        
        # If no cached detections, run object detection
        if detections is None:
            logger.info("No cached detections, running object detection...")
            try:
                detection_service = get_object_detection_service()
                # Decode image bytes to numpy array first
                from services.image_service import get_image_service
                image_service = get_image_service()
                image_array = image_service.decode_image(image_bytes)
                
                if image_array is not None:
                    detection_result = detection_service.detect(image_array)
                    # detection_result is already a list of dicts
                    detections = detection_result if isinstance(detection_result, list) else []
                    logger.info(f"Detected {len(detections)} objects")
                else:
                    logger.warning("Failed to decode image for detection")
                    detections = []
            except Exception as e:
                logger.warning(f"Object detection failed: {e}")
                detections = []
        
        # Convert detection objects to dicts if needed
        detection_dicts = []
        if detections:
            for det in detections:
                if hasattr(det, 'to_dict'):
                    detection_dicts.append(det.to_dict())
                elif isinstance(det, dict):
                    detection_dicts.append(det)
                else:
                    # Try to extract basic info
                    detection_dicts.append({
                        'class_name': getattr(det, 'class_name', 'unknown'),
                        'confidence': getattr(det, 'confidence', 0),
                        'distance': getattr(det, 'distance', None)
                    })
        
        # Call VLM service - NO FALLBACK
        answer, metadata = await vlm_service.ask_context(
            image_bytes=image_bytes,
            question=question,
            detections=detection_dicts
        )
        # Mark that this is from VLM
        metadata['source'] = 'vlm'
        
        # Calculate total processing time
        total_time = (time.time() - start_time) * 1000
        
        # Build response
        response_data = {
            "success": True,
            "answer": answer,
            "processing_time_ms": total_time,
            "context_used": {
                "detections_count": len(detection_dicts),
                "detections": detection_dicts,
                "cached": use_cached_detections and detections is not None
            },
            "metadata": metadata,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"✓ Contextual question answered in {total_time:.2f}ms")
        
        # Add to history for monitoring
        history_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": question,
            "answer": answer,
            "processing_time_ms": total_time,
            "metadata": metadata,
            "image_base64": base64.b64encode(image_bytes).decode('utf-8')  # Full image for monitor
        }
        request_history.append(history_entry)
        
        return JSONResponse(
            status_code=200,
            content=response_data
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error in ask_context: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": f"An unexpected error occurred: {str(e)}"
            }
        )


@router.get("/preset_questions")
@limiter.limit("30/minute")
async def get_preset_questions(request: Request) -> JSONResponse:
    """
    Get list of preset questions.
    
    Returns:
        JSON response with preset questions
    """
    try:
        vlm_service = get_vlm_service()
        questions = vlm_service.get_preset_questions()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "preset_questions": questions
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting preset questions: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Failed to retrieve preset questions."
            }
        )

@router.get("/ask_context_history")
async def get_history() -> JSONResponse:
    """
    Get recent request history for monitoring.
    
    Returns:
        JSON response with last 50 requests and their answers
    """
    try:
        history_list = list(request_history)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "count": len(history_list),
                "history": history_list
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Failed to retrieve history."
            }
        )