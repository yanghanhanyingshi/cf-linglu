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
            "User-Agent": "Mozilla/5.0"
        }
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print("请求失败:", e)
        return None


def parse_ip_and_domain(html):
    text = BeautifulSoup(html, "html.parser").get_text()

    ipv4 = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text)
    domains = re.findall(r'\b[a-zA-Z0-9.-]+\.6610000\.xyz\b', text)

    valid_ips = []
    for ip in ipv4:
        parts = ip.split(".")
        if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            valid_ips.append(ip)

    return set(valid_ips), set(domains)


def save_file(filename, data):
    if not data:
        print(f"{filename} 为空，跳过写入")
        return

    with open(filename, "w", encoding="utf-8") as f:
        for i in sorted(data):
            f.write(i + "\n")

    print(f"写入 {filename}: {len(data)} 条")


def main():
    print("=== 开始执行爬虫 ===")

    html = fetch_page_content(TARGET_URL)
    if not html:
        print("获取失败，退出")
        return 1

    ips, domains = parse_ip_and_domain(html)

    save_file(IP_FILE, ips)
    save_file(DOMAIN_FILE, domains)

    print("完成")
    return 0


if __name__ == "__main__":
    exit(main())
