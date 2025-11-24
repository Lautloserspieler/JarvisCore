"""
Crawler service package for J.A.R.V.I.S.

This module bundles crawler-specific helpers so they can be imported from other
Jarvis components while keeping the crawler service isolated below
services/crawler_service/.
"""

from .config import CrawlerConfig, load_config  # noqa: F401
