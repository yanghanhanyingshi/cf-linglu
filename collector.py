import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
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
    try:
        driver.get(url)
        time.sleep(8)  # 增加等待时间确保JS渲染
        html = driver.page_source
        # 打印部分HTML用于调试（可选）
        # print(html[:500])
        pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*[:：]\s*(\d+)"
        matches = re.findall(pattern, html)
        proxies = []
        for ip, port in matches:
            if 0 < int(port) < 65536:
                proxies.append(f"{ip}:{port}")
        return proxies
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return []

def main():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    # 隐藏webdriver特征
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    all_proxies = []
    for url in URLS:
        print(f"Fetching {url}")
        proxies = get_proxies_from_page(driver, url)
        print(f"Found {len(proxies)} proxies on {url}")
        all_proxies.extend(proxies)
        time.sleep(2)

    driver.quit()

    # 去重
    unique = []
    seen = set()
    for p in all_proxies:
        if p not in seen:
            seen.add(p)
            unique.append(p)

    output_lines = []
    for idx, proxy in enumerate(unique, 1):
        ip, port = proxy.split(":")
        output_lines.append(f"{ip}-{port}-{idx}-☆灵鹿公益☆")

    # 写入文件
    with open("proxies.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"Total unique proxies: {len(output_lines)}")
    print(f"File written at {datetime.now()}")

if __name__ == "__main__":
    main()
