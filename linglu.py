import time
import logging
import sys

# 配置日志（若已有全局 logger，可省略）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linglu.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 若您的项目已有这些函数，请确保它们已定义；否则请实现它们
# 以下是占位函数（仅用于演示，实际需替换为您的真实实现）
def delete_file_if_exists(filename):
    import os
    if os.path.exists(filename):
        os.remove(filename)

def get_ip_region(ip):
    # 示例：返回 "CN" 或 "US" 等
    return "CN"

def format_ip_line(ip, port, region):
    # 示例：返回 "ip:port#region"
    return f"{ip}:{port}#{region}"

def test_ips_concurrently(ips):
    # 示例：返回 [(ip, delay), ...]
    return [(ip, 100) for ip in ips[:50]]  # 模拟测试

def save_region_cache():
    # 示例：保存缓存
    pass

def main():
    start_time = time.time()
    try:
        # 删除旧文件
        for i in range(1, 6):
            delete_file_if_exists(f'linglu-{i:02d}.txt')
        
        logger.info("📥 开始采集IP地址...")
        # 注意：以下变量需来自您的实际采集逻辑，此处仅为示意
        # all_ips = collect_ips()  # 您需要实现采集
        # filtered_ips = filter_ips(all_ips)  # 您需要实现筛选
        # 为演示，构造假数据
        filtered_ips = ["192.168.1.1", "8.8.8.8", "1.1.1.1"]
        
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
        
        with open('linglu-04.txt', 'w', encoding='utf-8') as f:
            for ip in filtered_ips:
                f.write(f"{ip}\n")
        
        with open('linglu-01.txt', 'w', encoding='utf-8') as f:
            for ip, region_code, _, _ in region_results:
                f.write(format_ip_line(ip, 443, region_code) + "\n")
        
        logger.info(f"📄 保存 {len(filtered_ips)} 个IP到 linglu-04.txt")
        logger.info(f"📄 保存 {len(region_results)} 条记录到 linglu-01.txt")
        
        # ===== 高级模式 - 始终生成所有文件 =====
        logger.info("🔍 TCP Ping测试（深度检测）...")
        tcp_results = test_ips_concurrently(filtered_ips)
        logger.info(f"📡 TCP测试完成，可用 {len(tcp_results)} 个IP")
        
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
        
    except Exception as e:
        logger.error(f"❌ 程序运行出错: {e}", exc_info=True)
        # 即使出错，也确保至少生成空文件，避免后续步骤失败
        for i in range(1, 6):
            filename = f'linglu-{i:02d}.txt'
            if not os.path.exists(filename):
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("")  # 生成空文件
        sys.exit(1)  # 非正常退出，让 Workflow 知道失败

if __name__ == "__main__":
    main()
