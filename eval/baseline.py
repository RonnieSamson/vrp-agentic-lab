from app.models import Ticket


def run_baseline(ticket: Ticket) -> dict:
    """
    Simple non-agentic baseline.

    The baseline performs direct rule-based routing.
    It does not use:
    - LLM reasoning
    - planning
    - tool calls
    - policy reading
    - trajectory-based iteration

    The purpose is to provide a simple comparison point
    against the agentic workflow.
    """

    route_by_issue_type = {
        "return_request": "Route this ticket to returns support.",
        "billing_issue": "Route this ticket to billing support.",
        "shipping_issue": "Route this ticket to logistics and shipping support.",
        "service_request": "Route this ticket to equipment service support.",
        "course_booking": "Route this ticket to course administration support.",
        "trip_booking": "Route this ticket to trip booking support.",
    }

    missing_fields = []

    if not ticket.id:
        missing_fields.append("id")

    if not ticket.customer_name:
        missing_fields.append("customer_name")

    if not ticket.issue_type:
        missing_fields.append("issue_type")

    if not ticket.message:
        missing_fields.append("message")

    if ticket.issue_type in {"return_request", "billing_issue"} and not ticket.order_number:
        missing_fields.append("order_number")

    if missing_fields:
        final_answer = (
            "Baseline could not triage the ticket because the following "
            f"information is missing: {', '.join(missing_fields)}"
        )
    else:
        final_answer = route_by_issue_type.get(
            ticket.issue_type,
            "Route this ticket to general support."
        )

    return {
        "ticket_id": ticket.id,
        "final_answer": final_answer,
        "trajectory": [
            {
                "step": 1,
                "type": "baseline_decision",
                "content": final_answer,
            }
        ],
    }