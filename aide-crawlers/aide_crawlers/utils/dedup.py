"""
Deduplication Utilities

Generate deduplication keys for identifying duplicate items.
"""

from typing import Optional
from aide_data_core.utils import generate_content_hash
from .normalize import normalize_url


def generate_dedup_key(
    url: str,
    title: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """Generate deduplication key

    Strategy:
    1. Primary key: Normalized URL
    2. Fallback: Content hash (title + description)

    Args:
        url: Article URL
        title: Article title (optional)
        description: Article description (optional)

    Returns:
        Deduplication key (normalized URL or content hash)

    Example:
        >>> generate_dedup_key(
        ...     "https://news.naver.com/article/123?utm_source=fb",
        ...     "Test Title"
        ... )
        'https://news.naver.com/article/123'
    """
    # Use normalized URL as primary key
    normalized = normalize_url(url)

    if normalized:
        return normalized

    # Fallback to content hash
    if title or description:
        return generate_content_hash(title or "", description or "")

    # Last resort: original URL
    return url


def is_duplicate(
    new_url: str,
    existing_urls: set,
    new_title: Optional[str] = None,
    new_description: Optional[str] = None
) -> bool:
    """Check if item is duplicate

    Args:
        new_url: New item URL
        existing_urls: Set of existing normalized URLs
        new_title: New item title (optional)
        new_description: New item description (optional)

    Returns:
        True if duplicate, False otherwise

    Example:
        >>> existing = {'https://news.naver.com/article/123'}
        >>> is_duplicate(
        ...     "https://news.naver.com/article/123?utm_source=fb",
        ...     existing
        ... )
        True
    """
    dedup_key = generate_dedup_key(new_url, new_title, new_description)
    return dedup_key in existing_urls


def deduplicate_items(items: list, key_func=None) -> list:
    """Remove duplicates from list of items

    Args:
        items: List of items (dicts or objects)
        key_func: Function to extract dedup key from item
                  Default: lambda item: item.get('url') or item['url']

    Returns:
        List of unique items (preserves order)

    Example:
        >>> items = [
        ...     {'url': 'https://example.com/1', 'title': 'A'},
        ...     {'url': 'https://example.com/1?utm=x', 'title': 'A'},
        ...     {'url': 'https://example.com/2', 'title': 'B'},
        ... ]
        >>> unique = deduplicate_items(items)
        >>> len(unique)
        2
    """
    if not items:
        return []

    if key_func is None:
        # Default key function
        def key_func(item):
            if isinstance(item, dict):
                url = item.get('url') or item.get('detail_url', '')
                title = item.get('title', '')
                desc = item.get('description', '')
            else:
                url = getattr(item, 'url', '') or getattr(item, 'detail_url', '')
                title = getattr(item, 'title', '')
                desc = getattr(item, 'description', '')

            return generate_dedup_key(url, title, desc)

    seen = set()
    unique = []

    for item in items:
        key = key_func(item)

        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique
