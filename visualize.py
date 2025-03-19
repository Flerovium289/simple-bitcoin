#!/usr/bin/env python3
"""
区块链可视化脚本 - 用于创建区块链数据的可视化图表
需要安装: pip install matplotlib requests
"""

import requests
import matplotlib.pyplot as plt
import json
import time
from datetime import datetime

def get_blockchain_data(node_url):
    """获取区块链数据"""
    try:
        response = requests.get(f"http://{node_url}/chain")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting chain data: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error connecting to node: {e}")
        return None

def get_stats_data(node_url):
    """获取系统统计信息"""
    try:
        response = requests.get(f"http://{node_url}/stats")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting stats data: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error connecting to node: {e}")
        return None

def plot_blockchain_growth(chain_data):
    """绘制区块链增长图表"""
    if not chain_data or 'chain' not in chain_data:
        print("No valid chain data available")
        return
    
    blocks = chain_data['chain']
    heights = [block['height'] for block in blocks]
    timestamps = [block['timestamp'] for block in blocks]
    
    # 将时间戳转换为可读格式
    times = [datetime.fromtimestamp(ts).strftime('%H:%M:%S') for ts in timestamps]
    
    plt.figure(figsize=(12, 6))
    plt.plot(times, heights, marker='o', linestyle='-', linewidth=2)
    plt.title('区块链增长')
    plt.xlabel('时间')
    plt.ylabel('区块高度')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('blockchain_growth.png')
    print("区块链增长图表已保存为: blockchain_growth.png")

def plot_transaction_distribution(chain_data):
    """绘制每个区块的交易数量分布"""
    if not chain_data or 'chain' not in chain_data:
        print("No valid chain data available")
        return
    
    blocks = chain_data['chain']
    heights = [block['height'] for block in blocks]
    tx_counts = [len(block['transactions']) for block in blocks]
    
    plt.figure(figsize=(12, 6))
    plt.bar(heights, tx_counts)
    plt.title('区块交易数量分布')
    plt.xlabel('区块高度')
    plt.ylabel('交易数量')
    plt.grid(True, axis='y')
    plt.tight_layout()
    plt.savefig('transaction_distribution.png')
    print("交易分布图表已保存为: transaction_distribution.png")

def plot_account_balances(stats_data):
    """绘制账户余额分布"""
    if not stats_data or 'top_accounts' not in stats_data:
        print("No valid stats data available")
        return
    
    accounts = stats_data['top_accounts']
    addresses = [acc['address'] for acc in accounts]
    balances = [acc['balance'] for acc in accounts]
    
    plt.figure(figsize=(10, 6))
    plt.bar(addresses, balances)
    plt.title('Top 账户余额')
    plt.xlabel('账户地址')
    plt.ylabel('余额 (BTC)')
    plt.xticks(rotation=45)
    plt.grid(True, axis='y')
    plt.tight_layout()
    plt.savefig('account_balances.png')
    print("账户余额图表已保存为: account_balances.png")

def plot_mining_time(chain_data):
    """分析并绘制挖矿时间分布"""
    if not chain_data or 'chain' not in chain_data:
        print("No valid chain data available")
        return
    
    blocks = chain_data['chain']
    if len(blocks) < 2:
        print("Not enough blocks for mining time analysis")
        return
    
    # 计算相邻区块的时间差
    mining_times = []
    for i in range(1, len(blocks)):
        time_diff = blocks[i]['timestamp'] - blocks[i-1]['timestamp']
        mining_times.append(time_diff)
    
    block_heights = [blocks[i]['height'] for i in range(1, len(blocks))]
    
    plt.figure(figsize=(12, 6))
    plt.plot(block_heights, mining_times, marker='o', linestyle='-')
    plt.title('区块挖矿时间')
    plt.xlabel('区块高度')
    plt.ylabel('挖矿时间 (秒)')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('mining_times.png')
    print("挖矿时间图表已保存为: mining_times.png")

def main():
    """主函数"""
    print("=== 区块链可视化工具 ===")
    node_url = input("请输入节点URL (默认: localhost:5001): ") or "localhost:5001"
    
    print(f"正在从 {node_url} 获取区块链数据...")
    chain_data = get_blockchain_data(node_url)
    
    if not chain_data:
        print("无法获取区块链数据。请确保节点正在运行。")
        return
    
    print(f"已获取数据。区块链长度: {chain_data.get('length', 0)}")
    
    # 获取统计数据
    stats_data = get_stats_data(node_url)
    
    # 创建所有图表
    plot_blockchain_growth(chain_data)
    plot_transaction_distribution(chain_data)
    plot_mining_time(chain_data)
    
    if stats_data:
        plot_account_balances(stats_data)
    
    print("所有图表已生成完毕。")

if __name__ == "__main__":
    main()