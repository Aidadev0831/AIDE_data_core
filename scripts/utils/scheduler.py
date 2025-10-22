#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
자동 스케줄링 스크립트 (11PM, 8AM)
"""
import sys
import os
import schedule
import time
import subprocess
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent


def run_full_pipeline():
    """전체 파이프라인 실행"""
    print("\n" + "=" * 80)
    print(f"파이프라인 실행 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")

    scripts_to_run = [
        ("run_all_crawlers.py", "크롤링 (섹션 + API)"),
        ("classify_and_upload.py", "분류 및 카테고리별 Notion 업로드"),
        ("upload_today_headlines.py", "오늘의 헤드라인 업로드"),
    ]

    for script_name, description in scripts_to_run:
        print(f"\n{'='*80}")
        print(f"실행: {description}")
        print(f"스크립트: {script_name}")
        print(f"{'='*80}\n")

        script_path = project_root / "scripts" / script_name

        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(project_root),
                capture_output=False,
                text=True,
                timeout=3600  # 1시간 타임아웃
            )

            if result.returncode == 0:
                print(f"\n[SUCCESS] {description} 완료")
            else:
                print(f"\n[WARNING] {description} 실패 (exit code: {result.returncode})")

        except subprocess.TimeoutExpired:
            print(f"\n[ERROR] {description} 타임아웃 (1시간 초과)")
        except Exception as e:
            print(f"\n[ERROR] {description} 실행 중 오류: {e}")

    print("\n" + "=" * 80)
    print(f"파이프라인 실행 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")


def schedule_jobs():
    """스케줄 설정"""
    # 저녁 11시 실행
    schedule.every().day.at("23:00").do(run_full_pipeline)

    # 아침 8시 실행
    schedule.every().day.at("08:00").do(run_full_pipeline)

    print("=" * 80)
    print("스케줄러 시작")
    print("=" * 80)
    print()
    print("스케줄:")
    print("  - 매일 오후 11시 (23:00)")
    print("  - 매일 오전  8시 (08:00)")
    print()
    print("실행 내용:")
    print("  1. 부동산 섹션 크롤링")
    print("  2. API 키워드 크롤링 (insight_test 키워드)")
    print("  3. 분류 및 카테고리별 Notion 업로드")
    print("  4. 오늘의 헤드라인 업로드")
    print()
    print("=" * 80)
    print()

    # 다음 실행 시간 출력
    next_run = schedule.next_run()
    if next_run:
        print(f"다음 실행 예정: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("스케줄러 실행 중... (Ctrl+C로 중단)")
    print("=" * 80)
    print()


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="뉴스 크롤링 자동 스케줄러")
    parser.add_argument("--test", action="store_true", help="즉시 1회 실행 (테스트용)")
    args = parser.parse_args()

    if args.test:
        print("\n[TEST MODE] 파이프라인 즉시 실행\n")
        run_full_pipeline()
        return 0

    # 정상 스케줄링 모드
    schedule_jobs()

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 체크
    except KeyboardInterrupt:
        print("\n\n스케줄러 종료")
        return 0


if __name__ == "__main__":
    sys.exit(main())
