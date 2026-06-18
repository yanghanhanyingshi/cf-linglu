import requests
import concurrent.futures
import re
import time
import json
from pathlib import Path

SOURCE_URL = "https://vps789.com/public/sum/cfIpApi"
TIMEOUT = 3
MAX_WORKERS = 100

def download_source():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        r = requests.get(SOURCE_URL, timeout=15, headers=headers)
        r.raise_for_status()
        print(f"Downloaded {len(r.text)} bytes")
        return r.text
    except Exception as e:
        print(f"Download failed: {e}")
        raise

def extract_ips_from_json(text):
    """
    从 JSON 响应中递归提取所有形如 IP:端口 的字符串
    忽略非 IP 内容
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        print("Response is not JSON, fallback to line-by-line")
        return extract_ips_from_text(text)

    # 将 JSON 转换为字符串，然后正则匹配所有 IP:端口
    json_str = json.dumps(data)
    # 匹配 IP:端口 或纯 IP（端口可选）
    pattern = re.compile(r'((?:\d{1,3}\.){3}\d{1,3})(?::(\d+))?')
    matches = pattern.findall(json_str)
    ips = []
    for ip, port in matches:
        port = port if port else '80'
        ips.append(f"{ip}:{port}")
    return ips

def extract_ips_from_text(text):
    """备用：按行提取（如果非 JSON）"""
    lines = []
    pattern = re.compile(r'^((?:\d{1,3}\.){3}\d{1,3})(?::(\d+))?')
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if m:
            ip = m.group(1)
            port = m.group(2) if m.group(2) else '80'
            lines.append(f"{ip}:{port}")
    return lines

def test_ip_with_speed(line):
    """测试连通性，返回 (line, delay)"""
    try:
        # 从行中提取 IP 和端口（格式 IP:端口）
        addr = line.split('-')[0]  # 去掉可能的后缀
        ip, port = addr.split(':')
        port = int(port)
        url = f"http://{ip}:{port}"
        start = time.perf_counter()
        requests.get(url, timeout=TIMEOUT)
        elapsed = time.perf_counter() - start
        return (line, elapsed)
    except:
        return None

def main():
    print("Downloading...")
    raw = download_source()

    print("Extracting IP:port from JSON...")
    raw_ips = extract_ips_from_json(raw)
    print(f"Extracted {len(raw_ips)} IP:port entries")

    if not raw_ips:
        raise RuntimeError("No IPs extracted, check source format")

    # 去重
    seen = set()
    unique_ips = []
    for ip_port in raw_ips:
        if ip_port not in seen:
            seen.add(ip_port)
            unique_ips.append(ip_port)

    print(f"After dedupe: {len(unique_ips)}")

    # 添加后缀 -☆灵鹿优选☆
    formatted_lines = [f"{ip_port}-☆灵鹿优选☆" for ip_port in unique_ips]

    # 并发测试速度
    print("Testing connectivity and measuring speed...")
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(test_ip_with_speed, line) for line in formatted_lines]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res:
                results.append(res)

    print(f"Valid IPs after testing: {len(results)}")

    if not results:
        raise RuntimeError("No valid IPs found")

    # 按速度排序
    results.sort(key=lambda x: x[1])
    sorted_lines = [line for line, _ in results]

    # 保存到 vps789.txt
    Path("vps789.txt").write_text("\n".join(sorted_lines), encoding="utf-8")
    print(f"Saved {len(sorted_lines)} entries to vps789.txt")

if __name__ == "__main__":
    main()
