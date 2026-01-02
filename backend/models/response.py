"""
Pydantic Response Models
=========================

Data models for API responses with validation.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class DistanceStats(BaseModel):
    """Distance statistics from depth map."""
    min: float = Field(..., description="Minimum distance in meters")
    max: float = Field(..., description="Maximum distance in meters")
    avg: float = Field(..., description="Average distance in meters")


class Warning(BaseModel):
    """Individual warning message."""
    message: str = Field(..., description="Warning message")
    level: str = Field(..., description="Alert level (DANGER, NEAR, MEDIUM)")
    distance: float = Field(..., description="Distance that triggered warning")
    area_percentage: float = Field(..., description="Percentage of image area affected")


class RegionalAlert(BaseModel):
    """Alert for a specific region (left/center/right)."""
    alert_level: str = Field(..., description="Alert level for this region")
    min_distance: float = Field(..., description="Minimum distance in this region")
    has_obstacle: bool = Field(..., description="Whether obstacle detected in this region")
    message: str = Field(..., description="Distance message")


class RegionalAlerts(BaseModel):
    """Regional analysis for left, center, right zones."""
    left: RegionalAlert = Field(..., description="Left region analysis")
    center: RegionalAlert = Field(..., description="Center region analysis")
    right: RegionalAlert = Field(..., description="Right region analysis")


class DetectedObject(BaseModel):
    """Detected object information."""
    name: str = Field(..., description="Object name (English)")
    name_tr: str = Field(..., description="Object name (Turkish)")
    confidence: float = Field(..., description="Detection confidence (0-1)")
    bbox: List[float] = Field(..., description="Bounding box [x1, y1, x2, y2]")
    center: List[float] = Field(..., description="Center point [x, y]")
    priority: int = Field(..., description="Collision priority (0-10)")
    region: str = Field(..., description="Screen region (left/center/right)")
    # New tracking fields
    is_approaching: Optional[bool] = Field(None, description="Object moving towards camera")
    track_id: Optional[str] = Field(None, description="Unique tracking ID")
    stability: Optional[float] = Field(None, description="Detection stability (0-1)")


class AnalysisData(BaseModel):
    """Analysis results data."""
    alert_level: str = Field(..., description="Overall alert level")
    distance_stats: DistanceStats = Field(..., description="Distance statistics")
    warnings: List[Warning] = Field(default=[], description="List of warnings")
    area_percentages: Optional[Dict[str, float]] = Field(
        None,
        description="Percentage of image area per alert level"
    )
    regional_alerts: Optional[RegionalAlerts] = Field(
        None,
        description="Regional zone analysis (left/center/right)"
    )
    detected_objects: Optional[List[DetectedObject]] = Field(
        None,
        description="Detected objects in the scene"
    )
    depth_image_base64: Optional[str] = Field(
        None,
        description="Base64 encoded depth visualization (optional)"
    )
    # New metadata fields
    metadata: Optional[Dict] = Field(
        None,
        description="Additional analysis metadata (tracking, ground analysis)"
    )


class AnalyzeResponse(BaseModel):
    """Response model for /api/analyze endpoint."""
    success: bool = Field(..., description="Request success status")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    data: Optional[AnalysisData] = Field(None, description="Analysis results")
    error: Optional[Dict[str, str]] = Field(None, description="Error information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "timestamp": "2025-11-24T12:34:56.789Z",
                "processing_time_ms": 234.5,
                "data": {
                    "alert_level": "DANGER",
                    "distance_stats": {
                        "min": 0.45,
                        "max": 4.8,
                        "avg": 2.1
                    },
                    "warnings": [
                        {
                            "message": "DANGER! Object detected at 0.45m",
                            "level": "DANGER",
                            "distance": 0.45,
                            "area_percentage": 12.3
                        }
                    ],
                    "area_percentages": {
                        "danger": 12.3,
                        "near": 5.2,
                        "medium": 8.1
                    },
                    "depth_image_base64": "data:image/jpeg;base64,/9j/4AAQ..."
                }
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = Field(False, description="Always false for errors")
    error: Dict[str, str] = Field(..., description="Error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "INVALID_IMAGE",
                    "message": "Image could not be decoded or format not supported"
                }
            }
        }
