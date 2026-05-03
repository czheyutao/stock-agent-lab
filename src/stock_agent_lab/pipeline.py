"""
模块作用：
- 提供面向 CLI 和报告层的稳定分析入口，把图编排结果转换成 AnalysisReport。
- 支持通过开关决定是否把 LangGraph 的 node_trace 暴露到最终报告。
联动关系：
- 调用 graph.StockAnalysisGraph 执行多 Agent 流程。
- 将 models.AnalysisReport 交给 reports.writer 输出。
运行示例：
- python -m pytest tests/test_pipeline.py
"""

from __future__ import annotations

from datetime import date

from stock_agent_lab.agents import TraderAgent
from stock_agent_lab.graph import StockAnalysisGraph
from stock_agent_lab.llm import LLMClient
from stock_agent_lab.models import AgentResult, AnalysisReport, StockDataset


DISCLAIMER = "本报告仅用于学习和研究多 Agent 分析流程，不构成任何投资建议或交易依据。"
DEFAULT_RISK_NOTES = [
    "A股存在政策、流动性、财报、行业周期和市场情绪波动风险。",
    "模型输出可能遗漏或误读信息，应结合公告、财务数据和个人风险承受能力复核。",
]


class AnalysisPipeline:
    """面向 CLI/报告层的稳定入口，内部使用图编排执行多 Agent。"""

    def __init__(
        self,
        llm: LLMClient,
        max_debate_rounds: int = 1,
        include_node_trace: bool = False,
    ) -> None:
        self.graph = StockAnalysisGraph(llm, max_debate_rounds=max_debate_rounds)
        self.include_node_trace = include_node_trace

    def run(self, dataset: StockDataset) -> AnalysisReport:
        state = self.graph.run(dataset)
        results = state["results"]
        trader_summary = results["trader"].summary
        recommendation = TraderAgent.extract_recommendation(trader_summary)

        return AnalysisReport(
            symbol=dataset.symbol,
            analysis_date=date.today().isoformat(),
            data_range=f"{dataset.start_date} 至 {dataset.end_date}",
            core_summary=f"{dataset.symbol} 当前多 Agent 综合建议为 {recommendation}。",
            fundamentals=results.get(
                "fundamentals", AgentResult(agent="基本面分析师", summary="无可用基本面数据。")
            ),
            technical=results["technical"],
            news=results["news"],
            bull=results["bull"],
            bear=results["bear"],
            trader=results["trader"],
            risk=results["risk"],
            recommendation=recommendation,
            risk_notes=list(DEFAULT_RISK_NOTES),
            disclaimer=DISCLAIMER,
            warnings=dataset.warnings,
            node_trace=self._build_node_trace(state),
        )

    def _build_node_trace(self, state: dict) -> list[str]:
        if not self.include_node_trace:
            return []
        return list(state["node_trace"])
