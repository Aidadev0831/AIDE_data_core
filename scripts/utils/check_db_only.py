#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DB 상태만 확인하는 스크립트
"""
import sys
from pathlib import Path
from datetime import date

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "aide-data-core"))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from aide_data_core.models import NaverNews

db_url = "sqlite:///" + str(project_root / "aide-data-core" / "aide_dev.db")
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
db = Session()

try:
    # 전체 기사 수
    total_count = db.query(func.count(NaverNews.id)).scalar()

    # status 별 개수
    raw_count = db.query(func.count(NaverNews.id)).filter(NaverNews.status == 'raw').scalar()
    processed_count = db.query(func.count(NaverNews.id)).filter(NaverNews.status == 'processed').scalar()

    # 오늘 날짜 기사
    today_count = db.query(func.count(NaverNews.id)).filter(
        NaverNews.date >= date.today()
    ).scalar()

    # 키워드별 개수
    keyword_stats = db.query(
        NaverNews.keyword,
        func.count(NaverNews.id)
    ).group_by(NaverNews.keyword).all()

    # 출처별 개수 (상위 10개)
    source_stats = db.query(
        NaverNews.source,
        func.count(NaverNews.id)
    ).group_by(NaverNews.source).order_by(func.count(NaverNews.id).desc()).limit(10).all()

    print("=" * 80)
    print("DB 상태 확인 (NaverNews)")
    print("=" * 80)
    print(f"\n[총계] 총 기사 수: {total_count:,}개")

    print(f"\n[Status별 분포]")
    print(f"  - raw (미분류): {raw_count:,}개")
    print(f"  - processed (분류완료): {processed_count:,}개")

    print(f"\n[오늘 날짜 기사]: {today_count:,}개")

    if keyword_stats:
        print(f"\n[키워드별 분포]")
        for keyword, count in sorted(keyword_stats, key=lambda x: x[1], reverse=True):
            if keyword:
                print(f"  - {keyword}: {count:,}개")

    if source_stats:
        print(f"\n[출처별 분포] (상위 10개)")
        for source, count in source_stats:
            if source:
                print(f"  - {source}: {count:,}개")

    print("\n" + "=" * 80 + "\n")

    db.close()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    db.close()
