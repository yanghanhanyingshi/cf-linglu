#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime
import time
import sys

# 获取脚本所在目录的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 使用绝对路径定义输出文件
IP_FILE = os.path.join(BASE_DIR, "6610000ip.txt")
DOMAIN_FILE = os.path.join(BASE_DIR, "6610000cf.txt")
TARGET_URL = "https://cf.6610000.xyz/"

# ... (fetch_page_content, parse_ip_and_domain, save_to_file 函数与之前完全一致，无需修改) ...

def main():
    """主函数 - 带完整异常捕获"""
    try:
        print("=" * 50)
        print("🚀 开始执行爬虫程序")
        print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 文件保存目录: {BASE_DIR}")
        print("=" * 50)
        
        html_content = fetch_page_content(TARGET_URL)
        if not html_content:
            print("❌ 爬取失败，无法获取网页内容")
            return 0
        
        ips, domains = parse_ip_and_domain(html_content)
        
        ip_success = save_to_file(ips, IP_FILE)
        domain_success = save_to_file(domains, DOMAIN_FILE)
        
        print("=" * 50)
        if ip_success and domain_success:
            print("🎉 爬取完成！")
        else:
            print("⚠️ 部分数据保存失败，但程序已正常结束")
        print("=" * 50)
        return 0
        
    except Exception as e:
        print("=" * 50)
        print(f"💥 发生异常: {type(e).__name__}")
        print(f"📝 异常信息: {str(e)}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
