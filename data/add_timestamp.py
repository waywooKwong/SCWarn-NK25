import os
import pandas as pd

ROOT_DIR = "online-boutique"  # ← 修改为你的实际目录

for subdir in os.listdir(ROOT_DIR):
    subdir_path = os.path.join(ROOT_DIR, subdir)
    if not os.path.isdir(subdir_path):
        continue

    for filename in os.listdir(subdir_path):
        if not filename.endswith(".csv"):
            continue

        file_path = os.path.join(subdir_path, filename)

        try:
            df = pd.read_csv(file_path)

            # 将 timestamp 列转换为 Unix 时间戳
            unix_ts = pd.to_datetime(df['timestamp'], utc=True).astype('int64') // 10**9

            # 插入为第二列，临时列名为 timestamp_unix
            df.insert(1, 'timestamp_unix', unix_ts)

            # 把列名列表里 timestamp_unix 改成 timestamp（制造重复列名）
            cols = list(df.columns)
            ts_unix_index = cols.index('timestamp_unix')
            cols[ts_unix_index] = 'timestamp'
            df.columns = cols

            # 保存回原文件
            df.to_csv(file_path, index=False)
            print(f"✅ 成功插入重复列: {file_path}")

        except Exception as e:
            print(f"❌ 错误处理 {file_path}: {e}")
