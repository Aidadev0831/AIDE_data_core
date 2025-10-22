#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
오늘의 헤드라인 - Notion 업로드

지면신문 1면 헤드라인만 수집하여 언론사별로 표시
(부동산 뉴스 API 검색과는 별도로 진행)
"""
import sys
import os
import requests
from pathlib import Path
from datetime import datetime, date, timedelta

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "aide-data-core"))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from aide_data_core.models.paper_headlines import PaperHeadline

# Notion 설정
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_API_VERSION = "2022-06-28"
TODAY_HEADLINES_PAGE_ID = os.getenv("NOTION_PAGE_TODAY_HEADLINES", "28c18b63af4d8031afc6ed04b3d056c3")

# 언론사 순서 (종합지 → 경제지)
PRESS_ORDER = [
    "조선일보",
    "중앙일보",
    "동아일보",
    "한겨레",
    "경향신문",
    "매일경제",
    "한국경제",
    "머니투데이",
    "파이낸셜뉴스"
]


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

    # 4개의 빈 줄
    for _ in range(4):
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


def create_headline_blocks(date_str: str, headlines_by_press: dict):
    """
    헤드라인 블록 생성 (언론사별)

    Args:
        date_str: 날짜 (YYYY-MM-DD)
        headlines_by_press: {언론사명: [headline 리스트]}
    """
    blocks = []

    # 헤더
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    heading = f"{dt.year}년 {dt.month}월 {dt.day}일, 오늘의 헤드라인입니다"

    blocks.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "type": "text",
                "text": {"content": heading},
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

    # 언론사별 헤드라인
    for press_name in PRESS_ORDER:
        headlines = headlines_by_press.get(press_name, [])

        if not headlines:
            continue

        # 언론사명 (H3, 이모지 없음)
        blocks.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": press_name},
                    "annotations": {"bold": True}
                }]
            }
        })

        # 헤드라인 목록 (최대 5개)
        for idx, headline in enumerate(headlines[:5]):
            # 첫 번째 기사: 📌 + 볼드
            # 나머지 기사: 일반 텍스트
            if idx == 0:
                rich_text = [
                    {"type": "text", "text": {"content": "📌 "}},
                    {"type": "text", "text": {"content": f"{headline['title']} [{headline.get('source', '출처미상')}, [1]+건] "}, "annotations": {"bold": True}},
                    {"type": "text", "text": {"content": "🔗", "link": {"url": headline['url']}}}
                ]
            else:
                rich_text = [
                    {"type": "text", "text": {"content": f"{headline['title']} [{headline.get('source', '출처미상')}, [1]+건] "}},
                    {"type": "text", "text": {"content": "🔗", "link": {"url": headline['url']}}}
                ]

            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": rich_text}
            })

        # 언론사 사이 구분선
        blocks.append({
            "object": "block",
            "type": "divider",
            "divider": {}
        })

    # 푸터 추가
    footer_blocks = create_footer_blocks(logo_url="https://www.aidepartners.com/images/logo.png")
    blocks.extend(footer_blocks)

    return blocks


def main():
    """메인 프로세스"""
    print("=" * 80)
    print("Upload Today's Headlines to Notion")
    print("=" * 80)
    print(f"Date: {date.today().isoformat()}\n")

    # DB 연결
    db_url = "sqlite:///" + str(project_root / "aide-data-core" / "aide_dev.db")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 1. 오늘 날짜의 지면신문 1면 헤드라인 조회
        today = date.today()

        # 오늘 또는 최근 3일 이내 데이터 조회 (데이터가 없을 경우 대비)
        start_date = today - timedelta(days=3)

        headlines = db.query(PaperHeadline).filter(
            PaperHeadline.date >= start_date,
            PaperHeadline.status == 'raw'
        ).order_by(PaperHeadline.date.desc(), PaperHeadline.newspaper).all()

        print(f"Found: {len(headlines)} headlines\n")

        if len(headlines) == 0:
            print("No headlines to upload.")
            db.close()
            return 0

        # 2. 언론사별로 그룹화
        headlines_by_press = {}
        latest_date = None

        for headline in headlines:
            press_name = headline.newspaper

            if press_name not in headlines_by_press:
                headlines_by_press[press_name] = []

            headlines_by_press[press_name].append({
                'title': headline.title,
                'url': headline.url,
                'date': headline.date.strftime("%Y-%m-%d")
            })

            # 최신 날짜 추적
            if latest_date is None or headline.date > latest_date:
                latest_date = headline.date

        # 최신 날짜만 사용 (여러 날짜가 섞여있을 경우)
        if latest_date:
            headlines_by_press_filtered = {}
            for press_name, press_headlines in headlines_by_press.items():
                filtered = [h for h in press_headlines if h['date'] == latest_date.strftime("%Y-%m-%d")]
                if filtered:
                    headlines_by_press_filtered[press_name] = filtered
            headlines_by_press = headlines_by_press_filtered
            date_str = latest_date.strftime("%Y-%m-%d")
        else:
            date_str = today.isoformat()

        # 통계 출력
        print("Headlines by Press:")
        for press_name in PRESS_ORDER:
            count = len(headlines_by_press.get(press_name, []))
            if count > 0:
                print(f"  {press_name}: {count}개")

        # 3. Notion 업로드
        print(f"\nUploading to Notion (Date: {date_str})...\n")

        # 기존 블록 삭제 (3번째부터)
        delete_blocks_from_page(TODAY_HEADLINES_PAGE_ID, start_index=2)

        # 새 블록 추가
        blocks = create_headline_blocks(date_str, headlines_by_press)
        append_blocks_to_page(TODAY_HEADLINES_PAGE_ID, blocks)

        print("\n" + "=" * 80)
        print("[SUCCESS] Upload completed!")
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
