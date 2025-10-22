# AIDE Data Pipeline - Unified Orchestrator

통합 데이터 수집 및 처리 오케스트레이터. 네이버 뉴스, KDI 정책문서, 신용평가사 리서치 등 모든 데이터 소스를 단일 엔트리포인트로 관리합니다.

## 주요 기능

- 🔄 **통합 오케스트레이션**: 모든 크롤러를 단일 명령으로 실행
- ⏰ **스케줄링**: YAML 기반 작업 스케줄 관리
- 📊 **작업 추적**: 실행 로그, 에러 추적, 통계
- 🔌 **CLI 인터페이스**: Typer 기반 사용자 친화적 CLI
- 🎯 **선택적 실행**: 개별 작업 또는 전체 작업 실행

## 설치

```bash
cd projects/aide-data-pipeline
poetry install
```

## 사용법

### 1. 단일 작업 실행

```bash
# Naver 뉴스 수집
python -m aide_pipeline run naver_news

# KDI 정책 문서 수집
python -m aide_pipeline run kdi_policy

# 신용평가 리서치 수집
python -m aide_pipeline run credit_rating
```

### 2. 전체 작업 실행

```bash
# 활성화된 모든 작업 실행
python -m aide_pipeline run all
```

### 3. Dry Run 모드

```bash
# DB 쓰기 없이 테스트
python -m aide_pipeline run naver_news --dry-run
```

### 4. 스케줄러 시작

```bash
# schedule.yaml 기반 자동 실행
python -m aide_pipeline schedule
```

### 5. 작업 상태 확인

```bash
# 최근 10개 작업 실행 상태
python -m aide_pipeline status

# 최근 20개 조회
python -m aide_pipeline status --limit 20

# 특정 작업 필터링
python -m aide_pipeline status --job naver_news
```

## 설정 파일

### config/schedule.yaml

```yaml
global:
  timezone: "Asia/Seoul"
  max_parallel_jobs: 2

jobs:
  naver_news:
    enabled: true
    schedule: "30 8 * * *"  # 매일 8:30
    timeout_minutes: 30
    sources:
      - name: "api_search"
        keywords:
          - "PF"
          - "부동산"
          # ... 26개 키워드

  kdi_policy:
    enabled: true
    schedule: "0 9 * * *"  # 매일 9:00
    filters:
      date_range_days: 7

  credit_rating:
    enabled: true
    schedule: "0 10 * * 1-5"  # 평일 10:00
    agencies:
      - name: "kisrating"
      - name: "korearatings"
```

## 아키텍처

```
aide_pipeline/
├── __init__.py
├── __main__.py           # CLI 엔트리포인트
├── config.py             # 설정 로더
├── orchestrator.py       # 오케스트레이터 로직
└── jobs/                 # 개별 작업 구현

config/
└── schedule.yaml         # 작업 스케줄 정의
```

## 파이프라인 플로우

```
1. Crawling (크롤러 실행)
   ├── Naver News API
   ├── KDI Policy Crawler
   └── Credit Rating Crawler
           │
           ↓
2. Storage (DB 저장)
   └── aide-data-core models
           │
           ↓
3. Processing (데이터 처리)
   ├── Embedding (KR-SBERT)
   ├── Deduplication (DBSCAN)
   ├── Classification (Claude AI)
   └── Representative Selection
           │
           ↓
4. Logging (작업 추적)
   ├── IngestJobRun (실행 로그)
   └── IngestError (에러 추적)
```

## 환경 변수

`.env.development` 또는 `.env.production`에 다음 변수 설정:

```bash
# Database
DATABASE_URL=sqlite:///./aide_dev.db

# API Keys
CLAUDE_API_KEY=sk-ant-api03-...
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...

# Pipeline
PIPELINE_MODE=development
LOGGING_LEVEL=INFO
```

## CLI 명령어

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `run <job>` | 작업 실행 | `run naver_news` |
| `run all` | 전체 작업 실행 | `run all` |
| `run --dry-run` | Dry run 모드 | `run naver_news --dry-run` |
| `schedule` | 스케줄러 시작 | `schedule` |
| `status` | 작업 상태 조회 | `status --limit 20` |
| `status --job <name>` | 특정 작업 필터링 | `status --job naver_news` |

## 작업 추적

모든 작업 실행은 `IngestJobRun` 테이블에 기록됩니다:

```python
IngestJobRun(
    job_name="naver_news",
    started_at=datetime,
    completed_at=datetime,
    status="completed",  # running, completed, failed
    items_collected=150,
    items_processed=120,
    error_message=None,
)
```

에러는 `IngestError` 테이블에 별도 저장:

```python
IngestError(
    job_run_id=123,
    error_type="ValueError",
    error_message="Invalid response",
    traceback="...",
)
```

## 의존성

- **aide-data-core**: 데이터 모델, 스키마
- **aide-crawlers**: 크롤러 구현
- **aide-data-engine**: 데이터 처리 엔진
- **typer**: CLI 프레임워크
- **rich**: 터미널 출력
- **schedule**: 작업 스케줄링
- **pyyaml**: YAML 파싱

## 개발

### 테스트

```bash
poetry run pytest tests/ -v
```

### 새 작업 추가

1. `config/schedule.yaml`에 작업 정의
2. `orchestrator.py`에 크롤러 로직 추가
3. `jobs/` 디렉토리에 작업 구현 (선택)

## 로드맵

- [x] 단일 엔트리포인트 구현
- [x] YAML 기반 설정
- [x] 작업 추적 및 로깅
- [ ] 병렬 실행 지원
- [ ] 재시도 로직 구현
- [ ] 알림 통합 (Slack, Email)
- [ ] Web UI 대시보드

---

**버전**: 0.1.0
**작성자**: AIDE Team
**마지막 업데이트**: 2025-10-20
