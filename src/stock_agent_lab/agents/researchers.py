"""
模块作用：
- 实现多头和空头研究员，围绕技术面、新闻情绪和辩论历史进行正反论证。

联动关系：
- 被 graph.GraphSetup 注册为 Bull/Bear Researcher 节点，并读写 investment_debate_state。
"""

from __future__ import annotations

from stock_agent_lab.agents.base import Agent
from stock_agent_lab.models import AgentResult, StockDataset


class BullResearcher(Agent):
    name = "多头研究员"
    system_prompt = "多头研究员\n你负责提出支持买入或继续持有的最强理由，但不能忽略事实约束。"

    def build_prompt(self, dataset: StockDataset, context: dict[str, AgentResult]) -> str:
        # 研究员只接收必要上下文，不直接读取 Graph state，保持 Agent 可单独测试。
        debate_history = context.get("debate_history")
        last_argument = context.get("last_argument")
        return (
            f"股票代码: {dataset.symbol}\n"
            f"技术面结论:\n{context['technical'].summary}\n\n"
            f"新闻情绪结论:\n{context['news'].summary}\n\n"
            f"已有辩论历史:\n{debate_history.summary if debate_history else '暂无'}\n\n"
            f"上一轮观点:\n{last_argument.summary if last_argument else '暂无'}\n\n"
            "请提出多头观点，并列出最关键的验证条件。"
        )


class BearResearcher(Agent):
    name = "空头研究员"
    system_prompt = "空头研究员\n你负责提出反对买入或需要减仓的最强理由，强调风险和反证。"

    def build_prompt(self, dataset: StockDataset, context: dict[str, AgentResult]) -> str:
        # 空头研究员同样读取辩论历史，用来直接回应多头上一轮观点。
        debate_history = context.get("debate_history")
        last_argument = context.get("last_argument")
        return (
            f"股票代码: {dataset.symbol}\n"
            f"技术面结论:\n{context['technical'].summary}\n\n"
            f"新闻情绪结论:\n{context['news'].summary}\n\n"
            f"已有辩论历史:\n{debate_history.summary if debate_history else '暂无'}\n\n"
            f"上一轮观点:\n{last_argument.summary if last_argument else '暂无'}\n\n"
            "请提出空头观点，并列出最关键的风险触发条件。"
        )
