# NetWatch 2.0 — Intelligent Connectivity Support

A supervisor-led Agentic AI prototype for simulated internet-connectivity support. NetWatch accepts a customer complaint, gathers local account/network evidence, retrieves similar historical cases, recommends safe troubleshooting steps, processes follow-up feedback, and leaves a case pending, resolves it after explicit customer confirmation, or escalates it into a local SQLite ticket.

> **Academic prototype:** Customer, device, network-event and historical-case records are synthetic. NetWatch does not connect to a live ISP, physical router telemetry, or an external ticketing platform.

## Architecture at a glance

- **Supervisor Agent** — coordinates the workflow, shared case state, bounded retries, evidence-based replanning and final case packaging.
- **Customer Agent** — uses Gemini-assisted structured extraction when configured, with deterministic fallback, then looks up the customer account.
- **Network Diagnosis Agent** — uses deterministic account, simulated outage and synthetic event evidence; Gemini may provide advisory analysis.
- **Memory Agent** — retrieves similar historical cases using TF-IDF and cosine similarity.
- **Troubleshooting Agent** — prepares safe, context-aware next steps; Gemini may refine recommendations.
- **Customer Feedback Agent** — classifies follow-up as resolved, unresolved, action completed or unclear.
- **Verification & Escalation Agent** — applies deterministic resolution/escalation rules and creates local tickets.
- **Gemini adapter** — wraps the Google Gen AI SDK. API credentials are read from `.env`.

## Technology stack

Python 3.11+, Streamlit, Google Gen AI SDK, SQLite, pandas, Plotly, scikit-learn (TF-IDF/cosine similarity), python-dotenv and Pydantic.

## Synthetic dataset targets (M5)

| Entity | Initial target |
|---|---:|
| Customers | 1,000 |
| Network devices | 1,000 |
| Network events | 5,000 |
| Historical cases | 500 |

The original demonstration customers C1001–C1004 are preserved; generated customer IDs begin at C1005. The generator uses a fixed seed, is idempotent, fills missing records up to the configured targets, and does not delete existing rows. Runtime event generation appends additional synthetic events. Device and event records reference existing customers.

The repository's local `data/netwatch.db` is intentionally excluded. Run the seed command to generate a local database. Automated M5 tests validate target counts, generated account lookup, idempotence, append-only event generation and relational integrity.

## Setup — Windows PowerShell

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and add your own Gemini API key:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.8-flash
MAX_TROUBLESHOOTING_ATTEMPTS=3
MEMORY_SIMILARITY_THRESHOLD=0.08
DATABASE_PATH=data/netwatch.db
```

**Never commit `.env`, API keys, `.venv`, or local database files.** If a key is exposed, revoke it and create a replacement.

## Initialise and run

Run these commands from the project root (the directory containing `app.py`):

```powershell
python -m scripts.seed_dataset
python -m unittest discover -s tests -v
python -m streamlit run app.py
```

Use `python -m scripts.seed_dataset` (module mode) so Python resolves the project packages from the root directory.

## Original demo scenarios

| Customer | Simulated condition | Expected demonstration |
|---|---|---|
| C1001 | Active, Pune, router online, no area outage | Diagnosis and guided troubleshooting; pending customer confirmation |
| C1002 | Active, Pune, router offline | Router-side checks and escalation behaviour |
| C1003 | Suspended, Mumbai | Account restriction and escalation |
| C1004 | Active, Mumbai, simulated major area outage | Area-outage evidence and escalation |

Use a generated ID such as C1005 after seeding to demonstrate generated-customer lookup and the same agent workflow.

## Automated validation

The current source tree has **16 automated tests**. The tested suite covers the original customer scenarios, missing-ID handling, conversation persistence, explicit resolution, tool retry, WAN evidence replanning, attempt-limit escalation, generated-customer lookup/workflow, idempotent seeding, append-only runtime events and relational integrity.

Re-run the suite on the presentation machine. Live Gemini connectivity is separate from offline unit testing and should be smoke-tested with the team's own valid API key.

## Project structure

```text
NetWatch/
├── agents/          # Supervisor and six specialist agents
├── data/            # Synthetic dataset generator and event simulation
├── frontend/        # Streamlit frontend package
├── legacy/          # Original jury notebook
├── llm/             # Gemini SDK adapter and prompts
├── memory/          # SQLite persistence and historical-case retrieval
├── report/          # Milestone implementation notes
├── scripts/         # Dataset seeding and runtime event simulation
├── screenshots/     # Supplied M3/M4 application screenshots
├── tests/           # Automated regression and M5 data tests
├── tools/           # Simulated account/network tools and local tickets
├── docs/            # Final report, diagrams and presentation
├── app.py
├── config.py
├── requirements.txt
└── .env.example
```

## Milestones

- M1 — notebook audit and modular project foundation
- M2 — Gemini adapter, supervisor and specialist-agent backend
- M3 — persistent conversations, feedback, retry and evidence-based replanning
- M4 — Streamlit control center and operational views
- M5 — scalable synthetic data engine and integration/regression tests
- M6 — final report, presentation, README and screenshot evidence

## Limitations

- All customer and network records are synthetic.
- No live ISP, router telemetry or external help-desk integration is connected.
- Tickets are local SQLite records.
- Gemini availability depends on a valid key, network access and model availability.
- Automated tests validate implemented software behaviour; they do not establish universal model accuracy or production reliability.
