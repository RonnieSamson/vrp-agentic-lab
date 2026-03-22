# Agentic Ticket Triage Workflow for a Diving Shop Platform

This repository contains a small software artefact developed for the course **"Tillämpning av AI-agenter i Unity 2026"** at **Högskolan i Borås**.

## Project purpose

The purpose of this project is to implement a simple but clear **agentic workflow** rather than a single-prompt chatbot.

The system is designed as a small support-ticket triage workflow for a **diving shop / diving services platform**.

The platform domain includes:

- sales of diving equipment
- wetsuits / drysuits
- diving accessories
- dive computers
- spare parts
- service and maintenance of diving equipment
- diving courses
- guided dive trips / dive excursions

The workflow is intended to handle support-related tickets such as:

- return requests
- billing issues
- shipping issues
- equipment service requests
- course booking questions
- dive trip booking questions

## What the system demonstrates

The project is built to demonstrate core concepts in **agentic workflow design**, including:

- goal interpretation
- step-by-step decision making
- tool use
- state / memory handling through trajectory
- iterative reasoning
- recovery from invalid outputs or unsupported actions
- transparent traces of intermediate decisions

## Planned workflow design

The final workflow is intended to include:

1. **A task environment**
   - local support tickets in JSON format
   - local policy documents as text files

2. **An agentic controller loop**
   - receives a ticket
   - interprets the next best action
   - calls a tool when needed
   - observes the result
   - updates its trajectory/state
   - decides whether to continue or produce a final answer

3. **Simple tools**
   - read policy documents
   - check whether required fields are missing from a ticket

4. **Validation and recovery**
   - handle invalid model output
   - handle unknown tool calls
   - later verify outputs against simple rules

5. **Evaluation**
   - later compare the workflow against a simpler baseline

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
├── logs/
│
├── eval/
│   ├── baseline.py
│   └── run_eval.py
│
├── test_ollama.py
├── requirements.txt
├── README.md
└── .gitignore

---

# Setup

Clone the repository and create a local Python environment.


python -m venv .venv

.venv\Scripts\activate

pip install -r requirements.txt

## Requirements

- Python 3.13
- Ollama installed locally

Download model:

ollama pull llama3.1:8b
