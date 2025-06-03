import pandas as pd
import matplotlib.pyplot as plt
import os

# 设置基础路径和输出文件夹
dataset = "micro-demo"
base_path = f"data/{dataset}"
folders = ["abnormal", "normal", "train"]
output_dir = f"data/images/{dataset}"
success_rate_threshold = 90

# 创建输出文件夹（如果不存在）
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 获取任意文件夹中的CSV文件列表（这里用train文件夹）
csv_files = [
    f for f in os.listdir(os.path.join(base_path, "train")) if f.endswith(".csv")
]

# 处理每个服务的CSV文件
for csv_file in csv_files:
    # 创建新的图形
    plt.figure(figsize=(15, 12))

    try:
        # 为每个文件夹创建子图
        for idx, folder in enumerate(folders, 1):
            file_path = os.path.join(base_path, folder, csv_file)

            # 创建子图
            plt.subplot(3, 1, idx)

            # 读取CSV文件
            df = pd.read_csv(file_path)

            # 将时间戳转换为datetime格式
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            # 绘制主折线图
            plt.plot(
                df["timestamp"], df["success_rate"], color="blue", label="Success Rate"
            )

            # 标记成功率低于90%的点
            low_mask = df["success_rate"] < success_rate_threshold
            plt.scatter(
                df[low_mask]["timestamp"],
                df[low_mask]["success_rate"],
                color="red",
                s=50,
                label="abnormal point",
                zorder=5,
            )

            # 设置子图属性
            service_name = csv_file.replace(".csv", "")
            plt.title(f"{folder.capitalize()} - {service_name}")
            plt.ylabel("Success Rate (%)")

            # 只在最后一个子图显示x轴标签
            if idx == 3:
                plt.xlabel("Timestamp")

            plt.grid(True, alpha=0.3)

            # 只在有低于90%的点时显示图例
            if low_mask.any():
                plt.legend()

            # 调整x轴标签角度以提高可读性
            plt.xticks(rotation=45)

        # 调整子图之间的间距
        plt.tight_layout()

        # 保存图片
        service_name = csv_file.replace(".csv", "")
        output_file = os.path.join(output_dir, f"{service_name}.png")
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        print(f"已生成图片: {output_file}")

        # 关闭当前图形，释放内存
        plt.close()

    except Exception as e:
        print(f"处理文件 {csv_file} 时出错: {str(e)}")
        plt.close()

print("所有图片处理完成")
