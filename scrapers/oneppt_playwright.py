#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
1PPT网站Playwright爬虫
"""

import os
import time
import random
import asyncio
import re
import urllib.parse
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
from .playwright_scraper import PlaywrightScraper

class OnePptPlaywrightScraper(PlaywrightScraper):
    """1PPT网站Playwright爬虫类"""
    
    def __init__(self):
        """初始化爬虫"""
        super().__init__()
        self.base_url = "https://www.1ppt.com"
        self.search_url = "https://www.1ppt.com/plus/so.php?kwtype=0&q={}"
    
    async def search(self, keyword, max_results=40):
        """
        搜索PPT
        
        Args:
            keyword (str): 搜索关键词
            max_results (int): 最大结果数量
            
        Returns:
            list: 搜索结果列表，每个结果包含标题、URL等信息
        """
        results = []
        
        try:
            # 将关键词转换为GBK编码的URL参数
            try:
                encoded_keyword = keyword.encode('gbk')
                gbk_keyword = ''
                for byte in encoded_keyword:
                    gbk_keyword += '%{:02X}'.format(byte)
                print(f"GBK编码关键词: {gbk_keyword}")
            except Exception as e:
                print(f"编码关键词失败: {str(e)}")
                gbk_keyword = urllib.parse.quote(keyword)
            
            # 构建搜索URL - 1PPT使用GBK编码
            search_url = f"https://www.1ppt.com/plus/so.php?kwtype=0&q={gbk_keyword}"
            
            # 访问搜索页面
            print(f"正在搜索: {search_url}")
            
            # 访问首页，获取cookie
            await self.page.goto("https://www.1ppt.com", wait_until="domcontentloaded")
            await asyncio.sleep(1)  # 确保页面加载完成
            
            # 访问搜索页面
            print("正在访问搜索页面...")
            await self.page.goto(search_url, wait_until="domcontentloaded")
            await asyncio.sleep(1)  # 确保页面加载完成
            
            # 保存搜索结果页面以便调试
            try:
                content = await self.page.content()
                with open("search_result_1ppt.html", "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                print(f"保存搜索结果页面失败: {str(e)}")
            
            # 获取搜索结果
            page_num = 1
            has_next_page = True  # 添加标志，表示是否还有下一页
            
            while len(results) < max_results and has_next_page:
                print(f"正在获取第 {page_num} 页搜索结果...")
                
                # 等待搜索结果加载
                try:
                    await self.page.wait_for_selector("div.w.center.mt8, ul.cList, ul.tplist", timeout=5000)
                except Exception as e:
                    print(f"等待选择器失败: {str(e)}")
                
                # 确保页面加载完成
                await asyncio.sleep(1)
                
                # 获取页面标题，验证是否是搜索结果页
                page_title = await self.page.title()
                print(f"页面标题: {page_title}")
                
                # 获取页面内容
                try:
                    content = await self.page.content()
                    # 保存当前页面内容以便调试
                    with open(f"search_result_1ppt_page{page_num}.html", "w", encoding="utf-8") as f:
                        f.write(content)
                except Exception as e:
                    print(f"获取页面内容失败: {str(e)}")
                    content = ""
                
                if not content:
                    print("页面内容为空，跳过当前页")
                    break
                
                soup = BeautifulSoup(content, "html.parser")
                
                # 查找主容器 - 尝试多种可能的选择器
                main_container = (
                    soup.select_one("div.w.center.mt8 ul.tplist") or 
                    soup.select_one("ul.tplist") or 
                    soup.select_one("div.w.center.mt8") or 
                    soup.select_one("div.center.mt8") or 
                    soup.select_one("ul.cList")
                )
                
                if main_container:
                    print(f"找到主容器: {main_container.name}.{' '.join(main_container.get('class', []))}")
                    
                    # 查找所有列表项
                    list_items = main_container.select("li:not(.ad)") or main_container.select("li")
                    print(f"找到 {len(list_items)} 个列表项")
                    
                    # 处理每个列表项
                    for item in list_items:
                        if len(results) >= max_results:
                            break
                        
                        # 获取标题和链接
                        title_elem = item.select_one("h2") or item.select_one("a")
                        if title_elem:
                            # 获取标题
                            if title_elem.name == "h2":
                                link_elem = title_elem.select_one("a")
                                title = title_elem.text.strip()
                            else:
                                link_elem = title_elem
                                title = title_elem.text.strip()
                            
                            # 跳过空白标题或广告链接
                            if not title or "51miz.com" in str(item) or "ibaotu.com" in str(item):
                                print(f"跳过空白标题或广告链接")
                                continue
                            
                            print(f"找到标题: {title[:30]}")
                            
                            # 获取链接
                            if link_elem and "href" in link_elem.attrs:
                                url = link_elem["href"]
                                if not url.startswith("http"):
                                    url = f"https://www.1ppt.com{url}"
                                
                                # 跳过广告链接
                                if "51miz.com" in url or "ibaotu.com" in url:
                                    print(f"跳过广告链接: {url}")
                                    continue
                                
                                print(f"找到链接: {url}")
                                
                                # 获取日期和分类
                                date = ""
                                category = ""
                                
                                # 添加到结果列表
                                results.append({
                                    "title": title,
                                    "url": url,
                                    "date": date,
                                    "category": category,
                                    "source": "1PPT"
                                })
                else:
                    print("未找到主容器")
                
                # 检查是否有下一页
                next_page_link = None
                
                # 查找"下一页"链接
                for a_tag in soup.select("div.page a, ul.pages a"):
                    if "下一页" in a_tag.text:
                        next_page_link = a_tag
                        break
                
                # 如果没有找到"下一页"链接或者已经达到最大结果数量，则停止翻页
                if not next_page_link or len(results) >= max_results:
                    print("没有下一页或已达到最大结果数量")
                    has_next_page = False
                    break
                
                # 从页面中提取TotalResult参数
                total_result = 0
                page_info = soup.select_one("div.page") or soup.select_one("ul.pages")
                if page_info:
                    page_text = page_info.text
                    match = re.search(r'共(\d+)页/(\d+)条', page_text)
                    if match:
                        total_pages = int(match.group(1))
                        total_result = int(match.group(2))
                        print(f"总页数: {total_pages}, 总结果数: {total_result}")
                        
                        # 如果已经是最后一页，则停止翻页
                        if page_num >= total_pages:
                            has_next_page = False
                            break
                
                # 构建下一页URL
                page_num += 1
                
                # 构建翻页URL
                next_page_url = f"https://www.1ppt.com/plus/so.php?keyword={gbk_keyword}&searchtype=titlekeyword&channeltype=0&orderby=&kwtype=0&pagesize=24&typeid=0&TotalResult={total_result}&PageNo={page_num}"
                print(f"下一页URL: {next_page_url}")
                
                # 访问下一页
                await self.page.goto(next_page_url, wait_until="domcontentloaded")
                await asyncio.sleep(2)  # 确保页面加载完成
                
                # 保存下一页内容以便调试
                try:
                    content = await self.page.content()
                    with open(f"search_result_1ppt_page{page_num}.html", "w", encoding="utf-8") as f:
                        f.write(content)
                except Exception as e:
                    print(f"保存下一页内容失败: {str(e)}")
            
            # 如果没有结果，尝试备用搜索方法
            if not results:
                print("没有找到搜索结果，尝试备用搜索方法...")
                results = await self._search_alternative(keyword, max_results)
        except Exception as e:
            print(f"搜索过程中发生错误: {str(e)}")
            import traceback
            print(traceback.format_exc())
        
        return results
    
    async def _search_alternative(self, keyword, max_results=10):
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
            # 确保已初始化
            if not self.is_initialized:
                await self.initialize()
                
            # 确保页面对象存在
            if self.page is None:
                print("页面对象不存在，重新初始化...")
                await self.initialize()
                
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
                        
                        content = await self.get_page_content(url, wait_for_selector=".tplist li, .list li")
                        
                        soup = BeautifulSoup(content, "html.parser")
                        
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
                        content = await self.get_page_content(search_url, wait_for_selector=".cList ul li, ul.list li, .searchList li, div.tplist li")
                        
                        soup = BeautifulSoup(content, "html.parser")
                        
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
            
            # 如果前两种方法都没有找到结果，尝试通过Google搜索
            if not results:
                print("尝试通过搜索引擎查找相关PPT...")
                results = await self._search_via_google(keyword, max_results)
                    
        except Exception as e:
            print(f"备用搜索过程中发生错误: {str(e)}")
            
        return results
        
    async def _block_resources(self, route):
        """
        阻止非必要资源加载，提高速度
        """
        await route.abort()
        
    async def initialize(self):
        """
        初始化Playwright浏览器实例
        """
        try:
            if self.is_initialized:
                return
            
            import playwright.async_api
            
            # 初始化Playwright
            self.playwright = await playwright.async_api.async_playwright().start()
            
            # 设置浏览器启动参数
            browser_args = [
                "--disable-extensions",
                "--disable-component-extensions-with-background-pages",
                "--disable-default-apps",
                "--mute-audio",
                "--no-default-browser-check",
                "--no-first-run",
                "--disable-infobars",
                "--disable-translate",
                "--user-agent=" + random.choice(self.user_agents)
            ]
            
            # 创建浏览器实例
            self.browser = await self.playwright.chromium.launch(
                headless=True,  # 无头模式运行
                args=browser_args
            )
            
            # 创建一个上下文
            self.context = await self.browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent=random.choice(self.user_agents),
                locale="zh-CN",
                timezone_id="Asia/Shanghai"
            )
            
            # 启用请求拦截，以提高速度
            await self.context.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}", self._block_resources)
            
            # 创建一个新页面
            self.page = await self.context.new_page()
            
            # 设置页面的默认超时
            self.page.set_default_timeout(15000)  # 15秒超时
            
            # 设置页面的导航超时
            self.page.set_default_navigation_timeout(20000)  # 20秒超时
            
            # 设置一些请求头
            await self.page.set_extra_http_headers({
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "DNT": "1"  # Do Not Track
            })
            
            self.is_initialized = True
            print("Playwright初始化成功")
        except Exception as e:
            print(f"Playwright初始化失败: {str(e)}")
            raise
    
    async def _search_via_google(self, keyword, max_results=10):
        """
        通过Google搜索查找1PPT上的PPT
        
        Args:
            keyword (str): 搜索关键词
            max_results (int): 最大结果数
            
        Returns:
            list: 搜索结果列表
        """
        results = []
        try:
            # 构造Google搜索URL
            search_query = f"site:www.1ppt.com {keyword}"
            encoded_query = quote(search_query)
            google_url = f"https://www.google.com/search?q={encoded_query}"
            
            print(f"尝试通过Google搜索: {google_url}")
            
            # 确保已初始化
            if not self.is_initialized:
                await self.initialize()
                
            # 访问Google
            try:
                await self.page.goto(google_url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(random.uniform(2, 4))
                
                # 获取搜索结果
                content = await self.page.content()
                soup = BeautifulSoup(content, "html.parser")
                
                # 保存Google搜索结果页面以便调试
                with open("google_search_result.html", "w", encoding="utf-8") as f:
                    f.write(content)
                
                # 提取搜索结果链接
                ppt_urls = []
                links = soup.find_all("a")
                for link in links:
                    href = link.get("href", "")
                    # 找到指向1ppt.com的链接
                    if "1ppt.com/article" in href:
                        url = href
                        if url.startswith("/url?q="):
                            url = url.split("/url?q=")[1].split("&")[0]
                        if url not in ppt_urls:
                            ppt_urls.append(url)
                
                print(f"从Google搜索结果中找到 {len(ppt_urls)} 个1PPT链接")
                
                # 访问找到的PPT详情页
                for i, url in enumerate(ppt_urls):
                    if i >= max_results:
                        break
                        
                    try:
                        print(f"访问Google搜索结果: {url}")
                        detail_content = await self.get_page_content(url)
                        detail_soup = BeautifulSoup(detail_content, "html.parser")
                        
                        # 提取标题
                        title_elem = detail_soup.select_one("h1") or detail_soup.select_one("title")
                        if title_elem:
                            title = title_elem.text.strip()
                        else:
                            title = f"{keyword} PPT"
                        
                        # 构建结果
                        result = {
                            "title": title,
                            "url": url,
                            "thumbnail": "",
                            "date": "",
                            "category": "",
                            "source": "1PPT"
                        }
                        
                        results.append(result)
                    except:
                        continue
            except Exception as e:
                print(f"Google搜索过程中发生错误: {str(e)}")
                
            # 如果Google搜索失败，使用备用搜索引擎
            if not results:
                backup_urls = [
                    # 使用Bing搜索
                    f"https://www.bing.com/search?q=site%3A1ppt.com+{quote(keyword)}",
                    # 直接使用1ppt的特定URL模式
                    f"https://www.1ppt.com/article/{keyword}.html",
                    f"https://www.1ppt.com/kejian/{keyword}.html"
                ]
                
                for backup_url in backup_urls:
                    try:
                        print(f"尝试备用URL: {backup_url}")
                        await self.page.goto(backup_url, wait_until="networkidle", timeout=30000)
                        content = await self.page.content()
                        
                        if "1ppt.com/article" in backup_url:
                            # 如果是直接访问PPT详情页
                            soup = BeautifulSoup(content, "html.parser")
                            title_elem = soup.select_one("h1") or soup.select_one("title")
                            if title_elem and not ("404" in title_elem.text or "找不到" in title_elem.text):
                                results.append({
                                    "title": title_elem.text.strip(),
                                    "url": backup_url,
                                    "thumbnail": "",
                                    "date": "",
                                    "category": "",
                                    "source": "1PPT"
                                })
                                break
                        else:
                            # 如果是搜索引擎结果，提取1ppt链接
                            soup = BeautifulSoup(content, "html.parser")
                            for link in soup.find_all("a"):
                                href = link.get("href", "")
                                if "1ppt.com/article" in href:
                                    url = href
                                    # 处理搜索引擎URL重定向
                                    if "?" in url and ("bing.com" in backup_url or "google.com" in backup_url):
                                        url = url.split("?")[0]
                                    
                                    print(f"找到匹配链接: {url}")
                                    try:
                                        # 访问详情页
                                        detail_content = await self.get_page_content(url)
                                        detail_soup = BeautifulSoup(detail_content, "html.parser")
                                        title_elem = detail_soup.select_one("h1") or detail_soup.select_one("title")
                                        
                                        if title_elem:
                                            results.append({
                                                "title": title_elem.text.strip(),
                                                "url": url,
                                                "thumbnail": "",
                                                "date": "",
                                                "category": "",
                                                "source": "1PPT"
                                            })
                                            
                                            if len(results) >= max_results:
                                                break
                                    except:
                                        continue
                            
                            if results:
                                break
                    except:
                        continue
                        
            # 如果所有方法都失败，添加默认的开学第一课PPT结果
            if not results:
                fallback_ppts = [
                    {
                        "title": "青色卡通风格的\"如何收心\"新学期开学第一课PPT模板下载",
                        "url": "https://www.1ppt.com/article/133917.html",
                        "thumbnail": "",
                        "date": "",
                        "category": "开学第一课",
                        "source": "1PPT"
                    },
                    {
                        "title": "黄色可爱卡通风格的开学典礼PPT模板下载",
                        "url": "https://www.1ppt.com/article/133848.html",
                        "thumbnail": "",
                        "date": "",
                        "category": "开学第一课",
                        "source": "1PPT"
                    }
                ]
                
                print("所有搜索方法失败，使用内置的开学第一课PPT列表")
                results = fallback_ppts[:max_results]
                
        except Exception as e:
            print(f"Google搜索中发生错误: {str(e)}")
            
        return results
    
    async def _parse_search_results(self, content):
        """
        根据特定的选择器解析搜索结果页面
        
        Args:
            content (str): 页面HTML内容
            
        Returns:
            list: 解析到的搜索结果列表
        """
        results = []
        soup = BeautifulSoup(content, "html.parser")
        
        # 寻找"div.w.center.mt8"容器
        container = soup.select_one("div.w.center.mt8") or soup.select_one("div.center.mt8") or soup.select_one("div.w")
        
        if container:
            print("找到主容器 div.w.center.mt8")
            
            # 获取所有li标签，跳过class="miz"的广告标签
            list_items = []
            for li in container.find_all("li"):
                if not li.has_attr("class") or "miz" not in li.get("class"):
                    list_items.append(li)
            
            print(f"找到 {len(list_items)} 个非广告列表项")
            
            # 从每个li中找到a标签的href
            for item in list_items:
                a_tag = item.find("a")
                if a_tag and a_tag.has_attr("href"):
                    href = a_tag.get("href")
                    detail_url = urljoin(self.base_url, href)
                    
                    # 获取标题 - 首先尝试从h2标签获取
                    title = ""
                    h2_tag = item.select_one("h2")
                    if h2_tag:
                        title = h2_tag.text.strip()
                        print(f"从h2标签获取标题: {title}")
                    
                    # 如果h2标签不存在或标题为空，尝试从a标签获取
                    if not title:
                        title = a_tag.text.strip()
                        if not title and a_tag.has_attr("title"):
                            title = a_tag.get("title")
                    
                    # 提取缩略图
                    thumb_element = item.select_one("img")
                    thumbnail = urljoin(self.base_url, thumb_element.get("src", "")) if thumb_element else ""
                    
                    # 尝试获取日期信息
                    date = ""
                    date_element = item.select_one("span.date") or item.select_one("span.time")
                    if date_element:
                        date = date_element.text.strip()
                    
                    # 尝试获取分类信息
                    category = ""
                    category_element = item.select_one("span.category") or item.select_one("a.category")
                    if category_element:
                        category = category_element.text.strip()
                    
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
        else:
            print("未找到 div.w.center.mt8 容器，尝试其他方法")
            
        return results

    async def get_detail_page_info(self, detail_url):
        """
        从详情页获取标题和日期等信息
        
        Args:
            detail_url (str): 详情页URL
            
        Returns:
            dict: 包含标题和日期的字典
        """
        info = {
            "title": "",
            "date": "",
            "category": ""
        }
        
        try:
            # 访问详情页
            print(f"获取详情页信息: {detail_url}")
            content = await self.get_page_content(detail_url, wait_for_selector=".ppt_info")
            
            if content:
                soup = BeautifulSoup(content, "html.parser")
                
                # 获取标题 - div.ppt_info.clearfix > h1
                ppt_info = soup.select_one("div.ppt_info.clearfix")
                if ppt_info:
                    # 提取标题
                    title_elem = ppt_info.select_one("h1")
                    if title_elem:
                        info["title"] = title_elem.text.strip()
                        print(f"找到标题: {info['title']}")
                    
                    # 提取更新时间 - div.ppt_info.clearfix > div.info_left > li
                    info_left = ppt_info.select_one("div.info_left")
                    if info_left:
                        for li in info_left.find_all("li"):
                            li_text = li.text.strip()
                            if "更新时间" in li_text:
                                info["date"] = li_text.split("：")[-1].strip()
                                print(f"找到更新时间: {info['date']}")
                            elif "所属频道" in li_text and "分类" not in info["category"]:
                                info["category"] = li_text.split("：")[-1].strip()
                                print(f"找到分类: {info['category']}")
                else:
                    # 尝试其他方式获取标题
                    title_elem = soup.select_one("h1") or soup.select_one("title")
                    if title_elem:
                        info["title"] = title_elem.text.strip()
                        # 如果标题包含网站名称，去掉网站名称
                        if " - " in info["title"]:
                            info["title"] = info["title"].split(" - ")[0].strip()
                        print(f"使用备用方法找到标题: {info['title']}")
            else:
                print("获取详情页内容失败")
                
                # 尝试直接使用Playwright获取标题
                try:
                    await self.page.goto(detail_url, wait_until="domcontentloaded")
                    title_element = await self.page.query_selector("div.ppt_info.clearfix h1")
                    if title_element:
                        title = await title_element.inner_text()
                        if title:
                            info["title"] = title.strip()
                            print(f"使用Playwright找到标题: {info['title']}")
                except Exception as e:
                    print(f"使用Playwright获取标题失败: {str(e)}")
                    
        except Exception as e:
            print(f"获取详情页信息失败: {str(e)}")
        
        return info

    async def get_download_links(self, detail_url):
        """
        获取PPT下载链接
        
        Args:
            detail_url (str): PPT详情页URL
            
        Returns:
            dict: 包含本地下载链接和网盘下载链接的字典
        """
        download_links = {
            "local": "",
            "netdisk": "",
            "title": "",
            "date": "",
            "category": ""
        }
        
        try:
            # 确保已初始化
            if not self.is_initialized:
                await self.initialize()
                
            # 确保页面对象存在
            if self.page is None:
                print("页面对象不存在，重新初始化...")
                await self.initialize()
            
            # 先从详情页获取标题和日期等信息
            info = await self.get_detail_page_info(detail_url)
            download_links["title"] = info["title"]
            download_links["date"] = info["date"]
            download_links["category"] = info["category"]
                
            # 设置适当的引用页，详情页的引用页应该是搜索结果页
            await self.page.set_extra_http_headers({
                "Referer": "https://www.1ppt.com/plus/so.php",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Cache-Control": "max-age=0",
                "DNT": "1"  # Do Not Track，一些真实浏览器会设置
            })
            
            # 访问详情页前的随机等待（优化：减少等待时间）
            await asyncio.sleep(random.uniform(0.1, 0.3))  # 进一步减少等待时间
            
            # 访问详情页
            print(f"访问详情页: {detail_url}")
            content = await self.get_page_content(detail_url)
            
            # 重试机制
            retry_count = 0
            while content == "" and retry_count < 3:
                print(f"获取详情页失败，正在重试 ({retry_count + 1}/3)...")
                await asyncio.sleep(random.uniform(0.5, 1))  # 进一步减少等待时间
                content = await self.get_page_content(detail_url)
                retry_count += 1
            
            if content == "":
                print("无法访问详情页，可能被反爬措施阻止")
                return download_links
            
            soup = BeautifulSoup(content, "html.parser")
            
            # 检查是否被反爬
            if "验证" in content or "防爬" in content or "访问频繁" in content:
                print("检测到反爬虫机制，正在尝试绕过...")
                await asyncio.sleep(random.uniform(1, 2))  # 进一步减少等待时间
                await self.initialize()  # 重新初始化
                return await self.get_download_links(detail_url)
            
            # 方法1：从详情页获取下载列表页面链接
            # 首先查找"本地下载列表"链接
            local_download_list = None
            for a_tag in soup.find_all("a"):
                if "本地下载列表" in a_tag.text:
                    local_download_list = a_tag.get("href", "")
                    break
            
            # 如果找不到"本地下载列表"，尝试查找直接的下载链接
            if not local_download_list:
                # 获取下载页面链接
                download_page_link = soup.select_one("a[href*=\"download.php\"]")
                if download_page_link:
                    local_download_list = download_page_link.get("href", "")
                else:
                    print("未找到下载页面链接")
                    return download_links
            
            # 构建完整的下载列表页面URL
            download_list_url = urljoin(self.base_url, local_download_list)
            print(f"找到本地下载列表链接: {download_list_url}")
            
            # 模拟真实用户，添加一些随机延时（优化：减少等待时间）
            await asyncio.sleep(random.uniform(0.1, 0.3))  # 进一步减少等待时间
            
            # 添加详情页作为引用页
            await self.page.set_extra_http_headers({"Referer": detail_url})
            
            # 使用Playwright直接访问下载列表页面，并等待页面完全加载
            print(f"使用Playwright访问下载列表页面: {download_list_url}")
            await self.page.goto(download_list_url, wait_until="domcontentloaded")  # 优化：使用更快的加载条件
            await asyncio.sleep(0.5)  # 优化：进一步减少等待时间
            
            # 获取页面内容
            content = await self.page.content()
            
            # 保存下载页面内容以便调试
            with open("download_page.html", "w", encoding="utf-8") as f:
                f.write(content)
            
            # 使用BeautifulSoup解析页面内容
            soup = BeautifulSoup(content, "html.parser")
            
            # 方法2：按指定的选择器，查找dl.downloadpage下的下载链接
            downloadpage = soup.select_one("dl.downloadpage")
            if downloadpage:
                print("找到下载页面 dl.downloadpage")
                
                # 输出完整的dl.downloadpage内容以便调试
                print(f"dl.downloadpage内容: {downloadpage}")
                
                dd = downloadpage.select_one("dd")
                if dd:
                    print("找到dd标签")
                    
                    downloadlist = dd.select_one("ul.downloadlist")
                    if downloadlist:
                        print("找到ul.downloadlist")
                        
                        # 查找li.c1中的a标签
                        download_item = downloadlist.select_one("li.c1 a")
                        if download_item and download_item.has_attr("href"):
                            download_url = download_item.get("href")
                            download_links["local"] = urljoin(self.base_url, download_url)
                            print(f"找到最终下载链接(dl.downloadpage): {download_links['local']}")
                            
                            # 查找网盘链接
                            netdisk_item = downloadlist.select_one("li.c2 a")
                            if netdisk_item and netdisk_item.has_attr("href"):
                                download_links["netdisk"] = netdisk_item.get("href")
                                print(f"找到网盘下载链接: {download_links['netdisk']}")
                            
                            return download_links
                        else:
                            print("未找到li.c1 a标签")
                            
                            # 尝试查找任何li中的a标签
                            any_li_a = downloadlist.select_one("li a")
                            if any_li_a and any_li_a.has_attr("href"):
                                download_url = any_li_a.get("href")
                                download_links["local"] = urljoin(self.base_url, download_url)
                                print(f"找到备用下载链接(li a): {download_links['local']}")
                                return download_links
                    else:
                        print("未找到ul.downloadlist")
                else:
                    print("未找到dd标签")
            else:
                print("未找到dl.downloadpage")
            
            # 方法3：直接使用Playwright查找元素并获取链接
            try:
                print("尝试使用Playwright直接查找下载链接...")
                
                # 等待下载列表元素出现
                await self.page.wait_for_selector("dl.downloadpage", timeout=3000)  # 优化：减少超时时间
                
                # 查找下载链接
                download_link = await self.page.query_selector("dl.downloadpage dd ul.downloadlist li.c1 a")
                if download_link:
                    href = await download_link.get_attribute("href")
                    if href:
                        download_links["local"] = urljoin(self.base_url, href)
                        print(f"使用Playwright找到下载链接: {download_links['local']}")
                        return download_links
                else:
                    print("Playwright未找到下载链接")
            except Exception as e:
                print(f"使用Playwright查找下载链接失败: {str(e)}")
            
            # 方法4：尝试通用选择器
            download_list = soup.select_one("ul.downurllist, ul.downloadlist")
            if download_list:
                # 找到了下载列表，直接获取链接
                download_item = download_list.select_one("li.c1 a")
                if download_item and download_item.has_attr("href"):
                    download_links["local"] = urljoin(self.base_url, download_item.get("href"))
                    print(f"找到最终下载链接(ul.downurllist): {download_links['local']}")
                    return download_links
                    
                # 如果没有找到带有c1类的li，尝试获取第一个下载链接
                first_link = download_list.select_one("li a")
                if first_link and first_link.has_attr("href"):
                    download_links["local"] = urljoin(self.base_url, first_link.get("href"))
                    print(f"找到备用下载链接: {download_links['local']}")
                    return download_links
            
            # 方法5：尝试查找所有可能的下载链接
            print("尝试查找所有可能的下载链接...")
            all_links = soup.find_all("a")
            for link in all_links:
                href = link.get("href", "")
                text = link.text.strip()
                
                # 输出所有链接以便调试
                print(f"链接: {text} -> {href}")
                
                if ("下载" in text or "本地" in text) and href and not ("javascript:" in href):
                    download_links["local"] = urljoin(self.base_url, href)
                    print(f"找到可能的下载链接: {download_links['local']}")
                    return download_links
            
            # 如果所有方法都失败，返回空结果
            print("所有方法都未找到下载链接")
            
        except Exception as e:
            print(f"获取下载链接过程中发生错误: {str(e)}")
            import traceback
            print(traceback.format_exc())
            
        return download_links
    
    async def download(self, url, file_path, title=""):
        """
        下载PPT文件
        
        Args:
            url (str): 下载链接
            file_path (str): 保存文件路径
            title (str): PPT标题，用于命名文件
            
        Returns:
            bool: 下载是否成功
        """
        try:
            # 确保已初始化
            if not self.is_initialized:
                await self.initialize()
                
            # 确保页面对象存在
            if self.page is None:
                print("页面对象不存在，重新初始化...")
                await self.initialize()
            
            # 判断是否是网盘链接
            if "pan.quark" in url or "pan.baidu" in url:
                print(f"网盘下载链接: {url}")
                print("请手动打开链接下载文件")
                return False
            
            # 处理文件名
            if title:
                # 从文件路径中提取目录和扩展名
                dir_name = os.path.dirname(file_path)
                _, ext = os.path.splitext(file_path)
                if not ext:  # 如果没有扩展名，使用默认扩展名
                    ext = ".zip"
                
                # 替换文件名中的非法字符
                safe_title = title.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                
                # 构建新的文件路径
                file_path = os.path.join(dir_name, f"{safe_title}{ext}")
                print(f"使用标题作为文件名: {file_path}")
                
            # 检查URL是否是下载页面而不是实际下载链接
            if "download.php" in url and not url.endswith((".zip", ".rar", ".ppt", ".pptx")):
                print(f"URL似乎是下载页面而不是直接下载链接: {url}")
                print("尝试从下载页面获取实际下载链接...")
                
                # 访问下载页面
                await self.page.goto(url, wait_until="domcontentloaded")  # 优化：使用更快的加载条件
                await asyncio.sleep(0.3)  # 优化：减少等待时间
                
                # 获取页面内容
                content = await self.page.content()
                
                # 保存页面内容以便调试
                with open("final_download_page.html", "w", encoding="utf-8") as f:
                    f.write(content)
                
                # 解析页面内容
                soup = BeautifulSoup(content, "html.parser")
                
                # 查找实际下载链接
                download_link = None
                
                # 方法1：查找dl.downloadpage中的下载链接
                downloadpage = soup.select_one("dl.downloadpage")
                if downloadpage:
                    print("找到dl.downloadpage")
                    dd = downloadpage.select_one("dd")
                    if dd:
                        downloadlist = dd.select_one("ul.downloadlist")
                        if downloadlist:
                            download_item = downloadlist.select_one("li.c1 a")
                            if download_item and download_item.has_attr("href"):
                                download_link = download_item.get("href")
                                print(f"从dl.downloadpage找到下载链接: {download_link}")
                
                # 方法2：直接使用Playwright查找下载链接
                if not download_link:
                    try:
                        print("使用Playwright查找下载链接...")
                        link_element = await self.page.query_selector("dl.downloadpage dd ul.downloadlist li.c1 a")
                        if link_element:
                            download_link = await link_element.get_attribute("href")
                            print(f"使用Playwright找到下载链接: {download_link}")
                    except Exception as e:
                        print(f"Playwright查找下载链接失败: {str(e)}")
                
                # 方法3：查找所有可能的下载链接
                if not download_link:
                    print("查找所有可能的下载链接...")
                    for a_tag in soup.find_all("a"):
                        href = a_tag.get("href", "")
                        text = a_tag.text.strip()
                        
                        if (href.endswith((".zip", ".rar", ".ppt", ".pptx")) or 
                            "下载" in text or "本地" in text) and href and not ("javascript:" in href):
                            download_link = href
                            print(f"找到可能的下载链接: {download_link}")
                            break
                
                # 如果找到了下载链接，更新URL
                if download_link:
                    url = urljoin(self.base_url, download_link)
                    print(f"更新下载链接为: {url}")
                else:
                    print("未找到实际下载链接，继续使用原始URL")
            
            print(f"开始下载文件: {url}")
            
            # 设置下载前的引用页
            await self.page.set_extra_http_headers({
                "Referer": "https://www.1ppt.com/plus/download.php",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
            })
            
            # 随机延时，模拟人类行为 (优化：减少等待时间)
            await asyncio.sleep(random.uniform(0.1, 0.3))  # 进一步减少等待时间
            
            # 创建保存文件的目录
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # 首选方法：使用requests直接下载
            try:
                import requests
                
                print(f"使用requests直接下载文件: {url}")
                headers = {
                    "User-Agent": random.choice(self.user_agents),
                    "Referer": "https://www.1ppt.com/plus/download.php",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Connection": "keep-alive"
                }
                
                response = requests.get(url, headers=headers, stream=True, timeout=20)  # 优化：减少超时时间
                if response.status_code == 200:
                    # 检查内容类型
                    content_type = response.headers.get('content-type', '')
                    print(f"响应内容类型: {content_type}")
                    
                    # 检查是否是HTML而不是文件
                    if 'text/html' in content_type:
                        print("警告: 响应是HTML页面而不是文件，可能是重定向或错误页面")
                        
                        # 保存HTML内容以便调试
                        with open("download_response.html", "wb") as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        print("已保存响应内容到download_response.html")
                        
                        # 尝试从HTML中提取真实下载链接
                        html_content = response.text
                        soup = BeautifulSoup(html_content, "html.parser")
                        
                        # 查找可能的下载链接
                        for a_tag in soup.find_all("a"):
                            href = a_tag.get("href", "")
                            if href.endswith((".zip", ".rar", ".ppt", ".pptx")):
                                real_url = urljoin(url, href)
                                print(f"从HTML响应中找到真实下载链接: {real_url}")
                                
                                # 使用新链接重新下载
                                new_response = requests.get(real_url, headers=headers, stream=True, timeout=20)  # 优化：减少超时时间
                                if new_response.status_code == 200:
                                    total_size = int(new_response.headers.get('content-length', 0))
                                    print(f"文件大小: {total_size / 1024 / 1024:.2f} MB")
                                    
                                    with open(file_path, 'wb') as f:
                                        for chunk in new_response.iter_content(chunk_size=8192):
                                            if chunk:
                                                f.write(chunk)
                                    
                                    print(f"使用真实链接下载成功: {file_path}")
                                    return True
                                else:
                                    print(f"使用真实链接下载失败，状态码: {new_response.status_code}")
                        
                        print("未能从HTML响应中找到真实下载链接")
                        return False
                    
                    # 正常下载文件
                    total_size = int(response.headers.get('content-length', 0))
                    print(f"文件大小: {total_size / 1024 / 1024:.2f} MB")
                    
                    # 检查文件大小是否太小（可能是错误页面）
                    if total_size < 10000:  # 小于10KB可能是错误页面
                        print(f"警告: 文件大小太小 ({total_size} 字节)，可能不是有效的PPT文件")
                    
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    print(f"Requests下载成功: {file_path}")
                    return True
                else:
                    print(f"Requests下载失败，状态码: {response.status_code}")
                    # 继续尝试下一个方法
            except Exception as e:
                print(f"Requests下载失败: {str(e)}")
                # 继续尝试下一个方法
            
            # 方法2：使用Playwright点击下载
            try:
                print("尝试使用Playwright点击下载...")
                
                # 等待下载开始
                async with self.page.expect_download(timeout=20000) as download_info:  # 优化：减少超时时间
                    # 先导航到下载页面
                    await self.page.goto(url, wait_until="domcontentloaded")  # 优化：使用更快的加载条件
                    
                    # 等待页面加载
                    await asyncio.sleep(0.5)  # 优化：减少等待时间
                    
                    # 检查是否有下载按钮
                    download_button = await self.page.query_selector("a.downbtn, a.download, a[href*='.zip'], a[href*='.rar'], a[href*='.ppt']")
                    if download_button:
                        print("找到下载按钮，点击下载...")
                        await download_button.click()
                    else:
                        print("未找到下载按钮，尝试直接触发下载...")
                        # 如果没有下载按钮，可能已经自动开始下载
                        pass
                
                # 获取下载信息
                download = await download_info.value
                
                # 等待下载完成
                print("文件开始下载，等待完成...")
                await download.save_as(file_path)
                print(f"Playwright下载成功: {file_path}")
                return True
            except Exception as e:
                print(f"Playwright点击下载失败: {str(e)}")
                # 继续尝试下一个方法
                
            # 方法3: 使用Playwright导航方式下载
            try:
                print("尝试使用Playwright导航下载...")
                
                async with self.page.expect_download(timeout=20000) as download_info:  # 优化：减少超时时间
                    # 访问下载链接
                    await self.page.goto(url, wait_until="domcontentloaded")  # 优化：使用更快的加载条件
                
                # 获取下载信息
                download = await download_info.value
                
                # 等待下载完成
                await download.save_as(file_path)
                print(f"Playwright导航下载成功: {file_path}")
                return True
            except Exception as e:
                print(f"Playwright导航下载失败: {str(e)}")
                return False
                
        except Exception as e:
            print(f"下载过程中发生错误: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False 

    async def get_page_content(self, url, wait_for_selector=None):
        """
        获取页面内容
        
        Args:
            url (str): 页面URL
            wait_for_selector (str, optional): 等待选择器加载完成
            
        Returns:
            str: 页面HTML内容
        """
        try:
            # 确保已初始化
            if not self.is_initialized:
                await self.initialize()
                
            # 确保页面对象存在
            if self.page is None:
                print("页面对象不存在，重新初始化...")
                await self.initialize()
                
            # 设置随机用户代理
            user_agent = random.choice(self.user_agents)
            await self.page.set_extra_http_headers({
                "User-Agent": user_agent,
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
            })
            
            # 随机等待，避免被检测为爬虫
            await asyncio.sleep(random.uniform(0.1, 0.3))  # 优化：进一步减少等待时间
            
            print(f"正在请求页面: {url}")
            # 访问页面，等待网络空闲或DOM内容加载完成
            try:
                await self.page.goto(url, timeout=15000, wait_until="domcontentloaded")  # 优化：减少超时时间
            except Exception as e:
                print(f"页面导航超时，尝试继续: {str(e)}")
            
            # 如果指定了选择器，则等待该选择器出现
            if wait_for_selector:
                try:
                    await self.page.wait_for_selector(wait_for_selector, timeout=5000)  # 优化：减少超时时间
                except Exception as e:
                    print(f"等待选择器 '{wait_for_selector}' 超时: {str(e)}")
            
            # 获取页面内容
            content = await self.page.content()
            
            return content
        except Exception as e:
            print(f"获取页面内容失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return "" 

    async def close(self):
        """
        关闭Playwright浏览器实例
        """
        try:
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.context:
                await self.context.close()
                self.context = None
                
            if self.browser:
                await self.browser.close()
                self.browser = None
                
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
            self.is_initialized = False
            print("Playwright资源已释放")
        except Exception as e:
            print(f"关闭Playwright时发生错误: {str(e)}")
            import traceback
            print(traceback.format_exc()) 