"""
Naver News API Crawler

Crawls news articles using Naver Search API.
"""

from typing import List, Dict, Any, Optional
import os
import requests
from datetime import datetime

from aide_data_core.schemas import NaverNewsCreate

from ...crawlers.base import BaseCrawler
from ...sinks import AbstractSink


class NaverNewsAPICrawler(BaseCrawler):
    """Naver News Search API Crawler

    Uses Naver Search API to crawl news articles by keywords.

    Environment Variables:
        NAVER_CLIENT_ID: Naver API client ID
        NAVER_CLIENT_SECRET: Naver API client secret

    Example:
        >>> from aide_crawlers.crawlers.naver import NaverNewsAPICrawler
        >>> from aide_crawlers.sinks import LocalSink
        >>>
        >>> crawler = NaverNewsAPICrawler(
        ...     keywords=["PF", "부동산"],
        ...     sink=LocalSink(output_dir="data", format="json")
        ... )
        >>> result = crawler.run()
        >>> crawler.close()
    """

    API_URL = "https://openapi.naver.com/v1/search/news.json"

    def __init__(
        self,
        keywords: List[str],
        sink: AbstractSink,
        client_id: str = None,
        client_secret: str = None,
        display: int = 100,
        database_url: str = None
    ):
        """Initialize Naver News API crawler

        Args:
            keywords: List of search keywords
            sink: Sink instance for saving data
            client_id: Naver API client ID (default: from env)
            client_secret: Naver API client secret (default: from env)
            display: Number of results per keyword (max 100)
            database_url: Database URL for job logging
        """
        super().__init__(
            source_name="naver_news_api",
            sink=sink,
            database_url=database_url
        )

        self.keywords = keywords
        self.client_id = client_id or os.getenv("NAVER_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("NAVER_CLIENT_SECRET")
        self.display = min(display, 100)  # API max is 100

        if not self.client_id or not self.client_secret:
            raise ValueError("Naver API credentials not provided")

        self.logger.info(f"Initialized with {len(keywords)} keywords, display={display}")

    def crawl(self) -> List[Dict[str, Any]]:
        """Crawl news from Naver Search API

        Returns:
            List of raw news items from API
        """
        all_items = []

        for keyword in self.keywords:
            self.logger.info(f"Searching for keyword: {keyword}")

            try:
                items = self._search_keyword(keyword)
                all_items.extend(items)
                self.logger.info(f"Found {len(items)} items for '{keyword}'")

            except Exception as e:
                self.logger.error(f"Failed to search '{keyword}': {str(e)}")

        self.logger.info(f"Total crawled: {len(all_items)} items")
        return all_items

    def _search_keyword(self, keyword: str) -> List[Dict]:
        """Search news by single keyword

        Args:
            keyword: Search keyword

        Returns:
            List of news items from API response
        """
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }

        params = {
            "query": keyword,
            "display": self.display,
            "start": 1,
            "sort": "date"  # Sort by date (newest first)
        }

        response = requests.get(
            self.API_URL,
            headers=headers,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        # Add keyword to each item
        items = data.get('items', [])
        for item in items:
            item['keyword'] = keyword

        return items

    def parse(self, raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse raw API response to standardized format

        API Response Format:
        {
            "title": "HTML title",
            "originallink": "original URL",
            "link": "naver redirect URL",
            "description": "HTML description",
            "pubDate": "Mon, 20 Oct 2025 12:00:00 +0900",
            "keyword": "PF"  # Added by crawler
        }

        Args:
            raw_item: Raw item from Naver API

        Returns:
            Parsed item dictionary
        """
        try:
            # Use originallink if available, fallback to link
            url = raw_item.get('originallink') or raw_item.get('link')

            if not url:
                return None

            # Parse pubDate (RFC 1123 format)
            pub_date_str = raw_item.get('pubDate', '')
            date = self._parse_pub_date(pub_date_str)

            parsed = {
                'keyword': raw_item.get('keyword', 'unknown'),
                'title': self._strip_html(raw_item.get('title', '')),
                'source': 'Naver News',  # Will be normalized later
                'url': url,
                'date': date,
                'description': self._strip_html(raw_item.get('description', '')),
            }

            return parsed

        except Exception as e:
            self.logger.warning(f"Parse failed for item: {str(e)}")
            return None

    def _parse_pub_date(self, pub_date_str: str) -> str:
        """Parse RFC 1123 date format to ISO 8601

        Args:
            pub_date_str: Date string like "Mon, 20 Oct 2025 12:00:00 +0900"

        Returns:
            ISO 8601 formatted date string
        """
        try:
            # Parse RFC 1123 format
            dt = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
            return dt.isoformat()
        except Exception:
            # Fallback to current time
            return datetime.now().isoformat()

    def _strip_html(self, text: str) -> str:
        """Strip HTML tags from text

        Args:
            text: Text with HTML tags

        Returns:
            Plain text
        """
        import re

        if not text:
            return ""

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Decode HTML entities
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        text = text.replace('&nbsp;', ' ')

        return text.strip()

    def _convert_to_pydantic(self, items: List[Dict]) -> List[NaverNewsCreate]:
        """Convert validated dicts to NaverNewsCreate schemas

        Args:
            items: List of validated item dictionaries

        Returns:
            List of NaverNewsCreate instances
        """
        pydantic_items = []

        for item in items:
            try:
                schema = NaverNewsCreate(**item)
                pydantic_items.append(schema)
            except Exception as e:
                self.logger.warning(f"Failed to create schema: {str(e)}")

        return pydantic_items
