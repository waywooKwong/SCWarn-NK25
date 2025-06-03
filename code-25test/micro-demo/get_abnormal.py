import requests
import json
import csv
import os
from datetime import datetime, timedelta

# 配置信息
PROMETHEUS_URL = "http://127.0.0.1:54570"
NAMESPACE = "micro-demo"
SERVICE_COUNT = 6  # 服务总数，用于计算成功率

# 构建正确的输出目录路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))  # 回到项目根目录
OUTPUT_DIR = os.path.join(project_root, "data", "micro-demo", "test02")

# 加载指标映射
script_dir = os.path.dirname(os.path.abspath(__file__))
metric_mapping_path = os.path.join(script_dir, "metric_mapping.json")
with open(metric_mapping_path, "r", encoding="utf-8") as f:
    METRIC_MAPPING = json.load(f)


def get_all_services():
    """获取所有微服务名称"""
    print("[*] 获取所有微服务名称...")
    resp = requests.get(
        f"{PROMETHEUS_URL}/api/v1/label/service_istio_io_canonical_name/values"
    )
    if resp.status_code != 200:
        raise Exception("获取服务列表失败")

    services = resp.json()["data"]
    # 过滤出命名空间下的服务
    filtered_services = []
    for service in services:
        query = (
            f'{{namespace="{NAMESPACE}",service_istio_io_canonical_name="{service}"}}'
        )
        resp = requests.get(f"{PROMETHEUS_URL}/api/v1/series?match[]={query}")
        if resp.status_code == 200 and resp.json()["data"]:
            filtered_services.append(service)

    return filtered_services


def collect_metrics_for_service(service_name):
    """收集指定服务的所有指标数据"""
    end = datetime.utcnow()
    start = end - timedelta(minutes=360)
    step = "2s"

    timestamps = set()
    metric_data = {}

    # 收集基本指标
    for metric_key, metric_name in METRIC_MAPPING.items():
        if metric_key == "success_rate":
            continue

        query = f'{metric_name}{{namespace="{NAMESPACE}",service_istio_io_canonical_name="{service_name}"}}'
        url = f"{PROMETHEUS_URL}/api/v1/query_range?query={query}&start={start.isoformat()}Z&end={end.isoformat()}Z&step={step}"

        resp = requests.get(url)
        if resp.status_code != 200:
            continue

        results = resp.json()["data"]["result"]
        for timeseries in results:
            for ts, val in timeseries["values"]:
                ts = int(ts)
                timestamps.add(ts)
                metric_data.setdefault(ts, {}).setdefault(metric_key, val)

    # 计算成功率
    completed_query = f'{METRIC_MAPPING["success_rate"]["completed"]}{{namespace="{NAMESPACE}",service_istio_io_canonical_name="{service_name}"}}'
    total_query = f'{METRIC_MAPPING["success_rate"]["total"]}{{namespace="{NAMESPACE}",service_istio_io_canonical_name="{service_name}"}}'

    for query in [completed_query, total_query]:
        url = f"{PROMETHEUS_URL}/api/v1/query_range?query={query}&start={start.isoformat()}Z&end={end.isoformat()}Z&step={step}"
        resp = requests.get(url)
        if resp.status_code != 200:
            continue

        results = resp.json()["data"]["result"]
        for timeseries in results:
            for ts, val in timeseries["values"]:
                ts = int(ts)
                timestamps.add(ts)
                metric_key = "completed" if "completed" in query else "total"
                metric_data.setdefault(ts, {}).setdefault(metric_key, val)

    # 计算成功率
    for ts in timestamps:
        completed = float(metric_data[ts].get("completed", 0))
        total = float(metric_data[ts].get("total", 0))
        success_rate = (completed / total * 100) if total > 0 else 0
        metric_data[ts]["success_rate"] = success_rate

    return timestamps, metric_data


def generate_csv_for_service(service_name, timestamps, metric_data):
    """为指定服务生成CSV文件"""
    sorted_timestamps = sorted(list(timestamps))
    # 过滤掉timestamp字段，因为时间戳是由Prometheus自动添加的
    metrics = [key for key in METRIC_MAPPING.keys() if key != "timestamp"]
    header = ["timestamp"] + metrics

    rows = []
    for ts in sorted_timestamps:
        # 将Unix时间戳转换为ISO格式的时间字符串
        row = [datetime.utcfromtimestamp(ts).strftime("%Y-%m-%dT%H:%M:%SZ")]
        for metric in metrics:
            row.append(metric_data.get(ts, {}).get(metric, ""))
        rows.append(row)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    csv_path = os.path.join(OUTPUT_DIR, f"{service_name}.csv")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"[+] CSV generated: {csv_path}")


def main():
    try:
        services = get_all_services()
        print(f"[*] 找到 {len(services)} 个微服务")

        for service in services:
            print(f"[*] 正在处理服务: {service}")
            timestamps, metric_data = collect_metrics_for_service(service)
            generate_csv_for_service(service, timestamps, metric_data)

        print("[+] 所有服务指标收集完成")

    except Exception as e:
        print(f"[-] 发生错误: {str(e)}")


if __name__ == "__main__":
    main()
