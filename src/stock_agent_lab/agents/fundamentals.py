"""
模块作用：
- 实现基本面分析师，基于估值、盈利质量、成长趋势和财务健康度生成分析。
- 当 graph 中存在工具回路时，会优先消费 tools_fundamentals 节点准备好的基本面文本。
联动关系：
- graph/setup.py 将它注册为 Fundamentals Analyst 节点。
- agents/base.py 提供统一 Agent 调用逻辑和基本面格式化函数。
运行示例：
- python -m pytest tests/test_graph_workflow.py
"""

from __future__ import annotations

from stock_agent_lab.agents.base import Agent, format_fundamentals
from stock_agent_lab.models import AgentResult, StockDataset


class FundamentalsAnalyst(Agent):
    name = "基本面分析师"
    system_prompt = (
        "基本面分析师\n"
        "你专注A股财务基本面分析，包括估值水平(PE/PB)、盈利质量(ROE、净利润率)、"
        "成长趋势（营收/利润增长）和财务健康度（资产负债率）。"
        "输出中文，简洁但有判断。"
    )

    def build_prompt(self, dataset: StockDataset, context: dict[str, AgentResult]) -> str:
        fundamentals_source = context.get("fundamentals_tool_data")
        fundamentals_text = (
            fundamentals_source.summary if fundamentals_source else format_fundamentals(dataset)
        )
        return (
            "请基于以下基本面数据进行分析，必须覆盖估值水平、盈利质量、成长趋势和财务健康度，"
            "最后给出偏多、中性、偏空倾向。\n\n"
            f"{fundamentals_text}"
        )
