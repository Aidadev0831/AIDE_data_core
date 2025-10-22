---
description: 새 기능 추가 가이드 (초보자용)
---

# ✨ 새 기능 추가하기

새로운 기능을 추가하는 과정을 단계별로 안내합니다.

## 1단계: 기능 설계

먼저 다음 질문에 답해주세요:
1. 어떤 기능을 추가하고 싶으신가요?
2. 이 기능은 어떤 문제를 해결하나요?
3. 어떤 모듈에 추가되어야 하나요?

## 2단계: 파일 위치 결정

기능 유형별 위치:
- **새 크롤러**: `aide-crawlers/aide_crawlers/crawlers/`
- **데이터 처리**: `aide-data-engine/aide_data_engine/services/`
- **API 엔드포인트**: `aide-api/aide_api/routers/`
- **유틸리티**: `scripts/utils/`

## 3단계: 코드 작성

1. 기존 비슷한 코드 참고
2. 함수/클래스 작성
3. Docstring 추가 (설명 주석)

## 4단계: 테스트 작성

테스트 파일 생성:
- 입력값과 예상 결과 정의
- 다양한 케이스 테스트

## 5단계: 통합 및 실행

1. 의존성 설치 (`poetry install`)
2. 테스트 실행 (`/test-all`)
3. 실제 환경에서 테스트

## 6단계: Git 커밋

```bash
git add .
git commit -m "feat: [기능 설명]"
git push
```

---

각 단계마다 도움이 필요하면 질문해주세요!
저와 함께 천천히 진행해봅시다. 😊
