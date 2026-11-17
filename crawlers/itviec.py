"""ITviec job board crawler."""
import urllib.parse
from typing import List, Optional
from bs4 import BeautifulSoup

from crawlers.base import BaseCrawler
from db.models import JobItem
from utils.logger import logger
from utils.text_cleaner import clean_html, generate_job_hash, parse_salary, match_location, is_keyword_relevant


class ITViecCrawler(BaseCrawler):
    name = "itviec"
    BASE_URL = "https://itviec.com"

    def search(self, keyword: str, limit: int = 20, location: Optional[str] = None) -> List[JobItem]:
        """
        Crawls ITviec search results for the given keyword and optional location.
        """
        jobs: List[JobItem] = []
        encoded_kw = urllib.parse.quote(keyword.strip())
        is_remote_mode = bool(location and any(r in location.lower() for r in ["remote", "online", "tu xa"]))
        if is_remote_mode:
            search_url = f"{self.BASE_URL}/it-jobs/remote?query={encoded_kw}"
        else:
            search_url = f"{self.BASE_URL}/it-jobs?query={encoded_kw}"

        logger.info(f"[{self.name}] Searching for '{keyword}' at: {search_url}" + (f" (Filter: {location})" if location else ""))

        try:
            with self.get_client() as client:
                resp = client.get(search_url)
                if resp.status_code != 200:
                    logger.warning(f"[{self.name}] Received status code {resp.status_code}")
                    return jobs

                soup = BeautifulSoup(resp.text, "html.parser")
                job_cards = soup.select(
                    ".job-card, [data-search--job-selection-target='jobCard'], .search-page__job-card"
                )

                if not job_cards:
                    job_cards = soup.find_all("div", class_=lambda c: c and "job" in c.lower() and "card" in c.lower())

                logger.info(f"[{self.name}] Found {len(job_cards)} job cards on page")

                for card in job_cards:
                    item = self._parse_card(card, keyword)
                    if item:
                        if not is_keyword_relevant(item.title, item.job_description, keyword):
                            continue
                        if location and not match_location(item.location, location):
                            continue
                        jobs.append(item)
                        if len(jobs) >= limit:
                            break

        except Exception as e:
            logger.error(f"[{self.name}] Error crawling ITviec: {e}")

        return jobs

    def _parse_card(self, card, keyword: str) -> JobItem:
        # Title & URL
        title_tag = card.select_one("h3 a, h3, a[data-job-name], .title a, a[href*='/it-jobs/']")
        title = title_tag.get_text(strip=True) if title_tag else "Unknown Position"
        job_url = ""
        if title_tag and title_tag.name == "a" and title_tag.get("href"):
            job_url = urllib.parse.urljoin(self.BASE_URL, title_tag.get("href"))
        elif card.find("a", href=lambda h: h and "/it-jobs/" in h):
            job_url = urllib.parse.urljoin(self.BASE_URL, card.find("a", href=lambda h: h and "/it-jobs/" in h)["href"])

        # Company
        company_tag = card.select_one("span.ims-2, a.text-rich-grey, .company-name, .employer-name, a[data-company-name]")
        company = company_tag.get_text(strip=True) if company_tag else "Unknown Company"

        # Salary
        salary_tag = card.select_one(".salary, .text-salary, .salary-content, span.svg-icon--salary + span")
        salary_raw = salary_tag.get_text(strip=True) if salary_tag else "Thỏa thuận"
        sal_min, sal_max, currency = parse_salary(salary_raw)

        # Location
        location = "Vietnam"
        for loc_candidate in card.select("div.text-nowrap, div.small-text, span, div.text-dark-grey"):
            txt = loc_candidate.get_text(strip=True)
            if any(k in txt.lower() for k in ["ha noi", "hà nội", "da nang", "đà nẵng", "ho chi minh", "hồ chí minh", "remote", "hybrid", "hcm"]):
                location = txt.replace("At office", "At office - ").replace("Hybrid", "Hybrid - ")
                break

        # Skills / Tags
        skill_tags = card.select(".tag, .skill, .keyword-list a, .search-page__tag-group a, span.tag, a.tag")
        skills = [s.get_text(strip=True) for s in skill_tags if s.get_text(strip=True)]
        requirements_str = ", ".join(skills) if skills else ""

        # Description snippet / highlights
        desc_tag = card.select_one(".job-description, .snippet, .description, ul.paragraph")
        desc = clean_html(desc_tag.get_text(separator=" ")) if desc_tag else ""
        if not desc:
            # ITviec has 3 bullet points inside card
            bullets = [li.get_text(strip=True) for li in card.select("ul li") if li.get_text(strip=True)]
            if bullets:
                desc = " | ".join(bullets)

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
            experience=None,
            job_description=desc,
            requirements=requirements_str,
            benefits="",
            job_url=job_url,
            keyword_searched=keyword
        )
