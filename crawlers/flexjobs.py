"""FlexJobs remote job board crawler with anti-bot detection handling."""
import urllib.parse
from typing import List, Optional
from bs4 import BeautifulSoup

from crawlers.base import BaseCrawler
from db.models import JobItem
from utils.logger import logger
from utils.text_cleaner import clean_html, generate_job_hash, parse_salary, match_location


class FlexJobsCrawler(BaseCrawler):
    name = "flexjobs"
    BASE_URL = "https://www.flexjobs.com"

    def search(self, keyword: str, limit: int = 20, location: Optional[str] = None) -> List[JobItem]:
        """
        Crawls FlexJobs search results for remote/flexible jobs.
        Reports cleanly if blocked by anti-bot edge protection or timeout.
        """
        jobs: List[JobItem] = []
        encoded_kw = urllib.parse.quote(keyword.strip())
        search_url = f"{self.BASE_URL}/search?search={encoded_kw}"
        if location:
            search_url += f"&location={urllib.parse.quote(location.strip())}"

        logger.info(
            f"[{self.name}] Searching FlexJobs for '{keyword}' at: {search_url}"
            + (f" (Filter: {location})" if location else "")
        )

        status, html_content = self.fetch_html_playwright(search_url, wait_ms=3000)
        if not html_content:
            status, html_content = self.fetch_html_http(search_url)

        if status in (403, 429, 503) or self._is_blocked(html_content):
            logger.warning(
                f"[{self.name}] FlexJobs blocked automated access or returned a security challenge (HTTP {status})."
            )
            return jobs

        if not html_content:
            logger.warning(
                f"[{self.name}] Could not retrieve FlexJobs page (network timeout or blocked)."
            )
            return jobs

        jobs = self.parse_html(html_content, keyword, limit=limit, location=location)
        logger.info(f"[{self.name}] Collected {len(jobs)} jobs from FlexJobs.")
        return jobs

    def parse_html(
        self,
        html_content: str,
        keyword: str,
        limit: int = 20,
        location: Optional[str] = None,
    ) -> List[JobItem]:
        """Parses FlexJobs search HTML into JobItem records."""
        jobs: List[JobItem] = []
        soup = BeautifulSoup(html_content, "html.parser")
        cards = soup.select("[data-testid='job-card'], div[id^='job-'], li.job")
        if not cards:
            cards = soup.select(".job-card, div[class*='JobCard']")
        seen_hashes = set()

        for card in cards:
            title_tag = card.select_one(
                "a[id^='job-title'], a[href*='/publicjobs/'], a[data-testid='job-title'], h3 a, h2 a"
            )
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            if not title:
                continue

            href = title_tag.get("href", "")
            job_url = urllib.parse.urljoin(self.BASE_URL, href) if href else ""

            company_tag = card.select_one(
                "[data-testid='company-name'], .company-name, span[class*='company']"
            )
            company = company_tag.get_text(strip=True) if company_tag else "Remote Company (FlexJobs)"

            loc_tag = card.select_one(
                "[data-testid='job-location'], .job-location, span[class*='location'], li[id^='location']"
            )
            job_loc = loc_tag.get_text(strip=True) if loc_tag else "Remote"

            if location and not match_location(job_loc, location):
                continue

            sal_tag = card.select_one("[data-testid='job-salary'], .salary, span[class*='salary']")
            salary_raw = sal_tag.get_text(strip=True) if sal_tag else "Thỏa thuận"
            sal_min, sal_max, currency = parse_salary(salary_raw)

            desc_tag = card.select_one("[data-testid='job-description'], .job-description, p")
            desc = clean_html(desc_tag.get_text(separator=" ")) if desc_tag else ""

            tags = [t.get_text(strip=True) for t in card.select("span[class*='tag'], .badge") if t.get_text(strip=True)]

            job_hash = generate_job_hash(self.name, job_url, title, company)
            if job_hash in seen_hashes:
                continue
            seen_hashes.add(job_hash)
            jobs.append(
                JobItem(
                    source=self.name,
                    job_hash=job_hash,
                    title=title,
                    company=company,
                    location=job_loc,
                    salary_raw=salary_raw,
                    salary_min=sal_min,
                    salary_max=sal_max,
                    salary_currency=currency,
                    experience=None,
                    job_description=desc,
                    requirements=", ".join(tags),
                    benefits="",
                    job_url=job_url,
                    keyword_searched=keyword,
                )
            )
            if len(jobs) >= limit:
                break

        return jobs

    @staticmethod
    def _is_blocked(html_text: str) -> bool:
        if not html_text:
            return False
        lower = html_text.lower()
        return any(
            marker in lower
            for marker in ["access denied", "attention required! | cloudflare", "verify you are human", "captcha"]
        )
