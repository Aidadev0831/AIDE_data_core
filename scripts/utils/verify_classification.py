#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
분류 품질 검증 스크립트
"""
import sys
import os
from pathlib import Path
from collections import Counter
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "aide-data-core"))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from aide_data_core.models import NaverNews


def main():
    """분류 품질 검증"""
    print("=" * 80)
    print("분류 품질 검증 (Classification Quality Verification)")
    print("=" * 80)
    print()

    # DB 연결
    db_url = "sqlite:///" + str(project_root / "aide-data-core" / "aide_dev.db")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 전체 통계
        total = db.query(NaverNews).count()
        raw = db.query(NaverNews).filter(NaverNews.status == 'raw').count()
        processed = db.query(NaverNews).filter(NaverNews.status == 'processed').count()

        print(f"📊 전체 통계")
        print(f"  전체 기사: {total}개")
        print(f"  Raw 상태: {raw}개")
        print(f"  Processed 상태: {processed}개")
        print()

        # 카테고리별 통계
        print("=" * 80)
        print("📈 카테고리별 분류 통계")
        print("=" * 80)

        processed_articles = db.query(NaverNews).filter(
            NaverNews.status == 'processed'
        ).all()

        category_counter = Counter()

        for article in processed_articles:
            if article.classified_categories:
                try:
                    categories = json.loads(article.classified_categories)
                    for cat in categories:
                        category_counter[cat] += 1
                except:
                    pass

        for cat_name, count in category_counter.most_common():
            print(f"  {cat_name}: {count}개")

        print()

        # 샘플 기사 확인
        print("=" * 80)
        print("✅ 분류 완료 기사 샘플 (최근 10개)")
        print("=" * 80)

        recent_processed = db.query(NaverNews).filter(
            NaverNews.status == 'processed'
        ).order_by(NaverNews.id.desc()).limit(10).all()

        for i, article in enumerate(recent_processed, 1):
            print(f"\n[{i}] ID: {article.id}")
            print(f"제목: {article.title[:80]}")

            if article.classified_categories:
                try:
                    categories = json.loads(article.classified_categories)
                    print(f"카테고리: {', '.join(categories)}")
                except Exception as e:
                    print(f"카테고리: [ERROR] {article.classified_categories[:100]}")
            else:
                print(f"카테고리: 없음")

        # Multi-label 통계
        print()
        print("=" * 80)
        print("🏷️  Multi-label 통계")
        print("=" * 80)

        label_count_dist = Counter()

        for article in processed_articles:
            if article.classified_categories:
                try:
                    categories = json.loads(article.classified_categories)
                    label_count_dist[len(categories)] += 1
                except:
                    pass

        for num_labels, count in sorted(label_count_dist.items()):
            print(f"  {num_labels}개 카테고리: {count}개 기사")

        print()

        # 크롤링 키워드별 통계
        print("=" * 80)
        print("🔍 크롤링 키워드별 통계")
        print("=" * 80)

        keyword_stats = db.query(
            NaverNews.keyword,
            func.count(NaverNews.id).label('count')
        ).group_by(NaverNews.keyword).all()

        for keyword, count in keyword_stats:
            print(f"  {keyword}: {count}개")

        print()
        print("=" * 80)
        print("[DONE] 검증 완료")
        print("=" * 80)

        db.close()
        return 0

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        db.close()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
