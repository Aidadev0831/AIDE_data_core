#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
노션 키워드 관리 시스템 테스트

노션 연결 확인 및 키워드 로드 테스트
"""
import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.utils.notion_keywords import NotionKeywordManager, get_crawler_keywords, NOTION_AVAILABLE


def main():
    print("=" * 80)
    print("🧪 노션 키워드 관리 시스템 테스트")
    print("=" * 80)
    print()

    # 1. 패키지 확인
    if not NOTION_AVAILABLE:
        print("❌ notion-client 패키지가 설치되지 않았습니다")
        print()
        print("설치 방법:")
        print("  pip install notion-client")
        print()
        print("또는 requirements.txt가 있다면:")
        print("  pip install -r requirements.txt")
        return False

    print("✅ notion-client 패키지 설치됨")
    print()

    # 2. 환경변수 확인
    try:
        manager = NotionKeywordManager()
        print("✅ 환경변수 설정 확인 완료")
        print(f"  - NOTION_API_KEY: {'*' * 20}...{manager.api_key[-4:]}")
        print(f"  - NOTION_DATABASE_ID: {manager.database_id[:8]}...{manager.database_id[-8:]}")
        print()
    except ValueError as e:
        print(f"❌ 환경변수 오류: {e}")
        print()
        print("해결 방법:")
        print("  1. .env 파일에 다음 추가:")
        print("     NOTION_API_KEY=secret_xxxxx")
        print("     NOTION_DATABASE_ID=xxxxx")
        print()
        print("  2. 설정 가이드 참고:")
        print("     docs/NOTION_SETUP_GUIDE.md")
        return False

    # 3. 노션 연결 테스트
    print("📡 노션 연결 테스트 중...")
    if not manager.test_connection():
        print()
        print("해결 방법:")
        print("  1. Integration Token 확인")
        print("  2. 데이터베이스에 Integration 연결 확인")
        print("  3. 데이터베이스 ID 확인")
        print()
        print("자세한 내용: docs/NOTION_SETUP_GUIDE.md")
        return False

    print()

    # 4. 키워드 로드 테스트
    print("📋 키워드 로드 테스트...")
    try:
        keywords = manager.get_keywords()

        if not keywords:
            print("⚠️  활성화된 키워드가 없습니다")
            print()
            print("해결 방법:")
            print("  1. 노션 데이터베이스에서 키워드 추가")
            print("  2. '활성화' 체크박스 체크")
            print()
            return False

        print(f"✅ {len(keywords)}개 키워드 로드 성공!")
        print()

        # 5. 키워드 목록 출력
        print("📝 로드된 키워드:")
        for i, kw in enumerate(keywords[:15], 1):
            print(f"  {i:2d}. {kw}")

        if len(keywords) > 15:
            print(f"  ... 외 {len(keywords) - 15}개")

        print()

        # 6. 상세 정보 출력
        print("📊 키워드 상세 정보 (상위 5개):")
        detailed = manager.get_keywords_detailed()
        for kw_info in detailed[:5]:
            print(f"\n  📌 {kw_info['keyword']}")
            print(f"     카테고리: {kw_info['category']}")
            print(f"     우선순위: {kw_info['priority']}")
            if kw_info['memo']:
                print(f"     메모: {kw_info['memo']}")

        print()

        # 7. 카테고리별 통계
        print("📊 카테고리별 통계:")
        categories = {}
        for kw_info in detailed:
            cat = kw_info['category'] or '미분류'
            categories[cat] = categories.get(cat, 0) + 1

        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}개")

        print()

        # 8. get_crawler_keywords 함수 테스트
        print("🔧 get_crawler_keywords() 함수 테스트...")
        crawler_kws = get_crawler_keywords()
        print(f"✅ {len(crawler_kws)}개 키워드 로드")

        print()
        print("=" * 80)
        print("✅ 모든 테스트 통과!")
        print("=" * 80)
        print()
        print("다음 단계:")
        print("  1. 크롤러 실행: python scripts/crawling/crawl_naver_api.py")
        print("  2. 키워드 관리: 노션 데이터베이스에서 수정")
        print()

        return True

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
