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

def deploy_contract(code, owner, contract_state_db=None, deployed_contracts=None):
    """
    Deploy a new smart contract
    
    Input:
        code: Contract code (string)
        owner: Address of contract owner
        contract_state_db: Contract state database from main.py (optional)
        deployed_contracts: Deployed contracts database from main.py (optional)
    Output:
        result: Dictionary containing deployment result and contract ID if successful
    """
    # For simplicity, we'll check if code is valid by trying to compile it
    try:
        # Validate code
        compile(code, '<string>', 'exec')
        
        # Generate contract ID
        contract_id = generate_contract_id(code, owner)
        
        # Store contract if we have the state database
        if deployed_contracts is not None:
            deployed_contracts[contract_id] = {
                'code': code,
                'owner': owner
            }
        
        logger.info(f"📄 Deployed contract with ID: {contract_id} by {owner[:8]}...")
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

def execute_contract(contract_id, caller, function, args=None, contract_state_db=None, deployed_contracts=None):
    """
    Execute a function in a deployed contract
    
    Input:
        contract_id: ID of the contract to execute
        caller: Address of the caller
        function: Function name to call
        args: Arguments for the function (dictionary)
        contract_state_db: Contract state database from main.py (optional)
        deployed_contracts: Deployed contracts database from main.py (optional)
    Output:
        result: Dictionary containing execution result and state changes
    """
    logger.info(f"🔄 Executing contract {contract_id}, function: {function}, caller: {caller[:8]}...")
    logger.info(f"🔧 Function args: {args}")
    
    # If we don't have the state databases, we can't execute the contract
    if contract_state_db is None or deployed_contracts is None:
        logger.warning(f"❌ Contract state databases not provided")
        return {
            'success': False,
            'output': f"Fail: Contract state databases not provided"
        }
    
    # Check if contract exists
    if contract_id not in deployed_contracts:
        logger.warning(f"❌ Contract {contract_id} not found")
        return {
            'success': False,
            'output': f"Fail: Contract not found"
        }
    
    # Get the contract code
    contract = deployed_contracts[contract_id]
    code = contract['code']
    
    # Log current contract state
    current_state = {}
    for key in contract_state_db:
        if key.startswith(f"{contract_id}-"):
            var_name = key[len(contract_id)+1:]
            current_state[var_name] = contract_state_db[key]
    
    logger.info(f"📊 Current contract state: {current_state}")
    
    # Create contract environment
    contract_state_changes = {}
    
    # Function to get contract state
    def get_state(key):
        full_key = f"{contract_id}-{key}"
        return contract_state_db.get(full_key)
    
    # Function to set contract state
    def set_state(key, value):
        full_key = f"{contract_id}-{key}"
        contract_state_db[full_key] = value
        contract_state_changes[key] = value
        return full_key, value
    
    # Prepare execution environment
    env = {
        'contract_id': contract_id,  # Pass contract ID
        'caller': caller,
        'args': args or {},  # Provide global args dictionary
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
        
        # Execute function
        logger.info(f"🚀 Calling function {function}...")
        result = env[function]()  # Always don't pass any arguments, as contract functions will get parameters from global args
        logger.info(f"✅ Function execution result: {result}")
        
        # Collect state changes
        state_changes = []
        for key, value in contract_state_changes.items():
            full_key = f"{contract_id}-{key}"
            state_changes.append(f"{full_key}:{value}")
        
        logger.info(f"📝 State changes: {state_changes}")
        
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



def get_contract(contract_id, deployed_contracts=None):
    """
    Get a specific contract by ID
    
    Input: 
        contract_id: ID of the contract
        deployed_contracts: Deployed contracts database from main.py (optional)
    Output: 
        Contract dictionary or None
    """
    if deployed_contracts is None:
        return None
    return deployed_contracts.get(contract_id)

# Example contracts
def create_transfer_contract():
    """
    Create a simple transfer contract for testing
    """
    code = """
def init():
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
    # Initialize auction state
    set_state('highest_bid', 0)
    set_state('highest_bidder', '')
    set_state('end_time', args.get('duration', 3600) + time.time())  # Default 1 hour
    set_state('owner', caller)
    set_state('item_description', args.get('description', 'No description'))
    set_state('closed', False)
    
    return f"Auction contract {contract_id} initialized"

def bid():
    # Check if auction is still open
    if get_state('closed'):
        raise Exception("Auction is closed")
    
    if time.time() > get_state('end_time'):
        set_state('closed', True)
        raise Exception("Auction has ended")
    
    # Get current highest bid and the new bid amount from args
    current_highest = get_state('highest_bid')
    bid_amount = args.get('amount', 0)  # Get from global args variable
    
    # Check if bid is higher than current highest
    if bid_amount <= current_highest:
        raise Exception(f"Bid must be higher than current highest bid: {current_highest}")
    
    # Update highest bid and bidder
    set_state('highest_bid', bid_amount)
    set_state('highest_bidder', caller)
    
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

# # For testing
# if __name__ == "__main__":
#     # Create test state
#     test_contract_state_db = {}
#     test_deployed_contracts = {}
    
#     # Test contract deployment and execution
#     transfer_code = create_transfer_contract()
#     owner = "test_owner"
    
#     # Deploy contract
#     deployment_result = deploy_contract(transfer_code, owner, test_contract_state_db, test_deployed_contracts)
#     if deployment_result['success']:
#         contract_id = deployment_result['contract_id']
#         print(f"Contract deployed with ID: {contract_id}")
        
#         # Initialize contract
#         init_result = execute_contract(
#             contract_id, owner, "init", {}, 
#             test_contract_state_db, test_deployed_contracts
#         )
#         print(f"Initialization result: {init_result}")
        
#         # Deposit funds
#         deposit_result = execute_contract(
#             contract_id, owner, "deposit", {"amount": 100},
#             test_contract_state_db, test_deployed_contracts
#         )
#         print(f"Deposit result: {deposit_result}")
        
#         # Get balance
#         balance_result = execute_contract(
#             contract_id, owner, "get_balance", {},
#             test_contract_state_db, test_deployed_contracts
#         )
#         print(f"Balance result: {balance_result}")
        
#         # Withdraw funds
#         withdraw_result = execute_contract(
#             contract_id, owner, "withdraw", {"amount": 50},
#             test_contract_state_db, test_deployed_contracts
#         )
#         print(f"Withdraw result: {withdraw_result}")
#     else:
#         print(f"Contract deployment failed: {deployment_result['output']}")