from playwright.sync_api import sync_playwright
import time

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
            page.wait_for_selector(".el-table__row", timeout=15000)
            time.sleep(2)

            rows = page.query_selector_all(".el-table__row")
            domains = []
            for row in rows:
                td = row.query_selector("td")
                if td:
                    domain = td.inner_text().strip()
                    if domain:
                        domains.append(domain)
            
            # 去重
            domains = list(dict.fromkeys(domains))
            
            # 写入根目录的 vps789.txt
            with open("vps789.txt", "w", encoding="utf-8") as f:
                for domain in domains:
                    f.write(f"{domain}:443#☆灵鹿优选☆\n")
            
            print(f"提取完成！抓取到 {len(domains)} 个域名，已保存为 vps789.txt。")
        except Exception as e:
            print(f"❌ 抓取过程中发生错误: {e}")
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    run()
