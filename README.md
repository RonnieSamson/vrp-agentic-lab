# VRP Agentic Lab

This repository contains a software artefact developed as part of the course  
**"Tillämpning av AI-agenter i Unity 2026"** at the **University of Borås**.

The project implements a simplified **agentic workflow** for route planning in a home-care scenario.

The system demonstrates how an AI agent can:

- Interpret routing goals for home care staff.
- Call tools to calculate distances between locations.
- Validate time-window constraints for visits.
- Maintain state through a trajectory of previous decisions and observations.
- Recover from failures by iteratively refining the route plan when constraints are violated.

The implementation is intentionally simplified to focus on **agentic workflows and decision loops**, rather than full-scale logistics optimisation.

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
