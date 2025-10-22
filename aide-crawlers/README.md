# AIDE Crawlers

**Version**: 0.1.0
**Python**: 3.11+

## Overview

AIDE Crawlers is a data collection service for the AIDE Platform. It provides a flexible framework for crawling news articles, policy documents, and credit rating reports from various sources.

## Features

- **Modular Architecture**: Easy to add new crawlers
- **Sinks Abstraction**: Write to DB, local files, or API
- **Data Pipeline**: Crawl → Parse → Normalize → Deduplicate → Validate → Store
- **Job Logging**: Track execution with `ingest_job_runs` and `ingest_errors`
- **AIDE Data Core Integration**: Uses shared models and schemas

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL (optional, SQLite works for dev)
- Naver API credentials (for Naver crawlers)
- Chrome browser + ChromeDriver (for Selenium-based crawlers)

### Install Dependencies

```bash
cd projects/aide-crawlers

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
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret
```

## Quick Start

### Example 1: Crawl to Local Files

```python
from aide_crawlers.crawlers.naver import NaverNewsAPICrawler
from aide_crawlers.sinks import LocalSink

# Create local sink (saves to JSON files)
sink = LocalSink(output_dir="data", format="json")

# Create crawler
crawler = NaverNewsAPICrawler(
    keywords=["PF", "부동산", "금리"],
    sink=sink
)

# Run crawler
result = crawler.run()
print(f"Saved {result['created']} items to data/")

# Cleanup
crawler.close()
```

### Example 2: Crawl to Database

```python
from aide_crawlers.crawlers.naver import NaverNewsAPICrawler
from aide_crawlers.sinks import DBSink
from aide_data_core.models import NaverNews

# Create DB sink (saves to naver_news table)
sink = DBSink(
    database_url="postgresql://aide:aide123@localhost:5432/aide_db",
    target_table="domain",
    model_class=NaverNews
)

# Create crawler with job logging
crawler = NaverNewsAPICrawler(
    keywords=["PF"],
    sink=sink,
    database_url="postgresql://aide:aide123@localhost:5432/aide_db"
)

# Run crawler
result = crawler.run()
print(f"Created {result['created']}, Duplicates {result['duplicates']}")

# Cleanup
crawler.close()
```

### Example 3: Using Context Manager

```python
from aide_crawlers.crawlers.naver import NaverNewsAPICrawler
from aide_crawlers.sinks import LocalSink

with LocalSink(output_dir="data") as sink:
    with NaverNewsAPICrawler(keywords=["금리"], sink=sink) as crawler:
        result = crawler.run()
        print(result)
```

## Architecture

### Data Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Crawl                                                     │
│    → Fetch raw data from source (API, web scraping, etc.)   │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Parse                                                     │
│    → Convert to standardized format                          │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Normalize                                                 │
│    → normalize_url(), normalize_date(), normalize_source()  │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Deduplicate                                               │
│    → Remove duplicates by URL + content hash                │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Validate                                                  │
│    → Check required fields, URL format, text length         │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Write to Sink                                             │
│    → DBSink / LocalSink / APISink (future)                  │
└─────────────────────────────────────────────────────────────┘
```

### Sinks

**AbstractSink**: Base interface for all sinks

**DBSink**: Database direct storage
- Supports PostgreSQL (with upsert) and SQLite (with merge)
- Target: `staging_raw_items` or domain tables (`naver_news`, etc.)
- Handles duplicates with `ON CONFLICT` (PostgreSQL)

**LocalSink**: Local file storage
- Formats: JSON or CSV
- Timestamped filenames: `source_YYYYMMDD_HHMMSS.json`
- Useful for backups and debugging

**APISink**: REST API transmission (planned for Project 4)

## Project Structure

```
aide-crawlers/
├── aide_crawlers/
│   ├── __init__.py
│   │
│   ├── crawlers/                  # Crawler implementations
│   │   ├── base/
│   │   │   └── base_crawler.py   # Abstract base class
│   │   ├── naver/
│   │   │   └── news_api.py       # Naver News API crawler
│   │   ├── research/
│   │   │   └── kdi_policy.py     # KDI policy crawler
│   │   └── credit_rating/
│   │       ├── kisrating.py      # KIS Rating crawler
│   │       └── korearatings.py   # Korea Ratings crawler
│   │
│   ├── sinks/                     # Sink implementations
│   │   ├── abstract.py           # AbstractSink + SinkResult
│   │   ├── db_sink.py            # Database sink
│   │   └── local_sink.py         # Local file sink
│   │
│   ├── utils/                     # Utilities
│   │   ├── logger.py             # Logging setup
│   │   ├── normalize.py          # Data normalization
│   │   ├── dedup.py              # Deduplication
│   │   └── validation.py         # Data validation
│   │
│   ├── config/                    # Configuration files
│   └── tests/                     # Tests
│
├── examples/                      # Usage examples
│   ├── example_kdi_crawler.py    # KDI crawler examples
│   └── example_credit_rating_crawler.py  # Credit rating examples
│
├── pyproject.toml                 # Poetry dependencies
├── .env.example                   # Environment template
└── README.md                      # This file
```

## Creating Custom Crawlers

### Step 1: Subclass BaseCrawler

```python
from aide_crawlers.crawlers.base import BaseCrawler
from typing import List, Dict, Any, Optional

class MyCrawler(BaseCrawler):
    def __init__(self, sink, **kwargs):
        super().__init__(
            source_name="my_crawler",
            sink=sink
        )
        # Your initialization

    def crawl(self) -> List[Dict[str, Any]]:
        """Fetch raw data"""
        # Your crawling logic
        return [
            {"title": "Article 1", "url": "https://..."},
            {"title": "Article 2", "url": "https://..."},
        ]

    def parse(self, raw_item: Dict) -> Optional[Dict]:
        """Parse raw data"""
        return {
            'title': raw_item['title'],
            'url': raw_item['url'],
            'date': '2025-10-20T12:00:00Z',
            'source': 'My Source',
            'description': raw_item.get('summary', ''),
        }
```

### Step 2: Use Your Crawler

```python
from aide_crawlers.sinks import LocalSink

with LocalSink() as sink:
    with MyCrawler(sink=sink) as crawler:
        result = crawler.run()
```

## Utilities

### Normalization

```python
from aide_crawlers.utils import normalize_url, normalize_date, normalize_source

# URL normalization
url = normalize_url("https://example.com/page?utm_source=fb#comment")
# → "https://example.com/page"

# Date normalization
date = normalize_date("10분 전")
# → "2025-10-20T07:50:00+00:00"

# Source normalization
source = normalize_source("조선일보 신문")
# → "조선일보"
```

### Deduplication

```python
from aide_crawlers.utils import generate_dedup_key, deduplicate_items

# Generate dedup key
key = generate_dedup_key(url="https://example.com", title="Test")
# → "https://example.com"

# Deduplicate list
items = [...]
unique = deduplicate_items(items)
```

### Validation

```python
from aide_crawlers.utils import validate_news_item, validate_and_clean_item

item = {
    'title': 'Test News',
    'url': 'https://example.com',
    'date': '2025-10-20T12:00:00Z',
    'source': 'Test'
}

is_valid, errors = validate_news_item(item)
# → (True, [])

cleaned = validate_and_clean_item(item)
# → {...}  # Cleaned and validated
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=aide_crawlers --cov-report=html

# Run specific test file
pytest tests/test_sinks/test_local_sink.py -v
```

## Development

### Code Formatting

```bash
# Format with black
black aide_crawlers/

# Sort imports
isort aide_crawlers/

# Type check
mypy aide_crawlers/
```

## Available Crawlers

### Naver News API
- **Source**: Naver Search API
- **Class**: `NaverNewsAPICrawler`
- **Keywords**: Supports multiple keywords
- **Limit**: 100 results per keyword
- **Requirements**: Naver API credentials

### KDI Policy Documents
- **Source**: Korea Development Institute (KDI)
- **Class**: `KDIPolicyCrawler`
- **URL**: https://www.kdi.re.kr/research/subjects_list.jsp
- **Content**: Economic policy reports, research papers
- **Technology**: Selenium (JavaScript-rendered content)
- **Features**:
  - Date filtering (last N days)
  - Configurable max pages
  - Automatic PDF file detection

**Example**:
```python
from aide_crawlers.crawlers.research import KDIPolicyCrawler
from aide_crawlers.sinks import LocalSink

with LocalSink(output_dir="data/kdi") as sink:
    with KDIPolicyCrawler(sink=sink, headless=True, max_pages=3, days_back=30) as crawler:
        result = crawler.run()
        print(f"Created {result['created']} KDI policy documents")
```

### KIS Rating Research
- **Source**: Korea Investors Service (KIS Rating)
- **Class**: `KISRatingCrawler`
- **URL**: https://www.kisrating.com/research/research_list.do
- **Content**: Credit rating research reports
- **Technology**: Selenium
- **Features**:
  - Category classification
  - Author tracking
  - Date filtering

**Example**:
```python
from aide_crawlers.crawlers.credit_rating import KISRatingCrawler
from aide_crawlers.sinks import LocalSink

with LocalSink(output_dir="data/kisrating") as sink:
    with KISRatingCrawler(sink=sink, headless=True, max_pages=5) as crawler:
        result = crawler.run()
```

### Korea Ratings Research
- **Source**: Korea Ratings Corporation
- **Class**: `KoreaRatingsCrawler`
- **URL**: https://www.korearatings.com/research/research_list.do
- **Content**: Credit rating research reports
- **Technology**: Selenium
- **Features**:
  - Author metadata
  - Date filtering
  - Deduplication

**Example**:
```python
from aide_crawlers.crawlers.credit_rating import KoreaRatingsCrawler
from aide_crawlers.sinks import DBSink
from aide_data_core.models import NaverNews

with DBSink(database_url="sqlite:///./aide.db", target_table="domain", model_class=NaverNews) as sink:
    with KoreaRatingsCrawler(sink=sink, headless=True, max_pages=5) as crawler:
        result = crawler.run()
```

### Future Crawlers

- Naver News Section (부동산 섹션 크롤링)
- Research Reports (KB, Hana, KRIHS, KAMCO)

## Dependencies

- **aide-data-core**: Shared models and schemas
- **httpx/requests**: HTTP clients
- **beautifulsoup4**: HTML parsing
- **selenium**: Browser automation
- **pydantic**: Data validation
- **sqlalchemy**: Database ORM

## License

MIT License - see LICENSE file for details

## Related Projects

- [aide-data-core](../aide-data-core) - Shared database library
- [aide-api](../aide-api) - REST API server (future)
- [aide-data-engine](../aide-data-engine) - Data processing service (future)

## Support

- Issues: [GitHub Issues](https://github.com/aide-platform/aide-crawlers/issues)
- Documentation: [docs.aide-platform.com](https://docs.aide-platform.com)

---

**Built with ❤️ by AIDE Team**
