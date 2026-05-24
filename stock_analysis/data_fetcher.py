"""
A股股票数据获取模块
使用 akshare 获取A股市场数据
"""
import os
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 绕过代理设置，直接连接东方财富API
for _key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy']:
    os.environ.pop(_key, None)
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'


class StockDataFetcher:
    """A股数据获取器"""

    def __init__(self):
        self.today = datetime.now().strftime("%Y%m%d")

    def get_all_stock_list(self):
        """获取所有A股股票列表（带重试机制）"""
        print("📊 正在获取A股股票列表...")
        max_retries = 2
        for attempt in range(max_retries):
            try:
                df = ak.stock_zh_a_spot_em()
                # 保留关键字段
                df = df[['代码', '名称', '最新价', '涨跌幅', '涨跌额', '成交量', '成交额',
                          '振幅', '最高', '最低', '今开', '昨收', '量比', '换手率',
                          '市盈率-动态', '市净率', '总市值', '流通市值']]
                # 过滤掉ST股和停牌股
                df = df[~df['名称'].str.contains('ST|退|N/A', na=False)]
                df = df[df['最新价'] > 0]
                df = df[df['成交额'] > 0]
                print(f"✅ 获取到 {len(df)} 只股票")
                return df
            except Exception as e:
                print(f"⚠️ 第{attempt+1}次获取实时行情失败: {e}")
                if attempt < max_retries - 1:
                    wait = (attempt + 1) * 3
                    print(f"   等待{wait}秒后重试...")
                    time.sleep(wait)

        # 实时行情获取失败，回退到基础股票列表
        print("⚠️ 实时行情获取失败，尝试获取基础股票列表...")
        try:
            df = ak.stock_info_a_code_name()
            # 过滤ST股
            df = df[~df['name'].str.contains(r'ST|退', na=False)]
            df.columns = ['代码', '名称']
            print(f"✅ 获取到 {len(df)} 只股票（仅代码和名称）")
            return df
        except Exception as e:
            print(f"❌ 获取股票列表失败: {e}")
            return pd.DataFrame()

    def get_stock_history(self, code, period="daily", days=120):
        """获取单只股票的历史K线数据"""
        try:
            end_date = self.today
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            df = ak.stock_zh_a_hist(
                symbol=code,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"  # 前复权
            )
            return df
        except Exception as e:
            return pd.DataFrame()

    def get_stock_history_batch(self, codes, period="daily", days=120, max_workers=16):
        """并发批量获取多只股票的历史K线数据"""
        results = {}
        lock = threading.Lock()
        total = len(codes)
        done_count = [0]

        def _fetch_one(code):
            df = self.get_stock_history(code, period, days)
            with lock:
                done_count[0] += 1
                if done_count[0] % 100 == 0 or done_count[0] == total:
                    print(f"  📥 已获取 {done_count[0]}/{total} 只股票历史数据")
            return code, df

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_fetch_one, c): c for c in codes}
            for future in as_completed(futures):
                try:
                    code, df = future.result()
                    if df is not None and not df.empty:
                        results[code] = df
                except Exception:
                    pass

        print(f"  ✅ 成功获取 {len(results)}/{total} 只股票历史数据")
        return results

    def get_stock_industry(self):
        """获取股票行业分类"""
        try:
            df = ak.stock_board_industry_name_em()
            return df
        except Exception as e:
            print(f"❌ 获取行业分类失败: {e}")
            return pd.DataFrame()

    def get_industry_stocks(self, industry_name):
        """获取某个行业的所有股票"""
        try:
            df = ak.stock_board_industry_cons_em(symbol=industry_name)
            return df
        except Exception as e:
            return pd.DataFrame()

    def get_market_overview(self):
        """获取大盘指数数据"""
        indices = {}
        try:
            # 上证指数
            sh = ak.stock_zh_index_daily(symbol="sh000001")
            indices['上证指数'] = sh.tail(1).to_dict('records')[0] if not sh.empty else {}
        except:
            pass
        try:
            # 深证成指
            sz = ak.stock_zh_index_daily(symbol="sz399001")
            indices['深证成指'] = sz.tail(1).to_dict('records')[0] if not sz.empty else {}
        except:
            pass
        try:
            # 创业板指
            cy = ak.stock_zh_index_daily(symbol="sz399006")
            indices['创业板指'] = cy.tail(1).to_dict('records')[0] if not cy.empty else {}
        except:
            pass
        return indices

    def get_money_flow(self, code):
        """获取个股资金流向"""
        try:
            df = ak.stock_individual_fund_flow(stock=code, market="sh" if code.startswith("6") else "sz")
            return df
        except:
            return pd.DataFrame()