# PPT下载器

一个用于从1PPT和优品PPT网站搜索和下载PPT模板的工具。

## 功能特点

- 支持从1PPT和优品PPT两个网站搜索PPT模板
- 提供图形用户界面，操作简单直观
- 显示搜索结果的标题、日期、分类等信息
- 支持选择性下载，只下载用户勾选的PPT模板
- 自动获取PPT详情页的标题和日期信息
- 支持本地下载和网盘链接保存
- 提供操作日志，记录下载过程
- 自动打开下载目录，方便查看下载结果

## 安装要求

- Python 3.7+
- 依赖库：请查看requirements.txt

## 安装步骤

1. 克隆仓库：
```
git clone https://github.com/gds910228/downloadppt.git
cd downloadppt
```

2. 安装依赖：
```
pip install -r requirements.txt
```

3. 安装Playwright浏览器：
```
python -m playwright install
```

## 使用方法

### 图形界面版本

运行带有Playwright支持的图形界面版本：
```
python ppt_downloader_gui_with_playwright.py
```

1. 在搜索框中输入关键词
2. 选择搜索源（1PPT或优品PPT）
3. 点击"搜索"按钮
4. 在结果列表中勾选要下载的PPT
5. 点击"下载"按钮
6. 下载完成后会自动打开下载目录

### 命令行版本

运行带有Playwright支持的命令行版本：
```
python ppt_downloader_with_playwright.py
```

## 文件说明

- `ppt_downloader_gui_with_playwright.py`: 带有Playwright支持的图形界面版本
- `ppt_downloader_with_playwright.py`: 带有Playwright支持的命令行版本
- `scrapers/oneppt_playwright.py`: 1PPT网站的爬虫实现
- `scrapers/ypppt_playwright.py`: 优品PPT网站的爬虫实现
- `scrapers/base_scraper.py`: 爬虫基类
- `scrapers/playwright_scraper.py`: Playwright爬虫基类
- `requirements.txt`: 依赖库列表

## 注意事项

- 本工具仅供学习研究使用，请勿用于商业用途
- 下载的PPT模板版权归原作者所有，请遵守相关使用规定
- 使用过程中如遇到网站结构变化导致无法正常使用，请提交issue

## 更新日志

### 2023-07-15
- 修复了下载选择问题，现在只下载用户选中的项目
- 修复了标题显示问题，现在使用详情页面的标题作为文件名
- 优化了下载流程，提高了下载成功率
- 减少了等待时间，提高了操作速度

## 许可证

MIT 