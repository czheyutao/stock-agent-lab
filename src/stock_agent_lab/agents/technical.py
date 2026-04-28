"""
模块作用：
- 实现技术面分析师，基于价格、均线、波动率和成交量生成技术面观点。
- 当 graph 中存在工具回路时，会优先消费 tools_technical 节点准备好的技术面文本。
联动关系：
- graph/setup.py 将它注册为 Technical Analyst 节点。
- agents/base.py 提供统一 Agent 调用逻辑和技术指标格式化函数。
运行示例：
- python -m pytest tests/test_graph_workflow.py
"""

from __future__ import annotations

from stock_agent_lab.agents.base import Agent, format_technicals
from stock_agent_lab.models import AgentResult, StockDataset


class TechnicalAnalyst(Agent):
    name = "技术面分析师"
    system_prompt = "技术面分析师\n你专注A股日线趋势、均线、波动率和成交量。输出中文，简洁但有判断。"

    def build_prompt(self, dataset: StockDataset, context: dict[str, AgentResult]) -> str:
        technical_source = context.get("technical_tool_data")
        technical_text = technical_source.summary if technical_source else format_technicals(dataset)
        return (
            "请基于以下数据总结技术面，必须覆盖趋势、均线、波动和成交量，最后给出偏多、中性、偏空倾向。\n\n"
            f"{technical_text}"
        )
