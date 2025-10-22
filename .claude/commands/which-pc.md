---
description: 현재 어느 PC에서 작업 중인지 확인
allowed-tools: Bash(git:*), Bash(hostname:*)
---

# 💻 현재 작업 환경 확인

어느 PC에서 작업 중인지 확인하고, 환경에 맞는 설정을 확인합니다.

## 시스템 정보

- **컴퓨터 이름**: !`hostname`
- **현재 경로**: 작업 디렉토리 위치
- **Git 사용자**: !`git config user.name`
- **마지막 커밋**: 가장 최근 작업 내용

## OneDrive 상태

OneDrive 경로에서 작업 중인지 확인:
- ✅ OneDrive: 자동 동기화됨
- ❌ 로컬: 수동으로 Git 동기화 필요

## 환경별 추천 작업 방식

### 🖥️ 데스크탑 (사무실)
- 장시간 작업에 적합
- 테스트 및 배포 작업
- 정기적으로 `/sync-work` 실행

### 💻 노트북 (이동 중)
- 시작 전 `/sync-from-github` 실행
- 코드 리뷰 및 간단한 수정
- 작업 후 `/quick-save` 또는 `/sync-work`

---

현재 환경에 최적화된 작업 방법을 안내드립니다!
