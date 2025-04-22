# blockchain_node/smart_contract.py
"""
Smart contract module for the blockchain system
This module handles contract deployment, execution, and state management
"""

import json
import hashlib
import logging
import random
import time
import os
import threading
import pickle

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('smart_contract')

# 为每个节点创建独立的状态存储
# 使用节点ID (可以通过环境变量获取) 来区分不同节点
NODE_ID = os.environ.get('NODE_ID', 'node1')  # 默认为node1

# 使用互斥锁保护状态访问
state_lock = threading.Lock()

# 全局状态但是基于节点ID隔离
# 每个节点有自己的状态空间
node_states = {}

def get_node_state():
    """
    获取当前节点的状态
    如果不存在则初始化
    """
    with state_lock:
        if NODE_ID not in node_states:
            node_states[NODE_ID] = {
                'contract_state_db': {},      # 合约状态数据库
                'deployed_contracts': {}      # 已部署的合约
            }
        return node_states[NODE_ID]

def save_state_to_disk():
    """
    将状态保存到磁盘（可选）
    """
    try:
        state_file = f"state_{NODE_ID}.pkl"
        with open(state_file, 'wb') as f:
            pickle.dump(get_node_state(), f)
        logger.info(f"State saved to {state_file}")
    except Exception as e:
        logger.warning(f"Failed to save state: {e}")

def load_state_from_disk():
    """
    从磁盘加载状态（可选）
    """
    try:
        state_file = f"state_{NODE_ID}.pkl"
        if os.path.exists(state_file):
            with open(state_file, 'rb') as f:
                state = pickle.load(f)
                with state_lock:
                    node_states[NODE_ID] = state
            logger.info(f"State loaded from {state_file}")
    except Exception as e:
        logger.warning(f"Failed to load state: {e}")

def generate_contract_id(code, owner):
    """
    Generate a unique ID for a contract based on its code and owner
    
    Input:
        code: Contract code
        owner: Address of contract owner
    Output:
        contract_id: Unique contract ID
    """
    # Create a string combining code and owner with timestamp for uniqueness
    combined = f"{code}{owner}{time.time()}{random.randint(0, 1000000)}"
    # Hash the combined string to create a unique ID
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]

def deploy_contract(code, owner):
    """
    Deploy a new smart contract
    
    Input:
        code: Contract code (string)
        owner: Address of contract owner
    Output:
        result: Dictionary containing deployment result and contract ID if successful
    """
    # For simplicity, we'll check if code is valid by trying to compile it
    try:
        # 验证代码
        compile(code, '<string>', 'exec')
        
        # 生成合约ID
        contract_id = generate_contract_id(code, owner)
        
        # 获取节点状态
        state = get_node_state()
        
        # 存储合约
        with state_lock:
            state['deployed_contracts'][contract_id] = {
                'code': code,
                'owner': owner
            }
        
        logger.info(f"📄 Node {NODE_ID} deployed contract with ID: {contract_id} by {owner[:8]}...")
        return {
            'success': True,
            'output': "Success",
            'contract_id': contract_id
        }
    except Exception as e:
        logger.warning(f"❌ Contract deployment failed: {str(e)}")
        return {
            'success': False,
            'output': f"Fail: {str(e)}"
        }

def execute_contract(contract_id, caller, function, args=None):
    """
    Execute a function in a deployed contract
    
    Input:
        contract_id: ID of the contract to execute
        caller: Address of the caller
        function: Function name to call
        args: Arguments for the function (dictionary)
    Output:
        result: Dictionary containing execution result and state changes
    """
    logger.info(f"🔄 Node {NODE_ID} executing contract {contract_id}, function: {function}, caller: {caller[:8]}...")
    logger.info(f"🔧 Function args: {args}")
    
    # 获取节点状态
    state = get_node_state()
    
    # 检查合约是否存在
    with state_lock:
        if contract_id not in state['deployed_contracts']:
            logger.warning(f"❌ Contract {contract_id} not found in node {NODE_ID} state")
            return {
                'success': False,
                'output': f"Fail: Contract not found"
            }
    
        # Get the contract code
        contract = state['deployed_contracts'][contract_id]
        code = contract['code']
    
    # Log current contract state
    current_state = {}
    with state_lock:
        for key in state['contract_state_db']:
            if key.startswith(f"{contract_id}-"):
                var_name = key[len(contract_id)+1:]
                current_state[var_name] = state['contract_state_db'][key]
    
    logger.info(f"📊 Current contract state on node {NODE_ID}: {current_state}")
    
    # 创建合约环境，注意我们需要传递节点状态的引用
    contract_state_changes = {}
    
    # 函数用于获取合约状态
    def get_state(key):
        full_key = f"{contract_id}-{key}"
        with state_lock:
            return state['contract_state_db'].get(full_key)
    
    # 函数用于设置合约状态
    def set_state(key, value):
        full_key = f"{contract_id}-{key}"
        with state_lock:
            state['contract_state_db'][full_key] = value
            contract_state_changes[key] = value
        return full_key, value
    
    # Prepare execution environment
    env = {
        'contract_id': contract_id,  # 传递合约ID
        'caller': caller,
        'args': args or {},  # 提供全局参数字典
        'get_state': get_state,
        'set_state': set_state,
        'contract_state_changes': contract_state_changes,  # To track state changes
        'time': time,  # Add time module for contract use
    }
    
    try:
        # Execute the contract code in the prepared environment
        # In a real implementation, we would use a sandbox for security
        logger.info(f"🧪 Compiling contract code...")
        exec(code, env)
        
        # Check if the requested function exists
        if function not in env:
            logger.warning(f"❌ Function {function} not found in contract {contract_id}")
            return {
                'success': False,
                'output': f"Fail: Function {function} not found"
            }
        
        # 执行函数
        logger.info(f"🚀 Calling function {function}...")
        result = env[function]()  # 始终不传递任何参数，因为合约函数将从全局 args 获取参数
        logger.info(f"✅ Function execution result: {result}")
        
        # Collect state changes
        state_changes = []
        for key, value in contract_state_changes.items():
            full_key = f"{contract_id}-{key}"
            state_changes.append(f"{full_key}:{value}")
        
        logger.info(f"📝 State changes on node {NODE_ID}: {state_changes}")
        
        # 可选：保存状态到磁盘
        save_state_to_disk()
        
        return {
            'success': True,
            'output': state_changes if state_changes else "Success"
        }
    except Exception as e:
        logger.warning(f"❌ Contract execution failed: {str(e)}")
        # Log the exception traceback for debugging
        import traceback
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        return {
            'success': False,
            'output': f"Fail: {str(e)}"
        }


def get_deployed_contracts():
    """
    Get all deployed contracts
    
    Input: None
    Output: Dictionary of deployed contracts
    """
    state = get_node_state()
    with state_lock:
        return state['deployed_contracts'].copy()

def get_contract(contract_id):
    """
    Get a specific contract by ID
    
    Input: contract_id
    Output: Contract dictionary or None
    """
    state = get_node_state()
    with state_lock:
        return state['deployed_contracts'].get(contract_id)

# Example contracts
def create_transfer_contract():
    """
    Create a simple transfer contract for testing
    """
    code = """
def init():
    # 不再引用外部的 contract_id 变量
    set_state('balance', 0)
    return "Transfer contract initialized"

def deposit():
    current_balance = get_state('balance') or 0
    amount = args.get('amount', 0)
    new_balance = current_balance + amount
    set_state('balance', new_balance)
    return f"Deposited {amount}, new balance: {new_balance}"

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
"""
    return code

def create_auction_contract():
    """
    Create a simple auction contract for testing
    
    Input: None
    Output: Contract code as string
    """
    code = """
def init():
    # 使用环境中已有的 contract_id 变量
    contract_id_val = contract_id  # 从环境中获取合约ID
    
    # Initialize auction state
    set_state('highest_bid', 0)
    set_state('highest_bidder', '')
    set_state('end_time', args.get('duration', 3600) + time.time())  # Default 1 hour
    set_state('owner', caller)
    set_state('item_description', args.get('description', 'No description'))
    set_state('closed', False)
    
    # Track state changes
    contract_state_changes['highest_bid'] = 0
    contract_state_changes['highest_bidder'] = ''
    contract_state_changes['end_time'] = args.get('duration', 3600) + time.time()
    contract_state_changes['owner'] = caller
    contract_state_changes['item_description'] = args.get('description', 'No description')
    contract_state_changes['closed'] = False
    
    return f"Auction contract {contract_id_val} initialized"

# 关键修改：不使用任何参数直接定义 bid 函数
def bid():
    # Check if auction is still open
    if get_state('closed'):
        raise Exception("Auction is closed")
    
    if time.time() > get_state('end_time'):
        set_state('closed', True)
        contract_state_changes['closed'] = True
        raise Exception("Auction has ended")
    
    # Get current highest bid and the new bid amount from args
    current_highest = get_state('highest_bid')
    bid_amount = args.get('amount', 0)  # 从全局变量 args 获取数据
    
    # Check if bid is higher than current highest
    if bid_amount <= current_highest:
        raise Exception(f"Bid must be higher than current highest bid: {current_highest}")
    
    # Update highest bid and bidder
    set_state('highest_bid', bid_amount)
    set_state('highest_bidder', caller)
    
    contract_state_changes['highest_bid'] = bid_amount
    contract_state_changes['highest_bidder'] = caller
    
    return f"New highest bid: {bid_amount} by {caller}"

def end_auction():
    # Only the owner can end the auction
    if caller != get_state('owner'):
        raise Exception("Only the owner can end the auction")
    
    # Check if auction is already closed
    if get_state('closed'):
        raise Exception("Auction is already closed")
    
    # Close the auction
    set_state('closed', True)
    contract_state_changes['closed'] = True
    
    winner = get_state('highest_bidder')
    amount = get_state('highest_bid')
    
    return f"Auction ended. Winner: {winner}, Amount: {amount}"

def get_status():
    return {
        'highest_bid': get_state('highest_bid'),
        'highest_bidder': get_state('highest_bidder'),
        'owner': get_state('owner'),
        'closed': get_state('closed'),
        'end_time': get_state('end_time'),
        'item_description': get_state('item_description')
    }
"""
    return code

# For testing
if __name__ == "__main__":
    # Test contract deployment and execution
    transfer_code = create_transfer_contract()
    owner = "test_owner"
    
    # Deploy contract
    deployment_result = deploy_contract(transfer_code, owner)
    if deployment_result['success']:
        contract_id = deployment_result['contract_id']
        print(f"Contract deployed with ID: {contract_id}")
        
        # Initialize contract
        init_result = execute_contract(contract_id, owner, "init")
        print(f"Initialization result: {init_result}")
        
        # Deposit funds
        deposit_result = execute_contract(contract_id, owner, "deposit", {"amount": 100})
        print(f"Deposit result: {deposit_result}")
        
        # Get balance
        balance_result = execute_contract(contract_id, owner, "get_balance")
        print(f"Balance result: {balance_result}")
        
        # Withdraw funds
        withdraw_result = execute_contract(contract_id, owner, "withdraw", {"amount": 50})
        print(f"Withdraw result: {withdraw_result}")
    else:
        print(f"Contract deployment failed: {deployment_result['output']}")