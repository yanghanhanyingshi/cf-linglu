import requests
import concurrent.futures
import re
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
        raise  # 让工作流失败

def extract_ips(text):
    ips = []
    # 兼容多种格式：纯IP、IP:端口、可能包含空格
    pattern = re.compile(r'^((?:\d{1,3}\.){3}\d{1,3})(?::(\d+))?$')
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if pattern.match(line):
            ips.append(line)
        else:
            print(f"Skipping invalid line: {line[:50]}")  # 打印部分内容供调试
    return ips

def test_ip(item):
    try:
        parts = item.split(':')
        ip = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 80
        url = f"http://{ip}:{port}"
        requests.get(url, timeout=TIMEOUT)
        return item
    except:
        return None

def main():
    print("Downloading...")
    raw = download_source()

    print("Parsing...")
    ips = extract_ips(raw)
    print(f"Extracted {len(ips)} IP entries")

    if not ips:
        raise RuntimeError("No IPs extracted from source")

    # 去重
    ips = list(dict.fromkeys(ips))
    print(f"After dedupe: {len(ips)}")

    valid = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(test_ip, ip) for ip in ips]
        for f in concurrent.futures.as_completed(futures):
            r = f.result()
            if r:
                valid.append(r)

    print(f"Valid IPs after testing: {len(valid)}")

    if not valid:
        raise RuntimeError("No valid IPs found")

    valid = sorted(set(valid))
    Path("all.txt").write_text("\n".join(valid), encoding="utf-8")
    print(f"Saved {len(valid)} IPs to all.txt")

if __name__ == "__main__":
    main()
