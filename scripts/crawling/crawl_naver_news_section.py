#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
네이버 뉴스 부동산 섹션 크롤링 (오늘 기사만)

섹션 스크래핑 + 전처리:
1. '경제 > 부동산' 섹션 HTML 스크래핑
2. aide-preprocessing을 통한 전처리 및 DB 저장
"""
import sys
import os
import time
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict

import requests
from bs4 import BeautifulSoup

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "aide-preprocessing"))
sys.path.insert(0, str(project_root / "aide-data-core"))

from dotenv import load_dotenv
load_dotenv(project_root / "aide-data-core" / ".env")

from aide_preprocessing import PreprocessingPipeline
from aide_data_core.models import get_engine, get_session, NaverNews


def parse_relative_time(time_str: str) -> datetime:
    """상대 시간을 datetime으로 변환"""
    now = datetime.now()
    if '분전' in time_str:
        minutes = int(time_str.replace('분전', ''))
        return now - timedelta(minutes=minutes)
    elif '시간전' in time_str:
        hours = int(time_str.replace('시간전', ''))
        return now - timedelta(hours=hours)
    elif '일전' in time_str:
        days = int(time_str.replace('일전', ''))
        return now - timedelta(days=days)
    return now


def random_delay(min_sec: float = 0.3, max_sec: float = 1.2):
    """랜덤 지연 시간 (사람처럼 보이도록)"""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def get_random_headers(referer: str = "https://news.naver.com") -> dict:
    """랜덤 User-Agent 헤더 생성"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]
    return {
        "User-Agent": random.choice(user_agents),
        "Referer": referer,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }


def crawl_section_today() -> List[Dict]:
    """
    네이버 뉴스 '경제 > 부동산' 섹션 크롤링 (오늘 기사만)

    Returns:
        List[Dict]: 크롤링된 기사 정보 리스트 (Naver API 형식)
    """
    base_url = "https://news.naver.com/section/template/SECTION_ARTICLE_LIST_FOR_LATEST"

    # 경제 > 부동산
    sid1 = "101"  # 경제
    sid2 = "260"  # 부동산

    articles = []

    # 오늘 날짜
    today = datetime.now().strftime("%Y%m%d")

    print(f"=" * 80)
    print(f"네이버 뉴스 '경제 > 부동산' 섹션 크롤링")
    print(f"=" * 80)
    print(f"크롤링 날짜: {today} (오늘 기사만)")
    print()

    try:
        # 오늘 기사만 크롤링 (1시~24시)
        for hour in range(1, 25):
            next_value = f"{today}{hour:02}000000000"
            params = {
                "sid": sid1,
                "sid2": sid2,
                "pageNo": 1,
                "date": today,
                "next": next_value,
            }

            # 랜덤 헤더 생성
            headers = get_random_headers(referer="https://news.naver.com")

            # API 요청
            res = requests.get(base_url, headers=headers, params=params, verify=False, timeout=10)

            if res.status_code != 200:
                print(f"[{hour:02}시] HTTP {res.status_code} - 건너뛰기")
                continue

            data = res.json()
            html = data.get('renderedComponent', {}).get('SECTION_ARTICLE_LIST_FOR_LATEST', '')

            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            article_items = soup.select('li.sa_item')

            hour_count = 0

            for item in article_items:
                try:
                    # 기본 정보
                    title_elem = item.find('strong', class_='sa_text_strong')
                    title = title_elem.text.strip() if title_elem else ''

                    link_elem = item.find('a', class_='sa_text_title')
                    link = link_elem.get('href', '') if link_elem else ''

                    lede_elem = item.find('div', class_='sa_text_lede')
                    lede = lede_elem.text.strip() if lede_elem else ''

                    press_elem = item.find('div', class_='sa_text_press')
                    press = press_elem.text.strip() if press_elem else ''

                    date_elem = item.find('div', class_='sa_text_datetime')
                    date_time = date_elem.text.strip() if date_elem else ''

                    if not title or not link:
                        continue

                    # 상대 시간을 절대 시간으로 변환
                    if '시간전' in date_time or '분전' in date_time or '일전' in date_time:
                        dt = parse_relative_time(date_time)
                        pub_date_str = dt.strftime('%a, %d %b %Y %H:%M:%S +0900')
                    else:
                        # YYYY.MM.DD. HH:MM 형식 → RFC-822 형식
                        try:
                            dt = datetime.strptime(date_time, '%Y.%m.%d. %H:%M')
                            pub_date_str = dt.strftime('%a, %d %b %Y %H:%M:%S +0900')
                        except:
                            pub_date_str = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0900')

                    # Naver API 형식으로 변환
                    article = {
                        'title': title,  # 이미 정제된 텍스트 (HTML 태그 없음)
                        'description': lede,
                        'url': link,
                        'originallink': link,
                        'link': link,
                        'pubDate': pub_date_str,
                    }
                    articles.append(article)
                    hour_count += 1

                except Exception as e:
                    continue

            if hour_count > 0:
                print(f"[{hour:02}시] {hour_count}개 기사 수집")

            # 랜덤 지연 (0.3~1.2초)
            random_delay(0.3, 1.2)

    except Exception as e:
        print(f"\n[ERROR] 크롤링 오류: {e}")
        import traceback
        traceback.print_exc()

    print()
    print(f"총 {len(articles)}개 기사 크롤링 완료 (오늘 기사)")
    return articles


def main():
    """메인 프로세스: 크롤링 + 전처리"""
    print()
    print("=" * 80)
    print("네이버 뉴스 부동산 섹션 크롤러 (오늘 기사만)")
    print("=" * 80)
    print()

    # Initialize preprocessing pipeline
    db_path = str(project_root / "aide-data-core" / "aide_dev.db").replace("\\", "/")
    db_url = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")
    engine = get_engine(db_url)
    session = get_session(engine)
    pipeline = PreprocessingPipeline(session)

    try:
        # Step 1: Crawling (섹션 스크래핑)
        articles = crawl_section_today()

        if not articles:
            print("크롤링된 기사가 없습니다.")
            return 0

        # Step 2: Preprocessing (전처리 + 중복 확인 + DB 저장)
        print()
        print("=" * 80)
        print("전처리 및 DB 저장 중...")
        print("=" * 80)

        total, saved, duplicates = pipeline.process_and_save(
            articles,
            keyword='경제>부동산',
            model_class=NaverNews
        )

        print(f"\n총 {total}개 크롤링")
        print(f"  - 저장: {saved}개")
        print(f"  - 중복: {duplicates}개 ({duplicates/total*100:.1f}%)")

        print()
        print("=" * 80)
        print("[SUCCESS] 부동산 섹션 크롤링 완료")
        print("=" * 80)

        return saved

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 0

    finally:
        pipeline.close()


if __name__ == "__main__":
    saved = main()
    sys.exit(0 if saved >= 0 else 1)
