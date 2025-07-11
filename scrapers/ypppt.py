#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
优品PPT网站爬虫
"""

import time
import random
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
from .base_scraper import BaseScraper

class YppptScraper(BaseScraper):
    """优品PPT网站爬虫类"""
    
    def __init__(self):
        """初始化爬虫"""
        super().__init__()
        self.base_url = "https://www.ypppt.com"
        # 优品PPT的搜索URL
        self.search_url = "https://www.ypppt.com/search/{}.html"
    
    def search(self, keyword, max_results=10):
        """
        搜索优品PPT网站
        
        Args:
            keyword (str): 搜索关键词
            max_results (int): 最大结果数
            
        Returns:
            list: 搜索结果列表
        """
        results = []
        
        try:
            # 构造搜索URL
            encoded_keyword = quote(keyword)
            search_url = self.search_url.format(encoded_keyword)
            
            print(f"正在搜索: {search_url}")
            response = self.session.get(search_url, timeout=10)
            if response.status_code != 200:
                print(f"搜索请求失败，状态码: {response.status_code}")
                # 尝试备用搜索方法
                return self._search_alternative(keyword, max_results)
                
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 检查是否是404页面
            if soup.select_one("title") and "404" in soup.select_one("title").text:
                print("搜索结果页面返回404，可能是网站不支持该关键词搜索")
                # 尝试使用备用搜索方法
                return self._search_alternative(keyword, max_results)
                
            # 获取搜索结果列表
            search_results = soup.select(".box ul li")
            
            if not search_results:
                print("没有找到相关PPT，或网页结构已更改")
                # 尝试备用搜索方法
                return self._search_alternative(keyword, max_results)
                
            for i, item in enumerate(search_results):
                if i >= max_results:
                    break
                    
                # 提取PPT信息
                title_element = item.select_one("h2 a") or item.select_one("a")
                if not title_element:
                    continue
                    
                title = title_element.text.strip() or title_element.get("title", "")
                detail_url = urljoin(self.base_url, title_element.get("href", ""))
                
                # 提取缩略图
                thumb_element = item.select_one("img")
                thumbnail = urljoin(self.base_url, thumb_element.get("src", "")) if thumb_element else ""
                
                # 提取日期信息
                date = ""
                date_element = item.select_one(".date") or item.select_one(".info")
                if date_element:
                    date = date_element.text.strip()
                    
                # 构建结果
                result = {
                    "title": title,
                    "url": detail_url,
                    "thumbnail": thumbnail,
                    "date": date,
                    "source": "优品PPT"
                }
                
                results.append(result)
                
        except Exception as e:
            print(f"搜索过程中发生错误: {str(e)}")
            # 尝试备用搜索方法
            return self._search_alternative(keyword, max_results)
            
        return results
    
    def _search_alternative(self, keyword, max_results=10):
        """
        备用搜索方法，在主搜索方法失败时尝试
        
        Args:
            keyword (str): 搜索关键词
            max_results (int): 最大结果数
            
        Returns:
            list: 搜索结果列表
        """
        results = []
        
        # 尝试多种备用搜索方法
        search_methods = [
            self._search_by_index_php,
            self._search_by_category,
            self._search_by_tags,
            self._search_by_keywords
        ]
        
        for method in search_methods:
            try:
                method_results = method(keyword, max_results)
                if method_results:
                    results.extend(method_results)
                    if len(results) >= max_results:
                        return results[:max_results]
            except Exception as e:
                print(f"备用搜索方法出错: {str(e)}")
                continue
                
        return results[:max_results] if results else []
    
    def _search_by_index_php(self, keyword, max_results=10):
        """使用index.php搜索接口"""
        results = []
        try:
            # 尝试使用首页搜索框
            search_url = f"{self.base_url}/index.php?s={quote(keyword)}"
            print(f"尝试备用搜索 (index.php): {search_url}")
            
            response = self.session.get(search_url, timeout=10)
            if response.status_code != 200:
                return results
                
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 尝试查找结果列表
            search_results = soup.select(".list ul li") or soup.select(".box ul li")
            
            if not search_results:
                return results
                
            for i, item in enumerate(search_results):
                if i >= max_results:
                    break
                    
                title_element = item.select_one("h2 a") or item.select_one("a")
                if not title_element:
                    continue
                    
                title = title_element.text.strip() or title_element.get("title", "")
                detail_url = urljoin(self.base_url, title_element.get("href", ""))
                
                # 检查标题是否包含关键词，如果不包含则跳过
                if keyword.lower() not in title.lower():
                    continue
                
                # 提取缩略图
                thumb_element = item.select_one("img")
                thumbnail = urljoin(self.base_url, thumb_element.get("src", "")) if thumb_element else ""
                
                # 构建结果
                result = {
                    "title": title,
                    "url": detail_url,
                    "thumbnail": thumbnail,
                    "date": "",
                    "source": "优品PPT"
                }
                
                results.append(result)
                
        except Exception as e:
            print(f"index.php搜索过程中发生错误: {str(e)}")
            
        return results
    
    def _search_by_category(self, keyword, max_results=10):
        """通过分类页面搜索"""
        results = []
        try:
            # 可能的分类路径
            categories = [
                "/moban/", "/kejian/", "/jieri/", "/hangye/", 
                "/beijing/", "/sucai/", "/tubiao/"
            ]
            
            for category in categories:
                category_url = urljoin(self.base_url, category)
                print(f"尝试在分类中搜索: {category_url}")
                
                response = self.session.get(category_url, timeout=8)
                if response.status_code != 200:
                    continue
                    
                response.encoding = "utf-8"
                soup = BeautifulSoup(response.text, "html.parser")
                
                # 获取分类下的PPT列表
                items = soup.select(".list ul li") or soup.select(".box ul li")
                
                for item in items:
                    if len(results) >= max_results:
                        break
                        
                    title_element = item.select_one("h2 a") or item.select_one("a")
                    if not title_element:
                        continue
                        
                    title = title_element.text.strip() or title_element.get("title", "")
                    
                    # 检查标题是否包含关键词
                    if keyword.lower() not in title.lower():
                        continue
                        
                    detail_url = urljoin(self.base_url, title_element.get("href", ""))
                    
                    # 提取缩略图
                    thumb_element = item.select_one("img")
                    thumbnail = urljoin(self.base_url, thumb_element.get("src", "")) if thumb_element else ""
                    
                    # 构建结果
                    result = {
                        "title": title,
                        "url": detail_url,
                        "thumbnail": thumbnail,
                        "date": "",
                        "source": "优品PPT"
                    }
                    
                    results.append(result)
                    
                if results:
                    break
                    
        except Exception as e:
            print(f"分类搜索过程中发生错误: {str(e)}")
            
        return results
    
    def _search_by_tags(self, keyword, max_results=10):
        """通过标签搜索"""
        results = []
        try:
            # 尝试直接访问标签页面
            tag_url = f"{self.base_url}/tag/{quote(keyword)}/"
            print(f"尝试标签搜索: {tag_url}")
            
            response = self.session.get(tag_url, timeout=8)
            if response.status_code != 200:
                return results
                
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 获取标签页面的PPT列表
            items = soup.select(".list ul li") or soup.select(".box ul li")
            
            for i, item in enumerate(items):
                if i >= max_results:
                    break
                    
                title_element = item.select_one("h2 a") or item.select_one("a")
                if not title_element:
                    continue
                    
                title = title_element.text.strip() or title_element.get("title", "")
                detail_url = urljoin(self.base_url, title_element.get("href", ""))
                
                # 提取缩略图
                thumb_element = item.select_one("img")
                thumbnail = urljoin(self.base_url, thumb_element.get("src", "")) if thumb_element else ""
                
                # 构建结果
                result = {
                    "title": title,
                    "url": detail_url,
                    "thumbnail": thumbnail,
                    "date": "",
                    "source": "优品PPT"
                }
                
                results.append(result)
                
        except Exception as e:
            print(f"标签搜索过程中发生错误: {str(e)}")
            
        return results
    
    def _search_by_keywords(self, keyword, max_results=10):
        """通过关键词分词搜索"""
        results = []
        try:
            # 分词处理关键词
            search_terms = keyword.split()
            
            # 如果是复合词，尝试拆分
            if len(search_terms) > 1:
                for term in search_terms:
                    if len(term) >= 2:  # 只搜索长度大于等于2的词
                        term_url = f"{self.base_url}/search/{quote(term)}.html"
                        print(f"尝试关键词分词搜索: {term_url}")
                        
                        response = self.session.get(term_url, timeout=8)
                        if response.status_code != 200:
                            continue
                            
                        response.encoding = "utf-8"
                        soup = BeautifulSoup(response.text, "html.parser")
                        
                        # 检查是否是404页面
                        if soup.select_one("title") and "404" in soup.select_one("title").text:
                            continue
                            
                        # 获取搜索结果列表
                        items = soup.select(".box ul li") or soup.select(".list ul li")
                        
                        for i, item in enumerate(items):
                            if len(results) >= max_results:
                                break
                                
                            title_element = item.select_one("h2 a") or item.select_one("a")
                            if not title_element:
                                continue
                                
                            title = title_element.text.strip() or title_element.get("title", "")
                            
                            # 检查标题是否相关
                            if not any(t in title.lower() for t in search_terms):
                                continue
                                
                            detail_url = urljoin(self.base_url, title_element.get("href", ""))
                            
                            # 提取缩略图
                            thumb_element = item.select_one("img")
                            thumbnail = urljoin(self.base_url, thumb_element.get("src", "")) if thumb_element else ""
                            
                            # 构建结果
                            result = {
                                "title": title,
                                "url": detail_url,
                                "thumbnail": thumbnail,
                                "date": "",
                                "source": "优品PPT"
                            }
                            
                            results.append(result)
                            
                    if results:
                        break
                        
        except Exception as e:
            print(f"关键词分词搜索过程中发生错误: {str(e)}")
            
        return results
    
    def get_download_links(self, detail_url):
        """
        获取PPT下载链接
        
        Args:
            detail_url (str): PPT详情页URL
            
        Returns:
            dict: 包含本地下载链接和网盘下载链接的字典
        """
        download_links = {
            "local": "",
            "netdisk": ""
        }
        
        try:
            # 访问详情页
            response = self.session.get(detail_url, timeout=10)
            if response.status_code != 200:
                print(f"访问详情页失败，状态码: {response.status_code}")
                return download_links
                
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 获取本地下载链接
            local_download = soup.select_one(".down-button a") or soup.select_one("a.downbtn") or soup.select_one("a[href*=\"/d/\"]")
            if local_download:
                download_links["local"] = urljoin(self.base_url, local_download.get("href", ""))
            
            # 获取网盘下载链接
            netdisk_download = soup.select_one("a[href*=\"pan.baidu\"]") or soup.select_one("a[href*=\"pan.quark\"]")
            if netdisk_download:
                download_links["netdisk"] = netdisk_download.get("href", "")
                
        except Exception as e:
            print(f"获取下载链接过程中发生错误: {str(e)}")
            
        return download_links
    
    def download(self, url, file_path):
        """
        下载PPT文件
        
        Args:
            url (str): 下载链接
            file_path (str): 保存文件路径
            
        Returns:
            bool: 下载是否成功
        """
        try:
            # 判断是否是网盘链接
            if "pan.baidu" in url or "pan.quark" in url:
                print(f"网盘下载链接: {url}")
                print("请手动打开链接下载文件")
                return False
                
            # 下载文件
            response = self.session.get(url, stream=True, timeout=30)
            if response.status_code != 200:
                print(f"下载文件失败，状态码: {response.status_code}")
                return False
                
            # 保存文件
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        
            print(f"文件下载成功: {file_path}")
            return True
            
        except Exception as e:
            print(f"下载文件过程中发生错误: {str(e)}")
            return False 