import json

from fastapi import APIRouter
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from app import schemas
from app.agent.graph import hcp_agent

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Simple in-memory per-session conversation history.
# For production, swap this for a LangGraph checkpointer (e.g. backed by Postgres)
# so history survives restarts and scales across workers.
_SESSION_HISTORY: dict[str, list] = {}


@router.post("", response_model=schemas.ChatMessageOut)
def chat(payload: schemas.ChatMessageIn):
    history = _SESSION_HISTORY.get(payload.session_id, [])
    history.append(HumanMessage(content=payload.message))

    result = hcp_agent.invoke({"messages": history})
    new_messages = result["messages"]
    _SESSION_HISTORY[payload.session_id] = new_messages

    # Walk backwards from the end to collect: the final AI reply text, and the
    # names of any tools that were called this turn (for the UI to show, e.g.
    # a small "Logged via: log_interaction" badge), plus any interaction_id
    # surfaced by a tool result so the frontend can refresh that record.
    tool_calls_used = []
    interaction_id = None
    final_reply = ""

    for msg in reversed(new_messages):
        if isinstance(msg, AIMessage) and msg.content and not final_reply:
            final_reply = msg.content
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            tool_calls_used.extend([tc["name"] for tc in msg.tool_calls])
        if isinstance(msg, ToolMessage):
            try:
                parsed = json.loads(msg.content)
                if isinstance(parsed, dict) and parsed.get("interaction_id") and not interaction_id:
                    interaction_id = parsed["interaction_id"]
            except (json.JSONDecodeError, TypeError):
                pass
        if isinstance(msg, HumanMessage):
            break

    return schemas.ChatMessageOut(
        reply=final_reply or "Done.",
        tool_calls=list(dict.fromkeys(tool_calls_used)),
        interaction_id=interaction_id,
    )


@router.post("/reset")
def reset_session(session_id: str = "default"):
    _SESSION_HISTORY.pop(session_id, None)
    return {"status": "reset", "session_id": session_id}
