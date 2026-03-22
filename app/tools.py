from pathlib import Path


POLICY_FILES = {
	"returns": "return_policy.txt",
	"billing": "billing_policy.txt",
	"shipping": "shipping_policy.txt",
}


def read_policy(topic: str) -> str:
	filename = POLICY_FILES.get(topic)
	if filename is None:
		return f"ERROR: unknown policy topic: {topic}"

	policy_path = Path(__file__).resolve().parent.parent / "data" / "policies" / filename
	if not policy_path.exists():
		return f"ERROR: policy file not found for topic: {topic}"

	return policy_path.read_text(encoding="utf-8")


def check_required_fields(ticket: dict) -> str:
	missing_fields = []

	required_fields = ["id", "customer_name", "issue_type", "message"]
	for field_name in required_fields:
		if not ticket.get(field_name):
			missing_fields.append(field_name)

	issue_type = ticket.get("issue_type")
	if issue_type in {"return_request", "billing_issue"} and not ticket.get("order_number"):
		missing_fields.append("order_number")

	if missing_fields:
		return f"MISSING: {', '.join(missing_fields)}"

	return "OK: all required fields present"
