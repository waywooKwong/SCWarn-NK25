import requests
import json
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class MicroServiceSimulator:
    def __init__(self, config_file="config.json"):
        with open(config_file, "r") as f:
            self.config = json.load(f)

        self.base_url = self.config["front_end_url"]
        self.user_count = self.config["simulation_config"]["user_count"]
        self.product_count = self.config["simulation_config"]["product_count"]
        self.min_wait = self.config["simulation_config"]["min_wait_time"]
        self.max_wait = self.config["simulation_config"]["max_wait_time"]
        self.payment_prob = self.config["simulation_config"]["payment_probability"]

        # 用户会话存储
        self.user_sessions = {}

    def random_wait(self):
        """模拟用户思考时间"""
        time.sleep(random.uniform(self.min_wait, self.max_wait))

    def simulate_user_flow(self, user_id):
        """模拟单个用户的完整购物流程"""
        session = requests.Session()

        try:
            # 1. 用户登录
            logging.info(f"User {user_id}: 开始登录")
            login_data = {"username": f"user{user_id}", "password": "password123"}
            response = session.post(f"{self.base_url}/api/users/login", json=login_data)
            response.raise_for_status()

            self.random_wait()

            # 2. 浏览商品列表
            logging.info(f"User {user_id}: 浏览商品列表")
            response = session.get(f"{self.base_url}/api/products")
            response.raise_for_status()

            self.random_wait()

            # 3. 随机选择商品加入购物车
            product_id = random.randint(1, self.product_count)
            cart_data = {"product_id": product_id, "quantity": random.randint(1, 3)}
            logging.info(f"User {user_id}: 添加商品 {product_id} 到购物车")
            response = session.post(f"{self.base_url}/api/cart/add", json=cart_data)
            response.raise_for_status()

            self.random_wait()

            # 4. 查看购物车
            logging.info(f"User {user_id}: 查看购物车")
            response = session.get(f"{self.base_url}/api/cart")
            response.raise_for_status()

            # 5. 随机决定是否下单
            if random.random() < self.payment_prob:
                # 创建订单
                logging.info(f"User {user_id}: 创建订单")
                response = session.post(f"{self.base_url}/api/orders/create")
                response.raise_for_status()
                order_id = response.json()["order_id"]

                self.random_wait()

                # 支付订单
                payment_data = {
                    "order_id": order_id,
                    "payment_method": random.choice(
                        ["credit_card", "debit_card", "wallet"]
                    ),
                }
                logging.info(f"User {user_id}: 支付订单 {order_id}")
                response = session.post(
                    f"{self.base_url}/api/payments/process", json=payment_data
                )
                response.raise_for_status()

        except requests.exceptions.RequestException as e:
            logging.error(f"User {user_id} encountered error: {str(e)}")

        finally:
            # 登出
            logging.info(f"User {user_id}: 会话结束")
            session.close()

    def start_simulation(self):
        """启动模拟器"""
        logging.info(f"开始流量模拟，模拟 {self.user_count} 个用户")

        with ThreadPoolExecutor(max_workers=self.user_count) as executor:
            # 提交所有用户的模拟任务
            futures = [
                executor.submit(self.simulate_user_flow, user_id)
                for user_id in range(1, self.user_count + 1)
            ]

            # 等待所有任务完成
            for future in futures:
                future.result()

        logging.info("流量模拟完成")


if __name__ == "__main__":
    simulator = MicroServiceSimulator()
    simulator.start_simulation()
