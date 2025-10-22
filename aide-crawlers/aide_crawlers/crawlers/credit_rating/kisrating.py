"""
KIS Rating Crawler

Crawls research reports from Korea Investors Service (KIS Rating).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from aide_data_core.schemas import CreditRatingCreate

from ...crawlers.base import BaseCrawler
from ...sinks import AbstractSink


class KISRatingCrawler(BaseCrawler):
    """KIS Rating Research Crawler

    Crawls research reports from KIS Rating website.

    URL: https://www.kisrating.com/research/research_list.do

    Example:
        >>> from aide_crawlers.crawlers.credit_rating import KISRatingCrawler
        >>> from aide_crawlers.sinks import LocalSink
        >>>
        >>> crawler = KISRatingCrawler(
        ...     sink=LocalSink(output_dir="data/kisrating"),
        ...     headless=True,
        ...     max_pages=3
        ... )
        >>> result = crawler.run()
        >>> crawler.close()
    """

    BASE_URL = "https://www.kisrating.com/research/research_list.do"

    def __init__(
        self,
        sink: AbstractSink,
        headless: bool = True,
        max_pages: int = 3,
        days_back: int = 7,
        database_url: str = None
    ):
        """Initialize KIS Rating crawler

        Args:
            sink: Sink instance for saving data
            headless: Run Chrome in headless mode
            max_pages: Maximum pages to crawl
            days_back: Crawl reports from last N days
            database_url: Database URL for job logging
        """
        super().__init__(
            source_name="kisrating",
            sink=sink,
            database_url=database_url
        )

        self.headless = headless
        self.max_pages = max_pages
        self.days_back = days_back

        self.driver = None

    def _init_driver(self):
        """Initialize Selenium driver"""
        if self.driver is not None:
            return

        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')

        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')

        self.driver = webdriver.Chrome(options=chrome_options)
        self.logger.info("Selenium driver initialized")

    def crawl(self) -> List[Dict[str, Any]]:
        """Crawl research reports

        Returns:
            List of raw report items
        """
        self._init_driver()

        all_items = []
        cutoff_date = datetime.now() - timedelta(days=self.days_back)

        for page in range(1, self.max_pages + 1):
            self.logger.info(f"Crawling page {page}/{self.max_pages}")

            try:
                items = self._crawl_page(page)

                # Filter by date
                recent_items = [
                    item for item in items
                    if self._parse_date(item.get('date', '')) >= cutoff_date
                ]

                all_items.extend(recent_items)
                self.logger.info(f"Page {page}: {len(recent_items)} recent items")

                if len(recent_items) == 0:
                    self.logger.info("No recent items, stopping")
                    break

                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Failed to crawl page {page}: {str(e)}")
                break

        self.logger.info(f"Total crawled: {len(all_items)} items")
        return all_items

    def _crawl_page(self, page: int) -> List[Dict]:
        """Crawl single page

        Args:
            page: Page number

        Returns:
            List of items
        """
        # Navigate to page
        url = f"{self.BASE_URL}?pageIndex={page}"
        self.driver.get(url)

        # Wait for table to load
        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "tbl_list")))

        time.sleep(2)

        # Extract items from table
        items = []
        rows = self.driver.find_elements(By.CSS_SELECTOR, ".tbl_list tbody tr")

        for row in rows:
            try:
                item = self._extract_item(row)
                if item:
                    items.append(item)
            except Exception as e:
                self.logger.warning(f"Failed to extract item: {str(e)}")

        return items

    def _extract_item(self, row) -> Optional[Dict]:
        """Extract data from table row

        Args:
            row: Selenium WebElement (tr)

        Returns:
            Item dictionary or None
        """
        try:
            cells = row.find_elements(By.TAG_NAME, "td")

            if len(cells) < 4:
                return None

            # Title and URL
            title_elem = cells[1].find_element(By.TAG_NAME, "a")
            title = title_elem.text.strip()
            detail_url = title_elem.get_attribute('href')

            # Category
            category = cells[0].text.strip()

            # Author
            author = cells[2].text.strip()

            # Date
            date_text = cells[3].text.strip()

            return {
                'title': title,
                'url': detail_url,
                'category': category,
                'author': author,
                'date': date_text,
            }

        except Exception as e:
            self.logger.warning(f"Extract failed: {str(e)}")
            return None

    def parse(self, raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse raw item

        Args:
            raw_item: Raw item from crawl()

        Returns:
            Parsed item dictionary
        """
        try:
            parsed_date = self._format_date(raw_item.get('date', ''))

            parsed = {
                'title': raw_item.get('title', ''),
                'url': raw_item.get('url', ''),
                'date': parsed_date,
                'source': 'KIS Rating',
                'description': f"Category: {raw_item.get('category', '')}, Author: {raw_item.get('author', '')}",
                'keyword': '리서치',
                'category': raw_item.get('category', ''),
                'author': raw_item.get('author', ''),
                'agency': 'kisrating',
            }

            return parsed

        except Exception as e:
            self.logger.warning(f"Parse failed: {str(e)}")
            return None

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime

        Args:
            date_str: Date string like "2025-10-20"

        Returns:
            datetime object
        """
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            try:
                return datetime.strptime(date_str, "%Y.%m.%d")
            except:
                return datetime.now()

    def _format_date(self, date_str: str) -> str:
        """Format date to ISO 8601

        Args:
            date_str: Date string

        Returns:
            ISO 8601 formatted string
        """
        dt = self._parse_date(date_str)
        return dt.isoformat()

    def _convert_to_pydantic(self, items: List[Dict]) -> List[Any]:
        """Convert to Pydantic schemas

        Args:
            items: List of validated dictionaries

        Returns:
            List of schema instances
        """
        pydantic_items = []

        for item in items:
            try:
                schema = CreditRatingCreate(**item)
                pydantic_items.append(schema)
            except Exception as e:
                self.logger.warning(f"Schema conversion failed: {str(e)}")

        return pydantic_items

    def close(self):
        """Close resources"""
        if self.driver:
            self.driver.quit()
            self.logger.info("Selenium driver closed")

        super().close()
