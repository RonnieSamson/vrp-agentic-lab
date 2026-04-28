# Agentic Ticket Triage Workflow for a Diving Shop Platform

This repository contains a small software artefact developed for the course **"Tillämpning av AI-agenter i Unity 2026"** at **Högskolan i Borås**.

The project implements a simple but clear **agentic workflow** for support-ticket triage in a **diving shop / diving services platform**.

---

## Setup

Clone the repository and create a local Python environment.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Requirements

- Python 3.13
- Ollama installed locally
- Local Ollama model: `llama3.1:8b`

Download the model:

```bash
ollama pull llama3.1:8b
```

---

## Run the application

From the project root, run:

```bash
python -m app.main
```

This loads tickets from `data/tickets.json`, runs the agentic workflow, prints the final answer, shows the trajectory, and runs validation.

---

## Run the evaluation

From the project root, run:

```bash
python -m eval.run_eval
```

This runs both:

- a simple rule-based baseline
- the agentic workflow

The result is saved to:

```text
eval/evaluation_results.json
```

---

## Project purpose

The system is designed as a support-ticket triage workflow for a diving shop / diving services platform.

The platform domain includes:

- sales of diving equipment
- wetsuits / drysuits
- diving accessories
- dive computers
- spare parts
- service and maintenance of diving equipment
- diving courses
- guided dive trips / dive excursions

The workflow handles support-related tickets such as:

- return requests
- billing issues
- shipping issues
- equipment service requests
- course booking questions
- dive trip booking questions

---

## What the system demonstrates

The project demonstrates core concepts in **agentic workflow design**, including:

- goal interpretation
- step-by-step decision making
- tool use
- state / memory handling through trajectory
- iterative reasoning
- recovery from invalid outputs or unsupported actions
- transparent traces of intermediate decisions
- deterministic validation through a rule-based guardrail
- comparison against a simple baseline

---

## Implemented workflow design

The implemented workflow includes:

1. **Task environment**
   - local support tickets in JSON format
   - local policy documents as text files

2. **Agentic controller loop**
   - receives a ticket
   - asks the local LLM what the next action should be
   - calls a tool when needed
   - observes the result
   - updates its trajectory/state
   - decides whether to continue or produce a final answer

3. **Tools**
   - `read_policy` reads local policy documents
   - `check_required_fields` checks whether required fields are missing from a ticket

4. **Validation and recovery**
   - invalid model output is handled safely
   - unknown tool calls are handled safely
   - final answers are checked by `validator.py`
   - the validator acts as a deterministic guardrail for business rules

5. **Evaluation**
   - `eval/baseline.py` implements a simple rule-based baseline
   - `eval/run_eval.py` compares the baseline with the agentic workflow
   - results are saved to `eval/evaluation_results.json`

---

## Project structure

```text
vrp-agentic-lab/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── agent.py
│   ├── tools.py
│   ├── validator.py
│   ├── models.py
│   └── utils.py
│
├── data/
│   ├── tickets.json
│   └── policies/
│       ├── return_policy.txt
│       ├── billing_policy.txt
│       └── shipping_policy.txt
│
├── eval/
│   ├── __init__.py
│   ├── baseline.py
│   ├── run_eval.py
│   └── evaluation_results.json
│
├── logs/
│
├── test_ollama.py
├── requirements.txt
├── README.md
└── .gitignore
```

Note: `evaluation_results.json` is generated when running:

```bash
python -m eval.run_eval
```

---

## Runtime flow

1. `app/main.py` reads support tickets from `data/tickets.json`.
2. Each ticket is sent to `app/agent.py`.
3. The agent uses the local Ollama model `llama3.1:8b`.
4. The agent can call tools in `app/tools.py`.
5. Tool results are stored in a `trajectory`.
6. The agent produces a final answer.
7. `app/validator.py` checks the final answer against business rules.
8. `eval/run_eval.py` compares the agentic workflow with a simple baseline.

---

## Evaluation summary

The evaluation compares a simple baseline with the agentic workflow.

The baseline performs direct rule-based routing based on `issue_type`. It does not use an LLM, policy lookup, tool calls, trajectory, or iterative reasoning.

The agentic workflow uses the local LLM, tool calls, policy lookup, trajectory-based state, and validation through a deterministic guardrail.

In the current evaluation run, both baseline and agentic workflow produced the same number of tickets without validator remarks. The main difference is that the agentic workflow demonstrates the intended agentic behaviour through multiple recorded steps and tool calls, while the baseline is a single-step rule-based comparison point.