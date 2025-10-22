"""News API Router

Provides endpoints for querying processed news articles.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
import json

from aide_data_core.models import NaverNews
from aide_data_core.schemas import NaverNewsResponse
from aide_api.dependencies.database import get_db
from aide_api.config import settings

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/", response_model=List[NaverNewsResponse])
def get_news(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description="Number of records to return"
    ),
    status: Optional[str] = Query(None, description="Filter by status (raw/processed/published)"),
    keyword: Optional[str] = Query(None, description="Filter by keyword"),
    source: Optional[str] = Query(None, description="Filter by source"),
    category: Optional[str] = Query(None, description="Filter by category"),
    representatives_only: bool = Query(False, description="Return only representative articles"),
    db: Session = Depends(get_db)
):
    """Get list of news articles

    Returns paginated list of news articles with optional filtering.
    """
    query = db.query(NaverNews)

    # Apply filters
    if status:
        query = query.filter(NaverNews.status == status)

    if keyword:
        query = query.filter(NaverNews.keyword == keyword)

    if source:
        query = query.filter(NaverNews.source.like(f"%{source}%"))

    if representatives_only:
        query = query.filter(NaverNews.cluster_representative == True)

    if category:
        # Filter by category (stored as JSON)
        query = query.filter(NaverNews.classified_categories.like(f'%"{category}"%'))

    # Order by date (newest first)
    query = query.order_by(desc(NaverNews.date))

    # Paginate
    articles = query.offset(skip).limit(limit).all()

    return articles


@router.get("/{article_id}", response_model=NaverNewsResponse)
def get_news_by_id(
    article_id: int,
    db: Session = Depends(get_db)
):
    """Get single news article by ID"""
    article = db.query(NaverNews).filter(NaverNews.id == article_id).first()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return article


@router.get("/cluster/{cluster_id}", response_model=List[NaverNewsResponse])
def get_cluster(
    cluster_id: int,
    db: Session = Depends(get_db)
):
    """Get all articles in a duplicate cluster

    Returns all duplicate articles that belong to the same cluster.
    """
    articles = db.query(NaverNews).filter(
        NaverNews.duplicate_cluster_id == cluster_id
    ).order_by(desc(NaverNews.cluster_representative)).all()

    if not articles:
        raise HTTPException(status_code=404, detail="Cluster not found")

    return articles


@router.get("/search/", response_model=List[NaverNewsResponse])
def search_news(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    db: Session = Depends(get_db)
):
    """Search news articles by title or description

    Full-text search across title and description fields.
    """
    search_filter = or_(
        NaverNews.title.like(f"%{q}%"),
        NaverNews.description.like(f"%{q}%")
    )

    articles = db.query(NaverNews).filter(
        search_filter
    ).order_by(desc(NaverNews.date)).offset(skip).limit(limit).all()

    return articles


@router.get("/categories/stats")
def get_category_stats(
    db: Session = Depends(get_db)
):
    """Get statistics by category

    Returns count of articles per category.
    """
    # Get all articles with categories
    articles = db.query(NaverNews).filter(
        and_(
            NaverNews.classified_categories.isnot(None),
            NaverNews.classified_categories != ''
        )
    ).all()

    # Count by category
    category_counts = {}
    for article in articles:
        try:
            categories = json.loads(article.classified_categories)
            for category in categories:
                category_counts[category] = category_counts.get(category, 0) + 1
        except (json.JSONDecodeError, TypeError):
            continue

    return {
        "total_articles": len(articles),
        "categories": category_counts
    }


@router.get("/sources/stats")
def get_source_stats(
    db: Session = Depends(get_db)
):
    """Get statistics by source

    Returns count of articles per news source.
    """
    from sqlalchemy import func

    results = db.query(
        NaverNews.source,
        func.count(NaverNews.id).label('count')
    ).group_by(NaverNews.source).order_by(desc('count')).all()

    return {
        "total_sources": len(results),
        "sources": [{"source": r.source, "count": r.count} for r in results]
    }
