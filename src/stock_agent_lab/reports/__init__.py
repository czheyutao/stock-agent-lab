"""
模块作用：
- 汇总导出报告写入器，给 CLI 保持简洁导入入口。

联动关系：
- cli.py 从这里导入 ReportWriter，把 AnalysisReport 写成 Markdown 和 JSON。
"""

from stock_agent_lab.reports.writer import ReportWriter

__all__ = ["ReportWriter"]
