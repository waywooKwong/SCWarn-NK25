#!/bin/bash

# Online Boutique gRPC 性能测试主脚本
# 此脚本将运行对所有微服务的性能测试，并生成测试报告

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 基础设置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROTO_FILE="${SCRIPT_DIR}/../protos/demo.proto"
CONFIG_DIR="${SCRIPT_DIR}/configs"
SCRIPTS_DIR="${SCRIPT_DIR}/scripts"
RESULTS_DIR="${SCRIPT_DIR}/results/$(date +%Y%m%d_%H%M%S)"

# 创建结果目录
mkdir -p "${RESULTS_DIR}"
echo -e "${GREEN}测试结果将保存在: ${RESULTS_DIR}${NC}"

# 日志文件
LOG_FILE="${RESULTS_DIR}/test_log.txt"
touch "${LOG_FILE}"

# 记录系统信息
echo "===== 系统信息 =====" | tee -a "${LOG_FILE}"
echo "日期: $(date)" | tee -a "${LOG_FILE}"
echo "主机名: $(hostname)" | tee -a "${LOG_FILE}"
echo "================" | tee -a "${LOG_FILE}"

# 检查ghz是否已安装
if ! command -v ghz &> /dev/null; then
    echo -e "${RED}错误: ghz 未安装. 请先安装ghz工具.${NC}" | tee -a "${LOG_FILE}"
    echo "可以使用以下命令安装: brew install ghz" | tee -a "${LOG_FILE}"
    exit 1
fi

# 检查proto文件是否存在
if [ ! -f "${PROTO_FILE}" ]; then
    echo -e "${RED}错误: proto文件不存在: ${PROTO_FILE}${NC}" | tee -a "${LOG_FILE}"
    exit 1
fi

# 检查kubectl是否已安装
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}错误: kubectl 未安装. 请先安装kubectl工具.${NC}" | tee -a "${LOG_FILE}"
    exit 1
fi

# 检查k8s集群是否可访问
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}错误: 无法访问Kubernetes集群. 请确保您已连接到集群.${NC}" | tee -a "${LOG_FILE}"
    exit 1
fi

# 检查online-boutique命名空间是否存在
if ! kubectl get namespace online-boutique &> /dev/null; then
    echo -e "${RED}错误: online-boutique 命名空间不存在.${NC}" | tee -a "${LOG_FILE}"
    exit 1
fi

# 检查服务健康状态
check_service_health() {
    local namespace="online-boutique"
    local service=$1
    
    echo -e "${YELLOW}检查服务健康状态: ${service}${NC}" | tee -a "${LOG_FILE}"
    
    # 检查服务是否存在
    if ! kubectl get svc -n ${namespace} ${service} &> /dev/null; then
        echo -e "${RED}错误: 服务 ${service} 不存在${NC}" | tee -a "${LOG_FILE}"
        return 1
    fi
    
    # 检查相关的Pod是否正常运行
    local pod_selector=$(kubectl get svc -n ${namespace} ${service} -o jsonpath='{.spec.selector}' | sed 's/{//g' | sed 's/}//g' | sed 's/:/=/g')
    local pod_status=$(kubectl get pods -n ${namespace} -l ${pod_selector} -o jsonpath='{.items[0].status.phase}' 2>/dev/null)
    
    if [ "$pod_status" != "Running" ]; then
        echo -e "${RED}错误: 服务 ${service} 的Pod不在运行状态 (当前状态: ${pod_status:-Unknown})${NC}" | tee -a "${LOG_FILE}"
        return 1
    fi
    
    echo -e "${GREEN}服务 ${service} 健康状态正常${NC}" | tee -a "${LOG_FILE}"
    return 0
}

# 设置端口转发函数，带有重试机制
setup_port_forward() {
    local service=$1
    local port=$2
    local namespace="online-boutique"
    
    echo -e "${YELLOW}正在设置端口转发: ${service} -> localhost:${port}${NC}" | tee -a "${LOG_FILE}"
    
    # 最大重试次数
    local max_retries=3
    local retry_count=0
    local success=false
    
    while [ $retry_count -lt $max_retries ] && [ "$success" = false ]; do
        kubectl port-forward -n ${namespace} svc/${service} ${port}:${port} &
        PORT_FORWARD_PID=$!
        
        # 等待端口转发建立
        sleep 5
        
        # 检查端口转发是否成功
        if nc -z localhost ${port} > /dev/null 2>&1; then
            echo -e "${GREEN}端口转发成功: ${service} -> localhost:${port}${NC}" | tee -a "${LOG_FILE}"
            success=true
        else
            retry_count=$((retry_count + 1))
            echo -e "${YELLOW}端口转发失败，尝试第 ${retry_count}/${max_retries} 次重试${NC}" | tee -a "${LOG_FILE}"
            kill ${PORT_FORWARD_PID} 2>/dev/null || true
            wait ${PORT_FORWARD_PID} 2>/dev/null || true
            sleep 3
        fi
    done
    
    if [ "$success" = false ]; then
        echo -e "${RED}错误: 多次尝试后仍无法连接到 ${service} 服务的端口 ${port}${NC}" | tee -a "${LOG_FILE}"
        return 1
    fi
    
    return 0
}

# 停止端口转发
stop_port_forward() {
    if [ ! -z "${PORT_FORWARD_PID}" ]; then
        echo -e "${YELLOW}停止端口转发 (PID: ${PORT_FORWARD_PID})${NC}" | tee -a "${LOG_FILE}"
        kill ${PORT_FORWARD_PID} 2>/dev/null || true
        wait ${PORT_FORWARD_PID} 2>/dev/null || true
        PORT_FORWARD_PID=""
    fi
}

# 清理函数
cleanup() {
    echo -e "${YELLOW}正在清理...${NC}" | tee -a "${LOG_FILE}"
    stop_port_forward
    echo -e "${GREEN}清理完成${NC}" | tee -a "${LOG_FILE}"
}

# 捕获退出信号
trap cleanup EXIT INT TERM

# 运行测试函数，带有重试机制
run_test() {
    local service=$1
    local method=$2
    local port=$3
    local data=$4
    local output_file="${RESULTS_DIR}/${service}_${method}.html"
    local config_file="${CONFIG_DIR}/${service}_${method}.json"
    
    echo -e "\n${YELLOW}==== 测试: ${service}.${method} ====${NC}" | tee -a "${LOG_FILE}"
    
    # 最大重试次数
    local max_retries=2
    local retry_count=0
    local success=false
    
    while [ $retry_count -lt $max_retries ] && [ "$success" = false ]; do
        # 如果存在配置文件，则使用配置文件
        if [ -f "${config_file}" ]; then
            echo -e "${GREEN}使用配置文件: ${config_file}${NC}" | tee -a "${LOG_FILE}"
            ghz --config="${config_file}" --insecure --proto="${PROTO_FILE}" --format=html --output="${output_file}" localhost:${port} | tee -a "${LOG_FILE}"
        else
            echo -e "${GREEN}执行测试: ${service}.${method}${NC}" | tee -a "${LOG_FILE}"
            ghz --insecure \
                --proto="${PROTO_FILE}" \
                --call="hipstershop.${service}.${method}" \
                -d "${data}" \
                -n 500 -c 20 -z 30s \
                --connections=5 \
                --timeout=10s \
                --format=html \
                --output="${output_file}" \
                localhost:${port} | tee -a "${LOG_FILE}"
        fi
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}测试完成: ${service}.${method} - 结果保存在 ${output_file}${NC}" | tee -a "${LOG_FILE}"
            success=true
        else
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $max_retries ]; then
                echo -e "${YELLOW}测试失败，尝试第 ${retry_count}/${max_retries} 次重试${NC}" | tee -a "${LOG_FILE}"
                sleep 5  # 等待一段时间再重试
            else
                echo -e "${RED}测试失败: ${service}.${method} - 达到最大重试次数${NC}" | tee -a "${LOG_FILE}"
            fi
        fi
    done
    
    # 测试之间添加延迟，让服务有时间恢复
    sleep 10
    
    return 0
}

# 运行所有单独测试脚本
run_all_test_scripts() {
    echo -e "\n${YELLOW}==== 运行所有测试脚本 ====${NC}" | tee -a "${LOG_FILE}"
    
    # 按顺序运行脚本，以避免并发资源冲突
    for script in "${SCRIPTS_DIR}"/*.sh; do
        if [ -f "${script}" ]; then
            echo -e "${GREEN}运行脚本: ${script}${NC}" | tee -a "${LOG_FILE}"
            bash "${script}" "${RESULTS_DIR}" | tee -a "${LOG_FILE}"
            
            # 在测试脚本之间添加一些延迟，让系统恢复
            echo -e "${YELLOW}等待系统恢复 (15秒)...${NC}" | tee -a "${LOG_FILE}"
            sleep 15
        fi
    done
}

# 创建测试结果摘要
create_summary() {
    local summary_file="${RESULTS_DIR}/summary.html"
    
    echo -e "\n${YELLOW}==== 创建测试摘要 ====${NC}" | tee -a "${LOG_FILE}"
    
    # 创建简单的HTML摘要
    cat > "${summary_file}" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Online Boutique gRPC 性能测试结果</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1, h2 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:hover { background-color: #f5f5f5; }
        .success { color: green; }
        .failure { color: red; }
    </style>
</head>
<body>
    <h1>Online Boutique gRPC 性能测试结果</h1>
    <p>测试时间: $(date)</p>
    
    <h2>测试结果文件</h2>
    <table>
        <tr>
            <th>服务</th>
            <th>方法</th>
            <th>结果文件</th>
        </tr>
EOF

    # 添加每个测试结果文件的链接
    for result_file in "${RESULTS_DIR}"/*.html; do
        if [ "${result_file}" != "${summary_file}" ]; then
            filename=$(basename "${result_file}")
            # 从文件名提取服务和方法
            service=$(echo "${filename}" | cut -d'_' -f1)
            method=$(echo "${filename}" | cut -d'_' -f2 | sed 's/\.html//')
            
            echo "        <tr>" >> "${summary_file}"
            echo "            <td>${service}</td>" >> "${summary_file}"
            echo "            <td>${method}</td>" >> "${summary_file}"
            echo "            <td><a href=\"${filename}\">${filename}</a></td>" >> "${summary_file}"
            echo "        </tr>" >> "${summary_file}"
        fi
    done

    echo "    </table>" >> "${summary_file}"
    
    # 添加测试日志
    echo "    <h2>测试日志</h2>" >> "${summary_file}"
    echo "    <pre>" >> "${summary_file}"
    cat "${LOG_FILE}" >> "${summary_file}"
    echo "    </pre>" >> "${summary_file}"
    
    echo "</body>" >> "${summary_file}"
    echo "</html>" >> "${summary_file}"
    
    echo -e "${GREEN}测试摘要已创建: ${summary_file}${NC}" | tee -a "${LOG_FILE}"
}

# 主测试流程
main() {
    echo -e "${GREEN}开始 Online Boutique 微服务 gRPC 性能测试${NC}" | tee -a "${LOG_FILE}"
    
    # 检查关键服务的健康状态
    echo -e "\n${YELLOW}==== 检查服务健康状态 ====${NC}" | tee -a "${LOG_FILE}"
    local services=("productcatalogservice" "cartservice" "recommendationservice" "shippingservice" "checkoutservice" "paymentservice")
    local all_healthy=true
    
    for service in "${services[@]}"; do
        if ! check_service_health "${service}"; then
            all_healthy=false
        fi
    done
    
    if [ "$all_healthy" = false ]; then
        echo -e "\n${YELLOW}警告: 某些服务可能不健康，测试结果可能不准确${NC}" | tee -a "${LOG_FILE}"
        echo -e "${YELLOW}是否继续测试? (y/n) ${NC}"
        read -r continue_testing
        
        if [[ ! "$continue_testing" =~ ^[Yy]$ ]]; then
            echo -e "${RED}测试已取消${NC}" | tee -a "${LOG_FILE}"
            exit 1
        fi
    fi
    
    # 运行所有测试脚本
    run_all_test_scripts
    
    # 创建测试摘要
    create_summary
    
    echo -e "\n${GREEN}所有测试已完成！${NC}" | tee -a "${LOG_FILE}"
    echo -e "${GREEN}测试结果目录: ${RESULTS_DIR}${NC}" | tee -a "${LOG_FILE}"
    echo -e "${GREEN}测试摘要: ${RESULTS_DIR}/summary.html${NC}" | tee -a "${LOG_FILE}"
}

# 执行主函数
main 