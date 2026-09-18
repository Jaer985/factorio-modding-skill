#!/usr/bin/env python3
"""Scan Factorio mod .lua sources for numeric parameters in prototype
localised_name/localised_description arrays.

Factorio 2.x prototype (data-stage) localised strings REJECT numeric/boolean
parameters at load — "Value must be a string at ...localised_name[1]".
Numbers are runtime-only (game.translate). All parameters must be strings
(or nested { "key" } tables — those are allowed; only raw numbers/booleans
break the load).

Usage:
    python3 scan_localised_numeric_params.py [path-to-mod-source-dir]

Exit code 0 = clean, 1 = findings. Prints each offending line.

Pitfall discovered in DMR v4.2.0 gate test (2026-08-23):
localised_name = { "technology-name.dmrsa-materials-tech", def.tier }  -- BOOM
Fix: tostring() the numeric param.
"""

import os
import re
import sys

# Matches localised_name/localised_description = { ... } NON-nested bodies.
# Nested { "key" } tables are fine; this catches bare number tokens in the
# parameter list using a quote-balance heuristic.
PATTERN = re.compile(r"localised_(?:name|description)\s*=\s*\{([^}]*)\}")
NUMBER = re.compile(r'(?<!["\w.])-?\d+(?:\.\d+)?(?!["\w])')


def scan_file(path):
    hits = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        src = fh.read()
    for m in PATTERN.finditer(src):
        body = m.group(1)
        for tok in NUMBER.finditer(body):
            # skip tokens inside a string literal (odd quote count before it)
            if body[: tok.start()].count('"') % 2 == 1:
                continue
            # skip numbers that only appear inside a nested { ... } parameter —
            # nested tables are LOCALISED STRINGS; their internals are validated
            # recursively and a nested {"key", 1} would ALSO crash. Keep the hit
            # (conservative) — manually review any nested-table report.
            hits.append(body.strip().replace("\n", " ")[:120])
            break
    return hits


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    findings = []
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            if not f.endswith(".lua"):
                continue
            p = os.path.join(dirpath, f)
            for hit in scan_file(p):
                findings.append((os.path.relpath(p, root), hit))
    if findings:
        print("Numeric params in prototype localised strings (REQUIRED tostring()):")
        for rel, hit in findings:
            print(f"  {rel} | {hit}")
        print("\nFAIL: found", len(findings), "offending block(s).")
        return 1
    print("OK: no numeric params in localised strings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())