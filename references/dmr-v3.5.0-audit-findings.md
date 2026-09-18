# DMR v3.5.0 Full Audit — Findings & Root Cause Analysis

> **Date**: 2026-08-09  
> **Scope**: Complete source read of 21 Lua/CFG files, cross-checked against factorio-modding skill + 5 accumulated references  
> **Deliverables**: specs/PRD.md, specs/tech-design.md, specs/acceptance-criteria.md  
> **Outcome**: 16 findings (0 critical, 3 high, 4 medium, 9 low)

---

## Key Findings

### H1 — Recipe selection ignores normal.ingredients (cost-solver.lua:140-144)

**Root cause**: `build_recipe_map()` compares recipe simplicity via `#recipe.ingredients`. Factorio 2.0+ recipes that use `recipe.normal.ingredients` exclusively have `recipe.ingredients = nil` → `99`. These recipes never win the simplicity contest → `recipe_map[product_name]` points to wrong recipe → `recipe_tech_map[recipe.name]` returns nil → no tech tier bump → item stuck at ingredient-chain tier (often 1).

**This is the root cause of the "Components Tier 1 has too much stuff with Bob's" bug** (ref: `dmr-bobs-tier-misassignment.md` Candidate #1).

**Fix**: Add fallback to count `normal.ingredients` (and `expensive.ingredients`) when `recipe.ingredients` is nil. Extract a helper function `get_ing_count(r)`.

### H2 — get_tier_from_tech fallback heuristic order bug (cost-solver.lua:231-234)

```lua
-- Current (wrong):
if max_tier == 1 and pack_count >= 3 then max_tier = 2
elseif max_tier == 1 and pack_count >= 5 then max_tier = 3 end

-- Fix (invert):
if max_tier == 1 and pack_count >= 5 then max_tier = 3
elseif max_tier == 1 and pack_count >= 3 then max_tier = 2 end
```

pack_count >= 5 always hits the >= 3 branch first; `elseif` never executes.

### H3 — Late-loading mod discovery gap (data-updates.lua:6)

DMR's `DynamicGenerator.generate()` runs in data-updates, which sorts alphabetically. "dark-matter-replicators-reborn" runs BEFORE most overhaul mods (k, s, z). Items added by other mods in THEIR data-updates are invisible. Mitigation: add `?` dependencies on major overhauls (K2, SE, Bob's, Angel's) to force DMR to load after them.

---

## Dead Categories: device2-5 (M1)

`get_item_category()` (dynamic-generator.lua:69-182) returns 14 distinct categories: ore, science, chemical, module, military, alloy, shape, element, organic, exotic, magic, alien, life, general. It NEVER returns device2, device3, device4, or device5. These 4 categories are defined in repltypes.lua with fixed tiers and locale entries, but are unreachable dead code.

**Contradicts changelog v3.5.0 claim**: "Expanded replication categories from 7 to 18." Effective count: 14 active.

The reference `dmr-category-tier-system.md` notes this as a known limitation: "Since we can't auto-classify device tier without manual tables, items not matching the above categories fall into general."

---

## data-final-fixes PASS 3: Planetary Grouped Tech Orphans (M2)

The tier extraction patterns (data-final-fixes.lua:84-85):
```lua
string.match(orphan_name, prefix_pat .. "replication%-([1-5])")
string.match(orphan_name, prefix_pat .. "grouped%-repl%-([1-5])")
```

For planetary grouped techs like `dmrsa-grouped-repl-vulcanus-chemical-tech`, neither pattern matches because the planet name sits between "grouped-repl-" and the tier number. Pattern 2 expects `grouped-repl-{digit}` but gets `grouped-repl-{planet}-{category}-tech`. Result: `tier_match = nil`, `target_tech_name = nil`, unlocks are lost.

---

## Validated Hints (of 17 initial)

| Hint | Verdict | Severity |
|------|---------|----------|
| #1: device2-5 dead | ✅ Confirmed | MEDIUM |
| #2: tier_match planetarios | ✅ Confirmed (nuanced: only affects grouped tech orphans) | MEDIUM |
| #3: get_tech_icons dead code | ✅ Confirmed but harmless | LOW |
| #4: baseline/planetary duplication | ⚠️ Redundancy, not a bug | — |
| #5: MACHINE_EFFICIENCY default | ✅ Confirmed (fallback ≠ default_value) | MEDIUM |
| #6: math.min counter-intuitive | ⚠️ Works correctly, needs docs | LOW |
| #7: recursion depth | ⚠️ Theoretical only, visited[] handles | — |
| #8: ingredient_tier + 1 cap | ⚠️ Safe, ingredient_tier never 0 | — |
| #9: cache raw vs final | ⚠️ Correctly designed | — |
| #10: Lua pattern escaping | ✅ Already correct everywhere | — |
| #11: normal.result in 2.1 | ✅ Path exists | LOW |
| #12: localised_name "?" | ⚠️ Standard Factorio, works | — |
| #13: visited[] cleanup | ✅ Backtracking is correct | — |
| #14: data-phase ordering | ⚠️ Mostly fine (all data.lua runs first) | LOW |
| #15: missing item types | ⚠️ Minor (rail-planner, blueprint-book) | LOW |
| #16: thumbnail size | ✅ 962KB → should be ~30KB | LOW |
| #17: no control.lua | ⚠️ Intentional design choice | — |

---

## Architecture Observations

### Global state reliance
- `gprefix` is set as global in `defines.lua` (no `local`), consumed by other files. `raw-resources.lua` and `target-mapper.lua` don't require defines.lua but use gprefix. Works only because data.lua loads defines first.
- Removing the global and using explicit `require("defines")` would be more robust.

### Dual-compat coverage
- `dynamic-generator.lua` correctly branches `category`/`categories` via `dmrsa_is_v21()`.
- `recipe_has_category()` in cost-solver handles both formats.
- `base-recipes.lua` and `planetary-replicators.lua` recipes don't set category → inherit engine default (safe for both 2.0 and 2.1).
- ✅ Dual-compat is well-implemented.

### Cost-solver design correctness
- Raw values cached, penalty applied at return based on caller depth → correct.
- Cycle detection via visited[] backtracking → correct.
- Diminishing returns formula: `1 + penalty/(depth+1)` → convergente.
- Hard cap 600s → safety net.
- Tier cap: `max(ingredient_tier, tech_tier) capped at ingredient_tier + 1` → prevents Bob's inflation.
- ❌ Only flaw: recipe selection ignores normal.ingredients (H1).

### data-final-fixes 4-pass safety net
- PASS 1: Strip missing prereqs from dmrsa-* techs → ✅
- PASS 2: Cross-mod validate all techs referencing dmrsa techs → ✅
- PASS 3: Orphan reassignment → ⚠️ Bug for planetary grouped (M2)
- PASS 4: SA science packs on lab.inputs → ✅

---

## Files Analyzed

| File | Lines | Key Findings |
|------|-------|-------------|
| `info.json` | 15 | factorio_version "2.0", optional deps correct |
| `settings.lua` | 210 | dmrsa-use-machine-efficiency default=true ✅ |
| `defines.lua` | 25 | dmrsa_is_v21() helper, gprefix global |
| `data.lua` | 25 | safe_require pattern, loads modular prototypes |
| `data-updates.lua` | 127 | DynamicGenerator entry point, gravity restrictions |
| `data-final-fixes.lua` | 156 | 4-pass safety net, M2 bug at L84-85 |
| `lib/cost-solver.lua` | 462 | H1 (L140), H2 (L231), M3 (L368) |
| `lib/repltypes.lua` | 145 | 18 categories, 4 dead (device2-5) |
| `lib/helpers.lua` | 116 | LOG_LEVELS, item_exists, get_startup_setting |
| `lib/target-mapper.lua` | 83 | Hardcoded gprefix, 11 item classes |
| `prototypes/recipes/dynamic-generator.lua` | 785 | get_item_category (14 effective), dual-compat |
| `prototypes/recipes/base-recipes.lua` | 137 | No category field (inherits default) |
| `prototypes/entities/replicators.lua` | 225 | 5 tiers, replication-lab entity |
| `prototypes/entities/planetary-replicators.lua` | 188 | 4 planetary machines, tint overlays |
| `prototypes/technologies/technologies.lua` | 167 | Tier 1-5 techs, space-lock setting |
| `prototypes/technologies/planetary-tech.lua` | 114 | 4 planetary research techs |
| `prototypes/raw-resources.lua` | 160 | M4 (L16 direct settings access) |
| `prototypes/items/dark-matter.lua` | 99 | Item group, subgroups, tool prototypes |
| `locale/en/dark-matter-replicators.cfg` | 376 | device2-5 entries (dead), 118 elements |
| `locale/es-ES/dark-matter-replicators.cfg` | 376 | Full ES translation |
| `changelog.txt` | 360 | v3.5.0 claims "18 categories" (should be 14 active) |

---

## Cross-Reference to Existing Skill References

| Reference | Relevance | Status |
|-----------|-----------|--------|
| `dmr-dual-compat-2.0-2.1.md` | Dual-compat implementation verified | ✅ Accurate |
| `dmr-category-tier-system.md` | Says "15 categories" — outdated (18 defined, 14 active) | ⚠️ Minor inaccuracy |
| `dmr-cost-solver-balance.md` | Diminishing returns + tier cap verified | ✅ Accurate |
| `dmr-bobs-tier-misassignment.md` | Candidate #1 (normal.ingredients) confirmed as root cause | ✅ Accurate |
| `dmr-tier-cap-safe-prereq-3.3.6.md` | Tier cap logic verified | ✅ Accurate |
| `dmr-bobs-science-pack-detection.md` | Science pack patterns verified | ✅ Accurate |
