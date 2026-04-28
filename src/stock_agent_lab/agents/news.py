"""
模块作用：
- 实现新闻情绪分析师，基于新闻列表判断情绪和潜在事件风险。
- 当 graph 中存在工具回路时，会优先消费 tools_news 节点准备好的新闻摘要文本。
联动关系：
- graph/setup.py 将它注册为 News Analyst 节点。
- agents/base.py 提供统一 Agent 调用逻辑和新闻格式化函数。
运行示例：
- python -m pytest tests/test_graph_workflow.py
"""

from __future__ import annotations

from stock_agent_lab.agents.base import Agent, format_news
from stock_agent_lab.models import AgentResult, StockDataset


class NewsSentimentAnalyst(Agent):
    name = "新闻情绪分析师"
    system_prompt = "新闻情绪分析师\n你专注A股新闻情绪和风险事件。输出中文，避免夸大。"

    def build_prompt(self, dataset: StockDataset, context: dict[str, AgentResult]) -> str:
        news_source = context.get("news_tool_data")
        news_text = news_source.summary if news_source else format_news(dataset)
        return (
            "请基于以下新闻判断情绪和潜在风险。若新闻不足，要明确说明信息有限。\n\n"
            f"股票代码: {dataset.symbol}\n"
            f"{news_text}"
        )
