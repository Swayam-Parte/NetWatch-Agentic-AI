"""Controlled ticket creation. No external ticketing system is contacted."""
from datetime import datetime
from uuid import uuid4
from memory.database import create_ticket

def create_support_ticket(state: dict, reason: str):
    ticket = {
      "ticket_id": f"NT-{datetime.now():%y%m%d}-{uuid4().hex[:5].upper()}",
      "customer_id": state.get('customer_id'), "issue": state.get('issue'),
      "diagnosis": state.get('diagnosis'), "reason": reason,
      "created_at": datetime.now().isoformat(timespec='seconds'),
    }
    return create_ticket(ticket)
