# 🎓 AIDE 프로젝트 초보자 가이드

코딩이 처음이거나 음성 코딩을 사용하시는 분들을 위한 완벽 가이드입니다.

## 📌 시작하기 전에

### Claude Code란?
AI 어시스턴트 Claude와 함께 코드를 작성하는 도구입니다.
- 음성으로 명령을 내릴 수 있습니다
- 코드를 설명해줍니다
- 자동으로 코드를 작성해줍니다

### 필수 개념

#### Git이란?
코드의 변경 이력을 관리하는 도구입니다.
- **커밋(Commit)**: 변경사항 저장
- **푸시(Push)**: GitHub에 업로드
- **풀(Pull)**: GitHub에서 다운로드

#### 슬래시 커맨드란?
`/` 로 시작하는 명령어입니다.
- 예: `/start`, `/help-commands`
- 음성으로 "슬래시 스타트"라고 말하면 실행됩니다

## 🚀 첫 시작

### 1단계: 프로젝트 이해하기
```
/start
```
프로젝트 구조와 현재 상태를 확인합니다.

### 2단계: 명령어 배우기
```
/help-commands
```
사용 가능한 모든 명령어를 확인합니다.

### 3단계: 환경 설정
```
/setup-env
```
개발 환경을 자동으로 설정합니다.

## 💼 일상 작업 플로우

### 아침 - 작업 시작
```
/which-pc          # 현재 PC 확인
/sync-from-github  # 최신 코드 받기
/what-next         # 오늘 할 일 확인
```

### 작업 중
```
/explain-code [파일]  # 코드 이해하기
/run-crawler [이름]   # 크롤러 실행
/check-db             # 데이터 확인
```

### 퇴근 전 또는 PC 변경 전
```
/test-all      # 테스트 실행
/sync-work     # 작업 내용 저장 및 업로드
```

### 긴급 상황
```
/quick-save    # 빠르게 저장하고 종료
```

## 🔄 멀티 디바이스 작업

### 데스크탑 → 노트북
1. 데스크탑에서: `/sync-work`
2. 노트북에서: `/sync-from-github`
3. 작업 계속

### 노트북 → 데스크탑
1. 노트북에서: `/sync-work` 또는 `/quick-save`
2. 데스크탑에서: `/sync-from-github`
3. 작업 계속

## 🎯 상황별 명령어

### 데이터 수집하기
```
/run-crawler naver-news    # 네이버 뉴스 수집
/run-crawler kdi           # KDI 자료 수집
/show-data                 # 수집된 데이터 확인
```

### 코드 이해하기
```
/explain-code [파일경로]   # 코드 설명
/learn-basics              # 기본 개념 배우기
```

### 문제 해결
```
/troubleshoot              # 문제 해결 가이드
/check-db                  # DB 상태 확인
/deploy-check              # 전체 시스템 점검
```

### 새 기능 추가
```
/add-feature               # 기능 추가 단계별 가이드
```

## 📱 음성 명령어 팁

### 또렷하게 발음하기
- "슬래시 스타트" → `/start`
- "슬래시 헬프 커맨즈" → `/help-commands`
- "슬래시 싱크 워크" → `/sync-work`

### 파일 경로 말하기
```
"슬래시 익스플레인 코드 스크립트 슬래시 크롤링 슬래시 파일명"
```

### 인수가 있는 명령어
```
"슬래시 런 크롤러 네이버 뉴스"
```

## ⚠️ 주의사항

### 절대 하지 말아야 할 것
1. `.env` 파일을 Git에 커밋하지 않기
2. API 키를 코드에 직접 쓰지 않기
3. `rm -rf` 같은 위험한 명령어 사용 안 하기

### 항상 해야 할 것
1. 작업 전 `/sync-from-github`로 최신 코드 받기
2. 작업 후 `/sync-work`로 저장하기
3. 에러가 나면 에러 메시지 전체 복사해서 질문하기

## 🆘 도움 받기

### 에러가 났을 때
1. 에러 메시지를 천천히 읽어보기
2. `/troubleshoot` 명령어로 해결 방법 찾기
3. 안 되면 에러 메시지 전체를 복사해서 질문

### 질문하는 방법
```
"scripts/crawling/crawl_naver_api.py 파일에서
ModuleNotFoundError: No module named 'requests'
에러가 발생했어요. 어떻게 해결하나요?"
```

## 📚 학습 경로

### 1주차: 기본 익히기
- Day 1-2: `/start`, `/help-commands`, `/learn-basics`
- Day 3-4: `/explain-code`로 각 파일 이해하기
- Day 5: `/run-crawler`로 데이터 수집 실습

### 2주차: 실전 작업
- Day 1-2: `/sync-work`, `/sync-from-github` 연습
- Day 3-4: `/add-feature`로 간단한 기능 추가
- Day 5: `/deploy-check`, `/test-all` 테스트

### 3주차: 독립 작업
- 혼자서 크롤러 실행하고 데이터 확인
- 코드 수정하고 테스트하기
- Git으로 버전 관리하기

## 🎉 성공 체크리스트

- [ ] `/start`로 프로젝트를 이해했다
- [ ] `/help-commands`로 명령어를 외웠다
- [ ] `/sync-work`와 `/sync-from-github`를 사용할 수 있다
- [ ] `/run-crawler`로 데이터를 수집할 수 있다
- [ ] `/explain-code`로 코드를 이해할 수 있다
- [ ] 에러가 나도 `/troubleshoot`로 해결할 수 있다
- [ ] 여러 PC에서 작업을 전환할 수 있다

---

## 💡 핵심 기억사항

1. **작업 시작**: `/sync-from-github` (최신 코드 받기)
2. **작업 종료**: `/sync-work` (저장하고 업로드)
3. **급할 때**: `/quick-save` (빠르게 저장)
4. **모르겠을 때**: `/help-commands` (명령어 확인)
5. **에러날 때**: `/troubleshoot` (해결 방법)

이 5가지만 기억하면 됩니다! 😊

---

**이 가이드는 언제든 `.claude/BEGINNER_GUIDE.md`에서 다시 볼 수 있습니다.**
