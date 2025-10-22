"""
Base Crawler

Abstract base class for all crawlers in AIDE platform.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from aide_data_core.utils import generate_content_hash
from aide_data_core.models import IngestJobRun, IngestError
from aide_data_core.models.base import get_engine

from ...utils import (
    setup_logger,
    normalize_url,
    normalize_date,
    normalize_source,
    deduplicate_items,
    validate_and_clean_item,
)
from ...sinks import AbstractSink, SinkResult

import uuid
import json


class BaseCrawler(ABC):
    """Abstract base crawler class

    All crawlers must implement:
    - crawl(): Fetch raw data from source
    - parse(): Parse raw data to standardized format

    The base class handles:
    - Normalization
    - Deduplication
    - Validation
    - Sink writing
    - Job logging

    Example:
        >>> from aide_crawlers.crawlers.base import BaseCrawler
        >>> from aide_crawlers.sinks import DBSink
        >>>
        >>> class MyCrawler(BaseCrawler):
        ...     def crawl(self) -> List[Dict]:
        ...         return [{'title': 'Test', 'url': 'https://example.com'}]
        ...
        ...     def parse(self, raw_data: Dict) -> Dict:
        ...         return raw_data
        >>>
        >>> crawler = MyCrawler(source_name="test", sink=DBSink())
        >>> results = crawler.run()
    """

    def __init__(
        self,
        source_name: str,
        sink: AbstractSink,
        database_url: str = None
    ):
        """Initialize base crawler

        Args:
            source_name: Crawler source identifier (e.g., "naver_news_api")
            sink: Sink instance for saving data
            database_url: Database URL for job logging (optional)
        """
        self.source_name = source_name
        self.sink = sink
        self.database_url = database_url

        self.logger = setup_logger(f"crawler.{source_name}")
        self.job_id = str(uuid.uuid4())
        self.job_run = None

        # Job statistics
        self.stats = {
            'crawled': 0,
            'parsed': 0,
            'validated': 0,
            'duplicates': 0,
            'failed': 0,
        }

    @abstractmethod
    def crawl(self) -> List[Dict[str, Any]]:
        """Crawl raw data from source

        This method should fetch data from the source (API, webpage, etc.)
        and return a list of raw data dictionaries.

        Returns:
            List of raw data dictionaries

        Example:
            def crawl(self):
                response = requests.get("https://api.example.com/news")
                return response.json()['items']
        """
        pass

    @abstractmethod
    def parse(self, raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse raw data to standardized format

        Convert raw data to AIDE Data Core schema format.

        Args:
            raw_item: Raw data dictionary from crawl()

        Returns:
            Parsed data dictionary or None if parsing fails

        Example:
            def parse(self, raw_item):
                return {
                    'title': raw_item['headline'],
                    'url': raw_item['link'],
                    'date': raw_item['published_at'],
                    'source': self.source_name,
                    'description': raw_item['summary'],
                }
        """
        pass

    def run(self) -> SinkResult:
        """Execute complete crawling pipeline

        Pipeline stages:
        1. Create job run log
        2. Crawl raw data
        3. Parse each item
        4. Normalize data
        5. Deduplicate
        6. Validate
        7. Write to sink
        8. Update job run log

        Returns:
            SinkResult with statistics
        """
        self.logger.info(f"Starting crawler: {self.source_name} (job_id={self.job_id})")

        try:
            # Stage 1: Create job run
            self._create_job_run()

            # Stage 2: Crawl raw data
            raw_items = self.crawl()
            self.stats['crawled'] = len(raw_items)
            self.logger.info(f"Crawled {len(raw_items)} raw items")

            # Stage 3: Parse items
            parsed_items = []
            for raw_item in raw_items:
                try:
                    parsed = self.parse(raw_item)
                    if parsed:
                        parsed_items.append(parsed)
                        self.stats['parsed'] += 1
                except Exception as e:
                    self.logger.warning(f"Parse failed: {str(e)}")
                    self.stats['failed'] += 1
                    self._record_error(raw_item, f"Parse error: {str(e)}")

            self.logger.info(f"Parsed {len(parsed_items)} items")

            # Stage 4: Normalize data
            normalized_items = [self._normalize_item(item) for item in parsed_items]

            # Stage 5: Deduplicate
            unique_items = deduplicate_items(normalized_items)
            self.stats['duplicates'] = len(normalized_items) - len(unique_items)
            self.logger.info(f"Deduplicated: {len(normalized_items)} → {len(unique_items)}")

            # Stage 6: Validate and clean
            validated_items = []
            for item in unique_items:
                cleaned = validate_and_clean_item(item)
                if cleaned:
                    validated_items.append(cleaned)
                    self.stats['validated'] += 1
                else:
                    self.stats['failed'] += 1

            self.logger.info(f"Validated {len(validated_items)} items")

            # Stage 7: Write to sink (convert to Pydantic schemas first)
            pydantic_items = self._convert_to_pydantic(validated_items)
            result = self.sink.write(pydantic_items)

            # Stage 8: Update job run
            self._complete_job_run(result)

            self.logger.info(f"Crawler completed: {result}")
            return result

        except Exception as e:
            self.logger.error(f"Crawler failed: {str(e)}")
            self._fail_job_run(str(e))
            raise

    def _normalize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize item data

        Applies normalization to URL, date, and source fields.

        Args:
            item: Parsed item dictionary

        Returns:
            Normalized item dictionary
        """
        normalized = item.copy()

        # Normalize URL
        if 'url' in normalized:
            normalized['url'] = normalize_url(normalized['url'])

        # Normalize date
        if 'date' in normalized and isinstance(normalized['date'], str):
            normalized_date = normalize_date(normalized['date'])
            if normalized_date:
                normalized['date'] = normalized_date

        # Normalize source
        if 'source' in normalized:
            normalized['source'] = normalize_source(normalized['source'])

        # Generate content hash if not present
        if 'content_hash' not in normalized:
            title = normalized.get('title', '')
            description = normalized.get('description', '')
            normalized['content_hash'] = generate_content_hash(title, description)

        return normalized

    def _convert_to_pydantic(self, items: List[Dict]) -> List[Any]:
        """Convert dicts to Pydantic schemas

        Override this method in subclasses to convert to specific schema types.

        Args:
            items: List of validated item dictionaries

        Returns:
            List of Pydantic schema instances
        """
        # Default: return as-is (subclasses should override)
        return items

    def _create_job_run(self):
        """Create job run log in database"""
        if not self.database_url:
            return

        try:
            engine = get_engine(self.database_url)
            from sqlalchemy.orm import Session

            with Session(engine) as session:
                self.job_run = IngestJobRun(
                    job_id=self.job_id,
                    source=self.source_name,
                    started_at=datetime.now(timezone.utc),
                    status="running"
                )
                session.add(self.job_run)
                session.commit()

                self.logger.info(f"Created job run: {self.job_id}")

        except Exception as e:
            self.logger.warning(f"Failed to create job run: {str(e)}")

    def _complete_job_run(self, result: SinkResult):
        """Mark job run as completed"""
        if not self.job_run:
            return

        try:
            self.job_run.mark_success({
                **result,
                **self.stats
            })

            engine = get_engine(self.database_url)
            from sqlalchemy.orm import Session

            with Session(engine) as session:
                session.add(self.job_run)
                session.commit()

                self.logger.info(f"Job run completed: {self.job_id}")

        except Exception as e:
            self.logger.warning(f"Failed to update job run: {str(e)}")

    def _fail_job_run(self, error_message: str):
        """Mark job run as failed"""
        if not self.job_run:
            return

        try:
            self.job_run.mark_failed(error_message)

            engine = get_engine(self.database_url)
            from sqlalchemy.orm import Session

            with Session(engine) as session:
                session.add(self.job_run)
                session.commit()

                self.logger.info(f"Job run failed: {self.job_id}")

        except Exception as e:
            self.logger.warning(f"Failed to update job run: {str(e)}")

    def _record_error(self, item: Dict, error_message: str):
        """Record error in database"""
        if not self.database_url:
            return

        try:
            engine = get_engine(self.database_url)
            from sqlalchemy.orm import Session

            with Session(engine) as session:
                error = IngestError(
                    job_id=self.job_id,
                    source=self.source_name,
                    item_ref=item.get('url', 'unknown'),
                    error_type="crawler_error",
                    error_message=error_message[:500],
                    payload_snapshot=json.dumps(item, ensure_ascii=False)[:2000],
                    retriable=True
                )
                session.add(error)
                session.commit()

        except Exception as e:
            self.logger.warning(f"Failed to record error: {str(e)}")

    def close(self):
        """Close resources"""
        if self.sink:
            self.sink.close()

        self.logger.info(f"Crawler closed: {self.source_name}")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        return False
