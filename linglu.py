# ===== 主程序 =====
def main():
    start_time = time.time()
    
    delete_file_if_exists('linglu-01.txt')
    delete_file_if_exists('linglu-02.txt')
    delete_file_if_exists('linglu-03.txt')
    delete_file_if_exists('linglu-04.txt')
    delete_file_if_exists('linglu-05.txt')
    
    logger.info("📥 采集IP地址...")
    all_ips = []
    for url in CONFIG["ip_sources"]:
        try:
            logger.info(f"🔍 从 {url} 采集...")
            time.sleep(CONFIG["query_interval"])
            resp = session.get(url, timeout=CONFIG["timeout"])
            if resp.status_code == 200:
                ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', resp.text)
                valid_ips = [ip for ip in ips if all(0 <= int(p) <= 255 for p in ip.split('.'))]
                all_ips.extend(valid_ips)
                logger.info(f"✅ 采集 {len(valid_ips)} 个IP")
        except Exception as e:
            logger.error(f"❌ 采集失败: {str(e)[:50]}")
    
    unique_ips = sorted(list(set(all_ips)), key=lambda x: [int(p) for p in x.split('.')])
    logger.info(f"🔢 去重后 {len(unique_ips)} 个IP")
    
    if not unique_ips:
        logger.warning("⚠️ 无IP地址，程序结束")
        return
    
    logger.info("🔍 快速筛选...")
    filtered_ips = []
    for ip in unique_ips:
        is_good, delay = test_ip_availability(ip)
        if is_good:
            filtered_ips.append(ip)
    
    logger.info(f"🔍 保留 {len(filtered_ips)} 个IP")
    
    if not filtered_ips:
        logger.warning("⚠️ 无可用IP，程序结束")
        return
    
    logger.info("🌍 地区识别...")
    region_results = []
    for ip in filtered_ips:
        region_code = get_ip_region(ip)
        region_results.append((ip, region_code, 0, 0))
    
    logger.info("📄 生成基础文件...")
    
    # linglu-04.txt (纯IP)
    with open('linglu-04.txt', 'w', encoding='utf-8') as f:
        for ip in filtered_ips:
            f.write(f"{ip}\n")
    
    # linglu-01.txt (统一格式: IP:443#国家-☆灵鹿优选☆)
    with open('linglu-01.txt', 'w', encoding='utf-8') as f:
        for ip, region_code, _, _ in region_results:
            f.write(format_ip_line(ip, 443, region_code) + "\n")
    
    logger.info(f"📄 保存 {len(filtered_ips)} 个IP到 linglu-04.txt")
    logger.info(f"📄 保存 {len(region_results)} 条记录到 linglu-01.txt")
    
    if CONFIG["advanced_mode"]:
        logger.info("🔍 TCP Ping测试...")
        tcp_results = test_ips_concurrently(filtered_ips)
        logger.info(f"📡 TCP测试完成，可用 {len(tcp_results)} 个IP")
        
        if tcp_results:
            logger.info("📄 生成高级文件...")
            pro_region_results = []
            for ip, delay in tcp_results:
                region_code = get_ip_region(ip)
                pro_region_results.append((ip, region_code, delay))
            
            # linglu-05.txt (纯IP)
            with open('linglu-05.txt', 'w', encoding='utf-8') as f:
                for ip, _, _ in pro_region_results:
                    f.write(f"{ip}\n")
            
            # linglu-02.txt (统一格式: IP:443#国家-☆灵鹿优选☆)
            with open('linglu-02.txt', 'w', encoding='utf-8') as f:
                for ip, region_code, delay in pro_region_results:
                    f.write(format_ip_line(ip, 443, region_code) + "\n")
            
            # linglu-03.txt (按延迟排序，无编号)
            sorted_results = sorted(pro_region_results, key=lambda x: x[2])
            with open('linglu-03.txt', 'w', encoding='utf-8') as f:
                for ip, region_code, delay in sorted_results:
                    f.write(f"{format_ip_line(ip, 443, region_code)} (延迟: {delay}ms)\n")
            
            logger.info(f"📄 保存 {len(pro_region_results)} 个优选IP")
    
    save_region_cache()
    logger.info(f"⏱️ 总耗时: {round(time.time() - start_time, 2)}秒")
    logger.info("🏁 程序完成")
