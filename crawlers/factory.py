"""Crawler factory and registry."""
from typing import Dict, Type, List
from crawlers.base import BaseCrawler
from crawlers.itviec import ITViecCrawler
from crawlers.careerviet import CareerVietCrawler
from crawlers.topcv import TopCVCrawler
from crawlers.facebook import FacebookCrawler
from crawlers.joywork import JoyWorkCrawler
from crawlers.linkedin import LinkedInCrawler
from crawlers.flexjobs import FlexJobsCrawler
from crawlers.glassdoor import GlassdoorCrawler
from crawlers.remotive import RemotiveCrawler


class CrawlerFactory:
    _registry: Dict[str, Type[BaseCrawler]] = {
        "itviec": ITViecCrawler,
        "careerviet": CareerVietCrawler,
        "topcv": TopCVCrawler,
        "joywork": JoyWorkCrawler,
        "linkedin": LinkedInCrawler,
        "flexjobs": FlexJobsCrawler,
        "glassdoor": GlassdoorCrawler,
        "remotive": RemotiveCrawler,
        "facebook": FacebookCrawler,
    }

    @classmethod
    def get_crawler(cls, name: str) -> BaseCrawler:
        crawler_cls = cls._registry.get(name.lower().strip())
        if not crawler_cls:
            raise ValueError(f"Unknown crawler '{name}'. Supported: {list(cls._registry.keys())}")
        return crawler_cls()

    @classmethod
    def get_available_sources(cls) -> List[str]:
        return list(cls._registry.keys())


crawler_factory = CrawlerFactory
