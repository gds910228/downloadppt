#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
from scrapers.oneppt_playwright import OnePptPlaywrightScraper

async def test_1ppt_paging():
    """测试1PPT网站的翻页功能"""
    print("开始测试1PPT网站的翻页功能...")
    
    # 创建爬虫实例
    scraper = OnePptPlaywrightScraper()
    
    try:
        # 初始化爬虫
        await scraper.initialize()
        
        # 搜索"开学第一课"，获取50个结果（需要翻页）
        results = await scraper.search('开学第一课', max_results=50)
        
        # 输出结果
        print(f"共找到 {len(results)} 个结果")
        
        # 打印前5个和后5个结果
        print("\n前5个结果:")
        for i, result in enumerate(results[:5]):
            print(f"{i+1}. {result['title']} - {result['url']}")
            
        if len(results) > 5:
            print("\n后5个结果:")
            for i, result in enumerate(results[-5:]):
                print(f"{len(results)-4+i}. {result['title']} - {result['url']}")
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    finally:
        # 关闭爬虫
        await scraper.close()
        print("测试完成")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_1ppt_paging()) 