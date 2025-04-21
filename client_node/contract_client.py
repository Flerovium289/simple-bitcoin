# client_node/contract_client.py
"""
Client for testing smart contracts in the blockchain system
"""

import time
import json
import hashlib
import requests
import random
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization

# Constants
NODE_ADDRESSES = []  # Will be populated with blockchain node addresses
WAIT_TIME = 2  # Time to wait between operations

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
        signature: Hex string of the signature
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

def get_balance(account_address):
    """
    Get balance of an account
    
    Input:
        account_address: Address of the account
    Output:
        balance: Account balance
    """
    if not NODE_ADDRESSES:
        return 0
    
    node_address = NODE_ADDRESSES[0]
    try:
        response = requests.get(f"http://{node_address}/balance/{account_address}")
        if response.status_code == 200:
            return response.json().get('balance', 0)
    except requests.exceptions.RequestException as e:
        print(f"Error getting balance: {e}")
    
    return 0

def send_funds(from_account, to_account, amount):
    """
    Send funds from one account to another
    
    Input:
        from_account: (private_key, public_key, public_key_str) of sender
        to_account: (private_key, public_key, public_key_str) of receiver
        amount: Amount to send
    Output:
        success: Boolean indicating success
    """
    if not NODE_ADDRESSES:
        return False
    
    node_address = NODE_ADDRESSES[0]
    
    # Create message to sign
    timestamp = time.time()
    from_address = from_account[2]
    to_address = to_account[2]
    message = f"{timestamp},{from_address},{to_address},{amount}"
    
    # Sign the message
    signature = sign_message(from_account[0], message)
    
    # Create transaction
    transaction = {
        'timestamp': timestamp,
        'from': from_address,
        'to': to_address,
        'value': amount,
        'signature': signature,
        'type': 'transfer'
    }
    
    try:
        response = requests.post(f"http://{node_address}/transactions/new", json=transaction)
        if response.status_code == 201:
            print(f"Transaction sent: {from_address[:8]}... -> {to_address[:8]}..., {amount} BTC")
            return True
        else:
            print(f"Transaction rejected: {response.json()}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error sending transaction: {e}")
        return False

def deploy_contract(account, contract_code):
    """
    Deploy a smart contract
    
    Input:
        account: (private_key, public_key, public_key_str) of contract deployer
        contract_code: Code of the contract
    Output:
        contract_id: ID of the deployed contract, or None if failed
    """
    if not NODE_ADDRESSES:
        return None
    
    node_address = NODE_ADDRESSES[0]
    
    # Create message to sign
    timestamp = time.time()
    from_address = account[2]
    message = f"{timestamp},{from_address},{contract_code}"
    
    # Sign the message
    signature = sign_message(account[0], message)
    
    # Create deployment request
    deployment = {
        'from': from_address,
        'code': contract_code,
        'signature': signature
    }
    
    try:
        response = requests.post(f"http://{node_address}/contracts/deploy", json=deployment)
        if response.status_code == 201:
            contract_id = response.json().get('contract_id')
            print(f"Contract deployed with ID: {contract_id}")
            return contract_id
        else:
            print(f"Contract deployment rejected: {response.json()}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error deploying contract: {e}")
        return None

def call_contract(account, contract_id, function_name, args=None):
    """
    Call a smart contract function
    
    Input:
        account: (private_key, public_key, public_key_str) of caller
        contract_id: ID of the contract to call
        function_name: Name of the function to call
        args: Arguments for the function (dictionary)
    Output:
        result: Expected result of the call, or None if failed
    """
    if not NODE_ADDRESSES:
        return None
    
    node_address = NODE_ADDRESSES[0]
    
    # Create message to sign
    timestamp = time.time()
    from_address = account[2]
    message = f"{timestamp},{from_address},{contract_id},{function_name},{json.dumps(args or {})}"
    
    # Sign the message
    signature = sign_message(account[0], message)
    
    # Create call request
    call = {
        'from': from_address,
        'contract_id': contract_id,
        'function': function_name,
        'args': args or {},
        'signature': signature
    }
    
    try:
        response = requests.post(f"http://{node_address}/contracts/call", json=call)
        if response.status_code == 201:
            result = response.json().get('expected_result')
            print(f"Contract call submitted. Expected result: {result}")
            return result
        else:
            print(f"Contract call rejected: {response.json()}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error calling contract: {e}")
        return None

# Test functions

def test_transfer_contract():
    """
    Test the transfer contract
    """
    print("\n=== Testing Transfer Contract ===")
    
    # Generate accounts
    account1 = generate_keypair()
    account2 = generate_keypair()
    
    print(f"Account 1: {account1[2][:8]}...")
    print(f"Account 2: {account2[2][:8]}...")
    
    # Get initial balance of account1
    balance1 = get_balance(account1[2])
    print(f"Initial balance of Account 1: {balance1} BTC")
    
    # If account1 has no funds, request some
    if balance1 < 100:
        print("Account 1 needs funds. Waiting for mining rewards...")
        time.sleep(10)  # Wait for mining rewards
        balance1 = get_balance(account1[2])
        print(f"New balance of Account 1: {balance1} BTC")
    
    # Create transfer contract
    transfer_code = """
def init():
    set_state('balance', 0)
    contract_state_changes['balance'] = 0
    return "Transfer contract initialized"

def deposit():
    current_balance = get_state('balance') or 0
    new_balance = current_balance + args.get('amount', 0)
    set_state('balance', new_balance)
    contract_state_changes['balance'] = new_balance
    return f"Deposited {args.get('amount', 0)}, new balance: {new_balance}"

def withdraw():
    current_balance = get_state('balance') or 0
    amount = args.get('amount', 0)
    
    if amount > current_balance:
        raise Exception("Insufficient balance")
    
    new_balance = current_balance - amount
    set_state('balance', new_balance)
    contract_state_changes['balance'] = new_balance
    return f"Withdrawn {amount}, new balance: {new_balance}"

def get_balance():
    return get_state('balance') or 0
"""
    
    # Deploy contract
    contract_id = deploy_contract(account1, transfer_code)
    if not contract_id:
        print("Failed to deploy transfer contract")
        return
    
    # Wait for contract to be included in a block
    print("Waiting for contract to be included in a block...")
    time.sleep(WAIT_TIME)
    
    # Initialize contract
    print("Initializing contract...")
    init_result = call_contract(account1, contract_id, "init")
    time.sleep(WAIT_TIME)
    
    # Deposit funds
    deposit_amount = 50
    print(f"Depositing {deposit_amount} BTC...")
    deposit_result = call_contract(account1, contract_id, "deposit", {"amount": deposit_amount})
    time.sleep(WAIT_TIME)
    
    # Check balance
    print("Checking contract balance...")
    balance_result = call_contract(account1, contract_id, "get_balance")
    time.sleep(WAIT_TIME)
    
    # Withdraw funds
    withdraw_amount = 20
    print(f"Withdrawing {withdraw_amount} BTC...")
    withdraw_result = call_contract(account1, contract_id, "withdraw", {"amount": withdraw_amount})
    time.sleep(WAIT_TIME)
    
    # Check balance again
    print("Checking contract balance again...")
    balance_result = call_contract(account1, contract_id, "get_balance")
    
    print("Transfer contract test completed")

def test_auction_contract():
    """
    Test the auction contract
    """
    print("\n=== Testing Auction Contract ===")
    
    # Generate accounts
    seller = generate_keypair()
    bidder1 = generate_keypair()
    bidder2 = generate_keypair()
    
    print(f"Seller: {seller[2][:8]}...")
    print(f"Bidder 1: {bidder1[2][:8]}...")
    print(f"Bidder 2: {bidder2[2][:8]}...")
    
    # Create auction contract
    auction_code = """
def init():
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
    
    return "Auction initialized"

def bid():
    # Check if auction is still open
    if get_state('closed'):
        raise Exception("Auction is closed")
    
    if time.time() > get_state('end_time'):
        set_state('closed', True)
        contract_state_changes['closed'] = True
        raise Exception("Auction has ended")
    
    # Get current highest bid
    current_highest = get_state('highest_bid')
    bid_amount = args.get('amount', 0)
    
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
    
    # Deploy contract
    contract_id = deploy_contract(seller, auction_code)
    if not contract_id:
        print("Failed to deploy auction contract")
        return
    
    # Wait for contract to be included in a block
    print("Waiting for contract to be included in a block...")
    time.sleep(WAIT_TIME)
    
    # Initialize auction
    print("Initializing auction...")
    init_args = {
        "duration": 600,  # 10 minutes
        "description": "Vintage Watch"
    }
    init_result = call_contract(seller, contract_id, "init", init_args)
    time.sleep(WAIT_TIME)
    
    # First bid from bidder1
    bid1_amount = 100
    print(f"Bidder 1 placing bid of {bid1_amount}...")
    bid1_result = call_contract(bidder1, contract_id, "bid", {"amount": bid1_amount})
    time.sleep(WAIT_TIME)
    
    # Check auction status
    print("Checking auction status...")
    status_result = call_contract(bidder1, contract_id, "get_status")
    time.sleep(WAIT_TIME)
    
    # Second bid from bidder2
    bid2_amount = 150
    print(f"Bidder 2 placing bid of {bid2_amount}...")
    bid2_result = call_contract(bidder2, contract_id, "bid", {"amount": bid2_amount})
    time.sleep(WAIT_TIME)
    
    # Check auction status again
    print("Checking auction status again...")
    status_result = call_contract(seller, contract_id, "get_status")
    time.sleep(WAIT_TIME)
    
    # End the auction
    print("Seller ending the auction...")
    end_result = call_contract(seller, contract_id, "end_auction")
    
    print("Auction contract test completed")

def test_invalid_contract():
    """
    Test deploying and executing an invalid contract
    """
    print("\n=== Testing Invalid Contract ===")
    
    # Generate account
    account = generate_keypair()
    print(f"Account: {account[2][:8]}...")
    
    # Create invalid contract with syntax error
    invalid_code = """
def init():
    set_state('value', 0
    return "Invalid contract initialized"

def update_value():
    set_state('value', args.get('new_value'))
    return f"Value updated to {args.get('new_value')}"
"""
    
    # Try to deploy invalid contract
    contract_id = deploy_contract(account, invalid_code)
    if contract_id:
        print("Unexpected: Invalid contract was deployed")
    else:
        print("Expected: Invalid contract deployment was rejected")
    
    # Create valid contract but with runtime error
    runtime_error_code = """
def init():
    set_state('value', 0)
    return "Contract initialized"

def divide():
    # This will cause a runtime error if divisor is 0
    result = 100 / args.get('divisor', 0)
    set_state('result', result)
    return f"Result: {result}"
"""
    
    # Deploy contract with runtime error
    contract_id = deploy_contract(account, runtime_error_code)
    if not contract_id:
        print("Failed to deploy runtime error contract")
        return
    
    # Wait for contract to be included in a block
    print("Waiting for contract to be included in a block...")
    time.sleep(WAIT_TIME)
    
    # Initialize contract
    print("Initializing contract...")
    init_result = call_contract(account, contract_id, "init")
    time.sleep(WAIT_TIME)
    
    # Try to execute function that will cause runtime error
    print("Executing function that will cause runtime error...")
    divide_result = call_contract(account, contract_id, "divide", {"divisor": 0})
    if divide_result:
        print("Unexpected: Runtime error call was accepted")
    else:
        print("Expected: Runtime error call was rejected")
    
    print("Invalid contract test completed")

def main():
    """
    Main function
    """
    import os
    global NODE_ADDRESSES, WAIT_TIME
    
    # Configure node addresses from environment variables
    nodes = os.environ.get('NODES', '').split(',')
    for node in nodes:
        if node:
            NODE_ADDRESSES.append(node)
    
    if not NODE_ADDRESSES:
        # Default to localhost if no nodes specified
        NODE_ADDRESSES.append("localhost:5000")
    
    print(f"Connected to nodes: {NODE_ADDRESSES}")
    
    # Configure wait time
    wait_time = os.environ.get('WAIT_TIME')
    if wait_time:
        try:
            WAIT_TIME = float(wait_time)
            print(f"Wait time set to {WAIT_TIME}s")
        except ValueError:
            print(f"Invalid WAIT_TIME '{wait_time}', using default {WAIT_TIME}")
    
    # Run tests
    test_transfer_contract()
    time.sleep(WAIT_TIME * 2)
    
    test_auction_contract()
    time.sleep(WAIT_TIME * 2)
    
    test_invalid_contract()

if __name__ == "__main__":
    main()