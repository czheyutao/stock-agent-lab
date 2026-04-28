"""
模块作用：
- 组装 LangGraph 工作流，把各个 Agent 包装成图节点，并定义固定边、条件边和工具回路。
- 当前版本重点对齐原项目前半段结构：分析师节点 -> 工具节点 -> 分析师节点 -> 清理节点。
联动关系：
- trading_graph.py 注入各个 Agent 实例并调用这里编译图。
- conditional_logic.py 提供技术面、新闻和多空辩论的路由判断。
- states.py 承载节点之间共享的数据与工具临时状态。
运行示例：
- python -m pytest tests/test_graph_workflow.py
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from stock_agent_lab.agents import (
    BearResearcher,
    BullResearcher,
    NewsSentimentAnalyst,
    RiskManager,
    TechnicalAnalyst,
    TraderAgent,
)
from stock_agent_lab.agents.base import format_news, format_technicals
from stock_agent_lab.graph.conditional_logic import ConditionalLogic
from stock_agent_lab.graph.states import AgentState
from stock_agent_lab.models import AgentResult


class GraphSetup:
    """把 Agent 实例包装成 LangGraph 节点，并编译成可执行图。"""

    def __init__(
        self,
        technical: TechnicalAnalyst,
        news: NewsSentimentAnalyst,
        bull: BullResearcher,
        bear: BearResearcher,
        trader: TraderAgent,
        risk: RiskManager,
        conditional_logic: ConditionalLogic,
    ) -> None:
        self.technical = technical
        self.news = news
        self.bull = bull
        self.bear = bear
        self.trader = trader
        self.risk = risk
        self.conditional_logic = conditional_logic

    def setup_graph(self):
        """创建并编译 LangGraph。"""

        workflow = StateGraph(AgentState)

        workflow.add_node("Technical Analyst", self._technical_node)
        workflow.add_node("tools_technical", self._technical_tool_node)
        workflow.add_node("Msg Clear Technical", self._clear_technical_node)

        workflow.add_node("News Analyst", self._news_node)
        workflow.add_node("tools_news", self._news_tool_node)
        workflow.add_node("Msg Clear News", self._clear_news_node)

        workflow.add_node("Bull Researcher", self._bull_node)
        workflow.add_node("Bear Researcher", self._bear_node)
        workflow.add_node("Research Manager", self._research_manager_node)
        workflow.add_node("Trader", self._trader_node)
        workflow.add_node("Risk Manager", self._risk_manager_node)

        workflow.add_edge(START, "Technical Analyst")
        workflow.add_conditional_edges(
            "Technical Analyst",
            self.conditional_logic.should_continue_technical,
            {
                "tools_technical": "tools_technical",
                "Msg Clear Technical": "Msg Clear Technical",
            },
        )
        workflow.add_edge("tools_technical", "Technical Analyst")
        workflow.add_edge("Msg Clear Technical", "News Analyst")

        workflow.add_conditional_edges(
            "News Analyst",
            self.conditional_logic.should_continue_news,
            {
                "tools_news": "tools_news",
                "Msg Clear News": "Msg Clear News",
            },
        )
        workflow.add_edge("tools_news", "News Analyst")
        workflow.add_edge("Msg Clear News", "Bull Researcher")

        workflow.add_conditional_edges(
            "Bull Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bear Researcher": "Bear Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_conditional_edges(
            "Bear Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bull Researcher": "Bull Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_edge("Research Manager", "Trader")
        workflow.add_edge("Trader", "Risk Manager")
        workflow.add_edge("Risk Manager", END)

        return workflow.compile()

    def _technical_node(self, state: AgentState) -> dict[str, object]:
        # 第一次进入时先请求工具节点；拿到工具结果后再真正生成技术面报告。
        if "technical" not in state["results"] and not state["tool_outputs"]["technical"]:
            tool_requests = dict(state["tool_requests"])
            tool_requests["technical"] = True
            return {"tool_requests": tool_requests, "node_trace": ["Technical Analyst"]}

        if "technical" in state["results"]:
            return {"node_trace": ["Technical Analyst"]}

        results = dict(state["results"])
        context = {
            "technical_tool_data": AgentResult(
                agent="tools_technical",
                summary=state["tool_outputs"]["technical"],
            )
        }
        results["technical"] = self.technical.run(state["dataset"], context)
        return {
            "results": results,
            "node_trace": ["Technical Analyst"],
        }

    def _technical_tool_node(self, state: AgentState) -> dict[str, object]:
        # 轻量版工具节点直接把标准化技术面数据写入临时区，模拟原项目 ToolNode 的中转作用。
        tool_outputs = dict(state["tool_outputs"])
        tool_outputs["technical"] = format_technicals(state["dataset"])
        tool_requests = dict(state["tool_requests"])
        tool_requests["technical"] = False
        tool_call_count = dict(state["tool_call_count"])
        tool_call_count["technical"] += 1
        return {
            "tool_outputs": tool_outputs,
            "tool_requests": tool_requests,
            "tool_call_count": tool_call_count,
            "node_trace": ["tools_technical"],
        }

    def _clear_technical_node(self, state: AgentState) -> dict[str, object]:
        # 清理工具回路留下的临时状态，避免后续节点误读。
        tool_outputs = dict(state["tool_outputs"])
        tool_outputs["technical"] = ""
        tool_requests = dict(state["tool_requests"])
        tool_requests["technical"] = False
        return {
            "tool_outputs": tool_outputs,
            "tool_requests": tool_requests,
            "node_trace": ["Msg Clear Technical"],
        }

    def _news_node(self, state: AgentState) -> dict[str, object]:
        # 新闻分析也遵循同样的回路：先过工具节点，再根据工具结果形成观点。
        if "news" not in state["results"] and not state["tool_outputs"]["news"]:
            tool_requests = dict(state["tool_requests"])
            tool_requests["news"] = True
            return {"tool_requests": tool_requests, "node_trace": ["News Analyst"]}

        if "news" in state["results"]:
            return {"node_trace": ["News Analyst"]}

        results = dict(state["results"])
        context = {
            "news_tool_data": AgentResult(
                agent="tools_news",
                summary=state["tool_outputs"]["news"],
            )
        }
        results["news"] = self.news.run(state["dataset"], context)
        return {
            "results": results,
            "node_trace": ["News Analyst"],
        }

    def _news_tool_node(self, state: AgentState) -> dict[str, object]:
        # 这里先做文本型轻量工具节点，后续可平滑升级为真正的 ToolNode。
        tool_outputs = dict(state["tool_outputs"])
        tool_outputs["news"] = format_news(state["dataset"])
        tool_requests = dict(state["tool_requests"])
        tool_requests["news"] = False
        tool_call_count = dict(state["tool_call_count"])
        tool_call_count["news"] += 1
        return {
            "tool_outputs": tool_outputs,
            "tool_requests": tool_requests,
            "tool_call_count": tool_call_count,
            "node_trace": ["tools_news"],
        }

    def _clear_news_node(self, state: AgentState) -> dict[str, object]:
        tool_outputs = dict(state["tool_outputs"])
        tool_outputs["news"] = ""
        tool_requests = dict(state["tool_requests"])
        tool_requests["news"] = False
        return {
            "tool_outputs": tool_outputs,
            "tool_requests": tool_requests,
            "node_trace": ["Msg Clear News"],
        }

    def _bull_node(self, state: AgentState) -> dict[str, object]:
        result = self.bull.run(state["dataset"], self._debate_context(state))
        results = dict(state["results"])
        results["bull"] = result
        debate_state = self._build_updated_investment_debate_state(state, "Bull", result)
        return {
            "results": results,
            "investment_debate_state": debate_state,
            "node_trace": ["Bull Researcher"],
        }

    def _bear_node(self, state: AgentState) -> dict[str, object]:
        result = self.bear.run(state["dataset"], self._debate_context(state))
        results = dict(state["results"])
        results["bear"] = result
        debate_state = self._build_updated_investment_debate_state(state, "Bear", result)
        return {
            "results": results,
            "investment_debate_state": debate_state,
            "node_trace": ["Bear Researcher"],
        }

    def _research_manager_node(self, state: AgentState) -> dict[str, object]:
        debate_state = state["investment_debate_state"]
        plan = (
            "研究经理汇总\n"
            f"{debate_state['history'].strip()}\n\n"
            "请交易员在多空论证基础上给出可执行的 BUY/HOLD/SELL 建议。"
        )
        updated_debate_state = dict(debate_state)
        updated_debate_state["judge_decision"] = plan
        return {
            "investment_plan": plan,
            "investment_debate_state": updated_debate_state,
            "node_trace": ["Research Manager"],
        }

    def _trader_node(self, state: AgentState) -> dict[str, object]:
        context = dict(state["results"])
        context["investment_plan"] = AgentResult(agent="研究经理", summary=state["investment_plan"])
        result = self.trader.run(state["dataset"], context)
        results = dict(state["results"])
        results["trader"] = result
        return {
            "results": results,
            "final_trade_decision": result.summary,
            "node_trace": ["Trader"],
        }

    def _risk_manager_node(self, state: AgentState) -> dict[str, object]:
        results = dict(state["results"])
        results["risk"] = self.risk.run(state["dataset"], state["results"])
        return {"results": results, "node_trace": ["Risk Manager"]}

    def _debate_context(self, state: AgentState) -> dict[str, AgentResult]:
        """给多空研究员组装辩论上下文，避免 Agent 直接依赖完整 state 结构。"""

        context = dict(state["results"])
        debate_state = state["investment_debate_state"]
        context["debate_history"] = AgentResult(agent="投资辩论历史", summary=debate_state["history"])
        context["last_argument"] = AgentResult(agent="上一轮观点", summary=debate_state["current_response"])
        return context

    @staticmethod
    def _build_updated_investment_debate_state(
        state: AgentState, speaker: str, result: AgentResult
    ) -> dict[str, object]:
        """构造新的辩论状态，而不是原地修改，符合 LangGraph 的节点更新方式。"""

        debate_state = dict(state["investment_debate_state"])
        argument = f"{speaker} Analyst: {result.summary}"
        debate_state["history"] = (debate_state["history"] + "\n" + argument).strip()
        debate_state["current_response"] = argument
        debate_state["count"] += 1
        if speaker == "Bull":
            debate_state["bull_history"] = (debate_state["bull_history"] + "\n" + argument).strip()
        else:
            debate_state["bear_history"] = (debate_state["bear_history"] + "\n" + argument).strip()
        return debate_state
