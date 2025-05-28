import requests
import csv
import time
import os

PROM_URL = "http://localhost:55030"  # 替换成你的 Prometheus 地址


# 查询时间序列区间数据
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


# 解析数据，合并时间戳对应的值
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

    queries = {
        "ops": "microservices_demo_user_request_count",
        "success": "microservices_demo_user_request_success_count",
        "duration": "microservices_demo_user_request_latency_microseconds_sum",
        "cpu": 'container_cpu_usage_seconds_total{namespace="sock-shop"}',
        "memory": 'container_memory_usage_bytes{namespace="sock-shop"}',
        "receive": 'container_network_receive_bytes_total{namespace="sock-shop"}',
        "transmit": 'container_network_transmit_bytes_total{namespace="sock-shop"}',
    }

    # 1. 拉取所有指标数据
    data = {}
    for name, q in queries.items():
        try:
            metric_data = query_range(q, start, end)
            data[name] = parse_metric(metric_data)
        except Exception as e:
            print(f"Error querying {name}: {e}")
            data[name] = {}

    # 2. 合并所有时间戳
    all_timestamps = set()
    for v in data.values():
        all_timestamps.update(v.keys())
    timestamps = sorted(all_timestamps)
    print(f"Total combined timestamps: {len(timestamps)}")

    # 确保输出目录存在
    os.makedirs("export_metrics", exist_ok=True)

    # 3. 写入正常和异常两个CSV文件
    normal_file = "export_metrics/normal.csv"
    abnormal_file = "export_metrics/abnormal.csv"

    with open(normal_file, "w", newline="") as f_normal, open(
        abnormal_file, "w", newline=""
    ) as f_abnormal:
        writer_normal = csv.writer(f_normal)
        writer_abnormal = csv.writer(f_abnormal)

        header = [
            "timestamp",
            "ops",
            "success_rate",
            "duration",
            "cpu",
            "memory",
            "receive",
            "transmit",
        ]
        writer_normal.writerow(header)
        writer_abnormal.writerow(header)

        normal_count = 0
        abnormal_count = 0

        for ts in timestamps:
            ops_val = data.get("ops", {}).get(ts, 0)
            success_val = data.get("success", {}).get(ts, 0)
            success_rate = success_val / ops_val if ops_val > 0 else 0
            duration_val = data.get("duration", {}).get(ts, 0)
            cpu_val = data.get("cpu", {}).get(ts, 0)
            memory_val = data.get("memory", {}).get(ts, 0)
            receive_val = data.get("receive", {}).get(ts, 0)
            transmit_val = data.get("transmit", {}).get(ts, 0)

            row = [
                ts,
                ops_val,
                success_rate,
                duration_val,
                cpu_val,
                memory_val,
                receive_val,
                transmit_val,
            ]

            # 定义异常条件，比如成功率<0.9 或 cpu > 0.8 秒（可调整）
            # if success_rate < 0.9 or cpu_val > 0.8:
            if success_rate < 0.1:
                writer_abnormal.writerow(row)
                abnormal_count += 1
            else:
                writer_normal.writerow(row)
                normal_count += 1

        print(
            f"Export finished. Normal rows: {normal_count}, Abnormal rows: {abnormal_count}"
        )
        print(f"Files: {normal_file} and {abnormal_file}")


if __name__ == "__main__":
    main()
