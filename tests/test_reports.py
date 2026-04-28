"""
模块作用：
- 测试报告写入器能生成 Markdown 和 JSON，并按开关决定是否输出 node_trace。
联动关系：
- 覆盖 reports.ReportWriter 和 pipeline.AnalysisReport 输出结构。
运行示例：
- python -m pytest tests/test_reports.py
"""

from __future__ import annotations

import json

from stock_agent_lab.llm import MockLLMClient
from stock_agent_lab.pipeline import AnalysisPipeline
from stock_agent_lab.reports import ReportWriter


def test_report_writer_outputs_markdown_and_json(tmp_path, sample_dataset):
    report = AnalysisPipeline(MockLLMClient()).run(sample_dataset)
    markdown_path, json_path = ReportWriter().write(report, tmp_path)

    markdown = markdown_path.read_text(encoding="utf-8")
    data = json.loads(json_path.read_text(encoding="utf-8"))

    assert markdown_path.exists()
    assert json_path.exists()
    assert "核心结论" in markdown
    assert "技术面" in markdown
    assert "新闻情绪" in markdown
    assert "免责声明" in markdown
    assert "执行轨迹" not in markdown
    assert data["symbol"] == "600519"
    assert data["recommendation"] == "HOLD"
    assert data["node_trace"] == []


def test_report_writer_can_include_node_trace(tmp_path, sample_dataset):
    report = AnalysisPipeline(MockLLMClient(), include_node_trace=True).run(sample_dataset)
    markdown_path, json_path = ReportWriter().write(report, tmp_path)

    markdown = markdown_path.read_text(encoding="utf-8")
    data = json.loads(json_path.read_text(encoding="utf-8"))

    assert "执行轨迹" in markdown
    assert "- Technical Analyst" in markdown
    assert "- tools_technical" in markdown
    assert data["node_trace"][0] == "Technical Analyst"
    assert "tools_news" in data["node_trace"]
