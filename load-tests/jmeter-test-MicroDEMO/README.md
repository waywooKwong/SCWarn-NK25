# 微服务性能测试项目

这个项目包含了用于测试微服务系统性能的JMeter测试计划。

## 测试内容

测试计划通过端口转发访问front-end服务，然后通过front-end服务访问其他微服务的API：

1. 用户服务 (user-service)
   - 获取用户信息 (GET /api/users/{id})

2. 商品服务 (product-service)
   - 获取商品信息 (GET /api/products/{id})

3. 购物车服务 (cart-service)
   - 添加商品到购物车 (POST /api/carts)

4. 订单服务 (order-service)
   - 创建订单 (POST /api/orders)

5. 支付服务 (payment-service)
   - 创建支付 (POST /api/payments)

## 运行要求

- Apache JMeter 5.5或更高版本
- Java 8或更高版本
- 运行中的Minikube集群
- kubectl命令行工具
- 所有微服务都已在Kubernetes中部署并运行

## 如何运行测试

1. 确保所有微服务都已经在Kubernetes中启动：
   ```bash
   kubectl get pods -n micro-demo
   kubectl get svc -n micro-demo
   ```

2. 给运行脚本添加执行权限：
   ```bash
   chmod +x run_test.sh
   ```

3. 运行测试脚本：
   ```bash
   ./run_test.sh
   ```
   
   脚本会自动：
   - 设置端口转发（front-end服务的8080端口转发到本地30080端口）
   - 运行JMeter测试
   - 生成测试报告
   - 清理端口转发

4. 测试完成后，可以在以下位置查看结果：
   - JTL结果文件：`report/result.jtl`
   - HTML报告：`report/html/index.html`

## 测试配置说明

- 用户服务测试：50个线程，循环10次
- 商品服务测试：50个线程，循环10次
- 购物车服务测试：30个线程，循环5次
- 订单服务测试：20个线程，循环5次
- 支付服务测试：20个线程，循环5次

## 注意事项

1. 测试计划通过本地端口转发访问服务，确保端口30080没有被其他程序占用
2. 如果测试过程中遇到连接问题，可以手动检查端口转发是否正常：
   ```bash
   kubectl port-forward service/front-end -n micro-demo 30080:8080
   ```
3. 测试数据使用随机生成的ID，范围在1-10之间
4. 测试报告包含了响应时间、吞吐量等性能指标
5. 如果需要修改测试参数，可以直接编辑`micro_services_test.jmx`文件