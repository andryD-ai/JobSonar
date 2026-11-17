"""SQLite database initialization and connection management."""
import sqlite3
from typing import Optional
from pathlib import Path
from config.settings import settings
from utils.logger import logger
from utils.text_cleaner import strip_accents


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    job_hash TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    company TEXT DEFAULT 'Unknown',
    location TEXT DEFAULT 'Vietnam',
    salary_raw TEXT DEFAULT 'Thỏa thuận',
    salary_min REAL,
    salary_max REAL,
    salary_currency TEXT DEFAULT 'Unknown',
    experience TEXT,
    job_description TEXT DEFAULT '',
    requirements TEXT DEFAULT '',
    benefits TEXT DEFAULT '',
    job_url TEXT,
    posted_date TEXT,
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    keyword_searched TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_jobs_keyword ON jobs(keyword_searched);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_hash ON jobs(job_hash);
CREATE INDEX IF NOT EXISTS idx_jobs_crawled_at ON jobs(crawled_at);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    total_jobs_analyzed INTEGER DEFAULT 0,
    llm_model TEXT NOT NULL,
    summary_markdown TEXT NOT NULL,
    metrics_json TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reports_keyword ON reports(keyword);
CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created_at);
"""


class Database:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.DB_PATH
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Returns a connection with row factory configured as sqlite3.Row."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        # Register custom function for accent-insensitive search in Vietnamese
        conn.create_function("strip_accents", 1, lambda s: strip_accents(str(s).lower()) if s is not None else "")
        # Enable WAL mode for better concurrency and speed
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        """Executes table creation schema if not already present."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.get_connection() as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()
        logger.debug(f"Initialized database at: {self.db_path}")


db = Database()
