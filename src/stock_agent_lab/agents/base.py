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


def format_fundamentals(dataset: StockDataset) -> str:
    """将 FundamentalsSnapshot 格式化为 LLM 可读的中文文本。"""
    if not dataset.fundamentals:
        return "无可用基本面数据。"
    f = dataset.fundamentals
    lines = [f"股票代码: {dataset.symbol}"]
    if f.latest_pe is not None:
        lines.append(f"市盈率(PE): {f.latest_pe:.2f}")
    if f.latest_pb is not None:
        lines.append(f"市净率(PB): {f.latest_pb:.2f}")
    if f.latest_roe is not None:
        lines.append(f"净资产收益率(ROE): {f.latest_roe:.2f}%")
    if f.eps is not None:
        lines.append(f"每股收益(EPS): {f.eps:.4f}")
    if f.net_profit_margin is not None:
        lines.append(f"净利润率: {f.net_profit_margin:.2f}%")
    if f.debt_ratio is not None:
        lines.append(f"资产负债率: {f.debt_ratio:.2f}%")
    if f.revenue_growth_pct is not None:
        lines.append(f"营收同比增长: {f.revenue_growth_pct:.2f}%")
    if f.profit_growth_pct is not None:
        lines.append(f"净利润同比增长: {f.profit_growth_pct:.2f}%")
    if f._raw_summary:
        lines.append(f"\n原始数据详情:\n{f._raw_summary}")
    return "\n".join(lines)


def format_news(dataset: StockDataset) -> str:
    if not dataset.news:
        return "无可用新闻。"
    return "\n".join(
        f"- {item.published_at or '未知时间'} {item.source or '未知来源'}: {item.title}"
        for item in dataset.news
    )
