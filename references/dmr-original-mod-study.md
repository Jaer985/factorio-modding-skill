# DMR Original Mod Study — dark-matter-replicators-space-age 2.0.4 (nihilistzsche fork)

Source: `archivados/dark-matter-replicators-space-age_2.0.4.zip` (extractable with Python; no `unzip` in the sandbox).
Complete study 2026-08-22 → long report in `research/dmr-original-mod-study.md`. This summarizes what you need to remember:

## The original model (what "they do")
- **Declarative costs per mod**: `replications/<mod>.lua` (vanilla 226 lines, bob 617, yuoki 151...) with `repltech_recipe/item/item_table/ore/raw/element` + `replvar(name, cost)`.
- **Cost = ingredient chain + machine charge**: cost part `{type="recipe"}` decomposes the recipe into Σ replicable ingredients + var(category)×(energy_required−0.5). Category vars = kW/speed/270 of the real machine: `""`=56/90 (AM3), smelting=1/3, oil-processing=14/9, chemistry=56/90, centrifuging=140/81, rocket-building=25/27. Bob REDEFINES them (more efficient machines → lower costs).
- **Ores**: cost = var("ore")×mining_time/base_density×8 (rare = expensive; thorium 2.5/0.9 giant; Bob gems var 200).
- **Tiers per category**: ore=1, element=2 (research×0.5), shape=2, alloy=3, chemical=3, device2..5=2..5, life=5, module=5 (-1 → 4), science=manual.
- **Research**: count = tier×25 (t1/t5 ×2), time=5, packs DMR per tier (tenemut/scoop/transducer/conduit), no item_count.
- **Machines**: speed 2^(t−1) (1..16x), energy 256kW×2.5^(t−1) (256kW..10MW) — energy_factor > speed_factor → higher tiers LESS efficient. Cross-tier recursive (categories = 1..tier). Allowed modules: +speed/+consumption/+productivity/+quality/+pollution. Space-lock setting (default 6=off).
- **Prereqs**: tech of the tier + (recipe ingredients → their repltechs) + the ORIGINAL TECH (when recipe not enabled) + redundancy pruning + splice of disabled categories.
- **Original science packs**: automation 3, logistic 4, military 4, chemical 4, production 5, utility 5, space 5; SA all device5.
- **SA: ALL device5** (foundry, biochamber, mech-armor, fusion-reactor-equipment, planet ores tier 5). There are no planet ores in the original.
- **Exclusions**: replvar(name) without cost = exclusion (bob 44: bearings/roboport-parts/projectiles/warheads; angel 14: gas-*, nitric-acid...).
- **Replicators 1-5 and DMR items ARE REPLICATED** (replicator-N device3-5 upgrade=true, tenemut t1, scoop t2, transducer t3, conduit t4).
- **replication-penalty**: +0.5 FIXED per item (additive) — in our fork it multiplies (1+penalty) — DIFFERENT semantics, documented in audit-and-release.

## Divergences with our v4.2
Status 2026-08-22 (the complete refinement took the 5 implementable ones; the remaining 3 are still "don't touch without asking"):
- ✅ OWN REPLICATORS: original replicates them → IMPLEMENTED (whitelist + forced tier, see Refinement).
- ✅ RESEARCH: original NOT × item_count → IMPLEMENTED (10×tier fixed).
- ✅ RARE ORES: cost by rarity → IMPLEMENTED (mining_time×2 in dynamic ones).
- ✅ PRODUCTIVITY in replicators: removed (upstream exploit fixed).
- ✅ PENALTY: +0.5 additive, faithful to original.
- ⏸️ Personal equipment: original replicates mech-armor/fusion-reactor-equipment (device5); we exclude it (v4.0 user) — DON'T touch without asking.
- ⏸️ Planet science: original tier 5; we're t4 (B4) — DON'T touch without asking.
- ⏸️ Modules: original -1 in 4, 2/3 in 5; we're basic tier 3 — DON'T touch without asking.

## Refinement IMPLEMENTED (2026-08-22, user: "do the complete refinement")

After presenting the study divergences, the user took all 5. Reusable implementation patterns:

1. **Replicable DMR replicators** — "whitelist + forced tier" pattern (like tenemut/gems):
   - `target-mapper.lua`: `DMR_REPLICATOR_WHITELIST = {dmrsa-replicator-1..5}` and the gprefix filter exception (`and name ~= gprefix.."tenemut" and not DMR_REPLICATOR_WHITELIST[name]`).
   - `mirror-generator.lua`: `REPLICATOR_TIER = {replicator-1=1, ..., replicator-5=5}` applied over `local tier = solved.tier or 1` — each replicator falls into its own mirror tech (faithful to the `repltech_recipe(device3-5, upgrade=true)` of the original).
2. **Ore rarity** — in `CostSolver.initialize_base_resources()` (dynamic mineables block): `base_cost = base_cost + (res.minable.mining_time or 0.75) * 2` — mods with slow mining ores (tungsten 5 → +10) pay more than common ones even without a tier increase. ONLY affects mineables without a static entry in BASE_RESOURCE_COSTS; vanilla stays intact.
3. **Research without ×item_count** — `mirror-generator.lua` reps: `math.ceil(repetitions * (diff_vals.cost / 25))` (10×tier fixed; the original charges by TECH tier×25). materials-1 went from 250 → 10 reps.
4. **Remove "productivity"** from `allowed_effects` in replicators — with 0-ingredient recipes productivity is free duplication (upstream exploit). Quality comes from the Refiner (no modules).
5. **Penalty = +0.5 FIXED (additive)** — in `solve_cost` the cached branch: `dark_matter = cached.dark_matter + penalty; time = cached.time + penalty*0.5` — replaces the decaying multiplier (1+penalty/depth) that inflated long chains and contradicted the "added to the cost" description. Note: the `dmrsa-cost-calculation-method` setting ended up with NO EFFECT (both branches add) — documented in changelog.

## Workflow lesson (2026-08-22)

During the B2 package implementation the user sent an out-of-band "Wait" to realign the complete package (recapitulated point by point, then confirmed "take the b"). Lesson: in active DESIGN sessions (balance formulas + interactive decision), before launching patches you must confirm the COMPLETE PACKAGE in a single recap — the user explicitly expects it ("let's expand with examples", "let's verify before modifying something"). A half-accepted patch does NOT mean the next one in the batch is approved: each new decision (cross-tier, kW table, speed dosage) requires its own confirmation with data (options table + concrete cases, e.g. the basic inserter).

## Fresh pitfalls (this pass)
- The original zip can't be opened with `unzip` in the sandbox (not installed) — use `execute_code` with zipfile.
- `replvar("gem-ore", 200)` — Bob gems = enormous variable cost, not a tier entry.
- The comment in bob.lua justifying costs: "more efficient machines → replication costs reduced" — the conceptual justification for MACHINE_EFFICIENCY.
- The `Ingredient_count = -0` — 0-ingredient recipes (lore: "haha no ingredients").