"""
LangGraph agent that powers the chat side of the Log Interaction Screen.

Graph shape:

    START -> agent -> (tools?) -> agent -> ... -> END

`agent` is an LLM node bound to the 5 tools. On each turn it decides whether
to respond directly or call one (or several) tools. `tools` is a prebuilt
ToolNode that executes whichever tool calls the LLM asked for and feeds the
results back to `agent`, which then either calls another tool or produces a
final natural-language reply to the rep. This lets the rep log an interaction
purely via chat ("Met Dr. Smith, discussed Prodo-X, positive, left samples")
without ever touching the structured form.
"""
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage

from app.agent.llm import reasoning_llm
from app.agent.tools import ALL_TOOLS

SYSTEM_PROMPT = """You are the AI assistant embedded in a pharma sales rep's CRM,
specifically the "Log HCP Interaction" screen. Your job is to help the rep log,
edit, and follow up on interactions with healthcare professionals (HCPs) through
natural conversation, as an alternative to the structured form.

Guidelines:
- When the rep describes a completed interaction, call `log_interaction` to save it.
- If they mention a voice note / dictated note, you may call `summarize_voice_note`
  first to structure it, then `log_interaction` to save it - but only after the rep
  has confirmed the summary is accurate (voice note summarization requires consent).
- If the rep refers to a change to something already logged, call `edit_interaction`
  with the interaction_id from the earlier tool result in this conversation.
- If the rep wants to schedule a reminder tied to a logged interaction, call
  `schedule_followup`.
- If you're unsure which HCP record they mean, call `search_hcp` to check the roster.
- Always confirm back to the rep in plain language what was logged/changed, e.g.
  "Logged your meeting with Dr. Smith - positive sentiment, discussed Prodo-X efficacy,
  brochure shared." Keep responses brief and professional.
- Never fabricate HCP names, dates, or outcomes the rep did not mention.
"""


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def _agent_node(state: AgentState):
    llm_with_tools = reasoning_llm.bind_tools(ALL_TOOLS)
    messages = state["messages"]
    # Ensure the system prompt is always present as the first message
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("agent", _agent_node)
    graph.add_node("tools", ToolNode(ALL_TOOLS))

    graph.set_entry_point("agent")
    # tools_condition inspects the last message: if it has tool_calls, route to
    # "tools"; otherwise route to END (the agent produced a final answer).
    graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


# Compiled once at import time and reused across requests
hcp_agent = build_graph()
