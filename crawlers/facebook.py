"""Facebook Fanpage crawler using Playwright with persistent session and anti-detection."""
import time
import random
import json
from pathlib import Path
from typing import List, Optional
from bs4 import BeautifulSoup

from crawlers.base import BaseCrawler
from config.settings import settings
from db.models import JobItem
from utils.logger import logger
from utils.text_cleaner import clean_html, generate_job_hash, parse_salary, is_keyword_relevant


class FacebookCrawler(BaseCrawler):
    name = "facebook"

    def __init__(self, profile_dir: Optional[Path] = None, timeout: Optional[int] = None):
        super().__init__(timeout)
        self.profile_dir = profile_dir or settings.BROWSER_PROFILE_DIR
        self.profile_dir.mkdir(parents=True, exist_ok=True)

    def interactive_login(self) -> None:
        """
        Launches a headed browser with the persistent profile.
        Allows the user to log into their Facebook account (preferably a secondary/clone account).
        Once logged in, the session is saved permanently in data/browser_profile/.
        """
        from playwright.sync_api import sync_playwright

        logger.info("[facebook] Launching headed browser for manual login...")
        logger.info(f"[facebook] Session profile will be saved to: {self.profile_dir}")
        print("\n" + "=" * 60)
        print(">>> HƯỚNG DẪN ĐĂNG NHẬP FACEBOOK:")
        print("1. Trình duyệt sẽ mở trang https://www.facebook.com.")
        print("2. Đăng nhập tài khoản của bạn (nên dùng nick phụ).")
        print("3. Sau khi đăng nhập thành công vào Newsfeed, quay lại terminal và nhấn ENTER.")
        print("=" * 60 + "\n")

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                headless=False,
                viewport={"width": 1280, "height": 800},
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox"
                ]
            )
            page = context.new_page()
            page.goto("https://www.facebook.com", wait_until="domcontentloaded")
            input("Nhấn [ENTER] tại đây sau khi bạn đã đăng nhập xong trên trình duyệt...")
            context.close()
            logger.info("[facebook] Profile session saved successfully!")

    def search(self, keyword_or_url: str, limit: int = 15, location: Optional[str] = None) -> List[JobItem]:
        """
        Crawls a specific Facebook Fanpage or search results for jobs.
        If keyword_or_url starts with http, treats it as a Fanpage URL.
        Otherwise, navigates to Facebook search.
        """
        if keyword_or_url.startswith("http://") or keyword_or_url.startswith("https://"):
            target_url = keyword_or_url
            keyword = "Facebook Fanpage"
        else:
            import urllib.parse
            keyword = keyword_or_url
            target_url = f"https://www.facebook.com/search/posts/?q={urllib.parse.quote(keyword)}"

        return self.crawl_fanpage(target_url, keyword=keyword, limit=limit)

    def crawl_fanpage(
        self,
        target_url: str,
        keyword: str = "",
        limit: int = 15,
        min_delay: float = 3.0,
        max_delay: float = 10.0
    ) -> List[JobItem]:
        """
        Crawls posts from a target Fanpage/Group URL with human-like scrolling,
        random sleep delays up to 10 seconds, and auto-expanding 'Xem thêm' buttons.
        """
        jobs: List[JobItem] = []
        from playwright.sync_api import sync_playwright

        logger.info(f"[facebook] Navigating to: {target_url}")
        logger.info(f"[facebook] Random sleep interval between scrolls: {min_delay}s - {max_delay}s")

        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.profile_dir),
                    headless=True,
                    viewport={"width": 1280, "height": 900},
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox"
                    ]
                )
                page = context.new_page()
                page.goto(target_url, wait_until="domcontentloaded", timeout=self.timeout * 1000)

                # Initial natural pause
                initial_wait = random.uniform(3.0, 6.0)
                time.sleep(initial_wait)

                consecutive_no_new_posts = 0
                seen_texts = set()

                scroll_rounds = 0
                max_scroll_rounds = max(limit * 2, 10)

                while len(jobs) < limit and scroll_rounds < max_scroll_rounds:
                    scroll_rounds += 1

                    # Click "Xem thêm" / "See more" buttons to expand full post body
                    try:
                        see_more_buttons = page.query_selector_all(
                            "div[role='button']:has-text('Xem thêm'), div[role='button']:has-text('See more')"
                        )
                        for btn in see_more_buttons[:5]:
                            try:
                                btn.click(timeout=1000)
                                time.sleep(0.5)
                            except Exception:
                                pass
                    except Exception:
                        pass

                    # Extract post elements
                    post_elements = page.query_selector_all(
                        "div[role='article'], div[data-ad-preview='message'], div[dir='auto']"
                    )

                    new_in_this_round = 0
                    for el in post_elements:
                        try:
                            text = el.inner_text().strip()
                            if len(text) < 50:  # Skip comments or short reaction tags
                                continue

                            # Quick filter for job-related keywords in Vietnamese
                            lower_text = text.lower()
                            if not any(k in lower_text for k in ["tuyển", "tuyen dung", "hiring", "job", "lương", "jd", "vị trí", "fresher", "junior", "senior"]):
                                continue

                            first_line = text.split("\n")[0][:100]
                            if first_line in seen_texts:
                                continue
                            seen_texts.add(first_line)

                            job_item = self._post_to_job(text, target_url, keyword)
                            if job_item:
                                if not is_keyword_relevant(job_item.title, job_item.job_description, keyword):
                                    continue
                                jobs.append(job_item)
                                new_in_this_round += 1
                                if len(jobs) >= limit:
                                    break
                        except Exception:
                            continue

                    logger.info(f"[facebook] Round {scroll_rounds}: Extracted {len(jobs)}/{limit} posts so far")

                    if new_in_this_round == 0:
                        consecutive_no_new_posts += 1
                        if consecutive_no_new_posts >= 4:
                            logger.info("[facebook] Reached end of reachable feed or rate limit. Stopping scroll.")
                            break
                    else:
                        consecutive_no_new_posts = 0

                    # Human-like random scrolling
                    scroll_distance = random.randint(500, 950)
                    page.evaluate(f"window.scrollBy(0, {scroll_distance});")

                    # Crucial: Random sleep up to 10 seconds to avoid detection
                    sleep_time = random.uniform(min_delay, max_delay)
                    logger.debug(f"[facebook] Anti-bot delay: sleeping for {sleep_time:.2f}s...")
                    time.sleep(sleep_time)

                context.close()

        except Exception as e:
            logger.error(f"[facebook] Error during Facebook scraping: {e}")

        logger.info(f"[facebook] Finished. Collected {len(jobs)} posts.")
        return jobs

    def import_from_file(self, file_path: str, keyword: str = "Facebook Import") -> List[JobItem]:
        """
        Fallback mode: Imports posts from a JSON, HTML, or plain text file.
        Useful when scraping live is not desired or posts are exported manually.
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"[facebook] File not found: {file_path}")
            return []

        jobs: List[JobItem] = []
        try:
            if path.suffix.lower() == ".json":
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    items = data if isinstance(data, list) else data.get("posts", [])
                    for entry in items:
                        text = entry.get("text") or entry.get("content") or str(entry)
                        job = self._post_to_job(text, entry.get("url", file_path), keyword)
                        if job:
                            jobs.append(job)

            elif path.suffix.lower() in [".html", ".htm"]:
                with open(path, "r", encoding="utf-8") as f:
                    soup = BeautifulSoup(f.read(), "html.parser")
                    for el in soup.find_all(["div", "article", "p"]):
                        text = el.get_text(separator="\n").strip()
                        if len(text) > 60 and any(k in text.lower() for k in ["tuyển", "lương", "jd", "hiring"]):
                            job = self._post_to_job(text, file_path, keyword)
                            if job:
                                jobs.append(job)

            else:
                # Plain text - separate posts by double newline or delimiter
                with open(path, "r", encoding="utf-8") as f:
                    blocks = f.read().split("\n\n---\n\n")
                    for block in blocks:
                        text = block.strip()
                        if len(text) > 40:
                            job = self._post_to_job(text, file_path, keyword)
                            if job:
                                jobs.append(job)

            logger.info(f"[facebook] Imported {len(jobs)} jobs from file: {file_path}")
        except Exception as e:
            logger.error(f"[facebook] Error importing from file {file_path}: {e}")

        return jobs

    def _post_to_job(self, text: str, source_url: str, keyword: str) -> Optional[JobItem]:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if not lines:
            return None

        # Guess title from first 1-2 lines
        title = lines[0][:80]
        company = "Facebook Post / Fanpage"

        # Check for company in text
        for line in lines[:4]:
            if any(k in line.lower() for k in ["công ty", "cty", "company"]):
                company = line[:60]
                break

        # Extract salary
        salary_raw = "Thỏa thuận"
        for line in lines:
            if any(k in line.lower() for k in ["lương", "thu nhập", "salary", "triệu", "usd", "$"]):
                salary_raw = line[:50]
                break
        sal_min, sal_max, currency = parse_salary(salary_raw)

        job_hash = generate_job_hash(self.name, None, title, text[:150])

        return JobItem(
            source=self.name,
            job_hash=job_hash,
            title=title,
            company=company,
            location="Vietnam",
            salary_raw=salary_raw,
            salary_min=sal_min,
            salary_max=sal_max,
            salary_currency=currency,
            experience=None,
            job_description=text,
            requirements="",
            benefits="",
            job_url=source_url,
            keyword_searched=keyword
        )
