# DMR cost-solver test suite

Location: `~/projects/Factorio-Modding/dark-matter-replicator/dmr-tests/`
(outside the mod source dir so it never gets packaged into the zip).

## Run

```bash
cd ~/projects/Factorio-Modding/dark-matter-replicator/dmr-tests
lua5.2 run_tests.lua          # quiet
lua5.2 run_tests.lua verbose  # shows per-test + helper debug output
# Full suite (the 6 files, run all before any rebuild):
for t in run_tests test_mirror test_refiner test_step_filter \
        test_planet_routing test_cost_bands; do lua5.2 $t.lua; done
```

Requires Lua 5.2 (NOT 5.1): the cost-solver uses `goto`/`::label::` which is
Lua 5.2 syntax. Factorio 2.x embeds Lua 5.2, so this matches the game.
Install: `sudo apt-get install -y lua5.2`.

## The 6 files (as of 2026-09-04, post batch-3 + A2 + PR2)

| file | checks | covers |
|---|---|---|
| `run_tests.lua` | 54 | cost-solver: solve_cost branches, BASE_RESOURCE_COSTS, FLUID_TIER_OVERRIDES, MOD_ORE_TIERS, difficulty matrix |
| `test_mirror.lua` | 82 | TargetMapper exclusions (weapons/equipment/vequip/rpg/structural place_as_equipment_result), pack-level SCL + dynamic inference CAP=4, chunk eligibility (D17 canary) |
| `test_refiner.lua` | 48 | quality gate, per-step probabilities, 3× energy, skip rules, ammo/module classes (A4-1) |
| `test_step_filter.lua` | ~8 | hybrid step filter (bearings/projectiles/robot parts) |
| `test_planet_routing.lua` | 14 | PR-2 structural routing: producer-SC (unique/guarded), DIL (DMR-planets only), steam-shape rejection, ceiling-skip, keyword fallback, spoil (synthetic 4-planet data.raw) |
| `test_cost_bands.lua` | 257 | A2 commit-1 pipeline PURE: CT ladder, dm-floor, mm-on-solver-only, soft-clamp shape, band invariants, floor-rider class, difficulty matrix, median-lands-~40% sanity |

## Deliberate contract changes (A2 commit-2, 2026-09-04 — NOT regressions)

The jump-cap now applies UNCONDITIONALLY (the old "skip cap when
ingredient_tier==1" relaxation was the degradation mechanism — collapsed
chains absorbed the unlock tech's full tier). Two asserts were updated to
the new contract (both predicted by `sim-a2-rescale.md` §4b):
- `solve_cost("mid-item")` → **2** (was 3): min(tech 3, ingredient 1 + 1) = 2.
- `solve_cost("bob-sniper-rifle")` → **2** (was 5): simple-ingredient item
  sits at ingredient_tier+1; weapon exclusivity is target-mapper's job.

If a future change re-surfaces these to 3/5, that is a REVERT of the A2
design — check with the user before accepting.

## What it tests

Cost-solver layer only (solve_cost + BASE_RESOURCE_COSTS + FLUID_TIER_OVERRIDES
+ get_tier_from_tech). The final replication tier also depends on
dynamic-generator.lua's category floors / science override / planetary
routing, which are not unit-testable without the full prototype env — those
are covered by the receipt scripts in the release flow.

Current coverage (fixtures reproduce real bugs from the release cycle):
- fusion-plasma → tier 5 (FLUID_TIER_OVERRIDES, v3.5.9)
- promethium-asteroid-chunk → tier 5 (BASE_RESOURCE_COSTS, v3.5.9)
- carbonic-asteroid-chunk → tier 4 (name fix, v3.5.13)
- scrap → tier 1 (BASE_RESOURCE_COSTS; planetary routing in dynamic-generator)
- iron-plate → tier 1 (smelting chain)
- chemical-science-pack → tier 3 (recipe chain + tech mapping, v3.5.17/19)
- cyclic-a/b → resolves without crash (cycle fallback, v3.5.11)
- mid-item → tier 2 (A2 commit-2 unconditional jump-cap; was 3 via relaxation)
- bob-sniper-rifle → tier 2 (same; was 5)
- A2 commit-2 additions: angels-ingot-copper→2, angels-roll-steel→2,
  angels-geode-blue→3, angels-catalyst-metal-green→3, spaceship-scrap→3,
  auric-asteroid-chunk→5 (MOD_ORE_TIERS family floors)

## Key harness detail

Factorio auto-assigns `prototype.name = <table key>` for every prototype.
`test_harness.lua` `load_recipe/load_tech/...` functions replicate this by
setting `proto.name = proto.name or name`. Without this, code reading
`recipe.name` (e.g. `recipe_tech_map[recipe.name]` in solve_cost) gets nil
and the tech-tier mapping silently no-ops. This tripped the initial test run.

## Adding a test

1. Add fixtures in `fixtures_recipes.lua` (load_recipe/load_tech/load_resource/load_fluid).
2. Add asserts in `run_tests.lua` using `assert_tier(name, expected_tier, label)`
   or custom logic with `harness.stats.passed/failed` + `harness.stats.failures`.
3. Remember: get_tier_from_tech expects the TECH OBJECT, not the name string.
