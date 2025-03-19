#!/bin/bash
# 用于测试区块链系统的脚本

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}==== 区块链系统测试脚本 ====${NC}"

# 检查Docker是否运行
echo -e "${YELLOW}检查Docker容器状态...${NC}"
if ! docker ps | grep blockchain_node1 > /dev/null; then
    echo -e "${RED}区块链节点未运行。请先启动系统：docker-compose up -d${NC}"
    exit 1
fi

echo -e "${GREEN}区块链节点正在运行。${NC}"

# 定义节点地址
NODE1="localhost:5001"
NODE2="localhost:5002"

# 功能测试函数
function test_function() {
    local test_name=$1
    local command=$2
    local expected_code=$3
    
    echo -e "${YELLOW}测试 ${test_name}...${NC}"
    
    # 执行命令并捕获响应代码
    response=$(curl -s -o /dev/null -w "%{http_code}" $command)
    
    if [ "$response" -eq "$expected_code" ]; then
        echo -e "${GREEN}✓ ${test_name} 测试通过！${NC}"
        return 0
    else
        echo -e "${RED}✗ ${test_name} 测试失败。预期: ${expected_code}, 实际: ${response}${NC}"
        return 1
    fi
}

function show_function() {
    local name=$1
    local command=$2
    
    echo -e "${YELLOW}${name}:${NC}"
    echo -e "${BLUE}$(curl -s $command | jq .)${NC}"
    echo ""
}

# 测试区块链状态
test_function "区块链状态检查 (节点1)" "-X GET http://${NODE1}/chain" 200
test_function "区块链状态检查 (节点2)" "-X GET http://${NODE2}/chain" 200

# 获取区块链信息
echo -e "${YELLOW}获取区块链信息...${NC}"
node1_chain=$(curl -s http://${NODE1}/chain)
node2_chain=$(curl -s http://${NODE2}/chain)

# 使用jq解析JSON（如果安装了jq）
if command -v jq &> /dev/null; then
    node1_length=$(echo $node1_chain | jq '.length')
    node2_length=$(echo $node2_chain | jq '.length')
    
    echo -e "${GREEN}节点1区块链长度: ${node1_length}${NC}"
    echo -e "${GREEN}节点2区块链长度: ${node2_length}${NC}"
    
    # 检查两个节点的区块链长度是否一致
    if [ "$node1_length" -eq "$node2_length" ]; then
        echo -e "${GREEN}✓ 两个节点的区块链长度一致！${NC}"
    else
        echo -e "${RED}✗ 两个节点的区块链长度不一致。可能存在分叉情况。${NC}"
    fi
else
    echo -e "${YELLOW}未安装jq工具，无法解析JSON响应。建议安装jq以获得更好的输出：${NC}"
    echo -e "${BLUE}apt-get install jq 或 brew install jq${NC}"
    
    # 简单输出原始响应
    echo -e "${BLUE}节点1区块链: ${node1_chain}${NC}"
    echo -e "${BLUE}节点2区块链: ${node2_chain}${NC}"
fi

# 展示系统统计信息
if command -v jq &> /dev/null; then
    echo -e "${YELLOW}展示系统统计信息...${NC}"
    show_function "节点1统计信息" "http://${NODE1}/stats"
fi

# 测试交易创建
echo -e "${YELLOW}您可以使用客户端发送交易，系统将自动创建新交易。${NC}"
echo -e "${YELLOW}观察日志以查看交易处理和区块创建：${NC}"
echo -e "${BLUE}docker-compose logs -f${NC}"

echo -e "${GREEN}测试完成！${NC}"