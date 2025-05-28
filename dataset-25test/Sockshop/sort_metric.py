import requests
import json
import csv
import os
from collections import defaultdict
from datetime import datetime, timedelta

PROM_URL = (
    "http://localhost:64927"  # 修改为你的 Prometheus 地址（如 minikube 中端口转发地址）
)

# 确保 output 文件夹存在
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def fetch_all_metrics():
    print("Fetching all metric names from Prometheus...")
    resp = requests.get(f"{PROM_URL}/api/v1/label/__name__/values")
    resp.raise_for_status()
    all_metrics = resp.json()["data"]
    print(f"Total metric names fetched: {len(all_metrics)}")
    return all_metrics


def fetch_metric_metadata(metric_name):
    resp = requests.get(f"{PROM_URL}/api/v1/series", params={"match[]": metric_name})
    resp.raise_for_status()
    return resp.json()["data"]


def fetch_metric_data(metric_name, service_name):
    # 计算过去一个小时的时间范围
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=1)

    # 转换为 Unix 时间戳
    start_timestamp = int(start_time.timestamp())
    end_timestamp = int(end_time.timestamp())

    # 设置步长（每1分钟一个数据点）
    step = 60  # 60 秒

    # 构建查询
    query = f'{metric_name}{{kubernetes_namespace="sock-shop", kubernetes_name="{service_name}"}}'

    # 使用 query_range API
    resp = requests.get(
        f"{PROM_URL}/api/v1/query_range",
        params={
            "query": query,
            "start": start_timestamp,
            "end": end_timestamp,
            "step": step,
        },
    )
    resp.raise_for_status()
    return resp.json()["data"]["result"]


def main():
    all_metrics = fetch_all_metrics()
    print("Filtering metrics related to Sock Shop...")
    service_metric_map = defaultdict(set)

    for metric in all_metrics:
        try:
            metadata = fetch_metric_metadata(metric)
            for entry in metadata:
                if entry.get("kubernetes_namespace") == "sock-shop":
                    service = (
                        entry.get("kubernetes_name")
                        or entry.get("name")
                        or entry.get("job")
                    )
                    if service:
                        service_metric_map[service].add(metric)
        except Exception as e:
            print(f"Warning: Failed to fetch metadata for {metric}: {e}")

    # 转为 JSON 格式保存
    json_ready = {
        svc: sorted(list(metrics)) for svc, metrics in service_metric_map.items()
    }
    json_filename = os.path.join(OUTPUT_DIR, "sockshop_service_metrics.json")
    with open(json_filename, "w") as f:
        json.dump(json_ready, f, indent=2)
    print("\n✅ Output saved to sockshop_service_metrics.json")

    # 为每个服务导出指标数据到 CSV
    for service, metrics in service_metric_map.items():
        print(f"\n正在收集 {service} 的指标数据...")

        # 准备 CSV 文件
        csv_filename = os.path.join(OUTPUT_DIR, f"{service}_metrics.csv")
        with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
            # 准备 CSV 写入器
            csv_columns = ["timestamp"] + sorted(list(metrics))
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()

            # 获取每个指标的数据
            for metric in metrics:
                try:
                    metric_results = fetch_metric_data(metric, service)
                    for result in metric_results:
                        # 处理每个时间点的数据
                        for timestamp, value in result["values"]:
                            formatted_timestamp = datetime.fromtimestamp(
                                timestamp
                            ).strftime("%Y-%m-%d %H:%M:%S")

                            # 写入 CSV
                            row_data = {"timestamp": formatted_timestamp, metric: value}
                            writer.writerow(row_data)
                except Exception as e:
                    print(f"Warning: Failed to fetch data for {metric}: {e}")

        print(f"✅ 指标数据已保存到 {csv_filename}")


if __name__ == "__main__":
    main()
