#!/bin/bash

# Sock Shop JMeter 测试执行脚本

# 默认配置
DEFAULT_HOST="localhost"
DEFAULT_PORT="80"
DEFAULT_PROTOCOL="http"
DEFAULT_THREADS="10"
DEFAULT_RAMP_UP="10"
DEFAULT_LOOP_COUNT="1"
DEFAULT_DURATION="300"

# 获取命令行参数
while getopts ":h:p:P:t:r:l:d:J:f:" opt; do
  case $opt in
    h) HOST="$OPTARG" ;;
    p) PORT="$OPTARG" ;;
    P) PROTOCOL="$OPTARG" ;;
    t) THREADS="$OPTARG" ;;
    r) RAMP_UP="$OPTARG" ;;
    l) LOOP_COUNT="$OPTARG" ;;
    d) DURATION="$OPTARG" ;;
    J) JMETER_HOME="$OPTARG" ;;
    f) TEST_FILE="$OPTARG" ;;
    \?) echo "无效选项: -$OPTARG" >&2; exit 1 ;;
    :) echo "选项 -$OPTARG 需要参数." >&2; exit 1 ;;
  esac
done

# 设置变量，如果命令行没有提供则使用默认值
HOST="${HOST:-$DEFAULT_HOST}"
PORT="${PORT:-$DEFAULT_PORT}"
PROTOCOL="${PROTOCOL:-$DEFAULT_PROTOCOL}"
THREADS="${THREADS:-$DEFAULT_THREADS}"
RAMP_UP="${RAMP_UP:-$DEFAULT_RAMP_UP}"
LOOP_COUNT="${LOOP_COUNT:-$DEFAULT_LOOP_COUNT}"
DURATION="${DURATION:-$DEFAULT_DURATION}"
JMETER_HOME="${JMETER_HOME:-/opt/apache-jmeter}"

# 如果JMETER_HOME不存在，尝试自动查找JMeter
if [ ! -d "$JMETER_HOME" ]; then
  # 尝试几个常见的安装位置
  for path in \
    "/usr/local/apache-jmeter" \
    "/usr/local/jmeter" \
    "/usr/share/jmeter" \
    "$HOME/apache-jmeter"; do
    if [ -d "$path" ]; then
      JMETER_HOME="$path"
      break
    fi
  done
  
  # 如果仍然找不到，检查PATH中是否有jmeter命令
  if [ ! -d "$JMETER_HOME" ] && command -v jmeter >/dev/null 2>&1; then
    JMETER_PATH=$(which jmeter)
    JMETER_HOME=$(dirname $(dirname $JMETER_PATH))
  fi
  
  # 如果仍然找不到，尝试使用当前目录下的jmeter命令
  if [ ! -d "$JMETER_HOME" ] && [ -f "./jmeter" ]; then
    JMETER_HOME="."
  fi
fi

# 测试相关文件
TEST_FILE="${TEST_FILE:-sockshop_test_plan.jmx}"

# 根据测试文件名确定结果目录
TEST_NAME=$(basename "$TEST_FILE" .jmx)
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_DIR="results/${TEST_NAME}_${TIMESTAMP}"
REPORT_DIR="report/${TEST_NAME}_${TIMESTAMP}"
RESULTS_FILE="$RESULTS_DIR/results.jtl"
JMETER_LOG="jmeter_${TEST_NAME}_${TIMESTAMP}.log"

# 确保目录存在
mkdir -p $RESULTS_DIR
mkdir -p $REPORT_DIR

echo "====================== Sock Shop 性能测试 ======================"
echo "主机: $HOST"
echo "端口: $PORT"
echo "协议: $PROTOCOL"
echo "并发用户数: $THREADS"
echo "爬升时间(秒): $RAMP_UP"
echo "循环次数: $LOOP_COUNT"
echo "测试时长(秒): $DURATION"
echo "JMeter路径: $JMETER_HOME"
echo "测试计划: $TEST_FILE"
echo "结果目录: $RESULTS_DIR"
echo "报告目录: $REPORT_DIR"
echo "================================================================"

echo "开始执行测试..."

# 运行JMeter测试
$JMETER_HOME/bin/jmeter -n -t $TEST_FILE \
  -l $RESULTS_FILE \
  -j $JMETER_LOG \
  -e -o $REPORT_DIR \
  -Jhost=$HOST \
  -Jport=$PORT \
  -Jprotocol=$PROTOCOL \
  -Jthreads=$THREADS \
  -Jrampup=$RAMP_UP \
  -Jloopcount=$LOOP_COUNT \
  -Jduration=$DURATION

# 检查JMeter是否成功运行
if [ $? -eq 0 ]; then
  echo "测试完成！HTML报告已生成在: $REPORT_DIR 目录"
  echo "结果文件保存在: $RESULTS_FILE"
  echo "可以使用浏览器打开 $REPORT_DIR/index.html 查看详细报告"
  
  # 创建最新报告的软链接，方便访问
  ln -sf $REPORT_DIR latest_report
  ln -sf $RESULTS_DIR latest_results
  echo "最新报告链接: latest_report/index.html"
else
  echo "测试执行失败！请检查JMeter日志文件: $JMETER_LOG"
  exit 1
fi 