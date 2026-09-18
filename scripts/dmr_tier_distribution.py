#!/usr/bin/env python3
"""DMR replication tier/category distribution probe.

Reads a Factorio `--dump-data` JSON (data-raw-dump.json) and prints how the
dynamically-generated replication recipes (dmrsa-repl-*) are distributed by
tier and by category subgroup. Run BEFORE any tier/category redesign to see the
real distribution for the INSTALLED modlist (the dump reflects the installed
mod version, not local source).

Usage:
    python3 dmr_tier_distribution.py <data-raw-dump.json> [--sample N]

Tier is derived from the recipe's crafting category (dmrsa-replication-<tier>);
category from the recipe's subgroup (dmrsa-replication-<cat>).
"""
import json
import re
import sys
from collections import Counter


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    path = args[0]
    sample_n = 0
    if "--sample" in args:
        try:
            sample_n = int(args[args.index("--sample") + 1])
        except (ValueError, IndexError):
            sample_n = 0

    with open(path) as f:
        dump = json.load(f)

    recipes = dump.get("recipe", {})
    repl = {n: r for n, r in recipes.items() if n.startswith("dmrsa-repl-")}

    tier_of = {}
    for name, r in repl.items():
        cat = r.get("category") or (r.get("categories") or [None])[0]
        m = re.search(r"replication-(\d+)$", cat or "")
        if m:
            tier_of[name] = int(m.group(1))

    print(f"dmrsa-repl-* recipes: {len(repl)}")
    print("By tier:", dict(sorted(Counter(tier_of.values()).items())))

    sg = Counter(r.get("subgroup", "?") for r in repl.values())
    print("\nBy subgroup (category):")
    for name, c in sorted(sg.items(), key=lambda x: -x[1]):
        print(f"  {name}: {c}")

    if sample_n:
        for t in range(1, 6):
            items = [n.replace("dmrsa-repl-", "") for n in tier_of if tier_of[n] == t]
            print(f"\nSample tier {t}:", items[:sample_n])


if __name__ == "__main__":
    main()
