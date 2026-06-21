import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime

# 要采集的页面列表
URLS = [
    "https://spys.one/en/free-proxy-list/",
    "https://spys.one/en/anonymous-proxy-list/",
    "https://spys.one/en/https-ssl-proxy/",
    "https://spys.one/en/socks-proxy-list/",
    "https://spys.one/en/http-proxy-list/",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_proxies_from_page(url):
    """从单个页面提取代理 IP 和端口"""
    proxies = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")

        # Spys.one 的代理列表通常在 <table> 中，具体选择器需根据实际页面调整
        # 这里提供一种常见的解析方式示例
        rows = soup.select("table table tr")
        for row in rows:
            text = row.get_text(strip=True)
            # 匹配 IP:PORT 格式
            match = re.search(r"(\d+\.\d+\.\d+\.\d+)\s*:\s*(\d+)", text)
            if match:
                ip = match.group(1)
                port = match.group(2)
                proxies.append(f"{ip}:{port}")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return proxies

def main():
    all_proxies = []
    for url in URLS:
        print(f"Fetching: {url}")
        proxies = fetch_proxies_from_page(url)
        all_proxies.extend(proxies)
        time.sleep(2)  # 礼貌性延时

    # 去重
    unique_proxies = list(dict.fromkeys(all_proxies))

    # 按 "IP-端口-序号-☆灵鹿公益☆" 格式输出
    output_lines = []
    for idx, proxy in enumerate(unique_proxies, 1):
        ip, port = proxy.split(":")
        output_lines.append(f"{ip}-{port}-{idx}-☆灵鹿公益☆")

    # 写入文件
    with open("proxies.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"Total proxies collected: {len(output_lines)}")
    print(f"Saved to proxies.txt at {datetime.now()}")

if __name__ == "__main__":
    main()
