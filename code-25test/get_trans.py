import requests
import time
import datetime
import pandas as pd

# 配置
PROMETHEUS_URL = "http://127.0.0.1:51424"
QUERY = 'node_network_transmit_bytes_total{device=~".*bridge.*"}'
STEP = "30s"

# 时间范围：过去1小时
end_time = int(time.time())
start_time = end_time - 3600


def range_query_prometheus(query, start, end, step="30s"):
    url = f"{PROMETHEUS_URL}/api/v1/query_range"
    params = {"query": query, "start": start, "end": end, "step": step}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()["data"]["result"]
    else:
        raise Exception(f"HTTP error {response.status_code}: {response.text}")


# 获取数据
result = range_query_prometheus(QUERY, start_time, end_time, STEP)

# 多条时间序列 => 多个 CSV 或合并为一个
if result:
    for metric in result:
        device = metric["metric"].get("device", "unknown")
        instance = metric["metric"].get("instance", "unknown")
        values = metric["values"]
        df = pd.DataFrame(values, columns=["timestamp", "value"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
        df["value"] = df["value"].astype(float)

        # 保存为 CSV：包含 device 名称
        safe_device = device.replace("/", "_")
        filename = f"network_transmit_{safe_device}.csv"
        df.to_csv(filename, index=False)
        print(f"✅ 保存数据: {filename} （instance: {instance}）")
else:
    print("❌ 没有匹配到任何 bridge 相关的数据")
