# NetWatch 2.0 — Milestone 5
## Integration, scenario testing and scalable synthetic data

### Objectives
1. Validate the existing multi-agent workflow end to end.
2. Preserve original jury scenarios while expanding data volume.
3. Provide reproducible, relational synthetic customer/device/event data.
4. Support append-only runtime network-event simulation.
5. Validate database relationships and account lookup against generated records.

### Synthetic dataset design
The initial target is 1,000 customers, 1,000 network devices, 5,000 network events and 500 historical cases. The original notebook demo accounts C1001–C1004 are retained exactly; additional customer IDs begin at C1005. Generated records are fictional and are not real subscriber or network telemetry.

### Sustainable generation
- A fixed seed is used for reproducible initial synthetic records.
- `ensure_dataset()` is idempotent and only fills missing rows up to configured minimum targets.
- Existing records are not deleted when the generator is run again.
- `generate_network_events()` appends runtime events in bounded batches.
- SQLite indexes support area, customer and event-time lookups.
- Device and event records reference existing customer IDs.

### Runtime integration
The Streamlit Tickets & Analytics view reports live database counts for customers, devices, events and historical cases. It provides a selectable runtime event batch generator. Account lookup reads the generated SQLite customer table, retaining the original fixture fallback for compatibility.

### Validation plan
Run `python -m unittest discover -s tests -v`. The M5 data tests validate target counts, preservation of original fixture identities, generated account lookup, idempotence, append-only event generation and referential integrity. Existing M2/M3 tests continue to validate missing-ID handling, active customer diagnosis, outage/suspension escalation, conversation continuity, explicit resolution, WAN evidence replanning, tool retry and attempt-limit escalation.

### Limitations
All customer, device, event and historical case records are synthetic. Network event simulation is a local academic demonstration and is not a live monitoring service. The LLM may help interpret language and explain results, while deterministic local tools remain authoritative for the simulated account/network facts.
