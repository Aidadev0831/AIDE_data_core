#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
네이버 뉴스 API 크롤러 (insight_test 키워드, 오늘 기사만)

통합 크롤링 + 전처리:
1. Naver News API 크롤링 (오늘 날짜 필터링)
2. aide-preprocessing을 통한 전처리 및 DB 저장
"""
import sys
import os
import requests
from pathlib import Path
from datetime import datetime, date

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "aide-preprocessing"))
sys.path.insert(0, str(project_root / "aide-data-core"))

from dotenv import load_dotenv
load_dotenv(project_root / "aide-crawlers" / ".env")

from aide_preprocessing import PreprocessingPipeline
from aide_data_core.models import get_engine, get_session, NaverNews


def search_naver_news(keyword: str, display: int = 100):
    """Naver News API 검색 (순수 크롤링)

    Args:
        keyword: 검색 키워드
        display: 결과 개수 (최대 100)

    Returns:
        API 응답 JSON
    """
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError("NAVER API credentials not found in .env")

    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    params = {
        "query": keyword,
        "display": display,
        "sort": "date"  # 최신순
    }

    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()

    return response.json()


def is_today_article(pub_date_str: str) -> bool:
    """기사가 오늘 작성되었는지 확인"""
    try:
        # "Wed, 16 Oct 2024 18:30:00 +0900" 형식
        pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
        today = date.today()
        return pub_date.date() == today
    except:
        return False


def main():
    """메인 크롤링 + 전처리 함수"""
    print()
    print("=" * 80)
    print("네이버 뉴스 API 크롤러 (insight_test 키워드, 오늘 기사만)")
    print("=" * 80)
    print(f"크롤링 날짜: {date.today().isoformat()}")
    print()

    # Keywords (insight_test 검색어 26개)
    keywords = [
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

    print(f"키워드: {len(keywords)}개")
    print(f"예상 크롤링: ~{len(keywords) * 100}개 (필터링 전)")
    print()

    # Initialize preprocessing pipeline
    db_path = str(project_root / "aide-data-core" / "aide_dev.db").replace("\\", "/")
    db_url = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")
    engine = get_engine(db_url)
    session = get_session(engine)
    pipeline = PreprocessingPipeline(session)

    total_crawled = 0
    total_today = 0
    total_saved = 0
    total_duplicates = 0

    try:
        for idx, keyword in enumerate(keywords, 1):
            print(f"[{idx}/{len(keywords)}] {keyword}")

            # Step 1: Crawling (순수 크롤링)
            result = search_naver_news(keyword, display=100)
            items = result.get('items', [])
            total_crawled += len(items)

            # Filter today's articles only
            today_items = [item for item in items if is_today_article(item.get('pubDate', ''))]
            total_today += len(today_items)

            if not today_items:
                print(f"  크롤링: {len(items)}개 → 오늘: 0개 (건너뛰기)")
                continue

            print(f"  크롤링: {len(items)}개 → 오늘: {len(today_items)}개", end=" ")

            # Step 2: Preprocessing (전처리 + 중복 확인 + DB 저장)
            _, saved, duplicates = pipeline.process_and_save(
                today_items,
                keyword=keyword,
                model_class=NaverNews
            )

            total_saved += saved
            total_duplicates += duplicates

            print(f"→ 저장: {saved}개")

        # Final statistics
        print()
        print("=" * 80)
        print("크롤링 요약")
        print("=" * 80)
        print(f"총 크롤링: {total_crawled}개 (필터링 전)")
        print(f"오늘 기사: {total_today}개 ({total_today/total_crawled*100:.1f}%)" if total_crawled > 0 else "오늘 기사: 0개")
        print(f"저장: {total_saved}개")
        print(f"중복: {total_duplicates}개")
        print()
        print("=" * 80)
        print("[SUCCESS] API 크롤링 완료")
        print("=" * 80)

        return total_saved

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 0

    finally:
        pipeline.close()


if __name__ == "__main__":
    saved = main()
    sys.exit(0 if saved >= 0 else 1)
