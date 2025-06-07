#!/bin/bash

# 检查端口转发是否已经存在
PORT_FORWARD_PID=$(ps aux | grep "kubectl port-forward service/front-end" | grep -v grep | awk '{print $2}')
if [ ! -z "$PORT_FORWARD_PID" ]; then
    echo "关闭已存在的端口转发进程..."
    kill $PORT_FORWARD_PID
fi

# 启动端口转发
echo "启动端口转发..."
kubectl port-forward service/front-end -n micro-demo 30080:8080 &
PORT_FORWARD_PID=$!

# 等待端口转发就绪
echo "等待端口转发就绪..."
sleep 5

# JMeter测试脚本路径
TEST_PLAN="micro_services_test.jmx"
# 测试结果路径
RESULT_DIR="report"
RESULT_FILE="$RESULT_DIR/result.jtl"
# HTML报告路径
HTML_REPORT_DIR="$RESULT_DIR/html"

# 创建结果目录
mkdir -p $RESULT_DIR
mkdir -p $HTML_REPORT_DIR

echo "开始运行JMeter测试..."

# 运行JMeter测试（非GUI模式）
jmeter -n \
       -t $TEST_PLAN \
       -JHOST=localhost \
       -l $RESULT_FILE \
       -e \
       -o $HTML_REPORT_DIR

# 测试完成后关闭端口转发
echo "测试完成，关闭端口转发..."
kill $PORT_FORWARD_PID

echo "测试完成！HTML报告已生成在: $HTML_REPORT_DIR"