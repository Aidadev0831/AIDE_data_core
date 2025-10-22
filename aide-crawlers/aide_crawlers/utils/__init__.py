"""Utils module

Export commonly used utilities
"""

from .logger import setup_logger
from .normalize import normalize_url, normalize_date, normalize_source, clean_text
from .dedup import generate_dedup_key, is_duplicate, deduplicate_items
from .validation import (
    validate_url,
    validate_required_fields,
    validate_news_item,
    validate_and_clean_item,
    sanitize_html,
    ValidationError,
)

__all__ = [
    # Logger
    "setup_logger",
    # Normalization
    "normalize_url",
    "normalize_date",
    "normalize_source",
    "clean_text",
    # Deduplication
    "generate_dedup_key",
    "is_duplicate",
    "deduplicate_items",
    # Validation
    "validate_url",
    "validate_required_fields",
    "validate_news_item",
    "validate_and_clean_item",
    "sanitize_html",
    "ValidationError",
]
