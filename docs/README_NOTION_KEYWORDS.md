# 📋 노션 키워드 관리 시스템

## 개요

네이버 뉴스 크롤링 키워드를 노션 데이터베이스에서 관리하고, 크롤러가 실행될 때 자동으로 읽어옵니다.

## 장점

### ✅ 코드 수정 없이 관리
- 노션에서 키워드 추가/삭제/수정
- 코드 변경 및 Git 커밋 불필요

### ✅ 팀 협업 용이
- 노션 공유로 여러 사람이 관리
- 카테고리별 분류 및 우선순위 설정

### ✅ 안전성
- 노션 연결 실패 시 기본 키워드 사용
- 오프라인에서도 작동

## 빠른 시작

### 1. 설치

```bash
pip install -r requirements.txt
```

### 2. 노션 설정

자세한 내용: [`QUICK_START_NOTION.md`](QUICK_START_NOTION.md)

간단 요약:
1. 노션 Integration 생성 (https://www.notion.so/my-integrations)
2. 데이터베이스 생성 및 연결
3. `.env` 파일에 API 키 추가

### 3. 테스트

```bash
python scripts/utils/test_notion_keywords.py
```

### 4. 크롤러 실행

```bash
python scripts/crawling/crawl_naver_api.py
```

## 파일 구조

```
AIDE_data_core/
├── docs/
│   ├── NOTION_SETUP_GUIDE.md       # 자세한 설정 가이드
│   ├── QUICK_START_NOTION.md       # 빠른 시작 (5분)
│   └── README_NOTION_KEYWORDS.md   # 이 파일
├── scripts/
│   ├── utils/
│   │   ├── notion_keywords.py      # 노션 키워드 관리 모듈
│   │   └── test_notion_keywords.py # 연결 테스트
│   └── crawling/
│       ├── crawl_naver_api.py      # 수정됨 (노션 통합)
│       └── crawl_naver_news_bulk.py # 수정됨 (노션 통합)
├── requirements.txt                 # notion-client 포함
└── aide-crawlers/.env.example      # 노션 API 설정 추가
```

## 노션 데이터베이스 구조

| 컬럼 | 타입 | 필수 | 설명 |
|------|------|------|------|
| 키워드 | Title | ✅ | 검색 키워드 (예: "PF") |
| 카테고리 | Select | ❌ | 부동산금융, 부동산시장, 건설, 신탁사 |
| 활성화 | Checkbox | ✅ | 크롤링에 사용할지 여부 |
| 우선순위 | Number | ❌ | 1-10 (높을수록 먼저 크롤링) |
| 메모 | Text | ❌ | 키워드 설명 |

## 사용 방법

### 키워드 추가
1. 노션 데이터베이스에 새 행 추가
2. 키워드 입력
3. 카테고리 선택
4. "활성화" 체크
5. 우선순위 설정 (1-10)

### 키워드 수정
1. 노션에서 해당 행 수정
2. 다음 크롤링부터 자동 반영

### 키워드 비활성화
1. "활성화" 체크 해제
2. 크롤링에서 자동 제외 (삭제 안 함)

### 카테고리별 크롤링 (고급)

특정 카테고리만 크롤링:

```python
from scripts.utils.notion_keywords import NotionKeywordManager

manager = NotionKeywordManager()
keywords = manager.get_keywords(category="부동산금융")
```

## API 레퍼런스

### `NotionKeywordManager`

```python
manager = NotionKeywordManager(
    api_key=None,        # 환경변수에서 자동 로드
    database_id=None     # 환경변수에서 자동 로드
)

# 키워드 목록 가져오기
keywords = manager.get_keywords(
    category=None,           # 특정 카테고리만
    active_only=True,        # 활성화된 것만
    sort_by_priority=True    # 우선순위 정렬
)

# 상세 정보 포함
detailed = manager.get_keywords_detailed()
# Returns: [{'keyword': 'PF', 'category': '부동산금융', 'priority': 10, 'memo': '...'}, ...]

# 연결 테스트
manager.test_connection()  # Returns: True/False
```

### `get_crawler_keywords()` (권장)

```python
from scripts.utils.notion_keywords import get_crawler_keywords

# 노션에서 로드, 실패 시 기본 키워드 사용
keywords = get_crawler_keywords(
    category=None,              # 카테고리 필터
    fallback_to_default=True    # 실패 시 기본 키워드
)
```

## 환경변수

```env
# aide-crawlers/.env
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxx
```

## 폴백 메커니즘

노션 연결 실패 시:
1. 경고 메시지 출력
2. 기본 키워드 리스트 사용 (코드에 하드코딩)
3. 크롤링 계속 진행

```
⚠️  노션 연결 실패: Could not connect...
📋 기본 키워드 사용
✅ 키워드: 26개
```

## 문제 해결

### "notion-client not installed"
```bash
pip install notion-client
```

### "NOTION_API_KEY not set"
`.env` 파일 확인 및 API 키 추가

### "Could not connect to Notion API"
- Integration Token 재확인
- 데이터베이스에 Integration 연결 확인

### "No active keywords found"
- 노션 데이터베이스에서 "활성화" 체크 확인
- 최소 1개 이상의 활성화된 키워드 필요

## 고급 기능

### 우선순위 기반 크롤링

우선순위가 높은 키워드부터 크롤링:

```python
keywords = manager.get_keywords(sort_by_priority=True)
# 결과: ['PF', '프로젝트 파이낸싱', '브릿지론', ...]
```

### 카테고리별 통계

```python
detailed = manager.get_keywords_detailed()
categories = {}
for kw in detailed:
    cat = kw['category'] or '미분류'
    categories[cat] = categories.get(cat, 0) + 1

# 결과: {'부동산금융': 5, '부동산시장': 5, '건설': 2, '신탁사': 14}
```

## 성능

- **노션 API 호출**: 크롤러 시작 시 1회
- **캐싱**: 없음 (매번 최신 데이터 로드)
- **오버헤드**: ~1-2초 (네트워크 상태에 따라)

## 모범 사례

### ✅ 권장사항
1. 정기적으로 비활성 키워드 정리
2. 우선순위 10: 핵심 키워드
3. 우선순위 1-5: 보조 키워드
4. 메모에 키워드 설명 추가

### ❌ 주의사항
1. Integration Token 공개 금지
2. 데이터베이스 삭제 주의
3. 모든 키워드 비활성화 금지

## 마이그레이션 가이드

### 기존 코드 → 노션

1. 기존 키워드 목록 복사
2. 노션 데이터베이스에 입력
3. 크롤러 코드는 자동으로 노션 사용
4. 기존 코드의 키워드 리스트는 폴백용으로 유지

## 참고 문서

- [빠른 시작 (5분)](QUICK_START_NOTION.md)
- [자세한 설정 가이드](NOTION_SETUP_GUIDE.md)
- [Notion API 문서](https://developers.notion.com/)

## 라이센스

이 프로젝트의 일부입니다.
