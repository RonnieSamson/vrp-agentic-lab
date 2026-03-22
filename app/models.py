from dataclasses import dataclass
from typing import Optional


@dataclass
class Ticket:
	id: str
	customer_name: str
	issue_type: str
	message: str
	order_number: Optional[str] = None
	purchase_date: Optional[str] = None


@dataclass
class AgentDecision:
	action: str
	tool_name: Optional[str] = None
	tool_input: Optional[str] = None
	final_answer: Optional[str] = None
