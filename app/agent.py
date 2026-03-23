import json
from dataclasses import asdict

from langchain_ollama import ChatOllama

from app.models import AgentDecision, Ticket
from app.tools import check_required_fields, read_policy


POLICY_TOPIC_BY_ISSUE_TYPE = {
	"return_request": "returns",
	"billing_issue": "billing",
	"shipping_issue": "shipping",
}


SYSTEM_PROMPT = """You are a small workflow controller for support ticket triage in a diving shop and diving services platform.

Use the provided ticket data, current step, and trajectory to decide the next best action.
Think step by step from the state you are given.
Choose either a tool action or a final answer.
Return ONLY valid JSON.
Do not return explanations outside the JSON.
Use only the allowed tools.
Avoid repeating the same unnecessary action if the trajectory already contains that observation.

Important tool rules:
- Valid actions are ONLY: tool, final
- Valid tools are ONLY: read_policy, check_required_fields
- For read_policy, valid tool_input values are ONLY: returns, billing, shipping
- Never pass null, ticket JSON, field names, issue types, or full sentences as read_policy tool_input
- Never pass values like return_request, billing_issue, shipping_issue, order_number, or full JSON strings to read_policy
- If the issue type is return_request, use returns when reading policy
- If the issue type is billing_issue, use billing when reading policy
- If the issue type is shipping_issue, use shipping when reading policy
- For service_request, course_booking, and trip_booking, there is no dedicated policy file yet
- For service_request, course_booking, and trip_booking, usually check required fields first and then return a final answer
- If required fields are present and enough information has already been gathered, return action as final
- Do not repeat the same tool call if its result already appears in the trajectory

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
	mapped_policy_topic = POLICY_TOPIC_BY_ISSUE_TYPE.get(ticket.issue_type)
	if trajectory:
		trajectory_text = json.dumps(trajectory, indent=2)
	else:
		trajectory_text = "No previous actions have been taken yet."

	if mapped_policy_topic is None:
		policy_guidance = (
			"This issue type does not have a dedicated policy file yet. "
			"Usually check required fields and then produce a final answer."
		)
	else:
		policy_guidance = (
			f"Issue type mapping reminder: {ticket.issue_type} -> {mapped_policy_topic}. "
			f"If you use read_policy, the tool_input must be exactly '{mapped_policy_topic}'."
		)

	return (
		f"Current step: {step}\n"
		f"Max steps: {max_steps}\n\n"
		"Ticket fields:\n"
		f"{json.dumps(ticket_data, indent=2)}\n\n"
		"Issue type to policy mapping:\n"
		"- return_request -> returns\n"
		"- billing_issue -> billing\n"
		"- shipping_issue -> shipping\n"
		"- service_request, course_booking, trip_booking -> no policy file yet\n\n"
		f"{policy_guidance}\n\n"
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


def has_repeated_tool_call(trajectory: list[dict], tool_name: str | None, tool_input: str | None) -> bool:
	for entry in trajectory:
		if entry.get("type") != "tool_result":
			continue

		content = entry.get("content", {})
		if content.get("tool_name") == tool_name and content.get("tool_input") == tool_input:
			return True

	return False


def has_required_fields_result(trajectory: list[dict]) -> bool:
	for entry in trajectory:
		if entry.get("type") != "tool_result":
			continue

		content = entry.get("content", {})
		if content.get("tool_name") == "check_required_fields":
			return True

	return False


def has_policy_result(trajectory: list[dict], topic: str) -> bool:
	for entry in trajectory:
		if entry.get("type") != "tool_result":
			continue

		content = entry.get("content", {})
		if content.get("tool_name") == "read_policy" and content.get("tool_input") == topic:
			return True

	return False


def has_enough_information(ticket: Ticket, trajectory: list[dict]) -> bool:
	if not has_required_fields_result(trajectory):
		return False

	topic = POLICY_TOPIC_BY_ISSUE_TYPE.get(ticket.issue_type)
	if topic is None:
		return True

	return has_policy_result(trajectory, topic)


def build_final_answer(ticket: Ticket, trajectory: list[dict]) -> str:
	topic = POLICY_TOPIC_BY_ISSUE_TYPE.get(ticket.issue_type)

	route_by_issue_type = {
		"return_request": "Route this ticket to returns support.",
		"billing_issue": "Route this ticket to billing support.",
		"shipping_issue": "Route this ticket to logistics and shipping support.",
		"service_request": "Route this ticket to equipment service support.",
		"course_booking": "Route this ticket to course administration support.",
		"trip_booking": "Route this ticket to trip booking support.",
	}

	message = route_by_issue_type.get(ticket.issue_type, "Route this ticket to general support.")
	required_fields_text = "Required fields were checked."

	if topic and has_policy_result(trajectory, topic):
		policy_text = f" The {topic} policy was reviewed."
	else:
		policy_text = ""

	return f"{message} {required_fields_text}{policy_text}"


def run_agent(ticket: Ticket, max_steps: int = 5) -> dict:
	llm = ChatOllama(model="llama3.1:8b", temperature=0)
	trajectory = []
	final_answer = None

	for step in range(1, max_steps + 1):
		if has_enough_information(ticket, trajectory):
			final_answer = build_final_answer(ticket, trajectory)
			trajectory.append(
				{
					"step": step,
					"type": "final",
					"content": final_answer,
				}
			)
			break

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
			if has_repeated_tool_call(trajectory, decision.tool_name, decision.tool_input):
				trajectory.append(
					{
						"step": step,
						"type": "error",
						"content": (
							f"Repeated tool call blocked: {decision.tool_name} "
							f"with input {decision.tool_input}"
						),
					}
				)
				continue

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
				if has_enough_information(ticket, trajectory):
					final_answer = build_final_answer(ticket, trajectory)
					trajectory.append(
						{
							"step": step,
							"type": "final",
							"content": final_answer,
						}
					)
					break
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
				# NY LOGIK: Stoppa om info saknas
				if observation.startswith("MISSING:"):
					missing_fields = observation.replace("MISSING:", "").strip()
					final_answer = f"Ärendet kan inte triageras: följande information saknas: {missing_fields}"
					trajectory.append(
						{
							"step": step,
							"type": "final",
							"content": final_answer,
						}
					)
					break
				if has_enough_information(ticket, trajectory):
					final_answer = build_final_answer(ticket, trajectory)
					trajectory.append(
						{
							"step": step,
							"type": "final",
							"content": final_answer,
						}
					)
					break
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
