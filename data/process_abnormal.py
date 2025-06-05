import pandas as pd
import os
from pathlib import Path
from datetime import datetime, timedelta

"""
cd 到 SCWarn/data 目录下运行
"""
dataset = "sock-shop"

# 创建输出目录
output_dir = Path(f"./{dataset}/abnormal_processed")
output_dir.mkdir(parents=True, exist_ok=True)

# 输入目录
input_dir = Path(f"./{dataset}/abnormal")

# 处理每个CSV文件
for csv_file in input_dir.glob("*.csv"):
    # 读取CSV文件
    df = pd.read_csv(csv_file)

    # 将success_rate超过100的值设置为100
    df.loc[df["success_rate"] > 100.0, "success_rate"] = 100.0

    # 分离success_rate不为100的行和等于100的行
    abnormal_rows = df[df["success_rate"] != 100.0]
    normal_rows = df[df["success_rate"] == 100.0]

    # 计算正常行的中点
    mid_point = len(normal_rows) // 2

    # 创建新的DataFrame
    result = pd.concat(
        [normal_rows.iloc[:mid_point], abnormal_rows, normal_rows.iloc[mid_point:]]
    ).reset_index(drop=True)

    # 获取原始时间间隔
    original_timestamps = pd.to_datetime(df["timestamp"])
    time_intervals = []
    for i in range(1, len(original_timestamps)):
        interval = original_timestamps.iloc[i] - original_timestamps.iloc[i - 1]
        time_intervals.append(interval)

    # 使用第一个时间戳作为起点，重新生成时间序列
    start_time = pd.to_datetime(df["timestamp"].iloc[0])
    new_timestamps = [start_time]

    # 使用原始间隔重新生成时间戳
    for i in range(len(result) - 1):
        interval_idx = i % len(time_intervals)
        new_timestamps.append(new_timestamps[-1] + time_intervals[interval_idx])

    # 更新结果DataFrame的timestamp列
    result["timestamp"] = new_timestamps

    # 保存到新目录
    output_file = output_dir / csv_file.name
    result.to_csv(output_file, index=False)

print(f"处理完成！文件已保存到 {output_dir} 目录")
