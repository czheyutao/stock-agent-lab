"""
模块作用：
- 测试命令行入口的参数校验行为，并验证 include-node-trace 开关能正确传递到 pipeline。
联动关系：
- 直接调用 stock_agent_lab.cli.app，确保 CLI 层在进入 data/pipeline 前能拦截错误参数，并能透传新开关。
运行示例：
- python -m pytest tests/test_cli.py
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from stock_agent_lab.cli import app
from stock_agent_lab.models import AnalysisReport, AgentResult


def test_cli_rejects_invalid_symbol():
    result = CliRunner().invoke(app, ["analyze", "--symbol", "ABC", "--mock-llm"])

    assert result.exit_code != 0
    assert "6-digit" in result.output


def test_cli_passes_include_node_trace_flag(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    class FakeProvider:
        def fetch(self, symbol: str, days: int):
            captured["symbol"] = symbol
            captured["days"] = days
            return object()

    class FakePipeline:
        def __init__(self, llm, max_debate_rounds: int = 1, include_node_trace: bool = False):
            captured["include_node_trace"] = include_node_trace

        def run(self, dataset):
            captured["dataset_passed"] = dataset
            return AnalysisReport(
                symbol="600519",
                analysis_date="2026-04-28",
                data_range="2026-04-01 至 2026-04-28",
                core_summary="测试摘要",
                fundamentals=AgentResult(agent="基本面分析师", summary="基本面测试"),
                technical=AgentResult(agent="技术面分析师", summary="技术面测试"),
                news=AgentResult(agent="新闻情绪分析师", summary="新闻测试"),
                bull=AgentResult(agent="多头研究员", summary="多头测试"),
                bear=AgentResult(agent="空头研究员", summary="空头测试"),
                trader=AgentResult(agent="交易员", summary="HOLD"),
                risk=AgentResult(agent="风控经理", summary="风控测试"),
                recommendation="HOLD",
                risk_notes=["测试风险"],
                disclaimer="测试免责声明",
                node_trace=["Technical Analyst"],
            )

    class FakeWriter:
        def write(self, report: AnalysisReport, output_dir: Path):
            captured["written_report"] = report
            captured["output_dir"] = output_dir
            return output_dir / "report.md", output_dir / "result.json"

    monkeypatch.setattr("stock_agent_lab.cli.AkShareChinaStockProvider", FakeProvider)
    monkeypatch.setattr("stock_agent_lab.cli.AnalysisPipeline", FakePipeline)
    monkeypatch.setattr("stock_agent_lab.cli.ReportWriter", FakeWriter)

    result = CliRunner().invoke(
        app,
        [
            "analyze",
            "--symbol",
            "600519",
            "--days",
            "30",
            "--mock-llm",
            "--include-node-trace",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert captured["include_node_trace"] is True
    assert captured["output_dir"] == tmp_path
