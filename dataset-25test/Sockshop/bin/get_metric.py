import requests

PROM_URL = "http://localhost:55030"


def get_all_metrics():
    url = f"{PROM_URL}/api/v1/label/__name__/values"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    return data["data"]


def get_metric_metadata(metric_name):
    url = f"{PROM_URL}/api/v1/series"
    params = {"match[]": metric_name, "match[]": '{namespace="sock-shop"}'}
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()["data"]


all_metrics = get_all_metrics()
print(f"Total metrics: {len(all_metrics)}")

sockshop_metrics = []
for name in all_metrics:
    try:
        series = get_metric_metadata(name)
        if series:
            print(f"✔ {name} — appears in sock-shop")
            sockshop_metrics.append(name)
    except Exception as e:
        print(f"Failed to fetch metadata for {name}: {e}")

print(f"\nTotal sock-shop-related metrics: {len(sockshop_metrics)}")
