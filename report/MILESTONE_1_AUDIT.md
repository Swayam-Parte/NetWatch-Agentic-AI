# NetWatch — Milestone 1 Source Audit

## Source inspected
`legacy/NeTwatch_Final_Jury.ipynb` — 16 cells (markdown + Python).

## Observed implementation

| Area | Evidence in notebook |
|---|---|
| Customer data | 4 simulated customers: C1001–C1004 |
| Network data | Pune and Mumbai area status dictionaries |
| Support tools | retrieve_account, check_outage, diagnose_connection |
| Historical memory | 5 seed cases; TF-IDF and cosine similarity; top-2 retrieval |
| Intent model | 27 labelled utterances; TF-IDF + LogisticRegression |
| State | Explicit dictionary covering account, diagnosis, feedback, attempts and ticket state |
| Feedback | Phrase-based interpretation of resolution, restart, WAN light and router status |
| Troubleshooting | Rule-selected steps based on router status and attempt count |
| Escalation | Local ticket ID generated and diagnostic summary returned |
| Interface | Terminal input/output loop; not a web frontend |

## Migration notes

1. Preserve the source notebook unchanged under `legacy/`.
2. Extract deterministic data and tools into independent modules.
3. Retain the classifier as a baseline/fallback only if useful; LLM-based language understanding is a requested upgrade, not a feature of the source notebook.
4. Move ticket and case persistence from JSON/in-memory structures into SQLite during later milestones.
5. Validate the presentation's configuration (3 attempts, 0.08 threshold) against the notebook (4 attempts, 0.12 threshold) before finalising behavior.
6. Treat all network/customer information as simulated. The notebook does not establish live ISP connectivity or real-world network monitoring.

## Milestone 1 completion boundary

This milestone creates the modular project skeleton, dependency manifest, environment template, central settings, launchable Streamlit shell, setup guide and audit notes. It does not claim that the agentic workflow or LLM is implemented yet.
