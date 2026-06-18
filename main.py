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

def extract_lines(text):
    """返回完整的原始行列表，每行必须是 IP:端口#... 格式（端口可选）"""
    lines = []
    # 匹配整行：IP:端口（可选）#任意内容
    pattern = re.compile(r'^((?:\d{1,3}\.){3}\d{1,3})(?::(\d+))?(#.*)?$')
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if pattern.match(line):
            lines.append(line)
        else:
            print(f"Skipping invalid line: {line[:50]}")
    return lines

def test_ip(line):
    """测试该行对应的 IP:端口 是否可达，成功返回原始行，否则返回 None"""
    try:
        # 提取 IP 和端口
        parts = line.split(':')
        ip = parts[0]
        # 端口可能被 # 截断，先取前两部分
        # 如果存在 #，则端口在 # 前面；否则只有 IP 和端口
        if '#' in line:
            port_part = line.split('#')[0].split(':')[-1]
        else:
            port_part = parts[1] if len(parts) > 1 else ''
        port = int(port_part) if port_part else 80
        url = f"http://{ip}:{port}"
        requests.get(url, timeout=TIMEOUT)
        return line
    except:
        return None

def main():
    print("Downloading...")
    raw = download_source()

    print("Parsing...")
    lines = extract_lines(raw)
    print(f"Extracted {len(lines)} lines")

    if not lines:
        raise RuntimeError("No valid lines extracted, check source format")

    # 去重：基于 IP:端口 保留第一次出现的完整行
    seen = set()
    unique_lines = []
    for line in lines:
        # 提取 IP:端口 作为 key（忽略 # 后的内容）
        if '#' in line:
            key = line.split('#')[0]  # 形如 IP:端口
        else:
            key = line  # 无 #，则整行
        if key not in seen:
            seen.add(key)
            unique_lines.append(line)

    print(f"After dedupe: {len(unique_lines)}")

    # 测试连通性
    valid = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(test_ip, line) for line in unique_lines]
        for f in concurrent.futures.as_completed(futures):
            r = f.result()
            if r:
                valid.append(r)

    print(f"Valid after testing: {len(valid)}")

    if not valid:
        raise RuntimeError("No valid IPs found")

    # 排序（按 IP 排序，可选）
    valid = sorted(set(valid))  # set 去重（理论上已无重复）
    Path("all.txt").write_text("\n".join(valid), encoding="utf-8")
    print(f"Saved {len(valid)} entries to all.txt")

if __name__ == "__main__":
    main()
