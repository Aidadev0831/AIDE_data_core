"""
DB Sink - Database Direct Storage

Stores crawled data directly to PostgreSQL/SQLite using AIDE Data Core models.
"""

from typing import List, Type
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import inspect

from aide_data_core.models.base import get_engine, Base
from aide_data_core.models import (
    NaverNews,
    KDIPolicy,
    CreditRating,
    PaperHeadline,
    StagingRawItem,
)

from ..utils.logger import setup_logger
from .abstract import AbstractSink, SinkResult

import json
import os

logger = setup_logger("db_sink", format_type="text")


class DBSink(AbstractSink):
    """DB 직접 저장 Sink

    AIDE Data Core 모델을 사용하여 PostgreSQL/SQLite에 직접 저장합니다.

    Example:
        >>> from aide_crawlers.sinks import DBSink
        >>> from aide_data_core.schemas import NaverNewsCreate
        >>>
        >>> # Domain table에 직접 저장
        >>> sink = DBSink(target_table="domain", model_class=NaverNews)
        >>> result = sink.write([NaverNewsCreate(...)])
        >>> sink.close()
        >>>
        >>> # Staging table에 저장
        >>> sink = DBSink(target_table="staging")
        >>> result = sink.write([NaverNewsCreate(...)])
        >>> sink.close()
    """

    def __init__(
        self,
        database_url: str = None,
        target_table: str = "staging",
        model_class: Type[Base] = None
    ):
        """Initialize DBSink

        Args:
            database_url: Database connection string (defaults to env DATABASE_URL)
            target_table: "staging" (staging_raw_items) or "domain" (naver_news etc)
            model_class: Domain table model class (required if target_table="domain")
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "sqlite:///./aide_dev.db"
        )
        self.target_table = target_table
        self.model_class = model_class

        # Create engine and session
        self.engine = get_engine(self.database_url)
        self.session = Session(self.engine)

        logger.info(f"DBSink initialized: target={target_table}, db={self.database_url}")

    def write(self, items: List[BaseModel]) -> SinkResult:
        """Write items to database

        Strategy:
        1. Deduplicate within batch (by url)
        2. For staging: Insert as raw JSON
        3. For domain: Upsert with ON CONFLICT (PostgreSQL) or merge (SQLite)
        4. Record errors in ingest_errors table

        Args:
            items: List of Pydantic schema instances

        Returns:
            SinkResult with counts
        """
        logger.info(f"DBSink.write() called with {len(items)} items")

        result: SinkResult = {
            "created": 0,
            "updated": 0,
            "duplicates": 0,
            "failed": 0
        }

        if not items:
            return result

        # 1. Deduplicate batch
        unique_items = self._dedup_batch(items)
        result['duplicates'] = len(items) - len(unique_items)

        logger.info(f"Batch dedup: {len(items)} → {len(unique_items)} unique items")

        # 2. Write to target table
        if self.target_table == "staging":
            result = self._write_to_staging(unique_items, result)
        else:
            result = self._write_to_domain(unique_items, result)

        logger.info(f"DBSink.write() completed: {result}")

        return result

    def _dedup_batch(self, items: List[BaseModel]) -> List[BaseModel]:
        """Remove duplicates within batch by URL"""
        seen = set()
        unique = []

        for item in items:
            # Get url or detail_url
            key = getattr(item, 'url', None) or getattr(item, 'detail_url', None)

            if key and key not in seen:
                seen.add(key)
                unique.append(item)

        return unique

    def _write_to_staging(self, items: List[BaseModel], result: SinkResult) -> SinkResult:
        """Write to staging_raw_items table

        Stores raw JSON payload for later processing
        """
        try:
            from datetime import datetime, timezone

            for item in items:
                staging = StagingRawItem(
                    job_id="manual",  # TODO: Add job tracking
                    source=getattr(item, 'source', 'unknown'),
                    raw_data=json.dumps(item.model_dump(), ensure_ascii=False),
                    item_url=getattr(item, 'url', None) or getattr(item, 'detail_url', 'unknown'),
                    ingested_at=datetime.now(timezone.utc),
                    processed=False
                )

                self.session.add(staging)

            self.session.commit()
            result['created'] = len(items)

            logger.info(f"Saved {len(items)} items to staging_raw_items")

        except Exception as e:
            logger.error(f"Failed to write to staging: {str(e)}")
            self.session.rollback()
            result['failed'] = len(items)

        return result

    def _write_to_domain(self, items: List[BaseModel], result: SinkResult) -> SinkResult:
        """Write to domain table with upsert logic

        Uses ON CONFLICT for PostgreSQL or fallback for SQLite
        """
        if not self.model_class:
            logger.error("model_class is required for domain table writes")
            result['failed'] = len(items)
            return result

        try:
            # Check if PostgreSQL
            dialect_name = self.engine.dialect.name

            if dialect_name == "postgresql":
                result = self._upsert_postgresql(items, result)
            else:
                result = self._upsert_sqlite(items, result)

        except Exception as e:
            logger.error(f"Failed to write to domain table: {str(e)}")
            self.session.rollback()
            result['failed'] = len(items)

        return result

    def _upsert_postgresql(self, items: List[BaseModel], result: SinkResult) -> SinkResult:
        """PostgreSQL upsert using ON CONFLICT"""
        # Convert Pydantic to dict
        values = [item.model_dump() for item in items]

        # INSERT ... ON CONFLICT DO UPDATE
        stmt = insert(self.model_class).values(values)

        # Assume unique constraint on 'url' column
        stmt = stmt.on_conflict_do_update(
            index_elements=['url'],
            set_={
                'content_hash': stmt.excluded.content_hash,
                'updated_at': stmt.excluded.updated_at,
            }
        )

        self.session.execute(stmt)
        self.session.commit()

        result['created'] = len(items)
        logger.info(f"Upserted {len(items)} items to {self.model_class.__tablename__}")

        return result

    def _upsert_sqlite(self, items: List[BaseModel], result: SinkResult) -> SinkResult:
        """SQLite upsert using merge logic"""
        for item in items:
            # Check if exists
            url = getattr(item, 'url', None)
            existing = self.session.query(self.model_class).filter_by(url=url).first()

            if existing:
                # Update
                for key, value in item.model_dump().items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                result['updated'] += 1
            else:
                # Insert
                new_item = self.model_class(**item.model_dump())
                self.session.add(new_item)
                result['created'] += 1

        self.session.commit()
        logger.info(f"Merged {result['created']} new, {result['updated']} updated")

        return result

    def close(self):
        """Close database session"""
        self.session.close()
        logger.info("DBSink closed")
