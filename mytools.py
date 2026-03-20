import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict
from langchain.tools import tool

ORDERS_PATH = Path(r"C:\Users\VandanaS\Desktop\AI_assistant\data\orders.json")
TICKETS_PATH = Path(r"C:\Users\VandanaS\Desktop\AI_assistant\data\tickets.json")

def _load_orders() -> Dict:
    return json.loads(ORDERS_PATH.read_text())

def _load_tickets():
    if TICKETS_PATH.exists():
        try:
            return json.loads(TICKETS_PATH.read_text())
        except json.JSONDecodeError:
            return []
    return []

def _save_tickets(tickets):
    TICKETS_PATH.write_text(json.dumps(tickets, indent=2))

@tool
def check_order_status(order_id: str) -> Dict:
    """ Tool to check the status of an order by its ID."""
    orders = _load_orders()
    if order_id not in orders:
        return {"found": False, "message": f"Order {order_id} not found."}
    order = orders[order_id]
    return {
        "found": True,
        "order_id": order_id,
        "customer_name": order.get('customer_name'),
        "status": order.get('status'),
        "expected_delivery": order.get('expected_delivery'),
    }

@tool
def create_ticket(issue: str, metadata: Dict = None) -> Dict:
    """ Tool to create a support ticket. Checks for existing open tickets to prevent duplicates."""
    
    md = metadata or {}
    order_id = md.get("order_id")

    # 1) Validate order_id format
    if not isinstance(order_id, str) or not re.match(r"^ORD\d+$", order_id):
        return {
            "status": "skipped",
            "message": "Valid order_id (e.g., ORD123) is required to create a ticket.",
        }

    # 2) Load existing tickets to check for duplicates
    tickets = _load_tickets()
    
    # Check if there is already an "open" ticket for this specific order_id
    for t in tickets:
        if t.get("metadata", {}).get("order_id") == order_id and t.get("status") == "open":
            return {
                "id": t["id"],
                "status": "skipped",
                "message": f"An open ticket ({t['id']}) already exists for order {order_id}."
            }

    # 3) If no duplicate found, create the new ticket
    ticket = {
        "id": f"TCK{len(tickets)+1:04d}",
        "issue": issue,
        "metadata": md,
        "created_at": datetime.utcnow().isoformat() + 'Z',
        "status": "open",
    }
    
    tickets.append(ticket)
    _save_tickets(tickets)
    return ticket
