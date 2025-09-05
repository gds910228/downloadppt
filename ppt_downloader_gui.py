#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PPT下载工具 - 图形用户界面版本
用于从1PPT.com和YPPPT.com网站搜索和下载PPT文件

作者：Claude AI
日期：2025-07-09
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from scrapers.oneppt import OnePptScraper
from scrapers.ypppt import YppptScraper
from scrapers.oneppt_playwright import OnePptPlaywrightScraper
import asyncio

# Playwright 异步封装，避免跨事件循环复用实例
def pw_search(keyword, number):
    async def _run():
        s = OnePptPlaywrightScraper()
        try:
            # 显式初始化，确保有可用的 page/context
            await s.initialize()
            return await s.search(keyword, number)
        finally:
            try:
                await s.close()
            except Exception:
                pass
    return asyncio.run(_run())

def pw_get_links(detail_url):
    async def _run():
        s = OnePptPlaywrightScraper()
        try:
            return await s.get_download_links(detail_url)
        finally:
            try:
                await s.close()
            except Exception:
                pass
    return asyncio.run(_run())

def pw_download(download_url, file_path, title):
    async def _run():
        s = OnePptPlaywrightScraper()
        try:
            return await s.download(download_url, file_path, title=title)
        finally:
            try:
                await s.close()
            except Exception:
                pass
    return asyncio.run(_run())

class RedirectText:
    """重定向标准输出到Text控件"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""
        
    def write(self, string):
        self.buffer += string
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)
        
    def flush(self):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, self.buffer)
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)
        self.buffer = ""

class PPTDownloaderGUI:
    """PPT下载器图形界面类"""
    def __init__(self, root):
        self.root = root
        self.root.title("PPT下载器")
        self.root.geometry("700x500")
        self.root.minsize(700, 500)
        
        # 设置窗口图标
        try:
            self.root.iconbitmap("ppt_icon.ico")
        except:
            pass
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建搜索框架
        self.search_frame = ttk.LabelFrame(self.main_frame, text="搜索设置", padding="10")
        self.search_frame.pack(fill=tk.X, pady=5)
        
        # 关键词
        ttk.Label(self.search_frame, text="搜索关键词:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.keyword_var = tk.StringVar()
        self.keyword_entry = ttk.Entry(self.search_frame, textvariable=self.keyword_var, width=30)
        self.keyword_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.keyword_entry.focus()
        
        # 网站选择
        ttk.Label(self.search_frame, text="搜索网站:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.site_var = tk.StringVar(value="all")
        self.site_combo = ttk.Combobox(self.search_frame, textvariable=self.site_var, width=10)
        self.site_combo["values"] = ["全部", "1PPT", "优品PPT"]
        self.site_combo.current(0)
        self.site_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # 下载数量
        ttk.Label(self.search_frame, text="下载数量:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.number_var = tk.IntVar(value=5)
        self.number_spinbox = ttk.Spinbox(self.search_frame, from_=1, to=1000, textvariable=self.number_var, width=5)
        self.number_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 保存路径
        ttk.Label(self.search_frame, text="保存路径:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.path_var = tk.StringVar(value="downloads")
        self.path_entry = ttk.Entry(self.search_frame, textvariable=self.path_var, width=20)
        self.path_entry.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        
        # 浏览按钮
        self.browse_btn = ttk.Button(self.search_frame, text="浏览...", command=self.browse_path)
        self.browse_btn.grid(row=1, column=4, sticky=tk.W, padx=5, pady=5)
        
        # 搜索按钮
        self.search_btn = ttk.Button(self.search_frame, text="搜索并下载", command=self.start_download)
        self.search_btn.grid(row=2, column=0, columnspan=4, sticky=tk.EW, padx=5, pady=10)
        
        # 帮助按钮
        self.help_btn = ttk.Button(self.search_frame, text="帮助", command=self.show_help)
        self.help_btn.grid(row=2, column=4, sticky=tk.EW, padx=5, pady=10)
        
        # 输出框架
        self.output_frame = ttk.LabelFrame(self.main_frame, text="输出信息", padding="10")
        self.output_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 输出文本框
        self.output_text = scrolledtext.ScrolledText(self.output_frame, wrap=tk.WORD, height=15)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.config(state=tk.DISABLED)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.main_frame, orient=tk.HORIZONTAL, length=100, mode='determinate', variable=self.progress_var)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(self.main_frame, textvariable=self.status_var, anchor=tk.W)
        self.status_label.pack(fill=tk.X, pady=5)
        
        # 重定向标准输出到文本框
        self.redirect = RedirectText(self.output_text)
        self.old_stdout = sys.stdout
        sys.stdout = self.redirect
        
        # 下载线程
        self.download_thread = None
        
        # 关闭窗口时恢复标准输出
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def browse_path(self):
        """浏览并选择保存路径"""
        path = filedialog.askdirectory()
        if path:
            self.path_var.set(path)
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """PPT下载器使用帮助：

1. 搜索关键词：输入要搜索的PPT关键词
2. 搜索网站：选择要搜索的网站（全部、1PPT或优品PPT）
3. 下载数量：设置要下载的PPT数量（1-1000）
4. 保存路径：设置PPT文件保存的位置
5. 点击"搜索并下载"开始下载
6. 下载过程和结果将显示在下方文本框

注意事项：
- 部分PPT可能为网盘链接，需要手动下载
- 避免短时间内频繁搜索，防止被网站封IP
- 如遇到下载失败，可能是网络问题或网站结构变化

祝您使用愉快！
"""
        messagebox.showinfo("使用帮助", help_text)
    
    def start_download(self):
        """开始下载线程"""
        # 检查关键词
        keyword = self.keyword_var.get().strip()
        if not keyword:
            messagebox.showwarning("警告", "请输入搜索关键词!")
            return
        
        # 获取网站选择
        site_map = {"全部": "all", "1PPT": "1ppt", "优品PPT": "ypppt"}
        site = site_map[self.site_combo.get()]
        
        # 获取下载数量
        try:
            number = int(self.number_var.get())
            if number < 1:
                number = 1
            elif number > 1000:
                number = 1000
        except:
            number = 5
        
        # 获取保存路径
        save_path = self.path_var.get()
        if not save_path:
            save_path = "downloads"
        
        # 创建保存目录
        if not os.path.exists(save_path):
            try:
                os.makedirs(save_path)
            except Exception as e:
                messagebox.showerror("错误", f"创建目录失败: {e}")
                return
        
        # 清空输出
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        
        # 禁用搜索按钮
        self.search_btn.config(state=tk.DISABLED)
        
        # 重置进度条
        self.progress_var.set(0)
        self.status_var.set("正在下载...")
        
        # 启动下载线程
        self.download_thread = threading.Thread(target=self.download_ppts, 
                                               args=(keyword, site, number, save_path))
        self.download_thread.daemon = True
        self.download_thread.start()
        
        # 定期检查线程状态
        self.root.after(100, self.check_thread)
    
    def download_ppts(self, keyword, site, number, save_path):
        """在线程中执行下载任务"""
        try:
            total_downloaded = 0
            
            # 从1PPT网站下载
            if site in ["1ppt", "all"]:
                print(f"\n===== 正在从1PPT网站搜索 '{keyword}' =====")
                oneppt_scraper = OnePptScraper()
                used_playwright = False
                search_results = oneppt_scraper.search(keyword, number)
                if not search_results:
                    try:
                        print("常规请求可能被反爬，启用 Playwright 兜底搜索...")
                        search_results = pw_search(keyword, number)
                        used_playwright = bool(search_results)
                        if not used_playwright:
                            print("Playwright 兜底搜索也未找到结果")
                    except Exception as e:
                        print(f"Playwright 兜底搜索失败: {e}")
                        used_playwright = False
                
                if search_results:
                    print(f"找到 {len(search_results)} 个相关PPT")
                    
                    for i, result in enumerate(search_results):
                        if total_downloaded >= number:
                            break
                        
                        print(f"\n[{i+1}/{len(search_results)}] {result['title']}")
                        print(f"正在获取下载链接...")
                        
                        # 更新进度条
                        progress = (i / len(search_results)) * (50 if site == "all" else 100)
                        self.progress_var.set(progress)
                        self.status_var.set(f"正在处理: {result['title']}")
                        
                        # 获取下载链接（根据是否启用 Playwright 兜底选择实现）
                        if 'used_playwright' in locals() and used_playwright:
                            download_links = pw_get_links(result['url'])
                        else:
                            download_links = oneppt_scraper.get_download_links(result['url'])
                        
                        if download_links['local'] or download_links['netdisk']:
                            # 优先使用本地下载链接
                            download_url = download_links['local'] if download_links['local'] else download_links['netdisk']
                            
                            # 确定文件名
                            if download_links['local']:
                                # 从URL提取文件名
                                file_name = os.path.basename(download_links['local'])
                                if not file_name or file_name == "" or "." not in file_name:
                                    file_name = f"{result['title']}.zip"
                            else:
                                # 网盘链接，使用标题作为文件名
                                file_name = f"{result['title']}_网盘链接.txt"
                            
                            # 安全的文件名
                            file_name = file_name.replace('/', '_').replace('\\', '_')
                            file_name = file_name.replace(':', '_').replace('*', '_')
                            file_name = file_name.replace('?', '_').replace('"', '_')
                            file_name = file_name.replace('<', '_').replace('>', '_')
                            file_name = file_name.replace('|', '_')
                            
                            # 文件保存路径
                            file_path = os.path.join(save_path, file_name)
                            
                            print(f"正在下载: {file_name}")
                            
                            # 如果是网盘链接，则保存链接到文本文件
                            if download_links['netdisk'] and not download_links['local']:
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.write(f"网盘下载链接: {download_links['netdisk']}\n")
                                print(f"网盘链接已保存到: {file_path}")
                                total_downloaded += 1
                            else:
                                # 下载文件（根据是否启用 Playwright 兜底选择实现）
                                if 'used_playwright' in locals() and used_playwright:
                                    success = pw_download(download_url, file_path, title=result['title'])
                                else:
                                    success = oneppt_scraper.download(download_url, file_path)
                                if success:
                                    total_downloaded += 1
                        else:
                            print(f"无法获取下载链接")
                else:
                    print(f"没有找到与 '{keyword}' 相关的PPT")
            
            # 从优品PPT网站下载
            if site in ["ypppt", "all"]:
                print(f"\n===== 正在从优品PPT网站搜索 '{keyword}' =====")
                ypppt_scraper = YppptScraper()
                search_results = ypppt_scraper.search(keyword, number)
                
                if search_results:
                    print(f"找到 {len(search_results)} 个相关PPT")
                    
                    for i, result in enumerate(search_results):
                        if total_downloaded >= number:
                            break
                        
                        print(f"\n[{i+1}/{len(search_results)}] {result['title']}")
                        print(f"正在获取下载链接...")
                        
                        # 更新进度条
                        base = 0 if site == "ypppt" else 50
                        progress = base + (i / len(search_results)) * (50 if site == "all" else 100)
                        self.progress_var.set(progress)
                        self.status_var.set(f"正在处理: {result['title']}")
                        
                        # 获取下载链接
                        download_links = ypppt_scraper.get_download_links(result['url'])
                        
                        if download_links['local'] or download_links['netdisk']:
                            # 优先使用本地下载链接
                            download_url = download_links['local'] if download_links['local'] else download_links['netdisk']
                            
                            # 确定文件名
                            if download_links['local']:
                                # 从URL提取文件名
                                file_name = os.path.basename(download_links['local'])
                                if not file_name or file_name == "" or "." not in file_name:
                                    file_name = f"{result['title']}.zip"
                            else:
                                # 网盘链接，使用标题作为文件名
                                file_name = f"{result['title']}_网盘链接.txt"
                            
                            # 安全的文件名
                            file_name = file_name.replace('/', '_').replace('\\', '_')
                            file_name = file_name.replace(':', '_').replace('*', '_')
                            file_name = file_name.replace('?', '_').replace('"', '_')
                            file_name = file_name.replace('<', '_').replace('>', '_')
                            file_name = file_name.replace('|', '_')
                            
                            # 文件保存路径
                            file_path = os.path.join(save_path, file_name)
                            
                            print(f"正在下载: {file_name}")
                            
                            # 如果是网盘链接，则保存链接到文本文件
                            if download_links['netdisk'] and not download_links['local']:
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.write(f"网盘下载链接: {download_links['netdisk']}\n")
                                print(f"网盘链接已保存到: {file_path}")
                                total_downloaded += 1
                            else:
                                # 下载文件
                                success = ypppt_scraper.download(download_url, file_path)
                                if success:
                                    total_downloaded += 1
                        else:
                            print(f"无法获取下载链接")
                else:
                    print(f"没有找到与 '{keyword}' 相关的PPT")
            
            print(f"\n下载完成! 文件保存在: {save_path}")
            print(f"共下载 {total_downloaded} 个PPT文件")
            
            self.progress_var.set(100)
            self.status_var.set(f"下载完成! 共下载 {total_downloaded} 个文件")
            
        except Exception as e:
            print(f"下载过程中发生错误: {e}")
            self.status_var.set("下载出错!")
    
    def check_thread(self):
        """检查下载线程状态"""
        if self.download_thread and self.download_thread.is_alive():
            # 线程仍在运行，继续检查
            self.root.after(100, self.check_thread)
        else:
            # 线程已结束，启用搜索按钮
            self.search_btn.config(state=tk.NORMAL)
    
    def on_close(self):
        """关闭窗口时的处理"""
        # 恢复标准输出
        sys.stdout = self.old_stdout
        
        # 关闭窗口
        self.root.destroy()

def main():
    """主函数"""
    root = tk.Tk()
    app = PPTDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 