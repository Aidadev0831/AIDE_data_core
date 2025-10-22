# 노션 키워드 관리 시스템 설정 가이드

## 📌 개요

네이버 뉴스 크롤링 키워드를 노션 데이터베이스에서 관리하고, 크롤러 실행 시 자동으로 읽어옵니다.

## 🔧 1단계: 노션 Integration 생성

### 1.1 노션 Integration 만들기

1. https://www.notion.so/my-integrations 접속
2. "New integration" 클릭
3. 설정:
   - **Name**: AIDE Crawler Integration
   - **Associated workspace**: 본인의 워크스페이스 선택
   - **Type**: Internal Integration
4. "Submit" 클릭
5. **Internal Integration Token** 복사 (나중에 사용)

### 1.2 권한 설정

- ✅ Read content
- ✅ Update content (선택사항)
- ❌ Insert content (필요 없음)

## 📊 2단계: 노션 데이터베이스 생성

### 2.1 데이터베이스 구조

노션에서 새 페이지를 만들고 다음 구조의 데이터베이스를 생성합니다:

**데이터베이스 이름**: Crawler Keywords

| 속성 이름 | 타입 | 설명 |
|----------|------|------|
| 키워드 | Title | 검색 키워드 (예: "PF") |
| 카테고리 | Select | 부동산금융, 부동산시장, 건설, 신탁사 |
| 활성화 | Checkbox | 크롤링 사용 여부 |
| 우선순위 | Number | 1-10 (높을수록 우선) |
| 메모 | Text | 키워드 설명 |

### 2.2 샘플 데이터 입력

| 키워드 | 카테고리 | 활성화 | 우선순위 | 메모 |
|--------|---------|--------|---------|------|
| PF | 부동산금융 | ✅ | 10 | 프로젝트 파이낸싱 |
| 프로젝트 파이낸싱 | 부동산금융 | ✅ | 9 | |
| 브릿지론 | 부동산금융 | ✅ | 8 | |
| 부동산신탁 | 부동산금융 | ✅ | 7 | |
| 부동산경매 | 부동산시장 | ✅ | 6 | |
| NPL | 부동산시장 | ✅ | 5 | |
| 리츠 | 부동산시장 | ✅ | 5 | |
| 건설사 | 건설 | ✅ | 4 | |
| 시공사 | 건설 | ✅ | 4 | |
| 한국토지신탁 | 신탁사 | ✅ | 3 | |
| KB부동산신탁 | 신탁사 | ✅ | 3 | |

### 2.3 Integration 연결

1. 데이터베이스 페이지 우측 상단 `...` 클릭
2. "Add connections" 선택
3. 앞서 만든 "AIDE Crawler Integration" 선택

### 2.4 데이터베이스 ID 확인

데이터베이스 URL에서 ID 복사:
```
https://www.notion.so/{workspace}/{database_id}?v={view_id}
                                   ^^^^^^^^^^^^^^^^
                                   이 부분을 복사
```

예시:
```
https://www.notion.so/myworkspace/a1b2c3d4e5f6...
```
→ `a1b2c3d4e5f6...` 부분이 데이터베이스 ID

## 🔑 3단계: 환경 변수 설정

`.env` 파일에 추가:

```env
# Notion API
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_ID=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

## ✅ 4단계: 테스트

```bash
python scripts/utils/test_notion_keywords.py
```

성공 시 출력:
```
✅ 노션 연결 성공!
📋 활성화된 키워드 26개 로드됨
```

## 🎯 5단계: 크롤러 실행

이제 크롤러를 실행하면 자동으로 노션에서 키워드를 읽어옵니다:

```bash
python scripts/crawling/crawl_naver_api.py
```

## 📝 키워드 관리 방법

### 새 키워드 추가
1. 노션 데이터베이스에 새 행 추가
2. 키워드 입력 및 활성화 체크
3. 카테고리, 우선순위 설정
4. 저장 후 크롤러 실행

### 키워드 비활성화
1. 해당 키워드의 "활성화" 체크 해제
2. 다음 크롤링부터 자동으로 제외됨

### 우선순위 조정
1. "우선순위" 숫자 변경 (1-10)
2. 높은 숫자가 먼저 크롤링됨

## 🔄 고급 기능

### 카테고리별 필터링

특정 카테고리만 크롤링:
```bash
python scripts/crawling/crawl_naver_api.py --category "부동산금융"
```

### 우선순위 기반 크롤링

우선순위 높은 순으로 자동 정렬됨

## 🆘 문제 해결

### "Could not connect to Notion API"
- Integration Token 확인
- 데이터베이스에 Integration 연결 확인

### "Database not found"
- 데이터베이스 ID 확인
- Integration 권한 확인

### "No active keywords found"
- 노션에서 "활성화" 체크 확인
- 데이터베이스가 비어있지 않은지 확인

## 📊 노션 vs 코드 비교

| 방식 | 장점 | 단점 |
|------|------|------|
| **노션** | • 코드 수정 없이 관리<br>• 팀 공유 쉬움<br>• 카테고리/우선순위 관리<br>• 메모 추가 가능 | • API 설정 필요<br>• 네트워크 필요 |
| **코드** | • 빠름<br>• 오프라인 가능 | • 수정 시 코드 변경<br>• Git 커밋 필요 |

## 🎓 권장 사항

1. **일상 관리**: 노션에서 키워드 추가/삭제
2. **백업**: 정기적으로 키워드 목록 내보내기
3. **테스트**: 새 키워드 추가 후 소량 테스트

---

**다음 단계**: `scripts/utils/test_notion_keywords.py`로 연결 테스트
