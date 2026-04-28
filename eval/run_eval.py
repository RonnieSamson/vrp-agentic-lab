import json
from pathlib import Path

from app.agent import run_agent
from app.main import load_tickets
from app.models import AgentDecision
from app.validator import validate_decision
from eval.baseline import run_baseline


def count_tool_calls(trajectory: list[dict]) -> int:
    """
    Counts how many tool results exist in the trajectory.
    In the agentic workflow, tool calls produce entries of type 'tool_result'.
    In the baseline, this should normally be 0.
    """
    return sum(1 for entry in trajectory if entry.get("type") == "tool_result")


def count_steps(trajectory: list[dict]) -> int:
    """
    Counts how many recorded steps/entries exist in the trajectory.
    This gives a simple indication of whether the workflow was single-step
    or iterative.
    """
    return len(trajectory)


def evaluate_result(ticket, result: dict) -> dict:
    """
    Validates a single result and extracts simple evaluation metrics.
    """

    final_answer = result.get("final_answer") or ""

    decision = AgentDecision(
        action="final",
        final_answer=final_answer,
    )

    validation_errors = validate_decision(ticket, decision)
    trajectory = result.get("trajectory", [])

    return {
        "ticket_id": ticket.id,
        "issue_type": ticket.issue_type,
        "final_answer": final_answer,
        "steps": count_steps(trajectory),
        "tool_calls": count_tool_calls(trajectory),
        "validation_errors": validation_errors,
        "passed_validation": len(validation_errors) == 0,
    }


def summarize(results: list[dict]) -> dict:
    """
    Creates a small summary over all evaluated tickets.
    """

    total = len(results)

    if total == 0:
        return {
            "total_tickets": 0,
            "passed_validation": 0,
            "failed_validation": 0,
            "success_rate": 0,
            "average_tool_calls": 0,
            "average_steps": 0,
        }

    passed = sum(1 for result in results if result["passed_validation"])
    failed = total - passed

    total_tool_calls = sum(result["tool_calls"] for result in results)
    total_steps = sum(result["steps"] for result in results)

    return {
        "total_tickets": total,
        "passed_validation": passed,
        "failed_validation": failed,
        "success_rate": round(passed / total, 2),
        "average_tool_calls": round(total_tool_calls / total, 2),
        "average_steps": round(total_steps / total, 2),
    }


def main() -> None:
    """
    Runs the evaluation.

    For each ticket:
    1. Run the simple baseline.
    2. Run the agentic workflow.
    3. Validate both outputs.
    4. Save a JSON report.
    """

    tickets = load_tickets()

    baseline_results = []
    agent_results = []

    for ticket in tickets:
        print(f"Evaluating ticket {ticket.id}...")

        baseline_output = run_baseline(ticket)
        agent_output = run_agent(ticket)

        baseline_results.append(evaluate_result(ticket, baseline_output))
        agent_results.append(evaluate_result(ticket, agent_output))

    evaluation = {
        "baseline_summary": summarize(baseline_results),
        "agent_summary": summarize(agent_results),
        "baseline_results": baseline_results,
        "agent_results": agent_results,
    }

    output_path = Path(__file__).resolve().parent / "evaluation_results.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(evaluation, file, indent=2, ensure_ascii=False)

    print("\nEvaluation complete.")
    print(f"Results written to: {output_path}")

    print("\nBaseline summary:")
    print(json.dumps(evaluation["baseline_summary"], indent=2, ensure_ascii=False))

    print("\nAgent summary:")
    print(json.dumps(evaluation["agent_summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()