"""
股票分析平台 - 配置文件
"""
import os
from datetime import datetime

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据存储目录
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORT_DIR = os.path.join(BASE_DIR, "reports")
CACHE_DIR = os.path.join(BASE_DIR, "cache")

# 确保目录存在
for d in [DATA_DIR, REPORT_DIR, CACHE_DIR]:
    os.makedirs(d, exist_ok=True)

# ==================== 筛选参数 ====================

# 基本面筛选条件
FUNDAMENTAL_FILTER = {
    "pe_min": 0,           # 最小市盈率（排除亏损）
    "pe_max": 60,          # 最大市盈率
    "pb_min": 0.5,         # 最小市净率
    "pb_max": 10,          # 最大市净率
    "roe_min": 8,          # 最小ROE (%)
    "market_cap_min": 50,  # 最小总市值（亿元）
    "market_cap_max": 5000, # 最大总市值（亿元）
    "revenue_growth_min": 5,  # 最小营收增长率 (%)
    "profit_growth_min": 5,   # 最小净利润增长率 (%)
    "debt_ratio_max": 70,    # 最大资产负债率 (%)
}

# 技术面筛选条件
TECHNICAL_FILTER = {
    "ma_bullish": True,      # 均线多头排列
    "macd_golden": True,     # MACD金叉
    "rsi_low": 30,           # RSI超卖阈值
    "rsi_high": 70,          # RSI超买阈值
    "volume_ratio_min": 1.0, # 最小量比
    "turnover_min": 1.0,     # 最小换手率 (%)
    "turnover_max": 15.0,    # 最大换手率 (%)
}

# 评分权重
SCORE_WEIGHTS = {
    "fundamental_score": 0.35,  # 基本面权重
    "technical_score": 0.35,    # 技术面权重
    "momentum_score": 0.15,     # 动量权重
    "sentiment_score": 0.15,    # 市场情绪权重
}

# 输出数量
TOP_N_STOCKS = 50  # 推荐股票数量

# ==================== 技术指标参数 ====================
MA_PERIODS = [5, 10, 20, 60, 120]  # 均线周期
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
RSI_PERIOD = 14
KDJ_PERIOD = 9
BOLL_PERIOD = 20
BOLL_STD = 2

# 排除的板块/概念（精确匹配关键词）
EXCLUDE_KEYWORDS = ["ST", "*ST", "退市"]
# 新股前缀（仅排除名称以这些字符开头的新上市股票）
NEW_STOCK_PREFIXES = ["N", "C", "U", "W"]
# 除权除息标记
DIVIDEND_PREFIXES = ["XD", "XR", "DR"]

# ==================== 报告配置 ====================
REPORT_FORMAT = "html"  # html / txt / json