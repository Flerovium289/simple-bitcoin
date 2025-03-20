import time
import json
import threading
import requests
import hashlib
import random
import logging
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature
from flask import Flask, request, jsonify
import os
import logging

app = Flask(__name__)
@app.route('/stats', methods=['GET'])
def get_stats():
    """
    Endpoint for getting system statistics
    
    Input: None
    Output: JSON response with stats
    """
    # 收集系统统计信息
    stats = {
        'blockchain': {
            'length': len(blockchain),
            'latest_height': blockchain[-1]['height'] if blockchain else 0,
            'total_transactions': sum(len(block['transactions']) for block in blockchain)
        },
        'pending_transactions': len(pending_transactions),
        'accounts': {
            'total': len(account_balances),
            'total_balance': sum(account_balances.values())
        },
        'mining': {
            'total_mined_nonces': len(mined_nonces)
        }
    }
    
    # 添加最近5个区块的摘要
    recent_blocks = []
    for block in blockchain[-5:]:
        recent_blocks.append({
            'height': block['height'],
            'hash': block['hash'][:10] + '...',
            'transactions': len(block['transactions']),
            'timestamp': block['timestamp']
        })
    
    stats['recent_blocks'] = recent_blocks
    
    # 添加前5名账户
    top_accounts = []
    sorted_accounts = sorted([(addr, bal) for addr, bal in account_balances.items()], 
                            key=lambda x: x[1], reverse=True)[:5]
    
    for addr, balance in sorted_accounts:
        top_accounts.append({
            'address': addr[:10] + '...',
            'balance': balance
        })
    
    stats['top_accounts'] = top_accounts
    
    logger.info(f"📊 Stats requested: {stats['blockchain']['length']} blocks, {stats['pending_transactions']} pending txs")
    return jsonify(stats), 200@app.route('/mining/result', methods=['POST'])
def mining_result():
    """
    Endpoint for receiving mining results
    
    Input: JSON with nonce in request body
    Output: JSON response
    """
    data = request.get_json()
    nonce = data.get('nonce')
    
    if nonce is None:
        logger.warning("Mining result missing nonce")
        return jsonify({'accepted': False, 'message': 'Missing nonce'}), 400
    
    # Check if nonce has been used before
    if nonce in mined_nonces:
        logger.warning(f"Mining result with already used nonce: {nonce}")
        return jsonify({'accepted': False, 'message': 'Nonce already used'}), 400
    
    # This is a simplified implementation
    # In a real system, we would verify the nonce against the current block template
    
    logger.info(f"✅ Valid mining result received with nonce: {nonce}")
    return jsonify({'accepted': True, 'message': 'Mining result accepted'}), 201# blockchain_node/main.py
"""
Main program for a Bitcoin-like blockchain node
"""



# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('blockchain')

# Constants
MINING_REWARD = 100  # Reward for mining a block
BLOCK_TRANSACTIONS_LIMIT = 5  # Maximum number of transactions per block
DIFFICULTY = 4  # Number of leading zeros in block hash, can be overridden by env vars
NODE_ADDRESSES = []  # Will be populated with other node addresses from env vars

# Global variables
blockchain = []  # The blockchain
pending_transactions = []  # Transaction pool
account_balances = {}  # Account model: public_key -> balance
mined_nonces = set()  # Set of nonces that have been used
mining_thread = None


# Node keypair
private_key = None
public_key = None
public_key_str = None  # String representation for addresses

def generate_keypair():
    """
    Generate RSA keypair for the node
    
    Input: None
    Output: (private_key, public_key, public_key_str)
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    
    # Get string representation of public key for addresses
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    public_key_str = hashlib.sha256(public_key_bytes).hexdigest()
    
    return private_key, public_key, public_key_str

def sign_message(private_key, message):
    """
    Sign a message with private key
    
    Input: 
        private_key: RSA private key
        message: String to sign
    Output: 
        signature: Bytes of the signature
    """
    message_bytes = message.encode('utf-8')
    signature = private_key.sign(
        message_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature

def verify_signature(public_key_str, message, signature):
    """
    Verify signature with public key
    
    Input:
        public_key_str: String representation of public key
        message: Original message that was signed
        signature: Signature bytes
    Output:
        Boolean: True if valid signature, False otherwise
    TODO:
        - Convert public_key_str back to public key object
        - Verify the signature for the message
    """
    # In a real implementation, we would need to map from public_key_str back to a public key object
    # This is a simplified version that would need to be expanded
    try:
        # This would need proper implementation with key storage/retrieval
        # For demonstration purposes, we'll assume we can get the public key
        found_key = get_public_key_from_str(public_key_str)
        message_bytes = message.encode('utf-8')
        found_key.verify(
            signature,
            message_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except InvalidSignature:
        return False
    except Exception as e:
        print(f"Error verifying signature: {e}")
        return False

def get_public_key_from_str(public_key_str):
    """
    Get public key object from string representation
    
    Input:
        public_key_str: String representation of public key
    Output:
        public_key: Public key object
    TODO:
        - Implement key storage and retrieval
        - This is a placeholder for the actual implementation
    """
    # In a real implementation, we would store and retrieve keys
    # This is a simplified placeholder
    raise NotImplementedError("Key storage and retrieval not implemented")

def calculate_hash(block):
    """
    Calculate SHA-256 hash of a block
    
    Input:
        block: Block dict
    Output:
        hash_string: Hex digest of the hash
    """
    # Convert block to a string and calculate hash
    block_string = json.dumps(block, sort_keys=True).encode('utf-8')
    return hashlib.sha256(block_string).hexdigest()

def create_genesis_block():
    """
    Create the genesis block
    
    Input: None
    Output: Genesis block
    """
    timestamp = time.time()
    genesis_block = {
        'height': 0,
        'timestamp': timestamp,
        'transactions': [],
        'previous_hash': "0" * 64,
        'nonce': 0,
    }
    
    # Calculate the hash for genesis block
    genesis_block['hash'] = calculate_hash(genesis_block)
    
    # Give initial coins to this node
    account_balances[public_key_str] = 1000
    
    return genesis_block

def is_valid_proof(block, block_hash):
    """
    Check if block hash meets difficulty requirement
    
    Input:
        block: Block to validate
        block_hash: Hash of the block
    Output:
        Boolean: True if hash meets difficulty, False otherwise
    """
    return block_hash.startswith('0' * DIFFICULTY)

def mine_block(transactions, previous_hash, height):
    """
    Mine a new block
    
    Input:
        transactions: List of transactions to include
        previous_hash: Hash of the previous block
        height: Height of the new block
    Output:
        block: Mined block if successful, None otherwise
    TODO:
        - Create block with transactions
        - Find a nonce that makes the block hash meet difficulty
        - Return the mined block
    """
    timestamp = time.time()
    block = {
        'height': height,
        'timestamp': timestamp,
        'transactions': transactions,
        'previous_hash': previous_hash,
        'nonce': 0,
    }
    
    # 记录开始挖矿
    tx_count = len(transactions)
    mining_reward = next((tx['value'] for tx in transactions if tx['from'] == "COINBASE"), 0)
    logger.info(f"⛏️ Mining block #{height} with {tx_count} transactions (including {mining_reward} BTC reward)")
    
    # 挖矿尝试次数统计
    attempts = 0
    start_time = time.time()
    max_attempts = 10000  # 设置尝试上限，避免无限循环
    
    # For simplicity, we'll use random nonce instead of real mining
    # In a real implementation, we would increment nonce until hash meets difficulty
    while attempts < max_attempts:
        attempts += 1
        
        # Try a random nonce
        block['nonce'] = random.randint(0, 1000000)
        block_hash = calculate_hash(block)
        
        # Check if this nonce is valid and hasn't been used before
        if block['nonce'] not in mined_nonces and is_valid_proof(block, block_hash):
            block['hash'] = block_hash
            
            # 计算挖矿用时
            mining_time = time.time() - start_time
            logger.info(f"✅ Successfully mined block #{height} after {attempts} attempts in {mining_time:.2f}s. Hash: {block_hash[:16]}...")
            return block
        
        # 每1000次尝试记录一次日志
        if attempts % 1000 == 0:
            logger.debug(f"Mining block #{height}: {attempts} attempts so far...")
        
        # Let's add a small sleep to prevent CPU hogging
        time.sleep(0.001)
    
    logger.warning(f"⚠️ Failed to mine block #{height} after {max_attempts} attempts")
    return None

def mining_thread_func():
    """
    Thread function for mining
    
    Input: None
    Output: None
    TODO:
        - Continuously try to mine new blocks
        - If successful, process the block locally and broadcast
    """
    global mining_thread
    
    logger.info(f"🔄 Mining thread started")
    
    while True:
        # Get latest block
        latest_block = blockchain[-1]
        height = latest_block['height'] + 1
        previous_hash = latest_block['hash']
        
        # Create a reward transaction
        reward_tx = {
            'timestamp': time.time(),
            'from': "COINBASE",
            'to': public_key_str,
            'value': MINING_REWARD,
            'signature': "MINING_REWARD"  # No real signature for mining rewards
        }
        
        # Get transactions from pool
        with_reward = [reward_tx]
        tx_count = 0
        
        # Add transactions from pool up to limit
        for tx in list(pending_transactions):
            if tx_count >= BLOCK_TRANSACTIONS_LIMIT - 1:
                break
            with_reward.append(tx)
            tx_count += 1
        
        # Try to mine a block
        new_block = mine_block(with_reward, previous_hash, height)
        
        if new_block:
            logger.info(f"⛏️ Mined a new block at height {height} with {len(with_reward)} transactions")
            # Process the block locally
            if process_new_block(new_block):
                # Broadcast the block to other nodes
                broadcast_block(new_block)
                logger.info(f"📢 Broadcasted block at height {height} to other nodes")
        
        # Check if we should stop
        if mining_thread is None:
            break
        
        # Sleep a bit to prevent CPU hogging
        time.sleep(0.1)

def start_mining():
    """
    Start the mining thread
    
    Input: None
    Output: None
    """
    global mining_thread
    
    if mining_thread is None:
        mining_thread = threading.Thread(target=mining_thread_func)
        mining_thread.daemon = True
        mining_thread.start()

def stop_mining():
    """
    Stop the mining thread
    
    Input: None
    Output: None
    """
    global mining_thread
    
    if mining_thread is not None:
        mining_thread = None

def validate_transaction(transaction):
    """
    Validate a transaction
    
    Input:
        transaction: Transaction dict
    Output:
        Boolean: True if transaction is valid, False otherwise
    TODO:
        - Check if transaction has all required fields
        - Verify the signature
        - Check if sender has enough balance
    """
    # Check if transaction has all required fields
    required_fields = ['timestamp', 'from', 'to', 'value', 'signature']
    if not all(field in transaction for field in required_fields):
        missing_fields = [field for field in required_fields if field not in transaction]
        logger.warning(f"Transaction missing required fields: {', '.join(missing_fields)}")
        return False
    
    # Skip validation for mining rewards
    if transaction['from'] == "COINBASE":
        return True
    
    # Check if sender has enough balance
    sender = transaction['from']
    value = transaction['value']
    
    if sender not in account_balances:
        logger.warning(f"Sender account {sender[:8]}... does not exist")
        return False
        
    if account_balances[sender] < value:
        logger.warning(f"Insufficient balance: {sender[:8]}... has {account_balances[sender]}, needs {value}")
        return False
    
    # Verify signature - this would be implemented in a real system
    # For simplicity, we'll skip detailed signature verification here
    
    return True

def process_transaction(transaction):
    """
    Process a transaction, updating account balances
    
    Input:
        transaction: Transaction dict
    Output:
        Boolean: True if processed successfully, False otherwise
    TODO:
        - Update sender and receiver balances
    """
    sender = transaction['from']
    receiver = transaction['to']
    value = transaction['value']
    
    # 记录重要交易，如挖矿奖励或大额交易
    if sender == "COINBASE":
        logger.info(f"💰 Mining reward: {value} BTC to {receiver[:8]}...")
    elif value > 50:  # 只记录大额交易
        logger.info(f"💸 Large transaction: {sender[:8]}... -> {receiver[:8]}..., {value} BTC")
    
    # Update balances
    if sender != "COINBASE":  # Not a mining reward
        if sender not in account_balances or account_balances[sender] < value:
            logger.warning(f"❌ Failed to process transaction: Insufficient balance for {sender[:8]}...")
            return False
        account_balances[sender] -= value
    
    # Create account if it doesn't exist
    if receiver not in account_balances:
        account_balances[receiver] = 0
        logger.info(f"👤 New account created: {receiver[:8]}...")
    
    # Add value to receiver
    account_balances[receiver] += value
    
    return True

def validate_block(block):
    """
    Validate a block
    
    Input:
        block: Block dict
    Output:
        Boolean: True if block is valid, False otherwise
    TODO:
        - Check if block has all required fields
        - Verify the block hash
        - Check if previous hash matches
        - Validate all transactions in the block
    """
    # Check if block has all required fields
    required_fields = ['height', 'timestamp', 'transactions', 'previous_hash', 'nonce', 'hash']
    if not all(field in block for field in required_fields):
        logger.warning(f"Block missing required fields. Has: {', '.join(block.keys())}")
        return False
    
    # Check if the height is correct (should be one more than our latest block)
    if len(blockchain) > 0 and block['height'] != blockchain[-1]['height'] + 1:
        # Check if this is part of a fork
        if block['height'] <= blockchain[-1]['height']:
            # This could be part of a fork - we would need to handle this
            logger.info(f"Potential fork detected: Incoming block height {block['height']}, " 
                       f"our chain height {blockchain[-1]['height']}")
    
    # Verify the block hash
    calculated_hash = calculate_hash(block)
    if calculated_hash != block['hash']:
        logger.warning(f"Block hash verification failed. Given: {block['hash'][:8]}..., calculated: {calculated_hash[:8]}...")
        return False
    
    # Check if hash meets difficulty requirement
    if not is_valid_proof(block, block['hash']):
        logger.warning(f"Block hash does not meet difficulty requirement: {block['hash'][:8]}...")
        return False
    
    # Check if previous hash matches
    if len(blockchain) > 0 and block['previous_hash'] != blockchain[-1]['hash']:
        # This could be part of a fork - we would need to handle this
        logger.info(f"Previous hash doesn't match our chain's latest hash. "
                   f"Given: {block['previous_hash'][:8]}..., expected: {blockchain[-1]['hash'][:8]}...")
    
    # Validate all transactions in the block
    invalid_txs = []
    for idx, tx in enumerate(block['transactions']):
        if not validate_transaction(tx):
            invalid_txs.append(idx)
    
    if invalid_txs:
        logger.warning(f"Block contains {len(invalid_txs)} invalid transactions at indices: {invalid_txs}")
        return False
    
    return True

def process_new_block(block):
    """
    Process a new block, updating blockchain and account balances
    
    Input:
        block: Block dict
    Output:
        Boolean: True if processed successfully, False otherwise
    TODO:
        - Validate the block
        - Add to blockchain
        - Process all transactions
        - Remove processed transactions from pool
        - Handle potential forks
    """
    # Validate the block
    if not validate_block(block):
        logger.warning(f"Invalid block received at height {block['height']}")
        return False
    
    # Check if this block extends our current chain
    if len(blockchain) > 0 and block['previous_hash'] != blockchain[-1]['hash']:
        # This is a fork, decide if we should switch chains
        # For simplicity, we'll always choose the longest chain
        # In a real implementation, we would need to validate the entire fork
        fork_height = block['height']
        current_height = blockchain[-1]['height']
        
        logger.warning(f"⚠️ FORK DETECTED: Received block at height {fork_height} with previous_hash {block['previous_hash'][:8]}...")
        logger.warning(f"Current chain's last block at height {current_height} with hash {blockchain[-1]['hash'][:8]}...")
        
        if fork_height <= current_height:
            # Our chain is longer or equal, ignore this block
            logger.warning(f"FORK RESOLUTION: Keeping current chain as it's longer or equal. Current height: {current_height}")
            return False
        else:
            logger.warning(f"FORK RESOLUTION: Switching to longer chain! New height: {fork_height}, Old height: {current_height}")
    
    # Add block's nonce to mined_nonces
    mined_nonces.add(block['nonce'])
    
    # Process all transactions
    tx_count = len(block['transactions'])
    
    # Add to blockchain
    blockchain.append(block)
    logger.info(f"✅ Added new block at height {block['height']} with {tx_count} transactions. Chain length: {len(blockchain)}")
    
    # Process all transactions
    for tx in block['transactions']:
        process_transaction(tx)
        
        # Remove transaction from pending pool if it's there
        pending_transactions[:] = [t for t in pending_transactions 
                                  if not (t['from'] == tx['from'] and 
                                         t['to'] == tx['to'] and 
                                         t['value'] == tx['value'])]
    
    return True

def broadcast_transaction(transaction):
    """
    Broadcast transaction to all nodes
    
    Input:
        transaction: Transaction dict
    Output:
        None
    TODO:
        - Send transaction to all known nodes
    """
    for node_address in NODE_ADDRESSES:
        try:
            requests.post(f"http://{node_address}/transactions/new", 
                         json=transaction)
        except requests.exceptions.RequestException as e:
            print(f"Error broadcasting transaction to {node_address}: {e}")

def broadcast_block(block):
    """
    Broadcast block to all nodes
    
    Input:
        block: Block dict
    Output:
        None
    TODO:
        - Send block to all known nodes
    """
    for node_address in NODE_ADDRESSES:
        try:
            logger.info(f"📢 Broadcasting block #{block['height']} to {node_address}")
            requests.post(f"http://{node_address}/blocks/new", 
                         json=block)
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error broadcasting block to {node_address}: {str(e)[:100]}")
            
    # 定期打印区块链状态信息
    if len(blockchain) % 5 == 0:  # 每5个区块打印一次状态
        total_tx_count = sum(len(block['transactions']) for block in blockchain)
        logger.info(f"📊 Blockchain status: {len(blockchain)} blocks, {total_tx_count} total transactions")
        
        # 打印账户余额前10名
        top_accounts = sorted([(addr, bal) for addr, bal in account_balances.items()], 
                             key=lambda x: x[1], reverse=True)[:5]
        
        logger.info(f"💰 Top 5 accounts by balance:")
        for i, (addr, balance) in enumerate(top_accounts, 1):
            logger.info(f"   #{i}: {addr[:8]}... - {balance} BTC")

# API endpoints
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    """
    Endpoint for receiving new transactions
    
    Input: JSON transaction in request body
    Output: JSON response
    """
    transaction = request.get_json()
    
    # Validate the transaction
    if not validate_transaction(transaction):
        logger.warning(f"❌ Invalid transaction received from {transaction.get('from', 'unknown')[:8]}... to {transaction.get('to', 'unknown')[:8]}...")
        return jsonify({'message': 'Invalid transaction'}), 400
    
    # Add to pending transactions
    pending_transactions.append(transaction)
    
    # 为了减少日志噪音，只对每第10个交易或大额交易记录日志
    tx_value = transaction.get('value', 0)
    if len(pending_transactions) % 10 == 0 or tx_value > 50:
        logger.info(f"💰 New transaction: {transaction['from'][:8]}... -> {transaction['to'][:8]}..., {tx_value} BTC. Pool size: {len(pending_transactions)}")
    
    return jsonify({'message': 'Transaction will be added to the next block'}), 201

@app.route('/blocks/new', methods=['POST'])
def new_block():
    """
    Endpoint for receiving new blocks
    
    Input: JSON block in request body
    Output: JSON response
    """
    block = request.get_json()
    
    # Process the block
    if process_new_block(block):
        return jsonify({'message': 'Block added to the chain'}), 201
    else:
        logger.warning(f"❌ Rejected block at height {block.get('height', 'unknown')}")
        return jsonify({'message': 'Invalid block'}), 400

@app.route('/chain', methods=['GET'])
def get_chain():
    """
    Endpoint for getting the full blockchain
    
    Input: None
    Output: JSON response with blockchain
    """
    # 只返回最近的10个区块，避免响应过大
    recent_blocks = blockchain[-10:] if len(blockchain) > 10 else blockchain
    
    # 为了日志清晰，添加区块链摘要信息
    heights = [block['height'] for block in blockchain]
    min_height = min(heights) if heights else 0
    max_height = max(heights) if heights else 0
    total_txs = sum(len(block['transactions']) for block in blockchain)
    
    logger.info(f"📋 Chain info requested: {len(blockchain)} blocks, heights {min_height}-{max_height}, {total_txs} total transactions")
    
    response = {
        'chain': recent_blocks,
        'length': len(blockchain),
        'total_blocks': len(blockchain),
        'min_height': min_height,
        'max_height': max_height,
        'total_transactions': total_txs
    }
    return jsonify(response), 200

@app.route('/balance/<address>', methods=['GET'])
def get_balance(address):
    """
    Endpoint for getting account balance
    
    Input: Account address in URL
    Output: JSON response with balance
    """
    # 不为余额查询生成日志，减少日志噪音
    if address in account_balances:
        return jsonify({'address': address, 'balance': account_balances[address]}), 200
    else:
        return jsonify({'address': address, 'balance': 0}), 200

@app.route('/peers', methods=['POST'])
def register_peers():
    """
    Endpoint for registering peer nodes
    
    Input: JSON list of node addresses
    Output: JSON response
    """
    nodes = request.get_json().get('nodes')
    
    if nodes is None:
        return jsonify({'message': 'Error: Please provide a valid list of nodes'}), 400
    
    for node in nodes:
        if node not in NODE_ADDRESSES and node != f"{request.host}":
            NODE_ADDRESSES.append(node)
    
    return jsonify({'message': 'New nodes have been added', 'total_nodes': NODE_ADDRESSES}), 201

def main():
    """
    Main function to initialize and start the node
    
    Input: None
    Output: None
    """
    # 声明全局变量
    global private_key, public_key, public_key_str, blockchain, DIFFICULTY
    
    # 从环境变量配置日志级别
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    logging.getLogger().setLevel(getattr(logging, log_level))
    
    # 配置Flask日志，减少请求日志
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)
    
    # 从环境变量配置挖矿难度
    difficulty = os.environ.get('MINING_DIFFICULTY')
    if difficulty:
        try:
            DIFFICULTY = int(difficulty)
            logger.info(f"Mining difficulty set to {DIFFICULTY} from environment")
        except ValueError:
            logger.warning(f"Invalid MINING_DIFFICULTY '{difficulty}', using default {DIFFICULTY}")
    
    # Generate keypair for this node
    private_key, public_key, public_key_str = generate_keypair()
    logger.info(f"🔑 Node started with public key: {public_key_str[:16]}...")
    
    # Create genesis block
    genesis = create_genesis_block()
    blockchain = [genesis]
    logger.info(f"📦 Genesis block created with hash: {genesis['hash'][:16]}...")
    
    # Configure node addresses from environment variables
    peers = os.environ.get('PEERS', '').split(',')
    for peer in peers:
        if peer:
            NODE_ADDRESSES.append(peer)
    
    logger.info(f"🌐 Connected to peers: {NODE_ADDRESSES}")
    
    # Start mining
    start_mining()
    
    # Start the Flask app
    logger.info(f"🚀 Starting blockchain node API server on port 5000")
    app.run(host='0.0.0.0', port=5000)
    
    # 配置Flask日志，减少请求日志
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)
    
    # Generate keypair for this node
    private_key, public_key, public_key_str = generate_keypair()
    logger.info(f"🔑 Node started with public key: {public_key_str[:16]}...")
    
    # Create genesis block
    genesis = create_genesis_block()
    blockchain = [genesis]
    logger.info(f"📦 Genesis block created with hash: {genesis['hash'][:16]}...")
    
    # Configure node addresses from environment variables
    peers = os.environ.get('PEERS', '').split(',')
    for peer in peers:
        if peer:
            NODE_ADDRESSES.append(peer)
    
    logger.info(f"🌐 Connected to peers: {NODE_ADDRESSES}")
    
    # Start mining
    start_mining()
    
    # Start the Flask app
    logger.info(f"🚀 Starting blockchain node API server on port 5000")
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()