"""
模块作用：
- 实现交易员 Agent，综合分析师和研究员观点输出 BUY/HOLD/SELL 建议。

联动关系：
- 被 graph.GraphSetup 注册为 Trader 节点，pipeline 使用 extract_recommendation 解析最终建议。
"""

from __future__ import annotations

import re

from stock_agent_lab.agents.base import Agent
from stock_agent_lab.models import AgentResult, Recommendation, StockDataset


class TraderAgent(Agent):
    name = "交易员"
    system_prompt = (
        "交易员\n你负责综合技术面、新闻、多头和空头观点，给出 BUY/HOLD/SELL 三选一建议。"
        "回复必须包含一行 '建议: BUY'、'建议: HOLD' 或 '建议: SELL'。"
    )

    def build_prompt(self, dataset: StockDataset, context: dict[str, AgentResult]) -> str:
        # investment_plan 来自研究经理，是交易员在多空观点之上的汇总参考。
        investment_plan = context.get("investment_plan")
        return (
            f"股票代码: {dataset.symbol}\n"
            f"技术面:\n{context['technical'].summary}\n\n"
            f"新闻情绪:\n{context['news'].summary}\n\n"
            f"多头观点:\n{context['bull'].summary}\n\n"
            f"空头观点:\n{context['bear'].summary}\n\n"
            f"研究经理汇总:\n{investment_plan.summary if investment_plan else '暂无'}\n\n"
            "请给出最终交易建议、理由和需要等待确认的信号。"
        )

    @staticmethod
    def extract_recommendation(text: str) -> Recommendation:
        match = re.search(r"\b(BUY|HOLD|SELL)\b", text.upper())
        if not match:
            return "HOLD"
        return match.group(1)  # type: ignore[return-value]
