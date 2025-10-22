"""
Data Validation Utilities

Validate crawled data before saving to database or sending to API.
"""

from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import re


class ValidationError(Exception):
    """Raised when data validation fails"""
    pass


def validate_url(url: str) -> bool:
    """Validate URL format

    Args:
        url: URL string to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_url("https://news.naver.com/article/123")
        True
        >>> validate_url("not-a-url")
        False
    """
    if not url or not isinstance(url, str):
        return False

    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> tuple[bool, List[str]]:
    """Validate that required fields are present and non-empty

    Args:
        data: Data dictionary to validate
        required_fields: List of required field names

    Returns:
        Tuple of (is_valid, missing_fields)

    Example:
        >>> data = {'title': 'Test', 'url': 'https://example.com'}
        >>> valid, missing = validate_required_fields(data, ['title', 'url', 'date'])
        >>> valid
        False
        >>> missing
        ['date']
    """
    missing = []

    for field in required_fields:
        value = data.get(field)

        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field)

    return len(missing) == 0, missing


def validate_text_length(text: str, min_length: int = 1, max_length: int = 10000) -> bool:
    """Validate text length

    Args:
        text: Text to validate
        min_length: Minimum length (default: 1)
        max_length: Maximum length (default: 10000)

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_text_length("Hello", min_length=3, max_length=100)
        True
        >>> validate_text_length("Hi", min_length=3)
        False
    """
    if not text or not isinstance(text, str):
        return False

    length = len(text.strip())
    return min_length <= length <= max_length


def validate_date_format(date_str: str) -> bool:
    """Validate date format (ISO 8601)

    Args:
        date_str: Date string to validate

    Returns:
        True if valid ISO format, False otherwise

    Example:
        >>> validate_date_format("2025-10-20T12:00:00Z")
        True
        >>> validate_date_format("2025/10/20")
        False
    """
    if not date_str or not isinstance(date_str, str):
        return False

    # Check ISO 8601 pattern
    iso_pattern = r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$'
    return bool(re.match(iso_pattern, date_str))


def validate_news_item(item: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Validate news item data

    Checks:
    - Required fields: title, url, date, source
    - URL format
    - Title length (5-500 chars)
    - Date format

    Args:
        item: News item dictionary

    Returns:
        Tuple of (is_valid, error_messages)

    Example:
        >>> item = {
        ...     'title': 'Test News',
        ...     'url': 'https://example.com/news/1',
        ...     'date': '2025-10-20T12:00:00Z',
        ...     'source': 'Test Source'
        ... }
        >>> valid, errors = validate_news_item(item)
        >>> valid
        True
    """
    errors = []

    # Required fields
    required = ['title', 'url', 'date', 'source']
    is_valid, missing = validate_required_fields(item, required)

    if not is_valid:
        errors.append(f"Missing required fields: {', '.join(missing)}")

    # URL validation
    if 'url' in item and not validate_url(item['url']):
        errors.append("Invalid URL format")

    # Title length
    if 'title' in item and not validate_text_length(item['title'], min_length=5, max_length=500):
        errors.append("Title must be 5-500 characters")

    # Date format
    if 'date' in item and isinstance(item['date'], str):
        if not validate_date_format(item['date']):
            errors.append("Invalid date format (must be ISO 8601)")

    return len(errors) == 0, errors


def sanitize_html(html: str) -> str:
    """Remove HTML tags from text

    Args:
        html: HTML string

    Returns:
        Plain text without HTML tags

    Example:
        >>> sanitize_html("<p>Hello <b>World</b></p>")
        'Hello World'
    """
    if not html:
        return ""

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html)

    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)

    # Remove leading/trailing whitespace
    return text.strip()


def validate_and_clean_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Validate and clean item data

    Args:
        item: Raw item data

    Returns:
        Cleaned item dict or None if validation fails

    Example:
        >>> item = {
        ...     'title': '<p>Test</p>',
        ...     'url': 'https://example.com',
        ...     'date': '2025-10-20T12:00:00Z',
        ...     'source': '  Test Source  '
        ... }
        >>> cleaned = validate_and_clean_item(item)
        >>> cleaned['title']
        'Test'
        >>> cleaned['source']
        'Test Source'
    """
    if not item or not isinstance(item, dict):
        return None

    # Validate
    is_valid, errors = validate_news_item(item)

    if not is_valid:
        return None

    # Clean
    cleaned = item.copy()

    # Sanitize title
    if 'title' in cleaned and isinstance(cleaned['title'], str):
        cleaned['title'] = sanitize_html(cleaned['title'])

    # Sanitize description
    if 'description' in cleaned and isinstance(cleaned['description'], str):
        cleaned['description'] = sanitize_html(cleaned['description'])

    # Strip whitespace from source
    if 'source' in cleaned and isinstance(cleaned['source'], str):
        cleaned['source'] = cleaned['source'].strip()

    return cleaned
