"""
模块作用：
- 测试 AnalysisPipeline 能用 Mock LLM 跑完整多 Agent 流程。
- 额外验证 node_trace 默认关闭，以及打开开关后会被带入报告对象。
联动关系：
- 覆盖 pipeline、graph、agents 和 models 的集成路径，不依赖真实模型 API。
运行示例：
- python -m pytest tests/test_pipeline.py
"""

from __future__ import annotations

from stock_agent_lab.llm import MockLLMClient
from stock_agent_lab.pipeline import AnalysisPipeline


def test_pipeline_runs_with_mock_llm(sample_dataset):
    report = AnalysisPipeline(MockLLMClient()).run(sample_dataset)

    assert report.symbol == "600519"
    assert report.recommendation == "HOLD"
    assert report.technical.summary
    assert report.news.summary
    assert report.bull.summary
    assert report.bear.summary
    assert report.trader.summary
    assert report.risk.summary
    assert "不构成任何投资建议" in report.disclaimer
    assert report.node_trace == []


def test_pipeline_can_include_node_trace(sample_dataset):
    report = AnalysisPipeline(MockLLMClient(), include_node_trace=True).run(sample_dataset)

    assert report.node_trace
    assert report.node_trace[0] == "Technical Analyst"
    assert "tools_technical" in report.node_trace
    assert report.node_trace[-1] == "Risk Manager"
