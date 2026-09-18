# DMR v4.2 — Cost Model B2 (FINAL 2026-08-22: implemented + refined)

Design source of truth for the replication cost model. Load when touching
costs, replicator power, speed_factor, refiner energy, or any
"demasiado rápido/lento" feedback. All decisions user-approved; do not
re-litigate without data.

## ⚠️ A2 RE-SCALE (2026-09-04) — SUPERSEDES the pipeline below

Simulated first (read-only agent pass over the dump → `research/v42-audit/sim-a2-rescale.md`),
presented to the user with before/after numbers, THEN shipped as 2 commits.
If you touch costs today, THIS is the live pipeline (mirror-generator generate()):

```
solver_f = max(solver.dark_matter, 1.5×tier^1.5)      -- tier-faithful dm-floor
base_e   = min(vanilla_energy, solver_f)               -- if vanilla exists; else solver_f
            and MACHINE_MULT applies to the SOLVER term ONLY (no-vanilla path) —
            vanilla energy already contains its machine cost, never re-taxed
raw      = base_e × CT[tier] × mm [× fluid_qty] [× replic_mult]
cost     = SOFTCLAMP(raw, BAND_LO[tier]×mult, BAND_HI[tier]×mult):
           floor at LO (hard, by design — mass-use stays cheap);
           above HI → min(HI + (raw−HI)×0.3, 2×HI)     -- visible ordering up to 2×HI
cost     = max(1, ceil(cost)); difficulty cap = unreachable safety net
```

CT ladder RE-CENTERED (old {3,4,5,6,7} over-taxed t1-t2 → HI-pinned, under-taxed t3-t5):
| tier | CT (A2) | BAND_LO | BAND_HI | MACHINE_MULT (no-vanilla only) |
|-----:|---:|--------:|--------:|----:|
| 1 | 2.5 | 2.7 | 16 | 1.5 |
| 2 | 4.5 | 5.3 | 32 | 2.0 |
| 3 | 7.5 | 10.6 | 64 | 2.5 |
| 4 | 11 | 20 | 120 | 3.0 |
| 5 | 14 | 33.3 | 200 | 3.5 |

Simulated outcome (1,715 recipes): median per tier 15/32/50/30/123 → **14/23/45/55/168
(monotone)**; MJ/item p50 3/60/78/88/563 → **4/43/119/161/641 (monotone)**; band-edge
saturation 61% → **10%**; HI-pinned 661 → **2**; total energy ×1.35. Root cause that
motivated it: 60% of targets resolved the degenerate solver term dm=5.5 (cycle fallback),
so the band clamp decided everything.

Solver-side (commit-2, same date): jump-cap at `cost-solver.lua` now applies
UNCONDITIONALLY (the old `ingredient_tier > 1` bypass was the degradation mechanism —
collapsed chains absorbed the unlock tech's full tier; sim: 861/1602 tier flips without
the companion guard); `build_recipe_map` excludes `dmrsa-*` recipes (zero-ingredient
DMR recipes were fake chain terminators); branch-6 orphans get dm/time from their TIER
(1.5×t^1.5, 3.0×t/2) instead of flat 10.0/3.0; +16 MOD_ORE_TIERS family patterns
(angels ingot/powder/roll/wire→2, geode/catalyst/liquid-molten→3-4, chunks→5,
spaceship-scrap→3). Two test contracts changed DELIBERATELY (predicted by the sim,
not regressions): `mid-item` 3→2, `bob-sniper-rifle` 5→2 (see references/dmr-test-suite.md).
Test: `test_cost_bands.lua` (257 checks) pins the pure pipeline.

The B2 design philosophy below (time↔energy inverse, kW ramp, refino items, user
methodology) is STILL VALID — only the formula/CT/clamp changed.

## Formula (implemented in lib/mirror-generator.lua) — PRE-A2, historical

```
base_e = min(vanilla_energy, solver_tax)   -- if vanilla recipe exists; else solver_tax
raw    = base_e × CT[tier] × MACHINE_MULT[tier]   (machine only; else ×1)
if fluid: raw = raw × fluid_qty                    (LOT clamp — ×25 BEFORE band)
cost   = clamp(raw, BAND_LO[tier], BAND_HI[tier])  (bands FIXED, no ×machine)
```

Why `min(vanilla, solver)`: an item is never pricier than crafting it nor
than its own recipe chain. The solver's machine-efficiency flavour
(smelting 1/3 cheap) survives where the chain is cheaper than vanilla; the
dumb chain costs (plastic-bar 234s, steam 375s) die to the vanilla reference.
Power = energy per recipe (kW × real time) — that is the REAL premium: a
t5 recipe costs ~150-915 MJ, needs a big network.

Constants FINAL (after the "es muy rápido" refinement — option B):
| tier | CT | BAND_LO | BAND_HI | MACHINE_MULT |
|-----:|---:|--------:|--------:|-------------:|
| 1 | 3 | 2.7 | 16 | 1.5 |
| 2 | 4 | 5.3 | 32 | 2.0 |
| 3 | 5 | 10.6 | 64 | 2.5 |
| 4 | 6 | 20 | 120 | 3.0 |
| 5 | 7 | 33.3 | 200 | 3.5 |

All nominal seconds. **REAL time = nominal ÷ replicator `crafting_speed`** —
FINAL speeds are 1 / 1.6 / 2.56 / 4.1 / 6.55 (`replstats-speed-factor` 2.0 →
1.6). Real times across tiers: ~2.7-30.5s.

## The refinement decision (do NOT revert without data)

User flagged the FIRST B2 pass as "es muy rápido porque cada replicator
aumenta la velocidad" — real times were a uniform 1.6-12s on EVERY tier
(t5 at 16x crushed its band). Then: "si es más lento debe ser más económico
en términos energéticos". The resolved package:

1. **speed_factor 2.0 → 1.6**, bands ×1.33 → real ~2.7-30.5s (2-3x slower).
2. **kW ramp shifted DOWN to 1 / 3 / 8 / 15 / 30 MW** so ENERGY PER RECIPE
   STAYS INVARIANT (~same MJ as the 1/4/16/40/100 design) while the grid is
   more accessible (30MW at t5 instead of 100MW). Balance principle:
   time up + kW down = same energy/recipe; NEVER raise both axes together.
   The user's earlier "la energía debe ser mucho mayor" is satisfied by the
   INVARIANT level (t5 mediana ~385 MJ, up to 915) — do not re-bump kW
   without re-checking MJ/recipe.
3. Refiner own power 6MW → 4MW (same wave).
4. **Cross-tier recursive CONFIRMED already in place** (dump-verified): each
   replicator's `crafting_categories` = `replication-1..N` (t1 only tier 1,
   t5 accepts 1..5). Do NOT re-implement. Consequence shown to the user with
   the basic inserter: t5 mass-produces tier-1 items at 0.46s/13.7MJ vs
   3s/3MJ on t1 — the tier-N speed benefit is paid for in kWh (energy IS
   the brake).

## Machine layer (user: "todo ese tipo de maquinas, solar panels, steam
engine, etc")

Structural detection: precompute `machine_entities` from data.raw scanning
(a) infra prototype kinds: assembling-machine, furnace, mining-drill, lab,
centrifuge, rocket-silo, reactor, heat-exchanger, boiler, generator,
steam-engine, steam-turbine, offshore-pump, roboport, beacon, radar, turret,
artillery-turret, solar-panel, accumulator, storage-tank, pump,
electric-energy-interface, burner-generator; (b) ANY entity with
`crafting_categories` or `crafting_speed`. `is_machine(item)` = its
place_result (or itself) is in the set. Factorissimo factories are storage-
tank entities → caught automatically (dump-verified); factory-4 does not
exist in the 138-mod modlist. 371 machines flagged in the dump (108 t1 /
12 t2 / 214 t3 / 19 t4 / 18 t5).

## Power — FINAL values

- Replicators 1-5: PER_TIER_MW = {1, 3, 8, 15, 30}. replstats-energy-base/
  -factor settings are legacy (kept for save compat, unused).
- **Planetary replicators 400/800 → 40/80 MW** (vulcanus/fulgora/gleba = 40,
  aquilo = 80): the old values were tuned for the 600s era (200s × 400MW =
  80 GJ/recipe, unplayable). With the new bands the planets stay the most
  expensive machines at ~0.1-0.6 GJ/recipe. Do NOT re-bump 400/800 without
  re-checking real-time energy per recipe.
- Refiner: ENERGY_MULT = 3 (was 10), own power 4MW. Tests updated
  (test_refiner 48 checks — A4-1 added ammo/module/capsule/tool classes).

## Effects / verified numbers (dump sim, FINAL)

- Basic inserter (t1): 3s real / 3 MJ / 20 per min on replicator-1; on t5
  (cross-tier): 0.46s / 13.7 MJ / 131 per min — energy ×4.6, use as the demo.
- centrifuge 19.5s real / 156 MJ; electric-furnace 24.4s / 195 MJ;
  accumulator 20s / 60 MJ; stack-inserter 5.1s / 152 MJ; explosives 5.1s /
  152 MJ; space-science-pack 4.9s / 73 MJ.
- Mass-use t1 unchanged: transport-belt / inserter / plastic-bar ~3s,
  iron-plate 6s (never slower than the user's "objetos de uso masivo" rule).
- Median real times (PRE-A2, superseded — A2 median per tier is now monotone
  14/23/45/55/168 nominal; see the A2 section at top): t1 ~12s, t2 ~20s,
  t3 ~19.5s, t4 ~5.9s, t5 ~12.8s.
- Consumibles sin recipe (27 items, dumped): ALL legitimate — ores/minables,
  depleted fuel cells KEPT, seeds/potions KEPT, tenemut t5 intentional,
  fusion-plasma endgame. Nothing to change.
- Difficulty time caps (600/1000/1800/3200) never fire (bands ≤ 200) —
  difficulty affects research only, documented in changelog.

## Close-of-package (2026-08-22)

RESOLVED: speed, kW, refiner, planetary, cross-tier, consumables. Only
optional follow-up left: re-review the machine multiplier spread
(1.5-3.5x per tier — "¿es el spread correcto?") with real gate-test data,
and watch planetary behavior on a real gate test.

## Original-mod REFINO (2026-08-22, after studying upstream 2.0.4)

Full study: `references/dmr-original-mod-study.md` + `research/dmr-original-mod-study.md`.
User picked "haz el refino completo" — five changes, ALL implemented & tested (171 PASS):

1. **Replicators replicable**: `DMR_REPLICATOR_WHITELIST` in target-mapper
   (dmrsa-replicator-1..5 pass the gprefix exclusion) + `REPLICATOR_TIER`
   forced 1..5 in mirror-generator. The upstream declares them
   repltech_recipe(device3-5, upgrade=true) — you can duplicate your
   replicators.
2. **Ore rarity — FINAL: `mining_time × 4`** (mejora posterior: modelo COMPLETO
   del original `var("ore")(2) × (mining_time/density4 × 8) = mining_time × 4`;
   el primer refino usaba ×2, se duplicó el impacto). Dynamic minables (no
   static BASE_RESOURCE_COSTS entry) add `mining_time × 4` in
   initialize_base_resources. Density is NOT in resource protos (upstream
   passed it by hand per mod) → infer density=4. tungsten-ore (mining 5) pays
   +20, thorium (2.5) +10, common ~+4. Static vanilla entries untouched.
3. **Research WITHOUT ×item_count**: `reps_count = ceil(10×tier ×
   (diff_vals.cost/25))` — upstream charges per TECH (tier×25), not per item
   in the group. materials-1 (25 items) dropped 250 → 10 reps. Mirrors with
   item_count=1 unchanged.
4. **No "productivity" on replicators** (replicators.lua AND
   planetary-replicators.lua): 0-ingredient recipes make productivity a FREE
   duplication exploit (upstream has the hole; we closed it). Quality comes
   from the Refiner (module-less). Refiner already module_slots=0.
5. **Penalty = +0.5 FIXED SUM**, fiel al upstream: `dark_matter + penalty`,
   `time + penalty×0.5` — BOTH call sites (the memoized cache read AND the
   main solve return). It was a decaying MULTIPLIER (1+penalty/depth) that
   inflated long chains and contradicted the setting description.
6. **Difficulty now scales REPLICATION times too** — new 4th axis
   `replic_mult` in `helpers.get_research_difficulty_values()`: Easy ×1.0 /
   Medium ×1.5 / High ×2.0 / Very Hard ×3.0. In mirror-generator it
   multiplies raw AND bands (`clamp(raw×mult, lo×mult, hi×mult)` — everything
   rises, not just the raw; the difficulty cap stays as the safety net).
7. **Dead settings REMOVED from the menu** (not just marked legacy):
   `replstats-energy-base`, `replstats-energy-factor` (unused since the
   PER_TIER_MW table) and `dmrsa-cost-calculation-method` (no effect since
   the fixed penalty). Delete from settings.lua AND the name+description
   lines in locale EN+ES (3 lines × 2 sections × 2 languages — verify with a
   line-start `drop` pass, then grep the leftovers) — a setting that has no
   effect confuses players and the parity audit flags orphans.

Also: planetarios productivity removed at the same time (found by the
"allowed_effects in ALL machines" grep — the refino pass must sweep every
machine file, not just replicators.lua).

## User methodology — balance decisions are EXAMPLE-DRIVEN (2026-08-22)

The user does not accept abstract balance tables as a final answer. Every
time a model was proposed this session, they asked for tangible examples
before approving ("expandamos con ejemplos", "tomemos de ejemplo un basic
inserter", "cuanto seria el tiempo con un replicator tier 1 y replicator
tier 5"). Required presentation format for ANY balance proposal:

1. Named items with TIME AND ENERGY per item, current vs proposed
   (e.g. belt / basic inserter = mass-use tier-1 benchmark; centrifuge /
   electric-furnace = machine benchmark; space-science / stack-inserter =
   endgame benchmark). Don't show formulas alone.
2. When they ask for a concrete number ("¿cuánto tardaría en el t1 y en el
   t5?"), answer with the NUMBER per machine, not the formula. Use their
   real-time framing (÷ crafting_speed), never nominal seconds.
3. They approve in increments ("vamos con este y luego vemos") and refine
   hard after feeling it in play ("es muy rápido", "si es más lento debe
   ser más económico") — treat every model as a provisional pass, keep the
   constant tables in ONE place so a "dose" change is a one-line edit.
4. When the user asks for a feature that sounds new (cross-tier
   replication), VERIFY it isn't already implemented before planning to
   build it — check the actual machine categories in the dump first
   (cross-tier recursion existed; we nearly re-implemented it).

## Maintenance refactor (2026-08-22): data-final-fixes.lua → pass files

`data-final-fixes.lua` is now a thin ORCHESTRATOR; every PASS lives in its
own file: `prototypes/fixes/pass-generate.lua` (PASS 0: Mirror/Individual
generator + refiner + planetary attach), `pass-prereqs.lua` (PASS 1+2),
`pass-orphans.lua` (PASS 3), `pass-lab-inputs.lua` (PASS 4),
`pass-empty-categories.lua` (PASS 5). Do NOT put new PASS code inside
data-final-fixes.lua — add a file under prototypes/fixes/ and require it in
order. (PASS 6 was removed in v4.0; the comment lives in pass-generate.)

**Privacy-scan pitfall**: `check-no-private-data.py` flags the literal string
of a credential env-var NAME anywhere in the source tree — including
ROADMAP.md / docs that MERELY MENTION where the token lives. Never write a
real env-var name (nor its home path) into a
file that ships in the mod folder or gets pushed; paraphrase
("el token vive en el .env del perfil — ver skill").

**Verify lesson learned**: zip `in`-string checks gave FALSE positives for
"productivity" because the patch COMMENT contained the word. Check the
EXACT field (`grep "allowed_effects"`), not a whole-file substring.

## Dato técnico: `dmrsa-dark-matter` está HUÉRFANO (verificado en dump)

The item `dmrsa-dark-matter` (stack 1000, no fuel_category) is produced by
NOBODY (only a self-recycling recipe) and consumed by NOBODY in any recipe —
a legacy leftover. It is the natural FUEL candidate for the planned
"Reactor Chain Dark Energy" (5 tiers of reactors that burn dark matter to
feed replicator power; ROI: 1 reactor per replicator tier). The
`dark-matter-scoop`/`transducer` items are research materials only (crafted,
not machines). If a future session designs that chain, the economy must
also GIVE THE ITEM A PRODUCER (e.g. a scoop machine entity consuming
tenemut → dark matter), not just a consumer.