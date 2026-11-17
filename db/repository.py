"""Data repository for Job and Report operations in SQLite."""
import sqlite3
from typing import List, Optional, Tuple, Dict, Any
from db.database import db
from db.models import JobItem, ReportItem
from utils.logger import logger
from utils.text_cleaner import strip_accents, is_keyword_relevant


class JobRepository:
    def __init__(self, database=db):
        self.db = database

    def save_job(self, job: JobItem) -> bool:
        """
        Inserts a single job.
        Returns True if newly inserted, False if already existed and was updated, or False if irrelevant.
        """
        if job.keyword_searched and not is_keyword_relevant(job.title, job.job_description, job.keyword_searched):
            logger.info(f"[Guardrail] Rejected irrelevant job '{job.title}' for keyword '{job.keyword_searched}'")
            return False

        exists_sql = "SELECT id FROM jobs WHERE job_hash = ?"
        upsert_sql = """
        INSERT INTO jobs (
            source, job_hash, title, company, location, salary_raw,
            salary_min, salary_max, salary_currency, experience,
            job_description, requirements, benefits, job_url,
            posted_date, keyword_searched
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(job_hash) DO UPDATE SET
            salary_raw = excluded.salary_raw,
            salary_min = COALESCE(excluded.salary_min, jobs.salary_min),
            salary_max = COALESCE(excluded.salary_max, jobs.salary_max),
            job_description = CASE WHEN length(excluded.job_description) > length(jobs.job_description) THEN excluded.job_description ELSE jobs.job_description END,
            requirements = CASE WHEN length(excluded.requirements) > length(jobs.requirements) THEN excluded.requirements ELSE jobs.requirements END,
            benefits = CASE WHEN length(excluded.benefits) > length(jobs.benefits) THEN excluded.benefits ELSE jobs.benefits END
        """
        try:
            with self.db.get_connection() as conn:
                existing = conn.execute(exists_sql, (job.job_hash,)).fetchone()
                conn.execute(
                    upsert_sql,
                    (
                        job.source, job.job_hash, job.title, job.company, job.location, job.salary_raw,
                        job.salary_min, job.salary_max, job.salary_currency, job.experience,
                        job.job_description, job.requirements, job.benefits, job.job_url,
                        job.posted_date, job.keyword_searched
                    )
                )
                conn.commit()
                return existing is None
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            logger.error(f"Error saving job {job.title}: {e}")
            return False

    def save_jobs_batch(self, jobs: List[JobItem]) -> Tuple[int, int]:
        """
        Saves a batch of jobs.
        Returns (new_inserted_count, updated_or_existing_count).
        """
        inserted = 0
        for job in jobs:
            if self.save_job(job):
                inserted += 1
        duplicates = len(jobs) - inserted
        return inserted, duplicates

    def get_jobs_by_keyword(self, keyword: str, limit: int = 150) -> List[JobItem]:
        """
        Retrieves jobs matching a keyword from title, description, or keyword_searched.
        """
        clean_kw = f"%{strip_accents(keyword.strip().lower())}%"
        sql = """
        SELECT * FROM jobs
        WHERE strip_accents(keyword_searched) LIKE ?
           OR strip_accents(title) LIKE ?
           OR strip_accents(job_description) LIKE ?
           OR strip_accents(requirements) LIKE ?
        ORDER BY crawled_at DESC
        LIMIT ?
        """
        with self.db.get_connection() as conn:
            rows = conn.execute(sql, (clean_kw, clean_kw, clean_kw, clean_kw, limit)).fetchall()
            return [self._row_to_job(r) for r in rows]

    def search_jobs(
        self,
        keyword: Optional[str] = None,
        source: Optional[str] = None,
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        workplace_mode: Optional[str] = None,
        region: Optional[str] = None,
        has_salary_only: bool = False,
        is_remote_only: bool = False,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[JobItem], int]:
        """
        Advanced filtered search with pagination.
        Supports filtering by keyword, source, location/region, job_type, workplace_mode, salary.
        """
        conditions = []
        params = []

        if keyword and keyword.strip():
            kw = f"%{strip_accents(keyword.strip().lower())}%"
            conditions.append(
                "(strip_accents(title) LIKE ? OR strip_accents(company) LIKE ? OR strip_accents(job_description) LIKE ? OR strip_accents(requirements) LIKE ? OR strip_accents(keyword_searched) LIKE ?)"
            )
            params.extend([kw, kw, kw, kw, kw])

        if source and source.strip() and source.lower() != "all":
            conditions.append("lower(source) = ?")
            params.append(source.strip().lower())

        # Filter by Job Type (Loại công việc: Full-time, Part-time, Contract, Intern)
        if job_type and job_type.strip() and job_type.lower() != "all":
            jt = job_type.strip().lower()
            if jt in ["intern", "fresher", "internship", "thực tập", "trainee"]:
                conditions.append(
                    "(lower(title) LIKE '%intern%' OR lower(title) LIKE '%fresher%' OR lower(title) LIKE '%thuc tap%' "
                    "OR lower(title) LIKE '%thực tập%' OR lower(title) LIKE '%trainee%' OR lower(job_description) LIKE '%intern%' "
                    "OR lower(job_description) LIKE '%thuc tap%' OR lower(job_description) LIKE '%thực tập%')"
                )
            elif jt in ["part_time", "part-time", "bán thời gian"]:
                conditions.append(
                    "(lower(title) LIKE '%part-time%' OR lower(title) LIKE '%parttime%' "
                    "OR lower(title) LIKE '%ban thoi gian%' OR lower(title) LIKE '%bán thời gian%' OR lower(job_description) LIKE '%part-time%')"
                )
            elif jt in ["contract", "freelance", "hợp đồng"]:
                conditions.append(
                    "(lower(title) LIKE '%contract%' OR lower(title) LIKE '%freelance%' "
                    "OR lower(title) LIKE '%hop dong%' OR lower(title) LIKE '%hợp đồng%' OR lower(job_description) LIKE '%contract%' OR lower(job_description) LIKE '%freelance%')"
                )
            elif jt in ["full_time", "full-time", "toàn thời gian"]:
                conditions.append(
                    "(NOT (lower(title) LIKE '%intern%' OR lower(title) LIKE '%fresher%' OR lower(title) LIKE '%thuc tap%' "
                    "OR lower(title) LIKE '%thực tập%' OR lower(title) LIKE '%trainee%' OR lower(title) LIKE '%part-time%' "
                    "OR lower(title) LIKE '%contract%' OR lower(title) LIKE '%freelance%'))"
                )

        # Filter by Workplace Mode (Hình thức triển khai: Remote, Hybrid, On-site)
        wm = (workplace_mode or "").strip().lower()
        if is_remote_only or wm == "remote" or (location and any(r in location.strip().lower() for r in ["remote", "online", "tu xa"])):
            conditions.append(
                "("
                "lower(location) LIKE '%remote%' OR lower(location) LIKE '%tu xa%' OR lower(location) LIKE '%từ xa%' "
                "OR lower(location) LIKE '%online%' OR lower(location) LIKE '%wfh%' OR lower(location) LIKE '%work from home%' "
                "OR lower(title) LIKE '%remote%' OR lower(title) LIKE '%tu xa%' OR lower(title) LIKE '%từ xa%' OR lower(title) LIKE '%online%' "
                "OR lower(requirements) LIKE '%remote%' OR lower(requirements) LIKE '%từ xa%'"
                ")"
            )
        elif wm == "hybrid":
            conditions.append(
                "(lower(location) LIKE '%hybrid%' OR lower(title) LIKE '%hybrid%' OR lower(job_description) LIKE '%hybrid%')"
            )
        elif wm in ["onsite", "at_office"]:
            conditions.append(
                "("
                "lower(location) LIKE '%onsite%' OR lower(location) LIKE '%at office%' "
                "OR (NOT (lower(location) LIKE '%remote%' OR lower(location) LIKE '%tu xa%' OR lower(location) LIKE '%từ xa%' "
                "OR lower(location) LIKE '%online%' OR lower(location) LIKE '%hybrid%' OR lower(title) LIKE '%remote%' OR lower(title) LIKE '%hybrid%'))"
                ")"
            )

        # Filter by Deployment Region / Location (Nơi triển khai công việc)
        target_loc = (region or location or "").strip().lower()
        if target_loc and target_loc != "all" and target_loc != "remote":
            if any(k in target_loc for k in ["ha noi", "hanoi", "north", "mien_bac"]):
                conditions.append(
                    "(lower(location) LIKE '%ha noi%' OR lower(location) LIKE '%hà nội%' OR lower(location) LIKE '%hanoi%' "
                    "OR lower(location) LIKE '%bac ninh%' OR lower(location) LIKE '%bắc ninh%' OR lower(location) LIKE '%hai phong%' OR lower(location) LIKE '%hải phòng%')"
                )
            elif any(k in target_loc for k in ["ho chi minh", "hcm", "south", "mien_nam"]):
                conditions.append(
                    "(lower(location) LIKE '%ho chi minh%' OR lower(location) LIKE '%hồ chí minh%' OR lower(location) LIKE '%hcm%' "
                    "OR lower(location) LIKE '%sai gon%' OR lower(location) LIKE '%sài gòn%' OR lower(location) LIKE '%binh duong%' "
                    "OR lower(location) LIKE '%bình dương%' OR lower(location) LIKE '%dong nai%' OR lower(location) LIKE '%đồng nai%' OR lower(location) LIKE '%cu chi%')"
                )
            elif any(k in target_loc for k in ["da nang", "central", "mien_trung"]):
                conditions.append(
                    "(lower(location) LIKE '%da nang%' OR lower(location) LIKE '%đà nẵng%' OR lower(location) LIKE '%hue%' OR lower(location) LIKE '%huế%')"
                )
            elif any(k in target_loc for k in ["global", "quoc_te", "worldwide", "usa"]):
                conditions.append(
                    "(lower(location) LIKE '%worldwide%' OR lower(location) LIKE '%global%' OR lower(location) LIKE '%usa%' "
                    "OR lower(location) LIKE '%europe%' OR lower(location) LIKE '%, va%' OR lower(location) LIKE '%, tx%' "
                    "OR lower(location) LIKE '%, ca%' OR lower(location) LIKE '%, ny%' OR lower(location) LIKE '%, oh%' OR lower(location) LIKE '%, mn%')"
                )
            else:
                loc_term = f"%{target_loc}%"
                conditions.append("lower(location) LIKE ?")
                params.append(loc_term)

        if has_salary_only:
            conditions.append("(salary_min IS NOT NULL OR salary_max IS NOT NULL)")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        count_sql = f"SELECT COUNT(*) FROM jobs {where_clause}"
        offset = max(0, (page - 1) * limit)
        data_sql = f"""
        SELECT * FROM jobs
        {where_clause}
        ORDER BY crawled_at DESC, id DESC
        LIMIT ? OFFSET ?
        """

        with self.db.get_connection() as conn:
            total = conn.execute(count_sql, params).fetchone()[0]
            data_params = list(params) + [limit, offset]
            rows = conn.execute(data_sql, data_params).fetchall()
            jobs = [self._row_to_job(r) for r in rows]
            return jobs, total

    def get_stats(self) -> Dict[str, Any]:
        """Returns overview statistics of stored jobs."""
        with self.db.get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            by_source = conn.execute(
                "SELECT source, COUNT(*) as count FROM jobs GROUP BY source"
            ).fetchall()
            top_companies = conn.execute(
                "SELECT company, COUNT(*) as count FROM jobs WHERE company != 'Unknown' GROUP BY company ORDER BY count DESC LIMIT 5"
            ).fetchall()

            return {
                "total_jobs": total,
                "by_source": {r["source"]: r["count"] for r in by_source},
                "top_companies": [{r["company"]: r["count"]} for r in top_companies]
            }

    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> JobItem:
        return JobItem(
            id=row["id"],
            source=row["source"],
            job_hash=row["job_hash"],
            title=row["title"],
            company=row["company"],
            location=row["location"],
            salary_raw=row["salary_raw"],
            salary_min=row["salary_min"],
            salary_max=row["salary_max"],
            salary_currency=row["salary_currency"],
            experience=row["experience"],
            job_description=row["job_description"],
            requirements=row["requirements"],
            benefits=row["benefits"],
            job_url=row["job_url"],
            posted_date=row["posted_date"],
            crawled_at=row["crawled_at"],
            keyword_searched=row["keyword_searched"]
        )


class ReportRepository:
    def __init__(self, database=db):
        self.db = database

    def save_report(self, report: ReportItem) -> int:
        """Saves a generated market report."""
        sql = """
        INSERT INTO reports (keyword, total_jobs_analyzed, llm_model, summary_markdown, metrics_json)
        VALUES (?, ?, ?, ?, ?)
        """
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                sql,
                (report.keyword, report.total_jobs_analyzed, report.llm_model, report.summary_markdown, report.metrics_json)
            )
            conn.commit()
            return cursor.lastrowid

    def get_latest_report(self, keyword: str) -> Optional[ReportItem]:
        """Retrieves the newest report for a specific keyword."""
        clean_kw = f"%{keyword.strip().lower()}%"
        sql = """
        SELECT * FROM reports
        WHERE lower(keyword) LIKE ?
        ORDER BY created_at DESC
        LIMIT 1
        """
        with self.db.get_connection() as conn:
            row = conn.execute(sql, (clean_kw,)).fetchone()
            if not row:
                return None
            return ReportItem(
                id=row["id"],
                keyword=row["keyword"],
                total_jobs_analyzed=row["total_jobs_analyzed"],
                llm_model=row["llm_model"],
                summary_markdown=row["summary_markdown"],
                metrics_json=row["metrics_json"],
                created_at=row["created_at"]
            )

    def list_reports(self, limit: int = 15) -> List[ReportItem]:
        """Lists recent reports."""
        sql = "SELECT * FROM reports ORDER BY created_at DESC LIMIT ?"
        with self.db.get_connection() as conn:
            rows = conn.execute(sql, (limit,)).fetchall()
            return [
                ReportItem(
                    id=r["id"],
                    keyword=r["keyword"],
                    total_jobs_analyzed=r["total_jobs_analyzed"],
                    llm_model=r["llm_model"],
                    summary_markdown=r["summary_markdown"],
                    metrics_json=r["metrics_json"],
                    created_at=r["created_at"]
                )
                for r in rows
            ]


job_repo = JobRepository()
report_repo = ReportRepository()
