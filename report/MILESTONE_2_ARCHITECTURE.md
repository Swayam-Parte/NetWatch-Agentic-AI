# NetWatch Milestone 2 — Backend Architecture

## Objective
Move from a notebook-driven single control loop to a modular supervisor-led multi-agent backend, while introducing Gemini as the natural-language reasoning provider.

## Agent responsibilities
1. Customer Agent: extracts issue summary, intent, urgency and customer ID; performs controlled account lookup.
2. Network Diagnosis Agent: queries simulated area outage data and account state; records rule-based diagnosis and may request Gemini's structured second opinion.
3. Memory Agent: retrieves up to two similar historical cases using TF-IDF/cosine similarity and the configured threshold.
4. Troubleshooting Agent: proposes safe next steps based on diagnosis; Gemini may refine the language/steps, but unsafe or unsupported actions are excluded by prompt and deterministic constraints.
5. Verification & Escalation Agent: determines resolved/pending/escalated status. A case is resolved only when the customer explicitly confirms restoration. It creates a local SQLite ticket for outage/account issues.

## Supervisor sequence
Customer message → Customer Agent → Diagnosis Agent → Memory Agent → Troubleshooting Agent → Verification & Escalation Agent → structured result + execution trace.

## Data and trust boundaries
The original notebook's four customer examples, two area network records and five historical cases are preserved in the modular implementation. Gemini does not directly determine account status or live network state. Those facts come from deterministic tools over simulated data. Gemini output is advisory and cannot override verification/escalation policy. No real ISP, router telemetry or external ticketing integration is claimed.

## Validation
`tests/test_agents.py` checks missing customer ID handling, normal Pune case, Mumbai outage escalation and suspended account escalation without requiring an API key. A separate live Gemini smoke test is needed after a valid key is configured.
