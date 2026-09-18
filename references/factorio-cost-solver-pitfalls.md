# Factorio cost-solver pitfalls

> **What**: Concrete bugs found in DMR v3.5.0 cost-solver (audited 2026-08-09) and other dynamic-generators that compute recipe cost/tier recursively. Each pitfall includes: the bug pattern, why it triggers, and the exact fix.
>
> **Why**: The "3-pass audit methodology" in `factorio-modding` SKILL.md focuses on `category→categories` migration. It does NOT catch cost-solver internal bugs. These pitfalls extend the audit surface for any mod with a recursive cost solver.
>
> **Source**: SDD Think audit of `dark-matter-replicators-reborn_3` (DMR v3.5.0 → v3.5.1) on 2026-08-09. Full report at `<project>/specs/`.

---

## Pitfall C1: Recipe selection ignores `normal.ingredients` (HIGH)

**Symptom**: User reports "Components (Tier 1) contains too much stuff" with overhaul mods (Bob's, Angel's, Krastorio 2). Items that should be tier 2+ end up in tier 1.

**Root cause**: In `build_recipe_map()`, recipes are ranked by `#recipe.ingredients`. Recipes that use the Factorio 2.0+ format (only `recipe.normal.ingredients`, no `recipe.ingredients`) get count=99 and lose every comparison → the wrong (often vanilla) recipe is stored in `recipe_map[product_name]`. Then `recipe_tech_map[recipe.name]` returns nil because the wrong recipe name is indexed → no tech bump → tier 1.

**Where seen in DMR v3.5.0**: `lib/cost-solver.lua:140-144`
```lua
local current_ing_count = current_recipe.ingredients and #current_recipe.ingredients or 99
local new_ing_count = recipe.ingredients and #recipe.ingredients or 99
```

**Fix**:
```lua
local function get_ing_count(r)
    if r.ingredients then return #r.ingredients end
    if r.normal and r.normal.ingredients then return #r.normal.ingredients end
    if r.expensive and r.expensive.ingredients then return #r.expensive.ingredients end
    return 99
end

-- In build_recipe_map:
local current_ing_count = get_ing_count(current_recipe)
local new_ing_count = get_ing_count(recipe)
```

Apply the same priority helper to `recipe.results` / `recipe.normal.results` for consistency.

**Why 99 is dangerous**: It's a magic number that means "complex" but actually means "I couldn't read the field". With the fix, a recipe with `normal.ingredients = {a, b, c}` correctly reports count=3, not 99.

**Test case**: Add a temporary log in `build_recipe_map()` for any overhaul mod item (e.g. `bob-ruby-3`, `angels-coke`) and confirm `recipe_map[name].ingredients` or `recipe_map[name].normal.ingredients` is read correctly.

---

## Pitfall C2: `elseif` threshold chain makes the highest tier unreachable (HIGH)

**Symptom**: Science packs/items with 5+ unique ingredients should be tier 3 by a count-based fallback heuristic, but stay at tier 2.

**Root cause**: Lua evaluates `if`/`elseif` chains in order. The first matching condition wins. If the conditions are ordered from LOW to HIGH threshold, the HIGH branch is dead code:

```lua
-- BROKEN: with pack_count=6, the >=3 branch fires first → tier 2, never reaches >=5
if max_tier == 1 and pack_count >= 3 then
    max_tier = 2
elseif max_tier == 1 and pack_count >= 5 then
    max_tier = 3
end
```

**Where seen in DMR v3.5.0**: `lib/cost-solver.lua:231-234` (the `get_tier_from_tech` fallback heuristic).

**Fix**: Order from HIGH to LOW threshold, or use independent `if` blocks:
```lua
if max_tier == 1 and pack_count >= 5 then
    max_tier = 3
elseif max_tier == 1 and pack_count >= 3 then
    max_tier = 2
end
```

**Generalizes to**: ANY chain of mutually-exclusive numeric thresholds. Common spots: tier assignment, difficulty scaling, recipe complexity, complexity→price mappings. Always ask: "Is the highest-threshold branch reachable given the order?"

**Test case**: Construct a mock tech with 6 unique unknown science packs, call `get_tier_from_tech(mock_tech)`, assert result==3.

---

## Pitfall C3: Dead categories from incomplete refactors (MEDIUM)

**Symptom**: Locale or category registry lists N categories, but `get_item_category()` only ever returns M < N. Changelog says "Expanded from 7 to 18" but the runtime count is 14.

**Root cause**: A category was added to the central registry (`repltypes.lua`) and locale (`replcategory-name` section) during a refactor, but the classification function was not updated. The category is wired for display but unreachable for assignment.

**Where seen in DMR v3.5.0**: `lib/repltypes.lua` defines `device2, device3, device4, device5` (4 categories) with tiers and localization, but `prototypes/recipes/dynamic-generator.lua:get_item_category()` never returns any of them — all 4 are dead code.

**Detection**:
```bash
# Find all defined categories:
grep -E '^\s+[a-z0-9-]+\s*=\s*{' lib/repltypes.lua

# Find all returned categories:
grep -E 'return "[a-z0-9-]+"' prototypes/recipes/dynamic-generator.lua

# Diff them — any in the first list not in the second is dead
```

**Two valid fixes**:
1. **Eliminate** the dead categories from registry + locale (preferred for hygiene; lower risk).
2. **Wire them** in `get_item_category()` with a heuristic (e.g. `#recipe.ingredients >= 5 → device4`, `>= 8 → device5`). More work, more powerful, but the heuristic can misclassify edge cases.

**Changelog discipline**: When removing dead categories, update the changelog to match the actual count ("14 active categories" instead of "18"). Documentation should never claim more than the code delivers.

---

## Pitfall C4: Default-value drift between `settings.lua` and `cost-solver.lua` (MEDIUM)

**Symptom**: Changelog and `settings.lua` both say a setting defaults to `true`, but the cost-solver reads `get_startup_setting(name, false)` — fallback is `false`. If `settings.startup` were ever missing or corrupted, behavior would silently change.

**Where seen in DMR v3.5.0**:
- `settings.lua:184` → `default_value = true` for `dmrsa-use-machine-efficiency`
- `lib/cost-solver.lua:368` → `helpers.get_startup_setting("dmrsa-use-machine-efficiency", false)` (fallback false)

**Fix**: Keep the fallback in sync with `default_value`:
```lua
-- If settings.lua says default_value = true:
helpers.get_startup_setting("dmrsa-use-machine-efficiency", true)
```

**General audit command**:
```bash
# Extract all default_value= lines
grep -E 'default_value' settings.lua

# Extract all get_startup_setting fallback args
grep -E 'get_startup_setting\("[^"]+",\s*(true|false)\)' lib/*.lua
# Cross-check the two lists — every name+default pair must match
```

**Why this matters**: The fallback only fires in pathological cases (settings table missing), but when it does, the user gets silent behavior change with no error. Better to fail loudly or match the documented default.

---

## Pitfall C5: Direct `settings.startup[name].value` access in prototype files (MEDIUM)

**Symptom**: A `data.lua` or `prototypes/*.lua` file does `if settings.startup["foo"].value == false then ...` without nil-check. If the setting is renamed or removed, the file crashes with "attempt to index a nil value".

**Where seen in DMR v3.5.0**: `prototypes/raw-resources.lua:16`:
```lua
if settings.startup["tenemut-near-spawn"].value == false then
    autoplace_table.has_starting_area_placement = false
end
```

**Fix** (use the existing helper, requires `require("lib.helpers")` at the top):
```lua
local helpers = require("lib.helpers")
-- ...
if helpers.get_startup_setting("tenemut-near-spawn", true) == false then
    autoplace_table.has_starting_area_placement = false
end
```

**Why this matters**: prototype files run at data stage BEFORE startup settings are fully resolved in some edge cases (e.g. if another mod's data-final-fixes removes the setting). The `helpers.get_startup_setting` wrapper does nil-check internally and returns the fallback.

---

## Pitfall C6: `require("defines")` skipped for `gprefix` global (LOW)

**Symptom**: A file uses `gprefix` as if it were a global, but never requires `defines.lua` (which sets it). If load order changes, the file crashes with "attempt to concatenate a nil value".

**Where seen in DMR v3.5.0**:
- `prototypes/raw-resources.lua:1` uses `gprefix` but has no `require("defines")`
- `lib/target-mapper.lua:2` hardcodes `local gprefix = "dmrsa-"` instead of using `require("defines")`

**Fix**: Add `require("defines")` at the top OR use `local gprefix = require("defines").gprefix` if defines is structured to return that.

**Audit command**:
```bash
# Find files using gprefix
grep -rln 'gprefix' --include='*.lua' /path/to/mod/

# Find which require defines
grep -l 'require("defines")' /path/to/mod/**/*.lua

# Any file in the first set not in the second is at risk
```

---

## Audit checklist for cost-solver mods

Before publishing any mod with a recursive cost solver, run this checklist:

1. **Recipe selection** — does `build_recipe_map` check `normal.ingredients`? (Pitfall C1)
2. **Threshold chains** — are `if/elseif` chains ordered HIGH-to-LOW? (Pitfall C2)
3. **Category registry vs assignment** — does every category in the registry get assigned? (Pitfall C3)
4. **Default-value sync** — do `settings.lua` defaults match `get_startup_setting` fallbacks? (Pitfall C4)
5. **Nil-safe settings access** — every `settings.startup[name].value` wrapped in helper? (Pitfall C5)
6. **gprefix consistency** — every file using `gprefix` either requires `defines` or hardcodes consistently? (Pitfall C6)
7. **Cycle detection cache** — does the cycle fallback cache also dedupe identical cycles?
8. **Recursion depth** — is there a hard cap on recursion depth (e.g. 20 levels) to prevent stack overflow with deep mod chains?
9. **Hard cap on final cost** — is there a `if cost > MAX then cost = MAX` safety net? (DMR uses 600s.)
10. **Tier cap at ingredient + 1** — does the tech tier cap prevent "blue bottle in T5" with Bob's/Angel's?

A clean run on all 10 means the mod should not regress on common mod interactions.

---

## Related references

- `references/dmr-cost-solver-balance.md` — diminishing returns formula, hard caps, tier cap design.
- `references/dmr-bobs-tier-misassignment.md` — worked example of the C1 bug (tier 1 leakage with Bob's).
- `references/dmr-tier-cap-safe-prereq-3.3.6.md` — tier cap implementation and safe re-enable of prereqs.
