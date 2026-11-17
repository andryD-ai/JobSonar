"""Data models for jobs and reports."""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class JobItem(BaseModel):
    id: Optional[int] = None
    source: str = Field(description="Job board or platform: itviec, topcv, careerviet, facebook")
    job_hash: str = Field(description="Deterministic hash for deduplication")
    title: str
    company: Optional[str] = "Unknown"
    location: Optional[str] = "Vietnam"
    salary_raw: Optional[str] = "Thỏa thuận"
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = "Unknown"
    experience: Optional[str] = None
    job_description: Optional[str] = ""
    requirements: Optional[str] = ""
    benefits: Optional[str] = ""
    job_url: Optional[str] = ""
    posted_date: Optional[str] = None
    crawled_at: Optional[datetime] = None
    keyword_searched: str = ""

    @property
    def is_remote(self) -> bool:
        from utils.text_cleaner import is_remote_job
        return is_remote_job(self.title, self.location, self.job_description)

    @property
    def job_type(self) -> str:
        from utils.text_cleaner import get_job_type
        return get_job_type(self.title, self.job_description, self.benefits)

    @property
    def workplace_mode(self) -> str:
        from utils.text_cleaner import get_workplace_mode
        return get_workplace_mode(self.title, self.location, self.job_description)

    @property
    def deployment_region(self) -> str:
        from utils.text_cleaner import get_deployment_region
        return get_deployment_region(self.location, self.title)

    def to_dict(self) -> Dict[str, Any]:
        d = self.model_dump()
        d["is_remote"] = self.is_remote
        d["job_type"] = self.job_type
        d["workplace_mode"] = self.workplace_mode
        d["deployment_region"] = self.deployment_region
        return d


class ReportItem(BaseModel):
    id: Optional[int] = None
    keyword: str
    total_jobs_analyzed: int
    llm_model: str
    summary_markdown: str
    metrics_json: Optional[str] = "{}"
    created_at: Optional[datetime] = None
