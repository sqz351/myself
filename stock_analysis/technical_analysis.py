"""
A股股票分析平台 - 技术分析模块
计算各类技术指标并进行技术面评分
"""
import pandas as pd
import numpy as np
from config import (
    MA_PERIODS, MACD_FAST, MACD_SLOW, MACD_SIGNAL,
    RSI_PERIOD, KDJ_PERIOD, BOLL_PERIOD, BOLL_STD
)


class TechnicalAnalyzer:
    """技术分析器"""

    @staticmethod
    def calc_ma(df, periods=None):
        """计算移动平均线"""
        if periods is None:
            periods = MA_PERIODS
        for p in periods:
            df[f'MA{p}'] = df['收盘'].rolling(window=p).mean()
        return df

    @staticmethod
    def calc_ema(series, period):
        """计算指数移动平均"""
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def calc_macd(df):
        """计算MACD指标"""
        ema_fast = df['收盘'].ewm(span=MACD_FAST, adjust=False).mean()
        ema_slow = df['收盘'].ewm(span=MACD_SLOW, adjust=False).mean()
        df['MACD_DIF'] = ema_fast - ema_slow
        df['MACD_DEA'] = df['MACD_DIF'].ewm(span=MACD_SIGNAL, adjust=False).mean()
        df['MACD_HIST'] = 2 * (df['MACD_DIF'] - df['MACD_DEA'])
        return df

    @staticmethod
    def calc_rsi(df, period=None):
        """计算RSI指标"""
        if period is None:
            period = RSI_PERIOD
        delta = df['收盘'].diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df

    @staticmethod
    def calc_kdj(df, period=None):
        """计算KDJ指标"""
        if period is None:
            period = KDJ_PERIOD
        low_min = df['最低'].rolling(window=period).min()
        high_max = df['最高'].rolling(window=period).max()
        rsv = (df['收盘'] - low_min) / (high_max - low_min) * 100
        rsv = rsv.fillna(50)

        k_values = []
        d_values = []
        k = 50
        d = 50
        for rsv_val in rsv:
            if pd.isna(rsv_val):
                k_values.append(50)
                d_values.append(50)
            else:
                k = 2/3 * k + 1/3 * rsv_val
                d = 2/3 * d + 1/3 * k
                k_values.append(k)
                d_values.append(d)

        df['KDJ_K'] = k_values
        df['KDJ_D'] = d_values
        df['KDJ_J'] = 3 * df['KDJ_K'] - 2 * df['KDJ_D']
        return df

    @staticmethod
    def calc_boll(df, period=None, std_dev=None):
        """计算布林带"""
        if period is None:
            period = BOLL_PERIOD
        if std_dev is None:
            std_dev = BOLL_STD
        df['BOLL_MID'] = df['收盘'].rolling(window=period).mean()
        std = df['收盘'].rolling(window=period).std()
        df['BOLL_UP'] = df['BOLL_MID'] + std_dev * std
        df['BOLL_LOW'] = df['BOLL_MID'] - std_dev * std
        return df

    @staticmethod
    def calc_volume_ma(df, periods=[5, 10, 20]):
        """计算成交量均线"""
        for p in periods:
            df[f'VOL_MA{p}'] = df['成交量'].rolling(window=p).mean()
        return df

    @staticmethod
    def calc_atr(df, period=14):
        """计算ATR（平均真实波幅）"""
        high_low = df['最高'] - df['最低']
        high_close = (df['最高'] - df['收盘'].shift()).abs()
        low_close = (df['最低'] - df['收盘'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(window=period).mean()
        return df

    @staticmethod
    def calc_obv(df):
        """计算OBV（能量潮指标）"""
        obv = [0]
        for i in range(1, len(df)):
            if df['收盘'].iloc[i] > df['收盘'].iloc[i-1]:
                obv.append(obv[-1] + df['成交量'].iloc[i])
            elif df['收盘'].iloc[i] < df['收盘'].iloc[i-1]:
                obv.append(obv[-1] - df['成交量'].iloc[i])
            else:
                obv.append(obv[-1])
        df['OBV'] = obv
        return df

    def compute_all_indicators(self, df):
        """计算所有技术指标"""
        if df is None or df.empty or len(df) < 30:
            return df

        df = df.copy()
        df = self.calc_ma(df)
        df = self.calc_macd(df)
        df = self.calc_rsi(df)
        df = self.calc_kdj(df)
        df = self.calc_boll(df)
        df = self.calc_volume_ma(df)
        df = self.calc_atr(df)
        df = self.calc_obv(df)
        return df

    def analyze_single_stock(self, df):
        """
        对单只股票进行技术分析，返回技术面评分和信号
        返回值: dict 包含 score(0-100) 和 signals(信号列表)
        """
        if df is None or df.empty or len(df) < 60:
            return {"score": 0, "signals": ["数据不足"], "details": {}}

        df = self.compute_all_indicators(df)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        score = 50  # 基础分
        signals = []
        details = {}

        # ===== 1. 均线分析 (最高 +/-20分) =====
        ma_score = 0
        # 多头排列检查
        if (latest.get('MA5', 0) > latest.get('MA10', 0) > latest.get('MA20', 0)):
            ma_score += 10
            signals.append("短期均线多头排列 ✅")
        if (latest.get('MA10', 0) > latest.get('MA20', 0) > latest.get('MA60', 0)):
            ma_score += 5
            signals.append("中期均线多头排列 ✅")
        # 价格在均线上方
        if latest['收盘'] > latest.get('MA20', float('inf')):
            ma_score += 5
            signals.append("股价站上20日均线 ✅")
        elif latest['收盘'] < latest.get('MA60', 0):
            ma_score -= 10
            signals.append("股价跌破60日均线 ⚠️")
        # 空头排列
        if (latest.get('MA5', 0) < latest.get('MA10', 0) < latest.get('MA20', 0)):
            ma_score -= 10
            signals.append("均线空头排列 ❌")
        details['ma_score'] = ma_score

        # ===== 2. MACD分析 (最高 +/-15分) =====
        macd_score = 0
        if latest['MACD_DIF'] > latest['MACD_DEA']:
            macd_score += 8
            signals.append("MACD金叉状态 ✅")
        else:
            macd_score -= 5
            signals.append("MACD死叉状态 ❌")
        # MACD柱状图由负转正
        if latest['MACD_HIST'] > 0 and prev['MACD_HIST'] <= 0:
            macd_score += 7
            signals.append("MACD柱状图翻红 ✅")
        elif latest['MACD_HIST'] < 0 and prev['MACD_HIST'] >= 0:
            macd_score -= 7
            signals.append("MACD柱状图翻绿 ❌")
        # DIF在零轴上方
        if latest['MACD_DIF'] > 0:
            macd_score += 3
        details['macd_score'] = macd_score

        # ===== 3. RSI分析 (最高 +/-15分) =====
        rsi_score = 0
        rsi = latest['RSI']
        if 40 <= rsi <= 60:
            rsi_score += 5
            signals.append(f"RSI={rsi:.1f}，中性区域")
        elif 30 <= rsi < 40:
            rsi_score += 10
            signals.append(f"RSI={rsi:.1f}，接近超卖，可能反弹 ✅")
        elif rsi < 30:
            rsi_score += 15
            signals.append(f"RSI={rsi:.1f}，超卖区域，关注反弹 ✅")
        elif 60 < rsi <= 70:
            rsi_score += 3
            signals.append(f"RSI={rsi:.1f}，偏强")
        elif rsi > 80:
            rsi_score -= 10
            signals.append(f"RSI={rsi:.1f}，严重超买，注意回调风险 ❌")
        elif rsi > 70:
            rsi_score -= 5
            signals.append(f"RSI={rsi:.1f}，超买区域 ⚠️")
        details['rsi_score'] = rsi_score
        details['rsi'] = rsi

        # ===== 4. KDJ分析 (最高 +/-10分) =====
        kdj_score = 0
        k, d, j = latest['KDJ_K'], latest['KDJ_D'], latest['KDJ_J']
        if k > d and prev['KDJ_K'] <= prev['KDJ_D']:
            kdj_score += 10
            signals.append("KDJ金叉 ✅")
        elif k < d and prev['KDJ_K'] >= prev['KDJ_D']:
            kdj_score -= 5
            signals.append("KDJ死叉 ❌")
        if j < 20:
            kdj_score += 5
            signals.append("KDJ-J值超卖 ✅")
        elif j > 90:
            kdj_score -= 5
            signals.append("KDJ-J值超买 ⚠️")
        details['kdj_score'] = kdj_score

        # ===== 5. 布林带分析 (最高 +/-10分) =====
        boll_score = 0
        if latest['收盘'] > latest.get('BOLL_UP', float('inf')):
            boll_score -= 5
            signals.append("股价突破布林上轨，注意回调 ⚠️")
        elif latest['收盘'] < latest.get('BOLL_LOW', 0):
            boll_score += 10
            signals.append("股价跌破布林下轨，可能超卖反弹 ✅")
        elif latest['收盘'] > latest.get('BOLL_MID', 0):
            boll_score += 3
            signals.append("股价在布林中轨上方 ✅")
        details['boll_score'] = boll_score

        # ===== 6. 成交量分析 (最高 +/-10分) =====
        vol_score = 0
        if 'VOL_MA5' in latest and 'VOL_MA20' in latest:
            if latest['成交量'] > latest['VOL_MA5'] * 1.5:
                if latest['收盘'] > prev['收盘']:
                    vol_score += 10
                    signals.append("放量上涨 ✅")
                else:
                    vol_score -= 8
                    signals.append("放量下跌 ❌")
            elif latest['成交量'] < latest['VOL_MA20'] * 0.5:
                vol_score += 2
                signals.append("缩量整理")
        details['vol_score'] = vol_score

        # ===== 7. 价格动量 (最高 +/-10分) =====
        momentum_score = 0
        if len(df) >= 5:
            pct_5d = (latest['收盘'] / df.iloc[-5]['收盘'] - 1) * 100
            if 2 <= pct_5d <= 10:
                momentum_score += 10
                signals.append(f"5日涨幅{pct_5d:.1f}%，温和上涨 ✅")
            elif pct_5d > 15:
                momentum_score -= 5
                signals.append(f"5日涨幅{pct_5d:.1f}%，短期涨幅过大 ⚠️")
            elif pct_5d < -10:
                momentum_score += 5
                signals.append(f"5日跌幅{pct_5d:.1f}%，超跌反弹机会 ✅")
            details['pct_5d'] = pct_5d

        if len(df) >= 20:
            pct_20d = (latest['收盘'] / df.iloc[-20]['收盘'] - 1) * 100
            details['pct_20d'] = pct_20d

        total_score = score + ma_score + macd_score + rsi_score + kdj_score + boll_score + vol_score + momentum_score
        total_score = max(0, min(100, total_score))

        return {
            "score": round(total_score, 1),
            "signals": signals,
            "details": details
        }