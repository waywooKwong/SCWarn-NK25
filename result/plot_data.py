import pandas as pd
import matplotlib.pyplot as plt
import os

# 定义CSV文件夹路径和图像保存路径
csv_folder = "online-boutique"
image_folder = os.path.join("image", os.path.basename(csv_folder))

# 确保新的图像保存文件夹存在
os.makedirs(image_folder, exist_ok=True)

# 遍历CSV文件夹中的所有CSV文件
for filename in os.listdir(csv_folder):
    if filename.endswith(".csv"):
        csv_path = os.path.join(csv_folder, filename)
        df = pd.read_csv(csv_path)

        # 将timestamp列转换为datetime类型
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # 创建图形和坐标轴
        plt.figure(figsize=(12, 6))

        # 绘制每一列的数据（除了timestamp列）
        for column in df.columns:
            if column != "timestamp":
                plt.plot(df["timestamp"], df[column], label=column, linewidth=1.5)

        # 设置图形属性
        plt.title(f"Time Series Data - {filename}", fontsize=14)
        plt.xlabel("Time", fontsize=12)
        plt.ylabel("Value", fontsize=12)
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.legend(loc="best")

        # 自动调整x轴标签的角度，以防重叠
        plt.xticks(rotation=45)

        # 调整布局，确保所有元素都能显示
        plt.tight_layout()

        # 保存图形
        image_path = os.path.join(
            image_folder, f"{os.path.splitext(filename)[0]}_plot.png"
        )
        plt.savefig(image_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Plot has been saved as {image_path}")
