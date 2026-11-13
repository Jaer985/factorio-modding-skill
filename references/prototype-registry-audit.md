# Prototype registries & data-stage audit fixes (Factorio 2.x)

Lessons from the DMR batch-3 audit (real dump 138 mods, sep-2026).
Applies to ANY mod that generates prototypes dynamically (data-final-fixes)
and audits it against a real modlist dump.

## 1. data.raw.item is not the only item registry

Factorio 2.x separates item classes into their own registries. A defensive
`data.raw.item[name]` guard misses them all:

| Registry | What it contains | Example from dump |
|---|---|---|
| `item` | generic items | fast-inserter |
| `tool` | **science packs** and tools | apicultural-science-pack, dmrsa-tenemut |
| `ammo` | ammunition | piercing-rounds (66 in dump) |
| `module` | modules | speed-module (39) |
| `capsule` | capsules | (35) |
| `movement-bonus-equipment`, `energy-shield-equipment`, `night-vision-equipment`, `generator-equipment`, ... | equippable equipment (one registry PER category) | aircraft-afterburner |

- **Typical symptom**: "142 targets with quality but no refiner recipes" — the
  narrow registry guard silently skips them.
- **Class fix**: resolve from multi-registry prototypes
  (`{item, ammo, module, capsule, tool}` in order) in a SINGLE helper and use it
  in ALL guards in the file.
- **Debugging pitfall**: if an item "does not exist" in your shard/dump, check
  which registry it falls into BEFORE concluding it does not exist. A `tool` type
  science pack does not appear in the dump's `item` section — an hour was lost on the
  mystery of "apicultural-science-pack routed to gleba with no explanation"
  when the initial check looked in the wrong drawer (and yes: it was spoilable,
  the gleba rule was correct).

## 2. Structural signals > name patterns

- `place_as_equipment_result` (in the PROTO) marks equippable equipment even when the
  name does not contain "-equipment". 4 real leaks (aircraft-afterburner,
  aircraft-energy-shield, angels-cab-energy-interface-mk1,
  manual-color-module) escaped EVERY name pattern and would escape
  any new mod with creative names. The structural guard catches them all;
  class exceptions (solar/battery) still apply.
- For planetary routing: `default_import_location` and producer
  `surface_conditions` identify planet-exclusive items EXACTLY —
  keyword heuristics from the name miss everything that does not
  match (13 items from fulgora in numeric bands).

## 3. Cross-inheritance via empty prefix

`mod_prefix(name)` returning `""` for names WITHOUT a hyphen causes TWO
items from different mods without hyphens to share a "prefix" (`sulfur` vanilla vs
`biosulfur` from Bio Ind) → the vanilla item inherits the foreign mod's tech
(gleba T5). Class fix: empty prefix ≠ match — requires a REAL shared
prefix (both with hyphen and same segment).

## 4. Your own techs enter the reverse-map

If you generate `dmrsa-replication-N` techs (one per tier) and then build
a tech→items map from ALL techs with unlock-recipe, your own
techs enter and `normalize_tech_base()` collapses the `-N` into ONE mirror
→ broken self-mirror (replicators 1/2/4/5 in a t5 tech, tier-3
hijacked by another planet's tech). Fix: filter `dmrsa%-` from the
reverse-map BEFORE filling it (blast radius = only your own items).

## 5. Anti-pattern: max-SCL-wins to choose an item's tech

Choosing the unlocking tech with the HIGHEST science level causes early
items to be gated behind endgame techs (solid-fuel →
planet-discovery-aquilo T5; lubricant/sulfur → bioflux T5). Large
modlists re-gate vanilla recipes all the time. Class fix:
manual TECH_REDIRECT per item (dump-proven) for visible cases, and a
preferential selection rule by SCL CLOSEST to the solver tier, not
the maximum.

## 6. Dynamic routing invariants

- A new `planet_suffix` must reference an EXISTING `replication-<X>`
  category and a `planetary_unlocks` dict key — assigning "space" without
  a category crashes the load. Before adding a routing branch:
  verify category + key.
- VERIFY IN THE DUMP every hardcoded tech/item name
  (TECH_REDIRECT, MOD_PACK_LEVELS, exclusions) before writing the patch.
  A non-existent name (`planetaris-gold-processing`) is an invalid prereq
  in production. A 30s query vs a mod crash.
- Dynamic level inference (unknown packs) must have a CAP:
  the max-anchor over-anchors mid-game packs to T5 via co-consumption in endgame
  techs (62 inflated mirrors in the dump). Tier 5 = only explicit tables/families.

## 7. Locale/code drift

- Setting description says "multiplier (cost × (1+pen))" while
  the code applies "additive (cost + pen)" = the player tunes with the wrong
  mental model. When changing a setting's SEMANTICS, audit its
  EN and ES description.
- Every setting needs a key in `[mod-setting-name]` AND
  `[mod-setting-description]` (the name falls to the raw key with "Unknown key"
  in the log). Count them: names == descs.
- Verify actual line-ending bytes (CRLF vs LF) before
  assuming the documented convention — the doc may be stale.

## 7. Synchronized single-source lists

When the same item set lives in multiple decisions (tier gate, hidden
filter, eligibility whitelist), declare ONE list per file and
keep them synchronized with cross-references ("mirrors X, keep in sync").
Real DMR case D17: the 6 space chunks live in `SPACE_CHUNKS`
(mirror-generator: t5+gravity0 gate), `SPACE_CHUNK_TARGETS` (target-mapper:
hidden filter) and `ELIGIBILITY_WHITELIST` (target-mapper: obtainability) —
auric/bismuth were missing from the whitelist and escaped the ENTIRE chain until
arriving by accident via a steam-recycler swallow.

## 8. Layered filter debugging

If a test check fails for an item that "should" pass, do not assume the
obvious layer (the filter you just touched) is the culprit. The exclusion
pipeline has LAYERS in order (own prefix → blacklist → eligibility
→ v4 exclusions → hidden) and the failure may be in a DIFFERENT layer than
the one edited. Real case: chunk test failed after fixing the hidden
filter; the cause was the ELIGIBILITY_WHITELIST (another layer, another block).
Method: run the item against each layer in order, do not guess.

## 9. Level spread: dynamic eligibility + membership routing

To un-collapse `-N` chains (one mirror per tech level), eligibility
is computed DYNAMICALLY from the loaded modlist (do not hardcode chains —
principle "adaptable to any modlist"). Dump-validated filters:
1. level 1 PLAIN tech exists (otherwise the mirror chain breaks contiguity);
2. contiguous levels 1..deepest;
3. deepest >= 3 (1-2 chains have no real gap);
4. each level keeps >=1 item (attribution: minimum level whose tech
   unlocks a producing recipe of the item; orphans → deepest);
5. tier span >= 2 (otherwise the split does not change gameplay, only noise).

And item routing to its level is by MEMBERSHIP (`map[item]`
pre-built), not by iterating the item's techs: iterating techs can
divert an item to the best-tech fallback and leave a level mirror EMPTY →
"Non-contiguous levels" crash. The map guarantees base + non-empty levels.
In the tier loop, per-level mirrors take the tier of their ITEMS
(cost/machine), NOT the SCL of the original tech — a level-N tech is researched
with deep packs while its items are mid-game (that is the point of the
spread).

## 10. Large rebalance = read-only simulation BEFORE touching code

For rebalances touching the entire dataset (cost rescale, global routing
change): do not implement directly. Intermediate phase: dispatch 1-2
READ-ONLY subagents that (a) design the concrete model, (b) simulate it in
Python on the dump, (c) deliver the before/after (distribution by tier,
% at edges, outliers, regressions). Present the numbers to the user →
implement only with OK. The lesson from gate test 4.2.0 (depth clamp inflated
458/474 mirrors to t5 — detected IN the dump, after implementing) is the
reason: the wrong rebalance is visible in simulation, not in code.
Simulation baseline = current code recategorized with the current rules,
not the raw dump from an old version.

## Fix workflow (validated)

1. Backup files to touch → `backups/<batch>-pre/`.
2. Dump evidence BEFORE the patch (names, flags, categories).
3. Patch → `luac5.2 -p <file>` → full suite (all 4 test files).
4. NEW regression tests for each class fix (fixture reproducing
   the leak + expected behavior check).
5. Project docs up to date (ROADMAP/AGENTS) with what was applied vs
   pending decisions — separate "bug with clear fix" from "design
   decision".
6. Global rebalance (costs/routing): READ-ONLY simulation first (see §10)
   — present with numbers to the user before the patch.
