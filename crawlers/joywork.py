"""JoyWork (joywork.vn) job board crawler using its public JSON API."""
from typing import List, Optional, Dict, Any, Tuple
from crawlers.base import BaseCrawler
from db.models import JobItem
from utils.logger import logger
from utils.text_cleaner import clean_html, generate_job_hash, match_location, is_keyword_relevant


LOCATION_SLUG_MAP = {
    "ha-noi": "Hà Nội",
    "da-nang": "Đà Nẵng",
    "tp-ho-chi-minh": "TP. Hồ Chí Minh",
    "binh-duong": "Bình Dương",
    "hai-phong": "Hải Phòng",
    "can-tho": "Cần Thơ",
    "bac-ninh": "Bắc Ninh",
    "dong-nai": "Đồng Nai",
}

EXP_MAP = {
    "NO_EXP": "Không yêu cầu kinh nghiệm",
    "UNDER_1": "Dưới 1 năm",
    "Y1_2": "1 - 2 năm",
    "Y2_3": "2 - 3 năm",
    "Y3_5": "3 - 5 năm",
    "OVER_5": "Trên 5 năm",
}


class JoyWorkCrawler(BaseCrawler):
    name = "joywork"
    API_URL = "https://api.joywork.vn/api/jobs"
    BASE_URL = "https://joywork.vn"

    def search(self, keyword: str, limit: int = 20, location: Optional[str] = None) -> List[JobItem]:
        """
        Queries JoyWork's public JSON API and filters by keyword and optional location.
        """
        jobs: List[JobItem] = []
        fetch_limit = min(max(limit * 3, 30), 100) if location else min(limit, 100)
        params = {"q": keyword.strip(), "limit": fetch_limit, "page": 1}

        logger.info(
            f"[{self.name}] Querying JoyWork API for '{keyword}'"
            + (f" (Filter: {location})" if location else "")
        )

        try:
            with self.get_client() as client:
                resp = client.get(self.API_URL, params=params)
                if resp.status_code != 200:
                    logger.warning(f"[{self.name}] Received status code {resp.status_code}")
                    return jobs

                payload = resp.json()
                raw_jobs = payload.get("data", {}).get("jobs", [])
                logger.info(f"[{self.name}] API returned {len(raw_jobs)} jobs")

                for item in raw_jobs:
                    job = self._parse_item(item, keyword)
                    if not job:
                        continue
                    if not is_keyword_relevant(job.title, job.job_description, keyword):
                        continue
                    if location and not match_location(job.location, location):
                        continue
                    jobs.append(job)
                    if len(jobs) >= limit:
                        break
        except Exception as e:
            logger.error(f"[{self.name}] Error crawling JoyWork: {e}")

        return jobs

    def _parse_item(self, item: Dict[str, Any], keyword: str) -> Optional[JobItem]:
        title = (item.get("title") or "").strip()
        if not title:
            return None

        job_id = item.get("id", "")
        slug = item.get("slug", "")
        job_url = f"{self.BASE_URL}/jobs/{slug}--{job_id}" if slug and job_id else self.BASE_URL

        company_obj = item.get("company") or {}
        company = company_obj.get("name") or company_obj.get("legalName") or "Unknown Company"

        location_str = self._format_location(item)
        sal_raw, sal_min, sal_max, currency = self._format_salary(item)

        desc_parts = [clean_html(item.get(f)) for f in ("generalInfo", "mission", "tasks") if item.get(f)]
        job_description = "\n".join(p for p in desc_parts if p)

        req_parts = [clean_html(item.get(f)) for f in ("knowledge", "skills", "attitude") if item.get(f)]
        tags = item.get("tags") or []
        if tags:
            req_parts.insert(0, ", ".join(str(t) for t in tags))
        requirements = "\n".join(p for p in req_parts if p)

        benefit_parts = [clean_html(item.get(f)) for f in ("benefitsIncome", "benefitsPerks") if item.get(f)]
        benefits = "\n".join(p for p in benefit_parts if p)

        exp_raw = item.get("experienceLevel")
        experience = EXP_MAP.get(exp_raw, exp_raw) if exp_raw else None

        job_hash = generate_job_hash(self.name, job_url, title, company)

        return JobItem(
            source=self.name,
            job_hash=job_hash,
            title=title,
            company=company,
            location=location_str,
            salary_raw=sal_raw,
            salary_min=sal_min,
            salary_max=sal_max,
            salary_currency=currency,
            experience=experience,
            job_description=job_description,
            requirements=requirements,
            benefits=benefits,
            job_url=job_url,
            posted_date=item.get("createdAt"),
            keyword_searched=keyword,
        )

    @staticmethod
    def _format_location(item: Dict[str, Any]) -> str:
        raw_locs = item.get("locations") or []
        names = [LOCATION_SLUG_MAP.get(loc, loc.replace("-", " ").title()) for loc in raw_locs if loc]
        if not names and item.get("location"):
            names.append(str(item["location"]))
        if not names and item.get("specificAddress"):
            names.append(str(item["specificAddress"]))
        if not names:
            names.append("Vietnam")

        modes = item.get("workModes") or []
        mode_str = ", ".join(m.title() for m in modes if m)
        loc_text = ", ".join(dict.fromkeys(names))
        return f"{mode_str} - {loc_text}" if mode_str else loc_text

    @staticmethod
    def _format_salary(item: Dict[str, Any]) -> Tuple[str, Optional[float], Optional[float], str]:
        s_min = item.get("salaryMin")
        s_max = item.get("salaryMax")
        currency = item.get("currency") or "VND"

        if s_min is None and s_max is None:
            return "Thỏa thuận", None, None, "Negotiable"

        def _fmt(val: Optional[float]) -> Tuple[Optional[float], str]:
            if val is None:
                return None, ""
            v = float(val)
            # Some employers input salary in millions (e.g. 8 - 11 instead of 8000000 - 11000000)
            if currency == "VND" and 0 < v < 1000:
                return v * 1_000_000, f"{v:g} Triệu"
            if currency == "VND" and v >= 1_000_000:
                return v, f"{v / 1_000_000:g} Triệu"
            return v, f"{v:,.0f}"

        norm_min, min_str = _fmt(s_min)
        norm_max, max_str = _fmt(s_max)

        if min_str and max_str:
            raw = f"{min_str} - {max_str} {currency}"
        elif min_str:
            raw = f"Từ {min_str} {currency}"
        else:
            raw = f"Tới {max_str} {currency}"
        return raw, norm_min, norm_max, currency
