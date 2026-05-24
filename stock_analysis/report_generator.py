"""
A股股票分析平台 - 报告生成模块
生成HTML/文本格式的分析报告
"""
import os
import json
from datetime import datetime
from config import REPORT_DIR


class ReportGenerator:
    """分析报告生成器"""

    def __init__(self):
        os.makedirs(REPORT_DIR, exist_ok=True)

    def generate_html_report(self, top_stocks, analysis_info=None):
        """生成HTML格式的分析报告"""
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%Y-%m-%d %H:%M:%S")

        # 构建表格行
        table_rows = ""
        for i, stock in enumerate(top_stocks, 1):
            change_pct = stock.get('涨跌幅', 0)
            change_class = "up" if change_pct >= 0 else "down"
            change_icon = "▲" if change_pct >= 0 else "▼"

            score = stock.get('综合分', 0)
            if score >= 75:
                score_class = "score-high"
            elif score >= 60:
                score_class = "score-mid"
            else:
                score_class = "score-low"

            table_rows += f"""
            <tr>
                <td class="rank">{i}</td>
                <td class="code">{stock.get('代码', '')}</td>
                <td class="name">{stock.get('名称', '')}</td>
                <td class="price">{stock.get('最新价', 0):.2f}</td>
                <td class="{change_class}">{change_icon} {change_pct:+.2f}%</td>
                <td class="tech-score">{stock.get('技术分', 0):.0f}</td>
                <td class="fund-score">{stock.get('基本面分', 0):.0f}</td>
                <td class="mom-score">{stock.get('动量分', 0):.0f}</td>
                <td class="sen-score">{stock.get('情绪分', 0):.0f}</td>
                <td class="{score_class}"><strong>{score:.1f}</strong></td>
                <td class="turnover">{stock.get('换手率', 0):.2f}%</td>
                <td class="pe">{stock.get('市盈率', 0):.1f}</td>
                <td class="cap">{self._format_cap(stock.get('总市值', 0))}</td>
                <td class="signals">{stock.get('技术信号', '')}</td>
                <td class="advice">{stock.get('建议', '')}</td>
            </tr>"""

        # 统计信息
        total_analyzed = analysis_info.get('total_analyzed', 'N/A') if analysis_info else 'N/A'
        total_candidates = analysis_info.get('total_candidates', 'N/A') if analysis_info else 'N/A'

        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A股优质股分析报告 - {date_str}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #0c1445 0%, #1a1a3e 50%, #0d1137 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            padding: 30px 20px;
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            margin-bottom: 24px;
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
        }}
        .header h1 {{
            font-size: 28px;
            background: linear-gradient(90deg, #00d2ff, #7b68ee, #ff6b9d);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        .header .subtitle {{
            color: #8892b0;
            font-size: 14px;
        }}
        .stats {{
            display: flex;
            gap: 16px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }}
        .stat-card {{
            flex: 1;
            min-width: 200px;
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
            text-align: center;
        }}
        .stat-card .label {{ color: #8892b0; font-size: 13px; margin-bottom: 8px; }}
        .stat-card .value {{ font-size: 24px; font-weight: bold; color: #64ffda; }}
        .table-wrapper {{
            background: rgba(255,255,255,0.03);
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.1);
            overflow-x: auto;
            margin-bottom: 24px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        th {{
            background: rgba(100, 255, 218, 0.1);
            color: #64ffda;
            padding: 14px 10px;
            text-align: center;
            font-weight: 600;
            white-space: nowrap;
            border-bottom: 2px solid rgba(100, 255, 218, 0.2);
            position: sticky;
            top: 0;
        }}
        td {{
            padding: 12px 10px;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            white-space: nowrap;
        }}
        tr:hover {{
            background: rgba(100, 255, 218, 0.05);
        }}
        .rank {{ font-weight: bold; color: #ffd700; font-size: 16px; }}
        .code {{ color: #7b68ee; font-family: monospace; }}
        .name {{ color: #fff; font-weight: 600; text-align: left; }}
        .price {{ color: #e0e0e0; font-weight: 600; }}
        .up {{ color: #ff4757; font-weight: 600; }}
        .down {{ color: #2ed573; font-weight: 600; }}
        .score-high {{ color: #ff6b9d; font-size: 16px; }}
        .score-mid {{ color: #ffa502; font-size: 16px; }}
        .score-low {{ color: #8892b0; font-size: 16px; }}
        .tech-score {{ color: #70a1ff; }}
        .fund-score {{ color: #ffa502; }}
        .mom-score {{ color: #ff6348; }}
        .sen-score {{ color: #7bed9f; }}
        .signals {{
            max-width: 300px;
            white-space: normal;
            text-align: left;
            font-size: 12px;
            color: #a0a0a0;
            line-height: 1.6;
        }}
        .advice {{
            max-width: 300px;
            white-space: normal;
            text-align: left;
            font-size: 12px;
            line-height: 1.6;
        }}
        .turnover {{ color: #a0a0a0; }}
        .pe {{ color: #a0a0a0; }}
        .cap {{ color: #a0a0a0; }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #8892b0;
            font-size: 12px;
            line-height: 2;
        }}
        .footer .warning {{
            color: #ff6b6b;
            font-weight: 600;
            margin-top: 10px;
            padding: 12px;
            background: rgba(255, 107, 107, 0.1);
            border-radius: 8px;
            border: 1px solid rgba(255, 107, 107, 0.2);
        }}
        .methodology {{
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 24px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .methodology h3 {{
            color: #64ffda;
            margin-bottom: 12px;
        }}
        .methodology p {{
            color: #8892b0;
            font-size: 13px;
            line-height: 1.8;
        }}
        .legend {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-top: 10px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: #8892b0;
        }}
        .legend-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 A股优质股每日分析报告</h1>
            <p class="subtitle">生成时间：{time_str} | 数据来源：东方财富 | 分析周期：近120个交易日</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="label">全市场股票</div>
                <div class="value">{total_analyzed}</div>
            </div>
            <div class="stat-card">
                <div class="label">通过筛选</div>
                <div class="value">{total_candidates}</div>
            </div>
            <div class="stat-card">
                <div class="label">推荐数量</div>
                <div class="value">{len(top_stocks)}</div>
            </div>
            <div class="stat-card">
                <div class="label">平均综合分</div>
                <div class="value">{sum(s.get('综合分', 0) for s in top_stocks) / max(len(top_stocks), 1):.1f}</div>
            </div>
        </div>

        <div class="methodology">
            <h3>📊 评分体系说明</h3>
            <p>
                综合评分 = 技术面(35%) + 基本面(35%) + 动量(15%) + 市场情绪(15%)<br>
                技术面：均线系统、MACD、RSI、KDJ、布林带、成交量、价格动量<br>
                基本面：市盈率、市净率、总市值、换手率、量比、振幅、股价位置<br>
                动量：5日/20日涨跌幅、均线趋势、成交量趋势<br>
                情绪：量比、换手率、涨跌幅、振幅
            </p>
            <div class="legend">
                <div class="legend-item"><div class="legend-dot" style="background:#ff6b9d"></div>⭐⭐⭐ 强烈推荐 (≥75分)</div>
                <div class="legend-item"><div class="legend-dot" style="background:#ffa502"></div>⭐⭐ 推荐关注 (65-75分)</div>
                <div class="legend-item"><div class="legend-dot" style="background:#8892b0"></div>⭐ 一般关注 (55-65分)</div>
                <div class="legend-item"><div class="legend-dot" style="background:#ff4757"></div>⚠️ 谨慎/不推荐 (<55分)</div>
            </div>
        </div>

        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>代码</th>
                        <th>名称</th>
                        <th>最新价</th>
                        <th>涨跌幅</th>
                        <th>技术分</th>
                        <th>基本面</th>
                        <th>动量分</th>
                        <th>情绪分</th>
                        <th>综合分</th>
                        <th>换手率</th>
                        <th>PE</th>
                        <th>市值</th>
                        <th>技术信号</th>
                        <th>投资建议</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>⚠️ 免责声明：本报告由程序自动生成，仅供参考，不构成任何投资建议。</p>
            <p>股市有风险，投资需谨慎。请根据自身风险承受能力做出投资决策。</p>
            <p>© {now.year} A股智能分析平台 | Powered by Python</p>
        </div>
    </div>
</body>
</html>"""

        # 保存文件
        filename = f"stock_report_{date_str}.html"
        filepath = os.path.join(REPORT_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"\n📄 HTML报告已生成: {filepath}")
        return filepath

    def generate_json_report(self, top_stocks, analysis_info=None):
        """生成JSON格式的报告数据"""
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")

        report_data = {
            "report_date": date_str,
            "report_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "analysis_info": analysis_info or {},
            "top_stocks": top_stocks,
            "disclaimer": "本报告由程序自动生成，仅供参考，不构成任何投资建议。"
        }

        filename = f"stock_report_{date_str}.json"
        filepath = os.path.join(REPORT_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print(f"📄 JSON报告已生成: {filepath}")
        return filepath

    def generate_text_report(self, top_stocks, analysis_info=None):
        """生成文本格式的报告"""
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")

        lines = []
        lines.append("=" * 80)
        lines.append(f"  A股优质股每日分析报告")
        lines.append(f"  生成时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        lines.append("")

        for i, stock in enumerate(top_stocks, 1):
            change = stock.get('涨跌幅', 0)
            lines.append(f"  {i:2d}. {stock.get('名称', '')}({stock.get('代码', '')})")
            lines.append(f"      价格: {stock.get('最新价', 0):.2f}  |  涨跌: {change:+.2f}%  |  综合分: {stock.get('综合分', 0):.1f}")
            lines.append(f"      技术:{stock.get('技术分', 0):.0f}  基本面:{stock.get('基本面分', 0):.0f}  "
                        f"动量:{stock.get('动量分', 0):.0f}  情绪:{stock.get('情绪分', 0):.0f}")
            lines.append(f"      PE: {stock.get('市盈率', 0):.1f}  |  换手率: {stock.get('换手率', 0):.2f}%  |  "
                        f"市值: {self._format_cap(stock.get('总市值', 0))}")
            lines.append(f"      信号: {stock.get('技术信号', '')}")
            lines.append(f"      建议: {stock.get('建议', '')}")
            lines.append("-" * 80)

        lines.append("")
        lines.append("⚠️ 免责声明：本报告由程序自动生成，仅供参考，不构成任何投资建议。")
        lines.append("股市有风险，投资需谨慎。")

        filename = f"stock_report_{date_str}.txt"
        filepath = os.path.join(REPORT_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"📄 文本报告已生成: {filepath}")
        return filepath

    @staticmethod
    def _format_cap(cap_value):
        """格式化市值显示"""
        try:
            if cap_value != cap_value or cap_value == 0:  # NaN check
                return "N/A"
        except (TypeError, ValueError):
            return "N/A"
        cap_yi = cap_value / 1e8
        if cap_yi >= 1000:
            return f"{cap_yi/1000:.1f}千亿"
        else:
            return f"{cap_yi:.0f}亿"

    def generate_all_reports(self, top_stocks, analysis_info=None):
        """生成所有格式的报告"""
        reports = {}
        reports['html'] = self.generate_html_report(top_stocks, analysis_info)
        reports['json'] = self.generate_json_report(top_stocks, analysis_info)
        reports['txt'] = self.generate_text_report(top_stocks, analysis_info)
        return reports