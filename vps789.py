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
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(SOURCE_URL, timeout=15, headers=headers)
        r.raise_for_status()
        print(f"Downloaded {len(r.text)} bytes")
        # 打印前 500 字符，便于调试
        print("Raw response preview:", r.text[:500])
        return r.text
    except Exception as e:
        print(f"Download failed: {e}")
        raise

def extract_ips_from_json(text):
    """
    从 JSON 响应中递归提取所有 IP:端口 字符串。
    如果 JSON 解析失败，回退到按行提取。
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        print("Response is not JSON, fallback to line-by-line")
        return extract_ips_from_text(text)

    # 将整个 JSON 转成字符串，然后用正则匹配所有 IP:端口
    json_str = json.dumps(data)
    pattern = re.compile(r'((?:\d{1,3}\.){3}\d{1,3})(?::(\d+))?')
    matches = pattern.findall(json_str)
    ips = []
    for ip, port in matches:
        port = port if port else '80'
        ips.append(f"{ip}:{port}")
    return ips

def extract_ips_from_text(text):
    """按行提取 IP:端口（备用）"""
    pattern = re.compile(r'^((?:\d{1,3}\.){3}\d{1,3})(?::(\d+))?')
    ips = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if m:
            ip = m.group(1)
            port = m.group(2) if m.group(2) else '80'
            ips.append(f"{ip}:{port}")
    return ips

def test_ip_with_speed(line):
    """测试连通性，返回 (line, delay) 或 None"""
    try:
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
        # 打印帮助信息
        print("No IPs found. Please check the API response preview above.")
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
