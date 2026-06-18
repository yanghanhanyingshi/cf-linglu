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

def extract_and_format_lines(text):
    """
    从每行提取 IP、端口和国家代码，生成标准格式：
    IP:端口#国家-☆灵鹿优选☆
    如果缺少端口则默认为 80，但通常都有。
    """
    lines = []
    # 匹配 IP:端口（可选）和国家代码（#后紧接着两个大写字母，或更长）
    # 国家代码可能包含连字符，但示例是 JP 等，我们取 # 后第一个连续非空白非 '-' 的字符串
    pattern = re.compile(r'^((?:\d{1,3}\.){3}\d{1,3})(?::(\d+))?#([A-Za-z0-9]+)')
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if m:
            ip = m.group(1)
            port = m.group(2) if m.group(2) else '80'
            country = m.group(3)  # 例如 JP, US, HK
            new_line = f"{ip}:{port}#{country}-☆灵鹿优选☆"
            lines.append(new_line)
        else:
            print(f"Skipping invalid line: {line[:50]}")
    return lines

def test_ip(line):
    """从标准行提取 IP 和端口进行连通性测试，成功返回原行"""
    try:
        # 提取 IP:端口（#之前的部分）
        addr = line.split('#')[0]  # 形如 IP:端口
        ip, port = addr.split(':') if ':' in addr else (addr, '80')
        port = int(port)
        url = f"http://{ip}:{port}"
        requests.get(url, timeout=TIMEOUT)
        return line
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

    # 去重：基于 IP:端口（#前部分）
    seen = set()
    unique_lines = []
    for line in formatted_lines:
        key = line.split('#')[0]  # IP:端口
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

    # 排序（按 IP 排序）
    valid = sorted(set(valid))
    Path("all.txt").write_text("\n".join(valid), encoding="utf-8")
    print(f"Saved {len(valid)} entries to all.txt")

if __name__ == "__main__":
    main()
