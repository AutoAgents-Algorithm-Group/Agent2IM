"""
News scrapers package

This package contains scrapers for different news sources and trending repositories.
"""

from .techcrunch_scraper import TechCrunchScraper
from .verge_scraper import VergeScraper
from .github_trending_scraper import GitHubTrendingScraper
from .product_hunt_scraper import ProductHuntScraper
from .a16z_scraper import A16zScraper
from .kr36_scraper import Kr36Scraper

__all__ = [
    "TechCrunchScraper",
    "VergeScraper", 
    "GitHubTrendingScraper",
    "ProductHuntScraper",
    "A16zScraper",
    "Kr36Scraper"
]
