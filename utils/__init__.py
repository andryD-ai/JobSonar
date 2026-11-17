"""Utils package for cv_scan."""
from .logger import logger
from .text_cleaner import (
    clean_html,
    generate_job_hash,
    parse_salary,
    strip_accents,
    match_location,
    is_keyword_relevant
)

__all__ = [
    "logger",
    "clean_html",
    "generate_job_hash",
    "parse_salary",
    "strip_accents",
    "match_location",
    "is_keyword_relevant"
]
