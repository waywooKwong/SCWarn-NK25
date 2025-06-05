# Online Boutique 极高强度故障注入配置

## 概述

`aggressive-pod-kill.yaml` 是专为 Online Boutique 微服务架构设计的**极高强度**故障注入配置文件，参考了 sock-shop 的 aggressive-pod-kill.yaml 结构，实现了每 30 秒一次的频繁 Pod 终止测试。

⚠️ **警告：这是极高强度的故障注入配置，执行频率为 30 秒一次，请谨慎使用！**

## 配置特点

### 🎯 双重故障注入策略

1. **主要故障注入** (`online-boutique-aggressive-kill`)

   - 执行频率：**每 30 秒一次** - 极高强度
   - 执行时长：2.5 分钟
   - 并发执行：多个服务同时进行故障注入

2. **随机全局故障** (`online-boutique-random-chaos`)
   - 执行频率：**每 30 秒一次** - 极高强度
   - 随机杀死 30%的所有 pods
   - 持续时间：2 分钟

### 🎯 服务分类策略

#### 前端服务

- **frontend**: 同时杀死 2 个 pod，45 秒恢复时间

#### 核心业务服务

- **cartservice**: 杀死 60%的 pods，40 秒恢复时间
- **checkoutservice**: 杀死 50%的 pods，35 秒恢复时间
- **paymentservice**: 同时杀死 2 个 pods，50 秒恢复时间
- **productcatalogservice**: 杀死 40%的 pods，45 秒恢复时间
- **recommendationservice**: 杀死 1 个 pod，35 秒恢复时间
- **adservice**: 杀死 1 个 pod，40 秒恢复时间

#### 支撑服务

- **currencyservice**: 杀死 50%的 pods，45 秒恢复时间
- **shippingservice**: 杀死 50%的 pods，40 秒恢复时间
- **emailservice**: 杀死 1 个 pod，35 秒恢复时间

#### 基础设施服务

- **redis-cart**: 杀死 1 个 pod，60 秒恢复时间（谨慎处理数据存储）

## 关键参数说明

### gracePeriod 设置

- **范围**: 35-60 秒
- **目的**: 满足"半分钟内不让 pod 自动恢复"的要求
- **redis 特殊处理**: 60 秒恢复时间，保护数据完整性

### 杀死模式

- **fixed**: 杀死固定数量的 pods
- **fixed-percent**: 杀死指定百分比的 pods
- **random-max-percent**: 随机杀死最多指定百分比的 pods

### 并发策略

- **Parallel**: 多个服务同时执行故障注入
- **concurrencyPolicy: Forbid**: 防止重叠执行

## 使用方法

### 1. 部署配置

```bash
# 应用故障注入配置
kubectl apply -f aggressive-pod-kill.yaml

# 查看调度任务状态
kubectl get schedule -n chaos-testing

# 查看工作流执行历史
kubectl get workflow -n chaos-testing
```

### 2. 监控故障注入

```bash
# 查看当前正在执行的chaos实验
kubectl get podchaos -n chaos-testing

# 查看详细执行日志
kubectl describe schedule online-boutique-aggressive-kill -n chaos-testing
kubectl describe schedule online-boutique-random-chaos -n chaos-testing
```

### 3. 停止故障注入

```bash
# 停止所有故障注入
kubectl delete schedule online-boutique-aggressive-kill -n chaos-testing
kubectl delete schedule online-boutique-random-chaos -n chaos-testing

# 或删除整个配置文件
kubectl delete -f aggressive-pod-kill.yaml
```

## 影响分析

### 极高强度特征

- **超频繁执行**: **每 30 秒一次** - 这是极其频繁的故障注入
- **多 pod 杀死**: 每次实验杀死多个 pods
- **长恢复时间**: 35-60 秒的 gracePeriod
- **双重打击**: 主要故障注入 + 随机全局故障同时进行
- **持续压力**: 几乎无间断的故障模拟

### 测试覆盖

- ✅ 前端服务可用性
- ✅ 核心业务流程韧性
- ✅ 支撑服务稳定性
- ✅ 数据存储容错性
- ✅ 系统整体恢复能力
- ✅ 极限负载下的系统表现

## 注意事项

🚨 **极高强度警告**

1. **生产环境禁用**: 这种 30 秒频率的故障注入**绝对不可在生产环境使用**
2. **资源消耗巨大**: 需要确保集群有充足的 CPU、内存和网络资源
3. **监控必备**: 必须有实时监控和自动告警机制
4. **紧急停止方案**: 准备好立即停止故障注入的应急预案
5. **测试环境专用**: 仅适用于专门的测试环境或混沌工程实验室
6. **持续观察**: 执行期间需要全程监控系统状态
7. **资源预留**: 建议为关键服务预留额外的资源副本

## 与原有配置的区别

| 特性     | online-boutique-chaos-workflow.yaml | aggressive-pod-kill.yaml (30s 版本) |
| -------- | ----------------------------------- | ----------------------------------- |
| 执行方式 | 一次性 Workflow，持续 1 小时        | 定时 Schedule，**每 30 秒执行**     |
| 执行频率 | 单次执行                            | **极高频率: 每 30 秒**              |
| 故障强度 | 序列化执行，相对温和                | 并发执行，**极高强度**              |
| 恢复时间 | 立即恢复(gracePeriod=0)             | 35-60 秒延迟恢复                    |
| 适用场景 | 压力测试                            | **极限混沌工程实验**                |
| 风险等级 | 中等                                | **极高**                            |

## 性能影响评估

### 预期系统表现

- **响应时间**: 可能出现显著波动
- **可用性**: 短时间内可能低于 99%
- **错误率**: 预计会有临时性错误峰值
- **资源使用**: CPU 和内存使用率会大幅上升

### 建议监控指标

- Pod 重启次数和频率
- 服务响应时间和错误率
- 集群资源使用情况
- 网络连接数和延迟

## 扩展建议

可以根据需要调整以下参数：

- 调整 `schedule` 改变执行频率（建议不要低于 30 秒）
- 修改 `value` 改变杀死 pod 数量/百分比
- 调整 `gracePeriod` 改变恢复时间
- 增加新的故障类型（网络、磁盘等）

## 快速降级方案

如果系统无法承受 30 秒频率的故障注入，可以考虑以下降级方案：

```bash
# 方案1: 改为1分钟执行一次
schedule: "0 * * * * *"

# 方案2: 改为2分钟执行一次
schedule: "*/2 * * * *"

# 方案3: 减少pod杀死数量/百分比
value: "1"  # 或更小的百分比
```
