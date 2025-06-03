#!/bin/bash

# CartService 测试脚本

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
SERVICE="CartService"
PORT="7070"
NAMESPACE="online-boutique"

# 设置端口转发，带重试机制
setup_port_forward() {
    echo -e "${YELLOW}正在设置端口转发: ${SERVICE} -> localhost:${PORT}${NC}"
    
    # 最大重试次数
    local max_retries=3
    local retry_count=0
    local success=false
    
    while [ $retry_count -lt $max_retries ] && [ "$success" = false ]; do
        kubectl port-forward -n ${NAMESPACE} svc/cartservice ${PORT}:${PORT} &
        PORT_FORWARD_PID=$!
        
        # 等待端口转发建立
        sleep 5
        
        # 检查端口转发是否成功
        if nc -z localhost ${PORT} > /dev/null 2>&1; then
            echo -e "${GREEN}端口转发成功: ${SERVICE} -> localhost:${PORT}${NC}"
            success=true
        else
            retry_count=$((retry_count + 1))
            echo -e "${YELLOW}端口转发失败，尝试第 ${retry_count}/${max_retries} 次重试${NC}"
            kill ${PORT_FORWARD_PID} 2>/dev/null || true
            wait ${PORT_FORWARD_PID} 2>/dev/null || true
            sleep 2
        fi
    done
    
    if [ "$success" = false ]; then
        echo -e "${RED}错误: 多次尝试后仍无法连接到 ${SERVICE} 服务的端口 ${PORT}${NC}"
        return 1
    fi
    
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

# 运行测试函数，带重试机制
run_test() {
    local method=$1
    local data=$2
    local description=$3
    local output_file="${RESULTS_DIR}/${SERVICE}_${method}.html"
    
    echo -e "\n${YELLOW}==== 测试: ${SERVICE}.${method} - ${description} ====${NC}"
    
    # 最大重试次数
    local max_retries=2
    local retry_count=0
    local success=false
    
    while [ $retry_count -lt $max_retries ] && [ "$success" = false ]; do
        ghz --insecure \
            --proto="${PROTO_FILE}" \
            --call="hipstershop.${SERVICE}.${method}" \
            -d "${data}" \
            -n 500 -c 20 -z 30s \
            --connections=5 \
            --timeout=10s \
            --format=html \
            --output="${output_file}" \
            localhost:${PORT}
            
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}测试完成: ${SERVICE}.${method} - 结果保存在 ${output_file}${NC}"
            success=true
        else
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $max_retries ]; then
                echo -e "${YELLOW}测试失败，尝试第 ${retry_count}/${max_retries} 次重试${NC}"
                sleep 5  # 等待一段时间再重试
            else
                echo -e "${RED}测试失败: ${SERVICE}.${method} - 达到最大重试次数${NC}"
            fi
        fi
    done
    
    # 测试之间添加延迟，让服务有时间恢复
    sleep 10
    
    return 0
}

# 主测试流程
main() {
    echo -e "${GREEN}开始 ${SERVICE} 性能测试${NC}"
    
    # 设置端口转发
    setup_port_forward || {
        echo -e "${RED}无法设置端口转发，退出测试${NC}"
        exit 1
    }
    
    # 1. 测试 AddItem 方法
    run_test "AddItem" '{"user_id":"test-user", "item":{"product_id":"OLJCESPC7Z", "quantity":1}}' "添加商品到购物车"
    
    # 2. 测试 GetCart 方法
    run_test "GetCart" '{"user_id":"test-user"}' "获取购物车内容"
    
    # 3. 测试 EmptyCart 方法
    run_test "EmptyCart" '{"user_id":"test-user"}' "清空购物车"
    
    # 4. 测试 GetCart 方法（阶梯式并发）
    echo -e "\n${YELLOW}==== 测试: ${SERVICE}.GetCart - 阶梯式并发 ====${NC}"
    ghz --insecure \
        --proto="${PROTO_FILE}" \
        --call="hipstershop.${SERVICE}.GetCart" \
        -d '{"user_id":"test-user"}' \
        --concurrency-schedule=step \
        --concurrency-start=5 \
        --concurrency-end=50 \
        --concurrency-step=5 \
        --concurrency-step-duration=10s \
        --timeout=10s \
        --format=html \
        --output="${RESULTS_DIR}/${SERVICE}_GetCart_step_concurrency.html" \
        localhost:${PORT}
    
    echo -e "\n${GREEN}${SERVICE} 测试完成！${NC}"
}

# 执行主函数
main 