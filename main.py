import requests
import concurrent.futures
import re
import time
from pathlib import Path

SOURCE_URL = "https://zip.cm.edu.kg/all.txt"
TIMEOUT = 3
MAX_WORKERS = 100

def download_source():
    try:
        r = requests.get(SOURCE_URL, timeout=15)
        r.raise_for_status()
        print(f"Downloaded {len(r.text)} bytes")
        return r.text
    except Exception as e:
        print(f"Download failed: {e}")
        raise

def extract_and_format_lines(text):
    """
    从每行提取 IP、端口和国家代码，生成标准格式：
    IP:端口#国家-☆灵鹿优选☆
    """
    lines = []
    pattern = re.compile(r'^((?:\d{1,3}\.){3}\d{1,3})(?::(\d+))?#([A-Za-z0-9]+)')
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if m:
            ip = m.group(1)
            port = m.group(2) if m.group(2) else '80'
            country = m.group(3)
            new_line = f"{ip}:{port}#{country}-☆灵鹿优选☆"
            lines.append(new_line)
        else:
            print(f"Skipping invalid line: {line[:50]}")
    return lines

def test_ip_with_speed(line):
    """测试连通性并返回 (line, delay) 或 None"""
    try:
        addr = line.split('#')[0]  # IP:端口
        ip, port = addr.split(':') if ':' in addr else (addr, '80')
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
        key = line.split('#')[0]
        if key not in seen:
            seen.add(key)
            unique_lines.append(line)

    print(f"After dedupe: {len(unique_lines)}")

    # 并发测试并记录速度
    print("Testing connectivity and measuring speed...")
    results = []  # 存放 (line, delay) 元组

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(test_ip_with_speed, line) for line in unique_lines]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res:
                results.append(res)

    print(f"Valid IPs after testing: {len(results)}")

    if not results:
        raise RuntimeError("No valid IPs found")

    # 按延迟排序（从小到大）
    results.sort(key=lambda x: x[1])
    sorted_lines = [line for line, _ in results]

    # 保存所有有效IP到 all.txt
    Path("all.txt").write_text("\n".join(sorted_lines), encoding="utf-8")
    print(f"Saved all {len(sorted_lines)} entries to all.txt")

    # 保存最快100和300
    fastest_100 = sorted_lines[:100] if len(sorted_lines) >= 100 else sorted_lines
    fastest_300 = sorted_lines[:300] if len(sorted_lines) >= 300 else sorted_lines

    Path("fastest100.txt").write_text("\n".join(fastest_100), encoding="utf-8")
    Path("fastest300.txt").write_text("\n".join(fastest_300), encoding="utf-8")
    print(f"Saved {len(fastest_100)} fastest IPs to fastest100.txt")
    print(f"Saved {len(fastest_300)} fastest IPs to fastest300.txt")

if __name__ == "__main__":
    main()
