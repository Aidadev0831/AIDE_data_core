"""Tests for News API router"""

import pytest
from fastapi.testclient import TestClient


class TestNewsEndpoints:
    """Test news API endpoints"""

    def test_get_news_list_success(self, test_client: TestClient, multiple_news_articles):
        """Test getting list of news articles"""
        response = test_client.get("/news/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 10

    def test_get_news_with_pagination(self, test_client: TestClient, multiple_news_articles):
        """Test pagination parameters"""
        response = test_client.get("/news/?skip=2&limit=3")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_news_filter_by_status(self, test_client: TestClient, multiple_news_articles):
        """Test filtering by status"""
        response = test_client.get("/news/?status=processed")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        assert all(article["status"] == "processed" for article in data)

    def test_get_news_filter_by_keyword(self, test_client: TestClient, multiple_news_articles):
        """Test filtering by keyword"""
        response = test_client.get("/news/?keyword=PF")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        assert all(article["keyword"] == "PF" for article in data)

    def test_get_news_filter_by_source(self, test_client: TestClient, multiple_news_articles):
        """Test filtering by source"""
        response = test_client.get("/news/?source=한국경제")

        assert response.status_code == 200
        data = response.json()
        assert all("한국경제" in article["source"] for article in data)

    def test_get_news_representatives_only(self, test_client: TestClient, multiple_news_articles):
        """Test filtering representatives only"""
        response = test_client.get("/news/?representatives_only=true")

        assert response.status_code == 200
        data = response.json()
        # Should only have representative articles
        assert all(article.get("cluster_representative") is True for article in data if article.get("cluster_representative") is not None)

    def test_get_news_by_id_success(self, test_client: TestClient, sample_news_article):
        """Test getting single article by ID"""
        article_id = sample_news_article.id
        response = test_client.get(f"/news/{article_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == article_id
        assert data["title"] == sample_news_article.title

    def test_get_news_by_id_not_found(self, test_client: TestClient):
        """Test 404 for non-existent article"""
        response = test_client.get("/news/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_news_cluster(self, test_client: TestClient, multiple_news_articles):
        """Test getting articles in a cluster"""
        response = test_client.get("/news/cluster/2")

        assert response.status_code == 200
        data = response.json()
        assert all(article["duplicate_cluster_id"] == 2 for article in data)

    def test_search_news(self, test_client: TestClient, multiple_news_articles):
        """Test news search"""
        response = test_client.get("/news/search/?q=뉴스")

        assert response.status_code == 200
        data = response.json()
        assert all("뉴스" in article["title"] or "뉴스" in article.get("description", "") for article in data)

    def test_search_news_with_pagination(self, test_client: TestClient, multiple_news_articles):
        """Test search with pagination"""
        response = test_client.get("/news/search/?q=뉴스&limit=3")

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3

    def test_get_categories_stats(self, test_client: TestClient, multiple_news_articles):
        """Test category statistics"""
        response = test_client.get("/news/categories/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_categories" in data
        assert "categories" in data
        assert isinstance(data["categories"], list)

    def test_get_sources_stats(self, test_client: TestClient, multiple_news_articles):
        """Test source statistics"""
        response = test_client.get("/news/sources/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_sources" in data
        assert "sources" in data
        assert isinstance(data["sources"], list)

    def test_get_news_with_invalid_pagination(self, test_client: TestClient):
        """Test invalid pagination parameters"""
        # Negative skip
        response = test_client.get("/news/?skip=-1")
        assert response.status_code == 422

        # Limit too large
        response = test_client.get("/news/?limit=1000")
        assert response.status_code == 422

    def test_get_news_empty_result(self, test_client: TestClient):
        """Test getting news when database is empty"""
        response = test_client.get("/news/")

        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestNewsResponseFormat:
    """Test response format validation"""

    def test_news_response_structure(self, test_client: TestClient, sample_news_article):
        """Test news response has all required fields"""
        response = test_client.get(f"/news/{sample_news_article.id}")

        assert response.status_code == 200
        data = response.json()

        # Required fields
        assert "id" in data
        assert "keyword" in data
        assert "title" in data
        assert "source" in data
        assert "url" in data
        assert "date" in data
        assert "content_hash" in data
        assert "status" in data

        # Optional fields
        assert "description" in data
        assert "duplicate_cluster_id" in data
        assert "cluster_representative" in data
        assert "classified_categories" in data
        assert "tags" in data
        assert "classification_confidence" in data

    def test_news_list_response_format(self, test_client: TestClient, multiple_news_articles):
        """Test news list response is array"""
        response = test_client.get("/news/")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            assert isinstance(data[0], dict)
            assert "id" in data[0]
            assert "title" in data[0]
