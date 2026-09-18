#!/usr/bin/env python3
"""
Audit locale parity for a Factorio mod (EN vs ES-ES).

Used in the DMR v3.7.0 D2/D3 description-refresh passes. Catches:
  1. Key parity: every [section].key in EN must exist in ES and vice versa.
  2. Stale-text residue: any forbidden substring (old lore/descriptions) that
     must be GONE from both files.
  3. Factual-number survival: gameplay-relevant numbers (e.g. "3x", "5x") that
     a lore rewrite must NOT drop (planetary replicator speeds, freshness %).

Usage:
  python3 audit_locale_parity.py <locale_dir> [--forbid "old text" ...] \
      [--require "KEY:substring" ...]

Example (DMR D3 lore rewrite):
  python3 audit_locale_parity.py locale/en:es-ES \
      --forbid "Normally dark matter passes" "materia oscura atraviesa" \
      --require "dmrsa-replicator-vulcanus:3x" "dmrsa-replicator-gleba:3x" \
      --require "dmrsa-replicator-aquilo:5x"

Exit code 0 = all checks pass; 1 = any failure.
"""
import re
import sys
import os
import argparse


def parse_sections(path):
    """Parse a Factorio locale .cfg into {section: {key: value}}."""
    sections = {}
    current = None
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n\r")
            if not line or line.startswith("#"):
                continue
            sm = re.match(r"^\[([^\]]+)\]$", line)
            if sm:
                current = sm.group(1)
                sections.setdefault(current, {})
                continue
            if current and "=" in line:
                k, v = line.split("=", 1)
                sections[current][k] = v
    return sections


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("locale_dir", help="dir containing en/ and es-ES/ subdirs")
    ap.add_argument("--forbid", action="append", default=[],
                    help="substring that must NOT appear in either file (repeatable)")
    ap.add_argument("--require", action="append", default=[],
                    help="KEY:substring that must appear in BOTH locales for that key (repeatable)")
    args = ap.parse_args()

    en_path = os.path.join(args.locale_dir, "en", "dark-matter-replicators.cfg")
    es_path = os.path.join(args.locale_dir, "es-ES", "dark-matter-replicators.cfg")
    if not (os.path.exists(en_path) and os.path.exists(es_path)):
        print(f"FAIL: locale files not found under {args.locale_dir} (en/ + es-ES/)")
        return 1

    en = parse_sections(en_path)
    es = parse_sections(es_path)
    en_raw = open(en_path, encoding="utf-8", errors="replace").read()
    es_raw = open(es_path, encoding="utf-8", errors="replace").read()

    failures = []

    # 1. Key parity per section
    for section in en:
        if section not in es:
            failures.append(f"[SIN SECCIÓN EN ES] {section}")
            continue
        missing_es = set(en[section]) - set(es[section])
        missing_en = set(es[section]) - set(en[section])
        if missing_es:
            failures.append(f"[FALTAN EN ES] {section}: {sorted(missing_es)[:10]}")
        if missing_en:
            failures.append(f"[FALTAN EN EN] {section}: {sorted(missing_en)[:10]}")
    # sections only in ES
    for section in es:
        if section not in en:
            failures.append(f"[SIN SECCIÓN EN EN] {section}")

    # 2. Stale-text residue
    for frag in args.forbid:
        if frag in en_raw or frag in es_raw:
            failures.append(f"[TEXTO VIEJO PRESENTE] {frag!r}")

    # 3. Factual-number survival (key must contain substring in both locales)
    for spec in args.require:
        if ":" not in spec:
            failures.append(f"[REQUIRE mal formado] {spec!r} (esperaba KEY:substring)")
            continue
        key, sub = spec.split(":", 1)
        for label, sections in (("EN", en), ("ES", es)):
            found = any(sub in sections[s].get(key, "") for s in sections)
            if not found:
                failures.append(f"[REQUIRE] {label}: {key} no contiene {sub!r}")

    if failures:
        print("=== LOCALE PARITY FAILURES ===")
        for f in failures:
            print(f"  {f}")
        return 1
    print(f"Locale parity OK: {os.path.abspath(args.locale_dir)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
