#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
오늘의 헤드라인 (Today's Headlines) - Notion 업로드
"""
import sys
import os
import json
import requests
from pathlib import Path
from datetime import datetime, date

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "aide-data-core"))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from aide_data_core.models import NaverNews

# Notion 설정
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_API_VERSION = "2022-06-28"
TODAY_HEADLINES_PAGE_ID = os.getenv("NOTION_PAGE_TODAY_HEADLINES", "28c18b63af4d8031afc6ed04b3d056c3")

# 카테고리 이름
CATEGORY_NAMES = {
    "policy_regulation": "정책·규제",
    "market_transaction": "시장동향",
    "development_supply": "분양·입주",
    "finance_investment": "금융·투자",
    "construction_development": "개발·사업",
    "construction": "건설·시공",
    "commercial_realestate": "상업용 부동산",
    "auction_public_sale": "경매·공매",
}


def get_notion_headers():
    """Notion API 헤더"""
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION
    }


def delete_blocks_from_page(page_id: str, start_index: int = 2):
    """페이지의 특정 인덱스부터 블록 삭제"""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    response = requests.get(url, headers=get_notion_headers(), timeout=30)

    if response.status_code != 200:
        return False

    blocks = response.json().get("results", [])
    blocks_to_delete = blocks[start_index:]

    for block in blocks_to_delete:
        delete_url = f"https://api.notion.com/v1/blocks/{block['id']}"
        requests.delete(delete_url, headers=get_notion_headers(), timeout=30)

    return True


def append_blocks_to_page(page_id: str, blocks: list):
    """페이지에 블록 추가"""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    response = requests.patch(
        url,
        headers=get_notion_headers(),
        json={"children": blocks},
        timeout=30
    )
    return response.status_code == 200


def create_empty_block():
    """빈 블록 생성"""
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": ""}}]}
    }


def create_footer_blocks(logo_url: str = None):
    """푸터 블록 생성"""
    blocks = []

    # 3개의 빈 줄
    for _ in range(3):
        blocks.append(create_empty_block())

    # 로고 이미지 (있으면)
    if logo_url:
        blocks.append({
            "object": "block",
            "type": "image",
            "image": {
                "type": "external",
                "external": {"url": logo_url}
            }
        })

    # 회사 브랜드
    blocks.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "type": "text",
                "text": {"content": "부동산 비즈니스 전문가를 위한\n🟦 AIDE INSIGHT | 에이드 인사이트"},
                "annotations": {"bold": True}
            }]
        }
    })

    # 회사 정보
    blocks.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "type": "text",
                "text": {"content": "(주)에이드파트너스 | 대표이사: 송인근 | 사업자등록번호: 345-81-02007\n서울특별시 서초구 강남대로97길 26, 4층\n© 2025 AIDE Partners Co., Ltd. All rights reserved"}
            }]
        }
    })

    return blocks


def create_headlines_blocks(date_str: str, articles_by_category: dict, articles_per_category: int = 5):
    """오늘의 헤드라인 블록 생성"""
    blocks = []

    # 메인 헤더
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    main_heading = f"{dt.year}년 {dt.month}월 {dt.day}일, 오늘의 헤드라인 소식입니다"

    blocks.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "type": "text",
                "text": {"content": main_heading},
                "annotations": {"bold": True}
            }]
        }
    })

    # 구분선
    blocks.append({
        "object": "block",
        "type": "divider",
        "divider": {}
    })

    # 카테고리별 기사
    for cat_code, cat_name in CATEGORY_NAMES.items():
        articles = articles_by_category.get(cat_code, [])
        if not articles:
            continue

        # 카테고리 헤더
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": f"🔹 {cat_name}"}
                }]
            }
        })

        # 기사 목록 (최대 N개)
        for article in articles[:articles_per_category]:
            rich_text = [
                {"type": "text", "text": {"content": article['title']}}
            ]

            # 링크 추가
            rich_text.append({
                "type": "text",
                "text": {"content": " 🔗", "link": {"url": article['url']}}
            })

            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": rich_text}
            })

        # 카테고리 사이 빈 줄
        blocks.append(create_empty_block())

    # 푸터 추가
    footer_blocks = create_footer_blocks(logo_url="https://www.aidepartners.com/images/logo.png")
    blocks.extend(footer_blocks)

    return blocks


def main():
    """메인 프로세스"""
    print("=" * 80)
    print("오늘의 헤드라인 (Today's Headlines) - Notion Upload")
    print("=" * 80)
    print(f"Date: {date.today().isoformat()}\n")

    # DB 연결
    db_url = "sqlite:///" + str(project_root / "aide-data-core" / "aide_dev.db")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 1. 처리된 기사 조회 (오늘 기준)
        articles = db.query(NaverNews).filter(
            NaverNews.status == 'processed',
            NaverNews.cluster_representative == True
        ).order_by(NaverNews.date.desc()).limit(200).all()

        print(f"Found: {len(articles)} processed articles\n")

        # 2. 카테고리별로 분류
        print("Organizing by category...")
        articles_by_category = {cat: [] for cat in CATEGORY_NAMES.keys()}

        for article in articles:
            # classified_categories는 JSON 문자열
            if article.classified_categories:
                try:
                    categories = json.loads(article.classified_categories)

                    # 한글 카테고리명을 코드로 변환
                    for cat_name in categories:
                        for cat_code, name in CATEGORY_NAMES.items():
                            if name == cat_name:
                                articles_by_category[cat_code].append({
                                    'title': article.title,
                                    'url': article.url,
                                    'date': article.date
                                })
                                break
                except:
                    pass

        # 통계 출력
        total_articles = 0
        for cat_code, articles_list in articles_by_category.items():
            if articles_list:
                cat_name = CATEGORY_NAMES[cat_code]
                print(f"  [{cat_name}] {len(articles_list)} articles")
                total_articles += len(articles_list)

        print(f"\nTotal articles: {total_articles}\n")

        # 3. Notion 업로드
        print("Uploading to Notion (Today's Headlines)...")
        today_str = date.today().isoformat()

        # 기존 블록 삭제 (3번째부터)
        delete_blocks_from_page(TODAY_HEADLINES_PAGE_ID, start_index=2)

        # 새 블록 추가
        blocks = create_headlines_blocks(today_str, articles_by_category, articles_per_category=5)
        success = append_blocks_to_page(TODAY_HEADLINES_PAGE_ID, blocks)

        if success:
            print("\n" + "=" * 80)
            print("[SUCCESS] Today's Headlines uploaded!")
            print(f"Page URL: https://www.notion.so/{TODAY_HEADLINES_PAGE_ID.replace('-', '')}")
            print("=" * 80)
        else:
            print("\n[ERROR] Failed to upload blocks")
            return 1

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
