import requests
import csv
import time

PROM_URL = "http://localhost:55030"


# 你可能需要写多个查询，获取不同指标的时间序列数据
# 这里示例获取请求次数
def query_range(promql, start, end, step="30s"):
    url = f"{PROM_URL}/api/v1/query_range"
    params = {"query": promql, "start": start, "end": end, "step": step}
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()
    if data["status"] == "success":
        return data["data"]["result"]
    else:
        raise RuntimeError("Prometheus query failed: " + str(data))


def parse_metric(metric_data, value_index=1):
    # 返回 {timestamp: value} 字典，方便合并
    res = {}
    for result in metric_data:
        for v in result["values"]:
            ts = int(float(v[0]))
            val = float(v[value_index])
            res[ts] = res.get(ts, 0) + val  # 如果多个实例同时间戳，累加
    return res


def main():
    # 时间范围：过去1小时
    end = int(time.time())
    start = end - 3600

    # 查询示例指标，需替换成实际 sock-shop 指标名
    ops_data = query_range("microservices_demo_user_request_count", start, end)
    success_data = query_range(
        "microservices_demo_user_request_success_count", start, end
    )
    duration_data = query_range(
        "microservices_demo_user_request_latency_microseconds_sum", start, end
    )
    cpu_data = query_range(
        'container_cpu_usage_seconds_total{namespace="sock-shop"}', start, end
    )
    mem_data = query_range(
        'container_memory_usage_bytes{namespace="sock-shop"}', start, end
    )
    rx_data = query_range(
        'container_network_receive_bytes_total{namespace="sock-shop"}', start, end
    )
    tx_data = query_range(
        'container_network_transmit_bytes_total{namespace="sock-shop"}', start, end
    )

    # 转成 {timestamp: value} 格式
    ops = parse_metric(ops_data)
    success = parse_metric(success_data)
    duration = parse_metric(duration_data)
    cpu = parse_metric(cpu_data)
    memory = parse_metric(mem_data)
    receive = parse_metric(rx_data)
    transmit = parse_metric(tx_data)

    timestamps = sorted(
        set(ops.keys())
        | set(success.keys())
        | set(duration.keys())
        | set(cpu.keys())
        | set(memory.keys())
        | set(receive.keys())
        | set(transmit.keys())
    )

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
            ops_val = ops.get(ts, 0)
            success_val = success.get(ts, 0)
            # 计算成功率
            success_rate = success_val / ops_val if ops_val > 0 else 0
            duration_val = duration.get(ts, 0)
            cpu_val = cpu.get(ts, 0)
            memory_val = memory.get(ts, 0)
            receive_val = receive.get(ts, 0)
            transmit_val = transmit.get(ts, 0)
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


if __name__ == "__main__":
    main()
