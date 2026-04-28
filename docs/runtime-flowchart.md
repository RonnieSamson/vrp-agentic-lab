# Runtime Flowchart

```mermaid
flowchart LR
  classDef source fill:#E8F1FF,stroke:#2563EB,color:#0F172A;
  classDef data fill:#FFF7ED,stroke:#EA580C,color:#0F172A;
  classDef support fill:#ECFDF5,stroke:#059669,color:#0F172A;
  classDef empty fill:#F3F4F6,stroke:#9CA3AF,color:#374151,stroke-dasharray: 5 5;

  Tickets["data/tickets.json\nSupport tickets"]:::data
  Policies["data/policies/*.txt\nPolicy files"]:::data
  Ollama[("Local Ollama\nllama3.1:8b")]:::support

  Main["app/main.py\nLoad tickets and orchestrate"]:::source
  Agent["app/agent.py\nAgent loop and decision logic"]:::source
  Tools["app/tools.py\nread_policy + check_required_fields"]:::support
  Validator["app/validator.py\nBusiness-rule validation"]:::support
  Models["app/models.py\nTicket + AgentDecision"]:::support
  Test["test_ollama.py\nSmoke test"]:::source
  Trajectory["trajectory\nStep-by-step state"]:::empty

  Main --> Tickets
  Main --> Agent
  Main --> Validator

  Agent --> Models
  Agent --> Ollama
  Agent --> Tools
  Agent --> Trajectory

  Tools --> Policies
  Tools --> Tickets

  Agent -->|final answer| Validator
  Validator --> Tickets

  Test --> Ollama
```

## Kort läsning

1. `app/main.py` läser tickets och kör agenten för varje ärende.
2. `app/agent.py` frågar den lokala Ollama-modellen vad nästa steg ska vara.
3. Agenten kan läsa policyfiler eller kontrollera obligatoriska fält via `app/tools.py`.
4. Beslut och observationer sparas i en trajectory så att agenten inte upprepar sig.
5. `app/validator.py` gör en efterkontroll av slutbeslutet.
6. `test_ollama.py` är en separat kontroll mot samma lokala modell.