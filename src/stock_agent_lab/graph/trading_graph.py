"""
模块作用：
- 提供基于 LangGraph 的多 Agent 图编排主入口，负责创建路由器、状态初始化器和可执行图。

联动关系：
- pipeline.py 调用 StockAnalysisGraph.run；setup.py 负责节点组装，propagation.py 负责创建初始状态。
"""

from __future__ import annotations

from stock_agent_lab.agents import (
    BearResearcher,
    BullResearcher,
    FundamentalsAnalyst,
    NewsSentimentAnalyst,
    RiskManager,
    TechnicalAnalyst,
    TraderAgent,
)
from stock_agent_lab.graph.conditional_logic import ConditionalLogic
from stock_agent_lab.graph.propagation import Propagator
from stock_agent_lab.graph.setup import GraphSetup
from stock_agent_lab.graph.states import AgentState
from stock_agent_lab.llm import LLMClient
from stock_agent_lab.models import StockDataset


class StockAnalysisGraph:
    """基于 LangGraph 的多 Agent 工作流主入口。"""

    def __init__(
        self,
        llm: LLMClient,
        max_debate_rounds: int = 1,
        max_risk_discuss_rounds: int = 0,
    ) -> None:
        # 条件路由独立出来，后续接入更多节点时不需要改执行器主体。
        self.conditional_logic = ConditionalLogic(
            max_debate_rounds=max_debate_rounds,
            max_risk_discuss_rounds=max_risk_discuss_rounds,
        )
        # Propagator 专门负责创建初始 state，对齐原项目的职责拆分。
        self.propagator = Propagator()
        # GraphSetup 负责把具体 Agent 注入图节点，便于后续替换某个 Agent 实现。
        self.graph = GraphSetup(
            fundamentals=FundamentalsAnalyst(llm),
            technical=TechnicalAnalyst(llm),
            news=NewsSentimentAnalyst(llm),
            bull=BullResearcher(llm),
            bear=BearResearcher(llm),
            trader=TraderAgent(llm),
            risk=RiskManager(llm),
            conditional_logic=self.conditional_logic,
        ).setup_graph()

    def run(self, dataset: StockDataset) -> AgentState:
        """从数据集开始执行 LangGraph，返回包含全部中间结果的最终状态。"""

        state = self.propagator.create_initial_state(dataset)
        return self.graph.invoke(state)
