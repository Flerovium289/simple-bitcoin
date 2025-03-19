# 简易比特币系统

基于比特币原理的简化区块链实现，包含挖矿、区块验证、交易处理、分叉解决等核心功能。

## 功能特点

- 使用账户模型（而非UTXO模型）记录余额
- 实现工作量证明（PoW）挖矿机制
- 支持区块和交易验证
- 实现数字签名和公钥加密
- 使用最长链原则解决分叉
- 通过Docker实现多节点模拟

## 项目结构

```
simple-bitcoin/
├── blockchain_node/          # 区块链节点代码
│   ├── main.py               # 主程序 
│   └── miner.py              # 挖矿程序
├── client_node/              # 客户端节点代码  
│   └── client.py             # 客户端，用于生成交易
├── Dockerfile.node           # 区块链节点的Dockerfile
├── Dockerfile.client         # 客户端的Dockerfile
├── docker-compose.yml        # Docker Compose配置文件
├── requirements.txt          # Python依赖
├── install.sh                # 安装脚本
├── test.sh                   # 测试脚本
└── visualize.py              # 区块链可视化脚本
```

## 系统组件

1. **区块链节点**:
   - 维护区块链和账户余额
   - 处理和验证交易
   - 打包和验证区块
   - 处理区块链分叉

2. **挖矿程序**:
   - 寻找符合难度要求的nonce
   - 将挖矿结果发送给主程序

3. **客户端**:
   - 生成随机交易
   - 将交易发送给区块链节点

## 快速开始

### 前提条件

- Docker 和 Docker Compose
- Python 3.9+ (如果不使用Docker)

### 使用Docker运行

1. 克隆或下载项目:

```bash
git clone https://github.com/yourusername/simple-bitcoin.git
cd simple-bitcoin
```

2. 运行安装脚本:

```bash
bash install.sh
```

3. 启动系统:

```bash
docker-compose up --build
```

4. 在另一个终端窗口运行测试脚本:

```bash
bash test.sh
```

### 监控和可视化

1. 查看日志:

```bash
docker-compose logs -f
```

2. 通过API查看系统状态:

```bash
curl http://localhost:5001/stats | jq .
```

3. 生成可视化图表:

```bash
python visualize.py
```

## API端点

- `POST /transactions/new`: 提交新交易
- `POST /blocks/new`: 提交新区块
- `GET /chain`: 获取完整区块链
- `GET /balance/<address>`: 获取账户余额
- `GET /stats`: 获取系统统计信息

## 分叉检测和解决

当两个节点几乎同时挖出区块时，系统可能产生分叉。我们使用最长链原则解决分叉问题：

1. 检测到区块的前一个hash与当前链末端不匹配时，识别潜在分叉
2. 比较分叉链与当前链的长度
3. 如果分叉链更长，则切换到分叉链

## 自定义配置

您可以通过修改docker-compose.yml中的环境变量来调整系统参数:

```yaml
environment:
  - MINING_DIFFICULTY=3    # 挖矿难度
  - TRANSACTION_INTERVAL=0.1  # 交易生成间隔(秒)
  - LOG_LEVEL=INFO         # 日志级别
```

## 详细文档

- [系统使用指南](usage-guide.md) - 详细的使用和观察指南
- [安装说明](setup-instructions.md) - 安装和运行说明

## 参考资料

- [比特币白皮书](https://bitcoin.org/bitcoin.pdf)
- [哈希函数和数字签名](https://en.wikipedia.org/wiki/Cryptographic_hash_function)
- [区块链工作原理](https://en.wikipedia.org/wiki/Blockchain)