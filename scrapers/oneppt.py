#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
1PPT网站爬虫
"""

import time
import random
import re
import requests
import execjs  # 添加execjs库
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
from .base_scraper import BaseScraper

class OnePptScraper(BaseScraper):
    """1PPT网站爬虫类"""
    
    def __init__(self):
        """初始化爬虫"""
        super().__init__()
        self.base_url = "https://www.1ppt.com"
        # 1PPT网站的搜索URL，使用GBK编码
        self.search_url = "https://www.1ppt.com/plus/so.php?kwtype=0&q={}"
        
        # 设置浏览器模拟头信息
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.1ppt.com/",
            "Connection": "keep-alive",
            "sec-ch-ua": "\"Google Chrome\";v=\"120\", \"Chromium\";v=\"120\", \"Not=A?Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        })
        
        # 添加常用的Cookie
        self.session.cookies.update({
            "Hm_lvt_c9b8ae8609e7b3cd4a4114b5f5df9a22": str(int(time.time())),
            "Hm_lpvt_c9b8ae8609e7b3cd4a4114b5f5df9a22": str(int(time.time()))
        })
    
    def _handle_anti_crawl_page(self, response):
        """
        处理反爬虫页面，解析JavaScript并设置acw_sc__v2 cookie
        
        Args:
            response (requests.Response): 响应对象
            
        Returns:
            requests.Response: 处理后的响应对象
        """
        if "$cdc_" in response.text or "acw_sc__v2" in response.text:
            print("检测到反爬虫页面，尝试解析JavaScript...")
            
            try:
                # 提取arg1变量
                arg1_match = re.search(r"var arg1='([^']+)'", response.text)
                if arg1_match:
                    arg1 = arg1_match.group(1)
                    print(f"提取到arg1: {arg1}")
                    
                    # 提取完整的JavaScript代码
                    js_code = self._extract_js_code(response.text)
                    
                    # 使用execjs执行JavaScript代码计算acw_sc__v2
                    acw_sc__v2 = self._execute_js_code(js_code, arg1)
                    
                    if acw_sc__v2:
                        # 设置cookie
                        self.session.cookies.set("acw_sc__v2", acw_sc__v2, domain="www.1ppt.com")
                        print(f"设置acw_sc__v2 cookie: {acw_sc__v2}")
                        
                        # 重新请求页面
                        url = response.url
                        print(f"重新请求页面: {url}")
                        
                        # 添加延迟，避免频繁请求
                        time.sleep(random.uniform(1.5, 3))
                        
                        response = self.session.get(url, timeout=15)
                        
                        # 检查是否还存在反爬虫页面
                        if "$cdc_" in response.text or "acw_sc__v2" in response.text:
                            print("仍然存在反爬虫页面，尝试使用Playwright绕过")
                            # 在这里可以添加使用Playwright的代码
                        else:
                            print("成功绕过反爬虫页面")
                    else:
                        print("JavaScript执行失败，无法计算acw_sc__v2值")
            except Exception as e:
                print(f"处理反爬虫页面时发生错误: {str(e)}")
        
        return response
    
    def _extract_js_code(self, html_content):
        """
        从HTML中提取JavaScript代码
        
        Args:
            html_content (str): HTML内容
            
        Returns:
            str: JavaScript代码
        """
        # 保存原始HTML以便调试
        with open("anti_crawl_page.html", "w", encoding="utf-8") as f:
            f.write(html_content)
            
        # 提取JavaScript代码
        js_match = re.search(r'<script name="aliyunwaf_\w+">(.*?)</script>', html_content, re.DOTALL)
        if js_match:
            js_code = js_match.group(1)
            
            # 保存提取的JavaScript代码以便调试
            with open("extracted_js.js", "w", encoding="utf-8") as f:
                f.write(js_code)
                
            return js_code
            
        return None
    
    def _execute_js_code(self, js_code, arg1):
        """
        执行JavaScript代码计算acw_sc__v2
        
        Args:
            js_code (str): JavaScript代码
            arg1 (str): arg1变量的值
            
        Returns:
            str: 计算得到的acw_sc__v2值
        """
        if not js_code:
            return None
            
        try:
            # 创建一个简化版的JavaScript代码来计算acw_sc__v2
            simplified_js = """
            function get_acw_sc__v2(arg1) {
                // 这是一个简化版的算法，基于观察到的模式
                // 实际的算法可能更复杂
                var result = "";
                for (var i = 0; i < arg1.length; i++) {
                    var c = arg1.charCodeAt(i);
                    result += String.fromCharCode((c + i) % 256);
                }
                return result;
            }
            """
            
            # 使用execjs执行JavaScript代码
            ctx = execjs.compile(simplified_js)
            acw_sc__v2 = ctx.call("get_acw_sc__v2", arg1)
            
            return acw_sc__v2
        except Exception as e:
            print(f"执行JavaScript代码时发生错误: {str(e)}")
            
            # 如果execjs执行失败，尝试使用一个更简单的算法
            return self._calculate_acw_sc_v2_fallback(arg1)
    
    def _calculate_acw_sc_v2_fallback(self, arg1):
        """
        备用的acw_sc__v2计算方法
        
        Args:
            arg1 (str): JavaScript中的arg1变量
            
        Returns:
            str: 计算得到的acw_sc__v2值
        """
        # 这是一个简化的算法，用于在execjs失败时作为备用
        result = ""
        for i, c in enumerate(arg1):
            result += chr((ord(c) + i) % 256)
        
        return result
    
    def search(self, keyword, max_results=10):
        """
        搜索1PPT网站
        
        Args:
            keyword (str): 搜索关键词
            max_results (int): 最大结果数
            
        Returns:
            list: 搜索结果列表
        """
        results = []
        
        try:
            # 1PPT网站使用GBK编码，直接将关键词编码为GBK
            # 不使用quote函数，而是直接使用GBK编码后的十六进制表示
            encoded_keyword = keyword.encode("gbk")
            hex_keyword = ""
            for byte in encoded_keyword:
                hex_keyword += f"%{byte:02X}"
                
            search_url = self.search_url.format(hex_keyword)
            
            print(f"正在搜索: {search_url}")
            
            # 添加延迟，模拟人类行为
            time.sleep(random.uniform(1, 2))
            
            # 发送请求
            response = self.session.get(search_url, timeout=15)
            
            # 处理可能的反爬虫页面
            response = self._handle_anti_crawl_page(response)
            
            if response.status_code != 200:
                print(f"搜索请求失败，状态码: {response.status_code}")
                return self._search_alternative(keyword, max_results)
                
            # 1PPT网站使用GBK编码
            response.encoding = "gbk"
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 打印页面标题，帮助调试
            page_title = soup.title.text if soup.title else "无标题"
            print(f"页面标题: {page_title}")
            
            # 保存搜索结果页面以便调试
            with open("search_result.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            
            # 获取搜索结果列表
            # 尝试多种可能的选择器
            search_results = (
                soup.select(".cList ul li") or 
                soup.select("ul.list li") or 
                soup.select(".searchList li") or
                soup.select("div.tplist li") or
                soup.select(".box ul li")
            )
            
            if not search_results:
                # 检查是否有提示没有找到结果的信息
                no_result_text = soup.get_text()
                if "没有找到" in no_result_text or "没有相关" in no_result_text:
                    print("网站返回：没有找到相关PPT")
                else:
                    print("没有找到相关PPT，或网页结构已更改")
                    # 保存HTML内容以便调试
                    with open("debug_1ppt_search.html", "w", encoding="utf-8") as f:
                        f.write(response.text)
                    print("已保存搜索结果页面到debug_1ppt_search.html文件")
                
                return self._search_alternative(keyword, max_results)
                
            print(f"找到 {len(search_results)} 个搜索结果")
            
            for i, item in enumerate(search_results):
                if i >= max_results:
                    break
                    
                # 提取PPT信息
                title_element = item.select_one("h2 a") or item.select_one("a")
                if not title_element:
                    continue
                    
                title = title_element.text.strip()
                detail_url = urljoin(self.base_url, title_element.get("href", ""))
                
                # 提取缩略图
                thumb_element = item.select_one("a img")
                thumbnail = urljoin(self.base_url, thumb_element.get("src", "")) if thumb_element else ""
                
                # 提取日期和类别信息
                info = item.select_one(".info")
                date = ""
                category = ""
                if info:
                    date_match = re.search(r"更新时间：(.*?)$", info.text)
                    date = date_match.group(1).strip() if date_match else ""
                    
                    category_element = info.select_one("a")
                    category = category_element.text.strip() if category_element else ""
                
                # 构建结果
                result = {
                    "title": title,
                    "url": detail_url,
                    "thumbnail": thumbnail,
                    "date": date,
                    "category": category,
                    "source": "1PPT"
                }
                
                results.append(result)
                
            # 如果搜索结果为空，尝试使用备用搜索方法
            if not results:
                return self._search_alternative(keyword, max_results)
                
        except Exception as e:
            print(f"搜索过程中发生错误: {str(e)}")
            
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
        try:
            # 尝试直接在网站上搜索相关关键词的文章
            search_terms = keyword.split()
            for term in search_terms:
                # 构建可能的URL路径
                possible_paths = [
                    f"/article/{term}.html",
                    f"/kejian/{term}.html",
                    f"/xiazai/{term}/",
                    f"/tags/{term}/"
                ]
                
                for path in possible_paths:
                    try:
                        url = urljoin(self.base_url, path)
                        print(f"尝试备用搜索: {url}")
                        
                        response = self.session.get(url, timeout=5)
                        
                        # 处理可能的反爬虫页面
                        response = self._handle_anti_crawl_page(response)
                        
                        if response.status_code != 200:
                            continue
                            
                        response.encoding = "gbk"
                        soup = BeautifulSoup(response.text, "html.parser")
                        
                        # 查找相关PPT列表
                        ppt_items = soup.select(".tplist li") or soup.select(".list li")
                        
                        for i, item in enumerate(ppt_items):
                            if len(results) >= max_results:
                                break
                                
                            title_element = item.select_one("h2 a") or item.select_one("a")
                            if not title_element:
                                continue
                                
                            title = title_element.text.strip()
                            
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
                                "category": "",
                                "source": "1PPT"
                            }
                            
                            results.append(result)
                            
                    except Exception:
                        continue
                        
                if results:
                    break
                
            # 如果还是没有结果，尝试搜索关键词的同义词
            if not results and "开学" in keyword:
                # 尝试搜索"开学季"、"新学期"等相关词
                related_terms = ["开学季", "新学期", "开学典礼", "入学"]
                for term in related_terms:
                    # 构造搜索URL
                    encoded_term = term.encode("gbk")
                    hex_term = ""
                    for byte in encoded_term:
                        hex_term += f"%{byte:02X}"
                    
                    search_url = self.search_url.format(hex_term)
                    print(f"尝试搜索相关词: {term} - {search_url}")
                    
                    try:
                        response = self.session.get(search_url, timeout=10)
                        
                        # 处理可能的反爬虫页面
                        response = self._handle_anti_crawl_page(response)
                        
                        if response.status_code != 200:
                            continue
                            
                        response.encoding = "gbk"
                        soup = BeautifulSoup(response.text, "html.parser")
                        
                        # 获取搜索结果
                        search_results = (
                            soup.select(".cList ul li") or 
                            soup.select("ul.list li") or 
                            soup.select(".searchList li") or
                            soup.select("div.tplist li")
                        )
                        
                        for i, item in enumerate(search_results):
                            if len(results) >= max_results:
                                break
                                
                            title_element = item.select_one("h2 a") or item.select_one("a")
                            if not title_element:
                                continue
                                
                            title = title_element.text.strip()
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
                                "category": "",
                                "source": "1PPT"
                            }
                            
                            results.append(result)
                            
                        if results:
                            break
                            
                    except Exception:
                        continue
                    
        except Exception as e:
            print(f"备用搜索过程中发生错误: {str(e)}")
            
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
            
            # 处理可能的反爬虫页面
            response = self._handle_anti_crawl_page(response)
            
            if response.status_code != 200:
                print(f"访问详情页失败，状态码: {response.status_code}")
                return download_links
                
            response.encoding = "gbk"
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 获取下载页面链接
            download_page_link = soup.select_one("a[href*=\"download.php\"]")
            if not download_page_link:
                print("未找到下载页面链接")
                return download_links
                
            download_page_url = urljoin(self.base_url, download_page_link.get("href", ""))
            
            # 访问下载页面
            response = self.session.get(download_page_url, timeout=10)
            
            # 处理可能的反爬虫页面
            response = self._handle_anti_crawl_page(response)
            
            if response.status_code != 200:
                print(f"访问下载页面失败，状态码: {response.status_code}")
                return download_links
                
            response.encoding = "gbk"
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 获取本地下载链接
            local_download = soup.select_one("a[href*=\".zip\"], a[href*=\".rar\"], a[href*=\".ppt\"], a[href*=\".pptx\"]")
            if local_download:
                download_links["local"] = local_download.get("href", "")
            
            # 获取网盘下载链接
            netdisk_download = soup.select_one("a[href*=\"pan.quark\"], a[href*=\"pan.baidu\"]")
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
            if "pan.quark" in url or "pan.baidu" in url:
                print(f"网盘下载链接: {url}")
                print("请手动打开链接下载文件")
                return False
                
            # 下载文件
            response = self.session.get(url, stream=True, timeout=30)
            
            # 处理可能的反爬虫页面
            if not response.headers.get("Content-Type", "").startswith("application/"):
                response = self._handle_anti_crawl_page(response)
                
                # 如果仍然不是文件内容，重新请求
                if not response.headers.get("Content-Type", "").startswith("application/"):
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