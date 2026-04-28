"""
模块作用：
- 定义股票数据、Agent 输出和最终分析报告的核心数据结构。
- 当前版本还为报告对象增加了可选的 node_trace，用于输出 LangGraph 的实际执行轨迹。
联动关系：
- data 层产出 StockDataset。
- agents 层产出 AgentResult。
- pipeline、reports、cli 层消费 AnalysisReport。
运行示例：
- python -m pytest tests/test_pipeline.py
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Literal


Recommendation = Literal["BUY", "HOLD", "SELL"]


@dataclass
class PriceBar:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class TechnicalSnapshot:
    latest_close: float
    return_pct: float
    volatility_pct: float
    ma5: float | None
    ma20: float | None
    ma60: float | None
    volume_change_pct: float | None


@dataclass
class NewsItem:
    title: str
    url: str | None = None
    published_at: str | None = None
    source: str | None = None


@dataclass
class StockDataset:
    symbol: str
    start_date: str
    end_date: str
    prices: list[PriceBar]
    technicals: TechnicalSnapshot
    news: list[NewsItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class AgentResult:
    agent: str
    summary: str
    details: list[str] = field(default_factory=list)


@dataclass
class AnalysisReport:
    symbol: str
    analysis_date: str
    data_range: str
    core_summary: str
    technical: AgentResult
    news: AgentResult
    bull: AgentResult
    bear: AgentResult
    trader: AgentResult
    risk: AgentResult
    recommendation: Recommendation
    risk_notes: list[str]
    disclaimer: str
    warnings: list[str] = field(default_factory=list)
    # node_trace 默认空列表，只有 CLI 显式打开开关时才会被填入实际执行轨迹。
    node_trace: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def today_empty(cls, symbol: str) -> "AnalysisReport":
        empty = AgentResult(agent="empty", summary="")
        today = date.today().isoformat()
        return cls(
            symbol=symbol,
            analysis_date=today,
            data_range="",
            core_summary="",
            technical=empty,
            news=empty,
            bull=empty,
            bear=empty,
            trader=empty,
            risk=empty,
            recommendation="HOLD",
            risk_notes=[],
            disclaimer="本报告仅用于学习和研究，不构成任何投资建议。",
            node_trace=[],
        )
