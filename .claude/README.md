# Claude Code 설정 가이드

이 디렉토리는 AIDE Data Core 프로젝트의 Claude Code 환경 설정을 포함합니다.

## 파일 구조

```
.claude/
├── CLAUDE.md                 # 프로젝트 메모리 (컨텍스트)
├── BEGINNER_GUIDE.md         # 초보자 완벽 가이드 ⭐
├── settings.json             # 팀 공유 설정 (Git에 커밋됨)
├── settings.local.json       # 개인 설정 (Git에서 제외됨)
├── commands/                 # 슬래시 커맨드
│   ├── 🚀 시작하기
│   │   ├── start.md             # 프로젝트 시작 가이드
│   │   ├── help-commands.md     # 모든 명령어 설명
│   │   ├── setup-env.md         # 환경 설정
│   │   └── learn-basics.md      # 기본 작업 배우기
│   ├── 🔄 멀티 디바이스
│   │   ├── sync-work.md         # 작업 동기화 (이동 전)
│   │   ├── sync-from-github.md  # 최신 코드 가져오기
│   │   ├── quick-save.md        # 빠른 저장 (긴급)
│   │   └── which-pc.md          # 현재 PC 확인
│   ├── 🧪 테스트 & 검증
│   │   ├── test-all.md          # 전체 테스트
│   │   ├── check-db.md          # DB 상태 확인
│   │   └── deploy-check.md      # 배포 전 검증
│   ├── 🔧 데이터 작업
│   │   ├── run-crawler.md       # 크롤러 실행
│   │   ├── pipeline-status.md   # 파이프라인 상태
│   │   └── show-data.md         # 최근 데이터 확인
│   ├── 📝 코드 작업
│   │   ├── fix-imports.md       # Import 정리
│   │   ├── explain-code.md      # 코드 설명
│   │   └── add-feature.md       # 새 기능 추가
│   └── 🆘 도움말
│       ├── troubleshoot.md      # 문제 해결
│       └── what-next.md         # 다음 작업 추천
└── README.md                     # 이 파일
```

## 🎯 빠른 시작 (초보자용)

**처음 사용하시나요?** 먼저 이것부터 시작하세요:

```bash
/start              # 프로젝트 시작 가이드
/help-commands      # 모든 명령어 보기
```

**초보자 완벽 가이드**: `.claude/BEGINNER_GUIDE.md` 파일을 참고하세요!

## 📚 주요 슬래시 커맨드

### 🚀 시작하기
| 명령어 | 설명 | 사용 예 |
|--------|------|---------|
| `/start` | 프로젝트 시작 가이드 | `/start` |
| `/help-commands` | 모든 명령어 설명 | `/help-commands` |
| `/setup-env` | 개발 환경 설정 | `/setup-env` |
| `/learn-basics` | 기본 작업 배우기 | `/learn-basics` |

### 🔄 멀티 디바이스 (데스크탑↔노트북)
| 명령어 | 설명 | 언제 사용? |
|--------|------|-----------|
| `/sync-work` | 작업 저장 및 동기화 | PC 변경 전, 퇴근 전 |
| `/sync-from-github` | 최신 코드 가져오기 | 작업 시작 전 |
| `/quick-save` | 빠른 저장 | 긴급 상황 |
| `/which-pc` | 현재 PC 확인 | 환경 확인 필요 시 |

### 🧪 테스트 & 검증
| 명령어 | 설명 |
|--------|------|
| `/test-all` | 전체 테스트 실행 |
| `/check-db` | DB 상태 확인 |
| `/deploy-check` | 배포 전 검증 |

### 🔧 데이터 작업
| 명령어 | 예시 |
|--------|------|
| `/run-crawler [이름]` | `/run-crawler naver-news` |
| `/pipeline-status` | 파이프라인 상태 확인 |
| `/show-data` | 최근 수집 데이터 확인 |

### 📝 코드 작업
| 명령어 | 예시 |
|--------|------|
| `/explain-code [파일]` | `/explain-code scripts/crawling/crawl_naver_api.py` |
| `/fix-imports [파일]` | `/fix-imports scripts/utils/check_db.py` |
| `/add-feature` | 새 기능 추가 가이드 |

### 🆘 도움말
| 명령어 | 설명 |
|--------|------|
| `/troubleshoot` | 문제 해결 가이드 |
| `/what-next` | 다음 작업 추천 |

## 권한 설정

### 자동 허용 (Allow)
- Python 테스트 실행 (`pytest`)
- Poetry 명령어
- Git 조회 명령어 (`status`, `diff`, `log`)
- 프로젝트 파일 읽기/편집

### 자동 거부 (Deny)
- `.env` 파일 접근
- 위험한 삭제 명령 (`rm -rf`)
- 직접 pip install
- Poetry publish

### 확인 필요 (Ask)
- DB 정리 스크립트
- Git 커밋/푸시
- 환경 변수 파일 생성

## 프로젝트 메모리 (CLAUDE.md)

프로젝트의 구조, 명령어, 코딩 규칙 등이 문서화되어 있습니다.
Claude Code가 프로젝트를 이해하는 데 사용됩니다.

## 개인 설정 커스터마이징

팀 공유 설정을 유지하면서 개인 설정을 추가하려면 `settings.local.json`을 수정하세요.

```json
{
  "permissions": {
    "allow": [
      "Bash(custom-command:*)"
    ]
  }
}
```

`settings.local.json`은 Git에서 자동으로 제외됩니다.

## 💼 일상 작업 플로우

### 아침 - 작업 시작
```bash
/which-pc          # 현재 PC 확인
/sync-from-github  # 최신 코드 받기
/what-next         # 오늘 할 일 확인
```

### 작업 중
```bash
/run-crawler naver-news  # 데이터 수집
/check-db                # 데이터 확인
/test-all                # 테스트
```

### 퇴근 전 / PC 변경 전
```bash
/sync-work         # 작업 저장 및 업로드
```

### 긴급 상황
```bash
/quick-save        # 빠르게 저장하고 종료
```

## 🔄 멀티 디바이스 작업 시나리오

### 시나리오 1: 데스크탑 → 노트북
1. **데스크탑에서**: `/sync-work` (작업 저장)
2. **노트북에서**: `/sync-from-github` (코드 가져오기)
3. **작업 계속**

### 시나리오 2: 노트북 → 데스크탑
1. **노트북에서**: `/sync-work` 또는 `/quick-save`
2. **데스크탑에서**: `/sync-from-github`
3. **작업 계속**

## ⚡ 음성 명령어 팁 (바이브코딩)

### 기본 명령어
- "슬래시 스타트" → `/start`
- "슬래시 싱크 워크" → `/sync-work`
- "슬래시 헬프 커맨즈" → `/help-commands`

### 파라미터 있는 명령어
- "슬래시 런 크롤러 네이버 뉴스" → `/run-crawler naver-news`
- "슬래시 익스플레인 코드 [파일경로]" → `/explain-code [파일경로]`

## 모범 사례

### 보안
1. ⛔ `.env` 파일은 절대 Git에 커밋하지 않기
2. ⛔ API 키를 코드에 직접 쓰지 않기
3. ✅ `.env.example`로 필요한 환경변수 문서화

### 버전 관리
1. ✅ 작업 시작 전: `/sync-from-github`
2. ✅ 작업 완료 후: `/sync-work`
3. ✅ 의미있는 커밋 메시지 작성

### 코드 품질
1. ✅ 테스트 실행: `/test-all`
2. ✅ Import 정리: `/fix-imports`
3. ✅ 배포 전 검증: `/deploy-check`

## 문제 해결

### 커맨드가 작동하지 않을 때
- 커맨드 파일 경로 확인: `.claude/commands/[name].md`
- Frontmatter 형식 확인 (YAML)
- 허용된 도구 확인 (`allowed-tools`)

### 권한 거부 에러
- `settings.json`의 `permissions.deny` 확인
- 필요시 `permissions.ask`에 추가

## 추가 리소스

- [Claude Code 문서](https://docs.claude.com/en/docs/claude-code/)
- [슬래시 커맨드 가이드](https://docs.claude.com/en/docs/claude-code/slash-commands.md)
- [설정 가이드](https://docs.claude.com/en/docs/claude-code/settings.md)
