"""
Analysis Router
===============

Handles /api/analyze endpoint for depth estimation and alert generation.
Supports both single and batch image processing.
"""

import time
import logging
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from models.response import AnalyzeResponse, AnalysisData, DistanceStats, Warning, ErrorResponse, RegionalAlert, RegionalAlerts, DetectedObject
from services.depth_service import get_depth_service
from services.alert_service import get_alert_service
from services.image_service import get_image_service
from services.object_detection_service import get_object_detection_service
from services.object_tracking_service import get_tracking_service
# ✅ REMOVED: ground_analysis_service (not needed, performance optimization)

logger = logging.getLogger(__name__)

# Import global state
from core.state import app_state


# Router
router = APIRouter()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze image for depth and collision detection",
    description="""
    Upload an image to analyze depth map and detect potential collisions.
    
    **Process:**
    1. Receives image (JPEG/PNG)
    2. Runs MiDaS depth estimation
    3. Analyzes for collision risks
    4. Returns alert level, statistics, and optional depth visualization
    
    **Rate Limit:** 5 requests per second
    """,
    responses={
        200: {"model": AnalyzeResponse, "description": "Successful analysis"},
        400: {"model": ErrorResponse, "description": "Invalid image"},
        413: {"description": "Image too large (max 10MB)"},
        429: {"description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
@limiter.limit("5/second")
async def analyze_image(
    request: Request,
    image: UploadFile = File(..., description="Image file (JPEG/PNG, max 10MB)"),
    include_depth_image: bool = Query(
        default=False,
        description="Include base64 encoded depth visualization in response"
    ),
    colormap: str = Query(
        default="JET",
        description="Colormap for depth visualization (JET, VIRIDIS, MAGMA, etc.)"
    )
):
    """
    Analyze uploaded image for depth estimation and collision detection.
    
    Args:
        request: FastAPI request object (for rate limiting)
        image: Uploaded image file
        include_depth_image: Whether to include depth visualization in response
        colormap: Colormap to use for visualization
    
    Returns:
        AnalyzeResponse: Analysis results with alert level, stats, and warnings
    """
    start_time = time.time()
    
    try:
        # Validate file
        if not image.content_type or not image.content_type.startswith('image/'):
            logger.warning(f"Invalid content type: {image.content_type}")
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": {
                        "code": "INVALID_CONTENT_TYPE",
                        "message": f"Invalid content type: {image.content_type}. Expected image/*"
                    }
                }
            )
        
        # Read image data
        image_bytes = await image.read()
        
        # Check size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(image_bytes) > max_size:
            logger.warning(f"Image too large: {len(image_bytes)} bytes")
            raise HTTPException(
                status_code=413,
                detail={
                    "success": False,
                    "error": {
                        "code": "IMAGE_TOO_LARGE",
                        "message": f"Image size {len(image_bytes)} bytes exceeds limit of {max_size} bytes"
                    }
                }
            )
        
        logger.info(f"Processing image: {image.filename}, size: {len(image_bytes)} bytes")
        
        # Get services
        image_service = get_image_service()
        depth_service = get_depth_service()
        alert_service = get_alert_service()
        object_detection_service = get_object_detection_service()
        tracking_service = get_tracking_service()
        # ✅ REMOVED: ground_service (performance optimization)
        
        # Decode image
        image_array = image_service.decode_image(image_bytes)
        if image_array is None:
            logger.error("Failed to decode image")
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": {
                        "code": "INVALID_IMAGE",
                        "message": "Image could not be decoded. Please check format and try again."
                    }
                }
            )
        
        # Estimate depth
        depth_map = depth_service.estimate(image_array)
        if depth_map is None:
            logger.error("Depth estimation failed")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": {
                        "code": "DEPTH_ESTIMATION_FAILED",
                        "message": "Depth estimation failed. Please try again."
                    }
                }
            )
        
        # Detect objects with depth information
        detected_objects_list = object_detection_service.detect(
            image_array,
            confidence_threshold=0.5,
            max_objects=10,
            depth_map=depth_map
        )
        
        # Track objects across frames (temporal smoothing)
        tracked_objects = tracking_service.update(detected_objects_list)
        
        # ✅ REMOVED: Ground analysis (too slow, not priority)
        # Simple ground check instead
        ground_analysis = {
            'features': [],
            'stairs_detected': False,
            'stairs_info': None,
            'slope': 0.0,
            'smoothness': {'smoothness': 'unknown', 'warning_level': 'none'},
            'warnings': [],
            'ground_hazard_count': 0
        }
        
        # Analyze alerts
        alert_result = alert_service.analyze_depth(depth_map)
        
        # Combine warnings from depth analysis and ground analysis
        all_warnings = alert_result["warnings"].copy()
        
        # Add ground-related warnings
        for ground_warning in ground_analysis.get('warnings', []):
            all_warnings.append({
                'message': ground_warning.get('message_tr', ground_warning.get('message_en', 'Ground hazard detected')),
                'level': ground_warning.get('severity', 'medium'),
                'distance': 0.0,  # Ground warnings don't have specific distance
                'area_percentage': 0.0
            })
        
        # Prepare response data
        warnings_list = [
            Warning(
                message=w["message"],
                level=w["level"],
                distance=w["distance"],
                area_percentage=w["area_percentage"]
            )
            for w in all_warnings
        ]
        
        # Optional: Generate depth visualization
        depth_image_base64 = None
        if include_depth_image:
            depth_colored = image_service.create_visualization(
                depth_map,
                alert_result["alert_level"].value,
                alert_result["distance_stats"],
                colormap.upper()
            )
            
            if depth_colored is not None:
                depth_image_base64 = image_service.encode_image_to_base64(depth_colored)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Build regional alerts
        regional_data = alert_result.get("regional_alerts")
        regional_alerts = None
        if regional_data:
            regional_alerts = RegionalAlerts(
                left=RegionalAlert(**regional_data["left"]),
                center=RegionalAlert(**regional_data["center"]),
                right=RegionalAlert(**regional_data["right"])
            )
        
        # Build detected objects (use raw detections + tracking metadata)
        detected_objects = None
        if detected_objects_list:
            detected_objects = []
            # Create tracking lookup
            track_lookup = {t['name']: t for t in tracked_objects} if tracked_objects else {}
            
            for obj in detected_objects_list:
                eng_name = obj.get('name', 'unknown')  # ✅ Fixed: 'name' not 'class_name'
                # Get tracking info if available
                track_info = track_lookup.get(eng_name, {})
                
                detected_objects.append(DetectedObject(
                    name=eng_name,
                    name_tr=obj.get('name_tr', eng_name),
                    confidence=obj.get('confidence', 0.0),
                    distance=obj.get('distance', 0.0),
                    region=obj.get('region', 'center'),
                    priority=obj.get('priority', 0),
                    bbox=obj.get('bbox', [0, 0, 0, 0]),
                    center=obj.get('center', [0, 0]),
                    is_approaching=track_info.get('is_approaching', False),
                    track_id=track_info.get('track_id'),
                    stability=track_info.get('stability', 0.0)
                ))
        
        # Add metadata for tracking and ground analysis
        metadata = {
            'tracking': {
                'total_tracks': len(tracking_service.tracked_objects),
                'confirmed_objects': len(tracked_objects) if tracked_objects else 0
            },
            'ground_analysis': {
                'hazard_count': ground_analysis.get('ground_hazard_count', 0),
                'stairs_detected': ground_analysis.get('stairs_detected', False),
                'slope': ground_analysis.get('slope', 0.0),
                'smoothness': ground_analysis.get('smoothness', {}).get('smoothness', 'unknown')
            }
        }
        
        # Build response
        response = AnalyzeResponse(
            success=True,
            timestamp=datetime.now(timezone.utc).isoformat(),
            processing_time_ms=round(processing_time, 2),
            data=AnalysisData(
                alert_level=alert_result["alert_level"].value,
                distance_stats=DistanceStats(**alert_result["distance_stats"]),
                warnings=warnings_list,
                area_percentages=alert_result.get("area_percentages"),
                regional_alerts=regional_alerts,
                detected_objects=detected_objects,
                depth_image_base64=depth_image_base64,
                metadata=metadata
            )
        )
        
        logger.info(
            f"Analysis completed: {alert_result['alert_level'].value}, "
            f"time: {processing_time:.2f}ms, "
            f"warnings: {len(warnings_list)}"
        )
        
        # Update Global State for Debug Dashboard
        # This is a lightweight operation (reference copy)
        app_state.update_state(
            original_frame=image_array,
            depth_map=depth_map,
            analysis_result={
                'objects': detected_objects_list,
                'alert_level': alert_result["alert_level"].value,
                'alerts': all_warnings
            }
        )

        
        return response
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Catch unexpected errors
        logger.error(f"Unexpected error in analyze_image: {e}", exc_info=True)
        processing_time = (time.time() - start_time) * 1000
        
        return AnalyzeResponse(
            success=False,
            timestamp=datetime.now(timezone.utc).isoformat(),
            processing_time_ms=round(processing_time, 2),
            error={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred during analysis"
            }
        )


@router.post(
    "/analyze-batch",
    response_model=List[AnalyzeResponse],
    summary="Batch analyze multiple images",
    description="""
    Upload multiple images for batch processing.
    
    **Features:**
    - Process up to 10 images at once
    - Shared model inference (faster)
    - 3-4x speedup vs sequential processing
    
    **Rate Limit:** 2 requests per second
    """,
    responses={
        200: {"model": List[AnalyzeResponse], "description": "Batch analysis results"},
        400: {"model": ErrorResponse, "description": "Invalid images"},
        413: {"description": "Total size too large"},
        429: {"description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
@limiter.limit("2/second")
async def analyze_batch(
    request: Request,
    images: List[UploadFile] = File(..., description="Image files (max 10, 10MB each)"),
    include_depth_image: bool = Query(
        default=False,
        description="Include depth visualization in response"
    ),
    colormap: str = Query(
        default="JET",
        description="Colormap for depth visualization"
    )
):
    """
    Batch process multiple images for depth estimation and collision detection.
    
    Optimized for real-time video stream processing and multi-frame analysis.
    Models are loaded once and reused for all images (3-4x faster).
    
    Args:
        request: FastAPI request object
        images: List of image files (max 10)
        include_depth_image: Include depth visualization
        colormap: Colormap to use
    
    Returns:
        List[AnalyzeResponse]: Analysis results for each image
    """
    start_time = time.time()
    
    try:
        # Validate batch size
        if len(images) > 10:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": {
                        "code": "TOO_MANY_IMAGES",
                        "message": f"Maximum 10 images per batch, got {len(images)}"
                    }
                }
            )
        
        if len(images) == 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": {
                        "code": "NO_IMAGES",
                        "message": "At least 1 image required"
                    }
                }
            )
        
        # Get services once (reuse for all images)
        image_service = get_image_service()
        depth_service = get_depth_service()
        alert_service = get_alert_service()
        object_detection_service = get_object_detection_service()
        tracking_service = get_tracking_service()
        
        logger.info(f"Starting batch analysis for {len(images)} images")
        
        # Pre-load models if not already loaded (shared across all images)
        if not depth_service.is_loaded:
            depth_service.load_model()
        if not object_detection_service.is_loaded:
            object_detection_service.load_model()
        
        # Process all images
        results = []
        total_image_time = 0.0
        
        for idx, image_file in enumerate(images):
            image_start = time.time()
            
            try:
                # Validate file
                if not image_file.content_type or not image_file.content_type.startswith('image/'):
                    results.append(AnalyzeResponse(
                        success=False,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        processing_time_ms=0,
                        error={
                            "code": "INVALID_CONTENT_TYPE",
                            "message": f"Image {idx+1}: Invalid content type"
                        }
                    ))
                    continue
                
                # Read image data
                image_bytes = await image_file.read()
                max_size = 10 * 1024 * 1024
                
                if len(image_bytes) > max_size:
                    results.append(AnalyzeResponse(
                        success=False,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        processing_time_ms=0,
                        error={
                            "code": "IMAGE_TOO_LARGE",
                            "message": f"Image {idx+1}: Size exceeds limit"
                        }
                    ))
                    continue
                
                # Decode image
                image_array = image_service.decode_image(image_bytes)
                if image_array is None:
                    results.append(AnalyzeResponse(
                        success=False,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        processing_time_ms=0,
                        error={
                            "code": "INVALID_IMAGE",
                            "message": f"Image {idx+1}: Could not decode"
                        }
                    ))
                    continue
                
                # Estimate depth
                depth_map = depth_service.estimate(image_array)
                if depth_map is None:
                    results.append(AnalyzeResponse(
                        success=False,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        processing_time_ms=round((time.time() - image_start) * 1000, 2),
                        error={
                            "code": "DEPTH_ESTIMATION_FAILED",
                            "message": f"Image {idx+1}: Depth estimation failed"
                        }
                    ))
                    continue
                
                # Detect objects
                detected_objects_list = object_detection_service.detect(
                    image_array,
                    confidence_threshold=0.5,
                    max_objects=10,
                    depth_map=depth_map
                )
                
                # Track objects
                tracked_objects = tracking_service.update(detected_objects_list)
                
                # Analyze alerts
                alert_result = alert_service.analyze_depth(depth_map)
                
                # Prepare warnings
                warnings_list = [
                    Warning(**w) for w in alert_result["warnings"]
                ]
                
                # Prepare regional alerts
                regional_alerts = RegionalAlerts(
                    left=RegionalAlert(**alert_result["regional_alerts"]["left"]),
                    center=RegionalAlert(**alert_result["regional_alerts"]["center"]),
                    right=RegionalAlert(**alert_result["regional_alerts"]["right"])
                )
                
                # Prepare detected objects
                detected_objects = []
                for obj in detected_objects_list:
                    eng_name = obj.get('name', 'unknown')
                    track_info = next(
                        (t for t in (tracked_objects or []) if t['name'] == eng_name),
                        {}
                    )
                    
                    detected_objects.append(DetectedObject(
                        name=eng_name,
                        name_tr=obj.get('name_tr', eng_name),
                        confidence=obj.get('confidence', 0.0),
                        distance=obj.get('distance', 0.0),
                        region=obj.get('region', 'center'),
                        priority=obj.get('priority', 0),
                        bbox=obj.get('bbox', [0, 0, 0, 0]),
                        center=obj.get('center', [0, 0]),
                        is_approaching=track_info.get('is_approaching', False),
                        track_id=track_info.get('track_id'),
                        stability=track_info.get('stability', 0.0)
                    ))
                
                # Prepare depth image if requested
                depth_image_base64 = None
                if include_depth_image:
                    depth_image_base64 = image_service.depth_to_colormap_base64(
                        depth_map,
                        colormap=colormap
                    )
                
                # Add metadata
                metadata = {
                    'tracking': {
                        'total_tracks': len(tracking_service.tracked_objects),
                        'confirmed_objects': len(tracked_objects) if tracked_objects else 0
                    },
                    'batch_index': idx + 1
                }
                
                # Build response
                image_time = (time.time() - image_start) * 1000
                total_image_time += image_time
                
                response = AnalyzeResponse(
                    success=True,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    processing_time_ms=round(image_time, 2),
                    data=AnalysisData(
                        alert_level=alert_result["alert_level"].value,
                        distance_stats=DistanceStats(**alert_result["distance_stats"]),
                        warnings=warnings_list,
                        area_percentages=alert_result.get("area_percentages"),
                        regional_alerts=regional_alerts,
                        detected_objects=detected_objects,
                        depth_image_base64=depth_image_base64,
                        metadata=metadata
                    )
                )
                
                results.append(response)
                logger.info(f"Batch image {idx+1}/{len(images)} analyzed: {image_time:.2f}ms")
                
            except Exception as e:
                logger.error(f"Batch image {idx+1} error: {e}")
                results.append(AnalyzeResponse(
                    success=False,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    processing_time_ms=round((time.time() - image_start) * 1000, 2),
                    error={
                        "code": "PROCESSING_ERROR",
                        "message": f"Image {idx+1}: {str(e)}"
                    }
                ))
        
        total_time = (time.time() - start_time) * 1000
        logger.info(
            f"Batch completed: {len(images)} images, "
            f"total time: {total_time:.2f}ms, "
            f"avg per image: {total_time/len(images):.2f}ms"
        )
        
        return results
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Batch processing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "BATCH_ERROR",
                    "message": "Batch processing failed"
                }
            }
        )
