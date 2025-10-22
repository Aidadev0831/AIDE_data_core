"""
Tests for LocalSink
"""

import pytest
from pathlib import Path
import json
import tempfile
import shutil

from aide_crawlers.sinks import LocalSink, SinkResult
from pydantic import BaseModel


class MockNewsItem(BaseModel):
    """Mock news item for testing"""
    title: str
    url: str
    source: str
    date: str
    description: str = ""


class TestLocalSink:
    """Test LocalSink functionality"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def sample_items(self):
        """Create sample news items"""
        return [
            MockNewsItem(
                title="Test News 1",
                url="https://example.com/1",
                source="Test Source",
                date="2025-10-20T12:00:00Z",
                description="Test description 1"
            ),
            MockNewsItem(
                title="Test News 2",
                url="https://example.com/2",
                source="Test Source",
                date="2025-10-20T13:00:00Z",
                description="Test description 2"
            ),
        ]

    def test_write_json(self, temp_dir, sample_items):
        """Test writing items to JSON file"""
        sink = LocalSink(output_dir=temp_dir, format="json")

        result = sink.write(sample_items)

        # Check result
        assert result['created'] == 2
        assert result['failed'] == 0

        # Check file exists
        files = list(Path(temp_dir).glob("*.json"))
        assert len(files) == 1

        # Check file content
        with open(files[0], 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert len(data) == 2
            assert data[0]['title'] == "Test News 1"
            assert data[1]['title'] == "Test News 2"

        sink.close()

    def test_write_csv(self, temp_dir, sample_items):
        """Test writing items to CSV file"""
        sink = LocalSink(output_dir=temp_dir, format="csv")

        result = sink.write(sample_items)

        # Check result
        assert result['created'] == 2
        assert result['failed'] == 0

        # Check file exists
        files = list(Path(temp_dir).glob("*.csv"))
        assert len(files) == 1

        sink.close()

    def test_empty_items(self, temp_dir):
        """Test writing empty list"""
        sink = LocalSink(output_dir=temp_dir, format="json")

        result = sink.write([])

        # Check result
        assert result['created'] == 0
        assert result['failed'] == 0

        sink.close()

    def test_context_manager(self, temp_dir, sample_items):
        """Test using sink as context manager"""
        with LocalSink(output_dir=temp_dir, format="json") as sink:
            result = sink.write(sample_items)
            assert result['created'] == 2

        # Check file was created
        files = list(Path(temp_dir).glob("*.json"))
        assert len(files) == 1
