"""
Pytest configuration and fixtures
"""

import pytest
import os


@pytest.fixture(scope="session")
def test_database_url():
    """Test database URL"""
    return os.getenv("DATABASE_URL_TEST", "sqlite:///./test.db")


@pytest.fixture(scope="session")
def naver_api_credentials():
    """Naver API test credentials"""
    return {
        "client_id": os.getenv("NAVER_CLIENT_ID", "test_client_id"),
        "client_secret": os.getenv("NAVER_CLIENT_SECRET", "test_client_secret")
    }
