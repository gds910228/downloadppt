#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
使用Playwright的PPT下载器
"""

import os
import sys
import asyncio
import argparse
from bs4 import BeautifulSoup
from scrapers.oneppt_playwright import OnePptPlaywrightScraper
from scrapers.ypppt_playwright import YppptPlaywrightScraper

async def search_and_download(keyword, output_dir, max_results=5, site=None):
    """
    搜索并下载PPT
    
    Args:
        keyword (str): 搜索关键词
        output_dir (str): 输出目录
        max_results (int): 最大下载数量
        site (str): 指定网站，可选值为"1ppt"或"ypppt"，默认为None（搜索所有网站）
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 初始化爬虫
    oneppt_scraper = None
    ypppt_scraper = None
    
    try:
        # 搜索结果
        all_results = []
        
        # 如果没有指定网站或指定为1ppt，则搜索1PPT网站
        if site is None or site.lower() == "1ppt":
            print(f"\n===== 正在从1PPT网站搜索 '{keyword}' =====")
            oneppt_scraper = OnePptPlaywrightScraper()
            oneppt_results = await oneppt_scraper.search(keyword, max_results)
            all_results.extend(oneppt_results)
            print(f"从1PPT网站找到 {len(oneppt_results)} 个结果")
        
        # 如果没有指定网站或指定为ypppt，则搜索优品PPT网站
        if site is None or site.lower() == "ypppt":
            print(f"\n===== 正在从优品PPT网站搜索 '{keyword}' =====")
            ypppt_scraper = YppptPlaywrightScraper()
            ypppt_results = await ypppt_scraper.search(keyword, max_results)
            all_results.extend(ypppt_results)
            print(f"从优品PPT网站找到 {len(ypppt_results)} 个结果")
        
        # 如果没有找到结果
        if not all_results:
            print(f"\n没有找到与 '{keyword}' 相关的PPT")
            return
        
        # 显示搜索结果
        print("\n===== 搜索结果 =====")
        for i, result in enumerate(all_results):
            print(f"{i+1}. {result['title']} ({result['source']})")
            print(f"   链接: {result['url']}")
            if result['thumbnail']:
                print(f"   缩略图: {result['thumbnail']}")
            if result['date']:
                print(f"   日期: {result['date']}")
            if result['category']:
                print(f"   分类: {result['category']}")
            print()
        
        # 下载PPT
        print("\n===== 开始下载 =====")
        download_count = 0
        
        for i, result in enumerate(all_results):
            if download_count >= max_results:
                break
            
            print(f"\n正在下载 ({i+1}/{len(all_results)}): {result['title']}")
            
            # 根据来源选择爬虫
            if result['source'] == "1PPT":
                if oneppt_scraper is None:
                    oneppt_scraper = OnePptPlaywrightScraper()
                scraper = oneppt_scraper
            else:  # 优品PPT
                if ypppt_scraper is None:
                    ypppt_scraper = YppptPlaywrightScraper()
                scraper = ypppt_scraper
            
            # 获取下载链接
            download_links = await scraper.get_download_links(result['url'])
            
            # 优先使用本地下载链接，如果没有则使用网盘链接
            download_url = download_links['local'] or download_links['netdisk']
            
            if not download_url:
                print(f"未找到下载链接，跳过")
                continue
            
            # 构建文件名
            file_name = f"{result['title']}.zip"
            # 替换文件名中的非法字符
            file_name = file_name.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            file_path = os.path.join(output_dir, file_name)
            
            # 下载文件
            success = await scraper.download(download_url, file_path)
            
            if success:
                download_count += 1
                print(f"下载成功: {file_path}")
            else:
                print(f"下载失败: {download_url}")
                # 如果是网盘链接，保存到文件中
                if "pan.baidu" in download_url or "quark" in download_url:
                    netdisk_file = os.path.join(output_dir, f"{result['title']}_网盘链接.txt")
                    with open(netdisk_file, "w", encoding="utf-8") as f:
                        f.write(f"标题: {result['title']}\n")
                        f.write(f"网盘链接: {download_url}\n")
                    print(f"网盘链接已保存到: {netdisk_file}")
        
        print(f"\n下载完成! 文件保存在: {os.path.abspath(output_dir)}")
        print(f"共下载 {download_count} 个PPT文件")
        
    except Exception as e:
        print(f"发生错误: {str(e)}")
    finally:
        # 关闭爬虫
        if oneppt_scraper:
            await oneppt_scraper.close()
        if ypppt_scraper:
            await ypppt_scraper.close()

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="PPT下载器 - 使用Playwright")
    parser.add_argument("keyword", help="搜索关键词")
    parser.add_argument("-o", "--output", default="downloads", help="输出目录")
    parser.add_argument("-n", "--number", type=int, default=5, help="最大下载数量")
    parser.add_argument("-s", "--site", choices=["1ppt", "ypppt"], help="指定搜索网站")
    args = parser.parse_args()
    
    # 创建输出目录
    output_dir = os.path.join(args.output, args.keyword)
    
    # 运行异步函数
    asyncio.run(search_and_download(args.keyword, output_dir, args.number, args.site))

if __name__ == "__main__":
    main() 