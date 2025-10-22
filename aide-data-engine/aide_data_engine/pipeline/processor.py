"""Main Data Processing Pipeline

Orchestrates the complete data processing workflow:
1. Fetch raw articles from database
2. Generate embeddings
3. Deduplicate with DBSCAN
4. Select representatives
5. Classify with AI
6. Update database
"""

from typing import List, Dict, Optional
import json
import numpy as np
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aide_data_core.models import NaverNews, get_session
from aide_data_engine.services import (
    EmbeddingService,
    DeduplicationService,
    RepresentativeSelector,
    ClassificationService
)
from aide_data_engine.config import config

logger = logging.getLogger(__name__)


class DataProcessor:
    """Main Data Processing Pipeline

    Processes raw articles through embedding, deduplication, and classification.

    Example:
        >>> processor = DataProcessor(
        ...     database_url="postgresql://aide:aide123@localhost:5432/aide_db",
        ...     anthropic_api_key="your_api_key"
        ... )
        >>> result = processor.run()
        >>> print(f"Processed {result['processed']} articles")
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        batch_size: int = 100
    ):
        """Initialize data processor

        Args:
            database_url: Database connection URL
            anthropic_api_key: Anthropic API key for classification
            batch_size: Batch size for processing
        """
        self.database_url = database_url or config.database.url
        self.anthropic_api_key = anthropic_api_key or config.classification.api_key
        self.batch_size = batch_size

        # Initialize services
        self.embedding_service = EmbeddingService(
            model_name=config.embedding.model_name
        )
        self.dedup_service = DeduplicationService(
            eps=config.dbscan.eps,
            min_samples=config.dbscan.min_samples
        )
        self.representative_selector = RepresentativeSelector(
            information_weight=config.representative.information_weight,
            source_reliability_weight=config.representative.source_reliability_weight,
            trusted_sources=config.representative.trusted_sources
        )
        self.classification_service = ClassificationService(
            api_key=self.anthropic_api_key,
            model=config.classification.model
        )

        # Database session
        self.engine = create_engine(self.database_url)
        self.Session = sessionmaker(bind=self.engine)

        logger.info("DataProcessor initialized")

    def run(self, limit: Optional[int] = None) -> Dict:
        """Run complete processing pipeline

        Args:
            limit: Maximum number of articles to process (None = all)

        Returns:
            Dictionary with processing statistics
        """
        logger.info("Starting data processing pipeline")

        stats = {
            'fetched': 0,
            'embedded': 0,
            'deduplicated': 0,
            'representatives_selected': 0,
            'classified': 0,
            'processed': 0,
            'errors': 0
        }

        try:
            # Step 1: Fetch raw articles
            articles = self._fetch_raw_articles(limit=limit)
            stats['fetched'] = len(articles)
            logger.info(f"Fetched {len(articles)} raw articles")

            if not articles:
                logger.info("No raw articles to process")
                return stats

            # Step 2: Generate embeddings
            embeddings = self._generate_embeddings(articles)
            stats['embedded'] = len(embeddings)
            logger.info(f"Generated {len(embeddings)} embeddings")

            # Step 3: Deduplicate with DBSCAN
            cluster_ids = self._deduplicate(embeddings)
            stats['deduplicated'] = np.sum(cluster_ids != -1)
            logger.info(f"Found {stats['deduplicated']} duplicates in clusters")

            # Step 4: Select representatives
            representatives = self._select_representatives(articles, cluster_ids)
            stats['representatives_selected'] = len(representatives)
            logger.info(f"Selected {len(representatives)} representative articles")

            # Step 5: Classify representatives
            classifications = self._classify_articles(representatives)
            stats['classified'] = len(classifications)
            logger.info(f"Classified {len(classifications)} articles")

            # Step 6: Update database
            updated = self._update_database(articles, cluster_ids, representatives, classifications)
            stats['processed'] = updated
            logger.info(f"Updated {updated} articles in database")

        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}", exc_info=True)
            stats['errors'] += 1

        logger.info(f"Pipeline complete: {stats}")
        return stats

    def _fetch_raw_articles(self, limit: Optional[int] = None) -> List[NaverNews]:
        """Fetch raw articles from database

        Args:
            limit: Maximum number to fetch

        Returns:
            List of NaverNews objects
        """
        session = self.Session()
        try:
            query = session.query(NaverNews).filter(NaverNews.status == 'raw')
            if limit:
                query = query.limit(limit)
            articles = query.all()
            return articles
        finally:
            session.close()

    def _generate_embeddings(self, articles: List[NaverNews]) -> np.ndarray:
        """Generate embeddings for articles

        Args:
            articles: List of NaverNews objects

        Returns:
            Embedding matrix (N, 768)
        """
        article_dicts = [
            {
                'title': article.title,
                'description': article.description or ''
            }
            for article in articles
        ]

        embeddings = self.embedding_service.embed_articles(
            article_dicts,
            title_weight=0.7,
            description_weight=0.3,
            batch_size=config.embedding.batch_size,
            show_progress=True
        )

        return embeddings

    def _deduplicate(self, embeddings: np.ndarray) -> np.ndarray:
        """Deduplicate articles using DBSCAN

        Args:
            embeddings: Embedding matrix

        Returns:
            Cluster IDs array
        """
        cluster_ids = self.dedup_service.cluster(embeddings)
        return cluster_ids

    def _select_representatives(
        self,
        articles: List[NaverNews],
        cluster_ids: np.ndarray
    ) -> Dict[int, NaverNews]:
        """Select representative article from each cluster

        Args:
            articles: List of NaverNews objects
            cluster_ids: Cluster ID for each article

        Returns:
            Dictionary mapping cluster_id -> representative article
        """
        # Convert to dictionaries
        article_dicts = [
            {
                'id': article.id,
                'title': article.title,
                'description': article.description or '',
                'source': article.source,
                '_obj': article  # Keep reference to original object
            }
            for article in articles
        ]

        # Select representatives
        rep_dicts = self.representative_selector.select_from_clusters(
            article_dicts,
            cluster_ids.tolist()
        )

        # Extract original objects
        representatives = {
            cluster_id: rep_dict['_obj']
            for cluster_id, rep_dict in rep_dicts.items()
        }

        return representatives

    def _classify_articles(self, representatives: Dict[int, NaverNews]) -> Dict[int, Dict]:
        """Classify representative articles

        Args:
            representatives: Dict mapping cluster_id -> representative article

        Returns:
            Dict mapping cluster_id -> classification result
        """
        classifications = {}

        for cluster_id, article in representatives.items():
            result = self.classification_service.classify(
                title=article.title,
                description=article.description or ''
            )
            classifications[cluster_id] = result

        return classifications

    def _update_database(
        self,
        articles: List[NaverNews],
        cluster_ids: np.ndarray,
        representatives: Dict[int, NaverNews],
        classifications: Dict[int, Dict]
    ) -> int:
        """Update database with processing results

        Args:
            articles: List of all articles
            cluster_ids: Cluster ID for each article
            representatives: Representative articles by cluster
            classifications: Classifications by cluster

        Returns:
            Number of articles updated
        """
        session = self.Session()
        updated_count = 0

        try:
            for i, article in enumerate(articles):
                cluster_id = int(cluster_ids[i])

                # Set cluster info
                if cluster_id != -1:
                    article.duplicate_cluster_id = cluster_id

                    # Count duplicates in cluster
                    duplicate_count = np.sum(cluster_ids == cluster_id)
                    article.duplicate_count = int(duplicate_count)

                    # Check if representative
                    if cluster_id in representatives and representatives[cluster_id].id == article.id:
                        article.cluster_representative = True

                        # Add classification
                        if cluster_id in classifications:
                            classification = classifications[cluster_id]
                            article.classified_categories = json.dumps(
                                classification.get('categories', []),
                                ensure_ascii=False
                            )
                            article.tags = json.dumps(
                                classification.get('tags', []),
                                ensure_ascii=False
                            )
                            article.classification_confidence = classification.get('confidence', 0)
                    else:
                        article.cluster_representative = False
                else:
                    # Outlier (unique article)
                    article.duplicate_cluster_id = None
                    article.duplicate_count = 1
                    article.cluster_representative = True

                # Update status
                article.status = 'processed'
                updated_count += 1

            session.commit()
            logger.info(f"Database updated: {updated_count} articles")

        except Exception as e:
            session.rollback()
            logger.error(f"Database update failed: {str(e)}", exc_info=True)
            raise
        finally:
            session.close()

        return updated_count

    def close(self):
        """Clean up resources"""
        self.embedding_service.close()
        logger.info("DataProcessor closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
