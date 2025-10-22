"""Tests for Credit Rating API router"""

import pytest
from fastapi.testclient import TestClient


class TestRatingsEndpoints:
    """Test credit rating endpoints"""

    def test_get_ratings_list(self, test_client: TestClient, multiple_credit_ratings):
        """Test getting list of ratings"""
        response = test_client.get("/ratings/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 10

    def test_get_ratings_with_pagination(self, test_client: TestClient, multiple_credit_ratings):
        """Test pagination"""
        response = test_client.get("/ratings/?skip=2&limit=4")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4

    def test_get_ratings_filter_by_agency(self, test_client: TestClient, multiple_credit_ratings):
        """Test filtering by agency"""
        response = test_client.get("/ratings/?agency=kisrating")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        assert all(rating["agency"] == "kisrating" for rating in data)

    def test_get_ratings_filter_by_category(self, test_client: TestClient, multiple_credit_ratings):
        """Test filtering by category"""
        response = test_client.get("/ratings/?category=부동산")

        assert response.status_code == 200
        data = response.json()
        assert all("부동산" in rating["category"] for rating in data if rating.get("category"))

    def test_get_rating_by_id(self, test_client: TestClient, sample_credit_rating):
        """Test getting single rating"""
        rating_id = sample_credit_rating.id
        response = test_client.get(f"/ratings/{rating_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == rating_id
        assert data["title"] == sample_credit_rating.title
        assert data["agency"] == "kisrating"

    def test_get_rating_not_found(self, test_client: TestClient):
        """Test 404 for non-existent rating"""
        response = test_client.get("/ratings/99999")

        assert response.status_code == 404

    def test_search_ratings(self, test_client: TestClient, multiple_credit_ratings):
        """Test rating search"""
        response = test_client.get("/ratings/search/?q=리서치")

        assert response.status_code == 200
        data = response.json()
        assert all("리서치" in rating["title"] or "리서치" in rating.get("description", "") for rating in data)

    def test_get_agency_stats(self, test_client: TestClient, multiple_credit_ratings):
        """Test agency statistics"""
        response = test_client.get("/ratings/agencies/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_agencies" in data
        assert "agencies" in data
        assert isinstance(data["agencies"], list)
        assert len(data["agencies"]) == 2  # kisrating and korearatings

    def test_get_category_stats(self, test_client: TestClient, multiple_credit_ratings):
        """Test category statistics"""
        response = test_client.get("/ratings/categories/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_categories" in data
        assert "categories" in data
