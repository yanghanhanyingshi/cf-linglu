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
            print(f"📡 第 {attempt + 1} 次尝试连接...")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            print(f"✅ 连接成功，状态码: {response.status_code}")
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"⚠️ 第 {attempt + 1} 次尝试失败: {e}")
            if attempt < 2:
                print(f"⏳ 等待 5 秒后重试...")
                time.sleep(5)
            else:
                print(f"❌ 所有重试均失败")
                return None
    return None

def parse_ip_and_domain(html_content):
    """从HTML中解析IP和域名"""
    if not html_content:
        print("⚠️ HTML内容为空")
        return set(), set()

    print("🔍 开始解析HTML内容...")
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    
    # IPv4 正则
    ipv4_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    # IPv6 正则（简化版）
    ipv6_pattern = r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|\b(?:[0-9a-fA-F]{1,4}:){1,7}:[0-9a-fA-F]{1,4}\b'
    # 域名正则
    domain_pattern = r'\b[a-zA-Z0-9.-]+\.6610000\.xyz\b'
    
    # 提取所有匹配
    print("📝 提取IPv4地址...")
    ipv4_addresses = set(re.findall(ipv4_pattern, text))
    print(f"  找到 {len(ipv4_addresses)} 个IPv4候选")
    
    print("📝 提取IPv6地址...")
    ipv6_addresses = set(re.findall(ipv6_pattern, text))
    print(f"  找到 {len(ipv6_addresses)} 个IPv6候选")
    
    print("📝 提取域名...")
    domains = set(re.findall(domain_pattern, text))
    print(f"  找到 {len(domains)} 个域名候选")
    
    # 验证 IPv4
    valid_ips = set()
    for ip in ipv4_addresses:
        try:
            parts = ip.split('.')
            if all(0 <= int(part) <= 255 for part in parts):
                valid_ips.add(ip)
        except ValueError:
            continue
    
    # 添加 IPv6
    valid_ips.update(ipv6_addresses)
    
    # 验证域名
    valid_domains = {domain for domain in domains if domain.endswith('.6610000.xyz')}
    
    print(f"✅ 解析完成: IP地址 {len(valid_ips)} 个, 域名 {len(valid_domains)} 个")
    return valid_ips, valid_domains

def save_to_file(data, filename):
    """保存数据到文件"""
    if not data:
        print(f"⚠️ {filename} 没有数据可保存")
        return False
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for item in sorted(data):
                f.write(item + '\n')
        print(f"✅ 成功保存 {len(data)} 条记录到 {filename}")
        
        # 显示前3条记录作为预览
        preview = list(sorted(data))[:3]
        if preview:
            print(f"  预览: {', '.join(preview)}")
        return True
    except IOError as e:
        print(f"❌ 保存文件 {filename} 失败: {e}")
        return False

def main():
    """主函数 - 带完整异常捕获"""
    try:
        print("=" * 50)
        print("🚀 开始执行爬虫程序")
        print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        # 1. 获取网页内容
        print(f"🌐 目标URL: {TARGET_URL}")
        html_content = fetch_page_content(TARGET_URL)
        if not html_content:
            print("❌ 爬取失败，无法获取网页内容")
            return 0  # 返回0，不报错退出
        
        # 2. 解析IP和域名
        ips, domains = parse_ip_and_domain(html_content)
        
        # 3. 保存到文件
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
