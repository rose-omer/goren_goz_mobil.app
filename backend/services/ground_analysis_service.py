"""
Ground Analysis Service
========================

Analyzes ground/floor surface for obstacles, holes, stairs, and curbs.
Uses depth map segmentation to detect dangerous floor conditions.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy import ndimage
import cv2

logger = logging.getLogger(__name__)


class GroundAnalysisService:
    """
    Service for analyzing ground surface conditions.
    
    Features:
    - Stair/step detection
    - Curb detection
    - Hole/pit detection
    - Surface smoothness analysis
    - Slope detection
    """
    
    def __init__(
        self,
        ground_height_ratio: float = 0.7,  # Bottom 70% of image is ground
        depth_change_threshold: float = 0.35,  # 35% depth change indicates step (daha az hassas)
        hole_depth_threshold: float = 0.5,  # 50% deeper = potential hole (daha az hassas)
        min_feature_size: int = 300  # Minimum pixels for a feature (daha büyük)
    ):
        """Initialize ground analysis service."""
        self.ground_height_ratio = ground_height_ratio
        self.depth_change_threshold = depth_change_threshold
        self.hole_depth_threshold = hole_depth_threshold
        self.min_feature_size = min_feature_size
        
        logger.info(
            f"GroundAnalysisService initialized: "
            f"ground_ratio={ground_height_ratio}, "
            f"depth_threshold={depth_change_threshold}"
        )
    
    def _extract_ground_region(self, depth_map: np.ndarray) -> Tuple[np.ndarray, int]:
        """Extract ground/floor region from depth map."""
        height, width = depth_map.shape
        ground_start_row = int(height * (1.0 - self.ground_height_ratio))
        ground_region = depth_map[ground_start_row:, :]
        return ground_region, ground_start_row
    
    def _detect_horizontal_edges(self, depth_map: np.ndarray) -> np.ndarray:
        """Detect horizontal edges in depth map (stairs, curbs)."""
        # Sobel edge detection in vertical direction
        sobel_vertical = cv2.Sobel(depth_map, cv2.CV_64F, 0, 1, ksize=3)
        edges = np.abs(sobel_vertical)
        
        # Normalize
        if edges.max() > 0:
            edges = edges / edges.max()
        
        return edges
    
    def _find_depth_discontinuities(
        self,
        ground_region: np.ndarray,
        start_row: int
    ) -> List[Dict]:
        """Find significant depth changes (steps, holes, curbs)."""
        features = []
        height, width = ground_region.shape
        
        # Scan horizontally for depth changes
        for row in range(1, height):
            row_diff = np.abs(ground_region[row] - ground_region[row - 1])
            
            # Find positions with significant depth change
            threshold = self.depth_change_threshold * np.std(ground_region)
            discontinuities = np.where(row_diff > threshold)[0]
            
            if len(discontinuities) > self.min_feature_size / width:
                # Calculate feature properties
                avg_depth_before = np.mean(ground_region[row - 1, discontinuities])
                avg_depth_after = np.mean(ground_region[row, discontinuities])
                depth_change = avg_depth_after - avg_depth_before
                
                # Classify feature
                feature_type = 'unknown'
                severity = 'medium'
                
                if depth_change > 0:
                    # Depth increases = moving away = step down or hole
                    if abs(depth_change) > self.hole_depth_threshold:
                        feature_type = 'hole'
                        severity = 'critical'
                    else:
                        feature_type = 'step_down'
                        severity = 'high'
                else:
                    # Depth decreases = closer = step up or curb
                    feature_type = 'step_up'
                    severity = 'high'
                
                features.append({
                    'type': feature_type,
                    'severity': severity,
                    'row': start_row + row,
                    'columns': discontinuities.tolist(),
                    'depth_change': float(depth_change),
                    'width_percentage': len(discontinuities) / width
                })
        
        return features
    
    def _detect_stairs(self, ground_region: np.ndarray, features: List[Dict]) -> Optional[Dict]:
        """Detect stairs pattern from multiple step features."""
        # Look for multiple parallel step features
        step_features = [f for f in features if f['type'] in ['step_up', 'step_down']]
        
        if len(step_features) < 2:
            return None
        
        # Check if steps are evenly spaced (typical stair pattern)
        rows = [f['row'] for f in step_features]
        rows.sort()
        
        # Calculate spacing between steps
        spacings = [rows[i+1] - rows[i] for i in range(len(rows)-1)]
        
        # Stairs have relatively consistent spacing
        if len(spacings) > 1:
            avg_spacing = np.mean(spacings)
            spacing_variance = np.var(spacings)
            
            # Low variance indicates stairs
            if spacing_variance < avg_spacing * 0.2:  # 20% variance threshold (daha strict)
                confidence = 1.0 - (spacing_variance / (avg_spacing + 0.001))
                # En az 3 basamak ve yüksek güven gerekli
                if len(step_features) >= 3 and confidence > 0.8:
                    return {
                        'detected': True,
                        'num_steps': len(step_features),
                        'avg_spacing': float(avg_spacing),
                        'confidence': confidence
                    }
        
        return None
    
    def _calculate_slope(self, ground_region: np.ndarray) -> float:
        """Calculate average ground slope."""
        height, width = ground_region.shape
        
        # Compare top row with bottom row
        top_avg = np.mean(ground_region[0, :])
        bottom_avg = np.mean(ground_region[-1, :])
        
        # Slope = change in depth per row
        slope = (bottom_avg - top_avg) / height
        
        return float(slope)
    
    def _assess_surface_smoothness(self, ground_region: np.ndarray) -> Dict:
        """Assess how smooth/rough the ground surface is."""
        # Calculate local variance
        variance = np.var(ground_region)
        std_dev = np.std(ground_region)
        
        # Classify smoothness
        if std_dev < 0.05:
            smoothness = 'very_smooth'
            warning_level = 'none'
        elif std_dev < 0.1:
            smoothness = 'smooth'
            warning_level = 'low'
        elif std_dev < 0.2:
            smoothness = 'moderate'
            warning_level = 'medium'
        else:
            smoothness = 'rough'
            warning_level = 'high'
        
        return {
            'smoothness': smoothness,
            'variance': float(variance),
            'std_dev': float(std_dev),
            'warning_level': warning_level
        }
    
    def analyze(self, depth_map: np.ndarray) -> Dict:
        """
        Analyze ground surface for obstacles and hazards.
        
        Args:
            depth_map: Normalized depth map (0-1, closer = lower values)
        
        Returns:
            Dictionary with ground analysis results:
            - features: List of detected ground features (steps, holes, curbs)
            - stairs_detected: Boolean indicating if stairs pattern found
            - slope: Ground slope value
            - smoothness: Surface smoothness assessment
            - warnings: List of ground-related warnings
        """
        try:
            # Extract ground region
            ground_region, start_row = self._extract_ground_region(depth_map)
            
            # Find depth discontinuities
            features = self._find_depth_discontinuities(ground_region, start_row)
            
            # Detect stairs
            stairs_info = self._detect_stairs(ground_region, features)
            
            # Calculate slope
            slope = self._calculate_slope(ground_region)
            
            # Assess surface smoothness
            smoothness_info = self._assess_surface_smoothness(ground_region)
            
            # Generate warnings
            warnings = []
            
            # Stairs warning (daha yüksek güven eşiği)
            if stairs_info and stairs_info['confidence'] > 0.85:
                warnings.append({
                    'type': 'stairs',
                    'severity': 'critical',
                    'message_tr': f"MERDİVEN TESPİT EDİLDİ! {stairs_info['num_steps']} basamak görüldü. Çok dikkatli olun!",
                    'message_en': f"STAIRS DETECTED! {stairs_info['num_steps']} steps found. Be very careful!"
                })
            
            # Step/curb warnings
            critical_features = [f for f in features if f['severity'] == 'critical']
            if critical_features:
                warnings.append({
                    'type': 'hole_or_pit',
                    'severity': 'critical',
                    'message_tr': "DİKKAT! Önünüzde çukur veya basamak var! Durun!",
                    'message_en': "WARNING! Hole or step ahead! Stop!"
                })
            
            high_features = [f for f in features if f['severity'] == 'high']
            if high_features and not critical_features:
                feature_type = high_features[0]['type']
                if feature_type == 'step_up':
                    warnings.append({
                        'type': 'step_up',
                        'severity': 'high',
                        'message_tr': "Önünüzde basamak veya kaldırım var. Dikkatli adım atın.",
                        'message_en': "Step or curb ahead. Step carefully."
                    })
                elif feature_type == 'step_down':
                    warnings.append({
                        'type': 'step_down',
                        'severity': 'high',
                        'message_tr': "Dikkat! Aşağı basamak var. Yavaş ilerleyin.",
                        'message_en': "Caution! Step down ahead. Proceed slowly."
                    })
            
            # Slope warning
            if abs(slope) > 0.1:
                direction = "yukarı" if slope > 0 else "aşağı"
                direction_en = "uphill" if slope > 0 else "downhill"
                warnings.append({
                    'type': 'slope',
                    'severity': 'medium',
                    'message_tr': f"Yol {direction} doğru eğimli. Dikkatli ilerleyin.",
                    'message_en': f"Ground is sloped {direction_en}. Walk carefully."
                })
            
            # Rough surface warning
            if smoothness_info['warning_level'] == 'high':
                warnings.append({
                    'type': 'rough_surface',
                    'severity': 'medium',
                    'message_tr': "Zemin düzgün değil. Yavaş ve dikkatli yürüyün.",
                    'message_en': "Uneven surface. Walk slowly and carefully."
                })
            
            result = {
                'features': features,
                'stairs_detected': stairs_info is not None,
                'stairs_info': stairs_info,
                'slope': slope,
                'smoothness': smoothness_info,
                'warnings': warnings,
                'ground_hazard_count': len(features)
            }
            
            logger.debug(
                f"Ground analysis: {len(features)} features, "
                f"stairs={'yes' if stairs_info else 'no'}, "
                f"warnings={len(warnings)}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Ground analysis failed: {e}", exc_info=True)
            return {
                'features': [],
                'stairs_detected': False,
                'stairs_info': None,
                'slope': 0.0,
                'smoothness': {'smoothness': 'unknown', 'warning_level': 'none'},
                'warnings': [],
                'ground_hazard_count': 0
            }


# Singleton instance
_ground_service: Optional[GroundAnalysisService] = None


def get_ground_analysis_service() -> GroundAnalysisService:
    """Get or create the ground analysis service singleton."""
    global _ground_service
    if _ground_service is None:
        _ground_service = GroundAnalysisService()
    return _ground_service
