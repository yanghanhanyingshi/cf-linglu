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
        raise

def extract_ips(text):
    ips = []
    # 匹配 IP:端口（端口可选），忽略 # 后的任何内容
    pattern = re.compile(r'^((?:\d{1,3}\.){3}\d{1,3})(?::(\d+))?(?:#.*)?$')
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if m:
            ip = m.group(1)
            port = m.group(2) if m.group(2) else ''
            if port:
                ips.append(f"{ip}:{port}")
            else:
                ips.append(ip)
        else:
            print(f"Skipping invalid line: {line[:50]}")
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
        raise RuntimeError("No IPs extracted, check source format")

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
