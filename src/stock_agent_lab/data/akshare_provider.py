"""
模块作用：
- 封装 AkShare 的 A 股历史行情和新闻抓取逻辑，并转换成项目内部统一数据模型。
- 参考原项目补了东方财富请求头、代理失败重试，以及 AkShare 内部的东财/新浪双通路 fallback。
联动关系：
- cli.py 调用 AkShareChinaStockProvider.fetch 获取分析所需数据。
- indicators.py 对历史行情 DataFrame 计算技术指标。
运行示例：
- python -m pytest tests/test_data_provider.py
- stock-agent analyze --symbol 600519 --days 30 --mock-llm
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Callable, TypeVar

import pandas as pd

from stock_agent_lab.data.indicators import compute_technicals
from stock_agent_lab.models import NewsItem, PriceBar, StockDataset

T = TypeVar("T")


HISTORY_COLUMN_CANDIDATES = {
    "date": ("日期", "date"),
    "open": ("开盘", "open"),
    "high": ("最高", "high"),
    "low": ("最低", "low"),
    "close": ("收盘", "close"),
    "volume": ("成交量", "volume"),
}

NEWS_TITLE_COLUMNS = ("新闻标题", "标题")
NEWS_URL_COLUMNS = ("新闻链接", "链接")
NEWS_TIME_COLUMNS = ("发布时间", "时间")
NEWS_SOURCE_COLUMNS = ("文章来源", "来源", "新闻来源")

EASTMONEY_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.eastmoney.com/",
    "Connection": "keep-alive",
}

PROXY_ENV_KEYS = [
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
]


class DataProviderError(RuntimeError):
    """数据获取失败时抛出的统一异常。"""


class AkShareChinaStockProvider:
    """面向当前项目的轻量 AkShare Provider。"""

    def fetch(self, symbol: str, days: int) -> StockDataset:
        self._validate_request(symbol, days)

        history = self.fetch_history(symbol, days)
        news, warnings = self.fetch_news(symbol)
        technicals = compute_technicals(history)
        prices = [self._build_price_bar(row) for row in history.itertuples(index=False)]

        return StockDataset(
            symbol=symbol,
            start_date=prices[0].date,
            end_date=prices[-1].date,
            prices=prices,
            technicals=technicals,
            news=news,
            warnings=warnings,
        )

    def fetch_history(self, symbol: str, days: int) -> pd.DataFrame:
        ak = self._prepare_akshare()
        errors: list[str] = []

        for source_name, loader in self._history_loaders(ak, symbol):
            try:
                raw = self._call_with_proxy_retry(loader)
                return self._normalize_history_dataframe(raw, days)
            except Exception as exc:
                errors.append(f"{source_name}: {exc}")

        raise DataProviderError(
            f"Failed to fetch A-share daily history for {symbol}: " + " | ".join(errors)
        )

    def fetch_news(self, symbol: str) -> tuple[list[NewsItem], list[str]]:
        warnings: list[str] = []
        try:
            ak = self._prepare_akshare()
        except DataProviderError as exc:
            return [], [f"News skipped because AkShare cannot be imported: {exc}"]

        try:
            raw = self._call_with_proxy_retry(lambda: ak.stock_news_em(symbol=symbol))
        except Exception as exc:
            return [], [f"News fetch failed for {symbol}: {exc}"]

        if raw is None or raw.empty:
            return [], [f"No news returned for {symbol}."]

        items = [
            item
            for item in (self._build_news_item(row) for _, row in raw.head(10).iterrows())
            if item is not None
        ]
        return items, warnings

    @staticmethod
    def _validate_request(symbol: str, days: int) -> None:
        if not symbol.isdigit() or len(symbol) != 6:
            raise DataProviderError("A-share symbol must be a 6-digit code, for example 600519.")
        if days <= 0:
            raise DataProviderError("days must be greater than 0.")

    def _prepare_akshare(self):
        ak = self._import_akshare()
        self._patch_eastmoney_requests()
        return ak

    @staticmethod
    def _import_akshare():
        try:
            import akshare as ak
        except Exception as exc:
            raise DataProviderError("AkShare is not installed or cannot be imported.") from exc
        return ak

    def _history_loaders(self, ak, symbol: str) -> list[tuple[str, Callable[[], pd.DataFrame]]]:
        return [
            ("eastmoney", lambda: self._fetch_eastmoney_history(ak, symbol)),
            ("sina", lambda: self._fetch_sina_history(ak, symbol)),
        ]

    @staticmethod
    def _fetch_eastmoney_history(ak, symbol: str) -> pd.DataFrame:
        # 请求宽范围数据，再在本地裁剪最后 N 天，避免系统日期偏差影响窗口选择。
        return ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date="19700101",
            end_date="20500101",
            adjust="qfq",
            timeout=15,
        )

    @staticmethod
    def _fetch_sina_history(ak, symbol: str) -> pd.DataFrame:
        # 仍然留在 AkShare 体系内，只是从东财退回新浪历史接口。
        sina_symbol = f"sh{symbol}" if symbol.startswith("6") else f"sz{symbol}"
        return ak.stock_zh_a_daily(
            symbol=sina_symbol,
            start_date="19900101",
            end_date="21000101",
            adjust="qfq",
        )

    @staticmethod
    def _build_price_bar(row) -> PriceBar:
        return PriceBar(
            date=str(row.date),
            open=float(row.open),
            high=float(row.high),
            low=float(row.low),
            close=float(row.close),
            volume=float(row.volume),
        )

    def _build_news_item(self, row: pd.Series) -> NewsItem | None:
        title = self._first_non_empty(row, NEWS_TITLE_COLUMNS).strip()
        if not title:
            return None

        return NewsItem(
            title=title,
            url=self._first_non_empty(row, NEWS_URL_COLUMNS).strip() or None,
            published_at=self._first_non_empty(row, NEWS_TIME_COLUMNS).strip() or None,
            source=self._first_non_empty(row, NEWS_SOURCE_COLUMNS).strip() or None,
        )

    @staticmethod
    def _normalize_history_dataframe(raw: pd.DataFrame, days: int) -> pd.DataFrame:
        if raw is None or raw.empty:
            raise DataProviderError("No daily history returned.")

        rename_map: dict[str, str] = {}
        missing: list[str] = []
        for target, candidates in HISTORY_COLUMN_CANDIDATES.items():
            source = next((name for name in candidates if name in raw.columns), None)
            if source is None:
                missing.append("/".join(candidates))
            else:
                rename_map[source] = target

        if missing:
            raise DataProviderError(f"AkShare history data missing columns: {', '.join(missing)}")

        df = raw.rename(columns=rename_map)[list(HISTORY_COLUMN_CANDIDATES.keys())].copy()
        df["date"] = df["date"].astype(str)
        return df.sort_values("date").tail(days).reset_index(drop=True)

    @staticmethod
    def _first_non_empty(row: pd.Series, columns: tuple[str, ...]) -> str:
        for column in columns:
            value = row.get(column)
            if value is not None and str(value).strip():
                return str(value)
        return ""

    def _call_with_proxy_retry(self, loader: Callable[[], T]) -> T:
        try:
            return loader()
        except Exception as exc:
            if self._looks_like_proxy_error(exc):
                with self._without_proxy_env():
                    return loader()
            raise

    @staticmethod
    def _looks_like_proxy_error(exc: Exception) -> bool:
        message = str(exc).lower()
        return "proxy" in message or "407" in message or "tunnel connection failed" in message

    @contextmanager
    def _without_proxy_env(self):
        original = {key: os.environ.get(key) for key in PROXY_ENV_KEYS}
        try:
            for key in PROXY_ENV_KEYS:
                os.environ.pop(key, None)
            yield
        finally:
            for key, value in original.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    @staticmethod
    def _patch_eastmoney_requests() -> None:
        # 参考原项目：给东财请求补浏览器 headers，减少 stock_news_em 空响应和拦截概率。
        import requests

        if getattr(requests, "_stock_agent_lab_headers_patched", False):
            return

        original_get = requests.get

        def patched_get(url, **kwargs):
            if "eastmoney.com" in url:
                headers = kwargs.get("headers") or {}
                merged_headers = dict(EASTMONEY_HEADERS)
                merged_headers.update(headers)
                kwargs["headers"] = merged_headers
            return original_get(url, **kwargs)

        requests.get = patched_get
        requests._stock_agent_lab_headers_patched = True
