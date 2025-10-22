#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple crawling script with integrated preprocessing

통합 크롤링 스크립트:
1. Naver News API 크롤링
2. aide-preprocessing을 통한 전처리 및 DB 저장
"""
import sys
import os
import requests
from pathlib import Path
from datetime import date

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


def main():
    """메인 크롤링 + 전처리 함수"""
    print("=" * 80)
    print("Simple Naver News Crawling + Preprocessing")
    print("=" * 80)
    print(f"Date: {date.today().isoformat()}\n")

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

    print(f"Keywords: {len(keywords)} keywords")
    print(f"Target: ~{len(keywords) * 100} articles\n")

    # Initialize preprocessing pipeline
    db_path = str(project_root / "aide-data-core" / "aide_dev.db").replace("\\", "/")
    db_url = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")
    print(f"[DEBUG] DB Path: {db_path}")
    print(f"[DEBUG] DB URL: {db_url}")
    print(f"[DEBUG] File exists: {(project_root / 'aide-data-core' / 'aide_dev.db').exists()}")
    print()
    engine = get_engine(db_url)
    session = get_session(engine)
    pipeline = PreprocessingPipeline(session)

    total_crawled = 0
    total_saved = 0
    total_duplicates = 0

    try:
        for idx, keyword in enumerate(keywords, 1):
            print(f"[{idx}/{len(keywords)}] {keyword}")

            # Step 1: Crawling (순수 크롤링)
            result = search_naver_news(keyword, display=100)
            raw_articles = result.get('items', [])

            crawled = len(raw_articles)
            total_crawled += crawled

            if crawled == 0:
                print(f"  Crawled: 0 articles (skipped)\n")
                continue

            print(f"  Crawled: {crawled} articles")

            # Step 2: Preprocessing (전처리 + 중복 확인 + DB 저장)
            _, saved, duplicates = pipeline.process_and_save(
                raw_articles,
                keyword=keyword,
                model_class=NaverNews
            )

            total_saved += saved
            total_duplicates += duplicates

            print(f"  Saved: {saved} articles (duplicates: {duplicates})\n")

        # Final statistics
        print("=" * 80)
        print("Crawling + Preprocessing Summary:")
        print("=" * 80)
        print(f"Total crawled: {total_crawled} articles")
        print(f"Total saved: {total_saved} articles")
        print(f"Total duplicates: {total_duplicates} articles ({total_duplicates/total_crawled*100:.1f}%)")
        print("=" * 80 + "\n")

        print("[SUCCESS] Crawling and preprocessing completed!\n")
        return 0

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        pipeline.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
