"""Deduplication Service - DBSCAN-based clustering for duplicate detection

This service uses DBSCAN clustering on semantic embeddings to identify
duplicate or highly similar news articles.
"""

from typing import List, Dict, Tuple
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_distances
import logging

logger = logging.getLogger(__name__)


class DeduplicationService:
    """DBSCAN-based Deduplication Service

    Identifies duplicate articles by clustering semantic embeddings.
    Articles in the same cluster are considered duplicates.

    Example:
        >>> service = DeduplicationService(eps=0.3, min_samples=2)
        >>> embeddings = np.array([...])  # (N, 768)
        >>> cluster_ids = service.cluster(embeddings)
        >>> # cluster_ids: [-1, 0, 0, 1, 1, -1, ...]
        >>> # -1 = outlier (unique), 0+ = cluster ID
    """

    def __init__(
        self,
        eps: float = 0.3,
        min_samples: int = 2,
        metric: str = "cosine"
    ):
        """Initialize deduplication service

        Args:
            eps: Maximum distance between samples in a cluster
            min_samples: Minimum number of samples in a cluster
            metric: Distance metric ('cosine', 'euclidean', etc.)
        """
        self.eps = eps
        self.min_samples = min_samples
        self.metric = metric
        logger.info(
            f"DeduplicationService initialized (eps={eps}, min_samples={min_samples}, metric={metric})"
        )

    def cluster(self, embeddings: np.ndarray) -> np.ndarray:
        """Cluster embeddings using DBSCAN

        Args:
            embeddings: Embedding matrix (N, 768)

        Returns:
            Cluster IDs (N,) where -1 indicates outliers (unique articles)
        """
        if len(embeddings) == 0:
            return np.array([])

        logger.info(f"Clustering {len(embeddings)} embeddings")

        # Run DBSCAN
        dbscan = DBSCAN(
            eps=self.eps,
            min_samples=self.min_samples,
            metric=self.metric
        )
        cluster_ids = dbscan.fit_predict(embeddings)

        # Count clusters
        n_clusters = len(set(cluster_ids)) - (1 if -1 in cluster_ids else 0)
        n_outliers = np.sum(cluster_ids == -1)
        n_duplicates = len(embeddings) - n_outliers

        logger.info(
            f"Found {n_clusters} clusters, {n_duplicates} duplicates, {n_outliers} unique articles"
        )

        return cluster_ids

    def get_cluster_info(
        self,
        embeddings: np.ndarray,
        cluster_ids: np.ndarray
    ) -> Dict[int, Dict]:
        """Get detailed information about each cluster

        Args:
            embeddings: Embedding matrix (N, 768)
            cluster_ids: Cluster IDs from cluster() (N,)

        Returns:
            Dictionary mapping cluster_id -> cluster info
        """
        cluster_info = {}

        unique_clusters = set(cluster_ids)
        if -1 in unique_clusters:
            unique_clusters.remove(-1)  # Ignore outliers

        for cluster_id in unique_clusters:
            # Get indices in this cluster
            indices = np.where(cluster_ids == cluster_id)[0]
            cluster_embeddings = embeddings[indices]

            # Calculate centroid
            centroid = np.mean(cluster_embeddings, axis=0)

            # Calculate average distance to centroid
            distances = cosine_distances([centroid], cluster_embeddings)[0]
            avg_distance = np.mean(distances)

            cluster_info[int(cluster_id)] = {
                'size': len(indices),
                'indices': indices.tolist(),
                'avg_distance': float(avg_distance),
                'centroid': centroid
            }

        return cluster_info

    def find_similar_pairs(
        self,
        embeddings: np.ndarray,
        threshold: float = 0.3
    ) -> List[Tuple[int, int, float]]:
        """Find pairs of similar articles

        Args:
            embeddings: Embedding matrix (N, 768)
            threshold: Cosine distance threshold (lower = more similar)

        Returns:
            List of (idx1, idx2, distance) tuples for similar pairs
        """
        if len(embeddings) < 2:
            return []

        logger.info(f"Finding similar pairs (threshold={threshold})")

        # Calculate pairwise cosine distances
        distances = cosine_distances(embeddings)

        # Find pairs below threshold
        pairs = []
        n = len(embeddings)
        for i in range(n):
            for j in range(i + 1, n):
                dist = distances[i, j]
                if dist < threshold:
                    pairs.append((i, j, float(dist)))

        logger.info(f"Found {len(pairs)} similar pairs")
        return pairs

    def get_duplicate_groups(
        self,
        cluster_ids: np.ndarray,
        article_ids: List[int] = None
    ) -> Dict[int, List[int]]:
        """Group article IDs by cluster

        Args:
            cluster_ids: Cluster IDs from cluster() (N,)
            article_ids: Original article IDs (N,). If None, uses indices.

        Returns:
            Dictionary mapping cluster_id -> list of article IDs
        """
        if article_ids is None:
            article_ids = list(range(len(cluster_ids)))

        groups = {}
        unique_clusters = set(cluster_ids)
        if -1 in unique_clusters:
            unique_clusters.remove(-1)  # Ignore outliers

        for cluster_id in unique_clusters:
            indices = np.where(cluster_ids == cluster_id)[0]
            groups[int(cluster_id)] = [article_ids[i] for i in indices]

        return groups

    def calculate_similarity_matrix(
        self,
        embeddings: np.ndarray
    ) -> np.ndarray:
        """Calculate pairwise similarity matrix

        Args:
            embeddings: Embedding matrix (N, 768)

        Returns:
            Similarity matrix (N, N) with values in [0, 1]
            (1 = identical, 0 = completely different)
        """
        # Cosine distance -> cosine similarity
        distances = cosine_distances(embeddings)
        similarities = 1 - distances
        return similarities
