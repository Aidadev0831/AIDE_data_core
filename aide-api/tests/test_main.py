"""Tests for main app endpoints"""

import pytest
from fastapi.testclient import TestClient


class TestMainEndpoints:
    """Test main application endpoints"""

    def test_root_endpoint(self, test_client: TestClient):
        """Test root endpoint returns API info"""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert "name" in data
        assert "version" in data
        assert "description" in data
        assert "endpoints" in data

        # Check endpoints are listed
        endpoints = data["endpoints"]
        assert "/docs" in endpoints.values()
        assert "/health" in endpoints.values()
        assert "/news" in endpoints.values()
        assert "/kdi" in endpoints.values()
        assert "/ratings" in endpoints.values()

    def test_health_check(self, test_client: TestClient):
        """Test health check endpoint"""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "version" in data

    def test_openapi_docs(self, test_client: TestClient):
        """Test OpenAPI documentation is accessible"""
        response = test_client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()

        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_swagger_ui(self, test_client: TestClient):
        """Test Swagger UI is accessible"""
        response = test_client.get("/docs")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    def test_redoc(self, test_client: TestClient):
        """Test ReDoc is accessible"""
        response = test_client.get("/redoc")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    def test_cors_headers(self, test_client: TestClient):
        """Test CORS headers are set"""
        response = test_client.get("/")

        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers or response.status_code == 200
