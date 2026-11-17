"""Synthesizer module to prepare data, invoke LLM, and generate reports."""
import re
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional

from config.settings import settings
from db.models import ReportItem
from db.repository import job_repo, report_repo
from llm.client import get_llm_client
from llm.prompts import HR_SYSTEM_PROMPT, build_synthesis_prompt
from utils.logger import logger


class JobSynthesizer:
    def __init__(self, provider: Optional[str] = None, api_key: Optional[str] = None):
        self.client = get_llm_client(provider=provider, api_key=api_key)

    def generate_report(self, keyword: str, limit: int = 100) -> Tuple[str, Path]:
        """
        Retrieves matching jobs from SQLite, synthesizes with LLM,
        and saves the Markdown report to reports/ directory and DB.
        """
        logger.info(f"[Synthesizer] Querying jobs from database for keyword '{keyword}' (max {limit})...")
        jobs = job_repo.get_jobs_by_keyword(keyword, limit=limit)

        if not jobs:
            # Fallback to recent jobs if keyword is broad
            jobs = job_repo.get_recent_jobs(limit=limit)

        if not jobs:
            raise ValueError(f"Không tìm thấy công việc nào trong database cho từ khóa '{keyword}'. Vui lòng cào dữ liệu trước!")

        logger.info(f"[Synthesizer] Found {len(jobs)} jobs. Preparing summary for LLM...")

        # Format jobs into a condensed string
        jobs_summary_list = []
        for i, j in enumerate(jobs, 1):
            item_str = (
                f"{i}. [{j.source.upper()}] Tiêu đề: {j.title}\n"
                f"   Công ty: {j.company} | Địa điểm: {j.location}\n"
                f"   Mức lương: {j.salary_raw}\n"
            )
            if j.requirements:
                item_str += f"   Kỹ năng/Yêu cầu: {j.requirements}\n"
            if j.experience:
                item_str += f"   Kinh nghiệm: {j.experience}\n"
            if j.job_description:
                # Truncate description snippet to keep prompt concise
                snippet = j.job_description[:300].replace("\n", " ")
                item_str += f"   Mô tả vắn tắt: {snippet}...\n"
            jobs_summary_list.append(item_str)

        jobs_summary = "\n".join(jobs_summary_list)
        prompt = build_synthesis_prompt(keyword, len(jobs), jobs_summary)

        # Call LLM
        report_markdown = self.client.generate(prompt, system_instruction=HR_SYSTEM_PROMPT)

        # Ensure reports directory exists
        settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        # Save to markdown file
        safe_kw = re.sub(r"\W+", "_", keyword.strip().lower())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"report_{safe_kw}_{timestamp}.md"
        report_path = settings.REPORTS_DIR / report_filename

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_markdown)

        # Save to database
        model_name = getattr(self.client, "model", "llm")
        report_item = ReportItem(
            keyword=keyword,
            total_jobs_analyzed=len(jobs),
            llm_model=model_name,
            summary_markdown=report_markdown,
            metrics_json="{}"
        )
        report_repo.save_report(report_item)

        logger.info(f"[Synthesizer] Successfully saved market report to: {report_path}")
        return report_markdown, report_path
