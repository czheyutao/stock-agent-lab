"""
模块作用：
- 测试轻量图编排的节点顺序和多轮辩论路由。

联动关系：
- 直接验证 graph.StockAnalysisGraph，确保 pipeline 和 CLI 依赖的编排核心稳定。
"""

from __future__ import annotations

from stock_agent_lab.graph import StockAnalysisGraph
from stock_agent_lab.llm import MockLLMClient


def test_graph_runs_expected_node_trace(sample_dataset):
    state = StockAnalysisGraph(MockLLMClient()).run(sample_dataset)

    assert state["node_trace"] == [
        "Fundamentals Analyst",
        "tools_fundamentals",
        "Fundamentals Analyst",
        "Msg Clear Fundamentals",
        "Technical Analyst",
        "tools_technical",
        "Technical Analyst",
        "Msg Clear Technical",
        "News Analyst",
        "tools_news",
        "News Analyst",
        "Msg Clear News",
        "Bull Researcher",
        "Bear Researcher",
        "Research Manager",
        "Trader",
        "Risk Manager",
    ]
    assert state["investment_debate_state"]["count"] == 2
    assert state["investment_plan"]
    assert state["final_trade_decision"]
    assert set(state["results"]) == {"fundamentals", "technical", "news", "bull", "bear", "trader", "risk"}
    assert state["tool_call_count"] == {"fundamentals": 1, "technical": 1, "news": 1}
    assert state["tool_outputs"] == {"fundamentals": "", "technical": "", "news": ""}


def test_graph_supports_multiple_debate_rounds(sample_dataset):
    state = StockAnalysisGraph(MockLLMClient(), max_debate_rounds=2).run(sample_dataset)

    assert state["node_trace"].count("Fundamentals Analyst") == 2
    assert state["node_trace"].count("Bull Researcher") == 2
    assert state["node_trace"].count("Bear Researcher") == 2
    assert state["node_trace"].count("tools_fundamentals") == 1
    assert state["node_trace"].count("tools_technical") == 1
    assert state["node_trace"].count("tools_news") == 1
    assert state["investment_debate_state"]["count"] == 4
    assert state["node_trace"][-3:] == ["Research Manager", "Trader", "Risk Manager"]
