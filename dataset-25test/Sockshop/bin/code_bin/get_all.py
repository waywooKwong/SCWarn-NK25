import requests
import json
import csv
import os
from datetime import datetime, timedelta

PROMETHEUS_URL = "http://localhost:64927"  # 替换为你的 Prometheus 地址
OUTPUT_DIR = "output_all"


def get_services_metrics():
    """获取所有微服务及其暴露的指标名称"""
    resp = requests.get(f"{PROMETHEUS_URL}/api/v1/label/__name__/values")
    metric_names = resp.json()["data"]

    service_metrics = {}

    for metric in metric_names:
        query_url = f"{PROMETHEUS_URL}/api/v1/series?match[]={metric}"
        resp = requests.get(query_url)
        if resp.status_code != 200:
            continue
        series_list = resp.json()["data"]
        for series in series_list:
            job = series.get("job")
            if not job:
                continue
            service_metrics.setdefault(job, set()).add(metric)

    result = {svc: sorted(list(metrics)) for svc, metrics in service_metrics.items()}

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "service_metrics.json"), "w") as f:
        json.dump(result, f, indent=2)

    return result


def generate_csv_for_service_metrics(service_metrics):
    """为每个微服务抓取过去一小时的所有指标值，写入 CSV 到 output 文件夹"""
    end = datetime.utcnow()
    start = end - timedelta(hours=1)
    step = "30s"

    for service, metrics in service_metrics.items():
        rows = []
        timestamps = set()
        metric_data = {}

        for metric in metrics:
            query = f"{metric}{{job='{service}'}}"
            url = (
                f"{PROMETHEUS_URL}/api/v1/query_range"
                f"?query={query}&start={start.isoformat()}Z&end={end.isoformat()}Z&step={step}"
            )
            resp = requests.get(url)
            if resp.status_code != 200:
                continue
            results = resp.json()["data"]["result"]

            for timeseries in results:
                values = timeseries["values"]
                for ts, val in values:
                    ts = int(ts)
                    timestamps.add(ts)
                    metric_data.setdefault(ts, {}).setdefault(metric, val)

        sorted_timestamps = sorted(list(timestamps))
        header = ["timestamp"] + metrics
        for ts in sorted_timestamps:
            row = [datetime.utcfromtimestamp(ts).isoformat()]
            for metric in metrics:
                val = metric_data.get(ts, {}).get(metric, "")
                row.append(val)
            rows.append(row)

        csv_path = os.path.join(OUTPUT_DIR, f"{service}.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        print(f"[+] CSV generated: {csv_path}")


if __name__ == "__main__":
    service_metrics = get_services_metrics()
    generate_csv_for_service_metrics(service_metrics)
