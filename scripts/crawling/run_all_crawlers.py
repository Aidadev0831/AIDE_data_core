#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
통합 크롤링 실행 스크립트
"""
import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent

def main():
    print("\n통합 크롤링 시작\n")
    
    # 1. 섹션 크롤링
    print("[1/2] 섹션 크롤링 실행...")
    subprocess.run([sys.executable, str(project_root / "scripts" / "crawl_naver_news_section.py")])
    
    # 2. API 크롤링
    print("\n[2/2] API 크롤링 실행...")
    subprocess.run([sys.executable, str(project_root / "scripts" / "crawl_naver_api.py")])
    
    print("\n통합 크롤링 완료!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
