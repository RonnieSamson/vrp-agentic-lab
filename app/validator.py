from datetime import datetime, timedelta
from app.models import Ticket, AgentDecision

def validate_decision(ticket: Ticket, decision: AgentDecision) -> list[str]:
	"""
	Validate the agent's decision against business rules and policies.
	Returns a list of validation error messages (empty if valid).
	"""
	errors = []

	# 1. For return requests: check 30-day window
	if ticket.issue_type == "return_request":
		if ticket.purchase_date:
			try:
				purchase_dt = datetime.strptime(ticket.purchase_date, "%Y-%m-%d")
				now = datetime.now()
				if (now - purchase_dt).days > 30:
					errors.append("Return request is outside the 30-day window.")
			except Exception:
				errors.append("Invalid purchase_date format.")
		else:
			errors.append("Missing purchase_date for return request.")

		# 2. For returns: order number required
		if not ticket.order_number:
			errors.append("Order number is required for return requests.")

		# 3. Used personal equipment: flag for manual review
		personal_equipment_keywords = ["mask", "snorkel", "fins", "drysuit", "wetsuit", "hood"]
		if any(word in ticket.message.lower() for word in personal_equipment_keywords):
			if "used" in ticket.message.lower() or "tested" in ticket.message.lower():
				errors.append("Return of used personal equipment requires manual review.")

	# 4. For billing issues: order number required
	if ticket.issue_type == "billing_issue" and not ticket.order_number:
		errors.append("Order number is required for billing issues.")

	# 5. Add more rules as needed

	return errors
