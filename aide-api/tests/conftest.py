"""Pytest fixtures for AIDE API tests"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from aide_data_core.models.base import Base
from aide_data_core.models import NaverNews, KDIPolicy, CreditRating

from aide_api.main import app
from aide_api.dependencies.database import get_db


@pytest.fixture(scope="function")
def test_db() -> Session:
    """Create in-memory test database

    Returns:
        Session: SQLAlchemy session
    """
    # Create in-memory database with thread checking disabled for FastAPI TestClient
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False}  # Allow SQLite to work with TestClient
    )
    Base.metadata.create_all(engine)

    # Create session
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()

    yield db

    db.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def test_client(test_db: Session):
    """Create test client with test database

    Args:
        test_db: Test database session

    Returns:
        TestClient: FastAPI test client
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass  # Don't close here, conftest handles it

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()


# Sample data fixtures

@pytest.fixture
def sample_news_article(test_db: Session) -> NaverNews:
    """Create sample news article

    Args:
        test_db: Test database session

    Returns:
        NaverNews: Sample article
    """
    article = NaverNews(
        keyword="PF",
        title="정부, PF 대출 규제 강화",
        source="한국경제",
        url="https://example.com/news/1",
        date=datetime(2025, 10, 20, 12, 0, 0, tzinfo=timezone.utc),
        description="부동산 프로젝트 파이낸싱 대출 규제가 강화됩니다",
        content_hash="abc123def456",
        status="processed",
        duplicate_cluster_id=5,
        duplicate_count=3,
        cluster_representative=True,
        classified_categories='["정책/규제"]',
        tags='["PF", "대출규제"]',
        classification_confidence=95,
    )
    test_db.add(article)
    test_db.commit()
    test_db.refresh(article)
    return article


@pytest.fixture
def multiple_news_articles(test_db: Session) -> list[NaverNews]:
    """Create multiple news articles

    Args:
        test_db: Test database session

    Returns:
        list[NaverNews]: List of articles
    """
    articles = [
        NaverNews(
            keyword="PF" if i < 5 else "부동산",
            title=f"뉴스 기사 {i}",
            source="한국경제" if i % 2 == 0 else "매일경제",
            url=f"https://example.com/news/{i}",
            date=datetime(2025, 10, 20 - i, 12, 0, 0, tzinfo=timezone.utc),
            description=f"뉴스 설명 {i}",
            content_hash=f"hash{i}",
            status="processed" if i >= 5 else "raw",
            duplicate_cluster_id=i // 2 if i >= 5 else None,
            cluster_representative=i % 2 == 0 if i >= 5 else False,
            classified_categories='["정책/규제"]' if i % 3 == 0 else '["시장동향"]',
            tags='["PF"]',
            classification_confidence=90 + i,
        )
        for i in range(10)
    ]

    test_db.add_all(articles)
    test_db.commit()

    for article in articles:
        test_db.refresh(article)

    return articles


@pytest.fixture
def sample_kdi_policy(test_db: Session) -> KDIPolicy:
    """Create sample KDI policy

    Args:
        test_db: Test database session

    Returns:
        KDIPolicy: Sample policy
    """
    policy = KDIPolicy(
        title="2025년 경제정책 방향",
        url="https://kdi.re.kr/policy/12345",
        date=datetime(2025, 10, 15, 0, 0, 0, tzinfo=timezone.utc),
        source="KDI",
        description="2025년 주요 경제정책 방향",
        keyword="정책연구",
        content_hash="kdi_hash_123",
        pdf_url="https://kdi.re.kr/downloads/12345.pdf",
        category="경제정책",
        author="홍길동",
        status="raw",
    )
    test_db.add(policy)
    test_db.commit()
    test_db.refresh(policy)
    return policy


@pytest.fixture
def multiple_kdi_policies(test_db: Session) -> list[KDIPolicy]:
    """Create multiple KDI policies

    Args:
        test_db: Test database session

    Returns:
        list[KDIPolicy]: List of policies
    """
    policies = [
        KDIPolicy(
            title=f"정책 연구 {i}",
            url=f"https://kdi.re.kr/policy/{i}",
            date=datetime(2025, 10, 20 - i, 0, 0, 0, tzinfo=timezone.utc),
            source="KDI",
            description=f"정책 설명 {i}",
            keyword="정책연구",
            content_hash=f"kdi_hash{i}",
            category="경제정책" if i % 2 == 0 else "재정정책",
            author=f"연구자 {i}",
            status="raw",
        )
        for i in range(10)
    ]

    test_db.add_all(policies)
    test_db.commit()

    for policy in policies:
        test_db.refresh(policy)

    return policies


@pytest.fixture
def sample_credit_rating(test_db: Session) -> CreditRating:
    """Create sample credit rating

    Args:
        test_db: Test database session

    Returns:
        CreditRating: Sample rating
    """
    rating = CreditRating(
        title="2025 부동산 시장 전망",
        url="https://kisrating.com/research/12345",
        date=datetime(2025, 10, 18, 0, 0, 0, tzinfo=timezone.utc),
        source="KIS Rating",
        description="2025년 부동산 시장 전망",
        keyword="리서치",
        content_hash="rating_hash_123",
        category="부동산",
        author="김철수",
        agency="kisrating",
        status="raw",
    )
    test_db.add(rating)
    test_db.commit()
    test_db.refresh(rating)
    return rating


@pytest.fixture
def multiple_credit_ratings(test_db: Session) -> list[CreditRating]:
    """Create multiple credit ratings

    Args:
        test_db: Test database session

    Returns:
        list[CreditRating]: List of ratings
    """
    ratings = [
        CreditRating(
            title=f"리서치 보고서 {i}",
            url=f"https://rating.com/research/{i}",
            date=datetime(2025, 10, 20 - i, 0, 0, 0, tzinfo=timezone.utc),
            source="KIS Rating" if i % 2 == 0 else "Korea Ratings",
            description=f"리서치 설명 {i}",
            keyword="리서치",
            content_hash=f"rating_hash{i}",
            agency="kisrating" if i % 2 == 0 else "korearatings",
            category="부동산" if i % 3 == 0 else "금융",
            author=f"애널리스트 {i}",
            status="raw",
        )
        for i in range(10)
    ]

    test_db.add_all(ratings)
    test_db.commit()

    for rating in ratings:
        test_db.refresh(rating)

    return ratings
