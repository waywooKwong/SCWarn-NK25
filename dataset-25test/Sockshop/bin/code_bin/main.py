import requests
import json
import csv
import os
from datetime import datetime, timedelta

PROMETHEUS_URL = "http://localhost:51123"  # 替换为你的 Prometheus 地址
NAMESPACE = "sock-shop"
OUTPUT_DIR = "metrics"


def get_services_metrics_by_name():
    """收集所有指标及对应的name标签值，整理成 {name: set(metrics)}"""
    print("[*] 获取所有 metric 名称...")
    resp = requests.get(f"{PROMETHEUS_URL}/api/v1/label/__name__/values")
    metric_names = resp.json()["data"]

    name_metrics = {}

    for metric in metric_names:
        query_url = (
            f"{PROMETHEUS_URL}/api/v1/series"
            f'?match[]={metric}{{kubernetes_namespace="{NAMESPACE}"}}'
        )
        resp = requests.get(query_url)
        if resp.status_code != 200:
            continue
        series_list = resp.json()["data"]
        for series in series_list:
            name = series.get("name")
            if not name:
                continue
            name_metrics.setdefault(name, set()).add(metric)

    result = {k: sorted(list(v)) for k, v in name_metrics.items()}

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "service_metrics_by_name.json"), "w") as f:
        json.dump(result, f, indent=2)

    return result


def generate_csv_for_each_name(name_metrics):
    """根据name标签，分别为每个name抓取过去一小时的指标数据，写入对应CSV"""
    end = datetime.utcnow()
    start = end - timedelta(hours=1)
    step = "30s"

    for name, metrics in name_metrics.items():
        timestamps = set()
        metric_data = {}

        for metric in metrics:
            # 查询时限定 namespace 和 name 标签
            query = f'{metric}{{kubernetes_namespace="{NAMESPACE}",name="{name}"}}'
            url = (
                f"{PROMETHEUS_URL}/api/v1/query_range"
                f"?query={query}&start={start.isoformat()}Z&end={end.isoformat()}Z&step={step}"
            )
            resp = requests.get(url)
            if resp.status_code != 200:
                continue
            results = resp.json()["data"]["result"]

            for timeseries in results:
                for ts, val in timeseries["values"]:
                    ts = int(ts)
                    timestamps.add(ts)
                    metric_data.setdefault(ts, {}).setdefault(metric, val)

        sorted_timestamps = sorted(list(timestamps))
        header = ["timestamp"] + metrics
        rows = []
        for ts in sorted_timestamps:
            row = [datetime.utcfromtimestamp(ts).isoformat()]
            for metric in metrics:
                row.append(metric_data.get(ts, {}).get(metric, ""))
            rows.append(row)

        csv_path = os.path.join(OUTPUT_DIR, f"{name}.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        print(f"[+] CSV generated: {csv_path}")


if __name__ == "__main__":
    name_metrics = get_services_metrics_by_name()
    generate_csv_for_each_name(name_metrics)
