"""Glassdoor job board crawler with anti-bot detection handling."""
import urllib.parse
from typing import List, Optional
from bs4 import BeautifulSoup

from crawlers.base import BaseCrawler
from db.models import JobItem
from utils.logger import logger
from utils.text_cleaner import clean_html, generate_job_hash, parse_salary, match_location, is_keyword_relevant


class GlassdoorCrawler(BaseCrawler):
    name = "glassdoor"
    BASE_URL = "https://www.glassdoor.com"

    def search(self, keyword: str, limit: int = 20, location: Optional[str] = None) -> List[JobItem]:
        """
        Crawls Glassdoor job listings.
        Stops and reports clearly if Glassdoor presents a Cloudflare/security gate.
        """
        jobs: List[JobItem] = []
        encoded_kw = urllib.parse.quote(keyword.strip())
        loc_q = urllib.parse.quote(location.strip() if location and "," not in location else "Vietnam")
        search_url = f"{self.BASE_URL}/Job/jobs.htm?sc.keyword={encoded_kw}&locKeyword={loc_q}"

        logger.info(
            f"[{self.name}] Searching Glassdoor for '{keyword}' at: {search_url}"
            + (f" (Filter: {location})" if location else "")
        )

        status, html_content = self.fetch_html_playwright(search_url, wait_ms=3000)
        if not html_content:
            status, html_content = self.fetch_html_http(search_url)

        if status in (403, 429, 503) or self._is_blocked(html_content):
            logger.warning(
                f"[{self.name}] Glassdoor gated automated access with a security/Cloudflare challenge (HTTP {status})."
            )
            return jobs

        if not html_content:
            logger.warning(f"[{self.name}] Could not retrieve Glassdoor page (status: {status}).")
            return jobs

        jobs = self.parse_html(html_content, keyword, limit=limit, location=location)
        logger.info(f"[{self.name}] Collected {len(jobs)} jobs from Glassdoor.")
        return jobs

    def parse_html(
        self,
        html_content: str,
        keyword: str,
        limit: int = 20,
        location: Optional[str] = None,
    ) -> List[JobItem]:
        """Parses Glassdoor HTML listings into JobItem records."""
        jobs: List[JobItem] = []
        soup = BeautifulSoup(html_content, "html.parser")
        cards = soup.select("li[data-test='jobListing'], li[data-jobid]")
        if not cards:
            cards = soup.select("div[class*='JobCard_jobCardContainer'], .react-job-listing")
        seen_hashes = set()

        for card in cards:
            title_tag = card.select_one(
                "[data-test='job-title'], a[class*='JobCard_jobTitle'], a.jobTitle, a[href*='/job-listing/']"
            )
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            if not title:
                continue

            href = title_tag.get("href", "")
            job_url = urllib.parse.urljoin(self.BASE_URL, href) if href else ""

            company_tag = card.select_one(
                "[class*='EmployerProfile_compactEmployerName'], [data-test='employer-short-name'], .job-search-key-l2wjgv"
            )
            company = company_tag.get_text(strip=True) if company_tag else "Unknown Company"

            loc_tag = card.select_one(
                "[data-test='emp-location'], div[class*='JobCard_location'], span.loc"
            )
            job_loc = loc_tag.get_text(strip=True) if loc_tag else "Vietnam"

            if location and not match_location(job_loc, location):
                continue

            sal_tag = card.select_one(
                "[data-test='detailSalary'], div[class*='JobCard_salaryEstimate'], span[data-test='salary-estimate']"
            )
            salary_raw = sal_tag.get_text(strip=True) if sal_tag else "Thỏa thuận"
            sal_min, sal_max, currency = parse_salary(salary_raw)

            desc_tag = card.select_one("[data-test='job-description-snippet'], div[class*='JobCard_jobDescriptionSnippet']")
            desc = clean_html(desc_tag.get_text(separator=" ")) if desc_tag else ""

            if not is_keyword_relevant(title, desc, keyword):
                continue

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
                    requirements="",
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
            for marker in [
                "<title>security | glassdoor</title>",
                "just a moment...",
                "verify you are human",
                "help us protect glassdoor",
                "cf-turnstile",
            ]
        )
