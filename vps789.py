import requests
import concurrent.futures
import re
import time
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

def extract_and_format_lines(text):
    """
    提取 IP 和端口，生成统一格式：IP:端口-☆灵鹿优选☆
    忽略原始行中的任何备注/国家信息
    """
    lines = []
    # 匹配 IP:端口 或纯 IP
    pattern = re.compile(r'^((?:\d{1,3}\.){3}\d{1,3})(?::(\d+))?')
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if m:
            ip = m.group(1)
            port = m.group(2) if m.group(2) else '80'
            new_line = f"{ip}:{port}-☆灵鹿优选☆"
            lines.append(new_line)
        else:
            print(f"Skipping invalid line: {line[:50]}")
    return lines

def test_ip_with_speed(line):
    """测试连通性并返回 (line, delay)"""
    try:
        # 从行中提取 IP 和端口（格式 IP:端口-...）
        addr = line.split('-')[0]  # 去掉后缀
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

    print("Parsing and formatting...")
    formatted_lines = extract_and_format_lines(raw)
    print(f"Extracted {len(formatted_lines)} lines")

    if not formatted_lines:
        raise RuntimeError("No valid lines extracted, check source format")

    # 去重：基于 IP:端口
    seen = set()
    unique_lines = []
    for line in formatted_lines:
        key = line.split('-')[0]  # IP:端口
        if key not in seen:
            seen.add(key)
            unique_lines.append(line)

    print(f"After dedupe: {len(unique_lines)}")

    # 并发测试并记录速度
    print("Testing connectivity and measuring speed...")
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(test_ip_with_speed, line) for line in unique_lines]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res:
                results.append(res)

    print(f"Valid IPs after testing: {len(results)}")

    if not results:
        raise RuntimeError("No valid IPs found")

    # 按延迟排序
    results.sort(key=lambda x: x[1])
    sorted_lines = [line for line, _ in results]

    # 保存到 vps789.txt
    Path("vps789.txt").write_text("\n".join(sorted_lines), encoding="utf-8")
    print(f"Saved {len(sorted_lines)} entries to vps789.txt")

if __name__ == "__main__":
    main()
