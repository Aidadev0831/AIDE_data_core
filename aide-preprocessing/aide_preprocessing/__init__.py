"""AIDE Data Preprocessing Package

This package handles data preprocessing for news articles:
- HTML tag removal
- Source extraction from URLs
- Deduplication (URL + title similarity)
- Content hash generation
- Database storage
"""

__version__ = "0.1.0"

from aide_preprocessing.processors.text_cleaner import TextCleaner
from aide_preprocessing.processors.source_extractor import SourceExtractor
from aide_preprocessing.processors.deduplicator import Deduplicator
from aide_preprocessing.processors.hash_generator import HashGenerator
from aide_preprocessing.storage.db_writer import DBWriter
from aide_preprocessing.pipeline import PreprocessingPipeline

__all__ = [
    "TextCleaner",
    "SourceExtractor",
    "Deduplicator",
    "HashGenerator",
    "DBWriter",
    "PreprocessingPipeline",
]
