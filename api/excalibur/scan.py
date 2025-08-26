"""
本地的数据分析工具-扫描器
"""

from colorama import Fore, Style
import pandas as pd
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

import sys
import os
import pickle

import json
import re
import math
from datetime import datetime, timedelta
from collections.abc import Mapping, Iterable

file_path = '../data/cache/stocks'

def combine_stock_list() -> List[List[str]]:
  stock_list: List[List[str]] = [];
  
  # 获取当前文件所在目录
  current_dir = os.path.dirname(os.path.abspath(__file__))
  # 构建data/cache/stocks目录的完整路径
  stocks_dir = os.path.join(current_dir, file_path)
  
  # 检查目录是否存在
  if not os.path.exists(stocks_dir):
    print(f"目录不存在: {stocks_dir}")
    return stock_list
  
  # 遍历目录下的所有文件
  for filename in os.listdir(stocks_dir):
    # 确保只处理文件而不是子目录
    if os.path.isfile(os.path.join(stocks_dir, filename)) and filename.endswith('.pkl'):
      # 尝试从文件名中提取股票ID和日期信息
      # 根据实际文件名格式：sh.605080_2020-08-27-2025-08-26.pkl
      # 修正正则表达式，日期部分是用连字符连接的
      match = re.match(r'([a-z]+\.\d+)_(\d{4}-\d{2}-\d{2})-(\d{4}-\d{2}-\d{2})', filename)
      # print(f"filename {filename} {match}")
      if match:
        stock_id = match.group(1)
        start_date = match.group(2)
        end_date = match.group(3)
        
        # 添加到stock_list
        stock_list.append([stock_id, start_date, end_date])
  
  return stock_list

def scan_stock_item(code: str, start_data: str, end_data: str) -> Optional[pd.DataFrame]:
    """
    从pkl文件中读取指定股票代码和日期范围的股票数据
    
    Args:
        code: 股票代码，如'sh.600000'
        start_data: 起始日期，格式为'YYYY-MM-DD'
        end_data: 结束日期，格式为'YYYY-MM-DD'
        
    Returns:
        包含股票数据的DataFrame，如果文件不存在或读取失败则返回None
    """
    # 获取当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 构建完整的文件路径
    stocks_dir = os.path.join(current_dir, file_path)
    
    # 构建文件名（根据之前看到的格式：sh.605080_2020-08-27-2025-08-26.pkl）
    filename = f"{code}_{start_data}-{end_data}.pkl"
    file_path_full = os.path.join(stocks_dir, filename)
    
    # 检查文件是否存在
    if not os.path.exists(file_path_full):
        print(f"文件不存在: {file_path_full}")
        return None
    
    try:
        # 读取pkl文件
        with open(file_path_full, 'rb') as f:
            data = pickle.load(f)
        
        # 假设数据是pandas DataFrame格式
        if isinstance(data, pd.DataFrame):
            return data
        else:
            print(f"文件内容不是预期的DataFrame格式: {file_path_full}")
            return None
            
    except Exception as e:
        print(f"读取文件时出错: {file_path_full}, 错误: {str(e)}")
        return None

# 示例调用 - 仅在直接运行此脚本时执行
if __name__ == "__main__":
    # print(f'combine_stock_list {combine_stock_list()}')
    result = scan_stock_item('sh.600000', '2020-08-27', '2025-08-26')
    print(f'scan_stock_item 结果: {result.head() if isinstance(result, pd.DataFrame) else result}')

"""
if __name__ == "__main__":
    result = scan_stock_item('sh.600000', '2020-08-27', '2025-08-26')
    
    if isinstance(result, pd.DataFrame):
        # 打印完整数据
        print(f'scan_stock_item 结果 (共{len(result)}条记录):')
        
        # 设置pandas显示选项，确保所有行和列都能被打印出来
        pd.set_option('display.max_rows', None)  # 显示所有行
        pd.set_option('display.max_columns', None)  # 显示所有列
        pd.set_option('display.width', None)  # 自动调整宽度
        pd.set_option('display.max_colwidth', None)  # 显示完整的列内容
        
        print(result)
        
        # 如果数据量非常大，也可以选择以下方式之一:
        # 1. 写入到CSV文件查看
        # result.to_csv('stock_data.csv', index=True)
        # print('数据已保存到 stock_data.csv 文件')
        # 
        # 2. 分段打印大型数据
        # chunk_size = 100
        # for i in range(0, len(result), chunk_size):
        #     print(f'\n--- 数据块 {i//chunk_size + 1} ---')
        #     print(result.iloc[i:i+chunk_size])
    else:
        print(f'scan_stock_item 结果: {result}')
"""