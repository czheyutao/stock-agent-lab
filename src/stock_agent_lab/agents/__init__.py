"""
模块作用：
- 汇总导出所有 Agent 类，给 graph/setup.py 提供统一导入入口。

联动关系：
- graph.GraphSetup 从这里导入分析师、研究员、交易员和风控经理。
"""

from stock_agent_lab.agents.fundamentals import FundamentalsAnalyst
from stock_agent_lab.agents.news import NewsSentimentAnalyst
from stock_agent_lab.agents.researchers import BearResearcher, BullResearcher
from stock_agent_lab.agents.risk import RiskManager
from stock_agent_lab.agents.technical import TechnicalAnalyst
from stock_agent_lab.agents.trader import TraderAgent

__all__ = [
    "FundamentalsAnalyst",
    "TechnicalAnalyst",
    "NewsSentimentAnalyst",
    "BullResearcher",
    "BearResearcher",
    "TraderAgent",
    "RiskManager",
]
