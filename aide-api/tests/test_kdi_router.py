"""Tests for KDI API router"""

import pytest
from fastapi.testclient import TestClient


class TestKDIEndpoints:
    """Test KDI policy endpoints"""

    def test_get_policies_list(self, test_client: TestClient, multiple_kdi_policies):
        """Test getting list of policies"""
        response = test_client.get("/kdi/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 10

    def test_get_policies_with_pagination(self, test_client: TestClient, multiple_kdi_policies):
        """Test pagination"""
        response = test_client.get("/kdi/?skip=3&limit=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_get_policies_filter_by_category(self, test_client: TestClient, multiple_kdi_policies):
        """Test filtering by category"""
        response = test_client.get("/kdi/?category=경제정책")

        assert response.status_code == 200
        data = response.json()
        assert all("경제정책" in policy["category"] for policy in data if policy.get("category"))

    def test_get_policy_by_id(self, test_client: TestClient, sample_kdi_policy):
        """Test getting single policy"""
        policy_id = sample_kdi_policy.id
        response = test_client.get(f"/kdi/{policy_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == policy_id
        assert data["title"] == sample_kdi_policy.title

    def test_get_policy_not_found(self, test_client: TestClient):
        """Test 404 for non-existent policy"""
        response = test_client.get("/kdi/99999")

        assert response.status_code == 404

    def test_search_policies(self, test_client: TestClient, multiple_kdi_policies):
        """Test policy search"""
        response = test_client.get("/kdi/search/?q=정책")

        assert response.status_code == 200
        data = response.json()
        assert all("정책" in policy["title"] or "정책" in policy.get("description", "") for policy in data)

    def test_get_category_stats(self, test_client: TestClient, multiple_kdi_policies):
        """Test category statistics"""
        response = test_client.get("/kdi/categories/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_categories" in data
        assert "categories" in data
