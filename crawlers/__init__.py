"""Crawlers package for cv_scan."""
from .base import BaseCrawler
from .itviec import ITViecCrawler
from .careerviet import CareerVietCrawler
from .topcv import TopCVCrawler
from .facebook import FacebookCrawler
from .joywork import JoyWorkCrawler
from .linkedin import LinkedInCrawler
from .flexjobs import FlexJobsCrawler
from .glassdoor import GlassdoorCrawler
from .factory import crawler_factory

__all__ = [
    "BaseCrawler",
    "ITViecCrawler",
    "CareerVietCrawler",
    "TopCVCrawler",
    "FacebookCrawler",
    "JoyWorkCrawler",
    "LinkedInCrawler",
    "FlexJobsCrawler",
    "GlassdoorCrawler",
    "crawler_factory",
]
