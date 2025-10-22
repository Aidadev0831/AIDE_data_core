"""Database writer for preprocessed news articles"""

from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session


class DBWriter:
    """Write preprocessed articles to database

    Handles database insertion with proper session management.
    """

    def __init__(self, session: Session):
        """Initialize DBWriter

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def write_article(
        self,
        model_class,
        title: str,
        source: str,
        url: str,
        date: datetime,
        keyword: str,
        description: str = "",
        content_hash: str = "",
        status: str = "raw"
    ) -> Optional[object]:
        """Write single article to database

        Args:
            model_class: SQLAlchemy model class (e.g., NaverNews)
            title: Article title (cleaned)
            source: Media source
            url: Article URL
            date: Publication date
            keyword: Search keyword
            description: Article description (cleaned)
            content_hash: SHA-256 hash
            status: Processing status (default: 'raw')

        Returns:
            Created model instance, or None if failed

        Example:
            >>> from aide_data_core.models import NaverNews
            >>> article = writer.write_article(
            ...     NaverNews,
            ...     title="PF 대출 위기",
            ...     source="조선일보",
            ...     url="https://...",
            ...     date=datetime.now(),
            ...     keyword="PF",
            ...     description="프로젝트 파이낸싱...",
            ...     content_hash="a1b2c3...",
            ... )
        """
        try:
            article = model_class(
                title=title,
                source=source,
                url=url,
                date=date,
                keyword=keyword,
                description=description,
                content_hash=content_hash,
                status=status
            )

            self.session.add(article)
            return article

        except Exception as e:
            print(f"Error writing article: {e}")
            return None

    def write_batch(
        self,
        model_class,
        articles: List[Dict]
    ) -> int:
        """Write multiple articles to database

        Args:
            model_class: SQLAlchemy model class
            articles: List of article dictionaries

        Returns:
            Number of articles written

        Example:
            >>> articles = [
            ...     {
            ...         "title": "PF 대출 위기",
            ...         "source": "조선일보",
            ...         "url": "https://...",
            ...         "date": datetime.now(),
            ...         "keyword": "PF",
            ...         "description": "...",
            ...         "content_hash": "...",
            ...     },
            ...     ...
            ... ]
            >>> count = writer.write_batch(NaverNews, articles)
        """
        written = 0

        for article_data in articles:
            article = self.write_article(model_class, **article_data)
            if article:
                written += 1

        return written

    def commit(self):
        """Commit the transaction"""
        try:
            self.session.commit()
        except Exception as e:
            print(f"Error committing transaction: {e}")
            self.session.rollback()
            raise

    def close(self):
        """Close the session"""
        self.session.close()
