"""
Tests for normalization utilities
"""

import pytest
from aide_crawlers.utils import normalize_url, normalize_date, normalize_source, clean_text


class TestNormalizeURL:
    """Test URL normalization"""

    def test_remove_tracking_params(self):
        """Test removal of tracking parameters"""
        url = "https://news.naver.com/article/123?utm_source=fb&utm_medium=social"
        result = normalize_url(url)
        assert result == "https://news.naver.com/article/123"

    def test_remove_fragment(self):
        """Test removal of URL fragment"""
        url = "https://example.com/page#comment"
        result = normalize_url(url)
        assert result == "https://example.com/page"

    def test_lowercase_domain(self):
        """Test domain lowercasing"""
        url = "https://NEWS.NAVER.COM/article/123"
        result = normalize_url(url)
        assert "news.naver.com" in result

    def test_empty_url(self):
        """Test empty URL"""
        result = normalize_url("")
        assert result == ""

    def test_invalid_url(self):
        """Test invalid URL returns original"""
        invalid = "not-a-url"
        result = normalize_url(invalid)
        assert result == invalid


class TestNormalizeDate:
    """Test date normalization"""

    def test_standard_format(self):
        """Test standard date format"""
        result = normalize_date("2025-10-20")
        assert result is not None
        assert "2025-10-20" in result

    def test_korean_format(self):
        """Test Korean date format"""
        result = normalize_date("2025년 10월 20일")
        assert result is not None
        assert "2025-10-20" in result

    def test_dot_format(self):
        """Test dot-separated format"""
        result = normalize_date("2025.10.20")
        assert result is not None
        assert "2025-10-20" in result

    def test_empty_date(self):
        """Test empty date"""
        result = normalize_date("")
        assert result is None


class TestNormalizeSource:
    """Test source normalization"""

    def test_remove_suffix(self):
        """Test removal of common suffixes"""
        result = normalize_source("조선일보 신문")
        assert result == "조선일보"

    def test_strip_whitespace(self):
        """Test whitespace stripping"""
        result = normalize_source("  MBC 뉴스  ")
        assert result == "MBC"

    def test_empty_source(self):
        """Test empty source"""
        result = normalize_source("")
        assert result == "Unknown"


class TestCleanText:
    """Test text cleaning"""

    def test_remove_extra_whitespace(self):
        """Test removal of extra whitespace"""
        result = clean_text("Hello   World")
        assert result == "Hello World"

    def test_remove_newlines(self):
        """Test removal of newlines"""
        result = clean_text("Hello\n\nWorld")
        assert result == "Hello World"

    def test_strip_whitespace(self):
        """Test stripping leading/trailing whitespace"""
        result = clean_text("  Hello World  ")
        assert result == "Hello World"

    def test_empty_text(self):
        """Test empty text"""
        result = clean_text("")
        assert result == ""
