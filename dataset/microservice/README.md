# 微服务系统

## 项目结构

该项目包含以下微服务：

- **user-service**: 用户服务
- **order-service**: 订单服务
- **product-service**: 产品服务
- **gateway-service**: 网关服务

## 环境要求

- Java 17
- Maven
- Docker
- Minikube

## 部署步骤

1. **启动 Minikube**:
   ```bash
   minikube start
   ```

2. **创建命名空间**:
   ```bash
   kubectl create namespace microservice
   ```

3. **构建和推送 Docker 镜像**:
   使用以下命令构建所有微服务的 Docker 镜像并推送到 Docker Hub：
   ```bash
   ./deploy-all.sh
   ```

4. **应用 Kubernetes 配置**:
   所有的 Kubernetes 配置文件已经包含在 `k8s` 目录中。它们会自动部署到 `microservice` 命名空间中。

5. **检查资源状态**:
   部署完成后，可以使用以下命令检查在 `microservice` 命名空间中的所有资源状态：
   ```bash
   kubectl get all -n microservice
   ```

6. **访问服务**:
   使用以下命令将服务端口转发到本地：
   ```bash
   kubectl port-forward service/gateway-service 8080:8080 -n microservice
   ```
   然后可以通过访问 `http://localhost:8080` 来访问网关服务。

## 监控

Prometheus 监控已集成。确保 Prometheus 服务正在运行，并通过相应的端口访问监控数据。

## 注意事项

- 确保在构建和推送 Docker 镜像时，Docker Daemon 正在运行。
- 如果在推送镜像时遇到网络问题，请检查网络连接或使用其他镜像仓库。