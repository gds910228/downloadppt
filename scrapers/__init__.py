#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
爬虫模块
"""

# 导入基本爬虫
from .base_scraper import BaseScraper
from .oneppt import OnePptScraper
from .ypppt import YppptScraper

# 导入Playwright爬虫
from .playwright_scraper import PlaywrightScraper
from .oneppt_playwright import OnePptPlaywrightScraper
from .ypppt_playwright import YppptPlaywrightScraper

__all__ = [
    'BaseScraper',
    'OnePptScraper',
    'YppptScraper',
    'PlaywrightScraper',
    'OnePptPlaywrightScraper',
    'YppptPlaywrightScraper'
] 