#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
使用Playwright的爬虫基类
"""

import os
import time
import random
import asyncio
from playwright.async_api import async_playwright
from urllib.parse import urljoin
import playwright_stealth  # 正确导入

class PlaywrightScraper:
    """使用Playwright的爬虫基类"""
    
    def __init__(self):
        """初始化爬虫"""
        self.browser = None
        self.context = None
        self.page = None
        self.is_initialized = False
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        # 增加更多的请求头参数
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
    
    async def initialize(self):
        """初始化Playwright"""
        if not self.is_initialized:
            self.playwright = await async_playwright().start()
            
            # 使用Firefox浏览器可能更不容易被识别为爬虫
            self.browser = await self.playwright.chromium.launch(
                headless=True,  # 可以设为False进行调试
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--disable-site-isolation-trials"
                ]
            )
            
            # 选择一个随机用户代理
            user_agent = random.choice(self.user_agents)
            
            # 创建一个新的浏览器上下文
            self.context = await self.browser.new_context(
                user_agent=user_agent,
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
                timezone_id="Asia/Shanghai",
                geolocation={"longitude": 116.4, "latitude": 39.9},  # 北京坐标
                permissions=["geolocation"],
                java_script_enabled=True,
                has_touch=random.choice([True, False]),
                color_scheme=random.choice(["light", "dark", "no-preference"])
            )
            
            # 设置默认超时时间
            self.context.set_default_timeout(30000)
            
            # 创建新页面
            self.page = await self.context.new_page()
            
            # 应用stealth插件隐藏自动化特征
            try:
                # 通过Stealth类来应用反检测功能
                await self.page.add_init_script("""
                    () => {
                      Object.defineProperty(navigator, 'webdriver', {
                        get: () => false,
                      });
                      
                      // Chrome
                      window.navigator.chrome = {
                        runtime: {},
                      };
                      
                      // 修改语言和平台
                      Object.defineProperty(navigator, 'languages', {
                        get: () => ['zh-CN', 'zh', 'en-US', 'en'],
                      });
                      
                      Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                      });
                    }
                """)
            except Exception as e:
                print(f"应用stealth时出错: {e}")
            
            # 设置额外的请求头
            await self.page.set_extra_http_headers(self.headers)
            
            # 设置一些基本的cookie，包括更完整的cookie参数
            current_time = int(time.time())
            cookies = [
                {
                    "name": "Hm_lvt_c9b8ae8609e7b3cd4a4114b5f5df9a22",
                    "value": str(current_time - random.randint(3600, 86400)),
                    "domain": ".1ppt.com",
                    "path": "/",
                    "expires": current_time + 86400 * 30,
                    "httpOnly": False,
                    "secure": False,
                    "sameSite": "Lax"
                },
                {
                    "name": "Hm_lpvt_c9b8ae8609e7b3cd4a4114b5f5df9a22",
                    "value": str(current_time),
                    "domain": ".1ppt.com",
                    "path": "/",
                    "expires": current_time + 86400,
                    "httpOnly": False,
                    "secure": False,
                    "sameSite": "Lax"
                },
                {
                    "name": "visit_count",
                    "value": str(random.randint(1, 10)),
                    "domain": ".1ppt.com",
                    "path": "/",
                    "expires": current_time + 86400 * 30,
                    "httpOnly": False,
                    "secure": False,
                    "sameSite": "Lax"
                },
                # 添加优品PPT的相关cookie
                {
                    "name": "Hm_lvt_f8c273274a7aa69c69e3576174b0c7c7",
                    "value": str(current_time - random.randint(3600, 86400)),
                    "domain": ".ypppt.com",
                    "path": "/",
                    "expires": current_time + 86400 * 30,
                    "httpOnly": False,
                    "secure": False,
                    "sameSite": "Lax"
                },
                {
                    "name": "Hm_lpvt_f8c273274a7aa69c69e3576174b0c7c7",
                    "value": str(current_time),
                    "domain": ".ypppt.com",
                    "path": "/",
                    "expires": current_time + 86400,
                    "httpOnly": False,
                    "secure": False,
                    "sameSite": "Lax"
                }
            ]
            await self.page.context.add_cookies(cookies)
            
            self.is_initialized = True
    
    async def close(self):
        """关闭Playwright"""
        if self.is_initialized:
            await self.page.close()
            await self.context.close()
            await self.browser.close()
            await self.playwright.stop()
            self.is_initialized = False
    
    async def get_page_content(self, url, wait_for_selector=None):
        """
        获取页面内容
        
        Args:
            url (str): 要访问的URL
            wait_for_selector (str, optional): 等待选择器出现
            
        Returns:
            str: 页面HTML内容
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # 随机延迟，模拟人类行为
            await asyncio.sleep(random.uniform(2, 5))
            
            # 设置Referer为合理的来源
            referer = "https://www.baidu.com/s?wd=" + url.split("//")[1].split("/")[0]
            await self.page.set_extra_http_headers({"Referer": referer})
            
            # 访问页面前执行一些随机操作
            await self._random_pre_visit_actions()
            
            # 访问页面
            response = await self.page.goto(url, wait_until="networkidle", timeout=60000)
            
            if response is None or response.status >= 400:
                print(f"搜索请求失败，状态码: {response.status if response else '未知'}")
                return ""
                
            # 模拟人类浏览行为
            await self._simulate_human_behavior()
            
            # 如果需要等待特定元素
            if wait_for_selector:
                try:
                    await self.page.wait_for_selector(wait_for_selector, timeout=15000)
                except:
                    pass
            
            # 获取页面内容
            content = await self.page.content()
            return content
        except Exception as e:
            print(f"获取页面内容时发生错误: {str(e)}")
            return ""
    
    async def _random_pre_visit_actions(self):
        """执行访问页面前的随机操作"""
        try:
            # 随机决定是否先访问一个中间页面
            if random.random() < 0.3:
                intermediate_sites = [
                    "https://www.baidu.com/",
                    "https://www.sogou.com/",
                    "https://cn.bing.com/"
                ]
                await self.page.goto(random.choice(intermediate_sites), wait_until="domcontentloaded")
                await asyncio.sleep(random.uniform(1, 3))
        except:
            pass
    
    async def _simulate_human_behavior(self):
        """模拟人类浏览行为"""
        try:
            # 随机等待一段时间，模拟阅读
            await asyncio.sleep(random.uniform(2, 6))
            
            # 随机滚动
            await self._random_scroll()
            
            # 随机鼠标移动
            for _ in range(random.randint(1, 5)):
                x = random.randint(100, 1000)
                y = random.randint(100, 600)
                await self.page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.5, 2))
                
            # 有时随机点击无害元素
            if random.random() < 0.2:
                try:
                    non_link_elements = await self.page.query_selector_all('div:not(a), span:not(a), p:not(a)')
                    if non_link_elements and len(non_link_elements) > 0:
                        random_element = non_link_elements[random.randint(0, len(non_link_elements)-1)]
                        await random_element.click(force=True)
                        await asyncio.sleep(random.uniform(0.5, 1.5))
                except:
                    pass
        except:
            pass
    
    async def _random_scroll(self):
        """随机滚动页面"""
        try:
            # 获取页面高度
            height = await self.page.evaluate("document.body.scrollHeight")
            
            # 随机滚动几次，模拟阅读行为
            scroll_count = random.randint(3, 7)
            for i in range(scroll_count):
                # 计算滚动位置，逐渐向下滚动
                scroll_to = int((i + 1) * height / scroll_count)
                await self.page.evaluate(f"window.scrollTo({{top: {scroll_to}, behavior: 'smooth'}})")
                await asyncio.sleep(random.uniform(1, 3))
            
            # 随机向上滚动一点
            if random.random() < 0.7:
                scroll_up = int(height * random.uniform(0.3, 0.7))
                await self.page.evaluate(f"window.scrollTo({{top: {scroll_up}, behavior: 'smooth'}})")
                await asyncio.sleep(random.uniform(1, 2))
            
            # 有时滚动回顶部
            if random.random() < 0.3:
                await self.page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
                await asyncio.sleep(random.uniform(0.5, 1))
        except:
            pass
    
    async def search(self, url, selector):
        """
        通用搜索方法
        
        Args:
            url (str): 搜索URL
            selector (str): 结果选择器
            
        Returns:
            str: 页面HTML内容
        """
        content = await self.get_page_content(url, wait_for_selector=selector)
        return content
    
    async def download_file(self, url, file_path):
        """
        下载文件
        
        Args:
            url (str): 下载链接
            file_path (str): 保存文件路径
            
        Returns:
            bool: 下载是否成功
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 模拟人类行为，随机等待
            await asyncio.sleep(random.uniform(1, 3))
            
            # 下载文件
            async with self.page.expect_download() as download_info:
                await self.page.goto(url)
            
            download = await download_info.value
            await download.save_as(file_path)
            return True
        except Exception as e:
            print(f"下载文件时发生错误: {str(e)}")
            return False 