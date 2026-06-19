def main():
    start_time = time.time()
    
    delete_file_if_exists('linglu-01.txt')
    delete_file_if_exists('linglu-02.txt')
    delete_file_if_exists('linglu-03.txt')
    delete_file_if_exists('linglu-04.txt')
    delete_file_if_exists('linglu-05.txt')
    
    logger.info("📥 开始采集IP地址...")
    all_ips = []
    successful_sources = 0
    
    # ... 采集和筛选代码保持不变 ...
    
    # 快速筛选后
    logger.info(f"🔍 快速筛选完成，保留 {len(filtered_ips)} 个可用IP")
    
    if not filtered_ips:
        logger.warning("⚠️ 无可用IP，程序结束")
        return
    
    # 地区识别
    logger.info("🌍 开始地区识别...")
    region_results = []
    for ip in filtered_ips:
        region_code = get_ip_region(ip)
        region_results.append((ip, region_code, 0, 0))
    
    # 生成基础文件
    logger.info("📄 生成基础文件...")
    
    # linglu-04.txt (纯IP)
    with open('linglu-04.txt', 'w', encoding='utf-8') as f:
        for ip in filtered_ips:
            f.write(f"{ip}\n")
    
    # linglu-01.txt (格式化)
    with open('linglu-01.txt', 'w', encoding='utf-8') as f:
        for ip, region_code, _, _ in region_results:
            f.write(format_ip_line(ip, 443, region_code) + "\n")
    
    logger.info(f"📄 保存 {len(filtered_ips)} 个IP到 linglu-04.txt")
    logger.info(f"📄 保存 {len(region_results)} 条记录到 linglu-01.txt")
    
    # ===== 高级模式 - 始终生成所有文件 =====
    logger.info("🔍 TCP Ping测试（深度检测）...")
    tcp_results = test_ips_concurrently(filtered_ips)
    logger.info(f"📡 TCP测试完成，可用 {len(tcp_results)} 个IP")
    
    # 使用 TCP 结果，如果为空则使用 filtered_ips 备选
    if tcp_results:
        pro_region_results = []
        for ip, delay in tcp_results:
            region_code = get_ip_region(ip)
            pro_region_results.append((ip, region_code, delay))
    else:
        logger.warning("⚠️ TCP测试无结果，使用快速筛选结果（前100个）")
        pro_region_results = []
        for ip in filtered_ips[:100]:
            region_code = get_ip_region(ip)
            pro_region_results.append((ip, region_code, 0))
    
    # linglu-05.txt (纯IP)
    with open('linglu-05.txt', 'w', encoding='utf-8') as f:
        for ip, _, _ in pro_region_results:
            f.write(f"{ip}\n")
    
    # linglu-02.txt (格式化)
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
