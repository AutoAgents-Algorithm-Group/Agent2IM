"""
News utilities package

This package contains configuration management and database utilities for news handling.
"""

from .config_manager import ConfigManager
from .database import NewsDatabase

__all__ = ["ConfigManager", "NewsDatabase"]
