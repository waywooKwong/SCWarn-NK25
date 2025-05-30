# my_micro 微服务示例

## 服务结构

- user-service：用户服务
- product-service：商品服务
- order-service：订单服务（依赖 user、product）
- cart-service：购物车服务（依赖 product）
- payment-service：支付服务（依赖 order）

## 快速部署

1. 启动 minikube 并启用 istio-injection：
   ```bash
   minikube start
   kubectl create namespace micro-demo
   kubectl label namespace micro-demo istio-injection=enabled
   ```
2. 手动拉取要用到的 python 镜像
   ```
   docker pull python:3.10-slim
   ```
3. 构建 Dcoker 镜像：
   ```bash
   cd user-service
   docker build -t user-service:latest .
   cd ../product-service
   docker build -t product-service:latest .
   cd ../order-service
   docker build -t order-service:latest .
   cd ../cart-service
   docker build -t cart-service:latest .
   cd ../payment-service
   docker build -t payment-service:latest .
   ```
4. 部署到 Kubernetes
   ```bash
   cd user-service
   kubectl apply -f k8s.yaml -n micro-demo
   cd ../product-service
   kubectl apply -f k8s.yaml -n micro-demo
   cd ../order-service
   kubectl apply -f k8s.yaml -n micro-demo
   cd ../cart-service
   kubectl apply -f k8s.yaml -n micro-demo
   cd ../payment-service
   kubectl apply -f k8s.yaml -n micro-demo
   ```
4. 将本地 Docker 的镜像加载到 Minikube 中（待优化，部署文件是不是可以直接部署到 minikube 中）
```
   minikube image load cart-service:latest
   minikube image load order-service:latest
   minikube image load payment-service:latest
   minikube image load product-service:latest
```
5. 检查服务状态
   ```bash
   kubectl get pods -n micro-demo
   kubectl get svc -n micro-demo
   ```

## Istio 监控

- 部署在带有 istio-injection 的 namespace 下，Istio 会自动注入 sidecar。
- 可通过 Kiali、Jaeger、Prometheus 等工具可视化服务间调用链。

## 目录结构

```
my_micro/
├── user-service/
├── product-service/
├── order-service/
├── cart-service/
├── payment-service/
└── README.md
``` 