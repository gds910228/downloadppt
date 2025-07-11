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
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
from .playwright_scraper import PlaywrightScraper

class YppptPlaywrightScraper(PlaywrightScraper):
    """优品PPT网站Playwright爬虫类"""
    
    def __init__(self):
        """初始化爬虫"""
        super().__init__()
        self.base_url = "https://www.ypppt.com"
        self.search_url = "https://www.ypppt.com/search/{}.html"
        self.alt_search_url = "https://www.ypppt.com/index.php?s={}"
    
    async def search(self, keyword, max_results=10):
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
            # 确保已初始化
            if not self.is_initialized:
                await self.initialize()
                
            # 模拟搜索前的随机等待
            await asyncio.sleep(random.uniform(2, 4))
            
            # 构造搜索URL
            encoded_keyword = quote(keyword)
            search_url = self.search_url.format(encoded_keyword)
            
            # 添加搜索引擎来源的引用页
            search_engines = [
                "https://www.baidu.com/s?wd=PPT%20{}",
                "https://www.sogou.com/web?query=PPT%20{}",
                "https://cn.bing.com/search?q=PPT%20{}"
            ]
            referer = random.choice(search_engines).format(encoded_keyword)
            
            # 确保页面对象存在
            if self.page is None:
                print("页面对象不存在，重新初始化...")
                await self.initialize()
                
            await self.page.set_extra_http_headers({
                "Referer": referer,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Cache-Control": "max-age=0",
                "Sec-Ch-Ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
            })
            
            print(f"正在搜索: {search_url}")
            
            # 模拟更真实的搜索行为
            # 1. 先访问网站首页
            try:
                await self.get_page_content(self.base_url, wait_for_selector="body")
                await asyncio.sleep(random.uniform(1, 3))
                
                # 随机点击一个分类链接，模拟真实浏览
                if random.random() < 0.5:
                    try:
                        category_link = await self.page.query_selector(".topnav a")
                        if category_link:
                            await category_link.click()
                            await asyncio.sleep(random.uniform(2, 4))
                            await self.page.go_back()
                            await asyncio.sleep(random.uniform(1, 2))
                    except:
                        pass
            except:
                pass
            
            # 使用Playwright访问搜索页面
            content = await self.get_page_content(search_url, wait_for_selector=".posts li, .box li")
            
            # 防止搜索被阻止的重试机制
            retry_count = 0
            while (content == "" or "404" in content) and retry_count < 3:
                print(f"搜索结果为空或404，尝试重试 ({retry_count + 1}/3)...")
                # 随机等待更长时间
                await asyncio.sleep(random.uniform(5, 15))
                
                # 清除cookies或重新初始化
                if random.random() < 0.5:
                    await self.page.context.clear_cookies()
                    await self.initialize()  # 重新初始化
                
                # 更换User-Agent
                user_agent = random.choice(self.user_agents)
                await self.page.set_extra_http_headers({"User-Agent": user_agent})
                
                # 再次尝试
                content = await self.get_page_content(search_url, wait_for_selector=".posts li, .box li")
                retry_count += 1
            
            # 保存搜索结果页面以便调试
            with open("ypppt_search_result.html", "w", encoding="utf-8") as f:
                f.write(content)
                
            # 解析页面
            soup = BeautifulSoup(content, "html.parser")
            
            # 获取页面标题
            page_title = soup.title.text if soup.title else "无标题"
            print(f"页面标题: {page_title}")
            
            # 检查是否有反爬虫提示
            if "验证" in content or "防爬" in content or "访问频繁" in content or "访问受限" in content:
                print("检测到反爬虫机制，正在尝试绕过...")
                # 尝试休息一段时间后再次访问
                await asyncio.sleep(random.uniform(15, 30))
                await self.initialize()  # 重新初始化
                return await self.search(keyword, max_results)
            
            # 检查是否是404页面
            if "404" in page_title:
                print(f"搜索请求失败，状态码: 404")
                return await self._search_alternative(keyword, max_results)
            
            # 获取搜索结果列表
            search_results = (
                soup.select(".posts li") or 
                soup.select(".box li") or
                soup.select(".list li")
            )
            
            if not search_results:
                print("没有找到相关PPT，尝试备用搜索方法")
                return await self._search_alternative(keyword, max_results)
                
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
                
                # 模拟真实的搜索和浏览行为，在结果间添加随机延时
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
            # 如果搜索结果为空，尝试使用备用搜索方法
            if not results:
                return await self._search_alternative(keyword, max_results)
                
        except Exception as e:
            print(f"搜索过程中发生错误: {str(e)}")
            return await self._search_alternative(keyword, max_results)
            
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
                await self.initialize()
            
            # 先从详情页获取标题和日期等信息
            info = await self.get_detail_page_info(detail_url)
            download_links["title"] = info["title"]
            download_links["date"] = info["date"]
            download_links["category"] = info["category"]
            
            # 访问详情页
            content = await self.get_page_content(detail_url)
            
            if not content:
                print("获取详情页内容失败")
                return download_links
            
            # 解析页面内容
            soup = BeautifulSoup(content, "html.parser")
            
            # 获取下载按钮链接
            download_btn = soup.select_one("a.downbtn")
            if download_btn and download_btn.has_attr("href"):
                download_url = download_btn.get("href")
                download_links["local"] = urljoin(self.base_url, download_url)
                print(f"找到下载链接: {download_links['local']}")
                
                # 获取网盘链接
                netdisk_link = soup.select_one("a.downpan")
                if netdisk_link and netdisk_link.has_attr("href"):
                    download_links["netdisk"] = netdisk_link.get("href")
                    print(f"找到网盘链接: {download_links['netdisk']}")
                
                return download_links
            
            # 如果没有找到下载按钮，查找其他可能的下载链接
            download_links_found = []
            for a_tag in soup.find_all("a"):
                if a_tag.has_attr("href"):
                    href = a_tag.get("href")
                    text = a_tag.text.strip()
                    
                    if ("下载" in text or "本地" in text) and href and not href.startswith("#") and not href.startswith("javascript:"):
                        download_links_found.append((href, text))
                        print(f"找到可能的下载链接: {text} -> {href}")
            
            # 从找到的链接中选择最可能的下载链接
            for href, text in download_links_found:
                if "本地下载" in text or "免费下载" in text:
                    download_links["local"] = urljoin(self.base_url, href)
                    print(f"选择本地下载链接: {download_links['local']}")
                    break
            
            # 如果没有找到特定文本的链接，使用第一个找到的链接
            if not download_links["local"] and download_links_found:
                download_links["local"] = urljoin(self.base_url, download_links_found[0][0])
                print(f"选择第一个下载链接: {download_links['local']}")
            
            # 如果仍然没有找到下载链接，尝试使用Playwright直接查找
            if not download_links["local"]:
                try:
                    print("尝试使用Playwright直接查找下载链接...")
                    await self.page.goto(detail_url, wait_until="domcontentloaded")
                    download_button = await self.page.query_selector("a.downbtn, a.down_btn, a.download_btn")
                    if download_button:
                        href = await download_button.get_attribute("href")
                        if href:
                            download_links["local"] = urljoin(self.base_url, href)
                            print(f"使用Playwright找到下载链接: {download_links['local']}")
                except Exception as e:
                    print(f"使用Playwright查找下载链接失败: {str(e)}")
            
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
            if "pan.baidu" in url or "pan.quark" in url or "lanzou" in url:
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
            
            print(f"开始下载文件: {url}")
            
            # 设置下载前的引用页
            await self.page.set_extra_http_headers({
                "Referer": "https://www.ypppt.com/",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
            })
            
            # 随机延时，模拟人类行为
            await asyncio.sleep(random.uniform(0.3, 0.8))
            
            # 创建保存文件的目录
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # 首选方法：使用requests直接下载
            try:
                import requests
                
                print(f"使用requests直接下载文件: {url}")
                headers = {
                    "User-Agent": random.choice(self.user_agents),
                    "Referer": "https://www.ypppt.com/",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Connection": "keep-alive"
                }
                
                response = requests.get(url, headers=headers, stream=True, timeout=30)
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
                                new_response = requests.get(real_url, headers=headers, stream=True, timeout=30)
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
                async with self.page.expect_download(timeout=30000) as download_info:
                    # 先导航到下载页面
                    await self.page.goto(url)
                    
                    # 等待页面加载
                    await asyncio.sleep(1)  # 优化：减少等待时间
                    
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
                
                async with self.page.expect_download(timeout=30000) as download_info:
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
            print(f"下载文件过程中发生错误: {str(e)}")
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