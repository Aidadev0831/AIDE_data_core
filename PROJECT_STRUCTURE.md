# AIDE Project Structure

Updated: 2025-10-22

## Overview

AIDE 프로젝트는 뉴스 기사 수집, 전처리, 분류, 업로드를 담당하는 여러 독립적인 모듈로 구성됩니다.

## Project Architecture

```
projects/
├── aide-crawlers/          # Project 1: 크롤링 (Raw Data Collection)
├── aide-preprocessing/     # Project 1.5: 전처리 (Data Cleaning & Deduplication)
├── aide-data-core/         # Core: 데이터 모델 및 DB
├── aide-data-engine/       # Project 3: AI 분류 및 클러스터링
├── aide-data-pipeline/     # Project 2: 파이프라인 오케스트레이션
├── aide-api/               # Project 4: REST API
├── aide-platform/          # Project 5: 플랫폼 UI
└── scripts/                # 실행 스크립트
    ├── crawling/           # 크롤링 스크립트
    ├── preprocessing/      # 전처리 스크립트
    ├── classification/     # 분류 및 업로드 스크립트
    └── utils/              # 유틸리티 스크립트
```

## Module Responsibilities

### 1. aide-crawlers (크롤링)

**책임**: 순수 크롤링만 담당
- Naver News API 호출
- Naver News Section 스크래핑
- 원본 데이터 수집 (JSON 형태)

**출력**: Raw article data (JSON)

**포함 기능**:
- API 인증 및 호출
- HTML 파싱 (구조 분석)
- 페이지네이션
- Rate limiting

**제외 기능**:
- HTML 태그 제거 (전처리로 이동)
- 중복 확인 (전처리로 이동)
- DB 저장 (전처리로 이동)

### 2. aide-preprocessing (전처리)

**책임**: 데이터 정제 및 저장 전 처리
- HTML 태그 및 엔티티 제거
- 언론사 추출 (URL → 한글명)
- 중복 확인 (URL + 제목 98% 유사도)
- content_hash 생성 (SHA-256)
- DB 저장 (status='raw')

**입력**: Raw articles (JSON from crawlers)
**출력**: Cleaned articles in DB (status='raw')

**모듈**:
- `TextCleaner`: HTML 정제
- `SourceExtractor`: 언론사 추출
- `Deduplicator`: 중복 확인
- `HashGenerator`: 해시 생성
- `DBWriter`: DB 저장
- `PreprocessingPipeline`: 전체 파이프라인

### 3. aide-data-core (코어)

**책임**: 공통 데이터 모델 및 DB 관리
- SQLAlchemy 모델 정의
- Database session 관리
- Schema 정의

**모델**:
- `NaverNews`: 네이버 뉴스
- `KDIPolicy`: KDI 정책 보고서
- `CreditRating`: 신용평가 리포트

### 4. aide-data-engine (AI 분류/클러스터링)

**책임**: AI 기반 분류 및 클러스터링
- GPT-4o-mini 기반 카테고리 분류
- OpenAI embeddings 벡터화
- 유사도 기반 클러스터링
- 대표 기사 선정
- DB 업데이트 (status='processed')

**입력**: DB articles (status='raw')
**출력**: DB articles (status='processed')

### 5. aide-api (REST API)

**책임**: HTTP API 제공
- FastAPI 기반 REST API
- 기사 조회/검색
- 분류 결과 조회

### 6. aide-platform (플랫폼 UI)

**책임**: 웹 UI 제공
- Next.js 프론트엔드
- FastAPI 백엔드
- 사용자 인터페이스

## Data Flow

```
┌─────────────────────┐
│  1. Crawling        │
│  aide-crawlers      │
│                     │
│  - API 호출         │
│  - HTML 파싱        │
│  - 원본 데이터 수집  │
└──────────┬──────────┘
           │ Raw JSON
           ↓
┌─────────────────────┐
│  2. Preprocessing   │
│  aide-preprocessing │
│                     │
│  - HTML 태그 제거   │
│  - 언론사 추출      │
│  - 중복 확인        │
│  - Hash 생성        │
│  - DB 저장 (raw)    │
└──────────┬──────────┘
           │ status='raw'
           ↓
┌─────────────────────┐
│  3. Classification  │
│  aide-data-engine   │
│                     │
│  - AI 분류          │
│  - Embedding        │
│  - 클러스터링       │
│  - 대표 기사 선정   │
│  - DB 업데이트      │
└──────────┬──────────┘
           │ status='processed'
           ↓
┌─────────────────────┐
│  4. Upload          │
│  Notion API         │
│                     │
│  - 카테고리별 정리  │
│  - Notion 페이지    │
└─────────────────────┘
```

## Scripts Organization

### scripts/crawling/

크롤링 스크립트

- `simple_crawl.py`: 통합 크롤링 (크롤링 + 전처리)
- `crawl_naver_api.py`: Naver API 크롤러
- `crawl_naver_news_section.py`: 경제>부동산 섹션
- `crawl_paper_headlines.py`: 신문 헤드라인

### scripts/preprocessing/

전처리 스크립트

- `preprocess_news.py`: JSON → DB 전처리

### scripts/classification/

분류 및 업로드

- `classify_and_upload.py`: AI 분류 + Notion 업로드
- `upload_today_headlines.py`: 헤드라인 업로드

### scripts/utils/

유틸리티

- `check_db_only.py`: DB 상태 확인
- `export_db_to_excel.py`: Excel 출력
- `measure_pipeline_timing.py`: 성능 측정

## Execution Examples

### 방법 1: 통합 실행 (기존)

```bash
# 크롤링 + 전처리 + 분류 + 업로드
python scripts/crawling/simple_crawl.py
python scripts/classification/classify_and_upload.py
python scripts/classification/upload_today_headlines.py
```

### 방법 2: 단계별 실행 (새로운 구조)

```bash
# Step 1: 크롤링만 (JSON 출력)
python scripts/crawling/crawl_naver_api.py > raw_articles.json

# Step 2: 전처리 (JSON → DB)
python scripts/preprocessing/preprocess_news.py raw_articles.json --keyword "PF"

# Step 3: 분류 및 업로드
python scripts/classification/classify_and_upload.py
python scripts/classification/upload_today_headlines.py
```

## Key Features

### Separation of Concerns

각 프로젝트는 단일 책임을 가짐:
- **Crawlers**: 데이터 수집만
- **Preprocessing**: 정제 및 저장만
- **Engine**: 분류 및 클러스터링만

### Modularity

독립적인 Python 패키지로 구성:
- 재사용 가능
- 테스트 용이
- 유지보수 편의

### Scalability

각 단계를 독립적으로 스케일 가능:
- 크롤러: 병렬 실행
- 전처리: 배치 처리
- 분류: GPU 가속

## Configuration

### Crawling Keywords (26개)

**부동산 금융 (5)**: PF, 프로젝트 파이낸싱, 프로젝트파이낸싱, 브릿지론, 부동산신탁

**부동산 시장 (5)**: 부동산경매, 공매, 부실채권, NPL, 리츠

**건설 (2)**: 건설사, 시공사

**신탁사 (14)**: 한국토지신탁, 한국자산신탁, 대한토지신탁, 코람코자산신탁, KB부동산신탁, 하나자산신탁, 아시아신탁, 우리자산신탁, 무궁화신탁, 코리아신탁, 교보자산신탁, 대신자산신탁, 신영부동산신탁, 한국투자부동산신탁

### Classification Categories (8개)

- 정책/규제
- 시장동향
- 분양/청약
- 금융/금리
- 세금/법률
- 건설/부동산
- 해외 부동산
- 인물/칼럼

## Performance

### Pipeline Timing (26 keywords, ~1,000-1,500 articles)

- **크롤링**: 30-40초
- **전처리**: 10-20초 (포함된 경우)
- **AI 분류**: 2-3분
- **AI 임베딩 & 클러스터링**: 3-5분
- **Notion 업로드**: 30초-1분

**Total**: ~6-9분

## Development

### Install Dependencies

```bash
# aide-preprocessing
cd aide-preprocessing
poetry install

# aide-crawlers
cd aide-crawlers
poetry install

# aide-data-core
cd aide-data-core
poetry install
```

### Run Tests

```bash
# Each project
cd aide-preprocessing
poetry run pytest

cd aide-crawlers
poetry run pytest
```

## Migration Notes

### From Old Structure

기존 구조에서 새 구조로 변경된 사항:

1. **aide-preprocessing 신규 생성**
   - 전처리 로직을 독립 프로젝트로 분리

2. **scripts 폴더 재구성**
   - `scripts/` → `scripts/crawling/`, `scripts/preprocessing/`, etc.

3. **책임 분리**
   - 크롤러: 전처리 로직 제거
   - 전처리: 독립 모듈로 구현

4. **하위 호환성**
   - `simple_crawl.py` 등 통합 스크립트는 계속 사용 가능
   - 새로운 단계별 실행 방식도 지원

## Future Enhancements

- [ ] 크롤러 병렬화
- [ ] 전처리 배치 최적화
- [ ] 임베딩 캐싱
- [ ] Real-time pipeline
- [ ] Airflow 통합
