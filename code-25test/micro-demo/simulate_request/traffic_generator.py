import requests
import random
import time
import logging
import json
import os
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TrafficGenerator:
    def __init__(self, config_path="config.json"):
        # 加载配置文件
        with open(config_path, "r") as f:
            config = json.load(f)

        self.base_url = config["front_end_url"]
        self.config = config["simulation_config"]

        # 模拟的用户ID列表
        self.user_ids = list(range(1, self.config["user_count"] + 1))
        # 模拟的商品ID列表
        self.product_ids = list(range(1, self.config["product_count"] + 1))

    def simulate_browse_products(self):
        """模拟用户浏览商品列表"""
        try:
            url = f"{self.base_url}/products"
            response = requests.get(url)
            logger.info(f"浏览商品列表 - 状态码: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"浏览商品列表失败: {str(e)}")
            return False

    def simulate_view_product(self):
        """模拟用户查看单个商品详情"""
        try:
            product_id = random.choice(self.product_ids)
            url = f"{self.base_url}/products/{product_id}"
            response = requests.get(url)
            logger.info(f"查看商品 {product_id} - 状态码: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"查看商品详情失败: {str(e)}")
            return False

    def simulate_add_to_cart(self):
        """模拟用户添加商品到购物车"""
        try:
            user_id = random.choice(self.user_ids)
            product_id = random.choice(self.product_ids)
            url = f"{self.base_url}/cart"
            data = {
                "user_id": user_id,
                "product_id": product_id,
                "quantity": random.randint(1, 5),
            }
            response = requests.post(url, json=data)
            logger.info(
                f"用户 {user_id} 添加商品 {product_id} 到购物车 - 状态码: {response.status_code}"
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"添加购物车失败: {str(e)}")
            return False

    def simulate_create_order(self):
        """模拟用户创建订单"""
        try:
            user_id = random.choice(self.user_ids)
            url = f"{self.base_url}/orders"
            data = {
                "user_id": user_id,
                "products": [
                    {
                        "product_id": random.choice(self.product_ids),
                        "quantity": random.randint(1, 3),
                    }
                    for _ in range(random.randint(1, 3))
                ],
            }
            response = requests.post(url, json=data)
            logger.info(f"用户 {user_id} 创建订单 - 状态码: {response.status_code}")
            return response.status_code == 200, (
                response.json().get("order_id") if response.status_code == 200 else None
            )
        except Exception as e:
            logger.error(f"创建订单失败: {str(e)}")
            return False, None

    def simulate_payment(self, order_id):
        """模拟用户支付订单"""
        try:
            url = f"{self.base_url}/payments"
            data = {
                "order_id": order_id,
                "payment_method": random.choice(["credit_card", "alipay", "wechat"]),
            }
            response = requests.post(url, json=data)
            logger.info(f"支付订单 {order_id} - 状态码: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"支付订单失败: {str(e)}")
            return False

    def run_traffic_simulation(self):
        """运行流量模拟"""
        logger.info(f"开始流量生成，目标服务地址: {self.base_url}")

        while True:
            try:
                # 随机选择一个操作进行模拟
                action = random.choice(
                    [
                        self.simulate_browse_products,
                        self.simulate_view_product,
                        self.simulate_add_to_cart,
                        self.simulate_create_order,
                    ]
                )

                if action == self.simulate_create_order:
                    success, order_id = action()
                    if success and order_id:
                        # 根据配置的概率进行支付
                        if random.random() < self.config["payment_probability"]:
                            self.simulate_payment(order_id)
                else:
                    action()

                # 根据配置的等待时间范围随机等待
                wait_time = random.uniform(
                    self.config["min_wait_time"], self.config["max_wait_time"]
                )
                time.sleep(wait_time)

            except Exception as e:
                logger.error(f"模拟过程中发生错误: {str(e)}")
                time.sleep(5)  # 发生错误时等待5秒后继续


if __name__ == "__main__":
    # 获取脚本所在目录的路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")

    logger.info("正在启动流量生成器...")
    traffic_gen = TrafficGenerator(config_path=config_path)

    try:
        traffic_gen.run_traffic_simulation()
    except KeyboardInterrupt:
        logger.info("流量生成已停止")
