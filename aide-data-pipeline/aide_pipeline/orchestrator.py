"""AIDE Pipeline Orchestrator - Unified data collection and processing coordinator"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from aide_data_core.models import IngestJobRun, IngestError
from aide_data_core.models.base import get_session

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates data collection and processing jobs

    This class coordinates the execution of crawling jobs and subsequent
    data processing tasks (embedding, deduplication, classification).

    Attributes:
        config: Pipeline configuration dictionary
        dry_run: If True, skip DB writes (for testing)
    """

    def __init__(self, config: Dict[str, Any], dry_run: bool = False):
        """Initialize orchestrator

        Args:
            config: Pipeline configuration from schedule.yaml
            dry_run: If True, run without DB writes
        """
        self.config = config
        self.dry_run = dry_run
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = self.config.get("global", {}).get("log_level", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def run_job(self, job_name: str) -> IngestJobRun:
        """Execute a single data collection job

        Args:
            job_name: Name of the job to run (naver_news, kdi_policy, etc.)

        Returns:
            IngestJobRun record with execution details

        Raises:
            ValueError: If job_name not found in config
            Exception: Any error during job execution
        """
        if job_name not in self.config.get("jobs", {}):
            available = list(self.config.get("jobs", {}).keys())
            raise ValueError(
                f"Job '{job_name}' not found. Available: {', '.join(available)}"
            )

        job_config = self.config["jobs"][job_name]

        if not job_config.get("enabled", True):
            logger.warning(f"Job '{job_name}' is disabled in configuration")
            return None

        with get_session() as db:
            job_run = IngestJobRun(
                job_name=job_name,
                started_at=datetime.now(timezone.utc),
                status="running",
            )
            db.add(job_run)
            db.commit()
            db.refresh(job_run)

            try:
                logger.info(f"Starting job: {job_name}")

                # Step 1: Crawling
                items_crawled = self._run_crawler(job_name, job_config, db)

                # Step 2: Processing (if not dry run)
                if not self.dry_run and items_crawled > 0:
                    items_processed = self._run_processor(job_name, job_config, db)
                else:
                    items_processed = 0
                    if self.dry_run:
                        logger.info(f"DRY RUN: Skipping processing for {job_name}")

                # Step 3: Update job status
                job_run.status = "completed"
                job_run.completed_at = datetime.now(timezone.utc)
                job_run.items_collected = items_crawled
                job_run.items_processed = items_processed

                logger.info(
                    f"Job {job_name} completed: "
                    f"{items_crawled} crawled, {items_processed} processed"
                )

            except Exception as e:
                logger.error(f"Job {job_name} failed: {e}", exc_info=True)

                # Record error
                error = IngestError(
                    job_run_id=job_run.id,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    traceback=self._get_traceback(),
                )
                db.add(error)

                job_run.status = "failed"
                job_run.completed_at = datetime.now(timezone.utc)
                job_run.error_message = str(e)

            finally:
                db.commit()

            return job_run

    def _run_crawler(
        self, job_name: str, job_config: Dict[str, Any], db: Session
    ) -> int:
        """Run crawler for specific job

        Args:
            job_name: Job identifier
            job_config: Job-specific configuration
            db: Database session

        Returns:
            Number of items collected
        """
        if job_name == "naver_news":
            return self._run_naver_news_crawler(job_config, db)
        elif job_name == "kdi_policy":
            return self._run_kdi_policy_crawler(job_config, db)
        elif job_name == "credit_rating":
            return self._run_credit_rating_crawler(job_config, db)
        else:
            raise ValueError(f"Unknown job type: {job_name}")

    def _run_naver_news_crawler(
        self, job_config: Dict[str, Any], db: Session
    ) -> int:
        """Run Naver news crawler

        Args:
            job_config: Naver news job configuration
            db: Database session

        Returns:
            Number of articles collected
        """
        try:
            from aide_crawlers.crawlers.naver import NaverNewsAPI
            from aide_crawlers.sinks import DBSink

            total_collected = 0
            sink = DBSink(db)

            # Crawl from API search
            for source in job_config.get("sources", []):
                if source["name"] == "api_search":
                    crawler = NaverNewsAPI(
                        client_id=self.config["env"]["naver_client_id"],
                        client_secret=self.config["env"]["naver_client_secret"],
                    )

                    for keyword in source.get("keywords", []):
                        items = crawler.search(keyword=keyword, display=100)
                        sink.save_batch(items)
                        total_collected += len(items)
                        logger.info(f"Collected {len(items)} articles for keyword: {keyword}")

            return total_collected

        except Exception as e:
            logger.error(f"Naver news crawler failed: {e}")
            raise

    def _run_kdi_policy_crawler(
        self, job_config: Dict[str, Any], db: Session
    ) -> int:
        """Run KDI policy crawler

        Args:
            job_config: KDI job configuration
            db: Database session

        Returns:
            Number of documents collected
        """
        try:
            from aide_crawlers.crawlers.research import KDIPolicyCrawler
            from aide_crawlers.sinks import DBSink

            sink = DBSink(db)
            crawler = KDIPolicyCrawler()

            date_range_days = job_config.get("filters", {}).get("date_range_days", 7)
            items = crawler.collect_recent(days=date_range_days)

            sink.save_batch(items)
            logger.info(f"Collected {len(items)} KDI policy documents")

            return len(items)

        except Exception as e:
            logger.error(f"KDI policy crawler failed: {e}")
            raise

    def _run_credit_rating_crawler(
        self, job_config: Dict[str, Any], db: Session
    ) -> int:
        """Run credit rating research crawler

        Args:
            job_config: Credit rating job configuration
            db: Database session

        Returns:
            Number of research reports collected
        """
        try:
            from aide_crawlers.crawlers.credit_rating import (
                KISRatingCrawler,
                KoreaRatingsCrawler,
            )
            from aide_crawlers.sinks import DBSink

            total_collected = 0
            sink = DBSink(db)

            for agency_config in job_config.get("agencies", []):
                if not agency_config.get("enabled", True):
                    continue

                agency_name = agency_config["name"]

                if agency_name == "kisrating":
                    crawler = KISRatingCrawler()
                elif agency_name == "korearatings":
                    crawler = KoreaRatingsCrawler()
                else:
                    logger.warning(f"Unsupported agency: {agency_name}")
                    continue

                items = crawler.collect_recent()
                sink.save_batch(items)
                total_collected += len(items)
                logger.info(f"Collected {len(items)} reports from {agency_name}")

            return total_collected

        except Exception as e:
            logger.error(f"Credit rating crawler failed: {e}")
            raise

    def _run_processor(
        self, job_name: str, job_config: Dict[str, Any], db: Session
    ) -> int:
        """Run data processing pipeline

        Args:
            job_name: Job identifier
            job_config: Job configuration
            db: Database session

        Returns:
            Number of items processed
        """
        try:
            from aide_data_engine.pipeline import DataProcessor

            processor = DataProcessor(db)
            processing_config = self.config.get("processing", {})

            if job_name == "naver_news":
                # Deduplication
                if processing_config.get("deduplication", {}).get("enabled", True):
                    processor.deduplicate_news(
                        similarity_threshold=processing_config["deduplication"].get(
                            "similarity_threshold", 0.85
                        )
                    )

                # Classification
                if processing_config.get("classification", {}).get("enabled", True):
                    processor.classify_news(
                        model=processing_config["classification"].get("model"),
                        batch_size=processing_config["classification"].get("batch_size", 10),
                    )

                # Representative selection
                if processing_config.get("representative", {}).get("enabled", True):
                    processor.select_representatives()

            elif job_name in ["kdi_policy", "credit_rating"]:
                # Classification only for documents
                if processing_config.get("classification", {}).get("enabled", True):
                    processor.classify_documents(source=job_name)

            # Return number of items processed (simplified)
            return db.query(IngestJobRun).filter_by(status="completed").count()

        except Exception as e:
            logger.error(f"Processing pipeline failed: {e}")
            raise

    def _get_traceback(self) -> str:
        """Get current exception traceback

        Returns:
            Formatted traceback string
        """
        import traceback
        return traceback.format_exc()
