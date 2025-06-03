#!/bin/bash

# CheckoutService 测试脚本

# 获取输入参数（结果目录）
RESULTS_DIR=${1:-"./results/$(date +%Y%m%d_%H%M%S)"}
mkdir -p "${RESULTS_DIR}"

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROTO_FILE="${SCRIPT_DIR}/../../protos/demo.proto"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 服务设置
SERVICE="CheckoutService"
PORT="5050"
NAMESPACE="online-boutique"

# 设置端口转发
setup_port_forward() {
    echo -e "${YELLOW}正在设置端口转发: ${SERVICE} -> localhost:${PORT}${NC}"
    kubectl port-forward -n ${NAMESPACE} svc/checkoutservice ${PORT}:${PORT} &
    PORT_FORWARD_PID=$!
    
    # 等待端口转发建立
    sleep 3
    
    # 检查端口转发是否成功
    if ! nc -z localhost ${PORT} > /dev/null 2>&1; then
        echo -e "${RED}错误: 无法连接到 ${SERVICE} 服务的端口 ${PORT}${NC}"
        return 1
    fi
    
    echo -e "${GREEN}端口转发成功: ${SERVICE} -> localhost:${PORT}${NC}"
    return 0
}

# 停止端口转发
stop_port_forward() {
    if [ ! -z "${PORT_FORWARD_PID}" ]; then
        echo -e "${YELLOW}停止端口转发 (PID: ${PORT_FORWARD_PID})${NC}"
        kill ${PORT_FORWARD_PID} 2>/dev/null || true
        wait ${PORT_FORWARD_PID} 2>/dev/null || true
        PORT_FORWARD_PID=""
    fi
}

# 清理函数
cleanup() {
    echo -e "${YELLOW}正在清理...${NC}"
    stop_port_forward
    echo -e "${GREEN}清理完成${NC}"
}

# 捕获退出信号
trap cleanup EXIT INT TERM

# 运行测试函数
run_test() {
    local method=$1
    local data=$2
    local description=$3
    local output_file="${RESULTS_DIR}/${SERVICE}_${method}.html"
    
    echo -e "\n${YELLOW}==== 测试: ${SERVICE}.${method} - ${description} ====${NC}"
    
    ghz --insecure \
        --proto="${PROTO_FILE}" \
        --call="hipstershop.${SERVICE}.${method}" \
        -d "${data}" \
        -n 500 -c 20 -z 30s \
        --connections=5 \
        --format=html \
        --output="${output_file}" \
        localhost:${PORT}
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}测试完成: ${SERVICE}.${method} - 结果保存在 ${output_file}${NC}"
        return 0
    else
        echo -e "${RED}测试失败: ${SERVICE}.${method}${NC}"
        return 1
    fi
}

# 主测试流程
main() {
    echo -e "${GREEN}开始 ${SERVICE} 性能测试${NC}"
    
    # 设置端口转发
    setup_port_forward || {
        echo -e "${RED}无法设置端口转发，退出测试${NC}"
        exit 1
    }
    
    # 请求数据
    ADDRESS_DATA='{"street_address":"1600 Amphitheatre Parkway", "city":"Mountain View", "state":"CA", "country":"USA", "zip_code":94043}'
    CREDIT_CARD_DATA='{"credit_card_number":"4432-8015-6152-0454", "credit_card_cvv":672, "credit_card_expiration_year":2024, "credit_card_expiration_month":1}'
    
    # 测试 PlaceOrder 方法 - 标准订单
    run_test "PlaceOrder" "{\"user_id\":\"test-user\", \"user_currency\":\"USD\", \"address\":${ADDRESS_DATA}, \"email\":\"someone@example.com\", \"credit_card\":${CREDIT_CARD_DATA}}" "标准订单结账"
    
    # 测试 PlaceOrder 方法 - 使用欧元
    run_test "PlaceOrder" "{\"user_id\":\"test-user\", \"user_currency\":\"EUR\", \"address\":${ADDRESS_DATA}, \"email\":\"someone@example.com\", \"credit_card\":${CREDIT_CARD_DATA}}" "欧元订单结账"
    
    # 测试 PlaceOrder 方法 - 递增并发
    echo -e "\n${YELLOW}==== 测试: ${SERVICE}.PlaceOrder - 递增并发 ====${NC}"
    ghz --insecure \
        --proto="${PROTO_FILE}" \
        --call="hipstershop.${SERVICE}.PlaceOrder" \
        -d "{\"user_id\":\"test-user\", \"user_currency\":\"USD\", \"address\":${ADDRESS_DATA}, \"email\":\"someone@example.com\", \"credit_card\":${CREDIT_CARD_DATA}}" \
        --concurrency-schedule=line \
        --concurrency-start=5 \
        --concurrency-end=50 \
        --concurrency-step=5 \
        --concurrency-max-duration=2m \
        --format=html \
        --output="${RESULTS_DIR}/${SERVICE}_PlaceOrder_incremental_concurrency.html" \
        localhost:${PORT}
    
    echo -e "\n${GREEN}${SERVICE} 测试完成！${NC}"
}

# 执行主函数
main 