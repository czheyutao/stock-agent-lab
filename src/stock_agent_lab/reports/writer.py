"""
模块作用：
- 把 AnalysisReport 序列化为 Markdown 报告和 JSON 结果文件。
- 当报告对象携带 node_trace 时，额外输出一个“执行轨迹”小节，方便调试 LangGraph。
联动关系：
- pipeline.py 产出 AnalysisReport。
- cli.py 调用 ReportWriter.write 落盘。
运行示例：
- python -m pytest tests/test_reports.py
"""

from __future__ import annotations

import json
from pathlib import Path

from stock_agent_lab.models import AgentResult, AnalysisReport


class ReportWriter:
    def write(self, report: AnalysisReport, output_dir: Path) -> tuple[Path, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        markdown_path = output_dir / "report.md"
        json_path = output_dir / "result.json"

        markdown_path.write_text(self.to_markdown(report), encoding="utf-8")
        json_path.write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return markdown_path, json_path

    def to_markdown(self, report: AnalysisReport) -> str:
        sections = [
            f"# {report.symbol} 多 Agent 股票分析报告",
            f"- 分析日期: {report.analysis_date}",
            f"- 数据范围: {report.data_range}",
            f"- 最终建议: **{report.recommendation}**",
            "",
            "## 核心结论",
            report.core_summary,
            "",
            self._agent_section("技术面", report.technical),
            self._agent_section("新闻情绪", report.news),
            self._agent_section("多头观点", report.bull),
            self._agent_section("空头观点", report.bear),
            self._agent_section("交易员结论", report.trader),
            self._agent_section("风控复核", report.risk),
        ]
        sections.extend(self._optional_trace_section(report))
        sections.extend(
            [
                "## 风险提示",
                "\n".join(f"- {note}" for note in report.risk_notes),
            ]
        )
        if report.warnings:
            sections.extend(["", "## 数据警告", "\n".join(f"- {warning}" for warning in report.warnings)])
        sections.extend(["", "## 免责声明", report.disclaimer, ""])
        return "\n".join(sections)

    @staticmethod
    def _optional_trace_section(report: AnalysisReport) -> list[str]:
        if not report.node_trace:
            return []
        return ["## 执行轨迹", "\n".join(f"- {node}" for node in report.node_trace), ""]

    @staticmethod
    def _agent_section(title: str, result: AgentResult) -> str:
        return f"## {title}\n{result.summary}\n"
