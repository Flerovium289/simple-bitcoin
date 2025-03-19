# client_node/client.py
"""
Client node for a Bitcoin-like blockchain system
This client generates and sends transactions to blockchain nodes
"""

import time
import json
import random
import hashlib
import requests
import threading
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization

# Constants
TRANSACTION_INTERVAL = 0.01  # 10ms between transactions
NODE_ADDRESSES = []  # Will be populated with blockchain node addresses from env vars
MAX_ACCOUNTS = 5  # Number of accounts to simulate

# Global variables
accounts = []  # List of (private_key, public_key, public_key_str) tuples

def generate_keypair():
    """
    Generate RSA keypair
    
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
    return signature.hex()  # Convert to hex string for easier handling

def create_transaction(from_account, to_account, value):
    """
    Create a transaction
    
    Input:
        from_account: (private_key, public_key, public_key_str) of sender
        to_account: (private_key, public_key, public_key_str) of receiver
        value: Amount to transfer
    Output:
        transaction: Transaction dict
    TODO:
        - Create transaction with timestamp, from, to, value
        - Sign the transaction
    """
    timestamp = time.time()
    from_address = from_account[2]  # public_key_str
    to_address = to_account[2]  # public_key_str
    
    # Create message to sign
    message = f"{timestamp},{from_address},{to_address},{value}"
    
    # Sign the message
    signature = sign_message(from_account[0], message)
    
    # Create transaction
    transaction = {
        'timestamp': timestamp,
        'from': from_address,
        'to': to_address,
        'value': value,
        'signature': signature
    }
    
    return transaction

def send_transaction(transaction):
    """
    Send transaction to all blockchain nodes
    
    Input:
        transaction: Transaction dict
    Output:
        success: Boolean indicating if at least one node accepted the transaction
    TODO:
        - Send transaction to all known nodes
        - Return True if at least one node accepted it
    """
    success = False
    
    for node_address in NODE_ADDRESSES:
        try:
            response = requests.post(f"http://{node_address}/transactions/new", 
                                    json=transaction)
            if response.status_code == 201:
                success = True
                print(f"[{datetime.now()}] Transaction accepted by {node_address}")
            else:
                print(f"[{datetime.now()}] Transaction rejected by {node_address}: {response.json()}")
        except requests.exceptions.RequestException as e:
            print(f"[{datetime.now()}] Error sending transaction to {node_address}: {e}")
    
    return success

def get_account_balance(account):
    """
    Get balance of an account from a blockchain node
    
    Input:
        account: (private_key, public_key, public_key_str)
    Output:
        balance: Account balance
    TODO:
        - Query a node for the account balance
        - Return the balance
    """
    if not NODE_ADDRESSES:
        return 0
    
    # Try the first node
    node_address = NODE_ADDRESSES[0]
    try:
        response = requests.get(f"http://{node_address}/balance/{account[2]}")
        if response.status_code == 200:
            return response.json().get('balance', 0)
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] Error getting balance from {node_address}: {e}")
    
    return 0

def transaction_generator():
    """
    Generate and send transactions periodically
    
    Input: None
    Output: None
    TODO:
        - Periodically create random transactions
        - Send them to blockchain nodes
    """
    while True:
        # Select random sender and receiver
        from_idx = random.randint(0, len(accounts) - 1)
        to_idx = random.randint(0, len(accounts) - 1)
        
        # Make sure sender and receiver are different
        while to_idx == from_idx:
            to_idx = random.randint(0, len(accounts) - 1)
        
        from_account = accounts[from_idx]
        to_account = accounts[to_idx]
        
        # Get sender's balance
        balance = get_account_balance(from_account)
        
        # Skip if sender has no funds
        if balance <= 0:
            time.sleep(TRANSACTION_INTERVAL)
            continue
        
        # Create a random value to transfer (up to 10% of balance)
        value = random.uniform(1, max(1, balance * 0.1))
        value = round(value, 2)  # Round to 2 decimal places
        
        # Create and send transaction
        transaction = create_transaction(from_account, to_account, value)
        success = send_transaction(transaction)
        
        if success:
            print(f"[{datetime.now()}] Created transaction: {from_account[2][:8]}... -> {to_account[2][:8]}..., {value} BTC")
        else:
            print(f"[{datetime.now()}] Failed to send transaction")
        
        # Wait before next transaction
        time.sleep(TRANSACTION_INTERVAL)

def main():
    """
    Main function to initialize and start the client
    
    Input: None
    Output: None
    """
    global NODE_ADDRESSES, accounts
    
    # Configure node addresses from environment variables
    import os
    nodes = os.environ.get('NODES', '').split(',')
    for node in nodes:
        if node:
            NODE_ADDRESSES.append(node)
    
    if not NODE_ADDRESSES:
        # Default to localhost if no nodes specified
        NODE_ADDRESSES.append("localhost:5000")
    
    print(f"[{datetime.now()}] Client started. Connected to nodes: {NODE_ADDRESSES}")
    
    # Generate accounts
    for i in range(MAX_ACCOUNTS):
        account = generate_keypair()
        accounts.append(account)
        print(f"[{datetime.now()}] Generated account {i+1}: {account[2]}")
    
    # Start transaction generator in a separate thread
    tx_thread = threading.Thread(target=transaction_generator)
    tx_thread.daemon = True
    tx_thread.start()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"[{datetime.now()}] Client shutting down")

if __name__ == "__main__":
    main()