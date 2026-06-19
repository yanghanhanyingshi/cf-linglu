import pybase64
import base64
import requests
import binascii
import os
import sys

# ===================== 全局配置 =====================
TIMEOUT = 15
OUTPUT_ROOT = "output"
BASE64_SUB_FOLDER = os.path.join(OUTPUT_ROOT, "Base64")

# 强制标题前缀（所有订阅文件都会加上）
TITLE_PREFIX = "☆灵鹿收集☆ "

# Base64解码（与原来相同）
def decode_base64(encoded):
    decoded = ""
    for encoding in ["utf-8", "iso-8859-1"]:
        try:
            pad_encoded = encoded + b"=" * (-len(encoded) % 4)
            decoded = pybase64.b64decode(pad_encoded).decode(encoding)
            break
        except (UnicodeDecodeError, binascii.Error, TypeError):
            continue
    return decoded

# 拉取base64订阅（不变）
def decode_links(links):
    decoded_data = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for link in links:
        try:
            resp = requests.get(link, timeout=TIMEOUT, headers=headers)
            resp.raise_for_status()
            decoded_text = decode_base64(resp.content)
            if decoded_text:
                decoded_data.append(decoded_text)
        except requests.RequestException as e:
            print(f"[跳过] 链接请求失败: {link}, 错误: {str(e)[:30]}")
            continue
    return decoded_data

# 拉取明文订阅（不变）
def decode_dir_links(dir_links):
    decoded_dir_links = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for link in dir_links:
        try:
            resp = requests.get(link, timeout=TIMEOUT, headers=headers)
            resp.raise_for_status()
            text = resp.text.strip()
            if text:
                decoded_dir_links.append(text)
        except requests.RequestException as e:
            print(f"[跳过] 明文链接失败: {link}, 错误: {str(e)[:30]}")
            continue
    return decoded_dir_links

# 协议过滤+去重（不变）
def filter_for_protocols(data, protocols):
    filtered_data = []
    seen_configs = set()
    for content in data:
        if not content or not content.strip():
            continue
        lines = content.strip().splitlines()
        for line in lines:
            line = line.strip()
            if line.startswith("#") or not line:
                filtered_data.append(line)
                continue
            if any(pro in line for pro in protocols):
                if line not in seen_configs:
                    filtered_data.append(line)
                    seen_configs.add(line)
    return filtered_data

# 创建目录（不变）
def ensure_directories_exist():
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    os.makedirs(BASE64_SUB_FOLDER, exist_ok=True)
    return OUTPUT_ROOT, BASE64_SUB_FOLDER

def main():
    print("===== GitHub Actions 订阅合并任务启动 =====")
    output_folder, base64_folder = ensure_directories_exist()

    # 清理旧文件
    print("\n[1/6] 清理历史旧文件")
    main_txt = os.path.join(output_folder, "All_Configs_Sub.txt")
    main_b64 = os.path.join(output_folder, "All_Configs_base64_Sub.txt")
    for old_file in [main_txt, main_b64]:
        if os.path.exists(old_file):
            os.remove(old_file)
    for i in range(1, 21):
        sub_file = os.path.join(output_folder, f"Sub{i}.txt")
        b64_sub = os.path.join(base64_folder, f"Sub{i}_base64.txt")
        for fpath in [sub_file, b64_sub]:
            if os.path.exists(fpath):
                os.remove(fpath)

    # 订阅源列表（不变）
    protocols = ["vmess", "vless", "trojan", "ss", "ssr", "hy2", "tuic", "warp://"]
    links = [
        "https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/refs/heads/main/app/sub.txt",
        "https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/refs/heads/main/mtn/sub_1.txt",
        "https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/refs/heads/main/mtn/sub_2.txt",
        "https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/refs/heads/main/mtn/sub_3.txt",
        "https://raw.githubusercontent.com/mahsanet/MahsaFreeConfig/refs/heads/main/mtn/sub_4.txt",
        "https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/splitted/mixed"
    ]
    dir_links = [
        "https://raw.githubusercontent.com/itsyebekhe/PSG/main/lite/subscriptions/xray/normal/mix",
        "https://raw.githubusercontent.com/arshiacomplus/v2rayExtractor/refs/heads/main/mix/sub.html",
        "https://raw.githubusercontent.com/Rayan-Config/C-Sub/refs/heads/main/configs/proxy.txt",
        "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/Eternity.txt",
        "https://raw.githubusercontent.com/Everyday-VPN/Everyday-VPN/main/subscription/main.txt",
        "https://raw.githubusercontent.com/MahsaNetConfigTopic/config/refs/heads/main/xray_final.txt",
    ]

    # 拉取解析
    print("\n[2/6] 拉取并解析Base64订阅源")
    decoded_links = decode_links(links)
    print(f"成功解析源数量：{len(decoded_links)}")
    print("\n[3/6] 拉取并解析明文订阅源")
    decoded_dir_links = decode_dir_links(dir_links)
    print(f"成功解析源数量：{len(decoded_dir_links)}")

    # 合并过滤
    print("\n[4/6] 合并协议并去重")
    combined = decoded_links + decoded_dir_links
    merged_configs = filter_for_protocols(combined, protocols)
    print(f"最终有效节点总数：{len(merged_configs)}")

    # ========== 生成汇总文件（标题强制加前缀） ==========
    print("\n[5/6] 生成汇总订阅文件")
    # 汇总标题
    main_title = TITLE_PREFIX + "GitHub | Barry-far"
    b64_main_title = base64.b64encode(main_title.encode()).decode()
    fixed_text = f"""#profile-title: base64:{b64_main_title}
#profile-update-interval: 1
#subscription-userinfo: upload=29; download=12; total=10737418240000000; expire=2546249531
#support-url: https://github.com/barry-far/V2ray-config
#profile-web-page-url: https://github.com/barry-far/V2ray-config
"""
    with open(main_txt, "w", encoding="utf-8") as f:
        f.write(fixed_text)
        for cfg in merged_configs:
            f.write(cfg + "\n")

    # Base64 汇总
    with open(main_txt, "r", encoding="utf-8") as f:
        raw_data = f.read()
    b64_encode_data = base64.b64encode(raw_data.encode("utf-8")).decode()
    with open(main_b64, "w", encoding="utf-8") as f:
        f.write(b64_encode_data)

    # ========== 分片拆分（标题强制加前缀） ==========
    print("\n[6/6] 拆分多分片订阅文件")
    with open(main_txt, "r", encoding="utf-8") as f:
        all_lines = f.readlines()
    total_lines = len(all_lines)
    max_per_file = 500
    file_count = (total_lines + max_per_file - 1) // max_per_file
    print(f"共计拆分 {file_count} 个分片文件")

    for idx in range(file_count):
        file_num = idx + 1
        # 分片标题：前缀 + 原有内容
        split_title = TITLE_PREFIX + f"🆓 Git:barry-far | Sub{file_num} 🔥"
        b64_split_title = base64.b64encode(split_title.encode()).decode()
        split_header = f"""#profile-title: base64:{b64_split_title}
#profile-update-interval: 1
#subscription-userinfo: upload=29; download=12; total=10737418240000000; expire=2546249531
#support-url: https://github.com/barry-far/V2ray-config
#profile-web-page-url: https://github.com/barry-far/V2ray-config
"""
        split_txt_path = os.path.join(output_folder, f"Sub{file_num}.txt")
        start = idx * max_per_file
        end = start + max_per_file
        slice_lines = all_lines[start:end]
        with open(split_txt_path, "w", encoding="utf-8") as f:
            f.write(split_header)
            f.writelines(slice_lines)

        # 分片 Base64
        with open(split_txt_path, "r", encoding="utf-8") as f:
            slice_raw = f.read()
        slice_b64 = base64.b64encode(slice_raw.encode()).decode()
        split_b64_path = os.path.join(base64_folder, f"Sub{file_num}_base64.txt")
        with open(split_b64_path, "w", encoding="utf-8") as f:
            f.write(slice_b64)
        print(f"✅ 完成分片：Sub{file_num}.txt")

    print("\n==================== 任务全部完成 ====================")
    print(f"输出目录：{os.path.abspath(OUTPUT_ROOT)}")
    print(f"有效节点数：{len(merged_configs)}")
    print("汇总文件、分片文件、Base64文件已全部生成（标题均含 ☆灵鹿收集☆）")

if __name__ == "__main__":
    main()
