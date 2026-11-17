"""Base crawler definition and interface."""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
import httpx
from config.settings import settings
from db.models import JobItem
from utils.logger import logger


class BaseCrawler(ABC):
    name: str = "base"

    def __init__(self, timeout: Optional[int] = None):
        self.timeout = timeout or settings.REQUEST_TIMEOUT
        self.headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

    def get_client(self) -> httpx.Client:
        """Creates an HTTPX client with sensible defaults."""
        return httpx.Client(
            headers=self.headers,
            timeout=self.timeout,
            follow_redirects=True,
            verify=False  # Avoid potential SSL certificate issues on some local VN gateways
        )

    def fetch_html_http(self, url: str, params: Optional[dict] = None) -> Tuple[int, str]:
        """Fetches a URL via HTTPX and returns (status_code, html_text)."""
        try:
            with self.get_client() as client:
                resp = client.get(url, params=params)
                return resp.status_code, resp.text
        except Exception as e:
            logger.debug(f"[{self.name}] HTTP fetch failed for {url}: {e}")
            return 0, ""

    def fetch_html_playwright(self, url: str, wait_ms: int = 2500) -> Tuple[int, str]:
        """Renders a page with headless Chromium via Playwright and returns (status_code, html_text)."""
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
                )
                context = browser.new_context(
                    user_agent=self.headers["User-Agent"],
                    viewport={"width": 1280, "height": 800}
                )
                page = context.new_page()
                resp = page.goto(url, wait_until="domcontentloaded", timeout=self.timeout * 1000)
                page.wait_for_timeout(wait_ms)
                status = resp.status if resp else 0
                content = page.content()
                browser.close()
                return status, content
        except Exception as e:
            logger.debug(f"[{self.name}] Playwright fetch failed for {url}: {e}")
            return 0, ""

    @abstractmethod
    def search(self, keyword: str, limit: int = 20, location: Optional[str] = None) -> List[JobItem]:
        """
        Crawls and parses jobs for the given keyword and optional location.
        Must return a list of JobItem objects.
        """
        pass
