# Online Boutique 混沌工程实验部署指南

## 实验说明

这个混沌工程实验配置将对 online-boutique 应用进行为期 1 小时的故障注入测试，包括：

- **持续时间**: 60 分钟
- **故障类型**: Pod 杀死 (pod-kill)
- **覆盖服务**: 所有 online-boutique 微服务
- **选择器**: 使用 `app` 标签选择目标 pods

## 实验阶段

1. **第一阶段 (8 分钟)**: 杀死 frontend 和 productcatalogservice
2. **第二阶段 (10 分钟)**: 杀死 cartservice、checkoutservice 和 paymentservice
3. **第三阶段 (7 分钟)**: 随机杀死 recommendationservice 和 adservice
4. **第四阶段 (9 分钟)**: 杀死 currencyservice 和 shippingservice
5. **第五阶段 (6 分钟)**: 杀死 emailservice 和 redis-cart
6. **第六阶段 (8 分钟)**: 再次杀死关键服务 (frontend、cartservice、checkoutservice)
7. **第七阶段 (7 分钟)**: 随机杀死 50%的所有 pods
8. **第八阶段 (5 分钟)**: 最后一轮杀死 paymentservice、productcatalogservice 和 recommendationservice

## 部署步骤

### 1. 确保 Chaos Mesh 已安装

```bash
# 检查 Chaos Mesh 是否已安装
kubectl get pods -n chaos-testing

# 如果未安装，请先安装 Chaos Mesh
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm install chaos-mesh chaos-mesh/chaos-mesh -n=chaos-testing --create-namespace
```

### 2. 确保 online-boutique 正在运行

```bash
# 检查 online-boutique 服务状态
kubectl get pods -n online-boutique

# 应该看到所有服务都在运行状态
```

### 3. 部署混沌实验

```bash
# 应用混沌工程配置
kubectl apply -f online-boutique-chaos-workflow.yaml

# 查看实验状态
kubectl get workflow -n chaos-testing

# 查看详细信息
kubectl describe workflow online-boutique-intensive-pod-kill -n chaos-testing
```

### 4. 监控实验进度

```bash
# 实时查看 pod 状态变化
kubectl get pods -n online-boutique -w

# 查看实验日志
kubectl logs -n chaos-testing -l chaos-mesh.org/component=workflow-controller

# 查看被杀死和重启的 pods
kubectl get events -n online-boutique --sort-by='.lastTimestamp'
```

### 5. 收集指标数据

在实验进行期间，可以使用提供的 Python 脚本收集性能指标：

```bash
# 收集故障期间的指标数据
python get_normal.py
```

### 6. 停止实验（如需要）

```bash
# 如果需要提前停止实验
kubectl delete workflow online-boutique-intensive-pod-kill -n chaos-testing
```

## 注意事项

1. **资源消耗**: 这个实验会频繁杀死和重启 pods，请确保集群有足够的资源
2. **服务中断**: 实验期间服务会出现中断，不要在生产环境运行
3. **监控告警**: 建议在实验期间关闭告警，避免误报
4. **数据备份**: 如果有重要数据，请提前备份

## 实验后清理

```bash
# 清理混沌实验资源
kubectl delete workflow online-boutique-intensive-pod-kill -n chaos-testing

# 确保所有 pods 恢复正常
kubectl get pods -n online-boutique

# 如果有 pods 处于异常状态，可以删除让其重建
kubectl delete pods -n online-boutique --field-selector status.phase!=Running
```
