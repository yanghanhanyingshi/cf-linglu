import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import re
from datetime import datetime

URLS = [
    "https://spys.one/en/free-proxy-list/",
    "https://spys.one/en/anonymous-proxy-list/",
    "https://spys.one/en/https-ssl-proxy/",
    "https://spys.one/en/socks-proxy-list/",
    "https://spys.one/en/http-proxy-list/",
]

def get_proxies_from_page(driver, url):
    driver.get(url)
    time.sleep(5)  # 等待JS执行
    html = driver.page_source
    # 此时端口已经显示为数字
    pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*[:：]\s*(\d+)"
    matches = re.findall(pattern, html)
    proxies = [f"{ip}:{port}" for ip, port in matches if 0 < int(port) < 65536]
    return proxies

def main():
    # 配置无头 Chrome
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    all_proxies = []

    for url in URLS:
        print(f"Fetching {url}")
        proxies = get_proxies_from_page(driver, url)
        print(f"Found {len(proxies)}")
        all_proxies.extend(proxies)
        time.sleep(2)

    driver.quit()

    # 去重
    unique = list(dict.fromkeys(all_proxies))
    output = [f"{ip}-{port}-{idx}-☆灵鹿公益☆" for idx, (ip, port) in enumerate([p.split(":") for p in unique], 1)]

    with open("proxies.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    print(f"Total unique: {len(output)}")

if __name__ == "__main__":
    main()
