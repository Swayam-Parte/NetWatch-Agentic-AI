# NetWatch 2.0 — Milestone 3

## Implemented
- SQLite-backed conversation state and message history.
- Follow-up feedback agent classifying resolved, unresolved, action completed and unclear responses.
- Resolution is only accepted after explicit customer confirmation.
- Bounded retry of the simulated area-status tool (one retry after the initial attempt).
- Follow-up WAN probe and diagnosis replanning when probe evidence conflicts with the account router snapshot.
- Attempt counter and escalation at the configured maximum.
- Streamlit chat interface with new-case control, conversation display, agent activity and ticket panel.

## Evidence and limitations
- Customer accounts, outage status and WAN probe observations are simulated local data. No ISP or router is contacted.
- Gemini is used for language understanding/enhancement when configured; deterministic tools remain authoritative for account, network and escalation state.
- Conversation persistence is local SQLite. No cloud memory service is used.
- Tests cover conversation persistence, explicit resolution, WAN evidence replanning, transient tool retry and attempt-limit escalation.
