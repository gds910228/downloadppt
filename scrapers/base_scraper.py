#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
爬虫基类，提供基础功能
"""

import os
import time
import random
import requests
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from tqdm import tqdm

class BaseScraper(ABC):
    """爬虫基类"""
    
    def __init__(self):
        """初始化基类"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    @abstractmethod
    def search(self, keyword, max_results=10):
        """
        搜索PPT
        
        Args:
            keyword (str): 搜索关键词
            max_results (int): 最大结果数
            
        Returns:
            list: 搜索结果列表
        """
        pass 