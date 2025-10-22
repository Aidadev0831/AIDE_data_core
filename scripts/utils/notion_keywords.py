#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
노션 데이터베이스에서 크롤링 키워드 관리

노션 데이터베이스 구조:
- 키워드 (Title): 검색 키워드
- 카테고리 (Select): 부동산금융, 부동산시장, 건설, 신탁사
- 활성화 (Checkbox): 크롤링 사용 여부
- 우선순위 (Number): 1-10
- 메모 (Text): 설명
"""
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    print("⚠️  notion-client 패키지가 설치되지 않았습니다.")
    print("    설치: pip install notion-client")


class NotionKeywordManager:
    """노션에서 크롤링 키워드를 관리하는 클래스"""

    def __init__(self, api_key: Optional[str] = None, database_id: Optional[str] = None):
        """
        Args:
            api_key: 노션 API 키 (없으면 환경변수에서 읽음)
            database_id: 노션 데이터베이스 ID (없으면 환경변수에서 읽음)
        """
        if not NOTION_AVAILABLE:
            raise ImportError("notion-client 패키지가 필요합니다: pip install notion-client")

        # 환경변수 로드
        load_dotenv()

        self.api_key = api_key or os.getenv("NOTION_API_KEY")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")

        if not self.api_key:
            raise ValueError("NOTION_API_KEY가 설정되지 않았습니다 (.env 파일 확인)")

        if not self.database_id:
            raise ValueError("NOTION_DATABASE_ID가 설정되지 않았습니다 (.env 파일 확인)")

        self.client = Client(auth=self.api_key)

    def get_keywords(self,
                     category: Optional[str] = None,
                     active_only: bool = True,
                     sort_by_priority: bool = True) -> List[str]:
        """
        노션 데이터베이스에서 키워드 목록 가져오기

        Args:
            category: 특정 카테고리만 필터링 (None이면 전체)
            active_only: 활성화된 키워드만 (기본값: True)
            sort_by_priority: 우선순위 순으로 정렬 (기본값: True)

        Returns:
            키워드 문자열 리스트
        """
        keywords_data = self.get_keywords_detailed(category, active_only, sort_by_priority)
        return [kw['keyword'] for kw in keywords_data]

    def get_keywords_detailed(self,
                              category: Optional[str] = None,
                              active_only: bool = True,
                              sort_by_priority: bool = True) -> List[Dict]:
        """
        노션 데이터베이스에서 키워드 상세 정보 가져오기

        Returns:
            키워드 딕셔너리 리스트 [
                {
                    'keyword': str,
                    'category': str,
                    'priority': int,
                    'memo': str
                },
                ...
            ]
        """
        try:
            # 노션 데이터베이스 쿼리
            filter_conditions = []

            # 활성화 필터
            if active_only:
                filter_conditions.append({
                    "property": "활성화",
                    "checkbox": {
                        "equals": True
                    }
                })

            # 카테고리 필터
            if category:
                filter_conditions.append({
                    "property": "카테고리",
                    "select": {
                        "equals": category
                    }
                })

            # 필터 구성
            query_filter = {}
            if len(filter_conditions) > 1:
                query_filter = {
                    "and": filter_conditions
                }
            elif len(filter_conditions) == 1:
                query_filter = filter_conditions[0]

            # 정렬 설정
            sorts = []
            if sort_by_priority:
                sorts.append({
                    "property": "우선순위",
                    "direction": "descending"
                })

            # 쿼리 실행
            response = self.client.databases.query(
                database_id=self.database_id,
                filter=query_filter if query_filter else None,
                sorts=sorts if sorts else None
            )

            # 결과 파싱
            keywords = []
            for page in response.get("results", []):
                properties = page.get("properties", {})

                # 키워드 (Title)
                title_prop = properties.get("키워드", {})
                title_content = title_prop.get("title", [])
                keyword = title_content[0].get("text", {}).get("content", "") if title_content else ""

                if not keyword:
                    continue

                # 카테고리 (Select)
                category_prop = properties.get("카테고리", {})
                category_select = category_prop.get("select", {})
                category_value = category_select.get("name", "") if category_select else ""

                # 우선순위 (Number)
                priority_prop = properties.get("우선순위", {})
                priority = priority_prop.get("number", 5)

                # 메모 (Text)
                memo_prop = properties.get("메모", {})
                memo_content = memo_prop.get("rich_text", [])
                memo = memo_content[0].get("text", {}).get("content", "") if memo_content else ""

                keywords.append({
                    "keyword": keyword,
                    "category": category_value,
                    "priority": priority or 5,
                    "memo": memo
                })

            return keywords

        except Exception as e:
            print(f"❌ 노션 데이터베이스 읽기 실패: {e}")
            raise

    def test_connection(self) -> bool:
        """노션 연결 테스트"""
        try:
            # 데이터베이스 메타데이터 가져오기
            database = self.client.databases.retrieve(database_id=self.database_id)
            print(f"✅ 노션 연결 성공!")
            print(f"📋 데이터베이스: {database.get('title', [{}])[0].get('text', {}).get('content', 'Untitled')}")
            return True
        except Exception as e:
            print(f"❌ 노션 연결 실패: {e}")
            return False


def get_crawler_keywords(category: Optional[str] = None,
                         fallback_to_default: bool = True) -> List[str]:
    """
    크롤러에서 사용할 키워드 목록 가져오기

    노션 연결 실패 시 기본 키워드 리스트로 폴백

    Args:
        category: 카테고리 필터 (None이면 전체)
        fallback_to_default: 노션 실패 시 기본 키워드 사용 여부

    Returns:
        키워드 리스트
    """
    # 노션에서 읽기 시도
    if NOTION_AVAILABLE:
        try:
            manager = NotionKeywordManager()
            keywords = manager.get_keywords(category=category)

            if keywords:
                print(f"✅ 노션에서 {len(keywords)}개 키워드 로드")
                return keywords
            else:
                print("⚠️  노션 데이터베이스에 활성화된 키워드가 없습니다")

        except Exception as e:
            print(f"⚠️  노션 연결 실패: {e}")

    # 폴백: 기본 키워드
    if fallback_to_default:
        print("📋 기본 키워드 사용")
        return get_default_keywords()
    else:
        return []


def get_default_keywords() -> List[str]:
    """기본 키워드 리스트 (노션 연결 실패 시 사용)"""
    return [
        # 부동산 금융 관련
        "PF",
        "프로젝트 파이낸싱",
        "프로젝트파이낸싱",
        "브릿지론",
        "부동산신탁",

        # 부동산 시장 관련
        "부동산경매",
        "공매",
        "부실채권",
        "NPL",
        "리츠",

        # 건설 관련
        "건설사",
        "시공사",

        # 신탁사 (주요)
        "한국토지신탁",
        "한국자산신탁",
        "대한토지신탁",
        "코람코자산신탁",
        "KB부동산신탁",
        "하나자산신탁",
        "아시아신탁",
        "우리자산신탁",
        "무궁화신탁",
        "코리아신탁",
        "교보자산신탁",
        "대신자산신탁",
        "신영부동산신탁",
        "한국투자부동산신탁",
    ]


if __name__ == "__main__":
    # 테스트 코드
    print("=" * 80)
    print("노션 키워드 관리 테스트")
    print("=" * 80)

    if not NOTION_AVAILABLE:
        print("\n❌ notion-client 패키지가 설치되지 않았습니다")
        print("   설치: pip install notion-client")
        exit(1)

    try:
        manager = NotionKeywordManager()

        # 연결 테스트
        if manager.test_connection():
            print()

            # 전체 키워드
            all_keywords = manager.get_keywords()
            print(f"\n📋 전체 활성화 키워드: {len(all_keywords)}개")
            for i, kw in enumerate(all_keywords[:10], 1):
                print(f"  {i}. {kw}")
            if len(all_keywords) > 10:
                print(f"  ... 외 {len(all_keywords) - 10}개")

            # 상세 정보
            print("\n📊 상세 정보 (상위 5개):")
            detailed = manager.get_keywords_detailed()
            for kw_info in detailed[:5]:
                print(f"  • {kw_info['keyword']}")
                print(f"    카테고리: {kw_info['category']}, 우선순위: {kw_info['priority']}")
                if kw_info['memo']:
                    print(f"    메모: {kw_info['memo']}")

            # 카테고리별
            print("\n🏢 카테고리별 키워드:")
            for cat in ["부동산금융", "부동산시장", "건설", "신탁사"]:
                cat_keywords = manager.get_keywords(category=cat)
                print(f"  {cat}: {len(cat_keywords)}개")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
