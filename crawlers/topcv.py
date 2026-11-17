"""TopCV job board crawler with Playwright and HTTP fallback."""
import urllib.parse
from typing import List, Optional
from bs4 import BeautifulSoup

from crawlers.base import BaseCrawler
from db.models import JobItem
from utils.logger import logger
from utils.text_cleaner import clean_html, generate_job_hash, parse_salary, match_location, is_keyword_relevant


class TopCVCrawler(BaseCrawler):
    name = "topcv"
    BASE_URL = "https://www.topcv.vn"

    def search(self, keyword: str, limit: int = 20, location: Optional[str] = None) -> List[JobItem]:
        """
        Crawls TopCV jobs. Tries Playwright first to handle Cloudflare bot checks,
        falls back to HTTP client.
        """
        jobs: List[JobItem] = []
        encoded_kw = urllib.parse.quote(keyword.strip())
        search_url = f"{self.BASE_URL}/tim-viec-lam-moi-nhat?keyword={encoded_kw}"

        logger.info(f"[{self.name}] Searching for '{keyword}' at: {search_url}" + (f" (Filter: {location})" if location else ""))

        status, html_content = self.fetch_html_playwright(search_url, wait_ms=2000)
        if not html_content:
            status, html_content = self.fetch_html_http(search_url)
            if status != 200:
                html_content = ""

        if not html_content:
            logger.warning(f"[{self.name}] Could not retrieve page content from TopCV (status: {status}).")
            return jobs

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            job_cards = soup.select(".job-item-search-result, .job-item-2, .job-item, .box-item")

            logger.info(f"[{self.name}] Found {len(job_cards)} job cards on TopCV")

            for card in job_cards:
                job = self._parse_card(card, keyword)
                if job:
                    if not is_keyword_relevant(job.title, job.job_description, keyword):
                        continue
                    if location and not match_location(job.location, location):
                        continue
                    jobs.append(job)
                    if len(jobs) >= limit:
                        break
        except Exception as e:
            logger.error(f"[{self.name}] Error parsing TopCV jobs: {e}")

        return jobs

    def _parse_card(self, card, keyword: str) -> JobItem:
        title_tag = card.select_one(".title a, h3 a, a.job-title, .job-item-title")
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Position"
        job_url = ""
        if title_tag and title_tag.get("href"):
            job_url = urllib.parse.urljoin(self.BASE_URL, title_tag.get("href"))

        company_tag = card.select_one(".company a, .company-name, .job-item-company, a.name")
        company = company_tag.get_text(strip=True) if company_tag else "Unknown Company"

        salary_tag = card.select_one(".salary, .job-item-salary, .badge-salary, span.text-salary")
        salary_raw = salary_tag.get_text(strip=True) if salary_tag else "Thỏa thuận"
        sal_min, sal_max, currency = parse_salary(salary_raw)

        loc_tag = card.select_one(".address, .location, .job-item-address, span.city")
        location = loc_tag.get_text(strip=True) if loc_tag else "Vietnam"

        exp_tag = card.select_one(".experience, .exp, span.job-item-experience")
        experience = exp_tag.get_text(strip=True) if exp_tag else None

        desc_tag = card.select_one(".desc, .job-item-description")
        desc = clean_html(desc_tag.get_text(separator=" ")) if desc_tag else ""

        job_hash = generate_job_hash(self.name, job_url, title, company)

        return JobItem(
            source=self.name,
            job_hash=job_hash,
            title=title,
            company=company,
            location=location,
            salary_raw=salary_raw,
            salary_min=sal_min,
            salary_max=sal_max,
            salary_currency=currency,
            experience=experience,
            job_description=desc,
            requirements="",
            benefits="",
            job_url=job_url,
            keyword_searched=keyword
        )
