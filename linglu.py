# ===== 核心配置 =====
CONFIG = {
    "ip_sources": [
        # ✅ 已验证可用的源
        'https://api.uouin.com/cloudflare.html',
        'https://api.urlce.com/cloudflare.html',
        'https://addressesapi.090227.xyz/CloudFlareYes',
        'https://cf.090227.xyz/CloudFlareYes',
        'https://stock.hostmonit.com/CloudFlareYes',
        'https://vps789.com/openApi/cfIpTop20',
        'https://vps789.com/openApi/cfIpApi',
        'https://www.wetest.vip/page/cloudflare/total_v4.html',
        'https://www.wetest.vip/page/cloudflare/address_v4.html',
        'https://cf.090227.xyz/cmcc',
        'https://cf.090227.xyz/ct',
        # ✅ 备用源
        'https://raw.githubusercontent.com/ymyuuu/IPDB/main/BestCF/bestcfv4.txt',
        'https://ipdb.api.030101.xyz/?type=bestcf&country=true',
    ],
    
    # 🔍 网络测试配置 - 增加多个端口
    "test_ports": [443, 2052, 2053, 2082, 2083, 2086, 2087, 2095, 2096, 8443, 8444],
    "timeout": 10,                          # 采集超时时间（秒）
    "api_timeout": 5,                       # API查询超时时间（秒）
    "query_interval": 0.2,                 # API查询间隔时间（秒）
    
    # ⚡ 并发处理配置
    "max_workers": 20,                      # 最大并发线程数
    "batch_size": 15,                      # 批量处理IP数量
    "cache_ttl_hours": 168,                # 缓存有效期（7天）
    
    # 🚀 高级功能配置
    "advanced_mode": True,                  # 高级模式开关
    "bandwidth_test_count": 3,
    "bandwidth_test_size_mb": 10,
    "latency_filter_percentage": 30,
}

# ===== 快速筛选函数（增强版）=====
def test_ip_availability(ip):
    """
    TCP Socket检测IP可用性 - 支持多端口自定义
    增加连接超时和重试机制
    """
    try:
        parts = ip.split('.')
        if len(parts) != 4 or not all(0 <= int(p) <= 255 for p in parts):
            return (False, 0)
    except:
        return (False, 0)
    
    min_delay = float('inf')
    success_count = 0
    
    # 遍历配置的测试端口
    for port in CONFIG["test_ports"]:
        try:
            if not isinstance(port, int) or not (1 <= port <= 65535):
                continue
                
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)  # 增加超时到5秒
                start_time = time.time()
                
                # 尝试TCP连接
                if s.connect_ex((ip, port)) == 0:
                    delay = round((time.time() - start_time) * 1000)
                    min_delay = min(min_delay, delay)
                    success_count += 1
                    
                    # 如果延迟很好，立即返回最佳结果
                    if delay < 300:  # 放宽到300ms
                        return (True, delay)
        except (socket.timeout, socket.error, OSError):
            continue
        except Exception:
            continue
    
    # 返回最佳结果
    if success_count > 0:
        return (True, min_delay)
    
    return (False, 0)

# ===== 采集函数（增加详细日志和容错）=====
def main():
    start_time = time.time()
    
    # 清理旧文件
    delete_file_if_exists('linglu-01.txt')
    delete_file_if_exists('linglu-02.txt')
    delete_file_if_exists('linglu-03.txt')
    delete_file_if_exists('linglu-04.txt')
    delete_file_if_exists('linglu-05.txt')
    
    logger.info("📥 开始采集IP地址...")
    all_ips = []
    successful_sources = 0
    
    for url in CONFIG["ip_sources"]:
        try:
            logger.info(f"🔍 从 {url} 采集...")
            time.sleep(CONFIG["query_interval"])
            
            # 增加请求头模拟浏览器
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            resp = session.get(url, timeout=CONFIG["timeout"], headers=headers)
            
            if resp.status_code == 200:
                # 提取所有IPv4地址
                ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', resp.text)
                valid_ips = [ip for ip in ips if all(0 <= int(p) <= 255 for p in ip.split('.'))]
                
                if valid_ips:
                    all_ips.extend(valid_ips)
                    successful_sources += 1
                    logger.info(f"✅ 从 {url} 采集 {len(valid_ips)} 个IP")
                else:
                    logger.warning(f"⚠️ {url} 未找到有效IP")
            else:
                logger.warning(f"⚠️ {url} 返回状态码: {resp.status_code}")
        except Exception as e:
            logger.error(f"❌ {url} 采集失败: {str(e)[:50]}")
    
    logger.info(f"📊 采集统计: 成功 {successful_sources} 个源，总计 {len(all_ips)} 个IP")
    
    # 去重并排序
    unique_ips = sorted(list(set(all_ips)), key=lambda x: [int(p) for p in x.split('.')])
    logger.info(f"🔢 去重后 {len(unique_ips)} 个IP")
    
    if not unique_ips:
        logger.error("⚠️ 无IP地址，程序结束")
        logger.error("请检查网络连接或IP源是否可访问")
        return
    
    # 快速筛选
    logger.info("🔍 快速筛选可用IP...")
    filtered_ips = []
    total = len(unique_ips)
    
    for i, ip in enumerate(unique_ips, 1):
        if i % 10 == 0:  # 每10个输出进度
            logger.info(f"📊 筛选进度: {i}/{total}")
        is_good, delay = test_ip_availability(ip)
        if is_good:
            filtered_ips.append(ip)
            logger.info(f"✅ 可用IP: {ip} (延迟: {delay}ms)")
    
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
    
    # 保存基础文件
    logger.info("📄 生成基础文件...")
    
    with open('linglu-04.txt', 'w', encoding='utf-8') as f:
        for ip in filtered_ips:
            f.write(f"{ip}\n")
    
    with open('linglu-01.txt', 'w', encoding='utf-8') as f:
        for ip, region_code, _, _ in region_results:
            f.write(format_ip_line(ip, 443, region_code) + "\n")
    
    logger.info(f"📄 保存 {len(filtered_ips)} 个IP到 linglu-04.txt")
    logger.info(f"📄 保存 {len(region_results)} 条记录到 linglu-01.txt")
    
    # 高级模式
    if CONFIG["advanced_mode"]:
        logger.info("🔍 TCP Ping测试（深度检测）...")
        tcp_results = test_ips_concurrently(filtered_ips)
        logger.info(f"📡 TCP测试完成，可用 {len(tcp_results)} 个IP")
        
        if tcp_results:
            logger.info("📄 生成高级文件...")
            pro_region_results = []
            for ip, delay in tcp_results:
                region_code = get_ip_region(ip)
                pro_region_results.append((ip, region_code, delay))
            
            with open('linglu-05.txt', 'w', encoding='utf-8') as f:
                for ip, _, _ in pro_region_results:
                    f.write(f"{ip}\n")
            
            with open('linglu-02.txt', 'w', encoding='utf-8') as f:
                for ip, region_code, delay in pro_region_results:
                    f.write(format_ip_line(ip, 443, region_code) + "\n")
            
            sorted_results = sorted(pro_region_results, key=lambda x: x[2])
            with open('linglu-03.txt', 'w', encoding='utf-8') as f:
                for ip, region_code, delay in sorted_results:
                    f.write(f"{format_ip_line(ip, 443, region_code)} (延迟: {delay}ms)\n")
            
            logger.info(f"📄 保存 {len(pro_region_results)} 个优选IP")
    
    save_region_cache()
    logger.info(f"⏱️ 总耗时: {round(time.time() - start_time, 2)}秒")
    logger.info("🏁 程序完成")

# ===== 程序入口 =====
if __name__ == "__main__":
    load_region_cache()
    clean_expired_cache()
    try:
        main()
    except KeyboardInterrupt:
        logger.info("⏹️ 程序被中断")
    except Exception as e:
        logger.error(f"❌ 程序出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
