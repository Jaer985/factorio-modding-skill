# DMR + Bob's: Tier misassignment analysis (2026-07-19)

## Bug report

User `sp518` reported on the Mod Portal:
> "With Bob's, It looks like Replication: Components (Tier 1) contains too much stuff according things after enter Space Age (unlock with white bottle)."

**Discussion**: https://mods.factorio.com/mod/dark-matter-replicators-reborn/discussion/6a5c9c7a501290593666794f

## Tier assignment pipeline (data-updates.lua → dynamic-generator.lua)

```
TargetMapper.get_potential_replication_targets()
    ↓
CostSolver.solve_cost(name) → {dark_matter, time, tier}
    ↓
get_item_category(name, target) → "general" | "ore" | "alloy" | "chemical" | "module" | "science" | "organic"
    ↓
group_key = tier .. "-" .. category  → "1-general" = "Components (Tier 1)"
    ↓
Grouped tech: dmrsa-grouped-repl-{group_key}-tech
```

## Cost-solver tier logic (lib/cost-solver.lua)

`solve_cost()` computes tier through:

1. **Base resource check** — if item is in `BASE_RESOURCE_COSTS`, return that tier directly
2. **Ingredient recursion** — recurse into each ingredient, take `max_tier` across all
3. **Tech lookup** — `recipe_tech_map[recipe.name]` finds the unlocking technology
4. **Tech tier** — `get_tier_from_tech(unlock_tech)` classifies based on science packs:
   - Red/green → 1
   - Chemical → 2
   - Planetary (metallurgic, electromagnetic, agricultural) → 3
   - Production/utility (white bottle) → 4
   - Space/cryogenic/promethium → 5
5. **Tier cap** — `if max_tier > ingredient_tier + 1 then max_tier = ingredient_tier + 1 end`

## Three candidate root causes

### Candidate #1: recipe_tech_map lookup failure (most likely)

In `CostSolver.build_recipe_map()`, when multiple recipes produce the same item, the code chooses the one with the fewest ingredients:

```lua
local current_ing_count = current_recipe.ingredients and #current_recipe.ingredients or 99
local new_ing_count = recipe.ingredients and #recipe.ingredients or 99
if new_ing_count > 0 and new_ing_count < current_ing_count then
    recipe_map[product_name] = recipe
end
```

**Two sub-bugs here:**

**a) `recipe.ingredients` vs `recipe.normal.ingredients`**: For Factorio 2.0+ recipes that define ingredients *only* in `recipe.normal.ingredients`, `recipe.ingredients` is nil → `#nil or 99` → count = 99. This makes the recipe appear extremely complex, so it never wins the "simplicity" contest. The recipe stored in `recipe_map` may be the wrong one.

**b) Name mismatch**: If the selected recipe has a different `.name` than what `build_tech_map` indexed via `effect.recipe`, `recipe_tech_map[recipe.name]` returns nil → no tech bump → tier 1.

### Candidate #2: get_tier_from_tech misclassification

The function checks `tech.unit.ingredients` with string matching:

```lua
elseif name == "production-science-pack" or name == "utility-science-pack"
       or string.find(name, "production") or string.find(name, "utility") then
    max_tier = math.max(max_tier, 4)
```

- `string.find(name, "production")` is a Lua pattern match, not a substring check. Since `"production-science-pack"` contains no magic pattern chars, it works for standard pack names. But Bob's custom pack names need to contain the string "production" or "utility" to match.
- If Bob's techs use a different `ingredients` format (e.g. with `type = "item"` field that isn't parsed), the name extraction fails → returns tier 1.

### Candidate #3: Tier cap correctly limiting to tier 2

For an item with ingredient_tier=1 and tech_tier=4 (production science):
- `max_tier = math.max(1, 4) = 4`
- Cap: `4 > 1 + 1 = 2` → `max_tier = 2`

This is *intended behavior* from the tier cap fix (v3.3.6), but might still feel wrong to the user because Bob's items that should be end-game are accessible at tier 2.

## Key files examined

| File | Path | Role |
|------|------|------|
| cost-solver.lua | `lib/cost-solver.lua` | Recipe cost and tier computation |
| dynamic-generator.lua | `prototypes/recipes/dynamic-generator.lua` | Recipe creation, tech binding, category assignment |
| target-mapper.lua | `lib/target-mapper.lua` | Item discovery and filtering |
| technologies.lua | `prototypes/technologies/technologies.lua` | Base technology definitions (Tiers 1-5) |
| data-updates.lua | `data-updates.lua` | Entry point for generation + unlock attachment |
| defines.lua | `defines.lua` | `gprefix = "dmrsa-"` |

## Diagnostic patch

Add to `lib/cost-solver.lua` before the cache write in `solve_cost()`:

```lua
if string.find(name, "bob") or string.find(name, "angel") then
    local unlock_tech = recipe_tech_map[recipe.name]
    log(string.format("DMR-DEBUG: %s → recipe=%s, ingredient_tier=%d, tech_found=%s, tech_tier=%d, final_tier=%d",
        name,
        recipe.name,
        max_tier,  -- before tech bump
        tostring(unlock_tech ~= nil),
        unlock_tech and CostSolver.get_tier_from_tech(unlock_tech) or 0,
        max_tier   -- after tech bump and cap
    ))
end
```

## Tech distribution settings

The default setting `dmrsa-tech-distribution = "Grouped Categories"` creates one technology per category+tier combination. The localized name for "general" category is "Components", so "Replication: Components (Tier 1)" = the `1-general` group.

The alternate "Individual Technologies" mode creates one tech per item, which would still have wrong tiers but the user would see individual items at the wrong level rather than a flooded group tech.
