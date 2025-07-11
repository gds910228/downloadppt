#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import requests
from bs4 import BeautifulSoup

def test_1ppt():
    print("测试1PPT网站搜索功能")
    
    # 设置请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    # 搜索关键词
    keyword = "开学第一课"
    
    # 搜索URL
    try:
        # 将关键词编码为GBK格式
        encoded_keyword = keyword.encode('gbk').hex()
        encoded_keyword = "%".join([encoded_keyword[i:i+2] for i in range(0, len(encoded_keyword), 2)]).upper()
        encoded_keyword = "%" + encoded_keyword
        search_url = f"https://www.1ppt.com/plus/so.php?kwtype=0&q={encoded_keyword}"
        
        print(f"搜索URL: {search_url}")
        
        # 发送请求
        response = requests.get(search_url, headers=headers, timeout=10)
        response.encoding = 'gbk'
        
        print(f"状态码: {response.status_code}")
        
        # 解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 保存HTML以便检查
        with open("1ppt_response.html", "w", encoding='utf-8') as f:
            f.write(response.text)
        print("已保存响应到1ppt_response.html")
        
        # 查找搜索结果容器
        print("\n分析HTML结构...")
        
        # 查找常见的列表容器
        containers = [
            (".cList", "标准列表容器"),
            (".search-list", "搜索列表容器"),
            (".list", "通用列表"),
            ("#search-results", "搜索结果ID"),
            (".boxlist", "盒子列表")
        ]
        
        for selector, desc in containers:
            elements = soup.select(selector)
            print(f"{desc} ({selector}): 找到 {len(elements)} 个")
        
        # 查找所有链接
        all_links = soup.find_all('a')
        print(f"\n共找到 {len(all_links)} 个链接")
        
        # 查找可能包含关键词的链接
        keyword_links = []
        for link in all_links:
            text = link.get_text().strip()
            if "开学" in text or "第一课" in text:
                keyword_links.append(link)
                
        print(f"其中包含关键词的链接: {len(keyword_links)}")
        
        # 显示前5个包含关键词的链接
        for i, link in enumerate(keyword_links[:5]):
            text = link.get_text().strip()
            href = link.get("href", "")
            print(f"{i+1}. {text} - {href}")
            
        # 尝试查找h1/h2标题
        headings = soup.find_all(['h1', 'h2', 'h3'])
        print(f"\n找到 {len(headings)} 个标题")
        for i, heading in enumerate(headings[:5]):
            print(f"标题{i+1}: {heading.get_text().strip()}")
        
        # 查找搜索结果标记
        search_indicators = ["搜索结果", "找到相关", "为您找到", "搜索到"]
        for indicator in search_indicators:
            elements = soup.find_all(string=lambda text: indicator in text if text else False)
            if elements:
                print(f"\n找到搜索指示文本 '{indicator}': {len(elements)} 处")
                for el in elements[:2]:
                    print(f"  - {el.strip()}")
    
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print(f"Python版本: {sys.version}")
    test_1ppt() 