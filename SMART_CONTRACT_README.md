# 智能合约扩展实现

本文档提供关于实验二"智能合约"扩展功能的详细说明。该实现在原有区块链系统的基础上添加了智能合约支持。

## 功能特点

1. **智能合约支持**：
   - 部署合约
   - 调用合约
   - 合约状态管理

2. **交易类型扩展**：
   - 转账交易（原有）
   - 部署合约交易（新增）
   - 调用合约交易（新增）

3. **实现的合约类型**：
   - 转账合约：支持存款、取款和查询余额功能
   - 拍卖合约：支持竞价、查询状态和结束拍卖功能

## 系统架构

系统架构扩展了以下组件：

1. **智能合约模块**：
   - `smart_contract.py`：处理合约部署、执行和状态管理

2. **区块链节点扩展**：
   - `main.py`：添加了处理合约交易的功能

3. **合约测试客户端**：
   - `contract_client.py`：用于测试合约部署和调用

## 实现详情

### 合约部署和执行流程

1. **合约部署**：
   - 客户端创建部署合约交易
   - 区块链节点验证并预执行合约代码
   - 合约成功编译后生成唯一合约ID
   - 交易在区块中确认后，合约被正式部署

2. **合约调用**：
   - 客户端创建调用合约交易，指定合约ID、函数名和参数
   - 区块链节点验证并预执行合约函数
   - 执行结果记录在交易中
   - 交易在区块中确认后，合约状态被更新

3. **区块验证**：
   - 对于包含合约交易的区块，除了验证签名外，还会重新执行合约代码
   - 比对本地执行结果与区块中记录的结果
   - 如果结果不匹配，则拒绝该区块

### 合约环境和接口

合约使用Python语法编写，并提供以下接口：

- `get_state(key)`: 获取合约状态
- `set_state(key, value)`: 设置合约状态
- `contract_id`: 合约ID
- `caller`: 调用者地址
- `args`: 调用参数

### 转账合约示例

```python
def init():
    set_state('balance', 0)
    return "Transfer contract initialized"

def deposit():
    current_balance = get_state('balance') or 0
    new_balance = current_balance + args.get('amount', 0)
    set_state('balance', new_balance)
    return f"Deposited {args.get('amount', 0)}, new balance: {new_balance}"

def withdraw():
    current_balance = get_state('balance') or 0
    amount = args.get('amount', 0)
    
    if amount > current_balance:
        raise Exception("Insufficient balance")
    
    new_balance = current_balance - amount
    set_state('balance', new_balance)
    return f"Withdrawn {amount}, new balance: {new_balance}"

def get_balance():
    return get_state('balance') or 0
```

### 拍卖合约示例

```python
def init():
    set_state('highest_bid', 0)
    set_state('highest_bidder', '')
    set_state('end_time', args.get('duration', 3600) + time.time())
    set_state('owner', caller)
    set_state('item_description', args.get('description', 'No description'))
    set_state('closed', False)
    return "Auction initialized"

def bid():
    if get_state('closed'):
        raise Exception("Auction is closed")
    
    current_highest = get_state('highest_bid')
    bid_amount = args.get('amount', 0)
    
    if bid_amount <= current_highest:
        raise Exception(f"Bid must be higher than current highest bid: {current_highest}")
    
    set_state('highest_bid', bid_amount)
    set_state('highest_bidder', caller)
    return f"New highest bid: {bid_amount} by {caller}"

def end_auction():
    if caller != get_state('owner'):
        raise Exception("Only the owner can end the auction")
    
    set_state('closed', True)
    return f"Auction ended. Winner: {get_state('highest_bidder')}, Amount: {get_state('highest_bid')}"

def get_status():
    return {
        'highest_bid': get_state('highest_bid'),
        'highest_bidder': get_state('highest_bidder'),
        'owner': get_state('owner'),
        'closed': get_state('closed')
    }
```

## 测试与演示

系统提供了一个专门的测试客户端 `contract_client.py`，用于演示合约功能。

### 测试内容

1. **转账合约测试**：
   - 部署合约
   - 初始化合约
   - 存款操作
   - 查询余额
   - 取款操作

2. **拍卖合约测试**：
   - 部署合约
   - 初始化拍卖
   - 多方竞价
   - 查询拍卖状态
   - 结束拍卖

3. **错误处理测试**：
   - 部署语法错误的合约
   - 调用会产生运行时错误的合约
   - 测试交易验证和区块验证对错误的处理

### 运行测试

可以使用Docker Compose运行整个系统：

```bash
docker-compose up --build
```

测试合约功能：

```bash
docker-compose up contract_tester
```

## API接口

系统提供了以下API接口用于智能合约操作：

### 部署合约

```
POST /contracts/deploy
{
    "from": "发送者地址",
    "code": "合约代码",
    "signature": "签名"
}
```

### 调用合约

```
POST /contracts/call
{
    "from": "调用者地址",
    "contract_id": "合约ID",
    "function": "函数名",
    "args": {
        "参数1": "值1",
        "参数2": "值2"
    },
    "signature": "签名"
}
```

### 查询合约信息

```
GET /contracts/<contract_id>
```

## 注意事项

1. 合约代码在部署和执行时会在区块链节点上动态执行，请确保代码安全。
2. 合约状态在所有节点上必须保持一致，这是通过区块中记录执行结果并在验证时比对实现的。
3. 在实际生产环境中，应使用沙箱或其他安全机制限制合约执行的权限和资源。
4. 合约ID是根据代码内容、部署者地址和时间戳生成的唯一标识。