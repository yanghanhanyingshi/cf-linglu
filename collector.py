import cloudscraper
import re
import time
from datetime import datetime

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

def fetch_proxies(url):
    proxies = []
    try:
        scraper = cloudscraper.create_scraper()
        resp = scraper.get(url, headers=HEADERS, timeout=30)
        resp.encoding = "utf-8"
        # 使用正则从整个页面提取 IP:PORT（更灵活）
        # 匹配 IPv4 地址 + 端口
        pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*[:：]\s*(\d+)"
        matches = re.findall(pattern, resp.text)
        for ip, port in matches:
            # 简单过滤私有IP或无效端口（可选）
            if int(port) > 0 and int(port) < 65536:
                proxies.append(f"{ip}:{port}")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return proxies

def main():
    all_proxies = []
    for url in URLS:
        print(f"Fetching: {url}")
        prox = fetch_proxies(url)
        print(f"Found {len(prox)} proxies")
        all_proxies.extend(prox)
        time.sleep(2)  # 礼貌性等待

    # 去重（保持顺序）
    unique = list(dict.fromkeys(all_proxies))

    # 生成目标格式
    output = []
    for idx, item in enumerate(unique, 1):
        ip, port = item.split(":")
        output.append(f"{ip}-{port}-{idx}-☆灵鹿公益☆")

    # 写入文件
    with open("proxies.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    print(f"Total unique proxies: {len(output)}")
    print(f"Saved to proxies.txt at {datetime.now()}")

if __name__ == "__main__":
    main()
