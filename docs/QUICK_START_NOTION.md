# 🚀 노션 키워드 관리 빠른 시작 가이드

## 5분만에 설정하기

### 1️⃣ 노션 Integration 만들기 (2분)

1. https://www.notion.so/my-integrations 접속
2. "New integration" 클릭
3. 이름: `AIDE Crawler Integration`
4. **토큰 복사** (secret_xxxxx 형태)

### 2️⃣ 노션 데이터베이스 만들기 (2분)

1. 노션에서 새 페이지 생성
2. `/database` 입력 → "Table - Inline" 선택
3. 데이터베이스 이름: `Crawler Keywords`

### 3️⃣ 컬럼 설정

| 컬럼 이름 | 타입 | 필수 |
|-----------|------|------|
| 키워드 | Title | ✅ |
| 카테고리 | Select | ❌ |
| 활성화 | Checkbox | ✅ |
| 우선순위 | Number | ❌ |
| 메모 | Text | ❌ |

**카테고리 옵션 추가**: 부동산금융, 부동산시장, 건설, 신탁사

### 4️⃣ 샘플 데이터 입력

| 키워드 | 카테고리 | 활성화 | 우선순위 |
|--------|---------|--------|---------|
| PF | 부동산금융 | ✅ | 10 |
| 브릿지론 | 부동산금융 | ✅ | 8 |
| NPL | 부동산시장 | ✅ | 5 |

### 5️⃣ Integration 연결

1. 데이터베이스 페이지 우측 상단 `...` 클릭
2. "Add connections" → "AIDE Crawler Integration" 선택

### 6️⃣ 데이터베이스 ID 복사

URL에서 ID 부분 복사:
```
https://www.notion.so/workspace/[여기부분이ID]?v=...
                              ^^^^^^^^^^^^^^^^
```

### 7️⃣ .env 파일 설정

`aide-crawlers/.env` 파일에 추가:

```env
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxx
```

### 8️⃣ 패키지 설치

```bash
pip install notion-client
```

### 9️⃣ 테스트

```bash
python scripts/utils/test_notion_keywords.py
```

성공하면:
```
✅ 노션 연결 성공!
✅ 3개 키워드 로드 성공!
```

### 🔟 크롤러 실행

```bash
python scripts/crawling/crawl_naver_api.py
```

---

## 💡 사용 팁

### 키워드 추가
노션에서 새 행 추가 → "활성화" 체크 → 저장

### 키워드 비활성화
"활성화" 체크 해제

### 우선순위 조정
숫자 변경 (10이 가장 높음)

---

## 🆘 문제 해결

### "Could not connect"
→ Integration Token 다시 확인

### "Database not found"
→ 데이터베이스 ID 확인
→ Integration 연결 확인

### "No active keywords"
→ 노션에서 "활성화" 체크 확인

---

**자세한 내용**: `docs/NOTION_SETUP_GUIDE.md`
