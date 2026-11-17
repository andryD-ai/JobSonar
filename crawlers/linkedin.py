"""LinkedIn Jobs crawler using public guest jobs search and Playwright fallback."""
import time
import random
import urllib.parse
from typing import List, Optional
from bs4 import BeautifulSoup

from crawlers.base import BaseCrawler
from db.models import JobItem
from utils.logger import logger
from utils.text_cleaner import clean_html, generate_job_hash, parse_salary, match_location, is_keyword_relevant


class LinkedInCrawler(BaseCrawler):
    name = "linkedin"
    GUEST_API_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    PUBLIC_SEARCH_URL = "https://www.linkedin.com/jobs/search"

    def search(self, keyword: str, limit: int = 20, location: Optional[str] = None) -> List[JobItem]:
        """
        Crawls LinkedIn public job postings via guest API, falling back to Playwright.
        """
        jobs: List[JobItem] = []
        # LinkedIn guest search works best with a single country/city query, then local multi-city filter
        query_loc = "Vietnam"
        if location and "," not in location and ";" not in location:
            query_loc = location.strip()

        logger.info(
            f"[{self.name}] Searching LinkedIn for '{keyword}' in '{query_loc}'"
            + (f" (Filter: {location})" if location else "")
        )

        # Try Guest API with pagination (25 jobs per page)
        start = 0
        max_pages = 3
        page_idx = 0

        is_remote_mode = bool(location and any(r in location.lower() for r in ["remote", "online", "tu xa"]))
        while len(jobs) < limit and page_idx < max_pages:
            params = {
                "keywords": keyword.strip(),
                "location": query_loc,
                "start": start,
            }
            if is_remote_mode:
                params["f_WT"] = "2"  # 1: On-site, 2: Remote, 3: Hybrid
            status, html_text = self.fetch_html_http(self.GUEST_API_URL, params=params)

            if status == 0:
                logger.warning(
                    f"[{self.name}] Cannot connect to linkedin.com (may be blocked on local network/DNS)."
                )
                return jobs

            if status == 429:
                logger.warning(f"[{self.name}] Rate-limited by LinkedIn (HTTP 429). Stopping early.")
                break

            if status != 200 or not html_text.strip():
                logger.debug(f"[{self.name}] Guest API returned status {status}; trying Playwright fallback.")
                break

            parsed_batch = self._parse_cards(html_text, keyword)
            if not parsed_batch:
                break

            for job in parsed_batch:
                if not is_keyword_relevant(job.title, job.job_description, keyword):
                    continue
                if location and not match_location(job.location, location):
                    continue
                jobs.append(job)
                if len(jobs) >= limit:
                    break

            start += 25
            page_idx += 1
            if len(jobs) < limit and page_idx < max_pages:
                time.sleep(random.uniform(1.5, 3.5))

        # Fallback to public search page via Playwright if Guest API yielded nothing
        if not jobs and page_idx == 0:
            encoded_kw = urllib.parse.quote(keyword.strip())
            encoded_loc = urllib.parse.quote(query_loc)
            search_url = f"{self.PUBLIC_SEARCH_URL}?keywords={encoded_kw}&location={encoded_loc}"
            status, html_text = self.fetch_html_playwright(search_url, wait_ms=3000)
            if status == 200 and html_text:
                for job in self._parse_cards(html_text, keyword):
                    if not is_keyword_relevant(job.title, job.job_description, keyword):
                        continue
                    if location and not match_location(job.location, location):
                        continue
                    jobs.append(job)
                    if len(jobs) >= limit:
                        break
            elif status != 0:
                logger.warning(f"[{self.name}] Public LinkedIn page returned status {status}.")

        logger.info(f"[{self.name}] Collected {len(jobs)} jobs from LinkedIn.")
        return jobs

    def _parse_cards(self, html_text: str, keyword: str) -> List[JobItem]:
        soup = BeautifulSoup(html_text, "html.parser")
        cards = soup.select("div.base-card, div.job-search-card")
        if not cards:
            cards = soup.select("li")
        results: List[JobItem] = []
        seen_hashes = set()

        for card in cards:
            title_tag = (
                card.select_one("h3.base-search-card__title")
                or card.select_one("h3")
                or card.select_one("a.base-card__full-link")
            )
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            if not title:
                continue

            link_tag = card.select_one("a.base-card__full-link, a[href*='/jobs/view/']")
            job_url = link_tag.get("href", "").split("?")[0].strip() if link_tag else ""

            company_tag = card.select_one("h4.base-search-card__subtitle, a.hidden-nested-link, h4")
            company = company_tag.get_text(strip=True) if company_tag else "Unknown Company"

            loc_tag = card.select_one("span.job-search-card__location, .job-result-card__location")
            location = loc_tag.get_text(strip=True) if loc_tag else "Vietnam"

            sal_tag = card.select_one("span.job-search-card__salary-info")
            salary_raw = sal_tag.get_text(strip=True) if sal_tag else "Thỏa thuận"
            sal_min, sal_max, currency = parse_salary(salary_raw)

            time_tag = card.select_one("time")
            posted_date = time_tag.get("datetime") or time_tag.get_text(strip=True) if time_tag else None

            snippet_tag = card.select_one("p.job-search-card__snippet")
            desc = clean_html(snippet_tag.get_text(separator=" ")) if snippet_tag else ""

            job_hash = generate_job_hash(self.name, job_url, title, company)
            if job_hash in seen_hashes:
                continue
            seen_hashes.add(job_hash)
            results.append(
                JobItem(
                    source=self.name,
                    job_hash=job_hash,
                    title=title,
                    company=company,
                    location=location,
                    salary_raw=salary_raw,
                    salary_min=sal_min,
                    salary_max=sal_max,
                    salary_currency=currency,
                    experience=None,
                    job_description=desc,
                    requirements="",
                    benefits="",
                    job_url=job_url,
                    posted_date=posted_date,
                    keyword_searched=keyword,
                )
            )

        return results
