# Online Boutique 微服务 gRPC 性能测试框架

本框架用于对 Online Boutique 微服务应用进行 gRPC 性能测试，使用 ghz 工具生成负载并收集关键性能指标。

## 为什么不使用 JMeter？

JMeter 是一个流行的性能测试工具，但它在测试 gRPC 服务时存在一些局限性：

1. **HTTP/2 支持问题**：JMeter 主要支持 HTTP/1.1，而 gRPC 基于 HTTP/2。虽然有一些插件可以让 JMeter 支持 HTTP/2，但它们并不成熟或易用。

2. **Protobuf 序列化**：gRPC 使用 Protobuf 进行序列化/反序列化，JMeter 原生不支持这种格式。

3. **流式通信**：gRPC 支持流式通信（服务器流、客户端流和双向流），JMeter 难以模拟这些场景。

4. **高并发场景**：JMeter 在高并发场景下可能需要更多资源，而专用的 gRPC 测试工具如 ghz 更加高效。

相比之下，ghz 是专为 gRPC 性能测试设计的工具，提供了：
- 原生支持 HTTP/2 和 Protobuf
- 直接支持各种 gRPC 调用类型
- 简单易用的命令行接口
- 丰富的测试报告和指标

## 测试框架特点

- 支持测试多种微服务（产品目录、购物车、推荐、配送、支付、结账）
- 提供多种测试模式（标准请求-响应、递增负载、阶梯式并发、异步请求）
- 自动生成 HTML 格式的测试报告
- 内置错误处理和重试机制
- 服务健康状态检查

## 前提条件

### 公共前提条件
- 已部署 Online Boutique 微服务应用（在 Kubernetes 集群中）
- 已安装 kubectl 并配置访问权限
- 熟悉基本的命令行操作

### macOS 环境
1. 安装 Homebrew（如果尚未安装）:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. 安装 ghz:
   ```bash
   brew install ghz
   ```

3. 安装 netcat (用于端口检查):
   ```bash
   brew install netcat
   ```

### Windows 环境
1. 使用 [Scoop](https://scoop.sh/) 安装 ghz:
   ```powershell
   # 安装 Scoop (如果尚未安装)
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   irm get.scoop.sh | iex

   # 安装 ghz
   scoop install ghz
   ```

2. 或者从 [ghz 发布页面](https://github.com/bojand/ghz/releases) 下载预编译二进制文件并添加到 PATH

3. 安装 Netcat for Windows:
   ```powershell
   scoop install netcat
   ```

## 目录结构

```
ghz-tests/
├── configs/         # 测试配置文件
├── scripts/         # 服务测试脚本
├── results/         # 测试结果存放目录
├── run_all_tests.sh # 主测试脚本 (Mac/Linux)
├── run_all_tests.bat # 主测试脚本 (Windows)
└── README.md        # 文档
```

## 使用指南

### 运行测试 (macOS/Linux)

1. 确保 Online Boutique 已部署到 Kubernetes 集群中:
   ```bash
   kubectl get pods -n online-boutique
   ```

2. 克隆本仓库（如果尚未克隆）:
   ```bash
   git clone https://github.com/yourusername/microservices-demo.git
   cd microservices-demo
   ```

3. 确保测试脚本有执行权限:
   ```bash
   chmod +x ghz-tests/run_all_tests.sh
   chmod +x ghz-tests/scripts/*.sh
   ```

4. 运行测试:
   ```bash
   cd ghz-tests
   ./run_all_tests.sh
   ```

5. 查看测试结果，在 `results/YYYYMMDD_HHMMSS/` 目录下的 `summary.html` 文件提供了结果摘要。

### 运行测试 (Windows)

1. 确保 Online Boutique 已部署到 Kubernetes 集群中:
   ```powershell
   kubectl get pods -n online-boutique
   ```

2. 克隆本仓库（如果尚未克隆）:
   ```powershell
   git clone git@github.com:waywooKwong/SCWarn-NK25.git
   cd ghz-tests
   ```

3. 运行测试 (使用 Git Bash 或转换脚本为 .bat 文件):
   ```powershell
   bash run_all_tests.sh
   # 或使用预先准备的 Windows 批处理文件
   # run_all_tests.bat
   ```

4. 查看测试结果，在 `results/YYYYMMDD_HHMMSS/` 目录下的 `summary.html` 文件提供了结果摘要。

## 自定义测试参数

### 修改并发量和请求数

1. **通过配置文件修改（推荐）**:
   
   编辑 `configs/` 目录下对应服务的配置文件，例如 `CartService_GetCart.json`:

   ```json
   {
     "proto": "../protos/demo.proto",
     "call": "hipstershop.CartService.GetCart",
     "total": 500,         // 总请求数，可根据需要修改
     "concurrency": 20,    // 并发请求数，根据系统性能调整
     "data": {
       "user_id": "test-user"
     },
     "metadata": {
       "trace-id": "{{.RequestNumber}}",
       "timestamp": "{{.TimestampUnixNano}}"
     },
     "insecure": true,
     "connections": 5,     // 连接数，通常设置为并发数的1/4或1/5
     "duration": "30s",    // 测试持续时间
     "timeout": "10s",     // 请求超时时间
     "host": "localhost:7070"
   }
   ```

2. **直接修改测试脚本**:

   如果需要修改没有配置文件的测试，可以编辑 `scripts/` 目录下对应的脚本文件，寻找类似以下代码:

   ```bash
   ghz --insecure \
       --proto="${PROTO_FILE}" \
       --call="hipstershop.${SERVICE}.${method}" \
       -d "${data}" \
       -n 500 -c 20 -z 30s \  # 修改这里的参数
       --connections=5 \      # 修改连接数
       --timeout=10s \        # 修改超时时间
       --format=html \
       --output="${output_file}" \
       localhost:${PORT}
   ```

3. **修改主测试脚本中的默认值**:

   编辑 `run_all_tests.sh` (macOS/Linux) 或 `run_all_tests.bat` (Windows) 中的默认测试参数。

### 添加新服务测试

1. 创建新的测试脚本:
   
   复制现有脚本作为模板，例如:

   ```bash
   cp scripts/01_productcatalog_test.sh scripts/07_newservice_test.sh
   ```

2. 修改新脚本中的服务名称、端口和测试方法。

3. 创建对应的配置文件（可选）:

   ```bash
   touch configs/NewService_Method.json
   ```

4. 编辑配置文件内容，设置适当的测试参数。

## 常用测试模式

1. **标准请求-响应测试**:
   - 固定数量的请求和并发度
   - 适合测试服务的基本性能

2. **递增负载测试**:
   - 从低请求率逐步增加到高请求率
   - 适合找出系统的性能拐点

3. **阶梯式并发测试**:
   - 按步骤增加并发数
   - 适合测试系统在不同并发度下的表现

4. **短时间高并发测试**:
   - 短时间内发送大量请求
   - 适合测试系统的突发负载处理能力

5. **RPS限制测试**:
   - 限制每秒请求数
   - 适合模拟稳定流量场景

## 测试结果解读

测试报告会生成HTML格式，包含以下关键指标:

1. **吞吐量 (Throughput)**:
   - RPS (每秒请求数)
   - 总请求数

2. **延迟 (Latency)**:
   - 平均响应时间
   - 百分位响应时间 (p50, p90, p95, p99)
   - 最小/最大响应时间

3. **错误率**:
   - 成功/失败请求数
   - 错误类型分布

当看到大量 "unavailable" 错误时，可能的原因包括:
- 服务资源不足 (CPU/内存限制)
- 网络连接问题
- 并发量设置过高
- 服务依赖链中的故障

## 优化建议

如果测试中遇到大量错误，可尝试以下优化:

1. **降低并发量**:
   - 将并发请求数从50降低到20
   - 将总请求数从1000降低到500
   - 将连接数从10降低到5

2. **增加超时时间**:
   - 将请求超时从5秒增加到10秒

3. **增加服务资源**:
   - 增加Pod的CPU和内存限制
   - 增加服务副本数

4. **使用重试机制**:
   - 测试框架已内置重试机制，可根据需要调整重试次数

## 故障排除

### macOS/Linux

1. **ghz未安装**:
   ```bash
   # 检查ghz是否安装
   which ghz
   
   # 安装ghz
   brew install ghz
   ```

2. **端口转发失败**:
   ```bash
   # 检查端口是否被占用
   lsof -i :<PORT>
   
   # 检查服务是否运行
   kubectl get pods -n online-boutique
   ```

3. **测试脚本无执行权限**:
   ```bash
   chmod +x run_all_tests.sh
   chmod +x scripts/*.sh
   ```

### Windows

1. **ghz未安装或不在PATH中**:
   ```powershell
   # 检查ghz是否在PATH中
   where ghz
   
   # 使用Scoop安装
   scoop install ghz
   ```

2. **端口转发失败**:
   ```powershell
   # 检查端口是否被占用
   netstat -ano | findstr :<PORT>
   
   # 检查服务是否运行
   kubectl get pods -n online-boutique
   ```

3. **脚本运行失败**:
   - 确保使用Git Bash运行脚本
   - 或者将脚本转换为Windows批处理文件

## 结论

本测试框架提供了一种简单而强大的方式来测试gRPC微服务的性能。相比JMeter，它专为gRPC设计，能更准确地评估服务在各种负载条件下的表现。

通过调整测试参数，可以找出系统的性能瓶颈和最佳配置，确保微服务架构能够满足实际业务需求。 