"""
A股股票分析平台 - 主程序入口
运行完整的股票分析流程并生成报告
"""
import sys
import os
import time
from datetime import datetime

# 绕过代理设置，必须在导入其他模块前执行
for _key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'all_proxy']:
    os.environ.pop(_key, None)
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

# 确保能导入同目录模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stock_screener import StockScreener
from report_generator import ReportGenerator
from config import TOP_N_STOCKS


def run_analysis(max_candidates=150):
    """运行完整的股票分析流程"""
    start_time = time.time()
    now = datetime.now()

    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║                                                          ║")
    print("║          📈 A股智能分析平台 - 每日选股系统 📈             ║")
    print("║                                                          ║")
    print(f"║          运行时间: {now.strftime('%Y-%m-%d %H:%M:%S')}   ║")
    print("║                                                          ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()

    # 初始化筛选器
    screener = StockScreener()

    # 运行完整分析
    top_stocks = screener.run_full_analysis(max_candidates=max_candidates)

    if not top_stocks:
        print("\n❌ 未找到符合条件的股票，分析结束。")
        return None

    # 分析信息
    analysis_info = {
        'total_analyzed': 'A股全市场',
        'total_candidates': f'前{max_candidates}只活跃股',
        'top_n': TOP_N_STOCKS,
        'analysis_time': now.strftime('%Y-%m-%d %H:%M:%S'),
        'elapsed_seconds': round(time.time() - start_time, 1)
    }

    # 生成报告
    print("\n📝 生成分析报告...")
    reporter = ReportGenerator()
    reports = reporter.generate_all_reports(top_stocks, analysis_info)

    elapsed = time.time() - start_time

    print(f"\n{'='*60}")
    print(f"  ✅ 分析完成！耗时 {elapsed:.1f} 秒")
    print(f"{'='*60}")
    print(f"\n  📄 HTML报告: {reports.get('html', 'N/A')}")
    print(f"  📄 JSON报告: {reports.get('json', 'N/A')}")
    print(f"  📄 文本报告: {reports.get('txt', 'N/A')}")
    print()

    return reports.get('html')


if __name__ == "__main__":
    # 可通过命令行参数调整分析数量
    max_count = 6000  # 默认分析全部A股
    if len(sys.argv) > 1:
        try:
            max_count = int(sys.argv[1])
        except:
            pass

    report_path = run_analysis(max_candidates=max_count)

    # 自动打开HTML报告
    if report_path and os.path.exists(report_path):
        try:
            os.startfile(report_path)
            print(f"🌐 已在浏览器中打开报告")
        except:
            print(f"请手动打开报告文件: {report_path}")