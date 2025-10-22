# AIDE Data Engine

**Version**: 0.1.0
**Python**: 3.11+

## Overview

AIDE Data Engine is the data processing pipeline for the AIDE Platform. It transforms raw crawled data into structured, deduplicated, and AI-classified insights.

## Features

- **KR-SBERT Embedding**: Generate semantic embeddings for Korean news articles
- **DBSCAN Clustering**: Identify and group duplicate/similar articles
- **Representative Selection**: Select the most informative article from each cluster
- **AI Classification**: Classify articles into 8 categories using Claude API
- **Batch Processing**: Efficient batch processing with configurable workers

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Fetch Raw Data                                            │
│    → Query naver_news table (status='raw')                   │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Generate Embeddings                                       │
│    → KR-SBERT (jhgan/ko-sroberta-multitask)                 │
│    → Store 768-dim vector in embedding_vector field         │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Deduplicate with DBSCAN                                   │
│    → Cluster similar articles (eps=0.3, min_samples=2)      │
│    → Assign duplicate_cluster_id                            │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Select Representatives                                    │
│    → Score = 50% information + 50% source reliability       │
│    → Mark cluster_representative=True                       │
│    → Set duplicate_count                                    │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. AI Classification (Claude API)                           │
│    → Classify into 8 categories                             │
│    → Extract tags                                           │
│    → Store classification_confidence                        │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Update Status                                             │
│    → Set status='processed'                                  │
│    → Ready for API/Notion sync                              │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL (or SQLite for dev)
- Anthropic API key

### Install Dependencies

```bash
cd projects/aide-data-engine

# Install with Poetry
poetry install

# Activate virtual environment
poetry shell
```

### Environment Setup

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required variables:
```bash
DATABASE_URL=postgresql://aide:aide123@localhost:5432/aide_db
ANTHROPIC_API_KEY=your_api_key_here
```

## Quick Start

### Example: Process Raw News

```python
from aide_data_engine.pipeline import DataProcessor

# Create processor
processor = DataProcessor(
    database_url="postgresql://aide:aide123@localhost:5432/aide_db",
    anthropic_api_key="your_api_key"
)

# Run full pipeline
result = processor.run()
print(f"Processed {result['processed']} articles")
print(f"  Embedded: {result['embedded']}")
print(f"  Deduplicated: {result['deduplicated']}")
print(f"  Classified: {result['classified']}")
```

## Services

### 1. Embedding Service

Generate KR-SBERT embeddings for Korean text:

```python
from aide_data_engine.services import EmbeddingService

service = EmbeddingService(model_name="jhgan/ko-sroberta-multitask")

# Single text
embedding = service.embed("PF 시장 안정화 정책 발표")
# → numpy array (768,)

# Batch texts
texts = ["뉴스 1", "뉴스 2", "뉴스 3"]
embeddings = service.embed_batch(texts, batch_size=32)
# → numpy array (3, 768)
```

### 2. Deduplication Service

Identify duplicate articles using DBSCAN:

```python
from aide_data_engine.services import DeduplicationService

service = DeduplicationService(eps=0.3, min_samples=2)

# Cluster embeddings
embeddings = ...  # numpy array (N, 768)
cluster_ids = service.cluster(embeddings)
# → numpy array (N,) with cluster IDs (-1 for outliers)
```

### 3. Classification Service

Classify articles with Claude API:

```python
from aide_data_engine.services import ClassificationService

service = ClassificationService(api_key="your_api_key")

# Classify single article
result = service.classify(
    title="PF 시장 안정화 정책 발표",
    description="정부가 PF 시장 안정화를 위한 정책을 발표..."
)
# → {"categories": ["정책/규제"], "tags": ["PF", "부동산"], "confidence": 95}
```

### 4. Representative Selection

Select most informative article from cluster:

```python
from aide_data_engine.services import RepresentativeSelector

selector = RepresentativeSelector(
    information_weight=0.5,
    source_reliability_weight=0.5,
    trusted_sources=["조선일보", "중앙일보", "동아일보"]
)

# Select representative
articles = [...]  # List of articles in cluster
representative = selector.select(articles)
```

## Configuration

### KR-SBERT Model

- **Model**: `jhgan/ko-sroberta-multitask`
- **Dimensions**: 768
- **Batch Size**: 32 (configurable)

### DBSCAN Parameters

- **eps**: 0.3 (maximum distance between samples)
- **min_samples**: 2 (minimum cluster size)

### Categories

1. 정책/규제 (Policy/Regulation)
2. 시장동향 (Market Trends)
3. 금융/투자 (Finance/Investment)
4. 부동산개발 (Real Estate Development)
5. 기업/프로젝트 (Corporate/Projects)
6. 법률/소송 (Legal/Litigation)
7. 경제지표 (Economic Indicators)
8. 기타 (Others)

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=aide_data_engine --cov-report=html

# Run specific test file
pytest tests/test_embedding_service.py -v
```

## Development

### Code Formatting

```bash
# Format with black
black aide_data_engine/

# Sort imports
isort aide_data_engine/

# Type check
mypy aide_data_engine/
```

## Project Structure

```
aide-data-engine/
├── aide_data_engine/
│   ├── __init__.py
│   │
│   ├── services/                 # Core services
│   │   ├── __init__.py
│   │   ├── embedding.py          # KR-SBERT embedding
│   │   ├── deduplication.py      # DBSCAN clustering
│   │   ├── classification.py     # Claude AI classification
│   │   └── representative.py     # Representative selection
│   │
│   ├── pipeline/                 # Data pipeline
│   │   ├── __init__.py
│   │   └── processor.py          # Main pipeline orchestrator
│   │
│   ├── config/                   # Configuration
│   │   └── __init__.py
│   │
│   └── utils/                    # Utilities
│       └── __init__.py
│
├── tests/                        # Tests
├── pyproject.toml                # Poetry dependencies
├── .env.example                  # Environment template
└── README.md                     # This file
```

## Dependencies

- **aide-data-core**: Shared models and schemas
- **sentence-transformers**: KR-SBERT embeddings
- **scikit-learn**: DBSCAN clustering
- **anthropic**: Claude API
- **numpy/pandas**: Data processing
- **sqlalchemy**: Database ORM

## Performance

- **Embedding**: ~100 articles/second (batch_size=32)
- **Clustering**: O(n²) with DBSCAN, optimized with batch processing
- **Classification**: ~5 articles/second (Claude API rate limit)

## License

MIT License - see LICENSE file for details

## Related Projects

- [aide-data-core](../aide-data-core) - Shared database library
- [aide-crawlers](../aide-crawlers) - Data collection service
- [aide-api](../aide-api) - REST API server (future)

## Support

- Issues: [GitHub Issues](https://github.com/aide-platform/aide-data-engine/issues)
- Documentation: [docs.aide-platform.com](https://docs.aide-platform.com)

---

**Built with ❤️ by AIDE Team**
