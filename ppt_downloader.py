#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PPT下载工具
用于从1PPT.com和YPPPT.com网站搜索和下载PPT文件

作者：Claude AI
日期：2025-07-09
"""

import os
import sys
import time
import argparse
from scrapers.oneppt import OnePptScraper
from scrapers.ypppt import YppptScraper

def create_directory(directory):
    """创建目录，如果不存在"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"创建目录: {directory}")

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='从1PPT和优品PPT网站下载PPT')
    parser.add_argument('keyword', help='要搜索的关键词')
    parser.add_argument('-s', '--site', choices=['1ppt', 'ypppt', 'all'], default='all',
                        help='选择下载网站 (1ppt, ypppt, 或 all)')
    parser.add_argument('-n', '--number', type=int, default=5,
                        help='要下载的最大PPT数量，默认为5')
    parser.add_argument('-o', '--output', default='downloads',
                        help='下载文件保存目录，默认为downloads')
    args = parser.parse_args()
    
    # 创建保存目录
    output_dir = args.output
    create_directory(output_dir)
    
    # 搜索并下载PPT
    total_downloaded = 0
    
    # 从1PPT网站下载
    if args.site in ['1ppt', 'all']:
        print(f"\n===== 正在从1PPT网站搜索 '{args.keyword}' =====")
        oneppt_scraper = OnePptScraper()
        search_results = oneppt_scraper.search(args.keyword, args.number)
        
        if search_results:
            print(f"找到 {len(search_results)} 个相关PPT")
            
            for i, result in enumerate(search_results):
                if total_downloaded >= args.number:
                    break
                
                print(f"\n[{i+1}/{len(search_results)}] {result['title']}")
                print(f"正在获取下载链接...")
                
                # 获取下载链接
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
                    file_path = os.path.join(output_dir, file_name)
                    
                    print(f"正在下载: {file_name}")
                    
                    # 如果是网盘链接，则保存链接到文本文件
                    if download_links['netdisk'] and not download_links['local']:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(f"网盘下载链接: {download_links['netdisk']}\n")
                        print(f"网盘链接已保存到: {file_path}")
                        total_downloaded += 1
                    else:
                        # 下载文件
                        success = oneppt_scraper.download(download_url, file_path)
                        if success:
                            total_downloaded += 1
                else:
                    print(f"无法获取下载链接")
        else:
            print(f"没有找到与 '{args.keyword}' 相关的PPT")
    
    # 从优品PPT网站下载
    if args.site in ['ypppt', 'all']:
        print(f"\n===== 正在从优品PPT网站搜索 '{args.keyword}' =====")
        ypppt_scraper = YppptScraper()
        search_results = ypppt_scraper.search(args.keyword, args.number)
        
        if search_results:
            print(f"找到 {len(search_results)} 个相关PPT")
            
            for i, result in enumerate(search_results):
                if total_downloaded >= args.number:
                    break
                
                print(f"\n[{i+1}/{len(search_results)}] {result['title']}")
                print(f"正在获取下载链接...")
                
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
                    file_path = os.path.join(output_dir, file_name)
                    
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
            print(f"没有找到与 '{args.keyword}' 相关的PPT")
    
    print(f"\n下载完成! 文件保存在: {output_dir}")
    print(f"共下载 {total_downloaded} 个PPT文件")

if __name__ == "__main__":
    main() 