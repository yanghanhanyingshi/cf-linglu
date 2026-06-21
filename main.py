import requests
import concurrent.futures
import re
import time
from pathlib import Path

# 定义三个数据源
SOURCE_URLS = [
    "https://zip.cm.edu.kg/all.txt",
    "https://bestcf.pages.dev/WARP/WARP-MASQUE-IPs-443.txt",
    "https://countrymerge.pages.dev/all.txt"
]
TIMEOUT = 3
MAX_WORKERS = 100

def download_source(url):
    """下载单个URL的内容"""
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        print(f"Downloaded {len(r.text)} bytes from {url}")
        return r.text
    except Exception as e:
        print(f"Download failed for {url}: {e}")
        return ""

def extract_and_format_lines(text):
    """
    从每行提取 IP、端口和国家代码，生成标准格式：
    IP:端口#国家-☆灵鹿优选☆
    支持三种格式：
      1. IP:端口#国家
      2. IP:端口
      3. IP（无端口，默认80）
    若无国家代码则使用 'XX'
    """
    lines = []
    # 匹配IP地址（IPv4）
    ip_pattern = re.compile(r'\b((?:\d{1,3}\.){3}\d{1,3})\b')
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # 尝试提取国家代码（如果有#）
        country = "XX"
        if '#' in line:
            parts = line.split('#', 1)
            ip_port_part = parts[0].strip()
            country_candidate = parts[1].strip()
            if country_candidate:
                # 只取字母数字，可能还有短横线等，但简单取第一个单词
                m = re.match(r'^([A-Za-z0-9]+)', country_candidate)
                if m:
                    country = m.group(1)
                else:
                    country = "XX"
            line = ip_port_part  # 去掉#及后面的部分，后续只处理IP和端口
        else:
            ip_port_part = line

        # 提取IP
        ip_match = ip_pattern.search(ip_port_part)
        if not ip_match:
            print(f"Skipping line (no IP): {raw_line[:50]}")
            continue
        ip = ip_match.group(1)

        # 提取端口
        port = "80"
        # 检查是否有冒号后接数字（端口）
        port_match = re.search(r':(\d+)$', ip_port_part)
        if port_match:
            port = port_match.group(1)

        new_line = f"{ip}:{port}#{country}-☆灵鹿优选☆"
        lines.append(new_line)

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
    print("Downloading from all sources...")
    all_text = ""
    for url in SOURCE_URLS:
        content = download_source(url)
        if content:
            all_text += content + "\n"  # 确保换行分隔

    if not all_text.strip():
        raise RuntimeError("No data downloaded from any source.")

    print("Parsing and formatting...")
    formatted_lines = extract_and_format_lines(all_text)
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
