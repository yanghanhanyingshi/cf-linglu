#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime

TARGET_URL = "https://cf.6610000.xyz/"

IP_FILE = "6610000ip.txt"
DOMAIN_FILE = "6610000cf.txt"


def fetch_page_content(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        r.encoding = 'utf-8'
        print(f"✅ 请求成功，状态码: {r.status_code}")
        return r.text
    except Exception as e:
        print("❌ 请求失败:", e)
        return None


def parse_ip_and_domain(html):
    text = BeautifulSoup(html, "html.parser").get_text()

    # IPv4 匹配
    ipv4 = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text)
    # IPv6 匹配（可选，增强兼容）
    ipv6 = re.findall(r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|\b(?:[0-9a-fA-F]{1,4}:){1,7}:[0-9a-fA-F]{1,4}\b', text)
    # 域名匹配
    domains = re.findall(r'\b[a-zA-Z0-9.-]+\.6610000\.xyz\b', text)

    # 验证 IPv4
    valid_ips = []
    for ip in ipv4:
        parts = ip.split(".")
        if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            valid_ips.append(ip)
    
    # 添加 IPv6（直接加入，不做复杂验证）
    valid_ips.extend(ipv6)

    print(f"📊 解析结果: IPv4 {len(ipv4)} 个, IPv6 {len(ipv6)} 个, 域名 {len(domains)} 个")
    return set(valid_ips), set(domains)


def save_file(filename, data):
    # ⭐ 关键：即使为空也创建文件
    with open(filename, "w", encoding="utf-8") as f:
        if data:
            for i in sorted(data):
                f.write(i + "\n")
        # else: 文件保持为空（已通过打开文件自动创建）

    print(f"✅ 写入 {filename}: {len(data)} 条记录")


def main():
    print("=" * 50)
    print("🚀 开始执行爬虫程序")
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    html = fetch_page_content(TARGET_URL)
    if not html:
        print("❌ 获取网页内容失败，退出")
        return 1

    ips, domains = parse_ip_and_domain(html)
    
    # 显示部分结果预览
    if ips:
        preview = list(ips)[:3]
        print(f"  IP预览: {', '.join(preview)}")
    if domains:
        preview = list(domains)[:3]
        print(f"  域名预览: {', '.join(preview)}")

    save_file(IP_FILE, ips)
    save_file(DOMAIN_FILE, domains)

    print("=" * 50)
    print("🎉 爬虫执行完成")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    exit(main())
