import re
import os
import time
import socket
import json
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import requests
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linglu.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===== 核心配置 =====
CONFIG = {
    "ip_sources": [
        'https://api.uouin.com/cloudflare.html',
        'https://api.urlce.com/cloudflare.html',
        'https://addressesapi.090227.xyz/CloudFlareYes',
        'https://cf.090227.xyz/CloudFlareYes',
        'https://stock.hostmonit.com/CloudFlareYes',
        'https://vps789.com/openApi/cfIpTop20',
        'https://vps789.com/openApi/cfIpApi',
        'https://www.wetest.vip/page/cloudflare/total_v4.html',
        'https://www.wetest.vip/page/cloudflare/address_v4.html',
        'https://cf.090227.xyz/cmcc',
        'https://cf.090227.xyz/ct',
        'https://raw.githubusercontent.com/ymyuuu/IPDB/main/BestCF/bestcfv4.txt',
        'https://ipdb.api.030101.xyz/?type=bestcf&country=true',
    ],
    
    "test_ports": [443, 2052, 2053, 2082, 2083, 2086, 2087, 2095, 2096, 8443, 8444],
    "timeout": 10,
    "api_timeout": 5,
    "query_interval": 0.2,
    "max_workers": 20,
    "batch_size": 15,
    "cache_ttl_hours": 168,
    "advanced_mode": True,
    "bandwidth_test_count": 3,
    "bandwidth_test_size_mb": 10,
    "latency_filter_percentage": 30,
}

# ===== 国家/地区映射表 =====
COUNTRY_MAPPING = {
    'US': '美国', 'CA': '加拿大', 'MX': '墨西哥', 'GB': '英国', 'UK': '英国',
    'FR': '法国', 'DE': '德国', 'IT': '意大利', 'ES': '西班牙', 'NL': '荷兰',
    'RU': '俄罗斯', 'SE': '瑞典', 'CH': '瑞士', 'BE': '比利时', 'AT': '奥地利',
    'PL': '波兰', 'DK': '丹麦', 'NO': '挪威', 'FI': '芬兰', 'PT': '葡萄牙',
    'IE': '爱尔兰', 'UA': '乌克兰', 'CZ': '捷克', 'GR': '希腊', 'HU': '匈牙利',
    'RO': '罗马尼亚', 'TR': '土耳其', 'BG': '保加利亚', 'LT': '立陶宛', 'LV': '拉脱维亚',
    'EE': '爱沙尼亚', 'BY': '白俄罗斯', 'LU': '卢森堡', 'SI': '斯洛文尼亚', 'SK': '斯洛伐克',
    'MT': '马耳他', 'HR': '克罗地亚', 'RS': '塞尔维亚', 'BA': '波黑', 'ME': '黑山',
    'MK': '北马其顿', 'AL': '阿尔巴尼亚', 'MD': '摩尔多瓦', 'GE': '格鲁吉亚',
    'AM': '亚美尼亚', 'AZ': '阿塞拜疆', 'CY': '塞浦路斯',
    'CN': '中国', 'HK': '中国香港', 'TW': '中国台湾', 'MO': '中国澳门',
    'JP': '日本', 'KR': '韩国', 'SG': '新加坡', 'SGP': '新加坡',
    'IN': '印度', 'ID': '印度尼西亚', 'MY': '马来西亚', 'MYS': '马来西亚',
    'TH': '泰国', 'PH': '菲律宾', 'VN': '越南', 'PK': '巴基斯坦',
    'BD': '孟加拉', 'KZ': '哈萨克斯坦', 'IL': '以色列', 'ISR': '以色列',
    'SA': '沙特阿拉伯', 'SAU': '沙特阿拉伯', 'AE': '阿联酋',
    'AU': '澳大利亚', 'NZ': '新西兰',
    'ZA': '南非', 'EG': '埃及', 'NG': '尼日利亚', 'KE': '肯尼亚',
    'BR': '巴西', 'AR': '阿根廷', 'CL': '智利', 'CO': '哥伦比亚',
    'PE': '秘鲁', 'VE': '委内瑞拉', 'UY': '乌拉圭', 'PY': '巴拉圭',
    'Unknown': '未知'
}

region_cache = {}

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
})

adapter = requests.adapters.HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20,
    max_retries=3
)
session.mount('http://', adapter)
session.mount('https://', adapter)

# ===== 缓存管理函数 =====
def load_region_cache():
    global region_cache
    if os.path.exists('Cache.json'):
        try:
            with open('Cache.json', 'r', encoding='utf-8') as f:
                region_cache = json.load(f)
            logger.info(f"📦 加载缓存: {len(region_cache)} 个条目")
        except:
            region_cache = {}
    else:
        region_cache = {}

def save_region_cache():
    try:
        with open('Cache.json', 'w', encoding='utf-8') as f:
            json.dump(region_cache, f, ensure_ascii=False)
        logger.info(f"💾 保存缓存: {len(region_cache)} 个条目")
    except:
        pass

def is_cache_valid(timestamp, ttl_hours=24):
    if not timestamp:
        return False
    try:
        cache_time = datetime.fromisoformat(timestamp)
        return datetime.now() - cache_time < timedelta(hours=ttl_hours)
    except:
        return False

def clean_expired_cache():
    global region_cache
    current_time = datetime.now()
    expired_keys = []
    for ip, data in region_cache.items():
        if isinstance(data, dict) and 'timestamp' in data:
            try:
                cache_time = datetime.fromisoformat(data['timestamp'])
                if current_time - cache_time >= timedelta(hours=CONFIG["cache_ttl_hours"]):
                    expired_keys.append(ip)
            except:
                pass
    for key in expired_keys:
        del region_cache[key]
    if len(region_cache) > 1000:
        sorted_items = sorted(region_cache.items(), 
                            key=lambda x: x[1].get('timestamp', '') if isinstance(x[1], dict) else '')
        items_to_remove = len(region_cache) - 1000
        for i in range(items_to_remove):
            del region_cache[sorted_items[i][0]]
    if expired_keys:
        logger.info(f"清理了 {len(expired_keys)} 个过期缓存")

def delete_file_if_exists(file_path):
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"🗑️ 已删除: {file_path}")
        except:
            pass

# ===== 网络测试函数 =====
def test_ip_availability(ip):
    """
    TCP Socket检测IP可用性 - 支持多端口自定义
    增加连接超时和重试机制
    """
    try:
        parts = ip.split('.')
        if len(parts) != 4 or not all(0 <= int(p) <= 255 for p in parts):
            return (False, 0)
    except:
        return (False, 0)
    
    min_delay = float('inf')
    success_count = 0
    
    for port in CONFIG["test_ports"]:
        try:
            if not isinstance(port, int) or not (1 <= port <= 65535):
                continue
                
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                start_time = time.time()
                
                if s.connect_ex((ip, port)) == 0:
                    delay = round((time.time() - start_time) * 1000)
                    min_delay = min(min_delay, delay)
                    success_count += 1
                    
                    if delay < 300:
                        return (True, delay)
        except (socket.timeout, socket.error, OSError):
            continue
        except Exception:
            continue
    
    if success_count > 0:
        return (True, min_delay)
    
    return (False, 0)

def test_ips_concurrently(ips, max_workers=None):
    if max_workers is None:
        max_workers = CONFIG["max_workers"]
    
    logger.info(f"📡 并发检测 {len(ips)} 个IP")
    available_ips = []
    batch_size = CONFIG["batch_size"]
    
    for i in range(0, len(ips), batch_size):
        batch_ips = ips[i:i+batch_size]
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_ip = {executor.submit(test_ip_availability, ip): ip for ip in batch_ips}
            for future in as_completed(future_to_ip, timeout=30):
                ip = future_to_ip[future]
                try:
                    is_available, delay = future.result()
                    if is_available:
                        available_ips.append((ip, delay))
                except:
                    continue
    return available_ips

# ===== 地区识别函数 =====
def get_ip_region(ip):
    if ip in region_cache:
        cached_data = region_cache[ip]
        if isinstance(cached_data, dict) and 'timestamp' in cached_data:
            if is_cache_valid(cached_data['timestamp'], CONFIG["cache_ttl_hours"]):
                return cached_data['region']
        else:
            return cached_data
    
    try:
        resp = session.get(f'https://api.ipinfo.io/lite/{ip}?token=2cb674df499388', timeout=CONFIG["api_timeout"])
        if resp.status_code == 200:
            data = resp.json()
            country_code = data.get('country_code', '').upper()
            if country_code:
                region_cache[ip] = {'region': country_code, 'timestamp': datetime.now().isoformat()}
                return country_code
    except:
        pass
    
    try:
        resp = session.get(f'http://ip-api.com/json/{ip}?fields=countryCode', timeout=CONFIG["api_timeout"])
        if resp.json().get('status') == 'success':
            country_code = resp.json().get('countryCode', '').upper()
            if country_code:
                region_cache[ip] = {'region': country_code, 'timestamp': datetime.now().isoformat()}
                return country_code
    except:
        pass
    
    region_cache[ip] = {'region': 'Unknown', 'timestamp': datetime.now().isoformat()}
    return 'Unknown'

def get_country_name(code):
    return COUNTRY_MAPPING.get(code, code)

def format_ip_line(ip, port=443, country_code='Unknown'):
    """统一格式化输出: IP:端口#国家-☆灵鹿优选☆"""
    return f"{ip}:{port}#{country_code}-☆灵鹿优选☆"

# ===== 主程序 =====
def main():
    start_time = time.time()
    
    delete_file_if_exists('linglu-01.txt')
    delete_file_if_exists('linglu-02.txt')
    delete_file_if_exists('linglu-03.txt')
    delete_file_if_exists('linglu-04.txt')
    delete_file_if_exists('linglu-05.txt')
    
    logger.info("📥 开始采集IP地址...")
    all_ips = []
    successful_sources = 0
    
    for url in CONFIG["ip_sources"]:
        try:
            logger.info(f"🔍 从 {url} 采集...")
            time.sleep(CONFIG["query_interval"])
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            resp = session.get(url, timeout=CONFIG["timeout"], headers=headers)
            
            if resp.status_code == 200:
                ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', resp.text)
                valid_ips = [ip for ip in ips if all(0 <= int(p) <= 255 for p in ip.split('.'))]
                
                if valid_ips:
                    all_ips.extend(valid_ips)
                    successful_sources += 1
                    logger.info(f"✅ 从 {url} 采集 {len(valid_ips)} 个IP")
                else:
                    logger.warning(f"⚠️ {url} 未找到有效IP")
            else:
                logger.warning(f"⚠️ {url} 返回状态码: {resp.status_code}")
        except Exception as e:
            logger.error(f"❌ {url} 采集失败: {str(e)[:50]}")
    
    logger.info(f"📊 采集统计: 成功 {successful_sources} 个源，总计 {len(all_ips)} 个IP")
    
    unique_ips = sorted(list(set(all_ips)), key=lambda x: [int(p) for p in x.split('.')])
    logger.info(f"🔢 去重后 {len(unique_ips)} 个IP")
    
    if not unique_ips:
        logger.error("⚠️ 无IP地址，程序结束")
        return
    
    logger.info("🔍 快速筛选可用IP...")
    filtered_ips = []
    total = len(unique_ips)
    
    for i, ip in enumerate(unique_ips, 1):
        if i % 10 == 0:
            logger.info(f"📊 筛选进度: {i}/{total}")
        is_good, delay = test_ip_availability(ip)
        if is_good:
            filtered_ips.append(ip)
            logger.info(f"✅ 可用IP: {ip} (延迟: {delay}ms)")
    
    logger.info(f"🔍 快速筛选完成，保留 {len(filtered_ips)} 个可用IP")
    
    if not filtered_ips:
        logger.warning("⚠️ 无可用IP，程序结束")
        return
    
    logger.info("🌍 开始地区识别...")
    region_results = []
    for ip in filtered_ips:
        region_code = get_ip_region(ip)
        region_results.append((ip, region_code, 0, 0))
    
    logger.info("📄 生成基础文件...")
    
    # linglu-04.txt (纯IP)
    with open('linglu-04.txt', 'w', encoding='utf-8') as f:
        for ip in filtered_ips:
            f.write(f"{ip}\n")
    
    # linglu-01.txt (统一格式: IP:443#国家-☆灵鹿优选☆)
    with open('linglu-01.txt', 'w', encoding='utf-8') as f:
        for ip, region_code, _, _ in region_results:
            f.write(format_ip_line(ip, 443, region_code) + "\n")
    
    logger.info(f"📄 保存 {len(filtered_ips)} 个IP到 linglu-04.txt")
    logger.info(f"📄 保存 {len(region_results)} 条记录到 linglu-01.txt")
    
    if CONFIG["advanced_mode"]:
        logger.info("🔍 TCP Ping测试（深度检测）...")
        tcp_results = test_ips_concurrently(filtered_ips)
        logger.info(f"📡 TCP测试完成，可用 {len(tcp_results)} 个IP")
        
        if tcp_results:
            logger.info("📄 生成高级文件...")
            pro_region_results = []
            for ip, delay in tcp_results:
                region_code = get_ip_region(ip)
                pro_region_results.append((ip, region_code, delay))
            
            # linglu-05.txt (纯IP)
            with open('linglu-05.txt', 'w', encoding='utf-8') as f:
                for ip, _, _ in pro_region_results:
                    f.write(f"{ip}\n")
            
            # linglu-02.txt (统一格式: IP:443#国家-☆灵鹿优选☆)
            with open('linglu-02.txt', 'w', encoding='utf-8') as f:
                for ip, region_code, delay in pro_region_results:
                    f.write(format_ip_line(ip, 443, region_code) + "\n")
            
            # linglu-03.txt (按延迟排序，无编号)
            sorted_results = sorted(pro_region_results, key=lambda x: x[2])
            with open('linglu-03.txt', 'w', encoding='utf-8') as f:
                for ip, region_code, delay in sorted_results:
                    f.write(f"{format_ip_line(ip, 443, region_code)} (延迟: {delay}ms)\n")
            
            logger.info(f"📄 保存 {len(pro_region_results)} 个优选IP")
    
    save_region_cache()
    logger.info(f"⏱️ 总耗时: {round(time.time() - start_time, 2)}秒")
    logger.info("🏁 程序完成")

# ===== 程序入口 =====
if __name__ == "__main__":
    load_region_cache()
    clean_expired_cache()
    try:
        main()
    except KeyboardInterrupt:
        logger.info("⏹️ 程序被中断")
    except Exception as e:
        logger.error(f"❌ 程序出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
