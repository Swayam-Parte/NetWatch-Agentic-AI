"""CLI: ensure the configured synthetic NetWatch dataset minimums."""
import argparse
from data.generator import ensure_dataset

parser = argparse.ArgumentParser(description="Generate/extend NetWatch synthetic demo records.")
parser.add_argument("--customers", type=int, default=1000)
parser.add_argument("--events", type=int, default=5000)
parser.add_argument("--cases", type=int, default=500)
parser.add_argument("--seed", type=int, default=20261123)
args = parser.parse_args()
print(ensure_dataset(args.customers, args.events, args.cases, args.seed))
