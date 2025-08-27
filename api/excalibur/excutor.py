import os
import sys
import json
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from colorama import Fore, Style
from tqdm import tqdm
import pandas as pd
import numpy as np

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
  from api.excalibur.scan import combine_stock_list, scan_stock_item
  from api.excalibur.config import DEFAULT_CONFIG
  from api.excalibur.technical import calculate_ma
except ImportError:
  # 如果绝对导入失败，尝试相对导入（本地开发环境）
  from .scan import combine_stock_list, scan_stock_item
  from .config import DEFAULT_CONFIG
  from .technical import calculate_ma

def detect_platform_period(df: pd.DataFrame, window: int = 20, 
                           box_threshold: float = 0.05, 
                           ma_diff_threshold: float = 0.01, 
                           volatility_threshold: float = 0.02, 
                           volume_factor: float = 0.7) -> pd.DataFrame:
    """
    检测股票是否处于平台期，并为每条数据添加平台期状态标识
    
    Args:
        df: 包含股票数据的DataFrame，需包含date,open,high,low,close,volume列
        window: 检测平台期的窗口大小（天数）
        box_threshold: 价格区间阈值，超过此值不认为是平台期
        ma_diff_threshold: 均线收敛阈值，超过此值不认为是平台期
        volatility_threshold: 波动率阈值，超过此值不认为是平台期
        volume_factor: 成交量萎缩因子，低于此因子认为成交量萎缩
        
    Returns:
        添加了status列的DataFrame，status=1表示处于平台期，status=0表示不处于平台期
    """
    result_df = df.copy()
    result_df['status'] = 0  # 默认为非平台期
    
    if len(result_df) < window:
        return result_df
    
    # 计算价格特征和均线
    result_df = calculate_ma(result_df, periods=[5, 10, 20])
    
    # 计算滚动窗口内的价格区间
    result_df['rolling_high'] = result_df['high'].rolling(window=window).max()
    result_df['rolling_low'] = result_df['low'].rolling(window=window).min()
    result_df['box_range'] = (result_df['rolling_high'] - result_df['rolling_low']) / result_df['rolling_low']
    
    # 计算均线收敛程度
    def calculate_ma_diff(row):
        mas = [row.get(f'ma{period}', np.nan) for period in [5, 10, 20]]
        mas = [ma for ma in mas if not pd.isna(ma)]
        if len(mas) >= 2:
            return np.std(mas) / np.mean(mas)
        return np.nan
    
    result_df['ma_diff'] = result_df.apply(calculate_ma_diff, axis=1)
    
    # 计算价格波动率（收益率标准差）
    result_df['returns'] = result_df['close'].pct_change()
    result_df['volatility'] = result_df['returns'].rolling(window=window).std()
    
    # 计算成交量变化（当前窗口与前一窗口对比）
    result_df['avg_volume'] = result_df['volume'].rolling(window=window).mean()
    result_df['prev_avg_volume'] = result_df['avg_volume'].shift(window)
    result_df['volume_ratio'] = result_df['avg_volume'] / result_df['prev_avg_volume']
    
    # 判断平台期条件
    # 1. 价格区间小于阈值
    # 2. 均线收敛程度小于阈值
    # 3. 波动率小于阈值
    # 4. 成交量萎缩（当前成交量小于前一时期成交量的一定比例）
    platform_conditions = (
        (result_df['box_range'] <= box_threshold) & 
        (result_df['ma_diff'] <= ma_diff_threshold) &
        (result_df['volatility'] <= volatility_threshold) &
        (result_df['volume_ratio'] <= volume_factor)
    )
    
    # 将满足条件的日期标记为平台期
    result_df.loc[platform_conditions, 'status'] = 1
    
    # 清理中间计算列
    drop_columns = ['rolling_high', 'rolling_low', 'box_range', 'ma_diff', 
                    'returns', 'volatility', 'avg_volume', 'prev_avg_volume', 'volume_ratio']
    result_df = result_df.drop(columns=drop_columns, errors='ignore')
    
    return result_df

def scan_test_stock(code, start_date, end_date):
  print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")
  print(f"{Fore.CYAN}Starting {code} scan{Style.RESET_ALL}")
  print(f"{Fore.CYAN}======================================{Style.RESET_ALL}")

  stock_data = scan_stock_item(code, start_date=start_date, end_date=end_date)
  
  if stock_data is not None and not stock_data.empty:
      # 检测平台期并添加status字段
      stock_data_with_status = detect_platform_period(stock_data)
      
      # 显示结果统计
      platform_days = stock_data_with_status['status'].sum()
      total_days = len(stock_data_with_status)
      platform_percentage = (platform_days / total_days) * 100 if total_days > 0 else 0
      
      print(f"{Fore.GREEN}平台期检测完成：{Style.RESET_ALL}")
      print(f"总交易日数: {total_days}")
      print(f"平台期天数: {platform_days}")
      print(f"平台期占比: {platform_percentage:.2f}%")
      
      # 准备返回结果
      result = {
          "code": code,
          "start_date": start_date,
          "end_date": end_date,
          "total_days": total_days,
          "platform_days": int(platform_days),
          "platform_percentage": round(platform_percentage, 2),
          "data": []
      }
      
      # 将DataFrame转换为JSON格式
      for _, row in stock_data_with_status.iterrows():
          data_row = {
              "date": row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date']),
              "open": float(row['open']),
              "high": float(row['high']),
              "low": float(row['low']),
              "close": float(row['close']),
              "volume": int(row['volume']),
              "status": int(row['status'])
          }
          result["data"].append(data_row)
      
      # 生成JSON文件
      output_dir = os.path.dirname(os.path.abspath(__file__))
      json_file_path = os.path.join(output_dir, f"{code}.json")
      
      with open(json_file_path, 'w', encoding='utf-8') as f:
          json.dump(result, f, ensure_ascii=False, indent=2)
      
      print(f"\n{Fore.GREEN}数据已保存至文件：{json_file_path}{Style.RESET_ALL}")
      
      # 显示最近几天的数据样例
      print(f"\n{Fore.GREEN}最近5天数据样例（含平台期状态）:{Style.RESET_ALL}")
      print(json.dumps(result["data"][-5:], ensure_ascii=False, indent=2))
      
      return {"code": 200,  "result": result }
  else:
      print(f"{Fore.RED}未获取到有效的股票数据{Style.RESET_ALL}")
      return {"error": "未获取到有效的股票数据", "code": code}



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
  # scan_all_stocks()
  code = 'sh.600000'
  start_date = '2020-08-27'
  end_date = '2025-08-25'
  scan_test_stock(code, start_date, end_date)