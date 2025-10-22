#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
네이버 지면신문 1면 헤드라인 크롤러

주요 기능:
- 지면신문 1면 기사만 수집 (9개 언론사)
- SQLite 캐싱으로 빠른 재실행
- PaperHeadline 모델로 저장
- 자동 중복 제거
"""
import os
import sys
import time
import random
import hashlib
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "aide-data-core"))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from aide_data_core.models.paper_headlines import PaperHeadline

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NaverPaperCrawler:
    """네이버 지면신문 1면 크롤러"""

    # 언론사 OID 매핑
    PRESS_OID_MAP = {
        # 종합지
        "조선일보": "023",
        "중앙일보": "025",
        "동아일보": "020",
        "한겨레": "028",
        "경향신문": "032",
        # 경제지
        "매일경제": "009",
        "한국경제": "015",
        "머니투데이": "008",
        "파이낸셜뉴스": "014"
    }

    # OID -> 언론사명 역매핑
    OID_PRESS_MAP = {v: k for k, v in PRESS_OID_MAP.items()}

    # 기본 URL 템플릿
    BASE_URL_TEMPLATE = "https://news.naver.com/main/list.naver?mode=LPOD&mid=sec&oid={oid}&listType=paper&date={date}"

    def __init__(self, cache_dir: str = None):
        """
        Args:
            cache_dir: 캐시 디렉토리 경로 (기본값: data/cache/paper)
        """
        if cache_dir is None:
            cache_dir = project_root / "data" / "cache" / "paper"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 캐시 DB 초기화
        self.cache_db_path = self.cache_dir / "paper_cache.db"
        self._init_cache_db()

        # requests 세션
        self.session = requests.Session()

        # User-Agent 풀
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
        ]

        # DB 연결
        db_url = "sqlite:///" + str(project_root / "aide-data-core" / "aide_dev.db")
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

        # 통계
        self.stats = {
            "total_crawled": 0,
            "total_saved": 0,
            "duplicates": 0
        }

        logger.info(f"NaverPaperCrawler 초기화 완료")
        logger.info(f"캐시: {self.cache_db_path}")
        logger.info(f"DB: {db_url}")

    def _init_cache_db(self):
        """캐시 DB 초기화"""
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_cache (
                cache_key TEXT PRIMARY KEY,
                oid TEXT NOT NULL,
                date TEXT NOT NULL,
                html_content TEXT NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                article_count INTEGER
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_oid_date
            ON paper_cache(oid, date)
        """)

        conn.commit()
        conn.close()

    def _get_random_headers(self) -> Dict[str, str]:
        """랜덤 헤더 생성"""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

    def _random_sleep(self, min_sec: float = 0.7, max_sec: float = 1.5):
        """랜덤 슬립 (속도 제한)"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    def _generate_cache_key(self, oid: str, date: str) -> str:
        """캐시 키 생성"""
        raw = f"{oid}_{date}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _get_from_cache(self, oid: str, date: str) -> Optional[str]:
        """캐시에서 HTML 조회"""
        cache_key = self._generate_cache_key(oid, date)

        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT html_content FROM paper_cache WHERE cache_key = ?",
                (cache_key,)
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                logger.debug(f"캐시 히트: {self.OID_PRESS_MAP.get(oid, oid)} {date}")
                return row[0]

            return None

        except Exception as e:
            logger.warning(f"캐시 조회 실패: {e}")
            return None

    def _save_to_cache(self, oid: str, date: str, html_content: str, article_count: int):
        """캐시에 HTML 저장"""
        cache_key = self._generate_cache_key(oid, date)

        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO paper_cache
                (cache_key, oid, date, html_content, article_count)
                VALUES (?, ?, ?, ?, ?)
            """, (cache_key, oid, date, html_content, article_count))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.warning(f"캐시 저장 실패: {e}")

    def _fetch_with_retry(self, url: str, max_retries: int = 3) -> Optional[str]:
        """재시도 로직이 포함된 HTTP 요청"""
        for attempt in range(max_retries):
            try:
                headers = self._get_random_headers()
                response = self.session.get(url, headers=headers, timeout=10)

                if response.status_code == 200:
                    return response.text

                if response.status_code == 429 or response.status_code >= 500:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"HTTP {response.status_code}, {wait_time:.1f}초 대기...")
                    time.sleep(wait_time)
                    continue

                logger.error(f"HTTP {response.status_code}: {url}")
                return None

            except requests.exceptions.Timeout:
                logger.warning(f"타임아웃 (시도 {attempt + 1}/{max_retries})")
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                logger.error(f"네트워크 오류: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    return None

        logger.error(f"최대 재시도 초과: {url}")
        return None

    def _parse_paper_list(self, html: str, oid: str, date: str) -> List[Dict]:
        """지면신문 HTML 파싱 (1면만)"""
        try:
            soup = BeautifulSoup(html, "html.parser")
            articles = []

            press_name = self.OID_PRESS_MAP.get(oid, f"OID{oid}")
            formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:]}"

            # 지면 섹션 찾기
            list_body = soup.find("div", class_="list_body")
            if not list_body:
                logger.warning(f"{press_name} - list_body를 찾을 수 없습니다")
                return []

            # 섹션 제목 찾기
            section_titles = list_body.find_all("h4", class_="paper_h4")

            for section_title_elem in section_titles:
                section_title = section_title_elem.get_text(strip=True)

                # 1면 또는 A1면만 크롤링
                if not (section_title == "1면" or section_title == "A1면"):
                    continue

                # 해당 섹션의 기사 목록
                ul_section = section_title_elem.find_next_sibling("ul")
                if not ul_section:
                    continue

                article_items = ul_section.find_all("li")

                for item in article_items:
                    try:
                        dt = item.find("dt")
                        if not dt:
                            continue

                        # 제목과 링크
                        title_elem = dt.find("a")
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        if not title:
                            continue

                        article_url = title_elem.get("href", "")
                        if article_url and not article_url.startswith("http"):
                            article_url = f"https://news.naver.com{article_url}"

                        # 부제목/요약
                        summary_elem = dt.find("span", class_="lede")
                        summary = summary_elem.get_text(strip=True) if summary_elem else ""

                        # content_hash 생성 (URL 기반)
                        content_hash = hashlib.md5(article_url.encode()).hexdigest()

                        article = {
                            "title": title,
                            "url": article_url,
                            "date": formatted_date,
                            "newspaper": press_name,
                            "description": summary,
                            "content_hash": content_hash,
                            "status": "raw"
                        }

                        articles.append(article)

                    except Exception as e:
                        logger.debug(f"기사 파싱 오류: {e}")
                        continue

            logger.info(f"{press_name} {formatted_date}: {len(articles)}개 기사 파싱")
            return articles

        except Exception as e:
            logger.error(f"HTML 파싱 오류: {e}")
            return []

    def _save_to_db(self, articles: List[Dict]) -> int:
        """DB에 저장"""
        if not articles:
            return 0

        db = self.Session()
        saved_count = 0

        try:
            for article_data in articles:
                # 중복 확인 (URL 기반)
                existing = db.query(PaperHeadline).filter(
                    PaperHeadline.url == article_data['url']
                ).first()

                if existing:
                    self.stats["duplicates"] += 1
                    continue

                # 날짜 파싱
                date_obj = datetime.strptime(article_data['date'], "%Y-%m-%d")

                # 새 레코드 생성
                headline = PaperHeadline(
                    title=article_data['title'],
                    url=article_data['url'],
                    date=date_obj,
                    newspaper=article_data['newspaper'],
                    description=article_data['description'],
                    content_hash=article_data['content_hash'],
                    status='raw'
                )

                db.add(headline)
                saved_count += 1

            db.commit()
            self.stats["total_saved"] += saved_count
            logger.info(f"DB 저장: {saved_count}개 (중복: {len(articles) - saved_count}개)")

        except Exception as e:
            logger.error(f"DB 저장 오류: {e}")
            db.rollback()

        finally:
            db.close()

        return saved_count

    def crawl_paper_by_oid(self, oid: str, date: str, use_cache: bool = True) -> List[Dict]:
        """특정 언론사의 지면신문 크롤링"""
        press_name = self.OID_PRESS_MAP.get(oid, f"OID{oid}")
        logger.info(f"크롤링 시작: {press_name} ({oid}) - {date}")

        # 캐시 확인
        if use_cache:
            cached_html = self._get_from_cache(oid, date)
            if cached_html:
                return self._parse_paper_list(cached_html, oid, date)

        # URL 생성
        url = self.BASE_URL_TEMPLATE.format(oid=oid, date=date)

        # HTTP 요청
        html = self._fetch_with_retry(url)
        if not html:
            logger.error(f"크롤링 실패: {press_name} {date}")
            return []

        # 파싱
        articles = self._parse_paper_list(html, oid, date)
        self.stats["total_crawled"] += len(articles)

        # 캐시 저장
        if articles:
            self._save_to_cache(oid, date, html, len(articles))

        # 속도 제한
        self._random_sleep()

        return articles

    def crawl_all_papers(
        self,
        date: Optional[str] = None,
        press_list: Optional[List[str]] = None,
        use_cache: bool = True,
        save_to_db: bool = True
    ) -> Dict[str, List[Dict]]:
        """
        모든 언론사 지면신문 일괄 크롤링

        Args:
            date: 날짜 YYYYMMDD (None이면 오늘)
            press_list: 수집할 언론사 리스트 (None이면 전체)
            use_cache: 캐시 사용 여부
            save_to_db: DB 저장 여부

        Returns:
            {언론사명: [기사 목록]} 딕셔너리
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")

        if press_list is None:
            press_list = list(self.PRESS_OID_MAP.keys())

        logger.info("=" * 80)
        logger.info(f"전체 크롤링 시작: {date} ({len(press_list)}개 언론사)")
        logger.info("=" * 80)

        results = {}

        for press_name in press_list:
            oid = self.PRESS_OID_MAP.get(press_name)

            if not oid:
                logger.warning(f"알 수 없는 언론사: {press_name}")
                continue

            try:
                articles = self.crawl_paper_by_oid(oid, date, use_cache)
                results[press_name] = articles

                # DB 저장
                if save_to_db and articles:
                    self._save_to_db(articles)

            except Exception as e:
                logger.error(f"{press_name} 크롤링 오류: {e}")
                results[press_name] = []

        # 통계
        logger.info("=" * 80)
        logger.info(f"크롤링 완료: {len([r for r in results.values() if r])}/{len(press_list)} 성공")
        logger.info(f"총 크롤링: {self.stats['total_crawled']}개")
        logger.info(f"DB 저장: {self.stats['total_saved']}개")
        logger.info(f"중복: {self.stats['duplicates']}개")
        logger.info("=" * 80)

        return results


def main():
    """메인 실행"""
    print("=" * 80)
    print("네이버 지면신문 1면 헤드라인 크롤러")
    print("=" * 80)
    print(f"날짜: {datetime.now().strftime('%Y-%m-%d')}\n")

    crawler = NaverPaperCrawler()

    # 오늘 날짜
    today = datetime.now().strftime("%Y%m%d")

    # 전체 언론사 크롤링
    results = crawler.crawl_all_papers(today, save_to_db=True)

    # 결과 출력
    print("\n" + "=" * 80)
    print("크롤링 결과:")
    print("=" * 80)

    for press_name, articles in results.items():
        if articles:
            print(f"  {press_name}: {len(articles)}개")
            if articles:
                print(f"    ├─ 1위: {articles[0]['title'][:50]}...")

    print("\n" + "=" * 80)
    print("[SUCCESS] 크롤링 및 DB 저장 완료!")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
