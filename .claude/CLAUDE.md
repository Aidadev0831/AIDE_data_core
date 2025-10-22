# AIDE Data Core Project

## 프로젝트 개요
AIDE 데이터 파이프라인은 뉴스, 신용평가, 연구 자료 등을 수집하고 처리하는 통합 데이터 시스템입니다.

## 프로젝트 구조

### 주요 모듈
- **aide-api**: FastAPI 기반 REST API 서버 (뉴스, 신용평가, KDI 데이터 제공)
- **aide-crawlers**: 크롤러 모듈 (네이버 뉴스, KisRating, KoreaRatings, KDI)
- **aide-data-engine**: 데이터 처리 엔진 (분류, 중복제거, 임베딩, 대표선정)
- **aide-data-pipeline**: 파이프라인 오케스트레이션
- **aide-preprocessing**: 데이터 전처리 (해시생성, 텍스트정제, 중복제거)
- **scripts**: 실행 스크립트 (크롤링, 전처리, 분류, 유틸리티)

### 의존성 관리
- Python 3.8+ 필요
- Poetry를 사용한 의존성 관리 (각 모듈별 pyproject.toml)
- 환경변수는 `.env` 파일에서 관리 (민감정보는 Git에서 제외)

## 자주 사용하는 명령어

### 테스트 실행
```bash
# API 테스트
cd aide-api && poetry run pytest

# 크롤러 테스트
cd aide-crawlers && poetry run pytest
```

### 데이터베이스
- PostgreSQL 사용
- 연결 테스트: `python test_db_connection.py`

### 크롤링 실행
```bash
# 네이버 뉴스 크롤링
python scripts/crawling/crawl_naver_news_bulk.py

# KDI 정책 크롤링
python aide-crawlers/examples/example_kdi_crawler.py

# 신용평가 크롤링
python aide-crawlers/examples/example_credit_rating_crawler.py
```

### 데이터 처리
```bash
# 뉴스 전처리
python scripts/preprocessing/preprocess_news.py

# 분류 및 업로드
python scripts/classification/classify_and_upload.py

# 오늘의 헤드라인 업로드
python scripts/classification/upload_today_headlines.py
```

### 유틸리티
```bash
# DB 확인 및 정리
python scripts/utils/check_and_clear_db.py

# DB를 Excel로 내보내기
python scripts/utils/export_db_to_excel.py

# 분류 검증
python scripts/utils/verify_classification.py
```

## 코드 스타일

### Python 코딩 규칙
- PEP 8 준수
- Type hints 사용 권장
- Docstring은 Google 스타일
- 클래스명: PascalCase
- 함수/변수명: snake_case

### 파일 구조 패턴
```
module_name/
├── __init__.py
├── config/
├── [domain]/
│   ├── __init__.py
│   └── implementation.py
├── tests/
└── pyproject.toml
```

## 보안 및 주의사항

### 민감 정보
- API 키, DB 비밀번호는 `.env` 파일에 저장
- `.env` 파일은 절대 커밋하지 않음
- `.env.example` 파일로 필요한 환경변수 문서화

### Git 워크플로우
- main/master 브랜치는 프로덕션 코드
- 기능 개발은 feature 브랜치에서 진행
- 커밋 메시지는 한글 또는 영어로 명확하게 작성

## 데이터 파이프라인 플로우

1. **수집 (Crawling)**: aide-crawlers로 원본 데이터 수집
2. **전처리 (Preprocessing)**: aide-preprocessing으로 데이터 정제
3. **처리 (Processing)**: aide-data-engine으로 분류/임베딩
4. **저장**: PostgreSQL에 저장
5. **제공**: aide-api를 통해 REST API로 제공

## 환경 설정

### 필수 환경변수
- `DATABASE_URL`: PostgreSQL 연결 문자열
- `NAVER_CLIENT_ID`: 네이버 API 클라이언트 ID
- `NAVER_CLIENT_SECRET`: 네이버 API 클라이언트 시크릿
- `OPENAI_API_KEY`: OpenAI API 키 (분류/임베딩용)

### Poetry 환경 설정
각 모듈별로 독립적인 Poetry 환경:
```bash
cd [module-name]
poetry install
poetry shell
```
