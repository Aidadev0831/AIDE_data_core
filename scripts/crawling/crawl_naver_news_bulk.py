#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bulk Naver News Crawling Script
실제 200개 기사 크롤링
"""
import sys
import os
from pathlib import Path
from datetime import datetime, date

# aide-crawlers 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "aide-crawlers"))
sys.path.insert(0, str(project_root / "aide-data-core"))

from dotenv import load_dotenv
load_dotenv(project_root / "aide-crawlers" / ".env")

from aide_crawlers.crawlers.news.naver_news import NaverNewsCrawler
from aide_data_core.database import get_session
from aide_data_core.models import NaverNews
from sqlalchemy import func


def crawl_news_bulk(keywords: list = None, total_target: int = 200):
    """
    대량 뉴스 크롤링

    Args:
        keywords: 검색 키워드 리스트
        total_target: 목표 기사 수
    """
    if keywords is None:
        # insight_test 검색어
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

    print("=" * 80)
    print("Naver News Bulk Crawling")
    print("=" * 80)
    print(f"Target: {total_target} articles")
    print(f"Keywords: {len(keywords)} keywords")
    print(f"Date: {date.today().isoformat()}")
    print("=" * 80 + "\n")

    db = get_session()
    crawler = NaverNewsCrawler()

    total_crawled = 0
    total_saved = 0

    per_keyword = total_target // len(keywords)

    for keyword in keywords:
        print(f"\n[{keyword}] Crawling...")

        try:
            # 크롤링
            news_list = crawler.crawl(
                keyword=keyword,
                start_date=date.today(),
                end_date=date.today(),
                max_items=per_keyword
            )

            total_crawled += len(news_list)
            print(f"  Crawled: {len(news_list)} articles")

            # DB에 저장
            saved_count = 0
            for news_data in news_list:
                try:
                    # 중복 확인 (URL 기준)
                    exists = db.query(NaverNews).filter(
                        NaverNews.url == news_data.get('url')
                    ).first()

                    if exists:
                        continue

                    # 새 기사 생성
                    article = NaverNews(
                        title=news_data.get('title'),
                        source=news_data.get('source'),
                        url=news_data.get('url'),
                        date=news_data.get('date'),
                        keyword=keyword,
                        status='raw',
                        crawled_at=datetime.now()
                    )

                    # 설명/썸네일이 있으면 추가
                    if news_data.get('description'):
                        article.description = news_data.get('description')
                    if news_data.get('thumbnail'):
                        article.thumbnail = news_data.get('thumbnail')

                    db.add(article)
                    saved_count += 1

                except Exception as e:
                    print(f"    Error saving article: {e}")
                    continue

            db.commit()
            total_saved += saved_count
            print(f"  Saved: {saved_count} articles")

        except Exception as e:
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            continue

    # 통계
    print("\n" + "=" * 80)
    print("Crawling Summary")
    print("=" * 80)
    print(f"Total Crawled: {total_crawled} articles")
    print(f"Total Saved: {total_saved} articles")
    print(f"Duplicates: {total_crawled - total_saved} articles")

    # DB 통계
    total_in_db = db.query(func.count(NaverNews.id)).scalar()
    today_count = db.query(func.count(NaverNews.id)).filter(
        func.date(NaverNews.crawled_at) == date.today()
    ).scalar()

    print(f"\nDatabase Stats:")
    print(f"  Total articles in DB: {total_in_db}")
    print(f"  Today's articles: {today_count}")
    print("=" * 80 + "\n")

    db.close()

    return {
        "crawled": total_crawled,
        "saved": total_saved,
        "total_in_db": total_in_db
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Bulk crawl Naver news")
    parser.add_argument("--target", type=int, default=200, help="Target number of articles")

    args = parser.parse_args()

    result = crawl_news_bulk(total_target=args.target)

    print(f"\n[SUCCESS] Crawling completed!")
    print(f"  Crawled: {result['crawled']}")
    print(f"  Saved: {result['saved']}")
