"""CLI: append a batch of synthetic network events."""
import argparse
from data.simulation import simulate_event_batch

parser = argparse.ArgumentParser(description="Append simulated NetWatch network events.")
parser.add_argument("--count", type=int, default=100)
parser.add_argument("--seed", type=int, default=None)
args = parser.parse_args()
print(simulate_event_batch(args.count, args.seed))
