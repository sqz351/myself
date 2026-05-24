"""
A股股票分析平台 - 股票筛选排名模块
综合技术面和基本面，筛选并排名优质股票
"""
import pandas as pd
import numpy as np
import time
from datetime import datetime
from data_fetcher import StockDataFetcher
from technical_analysis import TechnicalAnalyzer
from fundamental_analysis import FundamentalAnalyzer
from config import SCORE_WEIGHTS, TOP_N_STOCKS, EXCLUDE_KEYWORDS, NEW_STOCK_PREFIXES, DIVIDEND_PREFIXES


class StockScreener:
    """股票筛选器"""

    def __init__(self):
        self.fetcher = StockDataFetcher()
        self.tech_analyzer = TechnicalAnalyzer()
        self.fund_analyzer = FundamentalAnalyzer()
        self.weights = SCORE_WEIGHTS

    def quick_filter(self, df):
        """快速过滤，排除不符合基本条件的股票"""
        import re
        filtered = df.copy()

        # 排除ST股和退市股
        for kw in EXCLUDE_KEYWORDS:
            pattern = re.escape(kw)
            filtered = filtered[~filtered['名称'].str.contains(pattern, na=False, regex=True)]

        # 排除除权除息标记的股票
        for prefix in DIVIDEND_PREFIXES:
            filtered = filtered[~filtered['名称'].str.startswith(prefix)]

        # 如果有实时行情数据，进行价格和成交额过滤
        if '最新价' in filtered.columns:
            filtered = filtered[filtered['最新价'] >= 2]
            filtered = filtered[filtered['最新价'] <= 500]
            filtered = filtered[filtered['成交额'] >= 1e7]

            # 排除新股（上市不满20个交易日，通常涨幅很大）
            for prefix in NEW_STOCK_PREFIXES:
                filtered = filtered[~filtered['名称'].str.startswith(prefix)]
        else:
            print("⚠️ 无实时行情数据，跳过价格/成交额过滤")
            # 无实时数据时，排除新股前缀
            for prefix in NEW_STOCK_PREFIXES:
                filtered = filtered[~filtered['名称'].str.startswith(prefix)]
            # 排除B股（代码以9开头或名称含B）
            filtered = filtered[~filtered['代码'].str.startswith('9')]
            filtered = filtered[~filtered['名称'].str.contains('B$', na=False, regex=True)]

        print(f"✅ 快速过滤后剩余 {len(filtered)} 只股票")
        return filtered

    def analyze_candidates(self, candidates_df, history_cache, max_analyze=None):
        """
        对候选股票进行详细技术分析（使用预取的历史数据缓存）
        """
        results = []
        if max_analyze is None:
            max_analyze = len(candidates_df)
        total = min(len(candidates_df), max_analyze)

        print(f"\n📊 开始详细分析 {total} 只候选股票...")

        for idx, (_, row) in enumerate(candidates_df.head(total).iterrows()):
            code = str(row['代码']).zfill(6)
            name = row['名称']
            progress = (idx + 1) / total * 100

            if (idx + 1) % 200 == 0 or idx == 0:
                print(f"  进度: {idx+1}/{total} ({progress:.0f}%)")

            try:
                hist_df = history_cache.get(code)
                if hist_df is None or hist_df.empty or len(hist_df) < 30:
                    continue

                # 技术分析
                tech_result = self.tech_analyzer.analyze_single_stock(hist_df)

                # 基本面分析
                fund_result = self.fund_analyzer.analyze_stock(row)

                # 综合评分
                tech_score = tech_result['score']
                fund_score = fund_result['score']

                # 动量评分
                momentum_score = self._calc_momentum_score(hist_df, row)

                # 市场情绪评分
                sentiment_score = self._calc_sentiment_score(row, hist_df)

                total_score = (
                    tech_score * self.weights['technical_score'] +
                    fund_score * self.weights['fundamental_score'] +
                    momentum_score * self.weights['momentum_score'] +
                    sentiment_score * self.weights['sentiment_score']
                )

                # 生成投资建议
                advice = self._generate_advice(total_score, tech_result, fund_result)

                last_close = hist_df['收盘'].iloc[-1] if not hist_df.empty else 0
                last_change = ((hist_df['收盘'].iloc[-1] / hist_df['收盘'].iloc[-2] - 1) * 100) if len(hist_df) >= 2 else 0

                result = {
                    '代码': code,
                    '名称': name,
                    '最新价': row.get('最新价', last_close),
                    '涨跌幅': row.get('涨跌幅', round(last_change, 2)),
                    '成交额': row.get('成交额', hist_df['成交额'].iloc[-1] if '成交额' in hist_df.columns else 0),
                    '换手率': row.get('换手率', 0),
                    '市盈率': row.get('市盈率-动态', 0),
                    '市净率': row.get('市净率', 0),
                    '总市值': row.get('总市值', 0),
                    '量比': row.get('量比', 0),
                    '技术分': tech_score,
                    '基本面分': fund_score,
                    '动量分': momentum_score,
                    '情绪分': sentiment_score,
                    '综合分': round(total_score, 1),
                    '建议': advice,
                    '技术信号': ' | '.join(tech_result['signals'][:5]),
                    '风险提示': ' | '.join(fund_result['warnings']) if fund_result['warnings'] else '无',
                }
                results.append(result)

            except Exception as e:
                continue

        print(f"\n✅ 完成分析，共分析 {len(results)} 只股票")
        return results

    def _calc_momentum_score(self, hist_df, spot_row):
        """计算动量评分 (0-100)"""
        score = 50

        if hist_df is None or len(hist_df) < 20:
            return score

        try:
            # 近5日涨幅
            if len(hist_df) >= 5:
                pct_5 = (hist_df['收盘'].iloc[-1] / hist_df['收盘'].iloc[-5] - 1) * 100
                if 1 <= pct_5 <= 8:
                    score += 15
                elif 8 < pct_5 <= 15:
                    score += 5
                elif pct_5 > 20:
                    score -= 15
                elif pct_5 < -10:
                    score += 5  # 超跌反弹

            # 近20日涨幅
            if len(hist_df) >= 20:
                pct_20 = (hist_df['收盘'].iloc[-1] / hist_df['收盘'].iloc[-20] - 1) * 100
                if 5 <= pct_20 <= 20:
                    score += 15
                elif pct_20 > 30:
                    score -= 10
                elif pct_20 < -20:
                    score += 10

            # 均线趋势
            ma5 = hist_df['收盘'].rolling(5).mean().iloc[-1]
            ma20 = hist_df['收盘'].rolling(20).mean().iloc[-1]
            if ma5 > ma20:
                score += 10
            else:
                score -= 10

            # 成交量趋势
            vol_ma5 = hist_df['成交量'].rolling(5).mean().iloc[-1]
            vol_ma20 = hist_df['成交量'].rolling(20).mean().iloc[-1]
            if vol_ma5 > vol_ma20 * 1.2:
                score += 5  # 放量

        except:
            pass

        return max(0, min(100, score))

    def _calc_sentiment_score(self, spot_row, hist_df):
        """计算市场情绪评分 (0-100)"""
        score = 50

        try:
            # 量比
            vr = float(spot_row.get('量比', 1) or 1)
            if 1.0 <= vr <= 2.0:
                score += 10
            elif vr > 3.0:
                score -= 5

            # 换手率
            turnover = float(spot_row.get('换手率', 0) or 0)
            if 1 <= turnover <= 5:
                score += 10
            elif turnover > 10:
                score -= 10

            # 涨跌幅
            change = float(spot_row.get('涨跌幅', 0) or 0)
            if 1 <= change <= 5:
                score += 10
            elif change > 7:
                score -= 5
            elif change < -5:
                score += 5  # 可能超跌

            # 振幅
            amp = float(spot_row.get('振幅', 0) or 0)
            if 2 <= amp <= 6:
                score += 5
            elif amp > 10:
                score -= 5

        except:
            pass

        return max(0, min(100, score))

    def _generate_advice(self, total_score, tech_result, fund_result):
        """生成投资建议"""
        if total_score >= 75:
            level = "⭐⭐⭐ 强烈推荐"
            desc = "技术面和基本面均表现优异，建议重点关注"
        elif total_score >= 65:
            level = "⭐⭐ 推荐关注"
            desc = "多项指标表现良好，可纳入观察池"
        elif total_score >= 55:
            level = "⭐ 一般关注"
            desc = "部分指标表现尚可，需进一步观察"
        elif total_score >= 45:
            level = "⚠️ 谨慎"
            desc = "指标表现一般，建议观望"
        else:
            level = "❌ 不推荐"
            desc = "多项指标表现不佳，建议回避"

        # 根据技术信号补充建议
        signals = tech_result.get('signals', [])
        if any('超卖' in s for s in signals):
            desc += "；存在超卖反弹机会"
        if any('超买' in s for s in signals):
            desc += "；注意短期回调风险"

        warnings = fund_result.get('warnings', [])
        if warnings:
            desc += f"；{'、'.join(warnings)}"

        return f"{level} - {desc}"

    def run_full_analysis(self, max_candidates=None):
        """运行完整的分析流程"""
        print("=" * 60)
        print(f"  📈 A股优质股筛选系统 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 60)

        # 第一步：获取全部A股实时数据
        print("\n🔍 第一步：获取全市场股票数据...")
        all_stocks = self.fetcher.get_all_stock_list()
        if all_stocks.empty:
            print("❌ 获取股票数据失败，退出分析")
            return []

        has_realtime = '最新价' in all_stocks.columns

        # 第二步：快速过滤
        print("\n🔍 第二步：快速过滤不符合条件的股票...")
        filtered = self.quick_filter(all_stocks)
        if filtered.empty:
            print("❌ 过滤后无候选股票")
            return []

        # 第三步：确定候选股票池
        print("\n🔍 第三步：确定候选股票池...")
        if has_realtime:
            candidates = self.fund_analyzer.filter_candidates(filtered)
            if candidates.empty:
                print("❌ 基本面筛选后无候选股票，使用全部过滤后股票...")
                candidates = filtered
            candidates = candidates.sort_values('成交额', ascending=False)
        else:
            print(f"⚠️ 无实时行情，将分析全部 {len(filtered)} 只过滤后股票")
            candidates = filtered

        total_candidates = len(candidates)
        print(f"📋 候选股票数量: {total_candidates}")

        # 第四步：并发获取所有候选股票的历史K线数据
        print(f"\n🔍 第四步：并发获取历史K线数据...")
        codes = [str(row['代码']).zfill(6) for _, row in candidates.iterrows()]
        history_cache = self.fetcher.get_stock_history_batch(codes, days=150, max_workers=16)

        # 第五步：详细分析
        print(f"\n🔍 第五步：详细分析...")
        results = self.analyze_candidates(candidates, history_cache)

        if not results:
            print("❌ 分析完成但无有效结果")
            return []

        # 第六步：排序并输出TOP N
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('综合分', ascending=False)
        top_stocks = results_df.head(TOP_N_STOCKS)

        print(f"\n{'='*60}")
        print(f"  🏆 TOP {TOP_N_STOCKS} 推荐股票")
        print(f"{'='*60}")

        for i, (_, stock) in enumerate(top_stocks.iterrows(), 1):
            print(f"\n  {i}. {stock['名称']}({stock['代码']}) "
                  f"| 价格:{stock['最新价']} "
                  f"| 涨跌:{float(stock['涨跌幅']):.2f}% "
                  f"| 综合分:{stock['综合分']}")
            print(f"     技术分:{stock['技术分']} | 基本面:{stock['基本面分']} | "
                  f"动量:{stock['动量分']} | 情绪:{stock['情绪分']}")
            print(f"     建议: {stock['建议']}")

        return top_stocks.to_dict('records')
