"""
模块作用：
- 定义多 Agent 工作流共享状态，作为 LangGraph 在节点之间传递的统一数据结构。
- 除了正式分析结果，还保存工具回路的临时状态，例如工具调用次数、工具输出和待执行标记。
联动关系：
- propagation.py 负责初始化这些状态。
- setup.py 中的各个节点会持续读写这些状态。
- conditional_logic.py 根据这些状态决定下一步路由。
运行示例：
- python -m pytest tests/test_graph_workflow.py
"""

from __future__ import annotations

from operator import add
from typing import Annotated, TypedDict

from stock_agent_lab.models import AgentResult, StockDataset


class InvestDebateState(TypedDict):
    """多空研究员辩论阶段的共享状态。"""

    bull_history: str
    bear_history: str
    history: str
    current_response: str
    judge_decision: str
    count: int


class RiskDebateState(TypedDict):
    """风险委员会辩论阶段的共享状态，先按原项目结构预留。"""

    risky_history: str
    safe_history: str
    neutral_history: str
    history: str
    latest_speaker: str
    current_risky_response: str
    current_safe_response: str
    current_neutral_response: str
    judge_decision: str
    count: int


class AgentState(TypedDict, total=False):
    """整个多 Agent 工作流的黑板状态，所有节点都只通过它交换信息。"""

    # dataset 是数据层产出的统一输入，后续所有 Agent 都围绕它分析。
    dataset: StockDataset
    # results 保存每个 Agent 的结构化输出，key 使用 technical/news/bull 等短名。
    results: dict[str, AgentResult]
    investment_debate_state: InvestDebateState
    risk_debate_state: RiskDebateState
    # tool_requests 记录某个分析师是否要求先执行工具节点。
    tool_requests: dict[str, bool]
    # tool_outputs 保存工具节点产出的临时文本，供分析师二次进入时消费。
    tool_outputs: dict[str, str]
    # tool_call_count 用于限制工具回路次数，也便于测试验证路由行为。
    tool_call_count: dict[str, int]
    # investment_plan 是研究经理给交易员的中间方案。
    investment_plan: str
    # final_trade_decision 保存交易员/风控后的最终自然语言结论。
    final_trade_decision: str
    # node_trace 在 LangGraph 中使用 add 作为 reducer，让每个节点都能追加自己的名字。
    node_trace: Annotated[list[str], add]
