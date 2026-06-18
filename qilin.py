from playwright.sync_api import sync_playwright
import re
import time
import os

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-images",
            ]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )

        page = context.new_page()

        try:
            print("正在打开：api.uouin.com/cloudflare.html")
            page.goto("https://api.uouin.com/cloudflare.html", timeout=60000)
            time.sleep(12)

            page_text = page.inner_text("body")
            ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
            all_ips = ip_pattern.findall(page_text)

            valid_ips = []
            for ip in all_ips:
                parts = ip.split(".")
                if len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts):
                    valid_ips.append(ip)

            unique_ips = list(set(valid_ips))
            unique_ips.sort()

            # 强制添加格式
            formatted_lines = [f"{ip}:443#☆灵鹿优选☆" for ip in unique_ips]

            # 直接保存在根目录
            with open("qilin_ip.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(formatted_lines))

            print(f"✅ 抓取完成！共获取 {len(formatted_lines)} 个优选IP（已格式化）")

        except Exception as e:
            print(f"❌ 错误：{str(e)}")
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    run()
