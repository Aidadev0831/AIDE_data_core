"""KDI Policy API Router

Provides endpoints for querying KDI policy documents.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from aide_data_core.models import KDIPolicy
from aide_data_core.schemas import KDIPolicyResponse
from aide_api.dependencies.database import get_db
from aide_api.config import settings

router = APIRouter(prefix="/kdi", tags=["kdi"])


@router.get("/", response_model=List[KDIPolicyResponse])
def get_policies(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description="Number of records to return"
    ),
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    author: Optional[str] = Query(None, description="Filter by author"),
    db: Session = Depends(get_db)
):
    """Get list of KDI policy documents

    Returns paginated list of policy documents with optional filtering.
    """
    query = db.query(KDIPolicy)

    # Apply filters
    if status:
        query = query.filter(KDIPolicy.status == status)

    if category:
        query = query.filter(KDIPolicy.category.like(f"%{category}%"))

    if author:
        query = query.filter(KDIPolicy.author.like(f"%{author}%"))

    # Order by date (newest first)
    query = query.order_by(desc(KDIPolicy.date))

    # Paginate
    policies = query.offset(skip).limit(limit).all()

    return policies


@router.get("/{policy_id}", response_model=KDIPolicyResponse)
def get_policy_by_id(
    policy_id: int,
    db: Session = Depends(get_db)
):
    """Get single KDI policy document by ID"""
    policy = db.query(KDIPolicy).filter(KDIPolicy.id == policy_id).first()

    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    return policy


@router.get("/search/", response_model=List[KDIPolicyResponse])
def search_policies(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    db: Session = Depends(get_db)
):
    """Search KDI policy documents by title or description

    Full-text search across title and description fields.
    """
    search_filter = or_(
        KDIPolicy.title.like(f"%{q}%"),
        KDIPolicy.description.like(f"%{q}%")
    )

    policies = db.query(KDIPolicy).filter(
        search_filter
    ).order_by(desc(KDIPolicy.date)).offset(skip).limit(limit).all()

    return policies


@router.get("/categories/stats")
def get_category_stats(
    db: Session = Depends(get_db)
):
    """Get statistics by category

    Returns count of policies per category.
    """
    from sqlalchemy import func

    results = db.query(
        KDIPolicy.category,
        func.count(KDIPolicy.id).label('count')
    ).filter(
        KDIPolicy.category.isnot(None)
    ).group_by(KDIPolicy.category).order_by(desc('count')).all()

    return {
        "total_categories": len(results),
        "categories": [{"category": r.category, "count": r.count} for r in results]
    }
