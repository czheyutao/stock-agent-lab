"""
模块作用：
- 测试 AkShare 数据适配器的输入校验、字段映射、代理重试、AkShare 内部 fallback 和异常包装。
联动关系：
- 覆盖 data.akshare_provider，保护 CLI 在数据源失败时能得到清晰错误。
运行示例：
- python -m pytest tests/test_data_provider.py
"""

from __future__ import annotations

import os
import sys
import types

import pandas as pd
import pytest

from stock_agent_lab.data import AkShareChinaStockProvider, DataProviderError


def test_invalid_symbol_fails_clearly():
    with pytest.raises(DataProviderError, match="6-digit"):
        AkShareChinaStockProvider().fetch("ABC", 90)


def test_history_exception_is_wrapped(monkeypatch):
    fake_akshare = types.SimpleNamespace(
        stock_zh_a_hist=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("network down")),
        stock_zh_a_daily=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("network down")),
    )
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)

    with pytest.raises(DataProviderError, match="Failed to fetch A-share daily history"):
        AkShareChinaStockProvider().fetch_history("600519", 90)


def test_history_columns_are_normalized_and_trimmed(monkeypatch):
    raw = pd.DataFrame(
        [
            {"日期": "2026-01-01", "开盘": 10, "最高": 11, "最低": 9, "收盘": 10.5, "成交量": 1000},
            {"日期": "2026-01-02", "开盘": 11, "最高": 12, "最低": 10, "收盘": 11.5, "成交量": 1100},
            {"日期": "2026-01-03", "开盘": 12, "最高": 13, "最低": 11, "收盘": 12.5, "成交量": 1200},
        ]
    )
    fake_akshare = types.SimpleNamespace(stock_zh_a_hist=lambda **kwargs: raw)
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)

    df = AkShareChinaStockProvider().fetch_history("600519", 2)

    assert list(df.columns) == ["date", "open", "high", "low", "close", "volume"]
    assert len(df) == 2
    assert df.iloc[0]["date"] == "2026-01-02"


def test_history_retries_without_proxy(monkeypatch):
    calls: list[dict[str, str | None]] = []

    def fake_hist(**kwargs):
        calls.append({"https_proxy": os.environ.get("HTTPS_PROXY")})
        if len(calls) == 1:
            raise RuntimeError("ProxyError: unable to connect to proxy")
        return pd.DataFrame(
            [{"日期": "2026-01-03", "开盘": 12, "最高": 13, "最低": 11, "收盘": 12.5, "成交量": 1200}]
        )

    fake_akshare = types.SimpleNamespace(stock_zh_a_hist=fake_hist)
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)
    monkeypatch.setenv("HTTPS_PROXY", "http://broken-proxy:7890")

    df = AkShareChinaStockProvider().fetch_history("600519", 1)

    assert len(calls) == 2
    assert calls[0]["https_proxy"] == "http://broken-proxy:7890"
    assert calls[1]["https_proxy"] is None
    assert os.environ.get("HTTPS_PROXY") == "http://broken-proxy:7890"
    assert df.iloc[0]["close"] == 12.5


def test_history_falls_back_to_sina_daily(monkeypatch):
    raw = pd.DataFrame(
        [
            {"date": "2026-01-01", "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 1000},
            {"date": "2026-01-02", "open": 11, "high": 12, "low": 10, "close": 11.5, "volume": 1100},
        ]
    )

    fake_akshare = types.SimpleNamespace(
        stock_zh_a_hist=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("eastmoney unavailable")),
        stock_zh_a_daily=lambda **kwargs: raw,
    )
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)

    df = AkShareChinaStockProvider().fetch_history("600519", 2)

    assert len(df) == 2
    assert list(df.columns) == ["date", "open", "high", "low", "close", "volume"]
    assert df.iloc[-1]["close"] == 11.5


def test_news_fields_are_parsed(monkeypatch):
    raw = pd.DataFrame(
        [
            {
                "新闻标题": "公司发布经营动态",
                "新闻链接": "https://example.com/news-1",
                "发布时间": "2026-01-30 10:00:00",
                "文章来源": "测试来源",
            }
        ]
    )
    fake_akshare = types.SimpleNamespace(stock_news_em=lambda **kwargs: raw)
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)

    news, warnings = AkShareChinaStockProvider().fetch_news("600519")

    assert warnings == []
    assert len(news) == 1
    assert news[0].title == "公司发布经营动态"
    assert news[0].url == "https://example.com/news-1"
    assert news[0].source == "测试来源"


def test_fundamentals_returns_none_when_no_data(monkeypatch):
    fake_akshare = types.SimpleNamespace(
        stock_financial_analysis_indicator=lambda **kwargs: (
            _ for _ in ()
        ).throw(RuntimeError("no data")),
        stock_zh_a_spot_em=lambda: (_ for _ in ()).throw(RuntimeError("no data")),
    )
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)

    result, warnings = AkShareChinaStockProvider().fetch_fundamentals("600519")
    assert result is None
    assert len(warnings) > 0


def test_fundamentals_extracts_snapshot(monkeypatch):
    analysis_raw = pd.DataFrame(
        [
            {
                "净资产收益率(%)": 18.5,
                "每股收益_调整后(元)": 2.45,
                "销售净利率(%)": 35.2,
                "资产负债率(%)": 28.0,
                "主营业务收入增长率(%)": 12.3,
                "净利润增长率(%)": 15.1,
            }
        ]
    )
    spot_df = pd.DataFrame(
        [
            {
                "代码": "600519",
                "市盈率-动态": 25.5,
                "市净率": 6.8,
            },
            {
                "代码": "000001",
                "市盈率-动态": 5.0,
                "市净率": 0.8,
            },
        ]
    )
    fake_akshare = types.SimpleNamespace(
        stock_financial_analysis_indicator=lambda **kwargs: analysis_raw,
        stock_zh_a_spot_em=lambda: spot_df,
    )
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)

    result, warnings = AkShareChinaStockProvider().fetch_fundamentals("600519")
    assert result is not None
    assert result.latest_pe == 25.5
    assert result.latest_pb == 6.8
    assert result.latest_roe == 18.5
    assert result.eps == 2.45
    assert result.revenue_growth_pct == 12.3
    assert result.profit_growth_pct == 15.1
    assert result.net_profit_margin == 35.2
    assert result.debt_ratio == 28.0


def test_fundamentals_falls_back_on_partial_failure(monkeypatch):
    """financial_analysis 成功但 spot 失败时仍有快照，PE/PB 为 None。"""
    analysis_raw = pd.DataFrame(
        [
            {
                "净资产收益率(%)": 18.5,
                "每股收益_调整后(元)": 2.45,
                "销售净利率(%)": 35.2,
                "资产负债率(%)": 28.0,
                "主营业务收入增长率(%)": 12.3,
                "净利润增长率(%)": 15.1,
            }
        ]
    )
    fake_akshare = types.SimpleNamespace(
        stock_financial_analysis_indicator=lambda **kwargs: analysis_raw,
        stock_zh_a_spot_em=lambda: (_ for _ in ()).throw(RuntimeError("timeout")),
    )
    monkeypatch.setitem(sys.modules, "akshare", fake_akshare)

    result, warnings = AkShareChinaStockProvider().fetch_fundamentals("600519")
    assert result is not None
    assert result.latest_pe is None
    assert result.latest_pb is None
    assert result.latest_roe == 18.5
    assert result.revenue_growth_pct == 12.3
