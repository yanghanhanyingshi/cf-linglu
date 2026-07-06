#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime
import time
import sys

# 目标网站URL
TARGET_URL = "https://cf.6610000.xyz/"
# 输出文件名
IP_FILE = "6610000ip.txt"
DOMAIN_FILE = "6610000cf.txt"

def fetch_page_content(url):
    """获取网页内容，带重试机制"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # 添加重试机制
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"第 {attempt + 1} 次尝试失败: {e}")
            if attempt < 2:
                time.sleep(5)  # 等待5秒后重试
            else:
                return None
    return None

def parse_ip_and_domain(html_content):
    """从HTML中解析IP和域名"""
    if not html_content:
        return set(), set()

    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    
    # IPv4 正则
    ipv4_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    # IPv6 正则（简化版）
    ipv6_pattern = r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|\b(?:[0-9a-fA-F]{1,4}:){1,7}:[0-9a-fA-F]{1,4}\b'
    # 域名正则
    domain_pattern = r'\b[a-zA-Z0-9.-]+\.6610000\.xyz\b'
    
    # 提取所有匹配
    ipv4_addresses = set(re.findall(ipv4_pattern, text))
    ipv6_addresses = set(re.findall(ipv6_pattern, text))
    domains = set(re.findall(domain_pattern, text))
    
    # 验证 IPv4
    valid_ips = set()
    for ip in ipv4_addresses:
        parts = ip.split('.')
        if all(0 <= int(part) <= 255 for part in parts):
            valid_ips.add(ip)
    
    # 添加 IPv6
    valid_ips.update(ipv6_addresses)
    
    # 验证域名
    valid_domains = {domain for domain in domains if domain.endswith('.6610000.xyz')}
    
    return valid_ips, valid_domains

def save_to_file(data, filename):
    """保存数据到文件"""
    if not data:
        print(f"警告：{filename} 没有数据可保存")
        return False
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for item in sorted(data):
                f.write(item + '\n')
        print(f"✅ 成功保存 {len(data)} 条记录到 {filename}")
        return True
    except IOError as e:
        print(f"❌ 保存文件 {filename} 失败: {e}")
        return False

def main():
    """主函数"""
    print(f"🔄 开始爬取: {TARGET_URL}")
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 获取网页内容
    html_content = fetch_page_content(TARGET_URL)
    if not html_content:
        print("❌ 爬取失败，程序退出。")
        sys.exit(1)
    
    # 解析IP和域名
    ips, domains = parse_ip_and_domain(html_content)
    
    print(f"📊 解析结果: IP地址 {len(ips)} 个, 域名 {len(domains)} 个")
    
    # 保存到文件
    ip_success = save_to_file(ips, IP_FILE)
    domain_success = save_to_file(domains, DOMAIN_FILE)
    
    if ip_success and domain_success:
        print("✅ 爬取完成！")
        sys.exit(0)
    else:
        print("⚠️ 部分数据保存失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
