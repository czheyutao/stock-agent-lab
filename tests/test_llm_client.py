"""
模块作用：
- 测试 OpenAICompatibleClient 的环境变量解析逻辑，尤其是 DeepSeek 的 OpenAI-compatible 配置。
联动关系：
- 覆盖 llm.client，保护 CLI 在切换 DeepSeek/OpenAI 兼容后端时的配置行为。
运行示例：
- python -m pytest tests/test_llm_client.py
"""

from __future__ import annotations

import pytest

from stock_agent_lab.llm import OpenAICompatibleClient


def test_client_prefers_openai_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")

    client = OpenAICompatibleClient()

    assert client.api_key == "openai-test-key"
    assert client.base_url == "https://example.com/v1"
    assert client.model == "gpt-test"


def test_client_supports_deepseek_environment(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-test-key")

    client = OpenAICompatibleClient()

    assert client.api_key == "deepseek-test-key"
    assert client.base_url == "https://api.deepseek.com"
    assert client.model == "deepseek-v4-flash"


def test_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)
    monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)

    with pytest.raises(ValueError, match="API_KEY"):
        OpenAICompatibleClient()
