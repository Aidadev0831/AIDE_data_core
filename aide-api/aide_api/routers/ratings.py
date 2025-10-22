"""Credit Rating API Router

Provides endpoints for querying credit rating research reports.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from aide_data_core.models import CreditRating
from aide_data_core.schemas import CreditRatingResponse
from aide_api.dependencies.database import get_db
from aide_api.config import settings

router = APIRouter(prefix="/ratings", tags=["ratings"])


@router.get("/", response_model=List[CreditRatingResponse])
def get_ratings(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description="Number of records to return"
    ),
    status: Optional[str] = Query(None, description="Filter by status"),
    agency: Optional[str] = Query(None, description="Filter by agency (kisrating/korearatings)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    author: Optional[str] = Query(None, description="Filter by author"),
    db: Session = Depends(get_db)
):
    """Get list of credit rating research reports

    Returns paginated list of reports with optional filtering.
    """
    query = db.query(CreditRating)

    # Apply filters
    if status:
        query = query.filter(CreditRating.status == status)

    if agency:
        query = query.filter(CreditRating.agency == agency.lower())

    if category:
        query = query.filter(CreditRating.category.like(f"%{category}%"))

    if author:
        query = query.filter(CreditRating.author.like(f"%{author}%"))

    # Order by date (newest first)
    query = query.order_by(desc(CreditRating.date))

    # Paginate
    ratings = query.offset(skip).limit(limit).all()

    return ratings


@router.get("/{rating_id}", response_model=CreditRatingResponse)
def get_rating_by_id(
    rating_id: int,
    db: Session = Depends(get_db)
):
    """Get single credit rating report by ID"""
    rating = db.query(CreditRating).filter(CreditRating.id == rating_id).first()

    if not rating:
        raise HTTPException(status_code=404, detail="Rating report not found")

    return rating


@router.get("/search/", response_model=List[CreditRatingResponse])
def search_ratings(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    db: Session = Depends(get_db)
):
    """Search credit rating reports by title or description

    Full-text search across title and description fields.
    """
    search_filter = or_(
        CreditRating.title.like(f"%{q}%"),
        CreditRating.description.like(f"%{q}%")
    )

    ratings = db.query(CreditRating).filter(
        search_filter
    ).order_by(desc(CreditRating.date)).offset(skip).limit(limit).all()

    return ratings


@router.get("/agencies/stats")
def get_agency_stats(
    db: Session = Depends(get_db)
):
    """Get statistics by agency

    Returns count of reports per agency.
    """
    from sqlalchemy import func

    results = db.query(
        CreditRating.agency,
        func.count(CreditRating.id).label('count')
    ).group_by(CreditRating.agency).order_by(desc('count')).all()

    return {
        "total_agencies": len(results),
        "agencies": [{"agency": r.agency, "count": r.count} for r in results]
    }


@router.get("/categories/stats")
def get_category_stats(
    db: Session = Depends(get_db)
):
    """Get statistics by category

    Returns count of reports per category.
    """
    from sqlalchemy import func

    results = db.query(
        CreditRating.category,
        func.count(CreditRating.id).label('count')
    ).filter(
        CreditRating.category.isnot(None)
    ).group_by(CreditRating.category).order_by(desc('count')).all()

    return {
        "total_categories": len(results),
        "categories": [{"category": r.category, "count": r.count} for r in results]
    }
