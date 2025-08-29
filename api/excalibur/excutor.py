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
  from api.analyzers.combined_analyzer import analyze_stock
  from api.config import ScanConfig
except ImportError:
  # 如果绝对导入失败，尝试相对导入（本地开发环境）
  from .scan import combine_stock_list, scan_stock_item
  from .config import DEFAULT_CONFIG
  from .technical import calculate_ma
  from ..config import ScanConfig
  from ..analyzers.combined_analyzer import analyze_stock

def detect_platform_period(df: pd.DataFrame) -> pd.DataFrame:
    """
    检测股票是否处于平台期，并为每条数据添加平台期状态标识
    
    Args:
        df: 包含股票数据的DataFrame，需包含date,open,high,low,close,volume列
        
    Returns:
        添加了status列的DataFrame，status=1表示处于平台期，status=0表示不处于平台期
    """
    result_df = df.copy()
    result_df['status'] = 0  # 默认为非平台期
    
    # 设置最小窗口大小，需要足够的历史数据来进行分析
    min_window = 120  # 使用较大的窗口以获取更可靠的结果
    
    if len(result_df) < min_window:
        return result_df
    
    # 创建配置对象（在循环外部创建一次，而不是每次循环都创建）
    config = ScanConfig(
        windows=[80, 100, 120],
        expected_count=10,
        box_threshold=0.3,
        ma_diff_threshold=0.25,
        volatility_threshold=0.4,
        use_volume_analysis=True,
        volume_change_threshold=0.5,
        volume_stability_threshold=0.5,
        volume_increase_threshold=1.5,
        use_technical_indicators=False,
        use_breakthrough_prediction=True,
        use_low_position=False,
        high_point_lookback_days=365,
        decline_period_days=180,
        decline_threshold=0.3,
        use_rapid_decline_detection=True,
        rapid_decline_days=30,
        rapid_decline_threshold=0.15,
        use_breakthrough_confirmation=False,
        breakthrough_confirmation_days=1,
        use_window_weights=False,
        window_weights={},
        use_box_detection=True,
        box_quality_threshold=0.3,
        use_fundamental_filter=False,
        revenue_growth_percentile=0.3,
        profit_growth_percentile=0.3,
        roe_percentile=0.3,
        liability_percentile=0.3,
        pe_percentile=0.7,
        pb_percentile=0.7,
        fundamental_years_to_check=3
    )
    
    # 确保window_weights不为None（analyze_stock函数可能期望一个字典而不是None）
    if config.window_weights is None:
        config.window_weights = {}
    
    # 遍历DataFrame，为每一天判断是否处于平台期
    for i in range(min_window, len(result_df)):
        # 为当前日期创建一个包含足够历史数据的窗口
        # 向前取min_window天的数据
        window_start = max(0, i - min_window + 1)
        window_data = result_df.iloc[window_start:i+1].copy()
        
        # 使用analyze_stock方法分析这个窗口的数据
        try:
            # 根据analyze_stock函数的参数顺序传入配置值
            analysis_result = analyze_stock(
                window_data,
                windows=config.windows,
                box_threshold=config.box_threshold,
                ma_diff_threshold=config.ma_diff_threshold,
                volatility_threshold=config.volatility_threshold,
                volume_change_threshold=config.volume_change_threshold,
                volume_stability_threshold=config.volume_stability_threshold,
                volume_increase_threshold=config.volume_increase_threshold,
                use_volume_analysis=config.use_volume_analysis,
                use_breakthrough_prediction=config.use_breakthrough_prediction,
                use_window_weights=config.use_window_weights,
                window_weights=config.window_weights,
                use_low_position=config.use_low_position,
                high_point_lookback_days=config.high_point_lookback_days,
                decline_period_days=config.decline_period_days,
                decline_threshold=config.decline_threshold,
                use_rapid_decline_detection=config.use_rapid_decline_detection,
                rapid_decline_days=config.rapid_decline_days,
                rapid_decline_threshold=config.rapid_decline_threshold,
                use_breakthrough_confirmation=config.use_breakthrough_confirmation,
                breakthrough_confirmation_days=config.breakthrough_confirmation_days,
                use_box_detection=config.use_box_detection,
                box_quality_threshold=config.box_quality_threshold
            )
            
            # 如果分析结果表明处于平台期，则将当前日期的status置为1
            if analysis_result.get('is_platform', False):
                result_df.iloc[i, result_df.columns.get_loc('status')] = 1
        except Exception as e:
            # 如果分析过程中出现错误，保持status为0
            print(f"分析出错: {e}")
            continue
    
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
  code = 'sz.000882'
  start_date = '2020-08-27'
  end_date = '2025-08-25'
  scan_test_stock(code, start_date, end_date)