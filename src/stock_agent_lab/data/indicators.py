"""
模块作用：
- 计算轻量技术指标快照，例如区间收益率、波动率、均线和成交量变化。

联动关系：
- data.akshare_provider 调用 compute_technicals，并把结果写入 models.StockDataset。
"""

from __future__ import annotations

import pandas as pd

from stock_agent_lab.models import TechnicalSnapshot


def compute_technicals(df: pd.DataFrame) -> TechnicalSnapshot:
    if df.empty:
        raise ValueError("Cannot compute technical indicators from empty price data.")

    closes = df["close"].astype(float)
    volumes = df["volume"].astype(float)
    latest_close = float(closes.iloc[-1])
    first_close = float(closes.iloc[0])
    return_pct = ((latest_close / first_close) - 1.0) * 100 if first_close else 0.0
    volatility_pct = float(closes.pct_change().dropna().std() * 100)

    volume_change_pct = None
    if len(volumes) >= 10:
        recent = float(volumes.tail(5).mean())
        previous = float(volumes.tail(10).head(5).mean())
        if previous:
            volume_change_pct = ((recent / previous) - 1.0) * 100

    def ma(window: int) -> float | None:
        if len(closes) < window:
            return None
        return float(closes.rolling(window).mean().iloc[-1])

    return TechnicalSnapshot(
        latest_close=latest_close,
        return_pct=return_pct,
        volatility_pct=volatility_pct,
        ma5=ma(5),
        ma20=ma(20),
        ma60=ma(60),
        volume_change_pct=volume_change_pct,
    )
