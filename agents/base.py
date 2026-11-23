"""Shared agent contract and structured execution event helper."""
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4
from memory.database import save_log

@dataclass
class AgentContext:
    run_id: str = field(default_factory=lambda: uuid4().hex[:10])
    customer_message: str = ""
    state: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    def log(self, agent: str, event: str, details: Any):
        item = {"agent":agent,"event":event,"details":details}
        self.events.append(item)
        try: save_log(self.run_id, agent, event, details)
        except Exception: pass

class BaseAgent:
    name = "Base Agent"
    def __init__(self, llm=None): self.llm = llm
