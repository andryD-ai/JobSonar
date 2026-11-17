"""CareerViet (formerly CareerBuilder Vietnam) crawler."""
import re
import urllib.parse
from typing import List, Optional
from bs4 import BeautifulSoup

from crawlers.base import BaseCrawler
from db.models import JobItem
from utils.logger import logger
from utils.text_cleaner import clean_html, generate_job_hash, parse_salary, match_location, is_keyword_relevant


class CareerVietCrawler(BaseCrawler):
    name = "careerviet"
    BASE_URL = "https://careerviet.vn"

    def search(self, keyword: str, limit: int = 20, location: Optional[str] = None) -> List[JobItem]:
        """
        Crawls CareerViet search results for the given keyword and optional location.
        """
        jobs: List[JobItem] = []
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", keyword.strip().lower()).strip("-")
        search_url = f"{self.BASE_URL}/viec-lam/{slug}-k-vi.html"

        logger.info(f"[{self.name}] Searching for '{keyword}' at: {search_url}" + (f" (Filter: {location})" if location else ""))

        try:
            with self.get_client() as client:
                resp = client.get(search_url)
                if resp.status_code != 200:
                    logger.warning(f"[{self.name}] Received status code {resp.status_code}")
                    return jobs

                soup = BeautifulSoup(resp.text, "html.parser")
                job_items = soup.select(".job-item, .bx_item, div[class*='job-item']")

                logger.info(f"[{self.name}] Found {len(job_items)} job items on page")

                for item in job_items:
                    job = self._parse_item(item, keyword)
                    if job:
                        if not is_keyword_relevant(job.title, job.job_description, keyword):
                            continue
                        if location and not match_location(job.location, location):
                            continue
                        jobs.append(job)
                        if len(jobs) >= limit:
                            break

        except Exception as e:
            logger.error(f"[{self.name}] Error crawling CareerViet: {e}")

        return jobs

    def _parse_item(self, item, keyword: str) -> Optional[JobItem]:
        title_tag = item.select_one(".job_link, .title a, h2 a, a.job-title")
        if not title_tag:
            return None
        title = title_tag.get_text(strip=True)
        job_url = ""
        if title_tag.get("href"):
            job_url = urllib.parse.urljoin(self.BASE_URL, title_tag.get("href"))

        company_tag = item.select_one(".company-name, .company, a.company_link")
        company = company_tag.get_text(strip=True) if company_tag else "Unknown Company"

        loc_tag = item.select_one(".location, .city, .fa-map-marker-alt + span, div.location")
        location = loc_tag.get_text(strip=True) if loc_tag else "Vietnam"

        salary_tag = item.select_one(".salary, .salary-text, .fa-dollar-sign + span, div.salary")
        salary_raw = salary_tag.get_text(strip=True) if salary_tag else "Thỏa thuận"
        sal_min, sal_max, currency = parse_salary(salary_raw)

        desc_tag = item.select_one(".desc, .job-desc, .caption")
        desc = clean_html(desc_tag.get_text(separator=" ")) if desc_tag else ""

        exp_tag = item.select_one(".fa-briefcase + span")
        experience = exp_tag.get_text(strip=True) if exp_tag else None

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
