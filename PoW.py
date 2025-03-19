import hashlib
import time

def calculate_target(difficulty):
    """
    根据难度计算目标值（最大哈希值 >> (difficulty * 4)）
    """
    max_hash = (1 << 256) - 1
    return max_hash >> (difficulty * 4)

def mine_block(version, prev_hash, merkle_root, difficulty):
    """
    Bitcoin Hashcash挖矿函数（模拟完整区块头）
    :param version: 版本号
    :param prev_hash: 前一区块哈希
    :param merkle_root: Merkle根哈希
    :param difficulty: 难度（前导零的个数）
    :return: (nonce, hash, elapsed_time)
    """
    target = calculate_target(difficulty)
    nonce = 0
    start_time = time.time()

    while True:
        timestamp = int(time.time())  # 当前时间戳

        # 拼接区块头数据
        block_header = f"{version}{prev_hash}{merkle_root}{timestamp}{difficulty}{nonce}".encode()
        hash_result = hashlib.sha256(block_header).hexdigest()

        # 将哈希值转换为整数进行比较
        hash_int = int(hash_result, 16)

        # 验证哈希值是否小于目标值
        if hash_int < target:
            elapsed_time = time.time() - start_time
            print(f"✅ 挖矿成功！")
            print(f"Nonce: {nonce}")
            print(f"Hash: {hash_result}")
            print(f"耗时: {elapsed_time:.4f} 秒")
            print(f"Timestamp: {timestamp}")
            return nonce, hash_result, timestamp, elapsed_time

        # 未找到有效哈希时，增加随机数
        nonce += 1

# 示例调用
version = 1
prev_hash = "0000000000000000000a1b2c3d4e5f67890123456789abcdefabcdefabcdef"  # 上一区块哈希
merkle_root = "4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5"  # Merkle根哈希
difficulty = 5  # 难度系数

mine_block(version, prev_hash, merkle_root, difficulty)
