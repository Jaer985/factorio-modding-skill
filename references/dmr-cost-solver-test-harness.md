# Cost-solver unit-test harness — design (backlog #6, started 2026-08-09)

> **⚠️ SUPERSEDED by `references/dmr-test-suite.md` (the suite is BUILT and
> PASSING 9/9).** This file preserves the ORIGINAL design for historical
> context, but several decisions changed during implementation — read
> `dmr-test-suite.md` for the current truth:
> - **lua5.1 → lua5.2**: Factorio 2.x embeds Lua 5.2 (cost-solver uses
>   `goto`/`::label::`, 5.2 syntax). Run with `lua5.2`.
> - **`tests/` in repo → `dmr-tests/` OUTSIDE the mod source dir**: the suite
>   must never be packaged into the release zip (user requirement).
> - **"tests NOT yet written" → written and passing**: fixtures + asserts in
>   `dmr-tests/` (`test_harness.lua`, `fixtures_recipes.lua`, `run_tests.lua`).
> - The `prototype.name = <table key>` auto-assignment detail (Factorio sets
>   it; the harness replicates it) was a key implementation discovery — see
>   `dmr-test-suite.md`.

_Historical design (kept for reference — assumptions below may be stale):_

_State: lua5.1 INSTALLED and verified (`sudo apt-get install -y lua5.1` →
`/usr/bin/lua5.1`). Harness design agreed with user (route = "vamos con #6").
Tests NOT yet written — this reference preserves the design so the next
session can write `run_tests.lua` without re-deriving it._

## Why this exists

The tier-classification bugs of the v3.5.8–v3.5.20 cycle (chemical-science-pack
pushed to tier 5 by its recipe chain, promethium-asteroid-chunk falling to
tier 1, carbonic vs carbonaceous name drift, scrap not routing to Fulgora,
Bob's items polluting Tier 1 grouped techs) would ALL have been caught by a
unit test with mock recipes. `lib/cost-solver.lua` is pure Lua — it does NOT
require Factorio. It only reads:
- global `data.raw.recipe` / `data.raw.technology` (via `build_recipe_map` /
  `build_tech_map`)
- global `settings.startup[...]` (via `helpers.get_startup_setting`)
- `helpers.item_exists`, `helpers.info/debug/warn` (log stubs)

So it can be loaded under stock `lua5.1` with a mock harness. Factorio embeds
Lua 5.1, so using lua5.1 (not 5.2/5.3/5.4) keeps semantics faithful.

## Files to create (in the mod repo, `tests/`)

1. `tests/test_harness.lua` — mocks before loading the real modules:
   ```lua
   -- Must run BEFORE require("lib.cost-solver")
   data = { raw = { recipe = {}, technology = {} } }
   settings = { startup = { ["dmrsa-use-machine-efficiency"] = { value = false },
                            ["dmrsa-cost-calculation-method"] = { value = "Raw Ingredients (Flat)" },
                            ["replication-penalty"] = { value = 0.5 } } }
   -- stub helpers.log family to no-ops (helpers.lua calls them at load/build time)
   -- then:
   package.path = "lib/?.lua;" .. package.path
   require("lib.helpers")
   require("lib.repltypes")
   local CostSolver = require("lib.cost-solver")
   ```
   NOTE: cost-solver.lua may call helpers functions at module load (e.g.
   dynamic resource mapping in build_recipe_map). Stub helpers BEFORE loading
   cost-solver, or provide a real minimal `helpers` table and let the real
   helpers.lua override it.

2. `tests/fixtures_recipes.lua` — mock recipes covering every historical bug:
   - `iron-plate`: smelting recipe, ingredient iron-ore (resource) → tier 1
   - `chemical-science-pack`: recipe with advanced-circuit + engine-unit +
     sulfur → cost-solver pushes tier 4-5; assert FORCED tier 3 via name
     override (the v3.5.19 rule lives in dynamic-generator, so the unit test
     should assert `solve_cost` tier AND document that the force-down happens
     in the generator, not the solver)
   - `promethium-asteroid-chunk`: no recipe (mined) → must map to tier 5
     (BASE_RESOURCE_COSTS entry)
   - `fusion-plasma`: fluid with no recipe → FLUID_TIER_OVERRIDES tier 5
   - `carbonic-asteroid-chunk`: resource tier 4 (name-drift regression guard)
   - `scrap`: resource → BASE_RESOURCE_COSTS tier 1, but planetary routing to
     fulgora happens in dynamic-generator (assert solver tier only, document
     the split)
   - cycle pair `a` ↔ `b` (each recipe needs the other) → fallback must use
     `recipe_tech_map` tech tier, NOT hardcoded 1 (v3.5.11 regression guard)
   - Bob's-like item: mid-game ingredients, cyclic → assert not tier 1

3. `tests/run_tests.lua` — plain assert-based runner (no busted dependency):
   ```lua
   local pass, fail = 0, 0
   local function check(cond, label)
       if cond then pass = pass + 1 else fail = fail + 1
           print("FAIL: " .. label) end
   end
   -- build maps, call CostSolver.solve_cost(name), check tier/cost
   print(("PASS %d FAIL %d"):format(pass, fail))
   os.exit(fail == 0 and 0 or 1)
   ```
   Run with `lua5.1 tests/run_tests.lua`.

## Key assertion targets (tier table from v3.5.17/19)

| Item | Expected solve_cost tier | Notes |
|---|---|---|
| iron-plate | 1 | smelting chain |
| chemical-science-pack | 3 (forced by name in generator; solver may say 4-5) | assert BOTH |
| promethium-asteroid-chunk | 5 | no recipe |
| fusion-plasma | 5 | fluid override |
| carbonic-asteroid-chunk | 4 | name-drift guard |
| scrap | 1 (solver) | fulgora routing is generator-side |
| cyclic a↔b | ≥ tech tier | v3.5.11 guard |

## Pitfall to remember

- `solve_cost` caches (solved_cache / cycle_cache) — reset between tests or
  design fixtures so cache order doesn't matter.
- Recipe `normal.ingredients` vs `ingredients` (2.0/2.1 dual format) — fixtures
  should exercise both shapes.
- The science-pack FORCE (tier = science_tier unconditional) lives in
  `dynamic-generator.lua`, NOT in cost-solver. A solver-only test cannot prove
  the v3.5.19 fix; either factor that helper out into lib, or add a companion
  test that simulates the generator tier-floor block with the same name→tier
  function.
