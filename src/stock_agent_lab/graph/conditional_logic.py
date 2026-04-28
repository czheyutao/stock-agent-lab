"""
模块作用：
- 集中管理工作流中的条件路由规则，例如技术面/新闻分析是否继续走工具回路，多空辩论是否继续。
联动关系：
- setup.py 在 add_conditional_edges 中调用这里的方法。
- states.py 提供判断所需的工具状态、计数器和辩论状态。
运行示例：
- python -m pytest tests/test_graph_workflow.py
"""

from __future__ import annotations

from stock_agent_lab.graph.states import AgentState


class ConditionalLogic:
    """轻量路由策略，参考原项目的条件边设计。"""

    def __init__(self, max_debate_rounds: int = 1, max_risk_discuss_rounds: int = 0) -> None:
        if max_debate_rounds < 1:
            raise ValueError("max_debate_rounds must be at least 1.")
        if max_risk_discuss_rounds < 0:
            raise ValueError("max_risk_discuss_rounds must be 0 or greater.")
        self.max_debate_rounds = max_debate_rounds
        self.max_risk_discuss_rounds = max_risk_discuss_rounds

    def should_continue_technical(self, state: AgentState) -> str:
        """决定技术面分析师是继续走工具节点，还是清理临时状态后进入下一阶段。"""

        if state["results"].get("technical"):
            return "Msg Clear Technical"
        if state["tool_requests"].get("technical"):
            return "tools_technical"
        return "Msg Clear Technical"

    def should_continue_news(self, state: AgentState) -> str:
        """决定新闻分析师是继续走工具节点，还是清理临时状态后进入下一阶段。"""

        if state["results"].get("news"):
            return "Msg Clear News"
        if state["tool_requests"].get("news"):
            return "tools_news"
        return "Msg Clear News"

    def should_continue_debate(self, state: AgentState) -> str:
        """判断多空研究员是否继续辩论，或者交给 Research Manager 汇总。"""

        debate_state = state["investment_debate_state"]
        current_count = debate_state["count"]
        max_count = 2 * self.max_debate_rounds
        if current_count >= max_count:
            return "Research Manager"

        current_speaker = debate_state["current_response"]
        if current_speaker.startswith("Bull"):
            return "Bear Researcher"
        return "Bull Researcher"

    def should_continue_risk_analysis(self, state: AgentState) -> str:
        """保留给后续风险回路使用，当前默认直接进入 Risk Judge。"""

        risk_state = state["risk_debate_state"]
        current_count = risk_state["count"]
        max_count = 3 * self.max_risk_discuss_rounds
        if current_count >= max_count:
            return "Risk Judge"

        latest_speaker = risk_state["latest_speaker"]
        if latest_speaker.startswith("Risky"):
            return "Safe Analyst"
        if latest_speaker.startswith("Safe"):
            return "Neutral Analyst"
        return "Risky Analyst"
