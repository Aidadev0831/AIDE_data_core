# Utility Scripts

Utility and management scripts.

## Scripts

### `check_db_only.py`

Check database status (read-only).

**Usage:**

```bash
python scripts/utils/check_db_only.py
```

**Output:** Statistics on articles by status, keyword, source, date.

### `export_db_to_excel.py`

Export database to Excel file.

**Usage:**

```bash
python scripts/utils/export_db_to_excel.py
```

**Output:** `naver_news_export_YYYYMMDD_HHMMSS.xlsx`

**Sheets:**
- 전체기사
- 미분류 (status='raw')
- 분류완료 (status='processed')
- 키워드별 (top 10 keywords)

### `check_and_clear_db.py`

Check and optionally clear database (interactive).

**Usage:**

```bash
python scripts/utils/check_and_clear_db.py
```

⚠️ **Warning:** Can delete all articles. Use with caution.

### `measure_pipeline_timing.py`

Measure pipeline timing for performance analysis.

**Usage:**

```bash
python scripts/utils/measure_pipeline_timing.py
```

### `verify_classification.py`

Verify classification accuracy.

**Usage:**

```bash
python scripts/utils/verify_classification.py
```

### `scheduler.py`

Scheduler for automated pipeline execution.

**Usage:**

```bash
python scripts/utils/scheduler.py
```
