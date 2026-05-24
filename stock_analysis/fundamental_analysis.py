"""
A股股票分析平台 - 基本面分析模块
评估股票的基本面质量并给出评分
"""
import pandas as pd
import numpy as np
from config import FUNDAMENTAL_FILTER


class FundamentalAnalyzer:
    """基本面分析器"""

    def __init__(self):
        self.filters = FUNDAMENTAL_FILTER

    def score_pe(self, pe):
        """市盈率评分 (0-20)"""
        if pd.isna(pe) or pe <= 0:
            return 0
        if pe < 10:
            return 20
        elif pe < 20:
            return 16
        elif pe < 30:
            return 12
        elif pe < 40:
            return 8
        elif pe < 60:
            return 4
        else:
            return 0

    def score_pb(self, pb):
        """市净率评分 (0-15)"""
        if pd.isna(pb) or pb <= 0:
            return 0
        if pb < 1:
            return 15  # 破净股，价值投资机会
        elif pb < 2:
            return 12
        elif pb < 3:
            return 9
        elif pb < 5:
            return 6
        elif pb < 10:
            return 3
        else:
            return 0

    def score_market_cap(self, cap_yi):
        """总市值评分（亿元）(0-15)"""
        if pd.isna(cap_yi) or cap_yi <= 0:
            return 0
        # 中盘股得分最高（100-1000亿）
        if 100 <= cap_yi <= 500:
            return 15
        elif 500 < cap_yi <= 1000:
            return 12
        elif 50 <= cap_yi < 100:
            return 10
        elif 1000 < cap_yi <= 3000:
            return 8
        elif 3000 < cap_yi <= 5000:
            return 6
        elif cap_yi > 5000:
            return 4
        else:
            return 2

    def score_turnover(self, turnover):
        """换手率评分 (0-10)"""
        if pd.isna(turnover):
            return 0
        if 1 <= turnover <= 3:
            return 10  # 适度活跃
        elif 3 < turnover <= 5:
            return 8
        elif 0.5 <= turnover < 1:
            return 6
        elif 5 < turnover <= 10:
            return 4
        elif turnover > 15:
            return 0  # 过度投机
        else:
            return 2

    def score_volume_ratio(self, vr):
        """量比评分 (0-10)"""
        if pd.isna(vr):
            return 0
        if 1.0 <= vr <= 2.0:
            return 10  # 温和放量
        elif 2.0 < vr <= 3.0:
            return 7
        elif 0.8 <= vr < 1.0:
            return 5
        elif 3.0 < vr <= 5.0:
            return 4
        elif vr > 5.0:
            return 2  # 异常放量
        else:
            return 1

    def score_amplitude(self, amp):
        """振幅评分 (0-10)"""
        if pd.isna(amp):
            return 0
        if 1 <= amp <= 3:
            return 10
        elif 3 < amp <= 5:
            return 7
        elif 0.5 <= amp < 1:
            return 5
        elif 5 < amp <= 8:
            return 3
        else:
            return 1

    def score_price_position(self, current, high, low):
        """股价位置评分 (0-10) - 距离低点近得分高"""
        if pd.isna(current) or pd.isna(high) or pd.isna(low):
            return 5
        if high == low:
            return 5
        position = (current - low) / (high - low) * 100
        if position <= 20:
            return 10  # 在低位
        elif position <= 40:
            return 8
        elif position <= 60:
            return 6
        elif position <= 80:
            return 4
        else:
            return 2  # 在高位

    def analyze_stock(self, stock_row):
        """
        对单只股票进行基本面分析
        参数: stock_row - 包含股票实时数据的一行
        返回: dict 包含 score 和 details
        """
        score = 0
        details = {}
        warnings = []

        # 获取各指标
        pe = float(stock_row.get('市盈率-动态', 0) or 0)
        pb = float(stock_row.get('市净率', 0) or 0)
        market_cap = float(stock_row.get('总市值', 0) or 0) / 1e8  # 转为亿
        turnover = float(stock_row.get('换手率', 0) or 0)
        volume_ratio = float(stock_row.get('量比', 0) or 0)
        amplitude = float(stock_row.get('振幅', 0) or 0)
        current = float(stock_row.get('最新价', 0) or 0)
        high = float(stock_row.get('最高', 0) or 0)
        low = float(stock_row.get('最低', 0) or 0)
        change_pct = float(stock_row.get('涨跌幅', 0) or 0)

        # 评分
        pe_score = self.score_pe(pe)
        pb_score = self.score_pb(pb)
        cap_score = self.score_market_cap(market_cap)
        turn_score = self.score_turnover(turnover)
        vr_score = self.score_volume_ratio(volume_ratio)
        amp_score = self.score_amplitude(amplitude)
        pos_score = self.score_price_position(current, high, low)

        score = pe_score + pb_score + cap_score + turn_score + vr_score + amp_score + pos_score

        # 基本面过滤条件
        if pe > 0 and pe < self.filters['pe_max']:
            pass
        elif pe > self.filters['pe_max']:
            warnings.append(f"PE过高({pe:.1f})")

        if market_cap < self.filters['market_cap_min']:
            warnings.append(f"市值偏小({market_cap:.0f}亿)")

        if market_cap > self.filters['market_cap_max']:
            warnings.append(f"市值过大({market_cap:.0f}亿)")

        details = {
            'pe': pe,
            'pb': pb,
            'market_cap_yi': round(market_cap, 2),
            'turnover': turnover,
            'volume_ratio': volume_ratio,
            'amplitude': amplitude,
            'change_pct': change_pct,
            'pe_score': pe_score,
            'pb_score': pb_score,
            'cap_score': cap_score,
            'turn_score': turn_score,
            'vr_score': vr_score,
            'amp_score': amp_score,
            'pos_score': pos_score,
        }

        return {
            "score": round(score, 1),
            "details": details,
            "warnings": warnings
        }

    def filter_candidates(self, df):
        """
        基本面预筛选，从全部股票中选出基本面合格的候选股
        """
        candidates = df.copy()

        # 市盈率筛选（排除亏损和过高PE）
        pe_col = '市盈率-动态'
        candidates = candidates[
            (candidates[pe_col] > self.filters['pe_min']) &
            (candidates[pe_col] <= self.filters['pe_max'])
        ]

        # 市净率筛选
        pb_col = '市净率'
        candidates = candidates[
            (candidates[pb_col] >= self.filters['pb_min']) &
            (candidates[pb_col] <= self.filters['pb_max'])
        ]

        # 总市值筛选（转为亿）
        candidates['_market_cap_yi'] = candidates['总市值'] / 1e8
        candidates = candidates[
            (candidates['_market_cap_yi'] >= self.filters['market_cap_min']) &
            (candidates['_market_cap_yi'] <= self.filters['market_cap_max'])
        ]

        # 成交额筛选（至少5000万）
        candidates = candidates[candidates['成交额'] > 5e7]

        # 换手率筛选
        candidates = candidates[
            (candidates['换手率'] >= 0.5) &
            (candidates['换手率'] <= 20)
        ]

        print(f"✅ 基本面预筛选后剩余 {len(candidates)} 只股票")
        return candidates