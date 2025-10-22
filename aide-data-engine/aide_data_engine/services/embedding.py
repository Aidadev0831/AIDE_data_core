"""Embedding Service - Generate KR-SBERT embeddings for Korean text

This service uses the jhgan/ko-sroberta-multitask model to generate
semantic embeddings for Korean news articles.
"""

from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """KR-SBERT Embedding Service

    Generates 768-dimensional semantic embeddings for Korean text using
    the jhgan/ko-sroberta-multitask model.

    Example:
        >>> service = EmbeddingService()
        >>> embedding = service.embed("PF 시장 안정화 정책 발표")
        >>> print(embedding.shape)
        (768,)

        >>> texts = ["뉴스 1", "뉴스 2", "뉴스 3"]
        >>> embeddings = service.embed_batch(texts)
        >>> print(embeddings.shape)
        (3, 768)
    """

    def __init__(
        self,
        model_name: str = "jhgan/ko-sroberta-multitask",
        device: str = None
    ):
        """Initialize embedding service

        Args:
            model_name: SentenceTransformers model name
            device: Device to use ('cpu', 'cuda', 'mps', or None for auto)
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        logger.info(f"Initializing EmbeddingService with model: {model_name}")

    def _load_model(self):
        """Load the sentence transformer model"""
        if self.model is None:
            logger.info(f"Loading model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            logger.info(f"Model loaded successfully (device: {self.model.device})")

    def embed(self, text: str) -> np.ndarray:
        """Generate embedding for single text

        Args:
            text: Input text

        Returns:
            Embedding vector (768,)
        """
        self._load_model()

        # Generate embedding
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            show_progress_bar=False
        )

        return embedding

    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> np.ndarray:
        """Generate embeddings for multiple texts

        Args:
            texts: List of input texts
            batch_size: Batch size for encoding
            show_progress: Show progress bar

        Returns:
            Embedding matrix (N, 768)
        """
        self._load_model()

        if not texts:
            return np.array([])

        # Generate embeddings
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=show_progress
        )

        logger.info(f"Generated embeddings for {len(texts)} texts")
        return embeddings

    def embed_articles(
        self,
        articles: List[dict],
        title_weight: float = 0.7,
        description_weight: float = 0.3,
        batch_size: int = 32,
        show_progress: bool = False
    ) -> np.ndarray:
        """Generate embeddings for articles (title + description)

        Combines title and description with weighted average.

        Args:
            articles: List of article dictionaries with 'title' and 'description'
            title_weight: Weight for title embedding (0-1)
            description_weight: Weight for description embedding (0-1)
            batch_size: Batch size for encoding
            show_progress: Show progress bar

        Returns:
            Embedding matrix (N, 768)
        """
        self._load_model()

        if not articles:
            return np.array([])

        # Prepare texts
        titles = [article.get('title', '') for article in articles]
        descriptions = [article.get('description', '') for article in articles]

        # Generate embeddings separately
        logger.info(f"Generating embeddings for {len(articles)} articles")
        title_embeddings = self.model.encode(
            titles,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=show_progress
        )

        description_embeddings = self.model.encode(
            descriptions,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=False  # Only show progress for one
        )

        # Weighted average
        combined_embeddings = (
            title_weight * title_embeddings +
            description_weight * description_embeddings
        )

        # Normalize
        norms = np.linalg.norm(combined_embeddings, axis=1, keepdims=True)
        combined_embeddings = combined_embeddings / (norms + 1e-8)

        logger.info(f"Generated combined embeddings for {len(articles)} articles")
        return combined_embeddings

    def close(self):
        """Free model resources"""
        if self.model is not None:
            del self.model
            self.model = None
            logger.info("Model resources freed")

    def __enter__(self):
        """Context manager entry"""
        self._load_model()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
