"""
模块作用：
- 创建工作流初始状态，把股票数据包装成所有节点共享的 AgentState。
- 初始化分析结果、多空辩论状态，以及工具回路所需的临时字段。
联动关系：
- trading_graph.py 调用 Propagator 创建初始状态。
- setup.py 中的分析师节点、工具节点和清理节点都会基于这里的默认值更新状态。
运行示例：
- python -m pytest tests/test_graph_workflow.py
"""

from __future__ import annotations

from stock_agent_lab.graph.states import AgentState, InvestDebateState, RiskDebateState
from stock_agent_lab.models import StockDataset


class Propagator:
    """负责创建工作流初始状态。"""

    def create_initial_state(self, dataset: StockDataset) -> AgentState:
        """把数据集包装成 AgentState，后续节点只读写这个共享状态。"""

        return AgentState(
            dataset=dataset,
            results={},
            investment_debate_state=InvestDebateState(
                bull_history="",
                bear_history="",
                history="",
                current_response="",
                judge_decision="",
                count=0,
            ),
            risk_debate_state=RiskDebateState(
                risky_history="",
                safe_history="",
                neutral_history="",
                history="",
                latest_speaker="",
                current_risky_response="",
                current_safe_response="",
                current_neutral_response="",
                judge_decision="",
                count=0,
            ),
            tool_requests={"technical": False, "news": False},
            tool_outputs={"technical": "", "news": ""},
            tool_call_count={"technical": 0, "news": 0},
            investment_plan="",
            final_trade_decision="",
            node_trace=[],
        )
