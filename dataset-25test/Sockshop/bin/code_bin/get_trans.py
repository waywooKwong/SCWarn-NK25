import requests
import time
import pandas as pd

PROMETHEUS_URL = "http://127.0.0.1:51424"
QUERY = 'node_network_transmit_bytes_total{device="bridge", instance="192.168.49.2:9100", job="node-exporter"}'
STEP = "30s"
end_time = int(time.time())
start_time = end_time - 60  # 改为 1小时时用：3600


def range_query_prometheus(query, start, end, step="30s"):
    url = f"{PROMETHEUS_URL}/api/v1/query_range"
    params = {"query": query, "start": start, "end": end, "step": step}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data["status"] == "success":
            return data["data"]["result"]
        else:
            print(f"⚠️ Prometheus query failed: {data}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误: {e}")
        return []


# 获取数据
result = range_query_prometheus(QUERY, start_time, end_time, STEP)

# 处理结果
if result:
    for metric in result:
        values = metric["values"]
        df = pd.DataFrame(values, columns=["timestamp", "value"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
        df["value"] = df["value"].astype(float)
        device = metric["metric"].get("device", "unknown")
        df.to_csv(f"network_transmit_{device}.csv", index=False)
        print(f"✅ 保存：network_transmit_{device}.csv")
else:
    print("⚠️ 没有获取到任何数据")
