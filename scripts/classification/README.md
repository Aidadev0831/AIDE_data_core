# Classification Scripts

AI-based classification and clustering scripts.

## Scripts

### `classify_and_upload.py`

Main classification and upload script with AI and clustering.

**Usage:**

```bash
python scripts/classification/classify_and_upload.py
```

**Process:**
1. Load articles with status='raw'
2. Keyword-based pre-classification
3. AI-based classification (GPT-4o-mini)
4. AI embedding & clustering (OpenAI)
5. Upload to Notion

### `upload_today_headlines.py`

Upload today's headlines to Notion.

**Usage:**

```bash
python scripts/classification/upload_today_headlines.py
```

### `ai_classifier.py`

AI classifier module (GPT-4o-mini).

### `ai_clustering_service.py`

AI-based clustering service.

### `clustering_service.py`

Legacy clustering service.

## Workflow

```
DB (status='raw')
    ↓
classify_and_upload.py
    ├── Keyword classification
    ├── AI classification
    ├── Embedding
    ├── Clustering
    └── Notion upload
    ↓
DB (status='processed') + Notion
```

## Categories

- 정책/규제
- 시장동향
- 분양/청약
- 금융/금리
- 세금/법률
- 건설/부동산
- 해외 부동산
- 인물/칼럼
