"""
Unit tests for alert service.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.alert_service import AlertService, AlertLevel


class TestAlertService:
    """Test suite for AlertService."""
    
    def test_initialization(self):
        """Test AlertService initialization."""
        service = AlertService()
        assert service is not None
        assert service.min_distance == 0.5
        assert service.warning_distance == 1.2
        assert service.warning_area_threshold == 0.10
    
    def test_alert_level_enum(self):
        """Test AlertLevel enum values."""
        assert AlertLevel.SAFE.value == "SAFE"
        assert AlertLevel.FAR.value == "FAR"
        assert AlertLevel.MEDIUM.value == "MEDIUM"
        assert AlertLevel.NEAR.value == "NEAR"
        assert AlertLevel.DANGER.value == "DANGER"
    
    def test_analyze_depth_safe_scenario(self):
        """Test safe depth map analysis."""
        service = AlertService()
        
        # Create safe depth map (all values > warning distance)
        depth_map = np.full((480, 640), 3.0, dtype=np.float32)
        
        result = service.analyze_depth(depth_map)
        assert result['alert_level'] == AlertLevel.SAFE
        assert 'distance_stats' in result
        assert result['distance_stats']['min'] >= service.warning_distance
    
    def test_analyze_depth_danger_scenario(self):
        """Test dangerous depth map analysis."""
        service = AlertService()
        
        # Create dangerous depth map with >10% area < min_distance
        depth_map = np.full((480, 640), 3.0, dtype=np.float32)
        depth_map[:48, :] = 0.3  # First 48 rows = ~10% area, very close
        
        result = service.analyze_depth(depth_map)
        assert result['alert_level'] == AlertLevel.DANGER
        assert any(w['level'] == 'DANGER' for w in result['warnings'])
    
    def test_analyze_depth_near_scenario(self):
        """Test near obstacle scenario."""
        service = AlertService()
        
        # Create near obstacle depth map (0.5-1.2m range)
        depth_map = np.full((480, 640), 3.0, dtype=np.float32)
        depth_map[:48, :] = 0.8  # ~10% area, in near range
        
        result = service.analyze_depth(depth_map)
        assert result['alert_level'] in [AlertLevel.NEAR, AlertLevel.DANGER]
    
    def test_distance_statistics(self, sample_depth_map):
        """Test distance statistics calculation."""
        service = AlertService()
        result = service.analyze_depth(sample_depth_map)
        
        stats = result['distance_stats']
        assert 'min' in stats
        assert 'max' in stats
        assert 'avg' in stats
        assert stats['min'] <= stats['avg'] <= stats['max']
        assert stats['min'] >= 0.0
        assert stats['max'] <= 10.0  # Reasonable max
    
    def test_regional_analysis(self, sample_depth_map):
        """Test regional (left/center/right) analysis."""
        service = AlertService()
        result = service.analyze_depth(sample_depth_map)
        
        assert 'regional_alerts' in result
        regions = result['regional_alerts']
        
        for region in ['left', 'center', 'right']:
            assert region in regions
            assert 'alert_level' in regions[region]
            assert 'min_distance' in regions[region]
            assert 'has_obstacle' in regions[region]
            assert 'message' in regions[region]
    
    def test_area_percentages(self, sample_depth_map):
        """Test area percentage calculation."""
        service = AlertService()
        result = service.analyze_depth(sample_depth_map)
        
        areas = result.get('area_percentages', {})
        if areas:
            total = sum(areas.values())
            assert 0.99 <= total <= 1.01  # Should sum to ~1.0
    
    def test_empty_depth_map(self):
        """Test handling of empty/invalid depth map."""
        service = AlertService()
        result = service.analyze_depth(None)
        assert result['alert_level'] == AlertLevel.SAFE
    
    def test_invalid_values_handling(self):
        """Test handling of NaN and Inf values."""
        service = AlertService()
        
        # Depth map with invalid values
        depth_map = np.full((480, 640), 2.0, dtype=np.float32)
        depth_map[:100, :] = np.nan
        depth_map[100:150, :] = np.inf
        
        result = service.analyze_depth(depth_map)
        # Should still process and return valid result
        assert 'alert_level' in result
        assert 'distance_stats' in result
    
    def test_warning_area_threshold(self):
        """Test warning area threshold sensitivity."""
        service = AlertService()
        
        # Test boundary: exactly at threshold
        depth_map = np.full((480, 640), 3.0, dtype=np.float32)
        # 10% area at danger level
        danger_pixels = int(480 * 640 * 0.10)
        depth_map.flat[:danger_pixels] = 0.3
        
        result = service.analyze_depth(depth_map)
        # Should trigger warning
        assert result['alert_level'] in [AlertLevel.DANGER, AlertLevel.NEAR]
        assert len(result['warnings']) > 0
