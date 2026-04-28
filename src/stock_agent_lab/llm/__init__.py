"""
模块作用：
- 汇总导出 LLM 客户端协议、真实 OpenAI 兼容客户端和 Mock 客户端。

联动关系：
- agents.base 依赖 LLMClient 协议，cli.py 根据参数选择 OpenAICompatibleClient 或 MockLLMClient。
"""

from stock_agent_lab.llm.client import LLMClient, MockLLMClient, OpenAICompatibleClient

__all__ = ["LLMClient", "MockLLMClient", "OpenAICompatibleClient"]
