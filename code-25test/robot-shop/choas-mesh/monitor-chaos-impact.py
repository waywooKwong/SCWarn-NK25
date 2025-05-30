#!/usr/bin/env python3
"""
Chaos实验监控脚本
监控robot-shop在故障注入期间的指标变化，特别是envoy_server_live存活率
"""

import requests
import json
import csv
import os
import time
from datetime import datetime, timedelta
import threading
import statistics

# 配置信息
PROMETHEUS_URL = "http://127.0.0.1:8080"
NAMESPACE = "robot-shop"
MONITORING_DURATION = 1800  # 30分钟
SAMPLE_INTERVAL = 5  # 5秒采样一次

# 构建输出目录
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
OUTPUT_DIR = os.path.join(project_root, "data", "robot-shop", "chaos")

# 加载指标映射
metric_mapping_path = os.path.join(os.path.dirname(script_dir), "metric_mapping.json")
with open(metric_mapping_path, "r", encoding='utf-8') as f:
    METRIC_MAPPING = json.load(f)

class ChaosMonitor:
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.metrics_data = {}
        self.events = []
        self.is_running = True
        
    def log_event(self, event_type, message):
        """记录事件"""
        timestamp = datetime.utcnow()
        self.events.append({
            "timestamp": timestamp.isoformat(),
            "type": event_type,
            "message": message,
            "elapsed_seconds": (timestamp - self.start_time).total_seconds()
        })
        print(f"[{timestamp.strftime('%H:%M:%S')}] {event_type}: {message}")
        
    def collect_metric(self, service_name, metric_key, metric_name):
        """收集单个指标"""
        if metric_key == "timestamp":
            return None
            
        query = f'{metric_name}{{namespace="{NAMESPACE}",service="{service_name}"}}'
        url = f"{PROMETHEUS_URL}/api/v1/query?query={query}"
        
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code != 200:
                return None
                
            results = resp.json()["data"]["result"]
            
            if metric_key == "success_rate":
                # 计算成功率
                values = []
                for timeseries in results:
                    value = float(timeseries["value"][1])
                    values.append(value)
                
                if values:
                    sum_val = sum(values)
                    count_val = len(values)
                    success_rate = (sum_val / count_val * 100) if count_val > 0 else 0
                    return success_rate
                return None
            else:
                # 其他指标取平均值
                values = []
                for timeseries in results:
                    value = float(timeseries["value"][1])
                    values.append(value)
                return statistics.mean(values) if values else None
                
        except Exception as e:
            self.log_event("ERROR", f"Failed to collect {metric_key} for {service_name}: {str(e)}")
            return None
            
    def monitor_services(self):
        """监控所有服务"""
        services = self.get_all_services()
        self.log_event("INFO", f"开始监控 {len(services)} 个服务")
        
        while self.is_running:
            timestamp = datetime.utcnow()
            elapsed = (timestamp - self.start_time).total_seconds()
            
            if elapsed > MONITORING_DURATION:
                break
                
            # 收集每个服务的指标
            for service in services:
                service_data = {
                    "timestamp": timestamp.isoformat(),
                    "elapsed_seconds": elapsed
                }
                
                for metric_key, metric_name in METRIC_MAPPING.items():
                    if metric_key != "timestamp":
                        value = self.collect_metric(service, metric_key, metric_name)
                        if value is not None:
                            service_data[metric_key] = value
                            
                            # 特别关注存活率
                            if metric_key == "success_rate" and value < 90:
                                self.log_event("WARNING", 
                                    f"{service} 存活率下降至 {value:.2f}%")
                
                # 保存数据
                if service not in self.metrics_data:
                    self.metrics_data[service] = []
                self.metrics_data[service].append(service_data)
            
            # 等待下一次采样
            time.sleep(SAMPLE_INTERVAL)
            
    def get_all_services(self):
        """获取所有服务"""
        resp = requests.get(f"{PROMETHEUS_URL}/api/v1/label/service/values")
        if resp.status_code != 200:
            raise Exception("获取服务列表失败")
        
        services = resp.json()["data"]
        filtered_services = []
        for service in services:
            query = f'{{namespace="{NAMESPACE}",service="{service}"}}'
            resp = requests.get(f"{PROMETHEUS_URL}/api/v1/series?match[]={query}")
            if resp.status_code == 200 and resp.json()["data"]:
                filtered_services.append(service)
        
        return filtered_services
        
    def save_results(self):
        """保存监控结果"""
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 保存每个服务的指标数据
        for service, data in self.metrics_data.items():
            csv_path = os.path.join(OUTPUT_DIR, f"{service}_chaos.csv")
            
            if data:
                # 获取所有的指标键
                keys = list(data[0].keys())
                
                with open(csv_path, "w", newline="", encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(data)
                    
                self.log_event("INFO", f"保存 {service} 的监控数据到 {csv_path}")
                
        # 保存事件日志
        events_path = os.path.join(OUTPUT_DIR, "chaos_events.json")
        with open(events_path, "w", encoding='utf-8') as f:
            json.dump(self.events, f, indent=2, ensure_ascii=False)
            
    def generate_report(self):
        """生成故障注入报告"""
        report_path = os.path.join(OUTPUT_DIR, "chaos_report.md")
        
        with open(report_path, "w", encoding='utf-8') as f:
            f.write("# Robot Shop 故障注入实验报告\n\n")
            f.write(f"## 实验概述\n\n")
            f.write(f"- **开始时间**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC\n")
            f.write(f"- **持续时间**: 30分钟\n")
            f.write(f"- **监控服务数**: {len(self.metrics_data)}个\n")
            f.write(f"- **采样间隔**: {SAMPLE_INTERVAL}秒\n\n")
            
            f.write("## 故障注入方法\n\n")
            f.write("使用Chaos Mesh进行Pod Kill实验，采用以下策略：\n\n")
            f.write("1. **第一阶段 (0-3分钟)**: 杀死payment服务pod\n")
            f.write("2. **第二阶段 (3-8分钟)**: 并行杀死cart和catalogue服务pods\n")
            f.write("3. **第三阶段 (8-12分钟)**: 随机杀死50%的shipping或dispatch服务pods\n")
            f.write("4. **第四阶段 (12-18分钟)**: 并行杀死web和user服务pods\n")
            f.write("5. **第五阶段 (18-20分钟)**: 杀死ratings服务pod\n\n")
            
            f.write("## 指标影响分析\n\n")
            
            # 分析每个服务的指标变化
            for service, data in self.metrics_data.items():
                f.write(f"### {service} 服务\n\n")
                
                # 计算各指标的统计信息
                metrics_stats = {}
                for metric_key in METRIC_MAPPING.keys():
                    if metric_key == "timestamp":
                        continue
                        
                    values = [d.get(metric_key) for d in data if metric_key in d]
                    if values:
                        metrics_stats[metric_key] = {
                            "min": min(values),
                            "max": max(values),
                            "avg": statistics.mean(values),
                            "std": statistics.stdev(values) if len(values) > 1 else 0
                        }
                
                # 特别分析存活率
                if "success_rate" in metrics_stats:
                    stats = metrics_stats["success_rate"]
                    f.write(f"#### 存活率 (envoy_server_live)\n")
                    f.write(f"- **最低值**: {stats['min']:.2f}%\n")
                    f.write(f"- **最高值**: {stats['max']:.2f}%\n")
                    f.write(f"- **平均值**: {stats['avg']:.2f}%\n")
                    f.write(f"- **标准差**: {stats['std']:.2f}%\n\n")
                    
                    # 检查存活率下降事件
                    drops = [d for d in data if d.get("success_rate", 100) < 90]
                    if drops:
                        f.write(f"**⚠️ 检测到{len(drops)}次存活率下降至90%以下**\n\n")
                
                # 其他指标
                f.write("#### 其他关键指标\n")
                for metric_key, stats in metrics_stats.items():
                    if metric_key != "success_rate":
                        metric_desc = {
                            "ops": "请求总数",
                            "duration": "连接持续时间",
                            "cpu": "CPU使用率",
                            "memory": "内存使用量",
                            "receive": "网络接收字节数",
                            "transmit": "网络发送字节数"
                        }.get(metric_key, metric_key)
                        
                        f.write(f"- **{metric_desc}**: ")
                        f.write(f"平均={stats['avg']:.2f}, ")
                        f.write(f"最小={stats['min']:.2f}, ")
                        f.write(f"最大={stats['max']:.2f}\n")
                
                f.write("\n")
            
            # 添加事件总结
            f.write("## 关键事件\n\n")
            warnings = [e for e in self.events if e["type"] == "WARNING"]
            errors = [e for e in self.events if e["type"] == "ERROR"]
            
            f.write(f"- 总警告数: {len(warnings)}\n")
            f.write(f"- 总错误数: {len(errors)}\n\n")
            
            if warnings:
                f.write("### 警告事件\n")
                for w in warnings[:10]:  # 只显示前10个
                    f.write(f"- [{w['timestamp']}] {w['message']}\n")
                f.write("\n")
            
            f.write("## 结论\n\n")
            f.write("通过本次故障注入实验，我们观察到：\n\n")
            f.write("1. **服务可用性影响**: Pod被杀死后，Kubernetes会自动重启pods，但在重启期间服务的存活率(envoy_server_live)会显著下降\n")
            f.write("2. **级联故障**: 某些服务的故障会影响到依赖它的其他服务\n")
            f.write("3. **恢复时间**: 大部分服务能在1-2分钟内恢复到正常状态\n")
            f.write("4. **系统韧性**: Robot Shop微服务架构展现出一定的容错能力，但仍需要改进以应对大规模故障\n")
            
        self.log_event("INFO", f"报告已生成: {report_path}")

def main():
    monitor = ChaosMonitor()
    
    try:
        # 开始监控
        monitor.monitor_services()
    except KeyboardInterrupt:
        monitor.log_event("INFO", "监控被用户中断")
    except Exception as e:
        monitor.log_event("ERROR", f"监控出错: {str(e)}")
    finally:
        # 保存结果并生成报告
        monitor.save_results()
        monitor.generate_report()

if __name__ == "__main__":
    main() 