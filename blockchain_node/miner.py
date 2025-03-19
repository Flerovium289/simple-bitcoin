# blockchain_node/miner.py
"""
Mining program for a Bitcoin-like blockchain node
This is a simplified miner that runs as a separate process.
"""

import time
import json
import random
import hashlib
import requests
import threading
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('miner')

# Constants
DIFFICULTY = 4  # Number of leading zeros required in hash
NODE_API_URL = "http://localhost:5000"  # URL of the main node program
MINING_INTERVAL = 0.1  # How often to try mining (seconds)

def calculate_hash(data):
    """
    Calculate SHA-256 hash of data
    
    Input:
        data: Data to hash (string)
    Output:
        hash_string: Hex digest of the hash
    """
    data_bytes = data.encode('utf-8')
    return hashlib.sha256(data_bytes).hexdigest()

def is_valid_proof(hash_string):
    """
    Check if hash meets difficulty requirement
    
    Input:
        hash_string: Hash to check
    Output:
        Boolean: True if hash meets difficulty, False otherwise
    """
    return hash_string.startswith('0' * DIFFICULTY)

def generate_nonce():
    """
    Generate a random nonce
    
    Input: None
    Output:
        nonce: Random integer
    """
    return random.randint(0, 1000000)

def notify_main_program(nonce):
    """
    Notify the main program about a mined nonce
    
    Input:
        nonce: Mined nonce
    Output:
        response: Server response
    TODO:
        - Send nonce to main program
        - Return the response
    """
    try:
        payload = {
            'nonce': nonce,
            'timestamp': time.time()
        }
        response = requests.post(f"{NODE_API_URL}/mining/result", json=payload)
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error notifying main program: {str(e)[:100]}...")
        return None

def mine():
    """
    Mine continuously, looking for valid nonces
    
    Input: None
    Output: None
    TODO:
        - Continuously generate nonces
        - Check if they meet difficulty requirement
        - Notify main program if a valid nonce is found
    """
    logger.info(f"⛏️ Miner started with difficulty {DIFFICULTY} (need {DIFFICULTY} leading zeros)")
    
    nonce_attempts = 0
    last_log_time = time.time()
    nonces_found = 0
    
    while True:
        # Generate a nonce
        nonce = generate_nonce()
        nonce_attempts += 1
        
        # For simplicity, we'll hash just the nonce
        # In a real implementation, we would get the current block data from the main program
        hash_string = calculate_hash(str(nonce))
        
        # 每30秒记录一次挖矿状态，表明挖矿程序仍在运行
        current_time = time.time()
        if current_time - last_log_time > 30:
            logger.info(f"⏱️ Mining status: {nonce_attempts} attempts, {nonces_found} valid nonces found in the last 30 seconds")
            nonce_attempts = 0
            nonces_found = 0
            last_log_time = current_time
        
        if is_valid_proof(hash_string):
            nonces_found += 1
            logger.info(f"💎 Found valid nonce: {nonce}, hash: {hash_string[:16]}...")
            response = notify_main_program(nonce)
            if response and response.get('accepted', False):
                logger.info(f"✅ Nonce accepted by main program - New block created!")
            else:
                logger.warning(f"❌ Nonce rejected by main program")
        
        # Sleep to prevent CPU hogging
        time.sleep(MINING_INTERVAL)

def main():
    """
    Main function to start the mining process
    
    Input: None
    Output: None
    """
    # Configure the node API URL from environment if available
    import os
    global NODE_API_URL, DIFFICULTY, MINING_INTERVAL
    
    # 配置日志级别
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    logging.getLogger().setLevel(getattr(logging, log_level))
    
    # 配置挖矿参数
    node_host = os.environ.get('NODE_HOST', 'localhost')
    node_port = os.environ.get('NODE_PORT', '5000')
    NODE_API_URL = f"http://{node_host}:{node_port}"
    
    # 可以从环境变量调整难度
    difficulty = os.environ.get('MINING_DIFFICULTY')
    if difficulty:
        try:
            DIFFICULTY = int(difficulty)
            logger.info(f"Mining difficulty set to {DIFFICULTY} from environment")
        except ValueError:
            logger.warning(f"Invalid MINING_DIFFICULTY '{difficulty}', using default {DIFFICULTY}")
    
    # 可以从环境变量调整挖矿间隔
    interval = os.environ.get('MINING_INTERVAL')
    if interval:
        try:
            MINING_INTERVAL = float(interval)
            logger.info(f"Mining interval set to {MINING_INTERVAL}s from environment")
        except ValueError:
            logger.warning(f"Invalid MINING_INTERVAL '{interval}', using default {MINING_INTERVAL}")
    
    logger.info(f"🔌 Connecting to blockchain node at {NODE_API_URL}")
    logger.info(f"⛏️ Mining with difficulty {DIFFICULTY} and interval {MINING_INTERVAL}s")
    
    # Start mining in a separate thread
    mining_thread = threading.Thread(target=mine)
    mining_thread.daemon = True
    mining_thread.start()
    
    # Keep the main thread alive and show periodic statistics
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info(f"🛑 Miner shutting down")


if __name__ == "__main__":
    main()