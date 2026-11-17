"""Remotive (remotive.com) remote job crawler using its official free JSON API."""
import urllib.parse
from typing import List, Optional, Dict, Any
from crawlers.base import BaseCrawler
from db.models import JobItem
from utils.logger import logger
from utils.text_cleaner import clean_html, generate_job_hash, parse_salary, is_keyword_relevant, match_location


class RemotiveCrawler(BaseCrawler):
    name = "remotive"
    API_URL = "https://remotive.com/api/remote-jobs"
    BASE_URL = "https://remotive.com"

    def search(self, keyword: str, limit: int = 20, location: Optional[str] = None) -> List[JobItem]:
        """
        Queries Remotive's official public JSON API for 100% remote jobs.
        """
        jobs: List[JobItem] = []
        fetch_limit = min(max(limit * 2, 25), 100)
        params = {
            "search": keyword.strip(),
            "limit": fetch_limit
        }

        logger.info(f"[{self.name}] Querying Remotive Remote API for '{keyword}'")

        try:
            with self.get_client() as client:
                resp = client.get(self.API_URL, params=params)
                if resp.status_code != 200:
                    logger.warning(f"[{self.name}] Received status code {resp.status_code}")
                    return jobs

                payload = resp.json()
                raw_jobs = payload.get("jobs", [])
                logger.info(f"[{self.name}] Remotive returned {len(raw_jobs)} remote jobs")

                for item in raw_jobs:
                    job = self._parse_item(item, keyword)
                    if not job:
                        continue
                    # If user requested a specific country filter like Vietnam, check it
                    if location and not match_location(job.location, location, job.title):
                        continue
                    jobs.append(job)
                    if len(jobs) >= limit:
                        break

        except Exception as e:
            logger.error(f"[{self.name}] Error querying Remotive: {e}")

        return jobs

    def _parse_item(self, item: Dict[str, Any], keyword: str) -> Optional[JobItem]:
        title = (item.get("title") or "").strip()
        if not title:
            return None

        # Verify keyword relevance to prevent generic non-tech ads
        desc_raw = item.get("description", "")
        if not is_keyword_relevant(title, desc_raw, keyword):
            return None

        company = (item.get("company_name") or "Unknown Company").strip()
        job_url = item.get("url") or self.BASE_URL

        candidate_loc = (item.get("candidate_required_location") or "Worldwide").strip()
        location = f"Remote ({candidate_loc})"

        salary_raw = (item.get("salary") or "").strip() or "Thỏa thuận"
        sal_min, sal_max, currency = parse_salary(salary_raw)

        cleaned_desc = clean_html(desc_raw)
        tags = item.get("tags") or []
        requirements = ", ".join(str(t) for t in tags)

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
            salary_currency=currency if currency != "Unknown" else "USD",
            experience=None,
            job_description=cleaned_desc[:4000],
            requirements=requirements,
            benefits=f"Remote work • Job type: {item.get('job_type', 'Full time')}",
            job_url=job_url,
            posted_date=item.get("publication_date"),
            keyword_searched=keyword
        )
