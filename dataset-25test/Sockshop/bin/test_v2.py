import requests
import csv
import time

PROM_URL = "http://localhost:55030"


def query_range(promql, start, end, step="30s"):
    url = f"{PROM_URL}/api/v1/query_range"
    params = {"query": promql, "start": start, "end": end, "step": step}
    print(f"Querying Prometheus: {promql}")
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()
    if data["status"] == "success":
        results = data["data"]["result"]
        print(f"  Got {len(results)} time series")
        # 打印每个时间序列的前3个数据点作示例
        for i, ts in enumerate(results[:3]):
            metric_info = ts.get("metric", {})
            values = ts.get("values", [])[:3]
            print(f"    Time series {i+1}: metric={metric_info}")
            print(f"      First 3 values: {values}")
        return results
    else:
        raise RuntimeError("Prometheus query failed: " + str(data))


def parse_metric(metric_data, value_index=1):
    res = {}
    for result in metric_data:
        for v in result["values"]:
            ts = int(float(v[0]))
            val = float(v[value_index])
            res[ts] = res.get(ts, 0) + val
    print(f"Parsed metric data into {len(res)} unique timestamps")
    return res


def main():
    end = int(time.time())
    start = end - 3600  # 过去1小时

    # 你需要根据实际指标名称替换下面的 promql 查询
    queries = {
        "ops": "microservices_demo_user_request_count",
        "success": "microservices_demo_user_request_success_count",
        "duration": "microservices_demo_user_request_latency_microseconds_sum",
        "cpu": 'container_cpu_usage_seconds_total{namespace="sock-shop"}',
        "memory": 'container_memory_usage_bytes{namespace="sock-shop"}',
        "receive": 'container_network_receive_bytes_total{namespace="sock-shop"}',
        "transmit": 'container_network_transmit_bytes_total{namespace="sock-shop"}',
    }

    data = {}
    for name, q in queries.items():
        try:
            metric_data = query_range(q, start, end)
            data[name] = parse_metric(metric_data)
        except Exception as e:
            print(f"Error querying {name}: {e}")
            data[name] = {}

    all_timestamps = set()
    for v in data.values():
        all_timestamps.update(v.keys())
    timestamps = sorted(all_timestamps)
    print(f"Total combined timestamps: {len(timestamps)}")

    with open("export_metrics/sockshop_metrics.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "timestamp",
                "ops",
                "success_rate",
                "duration",
                "cpu",
                "memory",
                "receive",
                "transmit",
            ]
        )
        for ts in timestamps:
            ops_val = data.get("ops", {}).get(ts, 0)
            success_val = data.get("success", {}).get(ts, 0)
            success_rate = success_val / ops_val if ops_val > 0 else 0
            duration_val = data.get("duration", {}).get(ts, 0)
            cpu_val = data.get("cpu", {}).get(ts, 0)
            memory_val = data.get("memory", {}).get(ts, 0)
            receive_val = data.get("receive", {}).get(ts, 0)
            transmit_val = data.get("transmit", {}).get(ts, 0)
            writer.writerow(
                [
                    ts,
                    ops_val,
                    success_rate,
                    duration_val,
                    cpu_val,
                    memory_val,
                    receive_val,
                    transmit_val,
                ]
            )

    print("CSV export completed: export_metrics/sockshop_metrics.csv")


if __name__ == "__main__":
    main()
