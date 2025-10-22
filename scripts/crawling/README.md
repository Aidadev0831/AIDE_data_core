# Crawling Scripts

Pure crawling scripts that collect raw news articles.

## Scripts

### `simple_crawl.py`

Simple Naver News API crawler with integrated preprocessing.

**Usage:**

```bash
python scripts/crawling/simple_crawl.py
```

**Output:** Crawls 26 keywords, preprocesses, and saves to DB.

### `crawl_naver_api.py`

Naver News API crawler (today's articles only).

**Usage:**

```bash
python scripts/crawling/crawl_naver_api.py
```

### `crawl_naver_news_section.py`

Crawls Naver News "경제 > 부동산" section.

**Usage:**

```bash
python scripts/crawling/crawl_naver_news_section.py
```

**Keyword:** `'경제>부동산'`

### `crawl_paper_headlines.py`

Crawls newspaper headline pages.

**Usage:**

```bash
python scripts/crawling/crawl_paper_headlines.py
```

## Keywords (26)

### 부동산 금융 (5개)
- PF
- 프로젝트 파이낸싱
- 프로젝트파이낸싱
- 브릿지론
- 부동산신탁

### 부동산 시장 (5개)
- 부동산경매
- 공매
- 부실채권
- NPL
- 리츠

### 건설 (2개)
- 건설사
- 시공사

### 신탁사 (14개)
- 한국토지신탁, 한국자산신탁, 대한토지신탁, 코람코자산신탁
- KB부동산신탁, 하나자산신탁, 아시아신탁, 우리자산신탁
- 무궁화신탁, 코리아신탁, 교보자산신탁, 대신자산신탁
- 신영부동산신탁, 한국투자부동산신탁

## Next Steps

After crawling, run preprocessing (if using raw output):

```bash
python scripts/preprocessing/preprocess_news.py raw_articles.json --keyword "PF"
```

Or use integrated scripts like `simple_crawl.py` that handle both.
