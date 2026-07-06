#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime
import time

# 目标网站URL
TARGET_URL = "https://cf.6610000.xyz/"
# 输出文件名
IP_FILE = "6610000ip.txt"
DOMAIN_FILE = "6610000cf.txt"

def fetch_page_content(url):
    """
    获取网页内容，并处理可能的请求失败
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # 检查请求是否成功
        response.encoding = 'utf-8'  # 明确指定编码
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"获取网页内容失败: {e}")
        return None

def parse_ip_and_domain(html_content):
    """
    从HTML内容中解析出所有IP地址（IPv4和IPv6）和域名
    """
    if not html_content:
        return set(), set()

    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 找到所有可能包含IP和域名的文本块
    # 基于页面结构，IP和域名出现在类似 "域名 xxx.6610000.xyz" 和 "IP xxx.xxx.xxx.xxx" 的格式中
    text = soup.get_text()
    
    # 正则表达式匹配IPv4地址
    ipv4_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    # 正则表达式匹配IPv6地址（简化版，匹配常见的IPv6格式）
    ipv6_pattern = r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|\b(?:[0-9a-fA-F]{1,4}:){1,7}:[0-9a-fA-F]{1,4}\b|\b(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}\b|\b(?:[0-9a-fA-F]{1,4}:){1,5}:[0-9a-fA-F]{1,4}\b|\b(?:[0-9a-fA-F]{1,4}:){1,4}:[0-9a-fA-F]{1,4}\b|\b(?:[0-9a-fA-F]{1,4}:){1,3}:[0-9a-fA-F]{1,4}\b|\b(?:[0-9a-fA-F]{1,4}:){1,2}:[0-9a-fA-F]{1,4}\b|\b[0-9a-fA-F]{1,4}::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}\b'
    # 匹配以 .6610000.xyz 结尾的域名
    domain_pattern = r'\b[a-zA-Z0-9.-]+\.6610000\.xyz\b'
    
    # 查找所有匹配项
    ipv4_addresses = set(re.findall(ipv4_pattern, text))
    ipv6_addresses = set(re.findall(ipv6_pattern, text))
    domains = set(re.findall(domain_pattern, text))
    
    # 合并IPv4和IPv6地址
    all_ips = ipv4_addresses.union(ipv6_addresses)
    
    # 过滤掉可能不是有效IP的匹配（例如，数字太大的IPv4）
    valid_ips = set()
    for ip in all_ips:
        if ':' in ip:  # IPv6
            # 简单的IPv6有效性检查：如果包含多个冒号且长度合理，认为有效
            if ip.count(':') >= 2:
                valid_ips.add(ip)
        else:  # IPv4
            parts = ip.split('.')
            if all(0 <= int(part) <= 255 for part in parts):
                valid_ips.add(ip)
    
    # 过滤域名，只保留以 .6610000.xyz 结尾的
    valid_domains = {domain for domain in domains if domain.endswith('.6610000.xyz')}
    
    return valid_ips, valid_domains

def save_to_file(data, filename):
    """
    将数据保存到文件，每个条目一行
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for item in sorted(data):
                f.write(item + '\n')
        print(f"成功保存 {len(data)} 条记录到 {filename}")
    except IOError as e:
        print(f"保存文件 {filename} 失败: {e}")

def main():
    """
    主函数：执行爬取和保存流程
    """
    print(f"开始爬取: {TARGET_URL} 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 获取网页内容
    html_content = fetch_page_content(TARGET_URL)
    if not html_content:
        print("爬取失败，程序退出。")
        return
    
    # 2. 解析IP和域名
    ips, domains = parse_ip_and_domain(html_content)
    
    # 3. 保存到文件
    if ips:
        save_to_file(ips, IP_FILE)
    else:
        print("警告：未解析到任何IP地址。")
    
    if domains:
        save_to_file(domains, DOMAIN_FILE)
    else:
        print("警告：未解析到任何域名。")
    
    print(f"爬取完成。IP数量: {len(ips)}, 域名数量: {len(domains)}")

if __name__ == "__main__":
    main()
