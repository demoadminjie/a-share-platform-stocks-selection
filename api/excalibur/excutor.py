import os
import sys
# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import cache
from colorama import Fore, Style
from tqdm import tqdm
import pandas as pd

from api.excalibur.scan import combine_stock_list, scan_stock_item
from api.excalibur.config import DEFAULT_CONFIG

def scan_all_stocks():
  stock_list = combine_stock_list()

  print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")
  print(f"{Fore.CYAN}Starting stock scan{Style.RESET_ALL} by {DEFAULT_CONFIG.max_works}")
  print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")

  try:
    executor_class = ProcessPoolExecutor
    print(f"{Fore.GREEN}Using ProcessPoolExecutor for scan data {Style.RESET_ALL}")
  except Exception as e:
    print(f"{Fore.RED}ProcessPoolExecutor initialization failed: {e}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Falling back to ThreadPoolExecutor{Style.RESET_ALL}")
    executor_class = ThreadPoolExecutor

  # 初始化数据
  success_count = 0
  error_count = 0;
  platform_count = 0;

  platform_stocks = []

  with executor_class(DEFAULT_CONFIG.max_works) as executor:
    """ 
    Python 中字典推导式的格式为 {键表达式: 值表达式 for 变量 in 可迭代对象}
    使用了传统的循环和字典赋值方式的话，写法为：
    future_to_stock = {}
    for s in stock_list:
      future_to_stock[executor.submit(scan_stock_item, s[0], s[1], s[2])] = s
    """

    future_to_stocks = { executor.submit(scan_stock_item, s[0], s[1], s[2]): s for s in stock_list }

    total_stocks = len(future_to_stocks)
    pbar = tqdm(total=total_stocks, desc="Scan stock", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]")

    # enumerate 函数用于 为迭代过程添加索引值i
    for i, future in enumerate(future_to_stocks):
      stock = future_to_stocks[future]
      # print('stock', stock)
      # stock ['sz.002988', '2020-08-27', '2025-08-26']
      stock_code = stock[0]
      stock_name = stock[0]

      try:
        df = future.result()

        success_count += 1

        progress_pct = f'{i + 1} / {total_stocks}'

        print(f'{progress_pct} {stock_name}: {df.head() if isinstance(df, pd.DataFrame) else df}')

      except Exception as e:
        error_count += 1
        print(f"{Fore.RED}Error processing stock {stock_code}: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()

      # Update progress bar
      pbar.set_postfix(success=success_count,error=error_count, platform=platform_count)
      pbar.update(1)

if __name__ == '__main__':
    scan_all_stocks()