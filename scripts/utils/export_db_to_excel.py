#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DB 기사를 엑셀로 출력
"""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "aide-data-core"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from aide_data_core.models import NaverNews

def export_to_excel():
    """DB 기사를 엑셀로 출력"""
    db_url = "sqlite:///" + str(project_root / "aide-data-core" / "aide_dev.db")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 모든 기사 조회
        articles = db.query(NaverNews).order_by(NaverNews.date.desc()).all()

        print("=" * 80)
        print("DB -> Excel Export")
        print("=" * 80)
        print(f"\nTotal articles: {len(articles)}")

        if len(articles) == 0:
            print("No articles to export.")
            db.close()
            return

        # DataFrame 생성
        data = []
        for article in articles:
            data.append({
                'ID': article.id,
                '제목': article.title,
                '출처': article.source,
                'URL': article.url,
                '키워드': article.keyword,
                '날짜': article.date.strftime('%Y-%m-%d %H:%M:%S') if article.date else '',
                '설명': article.description,
                '상태': article.status,
                '분류카테고리': article.classified_categories,
                '생성일시': article.created_at.strftime('%Y-%m-%d %H:%M:%S') if article.created_at else '',
                '수정일시': article.updated_at.strftime('%Y-%m-%d %H:%M:%S') if article.updated_at else ''
            })

        df = pd.DataFrame(data)

        # 엑셀 파일 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = project_root / f"naver_news_export_{timestamp}.xlsx"

        # 엑셀로 저장 (openpyxl 엔진 사용)
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 전체 데이터
            df.to_excel(writer, sheet_name='전체기사', index=False)

            # raw 상태만
            df_raw = df[df['상태'] == 'raw']
            if len(df_raw) > 0:
                df_raw.to_excel(writer, sheet_name='미분류', index=False)

            # processed 상태만
            df_processed = df[df['상태'] == 'processed']
            if len(df_processed) > 0:
                df_processed.to_excel(writer, sheet_name='분류완료', index=False)

            # 키워드별 시트
            for keyword in df['키워드'].dropna().unique()[:10]:  # 상위 10개 키워드만
                df_keyword = df[df['키워드'] == keyword]
                safe_keyword = str(keyword)[:30]  # 시트명 길이 제한
                df_keyword.to_excel(writer, sheet_name=safe_keyword, index=False)

        print(f"\n[SUCCESS] Excel file created: {output_file.name}")
        print(f"  Location: {output_file}")
        print(f"\nSheets:")
        print(f"  - 전체기사: {len(df)} rows")
        print(f"  - 미분류: {len(df_raw)} rows")
        print(f"  - 분류완료: {len(df_processed)} rows")
        print(f"  - 키워드별: {min(10, len(df['키워드'].dropna().unique()))} sheets")
        print("\n" + "=" * 80 + "\n")

        db.close()

    except ImportError as e:
        print(f"\nError: pandas or openpyxl not installed")
        print(f"Please install: pip install pandas openpyxl")
        print(f"Details: {e}")
        db.close()

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        db.close()


if __name__ == "__main__":
    export_to_excel()
