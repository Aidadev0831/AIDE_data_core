# Preprocessing Scripts

Data preprocessing scripts for news articles.

## Scripts

### `preprocess_news.py`

Preprocesses raw articles from JSON and saves to database.

**Usage:**

```bash
# From JSON file
python scripts/preprocessing/preprocess_news.py raw_articles.json --keyword "PF"
```

**Input:** JSON file with raw articles from crawler
**Output:** Preprocessed articles saved to DB with status='raw'

## Workflow

```
Raw Articles (JSON)
    ↓
preprocess_news.py
    ├── Clean HTML tags
    ├── Extract source
    ├── Generate hash
    ├── Check duplicates
    └── Save to DB
    ↓
Database (status='raw')
```

## Next Step

After preprocessing, run classification:

```bash
python scripts/classification/classify_and_upload.py
```
