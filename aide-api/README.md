# AIDE API

REST API server for AIDE Platform providing access to processed news articles, KDI policy documents, and credit rating research reports.

## Overview

AIDE API is a FastAPI-based REST API service that serves as the data access layer for the AIDE Platform. It provides endpoints for querying and retrieving:

- **News Articles**: Processed news from Naver with AI classification and deduplication
- **KDI Policies**: Policy documents and research from Korea Development Institute
- **Credit Ratings**: Research reports from KIS Rating, Korea Ratings, and other agencies

## Features

- **RESTful API Design**: Clean, intuitive endpoints following REST principles
- **Automatic Documentation**: Interactive API docs with Swagger UI and ReDoc
- **Filtering & Pagination**: Flexible query parameters for all list endpoints
- **Full-text Search**: Search across titles and descriptions
- **Statistics Endpoints**: Aggregated data by categories, sources, and agencies
- **CORS Support**: Configurable cross-origin resource sharing
- **Database Integration**: SQLAlchemy ORM with PostgreSQL/SQLite support
- **Type Safety**: Pydantic validation for all requests and responses

## Architecture

```
aide-api/
├── aide_api/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config/              # Configuration management
│   │   └── __init__.py      # Pydantic settings
│   ├── dependencies/        # FastAPI dependencies
│   │   ├── __init__.py
│   │   └── database.py      # Database session injection
│   └── routers/             # API route handlers
│       ├── __init__.py
│       ├── news.py          # News endpoints
│       ├── kdi.py           # KDI policy endpoints
│       └── ratings.py       # Credit rating endpoints
├── .env.example             # Environment variables template
├── pyproject.toml           # Poetry dependencies
└── README.md                # This file
```

## Installation

### Prerequisites

- Python 3.11+
- Poetry (package manager)
- PostgreSQL (production) or SQLite (development)
- `aide-data-core` package installed

### Setup

1. **Clone the repository** (if not already done):
```bash
cd projects/aide-api
```

2. **Install dependencies with Poetry**:
```bash
poetry install
```

3. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Set up the database**:

For development (SQLite):
```bash
# DATABASE_URL will use default sqlite:///./aide_dev.db
```

For production (PostgreSQL):
```bash
# Update .env:
# DATABASE_URL=postgresql://user:password@localhost:5432/aide_db
```

## Configuration

Edit `.env` file to configure the API:

### Database Configuration
```env
DATABASE_URL=postgresql://aide:aide123@localhost:5432/aide_db
# Or use SQLite for development:
# DATABASE_URL=sqlite:///./aide_dev.db
```

### API Configuration
```env
API_TITLE=AIDE API
API_VERSION=0.1.0
API_DESCRIPTION=REST API for AIDE Platform - News, Policies, and Ratings
```

### Server Configuration
```env
HOST=0.0.0.0          # Server host
PORT=8000             # Server port
RELOAD=true           # Auto-reload on code changes (dev only)
```

### CORS Configuration
```env
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
CORS_ALLOW_CREDENTIALS=true
```

### Pagination Settings
```env
DEFAULT_PAGE_SIZE=20  # Default number of items per page
MAX_PAGE_SIZE=100     # Maximum allowed page size
```

## Running the Server

### Development Mode

Run with auto-reload:
```bash
poetry run python -m aide_api.main
```

Or use uvicorn directly:
```bash
poetry run uvicorn aide_api.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
poetry run uvicorn aide_api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI schema: `http://localhost:8000/openapi.json`

## API Endpoints

### Root Endpoints

#### `GET /`
Get API information and available endpoints.

**Response:**
```json
{
  "name": "AIDE API",
  "version": "0.1.0",
  "description": "REST API for AIDE Platform - News, Policies, and Ratings",
  "endpoints": {
    "docs": "/docs",
    "redoc": "/redoc",
    "openapi": "/openapi.json",
    "health": "/health",
    "news": "/news",
    "kdi": "/kdi",
    "ratings": "/ratings"
  }
}
```

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

---

### News Endpoints (`/news`)

#### `GET /news/`
List news articles with optional filters.

**Query Parameters:**
- `skip` (int, default=0): Number of records to skip
- `limit` (int, default=20, max=100): Number of records to return
- `status` (str): Filter by status (raw, processed)
- `keyword` (str): Filter by keyword
- `source` (str): Filter by source
- `category` (str): Filter by classified category
- `representatives_only` (bool, default=false): Only show representative articles from duplicate clusters

**Example:**
```bash
curl "http://localhost:8000/news/?category=정책/규제&representatives_only=true&limit=10"
```

**Response:**
```json
[
  {
    "id": 1,
    "keyword": "PF",
    "title": "정부, PF 대출 규제 강화",
    "source": "한국경제",
    "url": "https://example.com/article1",
    "date": "2025-10-20T12:00:00Z",
    "description": "부동산 프로젝트 파이낸싱 대출 규제가 강화됩니다...",
    "content_hash": "abc123...",
    "status": "processed",
    "duplicate_cluster_id": 5,
    "duplicate_count": 8,
    "cluster_representative": true,
    "classified_categories": "[\"정책/규제\", \"금융/투자\"]",
    "tags": "[\"PF\", \"대출규제\", \"정부정책\"]",
    "classification_confidence": 95,
    "created_at": "2025-10-20T08:00:00Z",
    "updated_at": "2025-10-20T09:30:00Z"
  }
]
```

#### `GET /news/{article_id}`
Get single news article by ID.

**Example:**
```bash
curl "http://localhost:8000/news/123"
```

#### `GET /news/cluster/{cluster_id}`
Get all articles in a duplicate cluster.

**Example:**
```bash
curl "http://localhost:8000/news/cluster/5"
```

**Response:** Array of articles with same `duplicate_cluster_id`

#### `GET /news/search/`
Full-text search across title and description.

**Query Parameters:**
- `q` (str, required): Search query
- `skip` (int, default=0)
- `limit` (int, default=20, max=100)

**Example:**
```bash
curl "http://localhost:8000/news/search/?q=부동산&limit=10"
```

#### `GET /news/categories/stats`
Get statistics by category.

**Response:**
```json
{
  "total_categories": 8,
  "categories": [
    {
      "category": "정책/규제",
      "count": 245
    },
    {
      "category": "시장동향",
      "count": 189
    }
  ]
}
```

#### `GET /news/sources/stats`
Get statistics by source.

**Response:**
```json
{
  "total_sources": 15,
  "sources": [
    {
      "source": "한국경제",
      "count": 312
    },
    {
      "source": "매일경제",
      "count": 289
    }
  ]
}
```

---

### KDI Endpoints (`/kdi`)

#### `GET /kdi/`
List KDI policy documents with optional filters.

**Query Parameters:**
- `skip` (int, default=0)
- `limit` (int, default=20, max=100)
- `status` (str): Filter by status
- `category` (str): Filter by category
- `author` (str): Filter by author

**Example:**
```bash
curl "http://localhost:8000/kdi/?category=경제정책&limit=10"
```

**Response:**
```json
[
  {
    "id": 1,
    "title": "2025년 경제정책 방향",
    "url": "https://kdi.re.kr/policy/12345",
    "date": "2025-10-15T00:00:00Z",
    "source": "KDI",
    "description": "2025년 주요 경제정책 방향에 대한 연구...",
    "keyword": "정책연구",
    "content_hash": "def456...",
    "pdf_url": "https://kdi.re.kr/downloads/12345.pdf",
    "category": "경제정책",
    "author": "홍길동",
    "status": "raw",
    "created_at": "2025-10-15T10:00:00Z",
    "updated_at": "2025-10-15T10:00:00Z"
  }
]
```

#### `GET /kdi/{policy_id}`
Get single KDI policy document by ID.

**Example:**
```bash
curl "http://localhost:8000/kdi/45"
```

#### `GET /kdi/search/`
Full-text search across KDI policies.

**Query Parameters:**
- `q` (str, required): Search query
- `skip` (int, default=0)
- `limit` (int, default=20, max=100)

**Example:**
```bash
curl "http://localhost:8000/kdi/search/?q=부동산정책"
```

#### `GET /kdi/categories/stats`
Get statistics by category.

**Response:**
```json
{
  "total_categories": 12,
  "categories": [
    {
      "category": "경제정책",
      "count": 87
    },
    {
      "category": "재정정책",
      "count": 64
    }
  ]
}
```

---

### Credit Rating Endpoints (`/ratings`)

#### `GET /ratings/`
List credit rating research reports with optional filters.

**Query Parameters:**
- `skip` (int, default=0)
- `limit` (int, default=20, max=100)
- `status` (str): Filter by status
- `agency` (str): Filter by agency (kisrating, korearatings)
- `category` (str): Filter by category
- `author` (str): Filter by author

**Example:**
```bash
curl "http://localhost:8000/ratings/?agency=kisrating&category=부동산&limit=10"
```

**Response:**
```json
[
  {
    "id": 1,
    "title": "2025 부동산 시장 전망",
    "url": "https://kisrating.com/research/12345",
    "date": "2025-10-18T00:00:00Z",
    "source": "KIS Rating",
    "description": "2025년 부동산 시장 전망 및 분석...",
    "keyword": "리서치",
    "content_hash": "ghi789...",
    "category": "부동산",
    "author": "김철수",
    "agency": "kisrating",
    "status": "raw",
    "created_at": "2025-10-18T14:00:00Z",
    "updated_at": "2025-10-18T14:00:00Z"
  }
]
```

#### `GET /ratings/{rating_id}`
Get single credit rating report by ID.

**Example:**
```bash
curl "http://localhost:8000/ratings/67"
```

#### `GET /ratings/search/`
Full-text search across credit rating reports.

**Query Parameters:**
- `q` (str, required): Search query
- `skip` (int, default=0)
- `limit` (int, default=20, max=100)

**Example:**
```bash
curl "http://localhost:8000/ratings/search/?q=PF"
```

#### `GET /ratings/agencies/stats`
Get statistics by agency.

**Response:**
```json
{
  "total_agencies": 2,
  "agencies": [
    {
      "agency": "kisrating",
      "count": 156
    },
    {
      "agency": "korearatings",
      "count": 142
    }
  ]
}
```

#### `GET /ratings/categories/stats`
Get statistics by category.

**Response:**
```json
{
  "total_categories": 8,
  "categories": [
    {
      "category": "부동산",
      "count": 89
    },
    {
      "category": "금융",
      "count": 76
    }
  ]
}
```

## Usage Examples

### Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Get health status
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# Get representative news articles with category filter
params = {
    "category": "정책/규제",
    "representatives_only": True,
    "limit": 10
}
response = requests.get(f"{BASE_URL}/news/", params=params)
articles = response.json()

for article in articles:
    print(f"{article['title']} - {article['source']}")
    print(f"Categories: {article['classified_categories']}")
    print(f"Duplicate count: {article['duplicate_count']}")
    print()

# Search KDI policies
response = requests.get(f"{BASE_URL}/kdi/search/", params={"q": "부동산정책", "limit": 5})
policies = response.json()

# Get credit rating reports from KIS Rating
params = {
    "agency": "kisrating",
    "skip": 0,
    "limit": 20
}
response = requests.get(f"{BASE_URL}/ratings/", params=params)
reports = response.json()
```

### JavaScript/TypeScript Client Example

```typescript
const BASE_URL = "http://localhost:8000";

// Get news with filters
async function getNews() {
  const params = new URLSearchParams({
    category: "시장동향",
    representatives_only: "true",
    limit: "10"
  });

  const response = await fetch(`${BASE_URL}/news/?${params}`);
  const articles = await response.json();
  return articles;
}

// Search function
async function searchNews(query: string) {
  const params = new URLSearchParams({
    q: query,
    limit: "20"
  });

  const response = await fetch(`${BASE_URL}/news/search/?${params}`);
  const results = await response.json();
  return results;
}

// Get category statistics
async function getCategoryStats() {
  const response = await fetch(`${BASE_URL}/news/categories/stats`);
  const stats = await response.json();
  return stats;
}
```

## Response Models

All responses use Pydantic models from `aide-data-core`:

- **NaverNewsResponse**: News article model
- **KDIPolicyResponse**: KDI policy document model
- **CreditRatingResponse**: Credit rating report model

See the interactive API documentation at `/docs` for detailed schema definitions.

## Error Handling

The API uses standard HTTP status codes:

- `200 OK`: Successful request
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

Error responses include a detail message:
```json
{
  "detail": "Rating report not found"
}
```

## Integration with AIDE Platform

This API integrates with other AIDE Platform components:

1. **AIDE Data Core** (`aide-data-core`): Provides database models and schemas
2. **AIDE Crawlers** (`aide-crawlers`): Populates database with raw data
3. **AIDE Data Engine** (`aide-data-engine`): Processes and enriches data
4. **AIDE Platform** (future): Web UI and Notion sync

### Data Flow

```
Crawlers → Database (raw) → Data Engine → Database (processed) → API → Clients
```

## Development

### Code Formatting

```bash
# Format code with Black
poetry run black aide_api/

# Sort imports with isort
poetry run isort aide_api/

# Type checking with mypy
poetry run mypy aide_api/
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=aide_api --cov-report=html

# Run specific test file
poetry run pytest tests/test_news_router.py -v
```

## Deployment

### Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY aide_api ./aide_api

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Expose port
EXPOSE 8000

# Run server
CMD ["uvicorn", "aide_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t aide-api .
docker run -p 8000:8000 --env-file .env aide-api
```

### Production Checklist

- [ ] Set `RELOAD=false` in production
- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure proper CORS origins
- [ ] Set up reverse proxy (nginx/Traefik)
- [ ] Enable HTTPS/TLS
- [ ] Configure logging to file
- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Implement rate limiting
- [ ] Use multiple workers for uvicorn
- [ ] Set up database backups

## Performance Optimization

### Database Optimization

1. **Indexes**: All frequently queried fields are indexed (date, status, category, agency)
2. **Pagination**: Always use `limit` to avoid large result sets
3. **Connection Pooling**: SQLAlchemy handles connection pooling automatically

### API Optimization

1. **Use representatives_only**: Reduces duplicate data by ~70%
2. **Specific filters**: Apply category/source filters to reduce query size
3. **Caching**: Consider adding Redis for frequently accessed endpoints
4. **CDN**: Use CDN for static documentation assets

## Troubleshooting

### Database Connection Issues

```bash
# Check database connection
poetry run python -c "from aide_api.dependencies.database import get_db; print('DB OK')"
```

### Port Already in Use

```bash
# Kill process on port 8000 (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Kill process on port 8000 (Linux/Mac)
lsof -ti:8000 | xargs kill -9
```

### Import Errors

Make sure `aide-data-core` is installed:
```bash
cd ../aide-data-core
poetry install
cd ../aide-api
poetry install
```

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [AIDE Platform Issues](https://github.com/aide-platform/issues)
- Email: team@aide-platform.com

## Version History

### v0.1.0 (2025-10-20)
- Initial release
- News, KDI, and Credit Rating endpoints
- Full-text search functionality
- Statistics endpoints
- Automatic API documentation
- PostgreSQL and SQLite support
