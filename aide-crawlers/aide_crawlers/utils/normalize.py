"""
Data Normalization Utilities

Normalize URLs, dates, and sources for consistency.
"""

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from datetime import datetime, timezone
from typing import Optional
import re


def normalize_url(url: str) -> str:
    """Normalize URL for consistent comparison

    - Remove tracking parameters (utm_*, fbclid, etc.)
    - Remove fragments (#)
    - Lowercase domain
    - Sort query parameters
    - Remove trailing slash

    Args:
        url: Raw URL string

    Returns:
        Normalized URL string

    Example:
        >>> normalize_url("https://news.naver.com/article/123?utm_source=fb#comment")
        'https://news.naver.com/article/123'
    """
    if not url:
        return ""

    try:
        parsed = urlparse(url)

        # Lowercase domain
        netloc = parsed.netloc.lower()

        # Parse and filter query parameters
        params = parse_qs(parsed.query)

        # Remove tracking parameters
        tracking_params = {
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', '_ga', '_gac', 'mc_cid', 'mc_eid'
        }

        filtered_params = {
            k: v for k, v in params.items()
            if k.lower() not in tracking_params
        }

        # Sort and encode query
        query = urlencode(sorted(filtered_params.items()), doseq=True)

        # Remove fragment
        fragment = ''

        # Remove trailing slash from path
        path = parsed.path.rstrip('/') if parsed.path != '/' else parsed.path

        # Reconstruct URL
        normalized = urlunparse((
            parsed.scheme,
            netloc,
            path,
            parsed.params,
            query,
            fragment
        ))

        return normalized

    except Exception:
        # Return original on error
        return url


def normalize_date(date_str: str) -> Optional[str]:
    """Normalize date string to ISO 8601 format

    Handles various Korean date formats:
    - "2025.10.20"
    - "2025-10-20"
    - "2025년 10월 20일"
    - "10분 전", "3시간 전", "어제", "그제"

    Args:
        date_str: Date string in various formats

    Returns:
        ISO 8601 formatted string (YYYY-MM-DDTHH:MM:SSZ) or None

    Example:
        >>> normalize_date("2025.10.20")
        '2025-10-20T00:00:00+00:00'
        >>> normalize_date("10분 전")
        '2025-10-20T07:50:00+00:00'  # Current time - 10 minutes
    """
    if not date_str:
        return None

    try:
        # Handle relative times (Korean)
        now = datetime.now(timezone.utc)

        # "N분 전"
        match = re.search(r'(\d+)분\s*전', date_str)
        if match:
            minutes = int(match.group(1))
            dt = now.replace(second=0, microsecond=0)
            dt = dt.replace(minute=dt.minute - minutes)
            return dt.isoformat()

        # "N시간 전"
        match = re.search(r'(\d+)시간\s*전', date_str)
        if match:
            hours = int(match.group(1))
            dt = now.replace(second=0, microsecond=0)
            dt = dt.replace(hour=dt.hour - hours)
            return dt.isoformat()

        # "어제"
        if '어제' in date_str:
            dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
            dt = dt.replace(day=dt.day - 1)
            return dt.isoformat()

        # "그제"
        if '그제' in date_str:
            dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
            dt = dt.replace(day=dt.day - 2)
            return dt.isoformat()

        # Clean Korean characters
        cleaned = date_str.replace('년', '-').replace('월', '-').replace('일', '')
        cleaned = cleaned.replace('.', '-').replace('/', '-')
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        # Try parsing with datetime
        for fmt in [
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
        ]:
            try:
                dt = datetime.strptime(cleaned, fmt)
                # Make timezone aware
                dt = dt.replace(tzinfo=timezone.utc)
                return dt.isoformat()
            except ValueError:
                continue

        # If all parsing fails, return None
        return None

    except Exception:
        return None


def normalize_source(source: str) -> str:
    """Normalize source/publisher name

    - Remove common suffixes (신문, 뉴스, 방송, etc.)
    - Remove whitespace
    - Standardize common names

    Args:
        source: Raw source name

    Returns:
        Normalized source name

    Example:
        >>> normalize_source("조선일보 신문")
        '조선일보'
        >>> normalize_source("  MBC 뉴스  ")
        'MBC'
    """
    if not source:
        return "Unknown"

    # Remove whitespace
    normalized = source.strip()

    # Remove common suffixes
    suffixes = ['신문', '뉴스', '방송', '일보', '경제', 'TV', '미디어']
    for suffix in suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)].strip()

    # Standardize common names
    standardization = {
        '조선': '조선일보',
        '중앙': '중앙일보',
        '동아': '동아일보',
        'KBS': 'KBS',
        'MBC': 'MBC',
        'SBS': 'SBS',
    }

    for key, value in standardization.items():
        if normalized.startswith(key):
            normalized = value
            break

    return normalized or "Unknown"


def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace and special characters

    Args:
        text: Raw text string

    Returns:
        Cleaned text

    Example:
        >>> clean_text("  Hello\\n\\n  World  ")
        'Hello World'
    """
    if not text:
        return ""

    # Remove multiple whitespace
    cleaned = re.sub(r'\s+', ' ', text)

    # Remove leading/trailing whitespace
    cleaned = cleaned.strip()

    return cleaned
