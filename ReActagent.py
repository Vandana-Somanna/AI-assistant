from __future__ import annotations
import os
import re
from typing import Dict, Any
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

# --- Tools ---
from mytools import check_order_status, create_ticket, rag_search

# ---------------- Memory ----------------
class SessionMemory:
    """Simple session memory: last 20 turns + slot storage (e.g., last_order_id)."""
    _store: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get(cls, sid: str) -> Dict[str, Any]:
        return cls._store.setdefault(sid, {"history": [], "slots": {}})

    @classmethod
    def add(cls, sid: str, role: str, content: str) -> None:
        s = cls.get(sid)
        s["history"].append({"role": role, "content": content})
        s["history"] = s["history"][-20:]

    @classmethod
    def set_slot(cls, sid: str, key: str, val: Any) -> None:
        cls.get(sid)["slots"][key] = val

    @classmethod
    def get_slot(cls, sid: str, key: str) -> Any:
        return cls.get(sid)["slots"].get(key)


ORDER_RE = re.compile(r"\bORD\d+\b", re.I)

# ---------------- LLM & Agent setup ----------------
load_dotenv()
groq_key = os.getenv("GROQ_API_KEY") or os.getenv("API")

model = ChatGroq(model_name="llama-3.1-8b-instant", groq_api_key=groq_key, temperature=0.1)

tools = [check_order_status, create_ticket, rag_search]


prompt = """
You are a strict customer support assistant.

You ONLY have access to these tools:
- check_order_status: Use ONLY when user provides an order ID like ORD123
- rag_search: Use ONLY for policy questions — return, refund, shipping, cancellation
- create_ticket: Use ONLY when user explicitly requests a return or support ticket

STRICT RULES:
- Call each tool ONLY ONCE per query
- After calling a tool, you MUST use the tool's output as your final answer
- NEVER say "I don't know" if the tool returned a valid response
- Do NOT call another tool if you already have an answer from a previous tool
- Do NOT ignore tool output — always relay it directly to the user
- Use the MINIMUM number of tool calls needed
"""

# agent = create_react_agent(model=model, tools=tools, prompt=prompt)

agent_executor = create_react_agent(
    model=model,
    tools=tools,
    prompt=prompt,
)


# ---------------- Chat ----------------
import time

def chat(message: str, session_id: str = "default") -> Dict[str, Any]:
    # 1) Store user message
    SessionMemory.add(session_id, "user", message)

    # 2) Extract and remember order ID if present
    found_ids = ORDER_RE.findall(message)
    if found_ids:
        SessionMemory.set_slot(session_id, "last_order_id", found_ids[-1].upper())

    # 3) Inject remembered order ID into message if not already present
    order_id = SessionMemory.get_slot(session_id, "last_order_id")
    if order_id and order_id.upper() not in message.upper():
        message = f"{message} (Order ID from context: {order_id})"

    # 4) Run agent with retry on rate limit
    try:
        result = agent_executor.invoke(
            {"messages": [("user", message)]},
            config={"recursion_limit": 12}
        )
    except Exception as e:
        if "rate_limit" in str(e).lower() or "429" in str(e):
            time.sleep(3)
            result = agent_executor.invoke(
                {"messages": [("user", message)]},
                config={"recursion_limit": 12}
            )
        else:
            raise e

    # 5) Extract response
    messages = result.get("messages", [])
    response = messages[-1].content if messages else "Sorry, I could not process your request."

    # 6) Extract tools used
    tools_used = list({m.name for m in messages if hasattr(m, "name") and m.name})

    # 7) Store assistant response
    SessionMemory.add(session_id, "assistant", response)

    return {
        "response": response,
        "tools_used": tools_used
    }


# ---------------- Demo ----------------
if __name__ == "__main__":
    # print(chat("My order is delayed", session_id="u1"))
    print(chat("It is ORD123", session_id="u1"))
    print(chat("What is the return policy?", session_id="u1"))
    print(chat("I want to return my order ORD456", session_id="u1"))