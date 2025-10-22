"""Preprocessing pipeline for news articles"""

from typing import Dict, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from aide_preprocessing.processors.text_cleaner import TextCleaner
from aide_preprocessing.processors.source_extractor import SourceExtractor
from aide_preprocessing.processors.hash_generator import HashGenerator
from aide_preprocessing.processors.deduplicator import Deduplicator
from aide_preprocessing.storage.db_writer import DBWriter


class PreprocessingPipeline:
    """Complete preprocessing pipeline for news articles

    Pipeline steps:
    1. Clean HTML tags from title and description
    2. Extract media source from URL
    3. Generate content hash
    4. Check for duplicates
    5. Write to database (if not duplicate)
    """

    def __init__(self, db_session: Session):
        """Initialize pipeline

        Args:
            db_session: SQLAlchemy database session
        """
        self.text_cleaner = TextCleaner()
        self.source_extractor = SourceExtractor()
        self.hash_generator = HashGenerator()
        self.deduplicator = Deduplicator()
        self.db_writer = DBWriter(db_session)
        self.db_session = db_session

    def preprocess_article(
        self,
        raw_article: Dict,
        keyword: str
    ) -> Dict:
        """Preprocess a single raw article

        Args:
            raw_article: Raw article from crawler with fields:
                - title: str (with HTML tags)
                - description: str (with HTML tags)
                - url: str
                - pubDate: str or datetime
            keyword: Search keyword used

        Returns:
            Preprocessed article dictionary

        Example:
            >>> raw = {
            ...     "title": "<b>PF</b> 대출 &quot;위기&quot;",
            ...     "description": "<b>프로젝트 파이낸싱</b>...",
            ...     "url": "https://www.chosun.com/...",
            ...     "pubDate": "Wed, 16 Oct 2024 18:30:00 +0900"
            ... }
            >>> preprocessed = pipeline.preprocess_article(raw, "PF")
        """
        # Step 1: Clean text
        title = self.text_cleaner.clean_title(raw_article.get('title', ''))
        description = self.text_cleaner.clean_description(raw_article.get('description', ''))

        # Step 2: Extract source
        url = raw_article.get('originallink') or raw_article.get('link') or raw_article.get('url')
        source = self.source_extractor.extract(url)

        # Step 3: Generate hash
        content_hash = self.hash_generator.generate(title, description)

        # Step 4: Parse date
        pub_date = raw_article.get('pubDate') or raw_article.get('date')
        if isinstance(pub_date, str):
            try:
                # Try RFC-822 format (Naver API)
                date = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
            except:
                date = datetime.now()
        elif isinstance(pub_date, datetime):
            date = pub_date
        else:
            date = datetime.now()

        return {
            'title': title,
            'description': description,
            'url': url,
            'source': source,
            'date': date,
            'keyword': keyword,
            'content_hash': content_hash,
            'status': 'raw'
        }

    def check_duplicate(
        self,
        url: str,
        title: str,
        model_class
    ) -> Tuple[bool, str]:
        """Check if article is duplicate

        Args:
            url: Article URL
            title: Article title
            model_class: SQLAlchemy model class

        Returns:
            Tuple of (is_duplicate, reason)
        """
        # Get existing URLs and titles from DB
        existing_articles = self.db_session.query(model_class).all()
        existing_urls = [a.url for a in existing_articles]

        # For title similarity, only check today's articles
        from datetime import date
        today_articles = self.db_session.query(model_class).filter(
            model_class.date >= date.today()
        ).all()
        existing_titles = [a.title for a in today_articles]

        return self.deduplicator.check_duplicate(
            url, title, existing_urls, existing_titles
        )

    def process_and_save(
        self,
        raw_articles: List[Dict],
        keyword: str,
        model_class
    ) -> Tuple[int, int, int]:
        """Process and save multiple articles

        Args:
            raw_articles: List of raw articles from crawler
            keyword: Search keyword
            model_class: SQLAlchemy model class

        Returns:
            Tuple of (total, saved, duplicates)

        Example:
            >>> from aide_data_core.models import NaverNews
            >>> raw_articles = [...]  # From crawler
            >>> total, saved, dupes = pipeline.process_and_save(
            ...     raw_articles, "PF", NaverNews
            ... )
            >>> print(f"Saved {saved}/{total} articles ({dupes} duplicates)")
        """
        total = len(raw_articles)
        saved = 0
        duplicates = 0

        for raw_article in raw_articles:
            # Preprocess
            preprocessed = self.preprocess_article(raw_article, keyword)

            # Check duplicate
            is_dup, reason = self.check_duplicate(
                preprocessed['url'],
                preprocessed['title'],
                model_class
            )

            if is_dup:
                duplicates += 1
                continue

            # Save to DB
            article = self.db_writer.write_article(model_class, **preprocessed)
            if article:
                saved += 1

        # Commit transaction
        self.db_writer.commit()

        return total, saved, duplicates

    def close(self):
        """Close database session"""
        self.db_writer.close()
