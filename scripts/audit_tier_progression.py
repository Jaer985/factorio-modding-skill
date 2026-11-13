#!/usr/bin/env python3
"""Audit DMR tier assignments against original-tech science progression.

Usage: python3 audit_tier_progression.py <data-raw-dump.json>

Replicates the key checks from the 3.7.1 dump audit:
  1. Version sanity (dmrsa-repl-* count, -instantiated leftovers)
  2. Tier distribution
  3. Category (subgroup) distribution — how big is 'general'?
  4. Tier-vs-original-tech mismatch buckets (the progression signal check)
  5. Endgame items (orig lvl 5) at low tier — the "unlock anything" offenders
  6. Mirror-tech simulation (threshold=1) with configurable exclusions

Pitfalls encoded: dump ingredients are ARRAY style ["pack", amount]; Python
regex uses '-' not Lua's '%-'; tiers can be None (guard max/sorted).
"""
import json
import re
import sys
from collections import Counter, defaultdict

DUMP_PATH = sys.argv[1] if len(sys.argv) > 1 else (
    '~/projects/Factorio-Modding/dark-matter-replicator/dumps/data-raw-dump.json')

dump = json.load(open(DUMP_PATH))
recipes = dump.get('recipe', {})
techs = dump.get('technology', {})

repl = {n: r for n, r in recipes.items() if n.startswith('dmrsa-repl-')}
repl_items = set(n.replace('dmrsa-repl-', '') for n in repl)


def repl_tier(n, r):
    cat = r.get('category') or (r.get('categories') or [None])[0]
    m = re.search(r'replication-(\d+)$', cat or '')
    return int(m.group(1)) if m else None


def pack_level(p):
    if not p or not isinstance(p, str):
        return None
    if 'advanced-logistic' in p:
        return 3
    if 'automation' in p or 'logistic' in p:
        return 1
    if 'military' in p:
        return 2
    if 'chemical' in p or 'production' in p or 'utility' in p:
        return 3
    if 'metallurgic' in p or 'electromagnetic' in p or 'agricultural' in p:
        return 4
    if 'space' in p or 'cryogenic' in p or 'promethium' in p:
        return 5
    return None


def tech_level(tname):
    unit = techs.get(tname, {}).get('unit') or {}
    packs = []
    for ing in unit.get('ingredients') or []:
        # Dump format is ARRAY style: ["automation-science-pack", 1]
        if isinstance(ing, list) and len(ing) >= 1:
            packs.append(ing[0])
        elif isinstance(ing, dict):
            packs.append(ing.get('name') or '')
    lvls = [l for l in (pack_level(p) for p in packs) if l]
    return max(lvls) if lvls else None


# recipe -> set of unlocking techs
recipe_techs = defaultdict(set)
for tname, t in techs.items():
    for eff in t.get('effects') or []:
        if eff.get('type') == 'unlock-recipe' and eff.get('recipe'):
            recipe_techs[eff['recipe']].add(tname)


def best_orig_tech(item):
    ot = recipe_techs.get(item)
    if not ot:
        return None
    return max(ot, key=lambda t: tech_level(t) or 0)


# 1. Version sanity
instantiated = [n for n in recipes if 'instantiated' in n and n.startswith('dmrsa-repl-')]
print(f'=== VERSION CHECK ===')
print(f'dmrsa-repl-* recipes: {len(repl)} | -instantiated leftovers: {len(instantiated)} '
      f'(0 = 3.7.1 factorissimo fix applied)')

# 2. Tier distribution
tiers = Counter(repl_tier(n, r) for n, r in repl.items() if repl_tier(n, r))
print(f'\n=== TIER DISTRIBUTION ===')
print('by tier:', dict(sorted(tiers.items())))

# 3. Category distribution
sg_counts = Counter(r.get('subgroup', '?') for r in repl.values())
print(f'\n=== CATEGORY (subgroup) DISTRIBUTION ===')
for sg, c in sorted(sg_counts.items(), key=lambda x: -x[1]):
    print(f'  {sg}: {c}')

# 4. Mismatch buckets
print(f'\n=== TIER MISMATCH vs ORIGINAL-TECH PROGRESSION ===')
mismatch = []
no_tech = []
for n, r in repl.items():
    item = n.replace('dmrsa-repl-', '')
    tier = repl_tier(n, r)
    ot = best_orig_tech(item)
    olvl = tech_level(ot) if ot else None
    if olvl and tier:
        if olvl != tier:
            mismatch.append((item, tier, olvl, ot))
    else:
        no_tech.append((item, tier))

buckets = Counter(f'{olvl}->{tier}' for _, tier, olvl, _ in mismatch)
print(f'items with mismatch: {len(mismatch)}')
print('buckets (orig_level->current_tier):', dict(sorted(buckets.items())))
print(f'items with NO original tech: {len(no_tech)}')

# 5. Endgame offenders
print(f'\n=== ENDGAME (orig lvl 5) AT TIER <=3 — the "unlock anything" offenders ===')
bad = [(i, t, o, tech) for i, t, o, tech in mismatch if o == 5 and t and t <= 3]
for i, t, o, tech in sorted(bad, key=lambda x: x[1]):
    print(f'  {i:45s} tier={t} orig_lvl={o} ({tech})')

# 6. Mirror simulation (threshold=1) with exclusions
print(f'\n=== RESEARCH-MIRROR SIMULATION (threshold=1) ===')
EXCLUDE = set()
for t in ['gun', 'armor']:
    EXCLUDE |= set(dump.get(t, {}).keys())
veh_types = ['car', 'tank', 'spider-vehicle', 'locomotive', 'cargo-wagon',
             'fluid-wagon', 'artillery-wagon']
for t in veh_types:
    EXCLUDE |= set(dump.get(t, {}).keys())
# ammo deliberately NOT excluded (user decision 2026-08-12: mass-use items replicable)

tech_groups = defaultdict(list)
no_tech_after = []
for n, r in repl.items():
    item = n.replace('dmrsa-repl-', '')
    if item in EXCLUDE:
        continue
    ot = best_orig_tech(item)
    if ot:
        tech_groups[ot].append(item)
    else:
        no_tech_after.append(item)

mirror_all = {t: items for t, items in tech_groups.items() if items}
single = {t: items for t, items in mirror_all.items() if len(items) == 1}
multi = {t: items for t, items in mirror_all.items() if len(items) >= 2}
items_in_mirror = sum(len(v) for v in mirror_all.values())
print(f'excluded (guns/armor/vehicles): {len(EXCLUDE & repl_items)}')
print(f'items with tech: {items_in_mirror}')
print(f'MIRROR techs: {len(mirror_all)} '
      f'({len(single)} single-item + {len(multi)} multi-item)')
print(f'no-tech fallback to baseline: {len(no_tech_after)}')

print('\n=== multi-item mirror examples ===')
for t, items in sorted(multi.items(), key=lambda x: -len(x[1]))[:8]:
    lvl = tech_level(t)
    print(f'  "Replication: {t}" [lvl={lvl}] -> {len(items)}: {sorted(items)[:4]}')
