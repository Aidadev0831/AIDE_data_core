"""Data processing services for AIDE Data Engine"""

from aide_data_engine.services.embedding import EmbeddingService
from aide_data_engine.services.deduplication import DeduplicationService
from aide_data_engine.services.representative import RepresentativeSelector
from aide_data_engine.services.classification import ClassificationService

__all__ = [
    "EmbeddingService",
    "DeduplicationService",
    "RepresentativeSelector",
    "ClassificationService",
]
