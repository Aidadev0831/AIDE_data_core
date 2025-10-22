#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
전체 파이프라인 타이밍 측정
"""
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent

def measure_script_time(script_name: str, display_name: str):
    """스크립트 실행 시간 측정"""
    script_path = project_root / "scripts" / script_name

    print(f"\n{'='*80}")
    print(f"[{display_name}] Starting...")
    print(f"{'='*80}")

    start_time = time.time()

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300,  # 5분 타임아웃
            cwd=str(project_root)
        )

        end_time = time.time()
        elapsed = end_time - start_time

        print(f"\n[{display_name}] Completed in {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")

        # 출력 요약
        if "SUCCESS" in result.stdout:
            status = "[SUCCESS]"
        elif "ERROR" in result.stdout or result.returncode != 0:
            status = "[FAILED]"
        else:
            status = "[UNKNOWN]"

        print(f"Status: {status}")

        # 주요 통계 추출
        for line in result.stdout.split('\n'):
            if any(keyword in line for keyword in ['Total', 'Found:', 'Saved:', 'Articles:', 'Uploaded:', 'Classified:']):
                print(f"  {line.strip()}")

        return elapsed, status, result.returncode == 0

    except subprocess.TimeoutExpired:
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"\n[{display_name}] TIMEOUT after {elapsed:.2f} seconds")
        return elapsed, "[TIMEOUT]", False

    except Exception as e:
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"\n[{display_name}] ERROR: {e}")
        return elapsed, "[ERROR]", False


def main():
    """메인 타이밍 측정"""
    print("="*80)
    print("Pipeline Timing Measurement")
    print("="*80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = []

    # 1. 크롤링
    elapsed, status, success = measure_script_time(
        "simple_crawl.py",
        "1. Naver News Crawling"
    )
    results.append(("1. Crawling (simple_crawl.py)", elapsed, status))

    if not success:
        print("\n[WARNING] Crawling failed, skipping classification...")
    else:
        # 2. 분류 및 업로드
        elapsed, status, success = measure_script_time(
            "classify_and_upload.py",
            "2. AI Classification & Notion Upload"
        )
        results.append(("2. Classification & Upload (classify_and_upload.py)", elapsed, status))

    # 3. 헤드라인 업로드 (독립적으로 실행 가능)
    elapsed, status, success = measure_script_time(
        "upload_today_headlines.py",
        "3. Today's Headlines Upload"
    )
    results.append(("3. Headlines Upload (upload_today_headlines.py)", elapsed, status))

    # 전체 요약
    print(f"\n{'='*80}")
    print("TIMING SUMMARY")
    print(f"{'='*80}")

    total_time = 0
    for name, elapsed, status in results:
        print(f"{name}")
        print(f"  Time: {elapsed:.2f}s ({elapsed/60:.2f}min)")
        print(f"  Status: {status}")
        print()
        total_time += elapsed

    print(f"{'='*80}")
    print(f"TOTAL PIPELINE TIME: {total_time:.2f}s ({total_time/60:.2f}min)")
    print(f"{'='*80}")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


if __name__ == "__main__":
    main()
