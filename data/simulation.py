"""Runtime network-event simulation helpers; all events are synthetic."""
from data.generator import generate_network_events


def simulate_event_batch(count: int = 25, seed: int | None = None) -> dict:
    inserted = generate_network_events(count=count, seed=seed)
    return {"inserted": inserted, "source": "synthetic_runtime", "message": f"Generated {inserted} simulated network events."}
