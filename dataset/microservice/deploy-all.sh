#!/bin/bash
set -e

# 镜像仓库前缀，请替换为你的仓库地址
REPO=liqun0816

# 服务列表
SERVICES=(user-service order-service product-service gateway-service)
PORTS=(8080 8082 8083 8081)

# 1. 打包所有服务
for SVC in "${SERVICES[@]}"; do
  echo "\n==> 构建 $SVC ..."
  cd $SVC
  mvn clean package -DskipTests
  docker build -t $REPO/$SVC:latest .
  docker push $REPO/$SVC:latest
  cd ..
done

# 2. 部署到Kubernetes
kubectl apply -f k8s/

echo "\n全部服务和监控已部署完成！" 