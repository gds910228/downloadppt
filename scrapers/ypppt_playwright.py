#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
优品PPT网站Playwright爬虫
"""

import os
import time
import random
import asyncio
import re
import urllib.parse
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote, parse_qs, urlparse
from .playwright_scraper import PlaywrightScraper

class YppptPlaywrightScraper(PlaywrightScraper):
    """优品PPT网站Playwright爬虫类"""
    
    def __init__(self):
        """初始化爬虫"""
        super().__init__()
        self.base_url = "https://www.ypppt.com"
        self.search_url = "https://www.ypppt.com/p/search.php?kwtype=1&q={}"
        self.alt_search_url = "https://www.ypppt.com/index.php?s={}"
        
        # 创建临时目录用于保存HTML文件
        self.temp_dir = os.path.join(os.getcwd(), "temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # 添加.gitignore文件到临时目录
        gitignore_path = os.path.join(self.temp_dir, ".gitignore")
        if not os.path.exists(gitignore_path):
            with open(gitignore_path, "w", encoding="utf-8") as f:
                f.write("*\n!.gitignore\n")
    
    async def search(self, keyword, max_results=40, timeout=60):
        """
        搜索PPT
        
        Args:
            keyword (str): 搜索关键词
            max_results (int): 最大结果数量
            timeout (int): 搜索超时时间（秒）
            
        Returns:
            list: 搜索结果列表，每个结果包含标题、URL等信息
        """
        results = []
        search_start_time = time.time()
        encoded_keyword = urllib.parse.quote(keyword)
        
        try:
            # 构建搜索URL
            search_url = self.search_url.format(encoded_keyword)
            
            # 访问搜索页面
            print(f"正在搜索: {search_url}")
            
            # 访问首页，获取cookie
            await self.page.goto("https://www.ypppt.com", wait_until="domcontentloaded")
            
            # 访问搜索页面
            print("正在访问搜索页面...")
            await self.page.goto(search_url, wait_until="domcontentloaded")
            await asyncio.sleep(1)  # 确保页面加载完成
            
            # 保存搜索结果页面以便调试
            content = await self.page.content()
            with open(os.path.join(self.temp_dir, "search_result_ypppt.html"), "w", encoding="utf-8") as f:
                f.write(content)
            
            # 获取搜索结果
            page_num = 1
            has_next_page = True  # 添加标志，表示是否还有下一页
            total_result = 0  # 总记录数
            total_pages = 0   # 总页数
            page_size = 21    # 默认每页显示数量
            
            # 从第一页解析总记录数和总页数
            soup = BeautifulSoup(content, "html.parser")
            
            # 尝试从页面底部的分页区域获取总页数和总记录数
            pagination = soup.select_one(".page, .pages, .pagination")
            if pagination:
                page_text = pagination.text
                # 尝试匹配总页数和总记录数
                page_match = re.search(r'共(\d+)页', page_text)
                if page_match:
                    total_pages = int(page_match.group(1))
                    print(f"总页数: {total_pages}")
                
                # 如果在第一页找不到总记录数，我们需要获取第二页URL来提取
                if not total_result and len(pagination.select("a")) > 0:
                    for a_tag in pagination.select("a"):
                        a_text = a_tag.text.strip()
                        if "下一页" in a_text or ">" in a_text or a_text == "»" or a_text == "2":
                            next_page_url = a_tag["href"]
                            if not next_page_url.startswith("http"):
                                next_page_url = urljoin(self.base_url, next_page_url)
                            
                            # 从URL中提取TotalResult参数
                            parsed_url = urlparse(next_page_url)
                            query_params = parse_qs(parsed_url.query)
                            
                            if "TotalResult" in query_params:
                                total_result = int(query_params["TotalResult"][0])
                                print(f"总记录数: {total_result}")
                            
                            if "pagesize" in query_params:
                                page_size = int(query_params["pagesize"][0])
                                print(f"每页显示: {page_size}")
                            break
            
            while len(results) < max_results and has_next_page:
                # 检查是否超时
                if time.time() - search_start_time > timeout:
                    print(f"搜索超时，已经搜索了 {timeout} 秒")
                    break
                    
                print(f"正在获取第 {page_num} 页搜索结果...")
                
                # 等待搜索结果加载
                try:
                    await self.page.wait_for_selector("ul.posts, div.posts, div.box, div.list, ul.list", timeout=5000)
                except Exception as e:
                    print(f"等待选择器失败: {str(e)}")
                
                # 获取页面内容
                content = await self.page.content()
                
                # 保存当前页面内容以便调试
                search_result_path = os.path.join(self.temp_dir, f"search_result_ypppt_page{page_num}.html")
                with open(search_result_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                soup = BeautifulSoup(content, "html.parser")
                
                # 查找主容器 - 优先使用ul.posts.clear
                main_container = (
                    soup.select_one("ul.posts.clear") or
                    soup.select_one("ul.posts") or 
                    soup.select_one("div.posts") or 
                    soup.select_one("div.box") or 
                    soup.select_one("div.list") or 
                    soup.select_one("ul.list")
                )
                
                if main_container:
                    print(f"找到主容器: {main_container.name}.{' '.join(main_container.get('class', []))}")
                    
                    # 查找所有非广告的列表项 (排除 class="miz" 的li元素)
                    list_items = []
                    for li in main_container.select("li"):
                        # 只跳过明确标记为miz的广告li
                        if li.get("class") and "miz" in li.get("class"):
                            print(f"跳过广告li: {li.get('class')}")
                        else:
                            list_items.append(li)
                    
                    print(f"找到 {len(list_items)} 个非广告列表项")
                    
                    # 处理每个列表项
                    for item in list_items:
                        if len(results) >= max_results:
                            break
                        
                        # 获取链接
                        link_elem = item.select_one("a")
                        if not link_elem or not link_elem.has_attr("href"):
                            print("跳过没有链接的项目")
                            continue
                        
                        # 获取URL
                        url = link_elem["href"]
                        if not url.startswith("http"):
                            url = urljoin(self.base_url, url)
                        
                        # 跳过广告链接
                        if "51miz.com" in url or "ibaotu.com" in url:
                            print(f"跳过广告链接: {url}")
                            continue
                        
                        # 获取标题
                        title = ""
                        # 优先从h2或h3标签获取标题
                        title_elem = item.select_one("h2") or item.select_one("h3")
                        if title_elem:
                            title = title_elem.text.strip()
                        else:
                            # 从链接文本或title属性获取标题
                            title = link_elem.text.strip() or link_elem.get("title", "").strip()
                        
                        # 如果标题为空，尝试从图片alt属性获取
                        if not title:
                            img = link_elem.select_one("img")
                            if img and img.has_attr("alt"):
                                title = img.get("alt", "").strip()
                        
                        # 如果仍然没有标题，使用URL的最后部分
                        if not title:
                            title = url.split("/")[-1].split(".")[0]
                            
                        print(f"找到标题: {title[:30]}")
                        print(f"找到链接: {url}")
                        
                        # 获取日期和分类
                        date = ""
                        date_elem = item.select_one(".date") or item.select_one(".time")
                        if date_elem:
                            date = date_elem.text.strip()
                        
                        # 获取分类信息
                        category = ""
                        # 查找分类信息 - 通常是链接下方的另一个a标签
                        category_links = item.select("a")
                        if len(category_links) > 1:
                            for a in category_links:
                                if a != link_elem:
                                    category_text = a.text.strip()
                                    if category_text and "PPT" in category_text:
                                        category = category_text
                                        break
                        
                        # 如果没有找到分类，尝试其他选择器
                        if not category:
                            category_elem = item.select_one(".category") or item.select_one(".cat")
                            if category_elem:
                                category = category_elem.text.strip()
                        
                        # 添加到结果列表
                        results.append({
                            "title": title,
                            "url": url,
                            "date": date,
                            "category": category,
                            "source": "优品PPT"
                        })
                else:
                    print("未找到主容器")
                
                # 检查是否有下一页
                # 如果已经是最后一页，则停止翻页
                if total_pages > 0 and page_num >= total_pages:
                    print(f"已达到最后一页 ({page_num}/{total_pages})，停止翻页")
                    has_next_page = False
                    break
                
                # 如果已经达到最大结果数量，则停止翻页
                if len(results) >= max_results:
                    print(f"已达到最大结果数量 ({max_results})，停止翻页")
                    has_next_page = False
                    break
                
                # 构建下一页URL
                page_num += 1
                
                # 直接构建下一页URL，不依赖页面中的链接
                if total_result > 0:
                    # 使用标准格式构建翻页URL
                    next_page_url = f"https://www.ypppt.com/p/search.php?keyword={encoded_keyword}&searchtype=titlekeyword&channeltype=0&orderby=&kwtype=1&pagesize={page_size}&typeid=0&TotalResult={total_result}&PageNo={page_num}"
                    print(f"构建翻页URL: {next_page_url}")
                else:
                    # 查找页面中的所有数字链接和"下一页"链接
                    pagination = soup.select_one(".page, .pages, .pagination")
                    found_next_page = False
                    
                    if pagination:
                        # 输出分页区域的HTML以便调试
                        print(f"分页区域HTML: {pagination}")
                        
                        # 查找所有分页链接
                        page_links = pagination.select("a")
                        print(f"找到 {len(page_links)} 个分页链接")
                        
                        # 遍历所有链接，查找数字链接或"下一页"链接
                        for a_tag in page_links:
                            a_text = a_tag.text.strip()
                            print(f"分页链接文本: '{a_text}'")
                            
                            # 检查是否是"下一页"链接或数字链接
                            if (a_text == "下一页" or 
                                a_text == ">" or 
                                a_text == "»" or 
                                a_text == str(page_num) or
                                (a_text.isdigit() and int(a_text) == page_num)):
                                next_page_url = a_tag["href"]
                                if not next_page_url.startswith("http"):
                                    next_page_url = urljoin(self.base_url, next_page_url)
                                found_next_page = True
                                print(f"找到下一页链接: {next_page_url}")
                                break
                    
                    # 如果没有找到下一页链接，尝试构建一个
                    if not found_next_page:
                        # 如果当前是第一页，尝试构建第二页链接
                        if page_num == 2:
                            next_page_url = f"{search_url.replace('kwtype=1&q=', 'keyword=')}&searchtype=titlekeyword&channeltype=0&orderby=&kwtype=1&pagesize=21&typeid=0&PageNo=2"
                            print(f"构建默认第二页URL: {next_page_url}")
                        else:
                            print("没有找到下一页链接，停止翻页")
                            has_next_page = False
                            break
                
                print(f"下一页URL: {next_page_url}")
                
                # 访问下一页
                await self.page.goto(next_page_url, wait_until="domcontentloaded")
                await asyncio.sleep(1)  # 等待页面加载
                
                # 检查当前页是否有内容，如果没有内容则停止翻页
                content = await self.page.content()
                soup = BeautifulSoup(content, "html.parser")
                main_container = (
                    soup.select_one("ul.posts.clear") or
                    soup.select_one("ul.posts") or 
                    soup.select_one("div.posts") or 
                    soup.select_one("div.box") or 
                    soup.select_one("div.list") or 
                    soup.select_one("ul.list")
                )
                
                if not main_container or not (main_container.select("li") or main_container.select("div.post")):
                    print("当前页没有内容，停止翻页")
                    has_next_page = False
                    break
                
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
                
            # 尝试使用备用搜索URL
            encoded_keyword = quote(keyword)
            alt_search_url = self.alt_search_url.format(encoded_keyword)
            
            print(f"尝试备用搜索 (index.php): {alt_search_url}")
            
            content = await self.get_page_content(alt_search_url, wait_for_selector=".posts li, .box li")
            
            # 解析页面
            soup = BeautifulSoup(content, "html.parser")
            
            # 获取搜索结果列表
            search_results = (
                soup.select(".posts li") or 
                soup.select(".box li") or
                soup.select(".list li")
            )
            
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
                thumb_element = item.select_one("img")
                thumbnail = urljoin(self.base_url, thumb_element.get("src", "")) if thumb_element else ""
                
                # 提取日期信息
                date_element = item.select_one(".info span") or item.select_one(".date")
                date = date_element.text.strip() if date_element else ""
                
                # 构建结果
                result = {
                    "title": title,
                    "url": detail_url,
                    "thumbnail": thumbnail,
                    "date": date,
                    "category": "",
                    "source": "优品PPT"
                }
                
                results.append(result)
            
            # 如果还是没有结果，尝试在各个分类页面中搜索
            if not results:
                # 常见分类页面
                categories = [
                    "/moban/",
                    "/kejian/",
                    "/jieri/",
                    "/hangye/",
                    "/beijing/",
                    "/sucai/",
                    "/tubiao/"
                ]
                
                for category in categories:
                    category_url = urljoin(self.base_url, category)
                    print(f"尝试在分类中搜索: {category_url}")
                    
                    content = await self.get_page_content(category_url, wait_for_selector=".posts li, .box li")
                    
                    soup = BeautifulSoup(content, "html.parser")
                    
                    # 获取分类中的PPT列表
                    ppt_items = soup.select(".posts li") or soup.select(".box li") or soup.select(".list li")
                    
                    for i, item in enumerate(ppt_items):
                        if len(results) >= max_results:
                            break
                            
                        title_element = item.select_one("h2 a") or item.select_one("a")
                        if not title_element:
                            continue
                            
                        title = title_element.text.strip()
                        
                        # 检查标题是否包含关键词
                        if keyword.lower() not in title.lower():
                            continue
                            
                        detail_url = urljoin(self.base_url, title_element.get("href", ""))
                        
                        # 提取缩略图
                        thumb_element = item.select_one("img")
                        thumbnail = urljoin(self.base_url, thumb_element.get("src", "")) if thumb_element else ""
                        
                        # 提取日期信息
                        date_element = item.select_one(".info span") or item.select_one(".date")
                        date = date_element.text.strip() if date_element else ""
                        
                        # 构建结果
                        result = {
                            "title": title,
                            "url": detail_url,
                            "thumbnail": thumbnail,
                            "date": date,
                            "category": category.strip("/"),
                            "source": "优品PPT"
                        }
                        
                        results.append(result)
                    
                    if results:
                        break
            
            # 如果还是没有结果，尝试使用标签搜索
            if not results:
                tag_url = f"{self.base_url}/tag/{quote(keyword)}/"
                print(f"尝试标签搜索: {tag_url}")
                
                content = await self.get_page_content(tag_url, wait_for_selector=".posts li, .box li")
                
                soup = BeautifulSoup(content, "html.parser")
                
                # 获取标签页面中的PPT列表
                ppt_items = soup.select(".posts li") or soup.select(".box li") or soup.select(".list li")
                
                for i, item in enumerate(ppt_items):
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
                    
                    # 提取日期信息
                    date_element = item.select_one(".info span") or item.select_one(".date")
                    date = date_element.text.strip() if date_element else ""
                    
                    # 构建结果
                    result = {
                        "title": title,
                        "url": detail_url,
                        "thumbnail": thumbnail,
                        "date": date,
                        "category": "tag",
                        "source": "优品PPT"
                    }
                    
                    results.append(result)
                
        except Exception as e:
            print(f"备用搜索过程中发生错误: {str(e)}")
            
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
            content = await self.get_page_content(detail_url)
            
            if content:
                soup = BeautifulSoup(content, "html.parser")
                
                # 获取标题 - div.banner_article > div.infos > h1
                title_elem = soup.select_one("div.banner_article div.infos h1") or soup.select_one("h1.article-title")
                if title_elem:
                    info["title"] = title_elem.text.strip()
                    print(f"找到标题: {info['title']}")
                else:
                    # 尝试其他方式获取标题
                    title_elem = soup.select_one("h1") or soup.select_one("title")
                    if title_elem:
                        info["title"] = title_elem.text.strip()
                        # 如果标题包含网站名称，去掉网站名称
                        if " - " in info["title"]:
                            info["title"] = info["title"].split(" - ")[0].strip()
                        print(f"使用备用方法找到标题: {info['title']}")
                    
                # 提取更新时间 - div.xg > span
                date_elem = soup.select_one("div.xg span") or soup.select_one("div.article-meta span.item")
                if date_elem:
                    date_text = date_elem.text.strip()
                    if "更新时间" in date_text or "发布时间" in date_text:
                        info["date"] = date_text.split("：")[-1].strip()
                    else:
                        info["date"] = date_text
                    print(f"找到更新时间: {info['date']}")
                    
                # 提取分类
                category_elem = soup.select_one("div.xg a") or soup.select_one("div.article-meta a.category")
                if category_elem:
                    info["category"] = category_elem.text.strip()
                    print(f"找到分类: {info['category']}")
            else:
                print("获取详情页内容失败")
                
                # 尝试直接使用Playwright获取标题
                try:
                    await self.page.goto(detail_url, wait_until="domcontentloaded")
                    title_element = await self.page.query_selector("div.banner_article div.infos h1, h1.article-title")
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
                print("爬虫未初始化，正在初始化...")
                await self.initialize()
                
            # 确保页面对象存在
            if self.page is None:
                print("页面对象不存在，重新初始化...")
                await self.initialize()
                
            # 再次检查页面对象是否存在
            if self.page is None:
                print("无法创建页面对象，放弃获取下载链接")
                return download_links
            
            # 先从详情页获取标题和日期等信息
            info = await self.get_detail_page_info(detail_url)
            download_links["title"] = info["title"]
            download_links["date"] = info["date"]
            download_links["category"] = info["category"]
            
            # 访问详情页
            print(f"访问详情页: {detail_url}")
            content = await self.get_page_content(detail_url)
            
            # 保存详情页面以便调试
            with open(os.path.join(self.temp_dir, "detail_page.html"), "w", encoding="utf-8") as f:
                f.write(content)
            
            soup = BeautifulSoup(content, "html.parser")
            
            # 查找下载按钮 - div.button中的a标签
            download_button = soup.select_one("div.button a")
            if not download_button:
                # 尝试其他可能的选择器
                download_button = (
                    soup.select_one("a.downbtn") or 
                    soup.select_one("a.download") or
                    soup.select_one("a[href*='download']")
                )
            
            if not download_button:
                print("未找到下载按钮")
                return download_links
            
            # 获取下载页面链接
            download_page_url = download_button.get("href", "")
            if not download_page_url.startswith("http"):
                download_page_url = urljoin(self.base_url, download_page_url)
            
            print(f"找到下载页面链接: {download_page_url}")
            
            # 访问下载页面
            print(f"访问下载页面: {download_page_url}")
            download_page_content = await self.get_page_content(download_page_url)
            
            # 保存下载页面以便调试
            with open(os.path.join(self.temp_dir, "download_page.html"), "w", encoding="utf-8") as f:
                f.write(download_page_content)
            
            download_soup = BeautifulSoup(download_page_content, "html.parser")
            
            # 查找最终下载链接 - ul.down.clear中的li中的a标签
            download_list = download_soup.select_one("ul.down.clear")
            if not download_list:
                # 尝试其他可能的选择器
                download_list = (
                    download_soup.select_one("ul.down") or
                    download_soup.select_one("ul.downlist") or
                    download_soup.select_one("div.downlist")
                )
            
            if download_list:
                # 查找所有下载链接
                download_items = download_list.select("li a")
                if download_items:
                    # 获取第一个下载链接
                    download_url = download_items[0].get("href", "")
                    if download_url and not download_url.startswith("http"):
                        download_url = urljoin(self.base_url, download_url)
                    
                    download_links["local"] = download_url
                    print(f"找到最终下载链接: {download_url}")
                    
                    # 如果有网盘链接，通常在第二个li中
                    if len(download_items) > 1:
                        netdisk_url = download_items[1].get("href", "")
                        if netdisk_url and "pan" in netdisk_url:
                            download_links["netdisk"] = netdisk_url
                            print(f"找到网盘下载链接: {netdisk_url}")
            else:
                print("未找到下载列表")
                
                # 尝试直接查找下载链接
                for a_tag in download_soup.find_all("a"):
                    href = a_tag.get("href", "")
                    text = a_tag.text.strip()
                    
                    if (href.endswith((".zip", ".rar", ".ppt", ".pptx")) or 
                        "下载" in text or "本地" in text) and href and not ("javascript:" in href):
                        download_url = urljoin(self.base_url, href)
                        download_links["local"] = download_url
                        print(f"找到可能的下载链接: {download_url}")
                        break
                        
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
                print("爬虫未初始化，正在初始化...")
                await self.initialize()
                
            # 确保页面对象存在
            if self.page is None:
                print("页面对象不存在，重新初始化...")
                await self.initialize()
                
            # 再次检查页面对象是否存在
            if self.page is None:
                print("无法创建页面对象，放弃下载")
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
                
            print(f"开始下载文件: {url}")
            
            # 创建保存文件的目录
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # 首选方法：使用requests直接下载
            try:
                import requests
                
                print(f"使用requests直接下载文件: {url}")
                headers = {
                    "User-Agent": random.choice(self.user_agents),
                    "Referer": self.base_url,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Connection": "keep-alive"
                }
                
                response = requests.get(url, headers=headers, stream=True, timeout=20)
                if response.status_code == 200:
                    # 检查内容类型
                    content_type = response.headers.get('content-type', '')
                    print(f"响应内容类型: {content_type}")
                    
                    # 检查是否是HTML而不是文件
                    if 'text/html' in content_type:
                        print("警告: 响应是HTML页面而不是文件，可能是重定向或错误页面")
                        
                        # 保存HTML内容以便调试
                        with open(os.path.join(self.temp_dir, "download_response.html"), "wb") as f:
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
                                new_response = requests.get(real_url, headers=headers, stream=True, timeout=20)
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
                async with self.page.expect_download(timeout=20000) as download_info:
                    # 先导航到下载页面
                    await self.page.goto(url, wait_until="domcontentloaded")
                    
                    # 等待页面加载
                    await asyncio.sleep(0.5)
                    
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
                
                async with self.page.expect_download(timeout=20000) as download_info:
                    # 访问下载链接
                    await self.page.goto(url, wait_until="domcontentloaded")
                
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
            await asyncio.sleep(random.uniform(0.2, 0.5))  # 优化：减少等待时间
            
            print(f"正在请求页面: {url}")
            # 访问页面，等待网络空闲或DOM内容加载完成
            try:
                await self.page.goto(url, timeout=20000, wait_until="domcontentloaded")  # 优化：减少等待条件
            except Exception as e:
                print(f"页面导航超时，尝试继续: {str(e)}")
            
            # 如果指定了选择器，则等待该选择器出现
            if wait_for_selector:
                try:
                    await self.page.wait_for_selector(wait_for_selector, timeout=10000)  # 优化：减少超时时间
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