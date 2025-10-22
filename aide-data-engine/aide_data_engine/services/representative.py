"""Representative Article Selection Service

Selects the most representative article from each cluster based on:
1. Information content (50%): Length and detail of title + description
2. Source reliability (50%): Trustworthiness of the news source
"""

from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class RepresentativeSelector:
    """Representative Article Selection Service

    Selects one representative article from each cluster of duplicates.

    Example:
        >>> selector = RepresentativeSelector(
        ...     information_weight=0.5,
        ...     source_reliability_weight=0.5,
        ...     trusted_sources=["조선일보", "중앙일보"]
        ... )
        >>> articles = [
        ...     {"id": 1, "title": "짧은 제목", "description": "짧은 설명", "source": "조선일보"},
        ...     {"id": 2, "title": "매우 상세한 제목과 내용", "description": "매우 상세한 설명...", "source": "기타"},
        ... ]
        >>> rep = selector.select(articles)
        >>> print(rep["id"])  # 1 (trusted source wins despite shorter content)
    """

    def __init__(
        self,
        information_weight: float = 0.5,
        source_reliability_weight: float = 0.5,
        trusted_sources: List[str] = None
    ):
        """Initialize representative selector

        Args:
            information_weight: Weight for information content (0-1)
            source_reliability_weight: Weight for source reliability (0-1)
            trusted_sources: List of trusted news sources
        """
        if trusted_sources is None:
            trusted_sources = ["조선일보", "중앙일보", "동아일보", "한국경제", "매일경제"]

        self.information_weight = information_weight
        self.source_reliability_weight = source_reliability_weight
        self.trusted_sources = set(trusted_sources)

        # Normalize weights
        total = self.information_weight + self.source_reliability_weight
        if total > 0:
            self.information_weight /= total
            self.source_reliability_weight /= total

        logger.info(
            f"RepresentativeSelector initialized "
            f"(info={self.information_weight:.2f}, reliability={self.source_reliability_weight:.2f})"
        )

    def select(self, articles: List[Dict]) -> Optional[Dict]:
        """Select representative article from cluster

        Args:
            articles: List of article dictionaries

        Returns:
            Representative article dictionary, or None if empty
        """
        if not articles:
            return None

        if len(articles) == 1:
            return articles[0]

        # Score each article
        scored_articles = []
        for article in articles:
            score = self._score_article(article)
            scored_articles.append((score, article))

        # Sort by score (descending)
        scored_articles.sort(key=lambda x: x[0], reverse=True)

        representative = scored_articles[0][1]
        logger.debug(
            f"Selected representative: id={representative.get('id')}, "
            f"source={representative.get('source')}, "
            f"score={scored_articles[0][0]:.3f}"
        )

        return representative

    def select_from_clusters(
        self,
        articles: List[Dict],
        cluster_ids: List[int]
    ) -> Dict[int, Dict]:
        """Select representative from each cluster

        Args:
            articles: List of article dictionaries
            cluster_ids: Cluster ID for each article

        Returns:
            Dictionary mapping cluster_id -> representative article
        """
        # Group articles by cluster
        clusters = {}
        for article, cluster_id in zip(articles, cluster_ids):
            if cluster_id == -1:  # Skip outliers
                continue
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(article)

        # Select representative from each cluster
        representatives = {}
        for cluster_id, cluster_articles in clusters.items():
            rep = self.select(cluster_articles)
            if rep:
                representatives[cluster_id] = rep

        logger.info(f"Selected {len(representatives)} representatives from {len(clusters)} clusters")
        return representatives

    def _score_article(self, article: Dict) -> float:
        """Calculate score for article

        Args:
            article: Article dictionary with title, description, source

        Returns:
            Combined score (0-1)
        """
        # Information content score
        info_score = self._calculate_information_score(article)

        # Source reliability score
        reliability_score = self._calculate_reliability_score(article)

        # Combined score
        total_score = (
            self.information_weight * info_score +
            self.source_reliability_weight * reliability_score
        )

        return total_score

    def _calculate_information_score(self, article: Dict) -> float:
        """Calculate information content score

        Based on the length and detail of title + description.

        Args:
            article: Article dictionary

        Returns:
            Information score (0-1)
        """
        title = article.get('title', '')
        description = article.get('description', '')

        # Calculate lengths
        title_len = len(title)
        desc_len = len(description)

        # Score based on total length
        # Normalize to 0-1 range (assume max useful length = 500 chars)
        total_len = title_len + desc_len
        score = min(total_len / 500.0, 1.0)

        return score

    def _calculate_reliability_score(self, article: Dict) -> float:
        """Calculate source reliability score

        Args:
            article: Article dictionary with 'source' field

        Returns:
            Reliability score (0-1)
        """
        source = article.get('source', '')

        # Check if source is in trusted list
        if source in self.trusted_sources:
            return 1.0
        else:
            # Unknown sources get lower score
            return 0.3

    def rank_articles(self, articles: List[Dict]) -> List[tuple]:
        """Rank all articles by score

        Args:
            articles: List of article dictionaries

        Returns:
            List of (score, article) tuples, sorted by score descending
        """
        scored = [(self._score_article(article), article) for article in articles]
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored
