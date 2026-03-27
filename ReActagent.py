# from __future__ import annotations
# import os
# import re
# from typing import Dict, Any
# from dotenv import load_dotenv

# from langchain_groq import ChatGroq
# from langgraph.prebuilt import create_react_agent

# # --- Tools ---
# from mytools import check_order_status, create_ticket, rag_search

# # ---------------- Memory ----------------
# class SessionMemory:
#     """Simple session memory: last 20 turns + slot storage (e.g., last_order_id)."""
#     _store: Dict[str, Dict[str, Any]] = {}

#     @classmethod
#     def get(cls, sid: str) -> Dict[str, Any]:
#         return cls._store.setdefault(sid, {"history": [], "slots": {}})

#     @classmethod
#     def add(cls, sid: str, role: str, content: str) -> None:
#         s = cls.get(sid)
#         s["history"].append({"role": role, "content": content})
#         s["history"] = s["history"][-20:]

#     @classmethod
#     def set_slot(cls, sid: str, key: str, val: Any) -> None:
#         cls.get(sid)["slots"][key] = val

#     @classmethod
#     def get_slot(cls, sid: str, key: str) -> Any:
#         return cls.get(sid)["slots"].get(key)


# ORDER_RE = re.compile(r"\bORD\d+\b", re.I)

# # ---------------- LLM & Agent setup ----------------
# load_dotenv()
# groq_key = os.getenv("GROQ_API_KEY") or os.getenv("API")

# model = ChatGroq(model_name="llama-3.1-8b-instant", groq_api_key=groq_key, temperature=0.1)

# tools = [check_order_status, create_ticket, rag_search]


# prompt = """
# You are a strict customer support assistant for an e-commerce store.

# AVAILABLE TOOLS:
# 1. check_order_status: Use this to get delivery dates or status for an order ID (e.g., ORD123).
# 2. rag_search: Use ONLY for general policy questions (returns, refunds, shipping, etc.).
# 3. create_ticket: Use this ONLY when a user explicitly wants to return an item or needs a support ticket.

# STRICT GUIDELINES FOR RETURNS:
# - If a user says "I want to return ORD123", you MUST use the 'create_ticket' tool.
# - You MUST provide the 'metadata' argument to 'create_ticket' in this format: {"order_id": "ORD123"}.
# - Use the 'issue' argument to describe the request (e.g., "User wants to return order ORD123").

# GENERAL RULES:
# - Use the MINIMUM number of tool calls needed to answer the user.
# - After receiving a tool's output, relay that information directly to the user as your final answer.
# - Do NOT make up information; if the tool says an order is not found, tell the user exactly that.
# - If the user provides an order ID and a policy question in the same breath, prioritize the policy answer from 'rag_search'.
# """
# prompt = 
"""
You are a strict customer support assistant for an e-commerce store.

You ONLY handle these three things:
1. Order status — when user provides an order ID like ORD123 → call check_order_status
2. Store policies — return policy, refund, shipping, cancellation → call rag_search
3. Return requests — when user wants to return an order AND provides an order ID → call check_order_status THEN create_ticket

Return request phrases include:
- "return ord123"
- "i want to return ord123"
- "can i return ord123"
- "i need to return ord123"
- "return my order ord123"
- any message containing "return" AND an order ID like ORD123

You have access to these tools:
- check_order_status: ONLY when message contains an order ID like ORD123
- rag_search: ONLY for policy questions — return policy, refund, shipping, cancellation
- create_ticket: ONLY when user wants to return an order with a specific order ID

STRICT RULES:
- Treat EACH message independently — ignore previous order context for policy questions
- For policy questions, NEVER mention order details — only answer from rag_search output
- For general questions unrelated to orders, policies, or returns say exactly: "I can only help with order status, store policies, and support requests."
- "return policy" or "what is return policy" = policy question → use rag_search only
- NEVER answer policy questions from your own knowledge — ALWAYS call rag_search for ANY question about return policy, refund, shipping, or cancellation
"""
# # agent = create_react_agent(model=model, tools=tools, prompt=prompt)

# agent_executor = create_react_agent(
#     model=model,
#     tools=tools,
#     prompt=prompt,
# )


# # ---------------- Chat ----------------
# import time

# def chat(message: str, session_id: str = "default") -> Dict[str, Any]:
#     # 1) Store user message
#     SessionMemory.add(session_id, "user", message)

#     # 2) Extract and remember order ID if present
#     found_ids = ORDER_RE.findall(message)
#     if found_ids:
#         SessionMemory.set_slot(session_id, "last_order_id", found_ids[-1].upper())

#     # 3) Inject remembered order ID into message if not already present
#     order_id = SessionMemory.get_slot(session_id, "last_order_id")
#     if order_id and order_id.upper() not in message.upper():
#         message = f"{message} (Order ID from context: {order_id})"

#     # 4) Run agent with retry on rate limit
#     try:
#         result = agent_executor.invoke(
#             {"messages": [("user", message)]},
#             config={"recursion_limit": 12}
#         )
#     except Exception as e:
#         if "rate_limit" in str(e).lower() or "429" in str(e):
#             time.sleep(3)
#             result = agent_executor.invoke(
#                 {"messages": [("user", message)]},
#                 config={"recursion_limit": 20}
#             )
#         else:
#             raise e

#     # 5) Extract response
#     messages = result.get("messages", [])
#     response = messages[-1].content if messages else "Sorry, I could not process your request."

#     # 6) Extract tools used
#     tools_used = list({m.name for m in messages if hasattr(m, "name") and m.name})

#     # 7) Store assistant response
#     SessionMemory.add(session_id, "assistant", response)

#     return {
#         "response": response,
#         "tools_used": tools_used
#     }


# # ---------------- Demo ----------------
# if __name__ == "__main__":
#     # print(chat("My order is delayed", session_id="u1"))
#     print(chat("It is ORD123", session_id="u1"))
#     print(chat("What is the return policy?", session_id="u1"))

"""2.0"""
# --- IMPROVISED ReActagent.py ---
import time
import re
from typing import Dict, Any
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from mytools import check_order_status, create_ticket, rag_search

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
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0) # Using 70b for better tool logic

# IMPROVED PROMPT: Added Plan B and specific Return instructions
# system_message = """
# You are a strict customer support assistant.

# You ONLY have access to these tools:
# - check_order_status: Use ONLY when user provides an order ID like ORD123 
# - rag_search: Use ONLY for policy questions — return, refund, shipping, cancellation,cancel order
# - create_ticket: Use ONLY when user explicitly requests a return or cancel request or support ticket

# STRICT RULES:
# - Call each tool ONLY ONCE per query
# - After calling a tool, you MUST use the tool's output as your final answer
# - NEVER say "I don't know" if the tool returned a valid response
# - Do NOT call another tool if you already have an answer from a previous tool
# - Do NOT ignore tool output — always relay it directly to the user
# - Use the multiple tools in a single query ONLY if the user explicitly asks for multiple things (e.g., "I want to return ORD123 and also know the refund policy")
# """


system_message = """
### ROLE
You are a strict, authorized E-commerce Support Robot. You have THREE specific tools. You MUST use them to fulfill EVERY part of a user's request.

### TASK-TO-TOOL MAPPING
1. **Order Status**: For keywords like "status," "delayed," "when," "delivery," or "where is my order," you MUST call `check_order_status`.
2. **Store Policies**: For keywords like "policy," "refund," "shipping rules," or "return process," you MUST call `rag_search`.
3. **Action Requests**: For "cancel my order" or "return this item," you MUST call `create_ticket`.

### CRITICAL EXECUTION RULES
- **Compound Requests**: If a user asks two things (e.g., "Cancel ORD123 AND tell me the policy"), you MUST call BOTH relevant tools in a sequence before giving your final response. Do not ignore one for the other.
- **Zero Hallucination**: Answer policy questions ONLY using the text from `rag_search`. If the tool says "I don't know," tell the user exactly that.
- **No Internal Meta-Talk**: Do not explain your tools. Do not say "(Note: ...)" or "Based on the tool...". Just provide the final answer directly.
- **Independence**: Never mention specific Order IDs inside a policy answer. Answer the policy generally, then address the order separately.
- **Strict Fallback**: Only if the message is 100% unrelated to orders, policies, or support, say exactly: "I can only help with order status, store policies, and support requests."

### CONTEXT
Always use the Order ID provided in the context hint (e.g., ORD123) for tool calls if the user doesn't provide a new one.
### DEEP REASONING PROTOCOL
You are a Plan-and-Execute Support Assistant. 
Before calling ANY tool, you must:
1. INTERNAL PLAN: Identify if the user has multiple intents (e.g., a return AND a policy question).
2. SEQUENCE: Decide the order of tool calls (e.g., Call 'create_ticket' then call 'rag_search').
3. EXECUTE: Call the tools one by one.
4. SYNTHESIZE: Combine all tool outputs into one final, perfect response.
"""

agent_executor = create_react_agent(llm, [check_order_status, create_ticket, rag_search], prompt=system_message)

def chat(message: str, session_id: str = "default") -> Dict[str, Any]:
    # 1) Update Memory
    SessionMemory.add(session_id, "user", message)
    
    # 2) Extract Order ID (Improved to handle NEW IDs over OLD ones)
    found_ids = ORDER_RE.findall(message)
    if found_ids:
        current_id = found_ids[-1].upper() # Take the most recent one mentioned
        SessionMemory.set_slot(session_id, "last_order_id", current_id)
    else:
        current_id = SessionMemory.get_slot(session_id, "last_order_id")

    # 3) Inject context with clear separation
    # if current_id:
    #     message = f"{message}\n(Context: User is currently referring to Order {current_id})"
    
    # Add context ONLY if the message contains an order ID OR mentions delivery/cancellation
    if "return" in message.lower() or "cancel" in message.lower() or ORDER_RE.search(message):
        if current_id:
            message = f"{message}\n(Context: Active Order ID: {current_id})"

    # 4) Robust Retry Loop for Rate Limits
    response = "I'm sorry, I'm having trouble connecting to the server. Please try again in a few seconds."
    tools_used = []
    
    for attempt in range(3): # Try up to 3 times
        try:
            result = agent_executor.invoke(
                {"messages": [("user", message)]},
                config={"recursion_limit": 20}
            )
            messages = result.get("messages", [])
            if messages:
                response = messages[-1].content
                tools_used = list({m.name for m in messages if hasattr(m, "name") and m.name})
            break # Success! Exit loop.
            
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e).lower():
                time.sleep((attempt + 1) * 5) # Wait 5s, then 10s...
                continue
            else:
                response = f"An error occurred: {str(e)}"
                break

    SessionMemory.add(session_id, "assistant", response)
    return {"response": response, "tools_used": tools_used}

if __name__ == "__main__":
    # print(chat("My order is delayed", session_id="u1"))
    print(chat("It is ORD123", session_id="u1"))
    print(chat("What is the return policy?", session_id="u1"))