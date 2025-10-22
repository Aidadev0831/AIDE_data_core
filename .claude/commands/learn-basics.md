---
description: 기본 작업 배우기
---

# 📖 기본 작업 배우기

## Git 기본 작업

### 1. 변경사항 확인
```bash
git status
```
현재 어떤 파일이 변경되었는지 확인합니다.

### 2. 변경사항 저장 (커밋)
```bash
git add .
git commit -m "변경 내용 설명"
```

### 3. GitHub에 업로드
```bash
git push
```

## Python 스크립트 실행

### 크롤러 실행
```bash
python scripts/crawling/crawl_naver_news_bulk.py
```

### 데이터 전처리
```bash
python scripts/preprocessing/preprocess_news.py
```

### 테스트 실행
```bash
cd aide-api
poetry run pytest
```

## 자주 사용하는 명령어

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `/check-db` | DB 상태 확인 | `/check-db` |
| `/run-crawler` | 크롤러 실행 | `/run-crawler naver-news` |
| `/test-all` | 전체 테스트 | `/test-all` |

---

💡 **다음 단계**: `/what-next` 명령어로 다음 작업을 추천받으세요!
