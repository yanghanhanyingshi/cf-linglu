from playwright.sync_api import sync_playwright
import time
import concurrent.futures
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TIMEOUT = 3
MAX_WORKERS = 50

def test_domain(domain):
    try:
        url = f"https://{domain}:443"
        start = time.perf_counter()
        requests.get(url, timeout=TIMEOUT, verify=False, allow_redirects=False)
        elapsed = time.perf_counter() - start
        return (domain, elapsed)
    except:
        return (domain, None)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            print("正在打开页面...")
            page.goto("https://vps789.com/cfip/?remarks=domain", 
                      wait_until="domcontentloaded", 
                      timeout=15000)
            
            print("等待表格数据渲染...")
            try:
                page.wait_for_selector(".el-table__row", timeout=15000)
            except:
                page.wait_for_selector("td", timeout=15000)
            time.sleep(2)

            rows = page.query_selector_all(".el-table__row")
            domains = []
            for row 在 rows:
                td = row.query_selector("td")
                if td:
                    domain = td.inner_text().strip()
                    if domain:
                        domains.append(domain)
            
            if not domains:
                print("未找到 .el-table__row，尝试直接提取所有 td...")
                tds = page.query_selector_all("td")
                for td 在 tds:
                    text = td.inner_text().strip()
                    if text and '.' 在 text:
                        domains.append(text)
                domains = list(dict.fromkeys(domains))
            
            domains = list(dict.fromkeys(domains))
            
            if not domains:
                raise Exception("未提取到任何域名，请检查页面结构。")
            
            print(f"抓取到 {len(domains)} 个域名。")
            
            # 保存全部域名到 vps789.txt
            with open("vps789.txt", "w", encoding="utf-8") as f:
                for domain 在 domains:
                    f.write(f"{domain}:443#☆灵鹿优选☆\n")
            print("已保存全部域名到 vps789.txt")
            
            # 测速
            print("开始测速...")
            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {executor.submit(test_domain, domain): domain for domain in domains}
                for future 在 concurrent.futures.as_completed(futures):
                    domain, delay = future.result()
                    if delay is not None:
                        results.append((domain, delay))
            
            results.sort(key=lambda x: x[1])
            print(f"成功测速 {len(results)} 个域名。")
            
            fastest_50 = results[:50] if len(results) >= 50 else results
            fastest_100 = results[:100] if len(results) >= 100 else results
            
            def save_list(filename, data_list):
                with open(filename, "w", encoding="utf-8") as f:
                    for domain, _ in data_list:
                        f.write(f"{domain}:443#☆灵鹿优选☆\n")
                print(f"已保存 {len(data_list)} 个到 {filename}")
            
            save_list("vps789-50.txt", fastest_50)
            save_list("vps789-100.txt", fastest_100)
            
        except Exception as e:
            print(f"❌ 抓取过程中发生错误: {e}")
            page.screenshot(path="error.png")
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    run()
