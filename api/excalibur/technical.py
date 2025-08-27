import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, List, Optional

def calculate_ma(df: pd.DataFrame, periods: List[int] = [5, 10, 20, 30, 60]) -> pd.DataFrame:
  result_df = df.copy()

  for period in periods:
    result_df[f'ma{period}'] = result_df['close'].rolling(window=period).mean()

  return result_df
  