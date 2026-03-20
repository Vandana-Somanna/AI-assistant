# from langchain.agents import create_agent
# from dotenv import load_dotenv
# from langchain.agents import create_agent
# # from langchain.tools import tool
# from langchain.messages import HumanMessage, SystemMessage,AIMessage
# import os

# load_dotenv()  # take environment variables from .env.
# api_key = os.getenv("GROQ_API_KEY")

# from langchain_groq import ChatGroq
# model=ChatGroq(model="llama-3.1-8b-instant",api_key=api_key)

# from mytools import check_order_status , create_ticket
# Agent=create_agent(
#     tools=[check_order_status, create_ticket],
#     model=model,
#     system_prompt="Act as helpfull assistant who can answer questions related to order status and also can create ticket for any issue"
    
# )
# # print(model.invoke("What is the status of ORD123?"))
# # print(check_order_status.invoke({"order_id": "ORD123"})) """worked well"""

# result = Agent.invoke(
#     {"messages": [HumanMessage("I want to return my order ORD123, can you help me with that?")]}
# )
# print(result["messages"][-1].content)

"""2.0"""
# agent.py
from __future__ import annotations

from multiprocessing import context
import os, re
from typing import Dict, Any
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

import json
from pathlib import Path

# --- Your tools (already working) ---
from mytools import check_order_status, create_ticket  # [1](https://chimeratechpvtltd-my.sharepoint.com/personal/vandanas_chimeratechnologies_com/Documents/Microsoft%20Copilot%20Chat%20Files/mytools.py)

# --- Your RAG retriever built in rag.py ---
# IMPORTANT: rag.py currently builds the index & retriever at import time.
# That's OK for now. If it's slow, we can refactor later.
from rag import rag_retriever  # [2](https://chimeratechpvtltd-my.sharepoint.com/personal/vandanas_chimeratechnologies_com/Documents/Microsoft%20Copilot%20Chat%20Files/rag.py)


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

# --- ticket de-dup helper ---
TICKETS_FILE = Path(r"C:\Users\VandanaS\Desktop\AI_assistant\data\tickets.json")

def find_existing_ticket(order_id: str) -> str | None:
    """
    Return the latest open ticket ID for this order_id if one exists; else None.
    Safe: returns None if the file is missing/corrupt.
    """
    try:
        if not TICKETS_FILE.exists():
            return None
        raw = TICKETS_FILE.read_text(encoding="utf-8").strip() or "[]"
        tickets = json.loads(raw)
        # scan newest-first
        for t in reversed(tickets):
            meta = t.get("metadata", {}) or {}
            if meta.get("order_id") == order_id and t.get("status", "open") == "open":
                return t.get("id")
        return None
    except Exception:
        # fail-quiet: don't block agent if tickets file has issues
        return None

def decide_intent(message: str) -> Dict[str, bool]:
    """Lightweight intent router."""
    m = message.lower()
    return {
        "ask_policy": any(k in m for k in ["return policy", "refund", "return", "shipping", "delivery timeline", "cancel"]),
        "order_status": ("order" in m) or ("ord" in m) or bool(ORDER_RE.findall(message)),
        "create_ticket": any(k in m for k in ["ticket", "support", "help"]) or ("return" in m),
    }


# ---------------- LLM for RAG answers ----------------
load_dotenv()
groq_key = os.getenv("GROQ_API_KEY") or os.getenv("API")
# NOTE: In your current agent.py, you used ChatGroq with (model, api_key), but the wrapper expects (model_name, groq_api_key).
# We correct it here: [3](https://chimeratechpvtltd-my.sharepoint.com/personal/vandanas_chimeratechnologies_com/Documents/Microsoft%20Copilot%20Chat%20Files/agent.py)
model = ChatGroq(model_name="llama-3.1-8b-instant", groq_api_key=groq_key, temperature=0.1)

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a support assistant. Answer ONLY from the provided CONTEXT. If not present, say: 'I don't know based on our docs.' and confirm from the user before you create any ticket"),
    ("human", "QUESTION:\n{question}\n\nCONTEXT:\n{context}")
])


def rag_answer(question: str, top_k: int = 4) -> str:
    """Retrieve top-k chunks and answer strictly from context using your Groq model."""
    results = rag_retriever.retrieve(question, top_k=top_k)  # returns list with 'content' keys  [2](https://chimeratechpvtltd-my.sharepoint.com/personal/vandanas_chimeratechnologies_com/Documents/Microsoft%20Copilot%20Chat%20Files/rag.py)
    context = "\n\n".join([r["content"] for r in results]) if results else ""
    if not context:
        return "I don't know based on our docs."
    
    messages = RAG_PROMPT.format_messages(question=question, context=context)
    resp = model.invoke(messages)       #  Pass messages directly
    return resp.content



# ---------------- Chat orchestration (router) ----------------
def chat(message: str, session_id: str = "default") -> str:
    # memory: add user message & capture order ID if present
    SessionMemory.add(session_id, "user", message)
    found_ids = ORDER_RE.findall(message)
    if found_ids:
        SessionMemory.set_slot(session_id, "last_order_id", found_ids[-1].upper())
    order_id = SessionMemory.get_slot(session_id, "last_order_id")

    intents = decide_intent(message)

    parts = []

    # 1) Tools: order status (multi-turn-aware using last_order_id)
    if intents["order_status"] and order_id:
        info = check_order_status.invoke({"order_id": order_id})  # [1](https://chimeratechpvtltd-my.sharepoint.com/personal/vandanas_chimeratechnologies_com/Documents/Microsoft%20Copilot%20Chat%20Files/mytools.py)
        if info.get("found"):
            parts.append(
                f"Order {info['order_id']} for {info['customer_name']} is '{info['status']}'. "
                f"Expected delivery: {info['expected_delivery']}."
            )
        else:
            parts.append(info.get("message", "Order not found."))

    # 2) RAG: policy/FAQ/shipping
    if intents["ask_policy"]:
        parts.append(rag_answer(message, top_k=4))

    # 3).1 Mixed: return intent + order id -> create ticket
    if intents["create_ticket"] and ("return" in message.lower()) and order_id:
        reason = f"Return request for {order_id}"
        ticket = create_ticket.invoke({"issue": reason, "metadata": {"order_id": order_id, "type": "return"}})  # [1](https://chimeratechpvtltd-my.sharepoint.com/personal/vandanas_chimeratechnologies_com/Documents/Microsoft%20Copilot%20Chat%20Files/mytools.py)
        parts.append(f"I've created a support ticket {ticket['id']} for your request.")
    # existing_id = None
    # 3).2 Mixed: return intent + order id -> create ticket (with de-dup)
    # if intents["create_ticket"] and ("return" in message.lower()) and order_id:
    #     existing_id = find_existing_ticket(order_id)
    # if existing_id:
    #     parts.append(f"A return ticket ({existing_id}) is already open for {order_id}.")
    # else:
    #     reason = f"Return request for {order_id}"
    #     ticket = create_ticket.invoke({
    #         "issue": reason,
    #         "metadata": {"order_id": order_id, "type": "return"}
    #     })
    #     parts.append(f"I've created a support ticket {ticket['id']} for your request.")
    # 3) Mixed: return intent -> create ticket (with de-dup & guard)
    # if intents["create_ticket"] and ("return" in message.lower()):
    #     if not order_id:
    #     # No order id yet → DO NOT create a ticket. Ask for it.
    #         parts.append("Please share your order ID (e.g., ORD123) to raise a return ticket.")
    #     else:
    #         existing_id = find_existing_ticket(order_id)
    #     if existing_id:
    #         parts.append(f"A return ticket ({existing_id}) is already open for {order_id}.")
    #     else:
    #         reason = f"Return request for {order_id}"
    #         ticket = create_ticket.invoke({
    #             "issue": reason,
    #             "metadata": {"order_id": order_id, "type": "return"}
    #         })
    #         parts.append(f"I've created a support ticket {ticket['id']} for your request.")
    # 4) Fallback: try RAG if nothing else matched
    if not parts:
        parts.append(rag_answer(message, top_k=3))

    final = "\n".join(parts)
    SessionMemory.add(session_id, "assistant", final)
    return final


# ---------------- Demo ----------------
if __name__ == "__main__":
    # Multi-turn memory demo
    print(chat("My order is delayed", session_id="u1"))
    print(chat("It is ORD123", session_id="u1"))

    # RAG demo
    # print(chat("What is return policy?", session_id="u1"))

    # # Mixed flow demo
    print(chat("I want to return my order ORD456", session_id="u1"))