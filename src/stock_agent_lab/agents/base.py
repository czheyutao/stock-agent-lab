"""
模块作用：
- 定义 Agent 基类和通用格式化工具，统一每个 Agent 的 LLM 调用方式。

联动关系：
- technical/news/researchers/trader/risk 继承 Agent；data 层的 StockDataset 会在这里被格式化成提示词素材。
"""

from __future__ import annotations

from stock_agent_lab.llm import LLMClient
from stock_agent_lab.models import AgentResult, StockDataset


class Agent:
    name = "Agent"
    system_prompt = "你是一个谨慎的股票分析助手。"

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def run(self, dataset: StockDataset, context: dict[str, AgentResult] | None = None) -> AgentResult:
        response = self.llm.complete(self.system_prompt, self.build_prompt(dataset, context or {})).strip()
        return AgentResult(agent=self.name, summary=response)

    def build_prompt(self, dataset: StockDataset, context: dict[str, AgentResult]) -> str:
        raise NotImplementedError


def format_technicals(dataset: StockDataset) -> str:
    tech = dataset.technicals
    return "\n".join(
        [
            f"股票代码: {dataset.symbol}",
            f"数据区间: {dataset.start_date} 至 {dataset.end_date}",
            f"最新收盘价: {tech.latest_close:.2f}",
            f"区间涨跌幅: {tech.return_pct:.2f}%",
            f"日收益波动率: {tech.volatility_pct:.2f}%",
            f"MA5: {tech.ma5:.2f}" if tech.ma5 is not None else "MA5: N/A",
            f"MA20: {tech.ma20:.2f}" if tech.ma20 is not None else "MA20: N/A",
            f"MA60: {tech.ma60:.2f}" if tech.ma60 is not None else "MA60: N/A",
            f"近5日成交量相对前5日变化: {tech.volume_change_pct:.2f}%"
            if tech.volume_change_pct is not None
            else "近5日成交量相对前5日变化: N/A",
        ]
    )


def format_news(dataset: StockDataset) -> str:
    if not dataset.news:
        return "无可用新闻。"
    return "\n".join(
        f"- {item.published_at or '未知时间'} {item.source or '未知来源'}: {item.title}"
        for item in dataset.news
    )
