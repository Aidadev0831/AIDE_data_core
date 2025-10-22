"""Data processors for news articles"""

from aide_preprocessing.processors.text_cleaner import TextCleaner
from aide_preprocessing.processors.source_extractor import SourceExtractor
from aide_preprocessing.processors.deduplicator import Deduplicator
from aide_preprocessing.processors.hash_generator import HashGenerator

__all__ = [
    "TextCleaner",
    "SourceExtractor",
    "Deduplicator",
    "HashGenerator",
]
