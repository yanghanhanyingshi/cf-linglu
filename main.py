import requests
import concurrent.futures
import re
from pathlib import Path

SOURCE_URL = "https://zip.cm.edu.kg/all.txt"

TIMEOUT = 3
MAX_WORKERS = 100


def download_source():
    r = requests.get(SOURCE_URL, timeout=15)
    r.raise_for_status()
    return r.text


def extract_ips(text):
    ips = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        if re.search(r'((?:\d{1,3}\.){3}\d{1,3})(?::(\d+))?', line):
            ips.append(line)

    return ips


def test_ip(item):
    try:
        m = re.search(r'((?:\d{1,3}\.){3}\d{1,3})', item)
        if not m:
            return None

        ip = m.group(1)
        url = f"http://{ip}"

        requests.get(url, timeout=TIMEOUT)
        return item

    except:
        return None


def main():
    print("Downloading...")
    raw = download_source()

    print("Parsing...")
    ips = extract_ips(raw)

    print("Total:", len(ips))

    ips = list(dict.fromkeys(ips))

    print("After dedupe:", len(ips))

    valid = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(test_ip, ip) for ip in ips]

        for f in concurrent.futures.as_completed(futures):
            r = f.result()
            if r:
                valid.append(r)

    valid = sorted(set(valid))

    Path("all.txt").write_text("\n".join(valid), encoding="utf-8")

    print("Saved:", len(valid))


if __name__ == "__main__":
    main()
