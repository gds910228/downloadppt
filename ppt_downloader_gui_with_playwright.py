#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
使用Playwright的PPT下载器GUI
"""

import os
import sys
import asyncio
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from urllib.parse import urljoin
import datetime
import time

from scrapers.oneppt_playwright import OnePptPlaywrightScraper
from scrapers.ypppt_playwright import YppptPlaywrightScraper

class PPTDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PPT下载器 (Playwright版)")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # 初始化变量
        self.search_results = []
        self.is_searching = False
        self.is_downloading = False
        self.oneppt_scraper = None
        self.ypppt_scraper = None
        
        # 创建事件循环和线程
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._start_loop, daemon=True)
        self.thread.start()
        
        # 日志文件路径
        self.log_file_path = ""
        
        # 创建界面组件
        self.create_widgets()
        
        # 初始化日志
        self.init_log()
        
    def _start_loop(self):
        """在单独的线程中启动事件循环"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
        
    def create_widgets(self):
        """创建界面组件"""
        # 创建搜索框架
        search_frame = ttk.LabelFrame(self.root, text="搜索设置")
        search_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 第一行：搜索关键词
        ttk.Label(search_frame, text="搜索关键词:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.keyword_entry = ttk.Entry(search_frame, width=30)
        self.keyword_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # 第一行右侧：搜索网站选择
        ttk.Label(search_frame, text="搜索网站:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.source_var = tk.StringVar(value="1PPT")
        source_combobox = ttk.Combobox(search_frame, textvariable=self.source_var, values=["1PPT", "优品PPT"], state="readonly", width=15)
        source_combobox.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # 第二行：最大结果数
        ttk.Label(search_frame, text="最大结果数:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.max_results_var = tk.StringVar(value="10")
        max_results_spinbox = ttk.Spinbox(search_frame, from_=1, to=50, textvariable=self.max_results_var, width=5)
        max_results_spinbox.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # 第二行右侧：保存目录
        ttk.Label(search_frame, text="保存目录:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.output_dir_var = tk.StringVar(value="downloads")
        output_dir_entry = ttk.Entry(search_frame, textvariable=self.output_dir_var, width=30)
        output_dir_entry.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        ttk.Button(search_frame, text="选择...", command=self.browse_output_dir).grid(row=1, column=4, padx=5, pady=5)
        
        # 第三行：搜索按钮
        self.search_button = ttk.Button(search_frame, text="搜索", command=lambda: asyncio.run_coroutine_threadsafe(self.search(), self.loop))
        self.search_button.grid(row=2, column=0, columnspan=5, pady=10)
        
        # 创建搜索结果框架
        result_frame = ttk.LabelFrame(self.root, text="搜索结果")
        result_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 创建搜索结果表格
        columns = ("选择", "标题", "来源", "日期", "分类")
        self.result_table = ttk.Treeview(result_frame, columns=columns, show="headings", selectmode="extended")
        
        # 设置列宽
        self.result_table.column("选择", width=80, anchor="center")
        self.result_table.column("标题", width=300, anchor="w")
        self.result_table.column("来源", width=80, anchor="center")
        self.result_table.column("日期", width=120, anchor="center")
        self.result_table.column("分类", width=150, anchor="w")
        
        # 设置表头
        for col in columns:
            self.result_table.heading(col, text=col)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_table.yview)
        self.result_table.configure(yscroll=scrollbar.set)
        
        # 放置表格和滚动条
        self.result_table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 添加表格点击事件
        self.result_table.bind("<Button-1>", self.on_table_click)
        self.result_table.bind("<Double-1>", self.on_result_double_click)
        
        # 底部按钮框架
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # 全选复选框
        self.select_all_var = tk.BooleanVar(value=False)
        select_all_check = ttk.Checkbutton(button_frame, text="全选", variable=self.select_all_var, command=self.toggle_select_all)
        select_all_check.pack(side="left", padx=5)
        
        # 下载按钮
        self.download_button = ttk.Button(button_frame, text="下载选中项", command=lambda: asyncio.run_coroutine_threadsafe(self.download(), self.loop))
        self.download_button.pack(side="right", padx=5)
        
        # 日志框架
        log_frame = ttk.LabelFrame(self.root, text="日志")
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 创建日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_text.pack(fill="both", expand=True)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")
    
    def init_log(self):
        """初始化日志"""
        # 获取当前时间
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        
        # 创建日志文件名
        self.log_file_path = f"log_{timestamp}.txt"
        
        # 记录初始日志
        self.log(f"PPT下载器启动时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"日志文件: {self.log_file_path}")
        
    def save_log(self, output_dir):
        """
        保存日志到指定目录
        
        Args:
            output_dir (str): 保存目录
        """
        try:
            # 确保目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 获取日志内容
            log_content = self.log_text.get("1.0", tk.END)
            
            # 保存日志文件
            log_path = os.path.join(output_dir, self.log_file_path)
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(log_content)
                
            self.log(f"日志已保存到: {log_path}")
            return log_path
        except Exception as e:
            self.log(f"保存日志失败: {str(e)}")
            return None
    
    def log(self, message):
        """
        添加日志消息
        
        Args:
            message (str): 日志消息
        """
        # 获取当前时间
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 格式化日志消息
        log_message = f"[{now}] {message}\n"
        
        # 添加到日志文本框
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        
        # 更新GUI
        self.root.update_idletasks()
    
    def set_status(self, message):
        """
        设置状态栏消息
        
        Args:
            message (str): 状态消息
        """
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def browse_output_dir(self):
        """浏览并选择输出目录"""
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_var.set(directory)
    
    def on_table_click(self, event):
        """
        处理表格点击事件
        
        Args:
            event: 点击事件
        """
        # 获取点击的区域
        region = self.result_table.identify("region", event.x, event.y)
        
        # 如果点击的是单元格
        if region == "cell":
            # 获取点击的行和列
            row_id = self.result_table.identify_row(event.y)
            col_id = self.result_table.identify_column(event.x)
            
            # 如果点击的是第一列（选择列）
            if col_id == "#1" and row_id:
                # 获取当前值
                current_value = self.result_table.item(row_id, "values")[0]
                
                # 切换选择状态
                if current_value == "✓":
                    self.result_table.set(row_id, "选择", "")
                else:
                    self.result_table.set(row_id, "选择", "✓")
                    
                # 更新全选状态
                self.update_select_all_state()
                
                # 阻止进一步处理
                return "break"
    
    def on_result_double_click(self, event):
        """
        处理搜索结果双击事件
        
        Args:
            event: 双击事件
        """
        try:
            # 获取选中项
            selection = self.result_table.selection()
            if selection:
                item = selection[0]
                item_index = self.result_table.index(item)
                
                # 获取对应的搜索结果
                if 0 <= item_index < len(self.search_results):
                    result = self.search_results[item_index]
                    
                    # 打开详情页
                    import webbrowser
                    webbrowser.open(result["url"])
        except Exception as e:
            self.log(f"打开详情页失败: {str(e)}")
    
    def toggle_select_all(self):
        """切换全选状态"""
        # 获取全选状态
        is_select_all = self.select_all_var.get()
        
        # 更新所有行的选择状态
        for item in self.result_table.get_children():
            if is_select_all:
                self.result_table.set(item, "选择", "✓")
            else:
                self.result_table.set(item, "选择", "")
    
    def update_select_all_state(self):
        """更新全选复选框状态"""
        # 检查是否所有行都被选中
        all_selected = True
        for item in self.result_table.get_children():
            if self.result_table.item(item, "values")[0] != "✓":
                all_selected = False
                break
                
        # 更新全选复选框状态
        self.select_all_var.set(all_selected)
    
    async def search(self):
        """搜索PPT"""
        # 获取搜索关键词
        keyword = self.keyword_entry.get().strip()
        if not keyword:
            messagebox.showwarning("警告", "请输入搜索关键词")
            return
        
        # 获取最大结果数
        try:
            max_results = int(self.max_results_var.get())
            if max_results <= 0:
                raise ValueError("最大结果数必须大于0")
        except ValueError:
            messagebox.showwarning("警告", "请输入有效的最大结果数")
            return
        
        # 获取搜索网站
        source = self.source_var.get()
        
        # 设置状态
        self.is_searching = True
        self.search_button.config(state=tk.DISABLED)
        self.download_button.config(state=tk.DISABLED)
        self.set_status("正在搜索...")
        
        # 记录搜索日志
        self.log(f"开始搜索: {keyword} (网站: {source}, 最大结果数: {max_results})")
        
        try:
            # 根据来源选择爬虫
            if source == "1PPT":
                if self.oneppt_scraper is None:
                    self.log("初始化1PPT爬虫...")
                    self.oneppt_scraper = OnePptPlaywrightScraper()
                scraper = self.oneppt_scraper
            else:  # 优品PPT
                if self.ypppt_scraper is None:
                    self.log("初始化优品PPT爬虫...")
                    self.ypppt_scraper = YppptPlaywrightScraper()
                scraper = self.ypppt_scraper
            
            # 搜索PPT
            self.log("正在访问搜索页面...")
            results = await scraper.search(keyword, max_results=max_results)
            
            # 显示搜索结果
            self.log(f"找到 {len(results)} 个结果")
            await self.display_results(results)
            
        except Exception as e:
            self.log(f"搜索过程中发生错误: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
        finally:
            # 恢复状态
            self.is_searching = False
            self.search_button.config(state=tk.NORMAL)
            self.download_button.config(state=tk.NORMAL)
            self.set_status("搜索完成")
    
    async def display_results(self, results):
        """
        显示搜索结果
        
        Args:
            results (list): 搜索结果列表
        """
        # 清空现有结果
        for item in self.result_table.get_children():
            self.result_table.delete(item)
        
        self.search_results = results
        
        # 添加新结果
        for i, result in enumerate(results):
            # 准备表格数据
            item_data = (
                "✓",  # 默认选中
                result.get("title", ""),  # 标题
                result.get("source", ""),  # 来源
                result.get("date", ""),  # 日期
                result.get("category", "")  # 分类
            )
            
            # 插入表格
            self.result_table.insert("", "end", values=item_data)
            
            # 如果有缩略图，可以在日志中显示
            if "thumbnail" in result and result["thumbnail"]:
                self.log(f"结果 {i+1} 缩略图: {result['thumbnail']}")
                
        # 更新全选按钮状态
        self.select_all_var.set(True)
        
    async def download(self):
        """下载选中的PPT"""
        # 获取选中项
        selected_items = []
        for item in self.result_table.get_children():
            if self.result_table.item(item, "values")[0] == "✓":
                selected_items.append(item)
        
        if not selected_items:
            messagebox.showwarning("警告", "请选择要下载的PPT")
            return
        
        # 获取输出目录
        output_dir = self.output_dir_var.get()
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 设置状态
        self.is_downloading = True
        self.download_button.config(state=tk.DISABLED)
        self.search_button.config(state=tk.DISABLED)
        self.set_status("正在下载...")
        
        try:
            # 下载选中的PPT
            download_count = 0
            
            for item in selected_items:
                item_index = self.result_table.index(item)
                result = self.search_results[item_index]
                
                # 检查是否已经下载过（状态中包含"已下载"）
                current_status = self.result_table.item(item, "values")[0]
                if "已下载" in current_status:
                    self.log(f"跳过已下载的项目: {result['title']}")
                    continue
                
                self.log(f"\n正在下载: {result['title']} ({result['source']})")
                self.log(f"详情页URL: {result['url']}")
                
                # 根据来源选择爬虫
                if result['source'] == "1PPT":
                    if self.oneppt_scraper is None:
                        self.log("初始化1PPT爬虫...")
                        self.oneppt_scraper = OnePptPlaywrightScraper()
                    scraper = self.oneppt_scraper
                else:  # 优品PPT
                    if self.ypppt_scraper is None:
                        self.log("初始化优品PPT爬虫...")
                        self.ypppt_scraper = YppptPlaywrightScraper()
                    scraper = self.ypppt_scraper
                
                # 获取下载链接
                self.log("正在获取下载链接...")
                download_links = await scraper.get_download_links(result['url'])
                
                # 更新结果中的标题和日期（如果下载链接中有更详细的信息）
                if download_links['title'] and download_links['title'] != result['title']:
                    self.log(f"更新标题: {download_links['title']}")
                    result['title'] = download_links['title']
                    self.result_table.set(item, "标题", result['title'])
                
                if download_links['date'] and download_links['date'] != result['date']:
                    self.log(f"更新日期: {download_links['date']}")
                    result['date'] = download_links['date']
                    self.result_table.set(item, "日期", result['date'])
                
                if download_links['category'] and download_links['category'] != result['category']:
                    self.log(f"更新分类: {download_links['category']}")
                    result['category'] = download_links['category']
                    self.result_table.set(item, "分类", result['category'])
                
                self.log(f"获取到的下载链接: 本地链接={download_links['local']}, 网盘链接={download_links['netdisk']}")
                
                # 优先使用本地下载链接，如果没有则使用网盘链接
                download_url = download_links['local'] or download_links['netdisk']
                
                if not download_url:
                    self.log(f"未找到下载链接，跳过")
                    continue
                
                # 构建文件名（使用详情页获取的标题）
                title = download_links['title'] or result['title']
                if title:
                    file_name = f"{title}.zip"
                else:
                    file_name = f"{os.path.basename(result['url']).split('.')[0]}.zip"
                
                # 替换文件名中的非法字符
                file_name = file_name.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                file_path = os.path.join(output_dir, file_name)
                
                self.log(f"开始下载文件: {download_url}")
                self.log(f"保存到: {file_path}")
                
                # 下载文件，传递标题参数
                success = await scraper.download(download_url, file_path, title=title)
                
                if success:
                    download_count += 1
                    self.log(f"下载成功: {file_path}")
                    # 更新表格中的状态
                    self.result_table.set(item, "选择", "✓ (已下载)")
                    self.root.update_idletasks()
                else:
                    self.log(f"下载失败: {download_url}")
                    # 更新表格中的状态
                    self.result_table.set(item, "选择", "✓ (下载失败)")
                    self.root.update_idletasks()
                    
                    # 如果是网盘链接，保存到文件中
                    if "pan.baidu" in download_url or "quark" in download_url:
                        netdisk_file = os.path.join(output_dir, f"{title}_网盘链接.txt")
                        with open(netdisk_file, "w", encoding="utf-8") as f:
                            f.write(f"标题: {title}\n")
                            f.write(f"网盘链接: {download_url}\n")
                        self.log(f"网盘链接已保存到: {netdisk_file}")
            
            self.log(f"\n下载完成! 文件保存在: {os.path.abspath(output_dir)}")
            self.log(f"共下载 {download_count} 个PPT文件")
            
            # 保存日志到输出目录
            log_path = self.save_log(output_dir)
            
            # 下载完成后打开目录
            if download_count > 0:
                import webbrowser
                webbrowser.open(f"file://{os.path.abspath(output_dir)}")
            
        except Exception as e:
            self.log(f"下载过程中发生错误: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
        finally:
            # 恢复状态
            self.is_downloading = False
            self.download_button.config(state=tk.NORMAL)
            self.search_button.config(state=tk.NORMAL)
            self.set_status("下载完成")

    async def close_scrapers(self):
        """关闭爬虫实例"""
        try:
            if self.oneppt_scraper:
                await self.oneppt_scraper.close()
            if self.ypppt_scraper:
                await self.ypppt_scraper.close()
        except Exception as e:
            self.log(f"关闭爬虫时发生错误: {str(e)}")
            
if __name__ == "__main__":
    # 创建主窗口
    root = tk.Tk()
    app = PPTDownloaderGUI(root)
    
    # 运行主循环
    root.mainloop()
    
    # 关闭事件循环
    try:
        asyncio.run_coroutine_threadsafe(app.close_scrapers(), app.loop)
        app.loop.call_soon_threadsafe(app.loop.stop)
        app.thread.join(timeout=1.0)
    except Exception as e:
        print(f"关闭程序时发生错误: {e}") 