"""Deduplication logic for news articles"""

from difflib import SequenceMatcher
from typing import List, Tuple, Optional
from datetime import date


class Deduplicator:
    """Check for duplicate articles

    Uses two methods:
    1. URL-based: Exact URL match
    2. Title similarity: 98% similarity threshold
    """

    SIMILARITY_THRESHOLD = 0.98

    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """Calculate similarity ratio between two texts

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity ratio (0.0 ~ 1.0)

        Example:
            >>> Deduplicator.calculate_similarity("PF 대출 위기", "PF대출 위기")
            0.98
        """
        return SequenceMatcher(None, text1, text2).ratio()

    @staticmethod
    def is_duplicate_by_url(url: str, existing_urls: List[str]) -> bool:
        """Check if URL already exists

        Args:
            url: Article URL to check
            existing_urls: List of existing URLs

        Returns:
            True if URL exists
        """
        return url in existing_urls

    @staticmethod
    def is_duplicate_by_title(
        title: str,
        existing_titles: List[str],
        threshold: float = SIMILARITY_THRESHOLD
    ) -> Tuple[bool, Optional[str]]:
        """Check if title is similar to existing titles

        Args:
            title: Article title to check
            existing_titles: List of existing titles
            threshold: Similarity threshold (default: 0.98)

        Returns:
            Tuple of (is_duplicate, similar_title)

        Example:
            >>> Deduplicator.is_duplicate_by_title(
            ...     "PF 대출 위기",
            ...     ["PF대출 위기", "부동산 뉴스"],
            ...     0.98
            ... )
            (True, "PF대출 위기")
        """
        for existing_title in existing_titles:
            similarity = Deduplicator.calculate_similarity(title, existing_title)
            if similarity >= threshold:
                return True, existing_title

        return False, None

    @staticmethod
    def check_duplicate(
        url: str,
        title: str,
        existing_urls: List[str],
        existing_titles: List[str]
    ) -> Tuple[bool, str]:
        """Check if article is duplicate

        Checks both URL and title similarity.

        Args:
            url: Article URL
            title: Article title
            existing_urls: List of existing URLs
            existing_titles: List of existing titles

        Returns:
            Tuple of (is_duplicate, reason)
            reason: "url" | "title" | "none"

        Example:
            >>> Deduplicator.check_duplicate(
            ...     "https://example.com/article",
            ...     "PF 대출 위기",
            ...     ["https://example.com/article"],
            ...     []
            ... )
            (True, "url")
        """
        # Check URL first (faster)
        if Deduplicator.is_duplicate_by_url(url, existing_urls):
            return True, "url"

        # Check title similarity
        is_dup, _ = Deduplicator.is_duplicate_by_title(title, existing_titles)
        if is_dup:
            return True, "title"

        return False, "none"
