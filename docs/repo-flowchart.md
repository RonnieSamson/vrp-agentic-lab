# Repo Flowchart

Nedan finns en översikt av det som faktiskt ingår i körflödet: `app/`, `data/` och den lokala Ollama-kontrollen.

```mermaid
flowchart LR
  classDef source fill:#E8F1FF,stroke:#2563EB,color:#0F172A;
  classDef data fill:#FFF7ED,stroke:#EA580C,color:#0F172A;
  classDef support fill:#ECFDF5,stroke:#059669,color:#0F172A;
  classDef empty fill:#F3F4F6,stroke:#9CA3AF,color:#374151,stroke-dasharray: 5 5;

  subgraph App["app/"]
    Main["main.py\nOrchestrates ticket processing"]:::source
    Agent["agent.py\nLLM-driven agent loop"]:::source
    Models["models.py\nTicket + AgentDecision"]:::support
    Tools["tools.py\nread_policy + check_required_fields"]:::support
    Validator["validator.py\nBusiness-rule validation"]:::support
    Utils["utils.py\nEmpty helper module"]:::empty
  end

  subgraph Data["data/"]
    Tickets["tickets.json\nSupport tickets"]:::data

    subgraph Policies["policies/"]
      ReturnPolicy["return_policy.txt"]:::data
      BillingPolicy["billing_policy.txt"]:::data
      ShippingPolicy["shipping_policy.txt"]:::data
    end
  end

  Ollama[("Local Ollama model\nllama3.1:8b")]:::support
  Trajectory[("trajectory\nstep-by-step state")]

  Main -->|load tickets| Tickets
  Main -->|run agent| Agent
  Main -->|validate decision| Validator

  Agent -->|ticket data + trajectory| Models
  Agent -->|prompting| Ollama
  Agent -->|tool calls| Tools
  Agent -->|final checks| Validator
  Agent --> Trajectory

  Agent --> StatePrompt["build_state_prompt()"]:::source
  Agent --> SysPrompt["SYSTEM_PROMPT"]:::source
  StatePrompt --> LLM["ChatOllama.invoke()"]:::source
  SysPrompt --> LLM
  LLM --> Parse["parse_decision()"]:::source
  Parse --> Decision{"action?"}

  Decision -->|tool| ToolPick{"tool_name?"}
  Decision -->|final| FinalDirect["final answer from model"]:::source
  Decision -->|invalid| SafeStop["safe stop on invalid output"]:::source

  ToolPick -->|read policy| ReadPolicy["read_policy(topic)"]:::support
  ToolPick -->|check required fields| CheckFields["check_required_fields(ticket)"]:::support
  ToolPick -->|unknown| UnknownTool["unknown tool error"]:::source

  ReadPolicy --> ReturnPolicy
  ReadPolicy --> BillingPolicy
  ReadPolicy --> ShippingPolicy
  CheckFields --> Tickets

  ReadPolicy --> Trajectory
  CheckFields --> MissingCheck{"MISSING:?"}
  MissingCheck -->|yes| MissingFinal["final: missing information"]:::source
  MissingCheck -->|no| EnoughInfo{"enough information?"}
  EnoughInfo -->|yes| BuildFinal["build_final_answer()"]:::source
  EnoughInfo -->|no| StatePrompt

  BuildFinal --> Trajectory
  FinalDirect --> Trajectory
  MissingFinal --> Trajectory
  SafeStop --> Trajectory
  UnknownTool --> Trajectory

  Validator --> Models
  Validator --> Tickets

  TestOllama["test_ollama.py\nOllama smoke test"]:::source --> Ollama
```

## Kort läsning av flödet

1. `app/main.py` läser tickets från `data/tickets.json`.
2. Varje ticket skickas till `app/agent.py`, där modellen får välja mellan verktygsanrop eller ett slutligt svar.
3. Verktygen i `app/tools.py` läser lokala policyfiler eller kontrollerar obligatoriska fält.
4. Agenten bygger upp en `trajectory` för att undvika upprepningar och för att kunna avsluta säkert.
5. `app/validator.py` körs efteråt för att kontrollera affärsregler, särskilt för retur- och faktureringsärenden.
6. `test_ollama.py` är ett separat smoke test mot den lokala Ollama-modellen.
