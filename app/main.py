import json
from pathlib import Path

from app.agent import run_agent
from app.models import Ticket, AgentDecision
from app.validator import validate_decision


def load_tickets() -> list[Ticket]:
	data_path = Path(__file__).resolve().parent.parent / "data" / "tickets.json"
	with data_path.open("r", encoding="utf-8") as file:
		ticket_dicts = json.load(file)

	return [Ticket(**ticket_dict) for ticket_dict in ticket_dicts]



def main() -> None:
	tickets = load_tickets()
	demo_tickets = tickets  # all tickets

	for ticket in demo_tickets:
		result = run_agent(ticket)
		print(f"Ticket ID: {result['ticket_id']}")
		print(f"Final Answer: {result['final_answer']}")
		print("Trajectory:")
		print(json.dumps(result["trajectory"], indent=2, ensure_ascii=False))

		# Validate the agent's final decision
		decision = AgentDecision(
			action="final",
			final_answer=result["final_answer"]
		)
		validation_errors = validate_decision(ticket, decision)
		if validation_errors:
			print("VALIDATOR: Validation errors found:")
			for err in validation_errors:
				print(f"  - {err}")
		else:
			print("VALIDATOR: No validation errors.")
		print("-" * 60)


if __name__ == "__main__":
	main()
