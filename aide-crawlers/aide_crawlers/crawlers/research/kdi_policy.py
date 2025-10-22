"""
KDI Policy Crawler

Crawls policy documents from Korea Development Institute (KDI).
Uses Selenium for JavaScript-rendered content.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from aide_data_core.schemas import KDIPolicyCreate

from ...crawlers.base import BaseCrawler
from ...sinks import AbstractSink


class KDIPolicyCrawler(BaseCrawler):
    """KDI Policy Documents Crawler

    Crawls policy research documents from KDI website.

    URL: https://www.kdi.re.kr/research/subjects_list.jsp

    Example:
        >>> from aide_crawlers.crawlers.research import KDIPolicyCrawler
        >>> from aide_crawlers.sinks import LocalSink
        >>>
        >>> crawler = KDIPolicyCrawler(
        ...     sink=LocalSink(output_dir="data/kdi"),
        ...     headless=True,
        ...     max_pages=2
        ... )
        >>> result = crawler.run()
        >>> crawler.close()
    """

    BASE_URL = "https://www.kdi.re.kr/research/subjects_list.jsp"

    def __init__(
        self,
        sink: AbstractSink,
        headless: bool = True,
        max_pages: int = 2,
        days_back: int = 30,
        database_url: str = None
    ):
        """Initialize KDI Policy crawler

        Args:
            sink: Sink instance for saving data
            headless: Run Chrome in headless mode
            max_pages: Maximum pages to crawl
            days_back: Crawl documents from last N days
            database_url: Database URL for job logging
        """
        super().__init__(
            source_name="kdi_policy",
            sink=sink,
            database_url=database_url
        )

        self.headless = headless
        self.max_pages = max_pages
        self.days_back = days_back

        # Selenium driver (lazy init)
        self.driver = None

    def _init_driver(self):
        """Initialize Selenium Chrome driver"""
        if self.driver is not None:
            return

        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')

        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        self.driver = webdriver.Chrome(options=chrome_options)
        self.logger.info("Selenium driver initialized")

    def crawl(self) -> List[Dict[str, Any]]:
        """Crawl policy documents from KDI website

        Returns:
            List of raw policy documents
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
                self.logger.info(f"Page {page}: {len(recent_items)} items")

                # Stop if no recent items
                if len(recent_items) == 0:
                    self.logger.info("No recent items, stopping")
                    break

                time.sleep(1)  # Be polite

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
            List of items from page
        """
        # Navigate to page
        url = f"{self.BASE_URL}?pg={page}"
        self.driver.get(url)

        # Wait for content to load
        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "list_thesis")))

        time.sleep(2)  # Extra wait for JS rendering

        # Find all items
        items = []
        elements = self.driver.find_elements(By.CSS_SELECTOR, ".list_thesis li")

        for elem in elements:
            try:
                item = self._extract_item(elem)
                if item:
                    items.append(item)
            except Exception as e:
                self.logger.warning(f"Failed to extract item: {str(e)}")

        return items

    def _extract_item(self, element) -> Optional[Dict]:
        """Extract data from single list item

        Args:
            element: Selenium WebElement

        Returns:
            Item dictionary or None
        """
        try:
            # Title and URL
            title_elem = element.find_element(By.CSS_SELECTOR, ".tit a")
            title = title_elem.text.strip()
            detail_url = title_elem.get_attribute('href')

            # Date
            date_elem = element.find_element(By.CLASS_NAME, "date")
            date_text = date_elem.text.strip()

            # Category (if available)
            try:
                category_elem = element.find_element(By.CLASS_NAME, "category")
                category = category_elem.text.strip()
            except:
                category = "정책자료"

            # Description (if available)
            try:
                desc_elem = element.find_element(By.CLASS_NAME, "txt")
                description = desc_elem.text.strip()
            except:
                description = ""

            return {
                'title': title,
                'url': detail_url,
                'date': date_text,
                'category': category,
                'description': description,
            }

        except Exception as e:
            self.logger.warning(f"Extract failed: {str(e)}")
            return None

    def parse(self, raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse raw item to standardized format

        Args:
            raw_item: Raw item from crawl()

        Returns:
            Parsed item dictionary
        """
        try:
            # Parse date
            date_str = raw_item.get('date', '')
            parsed_date = self._format_date(date_str)

            parsed = {
                'title': raw_item.get('title', ''),
                'url': raw_item.get('url', ''),
                'date': parsed_date,
                'source': 'KDI',
                'description': raw_item.get('description', ''),
                'keyword': raw_item.get('category', '정책자료'),
            }

            return parsed

        except Exception as e:
            self.logger.warning(f"Parse failed: {str(e)}")
            return None

    def _parse_date(self, date_str: str) -> datetime:
        """Parse KDI date format to datetime

        Args:
            date_str: Date string like "2025.10.20"

        Returns:
            datetime object
        """
        try:
            # Format: YYYY.MM.DD
            return datetime.strptime(date_str, "%Y.%m.%d")
        except:
            return datetime.now()

    def _format_date(self, date_str: str) -> str:
        """Format date to ISO 8601

        Args:
            date_str: Date string like "2025.10.20"

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
            List of KDIPolicyCreate schema instances
        """
        pydantic_items = []

        for item in items:
            try:
                schema = KDIPolicyCreate(**item)
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
