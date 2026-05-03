"""
模块作用：
- 提供 pytest 共享测试夹具，构造稳定的股票样例数据。

联动关系：
- pipeline、reports、graph 等测试复用 sample_dataset，避免真实 AkShare 和真实 LLM 依赖。
"""

from __future__ import annotations

import pytest

from stock_agent_lab.models import (
    FundamentalsSnapshot,
    NewsItem,
    PriceBar,
    StockDataset,
    TechnicalSnapshot,
)


@pytest.fixture
def sample_dataset() -> StockDataset:
    prices = [
        PriceBar(date=f"2026-01-{day:02d}", open=10 + day, high=11 + day, low=9 + day, close=10.5 + day, volume=1000 + day)
        for day in range(1, 31)
    ]
    return StockDataset(
        symbol="600519",
        start_date=prices[0].date,
        end_date=prices[-1].date,
        prices=prices,
        technicals=TechnicalSnapshot(
            latest_close=40.5,
            return_pct=25.0,
            volatility_pct=1.8,
            ma5=38.0,
            ma20=31.0,
            ma60=None,
            volume_change_pct=8.5,
        ),
        fundamentals=FundamentalsSnapshot(
            latest_pe=25.5,
            latest_pb=6.8,
            latest_roe=18.5,
            eps=2.45,
            net_profit_margin=35.2,
            debt_ratio=28.0,
            revenue_growth_pct=12.3,
            profit_growth_pct=15.1,
            _raw_summary="mock fundamentals data",
        ),
        news=[
            NewsItem(title="公司发布经营动态", published_at="2026-01-30", source="测试新闻"),
            NewsItem(title="行业需求保持稳定", published_at="2026-01-29", source="测试新闻"),
        ],
    )
