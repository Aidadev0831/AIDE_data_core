# AIDE Preprocessing

Data preprocessing module for AIDE news articles.

## Overview

This module handles preprocessing of news articles collected by crawlers:

1. **Text Cleaning**: Remove HTML tags and entities
2. **Source Extraction**: Extract media source from URLs
3. **Deduplication**: Check for duplicate articles (URL + title similarity)
4. **Hash Generation**: Generate SHA-256 content hash
5. **Database Storage**: Save preprocessed articles to database

## Architecture

```
Raw Articles (from crawlers)
    ↓
TextCleaner → Remove HTML tags
    ↓
SourceExtractor → Extract media source
    ↓
HashGenerator → Generate content hash
    ↓
Deduplicator → Check duplicates
    ↓
DBWriter → Save to database
```

## Modules

### Processors

- **TextCleaner**: HTML tag and entity removal
- **SourceExtractor**: Media source extraction from URLs
- **HashGenerator**: SHA-256 content hash generation
- **Deduplicator**: Duplicate detection (URL + 98% title similarity)

### Storage

- **DBWriter**: Database write operations

### Pipeline

- **PreprocessingPipeline**: Complete preprocessing workflow

## Installation

```bash
poetry install
```

## Usage

### Basic Usage

```python
from aide_preprocessing import PreprocessingPipeline
from aide_data_core.database import get_session
from aide_data_core.models import NaverNews

# Initialize pipeline
session = get_session()
pipeline = PreprocessingPipeline(session)

# Process raw articles
raw_articles = [
    {
        "title": "<b>PF</b> 대출 &quot;위기&quot;",
        "description": "...",
        "url": "https://www.chosun.com/...",
        "pubDate": "Wed, 16 Oct 2024 18:30:00 +0900"
    },
    ...
]

# Preprocess and save
total, saved, duplicates = pipeline.process_and_save(
    raw_articles,
    keyword="PF",
    model_class=NaverNews
)

print(f"Saved {saved}/{total} articles ({duplicates} duplicates)")
pipeline.close()
```

### Individual Processors

```python
from aide_preprocessing.processors import TextCleaner, SourceExtractor

# Clean text
title = TextCleaner.clean("<b>PF</b> 대출 &quot;위기&quot;")
# → "PF 대출 \"위기\""

# Extract source
source = SourceExtractor.extract("https://www.chosun.com/...")
# → "조선일보"
```

## Deduplication Logic

### URL-based
- Exact URL match

### Title-based
- 98% similarity threshold using SequenceMatcher
- Only checks against today's articles for performance

## Project Structure

```
aide-preprocessing/
├── pyproject.toml
├── README.md
├── .env.example
├── .gitignore
├── aide_preprocessing/
│   ├── __init__.py
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── text_cleaner.py
│   │   ├── source_extractor.py
│   │   ├── deduplicator.py
│   │   └── hash_generator.py
│   ├── storage/
│   │   ├── __init__.py
│   │   └── db_writer.py
│   └── pipeline.py
└── tests/
    ├── __init__.py
    └── test_processors/
```

## Integration with AIDE Pipeline

```
[1. Crawling] aide-crawlers
    ↓ (Raw JSON data)
[2. Preprocessing] aide-preprocessing ← THIS MODULE
    ↓ (Cleaned data, saved to DB as 'raw')
[3. Classification] aide-data-engine
    ↓ (Processed data, status='processed')
[4. Upload] Notion
```

## Development

```bash
# Install dev dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Format code
poetry run black .
poetry run isort .

# Lint
poetry run flake8
```

## License

Private - AIDE Project
