# DMR v4 — Tier/progression redesign analysis (2026-08-13)

Context: user reported "basic, shape, alloy... no está funcionando, al final
puedo desbloquear cualquier cosa" — the category/tier system isn't gating
progression. Verified against the 3.7.1 data-raw-dump.json (NOT guessed).

## Diagnosis (dump-driven)

- 945 `dmrsa-repl-*` recipes; **46% (440) in `general`** category (fallback, NO
  tier floor) → the cost-solver decides their tier entirely.
- **503 items whose tier mismatches their original tech's science level.**
  Buckets (orig_level→current_tier): 3→4 (175), 3→5 (99), 1→4 (13), 1→5 (21),
  1→2 (115), 5→3 (14), 5→4 (11).
- The "unlock anything" offenders — endgame items at tier 3-4:
  requester/buffer/active-provider-chest (logistic-system), energy-shield-mk2,
  lightning-rod, aai-warehouse-*, nuclear-fuel, artillery-turret, mech-armor,
  tesla-ammo.
- **Root cause**: the cost-solver tiers by INGREDIENT CHAIN, which is NOT a
  progression signal with overhaul mods. The correct signal is the item's
  ORIGINAL tech science-pack level: automation/logistic=1, military=2,
  chemical/prod/utility=3, planetary=4, space/cryo/promethium=5.
- Dump JSON `unit.ingredients` format is `["pack-name", amount]` (array), NOT
  `{name=..., amount=...}` dict — parse both shapes defensively.

## v4 design direction (user-approved; NOT yet implemented)

> ⚠️ **USER-CORRECTED 2026-08-12** — read this before implementing. The
> canonical, consolidated decision record lives in
> `references/dmr-tier-gating-redesign.md` (DECISION section). The bullets
> below are the corrected direction; earlier drafts saying "every item gets
> its own repl tech" or excluding ammo are SUPERSEDED.

- **Research Mirror, threshold=1**: every ORIGINAL tech gets its own
  "Replication: <tech>" tech — even single-item techs (383 of 513 are
  single-item). The user's "tiene que ser individual / umbral a partir de uno"
  means MIRROR with threshold=1 ("cada tech permite investigar esa misma tech
  en replication"), NOT the existing per-item Individual Technologies mode.
  He corrected this twice — do not re-interpret.
- **Tier = science level of original tech** (not cost-solver). Fixes the 25+
  endgame offenders automatically; also deflates 3→4/3→5 over-inflation.
- **Catalog exclusions (user-confirmed)**: guns (11), armor (10), combat
  capsules (10), vehicles/rolling stock (27) = **58 removed**. **AMMO KEPT
  (55)** — user: mass-use items (aliens) must stay replicable. Rationale for
  the rest: weapons/armor are one-time production items, not production
  materials. Open candidates still being weighed: personal equipment (~55,
  `*-equipment` non-vehicle), vehicle equipment (50, `bob-vehicle-*`), fuel
  cells (10), seeds (3), raw-fish.
- Simulation numbers (threshold=1 mirror): v2 with ammo KEPT = 58 excluded →
  797 with tech → **513 mirror techs** (383 single + 130 multi) + 90 no-tech
  baseline. (v1 with ammo excluded = 472/743/89 — superseded.)
- Items WITHOUT an original tech (90: ores, vanilla basics like iron-plate,
  wood) → baseline tier fallback + category as floor (keeps MOD_ORE_TIERS /
  BASE_RESOURCE_COSTS working). Baseline attachment MUST add the original-tech
  prereq (PASS 6 gap — see dmr-tier-gating-redesign.md CRITICAL finding).
- Categories (shape/alloy/chemical/...) become **visual subgroups only**, no
  gating. The menu organization stays; the gate moves to the original tech.
- **Prereq**: original tech + tier machine (double gate), behind a future
  setting "investigar el objeto propio para replicarse" (require-original-tech
  ON/OFF). The mechanic already exists in dynamic-generator.lua section B.
- **Compatible with any mod**: no manual per-mod tables. Any mod that defines
  unlock-recipe tech effects gates its items automatically; unknown custom
  science packs (bob-science-pack-gold, bob-alien-science-pack-*) map via a
  short equivalence table → tier 5.

## Workflow decisions (user preference — respect this)

- The redesign is a candidate **NEXT major version (4.x)**, NOT a change to 3.7.x.
- **3.7.1 stays intact** (portal + local + GitHub commit f72f0ae + zip).
- **Backup created**: `backups/dark-matter-replicators-reborn_3.7.1-source-backup.tar.gz`
  in the project root (verified: info.json=3.7.1, changelog 3.7.1 present).
  Revert = `tar xzf backups/dark-matter-replicators-reborn_3.7.1-source-backup.tar.gz`.
- User rule: before a major redesign, keep the current version untouched and
  create a revert backup; only modify the original after confirmation. Ask
  before touching the published version.

## Analysis pitfalls (fresh this session)

- **Python regex is NOT Lua regex**: `%-` is Lua's literal-hyphen escape; in
  Python `%-` matches a literal `%` then `-` → silently matches NOTHING. Use
  `-` (or `\-`). This silently produced empty results mid-analysis.
- **Script filename `types.py` shadows stdlib `types`** → `import json` fails
  with "partially initialized module 'json'... circular import". Rename the
  analysis script (e.g. item_types_analysis.py).
- Filter `None` tiers before `Counter`/`sorted` — recipes routed to planetary
  categories have no numeric tier and crash comparisons.
- When an item is unlocked by 2+ techs (19 recipes in the dump, e.g.
  iron-stick, copper-cable), pick the tech with the HIGHEST science level
  (`max(techs, key=tech_level)`), not the first found.
- When scanning a mod zip for prototype definitions, remember Lua `%-` vs
  Python `-` applies to ANY regex over mod source (see the Bob's audit traps
  in SKILL.md).
