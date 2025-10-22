#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""간단한 노션 연결 테스트"""
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
env_path = Path(__file__).parent / "aide-crawlers" / ".env"
load_dotenv(env_path)

# 환경변수 확인
api_key = os.getenv("NOTION_API_KEY")
db_id = os.getenv("NOTION_DATABASE_ID")

print("="*80)
print("Notion Setup Check")
print("="*80)

if api_key:
    print(f"[OK] NOTION_API_KEY: {api_key[:10]}...{api_key[-4:]}")
else:
    print("[FAIL] NOTION_API_KEY: Not set")

if db_id:
    print(f"[OK] NOTION_DATABASE_ID: {db_id[:8]}...{db_id[-8:]}")
else:
    print("[FAIL] NOTION_DATABASE_ID: Not set")

print()

if not api_key or not db_id:
    print("환경변수가 설정되지 않았습니다.")
    exit(1)

# 노션 연결 테스트
try:
    from notion_client import Client

    print("Testing Notion connection...")
    client = Client(auth=api_key)

    # 데이터베이스 조회
    database = client.databases.retrieve(database_id=db_id)
    db_title = database.get('title', [{}])[0].get('text', {}).get('content', 'Untitled')
    print(f"[OK] Connected to Notion!")
    print(f"  Database: {db_title}")
    print()

    # 키워드 조회
    response = client.databases.query(database_id=db_id)
    total_items = len(response.get("results", []))
    print(f"[OK] Found {total_items} total items")

    # 활성화된 키워드만 필터링
    active_count = 0
    keywords = []

    for page in response.get("results", []):
        properties = page.get("properties", {})

        # 활성화 확인
        active_prop = properties.get("활성화", {})
        is_active = active_prop.get("checkbox", False)

        if is_active:
            # 키워드 추출
            title_prop = properties.get("키워드", {})
            title_content = title_prop.get("title", [])
            keyword = title_content[0].get("text", {}).get("content", "") if title_content else ""

            if keyword:
                keywords.append(keyword)
                active_count += 1

    print(f"[OK] Active keywords: {active_count}")
    print()

    if keywords:
        print("First 10 keywords:")
        for i, kw in enumerate(keywords[:10], 1):
            print(f"  {i}. {kw}")

        if len(keywords) > 10:
            print(f"  ... and {len(keywords) - 10} more")
    else:
        print("[WARNING] No active keywords found.")
        print("  Please check 'Active' checkbox in Notion database.")

    print()
    print("="*80)
    print("[SUCCESS] Test completed!")
    print("="*80)
    print()
    print("Next step:")
    print("  python scripts/crawling/crawl_naver_api.py")

except ImportError:
    print("[FAIL] notion-client package not installed")
    print("  Install: pip install notion-client")
    exit(1)

except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
