#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple News Crawling and DB Save Script
"""
import sys
import os
from pathlib import Path
from datetime import datetime, date

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "aide-crawlers"))
sys.path.insert(0, str(project_root / "aide-data-core"))

from dotenv import load_dotenv
load_dotenv(project_root / "aide-crawlers" / ".env")

from aide_crawlers.crawlers.naver.news_api import NaverNewsAPICrawler
from aide_crawlers.sinks.db_sink import DatabaseSink
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from aide_data_core.models import NaverNews


def main():
    """크롤링 및 DB 저장"""
    print("=" * 80)
    print("Naver News Crawling & Save")
    print("=" * 80)
    print(f"Date: {date.today().isoformat()}\n")

    # Database setup
    db_url = "sqlite:///" + str(project_root / "aide-data-core" / "aide_dev.db")

    # Keywords (insight_test 검색어)
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

    print(f"Keywords: {', '.join(keywords)}")
    print(f"Target: ~{len(keywords) * 100} articles\n")

    try:
        # Create crawler with DB sink
        sink = DatabaseSink(database_url=db_url)

        crawler = NaverNewsAPICrawler(
            keywords=keywords,
            sink=sink,
            display=100  # 100 per keyword
        )

        # Run crawl
        print("Starting crawl...\n")
        result = crawler.run()

        print(f"\n{'='*80}")
        print("Crawling Results:")
        print(f"  Crawled: {result.get('crawled_count', 0)} articles")
        print(f"  Saved: {result.get('saved_count', 0)} articles")
        print(f"  Errors: {result.get('error_count', 0)}")
        print(f"{'='*80}\n")

        # DB Stats
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        db = Session()

        total_count = db.query(func.count(NaverNews.id)).scalar()
        today_count = db.query(func.count(NaverNews.id)).filter(
            func.date(NaverNews.crawled_at) == date.today()
        ).scalar()

        print("Database Stats:")
        print(f"  Total articles: {total_count}")
        print(f"  Today's articles: {today_count}")
        print(f"{'='*80}\n")

        db.close()
        crawler.close()

        print("[SUCCESS] Crawling completed!\n")
        return 0

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
