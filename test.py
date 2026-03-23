import os
import requests

# 配置
API_KEY = "你的API_Key"          # 替换成你的
SEARCH_QUERY = "clouds"          # 搜索关键词
LIMIT = 50                       # 每次请求数量（最大50）
TOTAL = 200                      # 想下载的总数（不超过1000）
OUTPUT_DIR = "./giphy_clouds"    # 保存文件夹

def download_gif(url, filepath):
    """下载单个GIF"""
    try:
        r = requests.get(url, stream=True, timeout=10)
        if r.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            print(f"下载成功: {filepath}")
        else:
            print(f"下载失败: {url}")
    except Exception as e:
        print(f"下载出错 {url}: {e}")

def search_and_download():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    offset = 0
    downloaded = 0

    while downloaded < TOTAL:
        # 调用搜索 API
        url = "https://api.giphy.com/v1/gifs/search"
        params = {
            "api_key": API_KEY,
            "q": SEARCH_QUERY,
            "limit": LIMIT,
            "offset": offset,
            "rating": "g"      # 限制等级，g 为大众级
        }
        response = requests.get(url, params=params)
        data = response.json()

        # 提取 GIF 原始 URL
        gifs = data.get("data", [])
        if not gifs:
            break   # 无更多结果

        for idx, gif in enumerate(gifs):
            if downloaded >= TOTAL:
                break
            # 优先使用 fixed_height 版本（尺寸适中），也可以选择 original
            gif_url = gif["images"]["fixed_height"]["url"]
            filename = f"{SEARCH_QUERY}_{offset+idx+1}.gif"
            filepath = os.path.join(OUTPUT_DIR, filename)
            download_gif(gif_url, filepath)
            downloaded += 1

        offset += LIMIT
        print(f"已下载 {downloaded} 个，继续下一页 offset={offset}...")

    print("下载完成！")

if __name__ == "__main__":
    search_and_download()