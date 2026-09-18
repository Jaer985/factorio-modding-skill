# DMR Tier/Category Gating — Diagnosis & Redesign Brainstorm (2026-08-12)

## User report (verbatim trigger)
"lo de basic, shape, alloy, etc... no esta funcionando al final puedo desbloquear
cualquier cosa" — the categories don't gate progression; at endgame everything
is unlockable. User asked for brainstorming on tier-based (or improved) gating.

## How the system works TODAY (verified from source 2026-08-12)
- `CostSolver.solve_cost()` computes tier from the ingredient chain (depth/cost).
- `get_item_category()` (dynamic-generator.lua) classifies each item into:
  ore(1) / element(2) / shape(2) / alloy(3) / chemical(3) / organic(3) /
  military(3) / military-advanced(5) / module(3) / module-advanced(4) / life(5) /
  exotic(5) / magic(5) / alien(5) / science(dynamic) / general(dynamic).
- **Category tier is a FLOOR ONLY**: `if tier < category_def.tier then tier = category_def.tier end`.
  The cost-solver can always push HIGHER. `general` and `science` have `tier = nil` → cost-solver decides.
- Science packs: tier FORCED by name pattern (absolute, not floor) — see science-pack
  progression in the main skill.
- Individual tech prereqs: base machine (`replication-N`) + original item tech
  (via recipe_tech_map, PASS 6 re-attach).
- Grouped tech prereqs: base machine + **previous-tier-same-category group (ONLY
  if that group exists)** + original techs. If no group exists in the previous
  tier for that category, the chain collapses to machine-only.

## Dump-verified numbers (978 dmrsa-repl-* recipes, data-raw-dump.json 2026-08-11)
```
By tier:  T1=206, T2=55, T3=478 (49%!), T4=79, T5=110
By subgroup (category):
  general=453 (46%), ore=196, military=77, resources=50, chemical=47,
  shape=40, module=27, element=24, alloy=20, science=16, tier-5=15,
  exotic=7, tier-3=5, alien=1
Tier-1 sample: wood, coal, stone, iron-ore, copper-ore, electronic-circuit,
  wooden-chest, stone-furnace, burner-mining-drill, electric-mining-drill,
  burner-inserter, inserter, fast-inserter, offshore-pump, boiler
```

## Root causes (why categories "don't work")
1. **Category = floor only, not structure.** 46% land in `general` (no floor)
   → cost-solver dominates tier assignment for nearly half the modlist.
2. **Cost-solver underestimates mid-game items** (shallow ingredient chains):
   electronic-circuit, fast-inserter, engine-unit, assembling-machine-1 all sink
   to tier 1 → replicable from the Simple Replicator (needs only `electronics`).
3. **Grouped-tech progression chain is inconsistent**: "Shape Tier 3" requires
   "Shape Tier 2" only if such a group happens to exist; broken chains collapse
   to machine-only prereq → every category of the same tier opens together once
   the machine is unlocked.
4. **The best signal isn't used for tiering**: the item's ORIGINAL unlock tech
   (→ its science packs) is the truest measure of progression, but today it only
   becomes a PREREQ, never the tier source.

## Brainstorm directions (user asked; NOT yet implemented — design discussion)
- **A. Tier from ORIGINAL TECH**: tier = f(science packs of the unlock tech):
  automation/logistic=1, military=2, chemical/prod/utility=3, planetary=4,
  space/cryo/promethium=5. Cost-solver only computes costs (DM/time), never
  tiers. "No replicas lo que no sabes fabricar" holds naturally.
- **B. Fixed ABSOLUTE category tiers** (fork-original style): shape=2, alloy=3,
  chemical=3, module=3... eliminate `general` by splitting into more categories.
  Simple/predictable; requires pattern work for the 46% `general` bucket.
- **C. Hybrid (recommended / plan B)**: `tier = max(tier_original_tech, tier_category)`;
  no original tech → fallback to category/cost-solver. Uses the most reliable
  signal with the category floor as safety net.
- **D. Pure tier** (user's own lean): one grouped tech per TIER ("Replication
  Tier 3" unlocks everything tier 3); no category gating. Minimal tree, but
  loses per-category granularity.

## "Outside the box" directions (user asked for beyond C; NOT implemented)

- **E. Sample-based replication** (runtime, biggest change): the replicator
  needs ONE physical sample of the item before it can replicate it (learned per
  replicator/network, like asteroid research). Kills the problem at the root —
  impossible to unlock what you never obtained/crafted. Requires `control.lua`
  (on_player_crafted_item / on_entity_died), per-save persistence, and a
  paradigm shift from "replicate without crafting".
- **F. Mirror tree** (data-stage): generate techs that replicate WHOLE original
  techs ("Replication: Logistic System" unlocks every item that tech unlocks).
  Zero manual categories, zero `general`; natural progression (can't replicate
  what you haven't researched). Risk: one tech unlocks many items → overpowered;
  needs per-item cost balancing.
- **G. Machine as physical barrier** (data-stage): replicator tier N can only
  craft items up to N complexity (ingredient count, fluids, planets) — like
  assembling-machine ingredient limits. No giant tech tree, hard to break; but
  loses research-as-gate and needs capacity design per tier.

## Dump-verified audit technique (v3.7.1, 945 recipes) — repl-tier vs original tech

The cost-solver's ingredient-chain tier is NOT a reliable progression signal.
Cross-check every `dmrsa-repl-*` recipe's assigned tier against the item's
ORIGINAL unlock tech's highest science pack (the reliable signal):

1. `tech_level[t]` = max pack level over `t.unit.ingredients` — dump format is
   `["pack-name", 1]` LISTS, not dicts (guard both shapes).
2. `recipe_orig_tech[r]` = tech whose `effects` contain `unlock-recipe` for r.
3. For each `dmrsa-repl-<item>`: tier from its recipe-category
   (`replication-(\d+)$`); orig_lvl = tech_level[recipe_orig_tech[item]].
4. Bucket mismatches as `"{orig_lvl}->{tier}"`.

Pack-level mapping: `advanced-logistic`→3 (match BEFORE plain `logistic`),
automation/logistic→1, military→2, chemical/production/utility→3,
metallurgic/electromagnetic/agricultural→4, space/cryogenic/promethium→5.

### Results on 3.7.1 dump (945 recipes, 0 factorissimo-instantiated ✓)
```
By tier: T1=74, T2=159, T3=208, T4=216, T5=238   (better than 3.7.0's 206/55/478/79/110)
Mismatches vs original tech: 503/945
  buckets: 1->2 (115), 1->3 (36), 1->4 (13), 1->5 (21), 2->3 (13), 2->5 (6),
           3->4 (175), 3->5 (99), 5->3 (14), 5->4 (11)
```
- Cost-solver INFLATES chemical-tier items to 4-5 (`3->4`/`3->5` = 274).
- **Endgame DOWNGRADED to tier 3-4** (`5->3`/`5->4` = 25) — the literal
  "puedo desbloquear cualquier cosa" symptom. Offenders:
  `active-provider-chest`, `requester-chest`, `buffer-chest` (logistic-system),
  `energy-shield-mk2-equipment`, `lightning-rod` (fulgora discovery),
  `aai-warehouse-*`/`aai-strongbox-*`/`aai-storehouse-*` (aai-logistic);
  tier 4→5: `nuclear-fuel` (kovarex), `artillery-turret`/`artillery-wagon`,
  `mech-armor`, `tesla-ammo`/`teslagun`, `thruster`.
- `general` still 440 (46%); 196 items have NO original tech (ores, SA
  chunks/plants, mod equipment) — 103 of those sit at tier>=3.

### Simulation pitfall (IMPORTANT)
Simulating `new_tier = orig_lvl` over the dump: `recipe_orig_tech` is a dict
keyed by recipe; when MULTIPLE techs unlock the same recipe (common with Bob's,
e.g. `explosives`), the dict OVERWRITES and `pairs()` iteration order is
non-deterministic → the "tier DOWN" side of the simulation is noisy
(`explosives 5->1`, `bob-ruby-5 5->1` are artifacts). The "tier UP" side
(endgame items sitting too low) is solid because those items have ONE clear
unlock tech. Always sanity-check DOWN-side results before trusting them.

## DECISION (2026-08-13, user chose) — Research Mirror (B/F), threshold = 1

- **Chosen: Research Mirror** — one replication tech per ORIGINAL tech; tier =
  science level of that original tech; original tech always a prereq. The
  game's tech tree IS the replication tree. Rationale (user): "no se desbloquea
  todo a la vez" and it stays compatible with ANY mod — zero per-mod tables
  (mod's core philosophy; any mod's techs auto-mirror).
- **Threshold = 1 (user correction, 2026-08-12)**: EVERY original tech gets a
  mirror tech, even single-item techs. The user said "individual" twice and
  meant THIS — mirror with threshold=1 ("cada tech permite investigar esa misma
  tech en replication"), NOT the existing per-item "Individual Technologies"
  mode. Do not re-interpret: threshold=1 mirror, never per-item techs.
- **Tier of each mirror = science level of its original tech** (NOT cost-solver).
- **Prereq**: original tech + tier machine (double gate), behind a future
  setting "investigar el objeto propio para replicarse" (require-original-tech
  ON/OFF). Mechanic already exists in dynamic-generator.lua section B; 4.x
  makes it a setting + respects it in PASS 6.
- **Grouped-by-category techs REMOVED**; categories remain only as visual
  subgroups, no longer gate.
- **Exclusions (user-confirmed)**: guns (11), armor (10), combat capsules (10),
  vehicles (27) = **58 items**. **AMMO KEPT (55)** — user: "objetos de uso
  masivo deben poderse replicar" (used vs aliens). Open candidates still being
  weighed: personal equipment (~55, `*-equipment` non-vehicle), vehicle
  equipment (50, `bob-vehicle-*`), fuel cells (10), seeds (3), raw-fish.
- **Deferred as future setting**: sample-based replication (E) — expose later
  via `dmrsa-replication-mode` (values e.g. `Research Mirror` / `Sample-Based`
  / `Individual` / `Grouped Categories` legacy). Sample-based is runtime
  (`control.lua`), the rest are data-stage.
- **Plan B**: hybrid C (`max(orig-tech level, category floor)`).
- **Revert safety ("punto y aparte" = BACKUP, not a git fork)**: 3.7.1 source
  backup at `backups/dark-matter-replicators-reborn_3.7.1-source-backup.tar.gz`
  (verified info.json 3.7.1); zip `dark-matter-replicators-reborn_3.7.1.zip`;
  GitHub `f72f0ae`. Revert: `tar xzf backups/...`. User correction: when he
  says "hacerlo punto y aparte / un fork" about the redesign he means leave a
  revertible backup, NOT create a git branch/repo.
- **User workflow preference**: "expandamos, y verifiquemos antes de hacer
  alguna modificación" — explore ideas AND verify against the real dump BEFORE
  touching code. Never jump to implementation from a brainstorm. When he
  references a brainstorm option letter, re-read the full decision thread; he
  corrected interpretations twice this session ("me refiero al umbral", "no me
  estás entendiendo") — confirm with a structured recap before implementing.

## B refined design — dump-verified numbers (3.7.1, 945 recipes)

- Mirror threshold=1 WITH exclusions v2 (ammo KEPT): **513 mirror techs**
  (383 single-item + 130 multi-item) covering 797 items; **90 no-tech items**
  fall to baseline. (With ammo excluded: 472 mirror techs / 743 items / 89
  baseline — the v2 numbers are the current decision.)
- Multi-item mirror examples: "Replication: steam-power" [9], "Replication:
  bob-alien-research" [9], "Replication: ducts" [8], "Replication:
  circuit-network" [7], "Replication: artillery" → artillery-shell + turret.
- ⚠️ Baseline items STILL need their original-tech prereq attached (see CRITICAL
  finding below) or the baseline becomes the new "desbloquear cualquier cosa".
- **Universal rule (mod-agnostic)**: every item's tier = science level of its
  original tech (if one exists); prereq original-tech added ALWAYS, whether the
  item lands in a mirror tech or baseline. Custom-pack equivalence table for
  known mod packs (`bob-science-pack-gold`, `bob-alien-science-pack-*` → 5);
  unknown packs → fallback to cost-solver/category. No-tech items (93) stay on
  baseline tier + category floor. Categories become visual subgroups only
  (no gating).

## CRITICAL finding: baseline unlocks LOSE the original-tech gate

PASS 6 (re-attach) only covers individual (`dmrsa-tech-repl-*`) and grouped
(`dmrsa-grouped-repl-*`) techs. Items attached to the baseline machine techs
(`dmrsa-replication-N` in technologies.lua) do NOT get their original tech as
a prereq → machine-only gating for every baseline item. Any redesign must fix
this (add original-tech prereq to baseline attachments too), or the baseline
becomes the new "desbloquear cualquier cosa" hole.

## Reusable analysis
`scripts/dmr_tier_distribution.py <data-raw-dump.json> [--sample N]` — prints
the tier/category distribution of all dmrsa-repl-* recipes in a dump. Run this
BEFORE any tier-redesign work to see the real distribution for the installed
modlist (the dump reflects the INSTALLED mod version, not local source).

## Pitfall hit while analyzing (Python regex, again)
`%-` is Lua's literal-hyphen escape; in Python regex it matches a literal `%`
followed by `-` → silently matches NOTHING. When porting Lua pattern snippets
to Python, replace `%-` with plain `-` BEFORE running. This bit twice despite
being documented — prefer running `scripts/dmr_tier_distribution.py` over
hand-writing the scan each time.

## More analysis pitfalls (2026-08-12 session)
- **Script filename `types.py` collides with the Python stdlib `types` module**
  → circular-import crash (`json has no attribute load`). Rename any analysis
  script that shadows a stdlib module name.
- **Personal equipment has NO `equipment_category` field in the dump** — detect
  by name suffix `-equipment` (excluding `bob-vehicle-*`) and by registry type
  (`energy-shield-equipment`, `battery-equipment`, `roboport-equipment`,
  `generator-equipment`, `movement-bonus-equipment`, `solar-panel-equipment`).
  Do NOT use `equipment_grid` as a personal-equipment signal — vehicles
  (car/tank/wagons/spidertron) also have grids.
- Mirror tech tier can be None (e.g. bob-tungsten-processing items have no
  numeric replication category) — guard every max()/sorted() on tiers.
- `recipe_orig_tech` (recipe→tech dict) OVERWRITES when multiple techs unlock
  the same recipe; iterate deterministically and prefer the max science level
  (see the Simulation pitfall above).
