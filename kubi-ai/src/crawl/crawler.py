"""Web crawler using Playwright + Trafilatura."""

import asyncio
import logging
from typing import Optional
from urllib.parse import urlparse

import trafilatura
from bs4 import BeautifulSoup

from src.models.schemas import CrawlMetadata

logger = logging.getLogger(__name__)


class CrawlResult:
    def __init__(
        self,
        url: str = "",
        title: str = "",
        text: str = "",
        html: str = "",
        metadata: Optional[CrawlMetadata] = None,
    ):
        self.url = url
        self.title = title
        self.text = text
        self.html = html
        self.metadata = metadata or CrawlMetadata()


class WebCrawler:

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 15000,
        max_pages: int = 10,
        max_concurrent: int = 5,
    ):
        self.headless = headless
        self.timeout = timeout
        self.max_pages = max_pages
        self.max_concurrent = max_concurrent
        self._browser = None
        self._playwright = None
        self._browser_lock = asyncio.Lock()

    async def _ensure_browser(self):
        if self._browser is not None:
            return
        async with self._browser_lock:
            if self._browser is not None:
                return
            try:
                from playwright.async_api import async_playwright
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=self.headless,
                    args=["--no-sandbox", "--disable-setuid-sandbox"],
                )
            except Exception as e:
                logger.warning(f"Playwright not available: {e}")

    async def crawl(self, url: str) -> CrawlResult:
        html_content = ""

        await self._ensure_browser()
        if self._browser:
            try:
                html_content = await self._crawl_with_playwright(url)
            except Exception as e:
                logger.warning(f"Playwright crawl failed for {url}: {e}")

        if not html_content:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=self.timeout / 1000) as client:
                    resp = await client.get(url, follow_redirects=True, headers={
                        "User-Agent": "Mozilla/5.0 (compatible; KubiBot/1.0; +https://kubi.ai)"
                    })
                    resp.raise_for_status()
                    html_content = resp.text
            except Exception as e:
                logger.error(f"HTTP fetch failed for {url}: {e}")
                return CrawlResult(url=url)

        text = trafilatura.extract(
            html_content, include_comments=False, include_tables=True,
            include_links=False, output_format="txt",
        ) or ""

        metadata = self._extract_metadata(url, html_content, text)
        title = metadata.title
        if not title:
            soup = BeautifulSoup(html_content, "lxml")
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else ""

        return CrawlResult(url=url, title=title, text=text, html=html_content, metadata=metadata)

    async def crawl_batch(self, urls: list[str]) -> list[CrawlResult]:
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def _crawl_one(url: str) -> CrawlResult:
            async with semaphore:
                return await self.crawl(url)

        tasks = [_crawl_one(url) for url in urls[:self.max_pages]]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [
            r if isinstance(r, CrawlResult) else CrawlResult()
            for r in results
        ]

    async def _crawl_with_playwright(self, url: str) -> str:
        page = await self._browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=self.timeout)
            return await page.content()
        finally:
            await page.close()

    def _extract_metadata(self, url: str, html: str, text: str) -> CrawlMetadata:
        soup = BeautifulSoup(html, "lxml")
        domain = urlparse(url).netloc

        meta_tags = {}
        for tag in soup.find_all("meta"):
            name = tag.get("name", tag.get("property", ""))
            content = tag.get("content", "")
            if name and content:
                meta_tags[name.lower()] = content

        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        return CrawlMetadata(
            url=url,
            title=title,
            description=meta_tags.get("description", meta_tags.get("og:description", "")),
            author=meta_tags.get("author", meta_tags.get("article:author")),
            published_date=meta_tags.get("article:published_time", meta_tags.get("date")),
            domain=domain,
            word_count=len(text.split()) if text else 0,
            language=meta_tags.get("language", meta_tags.get("og:locale", "")),
        )

    async def close(self):
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
