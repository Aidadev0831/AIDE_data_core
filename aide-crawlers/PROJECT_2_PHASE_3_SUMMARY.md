# AIDE Crawlers - Phase 3: Additional Crawlers

**Date**: 2025-10-20
**Status**: ✅ Completed
**Duration**: Phase 3 Implementation

## Overview

Phase 3 adds three production-ready Selenium-based crawlers for research institutions and credit rating agencies to the AIDE Crawlers framework.

## Implemented Crawlers

### 1. KDI Policy Crawler
**Source**: Korea Development Institute (KDI)
**URL**: https://www.kdi.re.kr/research/subjects_list.jsp
**File**: `aide_crawlers/crawlers/research/kdi_policy.py`

**Features**:
- Selenium-based JavaScript content handling
- Date filtering (configurable days_back parameter)
- Multi-page crawling with early stopping
- PDF file detection
- List-based layout extraction (`.list_thesis li`)

**Configuration**:
```python
KDIPolicyCrawler(
    sink=sink,
    headless=True,
    max_pages=2,        # Max pages to crawl
    days_back=30,       # Only fetch last 30 days
    database_url=None   # Optional for job logging
)
```

**Data Fields**:
- `title`: Policy document title
- `url`: Document detail page URL
- `date`: Publication date (ISO 8601)
- `source`: "KDI"
- `description`: Document metadata
- `keyword`: "정책연구"

### 2. KIS Rating Crawler
**Source**: Korea Investors Service (KIS Rating)
**URL**: https://www.kisrating.com/research/research_list.do
**File**: `aide_crawlers/crawlers/credit_rating/kisrating.py`

**Features**:
- Table-based extraction (4-column layout)
- Category classification
- Author metadata tracking
- Date filtering (7 days default)
- Duplicate detection

**Configuration**:
```python
KISRatingCrawler(
    sink=sink,
    headless=True,
    max_pages=3,
    days_back=7,
    database_url=None
)
```

**Data Fields**:
- `title`: Research report title
- `url`: Report detail URL
- `date`: Publication date
- `source`: "KIS Rating"
- `description`: "Category: {category}, Author: {author}"
- `keyword`: "리서치"

### 3. Korea Ratings Crawler
**Source**: Korea Ratings Corporation
**URL**: https://www.korearatings.com/research/research_list.do
**File**: `aide_crawlers/crawlers/credit_rating/korearatings.py`

**Features**:
- Table-based extraction (3-column layout)
- Author metadata
- Date filtering (7 days default)
- Simplified data structure

**Configuration**:
```python
KoreaRatingsCrawler(
    sink=sink,
    headless=True,
    max_pages=3,
    days_back=7,
    database_url=None
)
```

**Data Fields**:
- `title`: Research report title
- `url`: Report detail URL
- `date`: Publication date
- `source`: "Korea Ratings"
- `description`: "Author: {author}"
- `keyword`: "리서치"

## Module Structure

### Updated Modules

**aide_crawlers/crawlers/research/__init__.py**:
```python
from .kdi_policy import KDIPolicyCrawler
__all__ = ["KDIPolicyCrawler"]
```

**aide_crawlers/crawlers/credit_rating/__init__.py**:
```python
from .kisrating import KISRatingCrawler
from .korearatings import KoreaRatingsCrawler
__all__ = ["KISRatingCrawler", "KoreaRatingsCrawler"]
```

## Usage Examples

### Example 1: KDI Crawler with Local Sink
```python
from aide_crawlers.crawlers.research import KDIPolicyCrawler
from aide_crawlers.sinks import LocalSink

with LocalSink(output_dir="data/kdi") as sink:
    with KDIPolicyCrawler(sink=sink, headless=True, max_pages=3, days_back=30) as crawler:
        result = crawler.run()
        print(f"Created {result['created']} KDI policy documents")
```

### Example 2: Credit Rating Crawlers Combined
```python
from aide_crawlers.crawlers.credit_rating import KISRatingCrawler, KoreaRatingsCrawler
from aide_crawlers.sinks import LocalSink

all_results = {'created': 0, 'duplicates': 0, 'failed': 0}

# Crawl KIS Rating
with LocalSink(output_dir="data/credit_rating") as sink:
    with KISRatingCrawler(sink=sink, headless=True, max_pages=2) as crawler:
        result = crawler.run()
        all_results['created'] += result['created']
        all_results['duplicates'] += result['duplicates']

# Crawl Korea Ratings
with LocalSink(output_dir="data/credit_rating") as sink:
    with KoreaRatingsCrawler(sink=sink, headless=True, max_pages=2) as crawler:
        result = crawler.run()
        all_results['created'] += result['created']
        all_results['duplicates'] += result['duplicates']

print(f"Total: {all_results['created']} reports from 2 agencies")
```

### Example 3: Database Sink with Job Logging
```python
from aide_crawlers.crawlers.research import KDIPolicyCrawler
from aide_crawlers.sinks import DBSink
from aide_data_core.models import NaverNews  # TODO: Use KDIPolicy model

sink = DBSink(
    database_url="sqlite:///./aide_dev.db",
    target_table="domain",
    model_class=NaverNews  # Temporary placeholder
)

crawler = KDIPolicyCrawler(
    sink=sink,
    headless=True,
    max_pages=2,
    days_back=30,
    database_url="sqlite:///./aide_dev.db"  # Enable job logging
)

result = crawler.run()
crawler.close()
```

## Example Files

**examples/example_kdi_crawler.py**:
- Local sink example
- Database sink example
- Context manager example

**examples/example_credit_rating_crawler.py**:
- KIS Rating individual example
- Korea Ratings individual example
- Combined crawling example

## Technical Implementation

### Selenium Integration

All three crawlers use Selenium WebDriver with Chrome:

```python
def _init_driver(self):
    chrome_options = Options()
    if self.headless:
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')

    self.driver = webdriver.Chrome(options=chrome_options)
```

### Date Filtering Pattern

```python
def crawl(self) -> List[Dict[str, Any]]:
    self._init_driver()
    all_items = []
    cutoff_date = datetime.now() - timedelta(days=self.days_back)

    for page in range(1, self.max_pages + 1):
        items = self._crawl_page(page)
        recent_items = [
            item for item in items
            if self._parse_date(item.get('date', '')) >= cutoff_date
        ]
        all_items.extend(recent_items)

        # Early stopping
        if len(recent_items) == 0:
            self.logger.info("No recent items, stopping")
            break

    return all_items
```

### Resource Cleanup

```python
def close(self):
    if self.driver:
        self.driver.quit()
        self.logger.info("Selenium driver closed")

    super().close()
```

## Documentation Updates

**README.md** updated with:
1. **Prerequisites**: Added Chrome browser + ChromeDriver requirement
2. **Available Crawlers**: Added three new crawler sections with examples
3. **Project Structure**: Updated to show implemented files
4. **Examples Directory**: Added examples/ section

## Dependencies

**New dependencies required**:
- `selenium`: Browser automation (already in pyproject.toml)
- Chrome browser + ChromeDriver

**Existing dependencies used**:
- `aide-data-core`: Models and schemas
- `sqlalchemy`: Database operations
- `beautifulsoup4`: HTML parsing (future use)

## Current Limitations & TODOs

1. **Schema Placeholders**: Currently using `NaverNewsCreate` as temporary schema
   - TODO: Create `KDIPolicyCreate` schema in aide-data-core
   - TODO: Create `CreditRatingCreate` schema in aide-data-core

2. **Model Placeholders**: Using `NaverNews` model for storage
   - TODO: Create `KDIPolicy` model in aide-data-core
   - TODO: Create `CreditRating` model in aide-data-core

3. **Content Extraction**: Currently fetching metadata only
   - Future: Extract full report content (PDF parsing)
   - Future: Extract structured data from reports

## Testing Status

**Manual Testing**: ✅ All crawlers tested successfully
- KDI crawler: List-based extraction works
- KIS Rating crawler: 4-column table extraction works
- Korea Ratings crawler: 3-column table extraction works

**Unit Tests**: ⏳ Not yet created
- TODO: Create unit tests for each crawler
- TODO: Create integration tests with LocalSink
- TODO: Mock Selenium driver for faster tests

## Integration with AIDE Platform

These crawlers integrate seamlessly with:

1. **AIDE Data Core**: Uses shared models (temporarily NaverNews)
2. **Sinks System**: Works with DBSink, LocalSink, APISink (future)
3. **Job Logging**: Automatic logging via `IngestJobRun` and `IngestError`
4. **Deduplication**: URL + content_hash based dedup via BaseCrawler

## Statistics

**Total Crawlers**: 4
- Naver News API (existing)
- KDI Policy (new)
- KIS Rating (new)
- Korea Ratings (new)

**Total Lines of Code (Phase 3)**:
- kdi_policy.py: ~270 lines
- kisrating.py: ~290 lines
- korearatings.py: ~283 lines
- example_kdi_crawler.py: ~97 lines
- example_credit_rating_crawler.py: ~88 lines
- **Total**: ~1,028 lines

## Next Steps

### Immediate Next Steps (Phase 4):
1. Create dedicated models in aide-data-core:
   - `KDIPolicy` model
   - `CreditRating` model
2. Create dedicated schemas:
   - `KDIPolicyCreate/Update/Response`
   - `CreditRatingCreate/Update/Response`
3. Update crawlers to use proper models/schemas

### Future Enhancements:
1. Add more credit rating agencies (NICE, KMRI)
2. Implement PDF content extraction
3. Add structured data parsing from reports
4. Create scheduler for automated crawling
5. Add Notion sync integration

## Phase 3 Completion Summary

✅ **Completed Tasks**:
- [x] KDI Policy Crawler implementation
- [x] KIS Rating Crawler implementation
- [x] Korea Ratings Crawler implementation
- [x] Module exports updated
- [x] Usage examples created
- [x] Documentation updated

📊 **Impact**:
- Expanded from 1 to 4 crawlers (4x increase)
- Added research institution coverage
- Added credit rating agency coverage
- Established Selenium-based crawling pattern

🎯 **Ready for**:
- Production deployment
- Integration with AIDE Data Engine (Project 3)
- Scheduled automated crawling
- Notion synchronization

---

**Phase 3 Status**: ✅ Complete
**Next Phase**: Phase 4 - Model & Schema Creation in aide-data-core
