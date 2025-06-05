import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# 读取CSV文件
df = pd.read_csv("result/sample.csv")

# 将timestamp列转换为datetime类型
df["timestamp"] = pd.to_datetime(df["timestamp"])

# 创建图形和坐标轴
plt.figure(figsize=(12, 6))

# 绘制每一列的数据（除了timestamp列）
for column in df.columns:
    if column != "timestamp":
        plt.plot(df["timestamp"], df[column], label=column, linewidth=1.5)

# 设置图形属性
plt.title("Time Series Data", fontsize=14)
plt.xlabel("Time", fontsize=12)
plt.ylabel("Value", fontsize=12)
plt.grid(True, linestyle="--", alpha=0.7)
plt.legend(loc="best")

# 自动调整x轴标签的角度，以防重叠
plt.xticks(rotation=45)

# 调整布局，确保所有元素都能显示
plt.tight_layout()

# 保存图形
plt.savefig("result_plot.png", dpi=300, bbox_inches="tight")
print("Plot has been saved as trend_plot.png")
