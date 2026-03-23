import json
from pathlib import Path

from app.agent import run_agent
from app.models import Ticket


def load_tickets() -> list[Ticket]:
	data_path = Path(__file__).resolve().parent.parent / "data" / "tickets.json"
	with data_path.open("r", encoding="utf-8") as file:
		ticket_dicts = json.load(file)

	return [Ticket(**ticket_dict) for ticket_dict in ticket_dicts]


def main() -> None:
	tickets = load_tickets()
	demo_tickets = tickets[:4]

	for ticket in demo_tickets:
		result = run_agent(ticket)
		print(f"Ticket ID: {result['ticket_id']}")
		print(f"Final Answer: {result['final_answer']}")
		print("Trajectory:")
		print(json.dumps(result["trajectory"], indent=2, ensure_ascii=False))
		print("-" * 60)


if __name__ == "__main__":
	main()
