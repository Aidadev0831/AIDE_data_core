#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DB 상태 확인 및 삭제 스크립트
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "aide-data-core"))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from aide_data_core.models import NaverNews

def check_db_status():
    """DB 상태 확인"""
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

        # 날짜별 개수
        today_count = db.query(func.count(NaverNews.id)).filter(
            func.date(NaverNews.created_at) == func.date('now')
        ).scalar()

        # 키워드별 개수
        keyword_stats = db.query(
            NaverNews.keyword,
            func.count(NaverNews.id)
        ).group_by(NaverNews.keyword).all()

        print("=" * 80)
        print("DB 상태 확인")
        print("=" * 80)
        print(f"\n총 기사 수: {total_count}")
        print(f"\nStatus별 분포:")
        print(f"  - raw: {raw_count}")
        print(f"  - processed: {processed_count}")
        print(f"\n오늘 수집된 기사: {today_count}")

        if keyword_stats:
            print(f"\n키워드별 분포:")
            for keyword, count in keyword_stats:
                print(f"  - {keyword}: {count}")

        db.close()
        return total_count

    except Exception as e:
        print(f"Error: {e}")
        db.close()
        return 0


def clear_naver_news():
    """NaverNews 테이블의 모든 데이터 삭제"""
    db_url = "sqlite:///" + str(project_root / "aide-data-core" / "aide_dev.db")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 삭제 전 개수 확인
        before_count = db.query(func.count(NaverNews.id)).scalar()

        # 모든 기사 삭제
        db.query(NaverNews).delete()
        db.commit()

        # 삭제 후 개수 확인
        after_count = db.query(func.count(NaverNews.id)).scalar()

        print("\n" + "=" * 80)
        print("DB 삭제 완료")
        print("=" * 80)
        print(f"삭제 전: {before_count}개")
        print(f"삭제 후: {after_count}개")
        print(f"삭제된 기사: {before_count - after_count}개")
        print("=" * 80 + "\n")

        db.close()
        return before_count - after_count

    except Exception as e:
        print(f"Error during deletion: {e}")
        db.rollback()
        db.close()
        return 0


if __name__ == "__main__":
    # 1. DB 상태 확인
    total = check_db_status()

    if total == 0:
        print("\n데이터베이스가 이미 비어있습니다.")
        sys.exit(0)

    # 2. 삭제 확인
    print("\n" + "=" * 80)
    response = input(f"정말로 {total}개의 모든 기사를 삭제하시겠습니까? (yes/no): ")

    if response.lower() == 'yes':
        deleted = clear_naver_news()
        print(f"✓ {deleted}개 기사가 삭제되었습니다.")
    else:
        print("삭제가 취소되었습니다.")
