"""Configuration management for AIDE Data Engine"""

import os
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class EmbeddingConfig(BaseModel):
    """Embedding service configuration"""

    model_name: str = Field(
        default=os.getenv("EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask"),
        description="KR-SBERT model name"
    )
    dimension: int = Field(
        default=int(os.getenv("EMBEDDING_DIMENSION", "768")),
        description="Embedding dimension"
    )
    batch_size: int = Field(
        default=int(os.getenv("BATCH_SIZE", "32")),
        description="Batch size for embedding"
    )


class DBSCANConfig(BaseModel):
    """DBSCAN clustering configuration"""

    eps: float = Field(
        default=float(os.getenv("DBSCAN_EPS", "0.3")),
        description="Maximum distance between samples"
    )
    min_samples: int = Field(
        default=int(os.getenv("DBSCAN_MIN_SAMPLES", "2")),
        description="Minimum cluster size"
    )


class RepresentativeConfig(BaseModel):
    """Representative article selection configuration"""

    information_weight: float = Field(
        default=float(os.getenv("INFORMATION_WEIGHT", "0.5")),
        description="Weight for information content (0-1)"
    )
    source_reliability_weight: float = Field(
        default=float(os.getenv("SOURCE_RELIABILITY_WEIGHT", "0.5")),
        description="Weight for source reliability (0-1)"
    )
    trusted_sources: List[str] = Field(
        default_factory=lambda: os.getenv(
            "TRUSTED_SOURCES",
            "조선일보,중앙일보,동아일보,한국경제,매일경제"
        ).split(","),
        description="List of trusted news sources"
    )


class ClassificationConfig(BaseModel):
    """AI classification configuration"""

    api_key: str = Field(
        default=os.getenv("ANTHROPIC_API_KEY", ""),
        description="Anthropic API key"
    )
    model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Claude model to use"
    )
    max_tokens: int = Field(
        default=1000,
        description="Maximum tokens for response"
    )
    temperature: float = Field(
        default=0.0,
        description="Temperature for generation"
    )


class ProcessingConfig(BaseModel):
    """Processing pipeline configuration"""

    batch_size: int = Field(
        default=int(os.getenv("PROCESS_BATCH_SIZE", "100")),
        description="Batch size for processing"
    )
    max_workers: int = Field(
        default=int(os.getenv("MAX_WORKERS", "4")),
        description="Maximum worker threads"
    )


class DatabaseConfig(BaseModel):
    """Database configuration"""

    url: str = Field(
        default=os.getenv("DATABASE_URL", "sqlite:///./aide_dev.db"),
        description="Database connection URL"
    )


class Config(BaseModel):
    """Main configuration"""

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    dbscan: DBSCANConfig = Field(default_factory=DBSCANConfig)
    representative: RepresentativeConfig = Field(default_factory=RepresentativeConfig)
    classification: ClassificationConfig = Field(default_factory=ClassificationConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)


# Global config instance
config = Config()


__all__ = [
    "Config",
    "EmbeddingConfig",
    "DBSCANConfig",
    "RepresentativeConfig",
    "ClassificationConfig",
    "ProcessingConfig",
    "DatabaseConfig",
    "config",
]
