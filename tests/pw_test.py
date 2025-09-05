import os
import sys
from pprint import pprint

# 确保可以从项目根目录导入模块
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 复用 GUI 中的同步封装，避免事件循环冲突
from ppt_downloader_gui import pw_search, pw_get_links, pw_download

def main():
    kw = "中秋节"
    n = 5
    print(f"[TEST] Playwright 兜底搜索: {kw} (top {n})")
    results = pw_search(kw, n)
    print(f"[TEST] 搜索结果数量: {len(results)}")
    for idx, r in enumerate(results, 1):
        title = r.get("title", "").strip()
        url = r.get("url", "")
        print(f"[{idx}] {title} -> {url}")
        links = pw_get_links(url)
        print(f"[{idx}] 下载链接:"); pprint(links)
        if links.get("local"):
            # 确保保存目录
            save_dir = os.path.join("downloads", "中秋节")
            os.makedirs(save_dir, exist_ok=True)
            # 交给封装以标题命名文件，传入缺省扩展名以便推断
            fp = os.path.join(save_dir, "tmp.zip")
            ok = pw_download(links["local"], fp, title=title or "中秋节PPT")
            print(f"[{idx}] 下载结果: {ok}")
            break

if __name__ == "__main__":
    main()