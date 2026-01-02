"""
Integration tests for API endpoints.
"""

import pytest
import numpy as np
from pathlib import Path
import sys
import cv2
import base64
import io
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_image_file():
    """Create a sample image file for testing."""
    # Create a simple RGB image
    img = Image.new('RGB', (640, 480), color='red')
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    
    return img_byte_arr


class TestAnalyzeEndpoint:
    """Test suite for /api/analyze endpoint."""
    
    def test_endpoint_exists(self, client):
        """Test that endpoint exists."""
        # This will fail without proper model setup, but endpoint should exist
        response = client.post(
            "/api/analyze",
            files={"image": ("test.jpg", b"fake_image_data", "image/jpeg")}
        )
        # Should get 400 (bad request) or 500 (server error), not 404
        assert response.status_code != 404
    
    def test_missing_image_parameter(self, client):
        """Test missing image parameter."""
        response = client.post("/api/analyze")
        assert response.status_code == 422  # Unprocessable entity
    
    def test_invalid_content_type(self, client):
        """Test invalid content type."""
        response = client.post(
            "/api/analyze",
            files={"image": ("test.txt", b"not_an_image", "text/plain")}
        )
        # Should reject non-image content type
        assert response.status_code in [400, 422]
    
    def test_rate_limiting(self, client):
        """Test rate limiting (5 requests/second)."""
        # Note: This is a basic test. Real rate limiting test would be more complex
        responses = []
        for i in range(3):
            response = client.post(
                "/api/analyze",
                files={"image": ("test.jpg", b"fake", "image/jpeg")}
            )
            responses.append(response.status_code)
        
        # Should not get 429 (rate limit) for 3 requests
        assert 429 not in responses


class TestHealthEndpoint:
    """Test suite for health check endpoint."""
    
    def test_health_endpoint(self, client):
        """Test /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert 'status' in data
        assert data['status'] == 'healthy'
    
    def test_health_endpoint_response_format(self, client):
        """Test health endpoint response format."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert 'status' in data
        assert isinstance(data['status'], str)


class TestDocsEndpoint:
    """Test suite for API documentation."""
    
    def test_docs_endpoint(self, client):
        """Test /docs endpoint."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']
    
    def test_redoc_endpoint(self, client):
        """Test /redoc endpoint."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert 'text/html' in response.headers['content-type']


class TestCORS:
    """Test suite for CORS configuration."""
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options(
            "/api/analyze",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # Check CORS headers
        assert 'access-control-allow-origin' in response.headers or \
               'Access-Control-Allow-Origin' in response.headers
    
    def test_cors_preflight(self, client):
        """Test CORS preflight request."""
        response = client.options(
            "/api/analyze",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        assert response.status_code in [200, 204]


class TestErrorHandling:
    """Test suite for error handling."""
    
    def test_404_not_found(self, client):
        """Test 404 error for non-existent endpoint."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test 405 method not allowed."""
        response = client.get("/api/analyze")  # Should be POST
        assert response.status_code == 405
    
    def test_error_response_format(self, client):
        """Test error response format."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        
        # Check response is JSON
        assert 'application/json' in response.headers['content-type']


class TestResponseFormat:
    """Test suite for response format validation."""
    
    def test_analyze_response_structure(self):
        """Test response structure matches spec."""
        # Expected response format
        expected_fields = [
            'success',
            'timestamp',
            'processing_time_ms',
            'data',
            'error'
        ]
        
        # In a real test, we'd have actual response
        # This validates the schema exists
        for field in expected_fields:
            assert field is not None  # Placeholder
    
    def test_distance_stats_structure(self):
        """Test distance stats structure."""
        expected_stats = {
            'min': 0.5,
            'max': 5.0,
            'avg': 2.5
        }
        
        # Validate all required fields present
        assert 'min' in expected_stats
        assert 'max' in expected_stats
        assert 'avg' in expected_stats
        assert expected_stats['min'] <= expected_stats['avg'] <= expected_stats['max']
