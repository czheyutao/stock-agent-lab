"""
模块作用：
- 定义 LLM 调用抽象，并提供 OpenAI-compatible 实现和本地 Mock 实现。
- 当前版本增强了 DeepSeek 支持：当存在 DEEPSEEK_* 环境变量时，可直接按 OpenAI-compatible 方式接入。
联动关系：
- 所有 Agent 通过 LLMClient.complete 调用模型。
- 测试和 --mock-llm 使用 MockLLMClient 避免真实 API 依赖。
运行示例：
- python -m pytest tests/test_llm_client.py
- stock-agent analyze --symbol 600519 --days 30 --include-node-trace
"""

from __future__ import annotations

import os
from typing import Protocol


class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> str:
        """Return a short Chinese analysis response."""


class OpenAICompatibleClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> None:
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        deepseek_base_url = os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com"
        deepseek_model = os.getenv("DEEPSEEK_MODEL") or "deepseek-v4-flash"

        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or deepseek_api_key
        self.base_url = (
            base_url
            or os.getenv("OPENAI_BASE_URL")
            or (deepseek_base_url if deepseek_api_key else None)
            or "https://api.openai.com/v1"
        )
        self.model = (
            model
            or os.getenv("OPENAI_MODEL")
            or (deepseek_model if deepseek_api_key else None)
            or "gpt-4o-mini"
        )
        self.temperature = temperature
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY or DEEPSEEK_API_KEY is required. "
                "Set it in the environment or run with --mock-llm for local demos."
            )

    def complete(self, system: str, user: str) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        response = client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""


class MockLLMClient:
    def complete(self, system: str, user: str) -> str:
        role = system.splitlines()[0].strip() if system else "Agent"
        if "交易员" in role:
            return "建议: HOLD\n理由: 当前信号混合，等待更明确的趋势确认。"
        if "风控" in role:
            return "风险提示: 控制仓位，关注市场波动、消息面反转和流动性风险。"
        if "多头" in role:
            return "多头观点: 若价格站上均线且成交量改善，存在继续修复的可能。"
        if "空头" in role:
            return "空头观点: 若趋势转弱或新闻情绪恶化，短期回撤风险仍需警惕。"
        if "新闻" in role:
            return "新闻情绪: 近期信息需要结合公告和行业变化审慎解读。"
        return "技术面: 结合趋势、均线、波动率和成交量观察，当前更适合保持谨慎。"
