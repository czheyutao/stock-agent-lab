"""
模块作用：
- 实现风控经理，负责在交易员建议之后补充风险提示和仓位控制建议。

联动关系：
- 被 graph.GraphSetup 注册为 Risk Manager 节点，最终报告会展示它的输出。
"""

from __future__ import annotations

from stock_agent_lab.agents.base import Agent
from stock_agent_lab.models import AgentResult, StockDataset


class RiskManager(Agent):
    name = "风控经理"
    system_prompt = "风控经理\n你负责补充A股投资风险、仓位建议和免责声明。输出中文，务必谨慎。"

    def build_prompt(self, dataset: StockDataset, context: dict[str, AgentResult]) -> str:
        return (
            f"股票代码: {dataset.symbol}\n"
            f"交易员建议:\n{context['trader'].summary}\n\n"
            "请给出风险提示、仓位控制建议和非投资建议声明。"
        )
