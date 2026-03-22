import json
from dataclasses import asdict

from langchain_ollama import ChatOllama

from app.models import AgentDecision, Ticket
from app.tools import check_required_fields, read_policy


SYSTEM_PROMPT = """You are a small workflow controller for support ticket triage in a diving shop and diving services platform.

Use the provided ticket data, current step, and trajectory to decide the next best action.
Think step by step from the state you are given.
Choose either a tool action or a final answer.
Return ONLY valid JSON.
Do not return explanations outside the JSON.
Use only the allowed tools.
Avoid repeating the same unnecessary action if the trajectory already contains that observation.

Allowed actions:
- tool
- final

Allowed tools:
- read_policy
- check_required_fields

Required JSON schema:
{
  "action": "tool" | "final",
  "tool_name": "read_policy" | "check_required_fields" | null,
  "tool_input": "<string or null>",
  "final_answer": "<string or null>"
}
"""


def build_state_prompt(ticket: Ticket, trajectory: list[dict], step: int, max_steps: int) -> str:
	ticket_data = asdict(ticket)
	if trajectory:
		trajectory_text = json.dumps(trajectory, indent=2)
	else:
		trajectory_text = "No previous actions have been taken yet."

	return (
		f"Current step: {step}\n"
		f"Max steps: {max_steps}\n\n"
		"Ticket fields:\n"
		f"{json.dumps(ticket_data, indent=2)}\n\n"
		"Trajectory so far:\n"
		f"{trajectory_text}\n\n"
		"Choose the next best action for ticket triage. "
		"Use a tool if more information is needed, or return a final answer if the ticket can be triaged now."
	)


def parse_decision(raw_text: str) -> AgentDecision:
	try:
		data = json.loads(raw_text)
		if not isinstance(data, dict):
			raise ValueError("Model output was not a JSON object")
	except (json.JSONDecodeError, ValueError, TypeError):
		return AgentDecision(
			action="final",
			final_answer="Invalid model output. Stopping triage safely.",
		)

	return AgentDecision(
		action=data.get("action", "final"),
		tool_name=data.get("tool_name"),
		tool_input=data.get("tool_input"),
		final_answer=data.get("final_answer"),
	)


def run_agent(ticket: Ticket, max_steps: int = 5) -> dict:
	llm = ChatOllama(model="llama3.1:8b", temperature=0)
	trajectory = []
	final_answer = None

	for step in range(1, max_steps + 1):
		state_prompt = build_state_prompt(ticket, trajectory, step, max_steps)

		try:
			response = llm.invoke(f"{SYSTEM_PROMPT}\n\n{state_prompt}")
			raw_text = response.content if hasattr(response, "content") else str(response)
		except Exception as error:
			trajectory.append(
				{
					"step": step,
					"type": "error",
					"content": f"Model call failed: {error}",
				}
			)
			break

		decision = parse_decision(raw_text)
		trajectory.append(
			{
				"step": step,
				"type": "model_decision",
				"content": {
					"raw_text": raw_text,
					"parsed": asdict(decision),
				},
			}
		)

		if decision.action == "tool":
			if decision.tool_name == "read_policy":
				observation = read_policy(decision.tool_input or "")
				trajectory.append(
					{
						"step": step,
						"type": "tool_result",
						"content": {
							"tool_name": "read_policy",
							"tool_input": decision.tool_input,
							"observation": observation,
						},
					}
				)
				continue

			if decision.tool_name == "check_required_fields":
				observation = check_required_fields(asdict(ticket))
				trajectory.append(
					{
						"step": step,
						"type": "tool_result",
						"content": {
							"tool_name": "check_required_fields",
							"tool_input": "ticket",
							"observation": observation,
						},
					}
				)
				continue

			trajectory.append(
				{
					"step": step,
					"type": "error",
					"content": f"Unknown tool requested: {decision.tool_name}",
				}
			)
			break

		if decision.action == "final":
			final_answer = decision.final_answer or "No final answer was provided by the model."
			trajectory.append(
				{
					"step": step,
					"type": "final",
					"content": final_answer,
				}
			)
			break

		trajectory.append(
			{
				"step": step,
				"type": "error",
				"content": f"Unknown action requested: {decision.action}",
			}
		)
		break

	if final_answer is None:
		final_answer = "Unable to complete ticket triage within the allowed number of steps."

	return {
		"ticket_id": ticket.id,
		"final_answer": final_answer,
		"trajectory": trajectory,
	}
