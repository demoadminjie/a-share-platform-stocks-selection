from typing import Dict, Any, List
from pydantic import BaseModel, Field
import multiprocessing

class ScanConfig(BaseModel):
  # 系统配置
  max_works: int = multiprocessing.cpu_count() or 8;

DEFAULT_CONFIG = ScanConfig();
