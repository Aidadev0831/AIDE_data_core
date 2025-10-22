#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Preprocess raw news articles from JSON and save to DB

This script reads raw articles (from crawlers),
preprocesses them using aide-preprocessing,
and saves to database.
"""
import sys
import json
from pathlib import Path
from datetime import date

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "aide-preprocessing"))
sys.path.insert(0, str(project_root / "aide-data-core"))

from aide_preprocessing import PreprocessingPipeline
from aide_data_core.database import get_session
from aide_data_core.models import NaverNews


def preprocess_from_json(json_file: str, keyword: str):
    """Preprocess articles from JSON file

    Args:
        json_file: Path to JSON file with raw articles
        keyword: Search keyword used for crawling
    """
    print("=" * 80)
    print("News Article Preprocessing")
    print("=" * 80)
    print(f"Input: {json_file}")
    print(f"Keyword: {keyword}")
    print(f"Date: {date.today().isoformat()}\n")

    # Load raw articles
    with open(json_file, 'r', encoding='utf-8') as f:
        raw_articles = json.load(f)

    print(f"Loaded: {len(raw_articles)} raw articles\n")

    # Initialize pipeline
    session = get_session()
    pipeline = PreprocessingPipeline(session)

    try:
        # Process and save
        total, saved, duplicates = pipeline.process_and_save(
            raw_articles,
            keyword=keyword,
            model_class=NaverNews
        )

        # Statistics
        print(f"\n{'='*80}")
        print("Preprocessing Summary:")
        print(f"  Total: {total} articles")
        print(f"  Saved: {saved} articles")
        print(f"  Duplicates: {duplicates} articles ({duplicates/total*100:.1f}%)")
        print(f"{'='*80}\n")

        print("[SUCCESS] Preprocessing completed!\n")
        return saved

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 0

    finally:
        pipeline.close()


def preprocess_from_list(raw_articles: list, keyword: str):
    """Preprocess articles from list

    Args:
        raw_articles: List of raw article dictionaries
        keyword: Search keyword
    """
    session = get_session()
    pipeline = PreprocessingPipeline(session)

    try:
        total, saved, duplicates = pipeline.process_and_save(
            raw_articles,
            keyword=keyword,
            model_class=NaverNews
        )

        print(f"Preprocessing: {saved}/{total} saved ({duplicates} duplicates)")
        return saved

    finally:
        pipeline.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Preprocess raw news articles")
    parser.add_argument("json_file", help="JSON file with raw articles")
    parser.add_argument("--keyword", "-k", required=True, help="Search keyword")

    args = parser.parse_args()

    saved = preprocess_from_json(args.json_file, args.keyword)
    sys.exit(0 if saved >= 0 else 1)
