import requests
import json
import csv
import os
from datetime import datetime, timedelta

# 配置信息
PROMETHEUS_URL = "http://127.0.0.1:64042"
NAMESPACE = "sock-shop"

# 改为函数调用时指定的参数
# OUTPUT_DIR = "train"

# 加载指标映射
with open("metric_mapping.json", "r") as f:
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
    # 过滤出online-boutique命名空间下的服务
    filtered_services = []
    for service in services:
        query = (
            f'{{namespace="{NAMESPACE}",service_istio_io_canonical_name="{service}"}}'
        )
        resp = requests.get(f"{PROMETHEUS_URL}/api/v1/series?match[]={query}")
        if resp.status_code == 200 and resp.json()["data"]:
            filtered_services.append(service)

    return filtered_services


# 修改1：把开始、终止时间设置为变量，方便传递
def collect_metrics_for_service(service_name, end, start, step):
    """收集指定服务的所有指标数据"""

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


# 修改位置2：OUTPUT_DIR = "normal" or "abnormal"
def generate_csv_for_service(
    service_name, timestamps, metric_data, OUTPUT_DIR="normal"
):
    """为指定服务生成CSV文件"""
    sorted_timestamps = sorted(list(timestamps))
    metrics = list(METRIC_MAPPING.keys())
    header = ["timestamp"] + metrics

    rows = []
    for ts in sorted_timestamps:
        row = [datetime.utcfromtimestamp(ts).isoformat()]
        for metric in metrics:
            row.append(metric_data.get(ts, {}).get(metric, ""))
        rows.append(row)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    csv_path = os.path.join(OUTPUT_DIR, f"{service_name}.csv")

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"[+] CSV generated: {csv_path}")


def main():
    try:
        services = get_all_services()
        print(f"[*] 找到 {len(services)} 个微服务")

        end = datetime.utcnow()
        start = end - timedelta(hours=1)
        step = "1s"
        # 2025-05-28T13:52:52
        # start = datetime.strptime("2025-05-28T11:22:47Z", "%Y-%m-%dT%H:%M:%SZ")
        # end = start + timedelta(hours=1)
        # step = "1s"

        for service in services:
            print(f"[*] 正在处理服务: {service}")
            timestamps, metric_data = collect_metrics_for_service(
                service, end, start, step
            )
            generate_csv_for_service(
                service, timestamps, metric_data, OUTPUT_DIR="train"
            )

        print("[+] 所有服务指标收集完成")

    except Exception as e:
        print(f"[-] 发生错误: {str(e)}")


if __name__ == "__main__":
    main()
