# DMR 2.1 Category Audit — Worked Example

Audit date: 2026-07-18
Mod: Dark Matter Replicators Reborn v3.3.6 → 3.4.0
Auditor: Kai (game-dev)

## Goal

Migrate DMR from Factorio 2.0 to 2.1. The #1 breaking change is `RecipePrototype::category` (single string) → `categories` (array of strings). This file documents the full systematic audit.

## Files scanned

16 Lua files across the mod:

```
lib/cost-solver.lua
lib/helpers.lua
lib/target-mapper.lua
prototypes/recipes/dynamic-generator.lua
prototypes/recipes/base-recipes.lua
prototypes/entities/replicators.lua
prototypes/entities/planetary-replicators.lua
prototypes/items/dark-matter.lua
prototypes/raw-resources.lua
prototypes/technologies/technologies.lua
prototypes/technologies/planetary-tech.lua
data.lua
data-updates.lua
data-final-fixes.lua
defines.lua
settings.lua
```

## Discovery command

```bash
grep -rn 'category' --include='*.lua' /path/to/mod/
```

128 total matches. Each classified by bucket (see factorio-modding skill → Workflow → Step 2).

## Breaking changes found

Only **3** of 128 matches were actually breaking:

### 1. `cost-solver.lua:79` — Bucket B (data-stage iteration)

```lua
-- OLD (2.0):
if recipe.category == "recycling" or string.find(name, "%-recycling$") then

-- NEW (2.1):
if recipe_has_category(recipe, "recycling") or string.find(name, "%-recycling$") then
```

### 2. `cost-solver.lua:82` — Bucket B (data-stage iteration)

```lua
-- OLD (2.0):
if recipe.category == "barreling" or string.find(name, "empty%-") or string.find(name, "%-unbarrel") then

-- NEW (2.1):
if recipe_has_category(recipe, "barreling") or string.find(name, "empty%-") or string.find(name, "%-unbarrel") then
```

### 3. `dynamic-generator.lua:214` — Bucket A (recipe prototype definition)

```lua
-- OLD (2.0):
category = category,

-- NEW (2.1):
categories = { category },
```

## Helper added to cost-solver.lua

```lua
local function recipe_has_category(recipe, cat)
    if recipe.categories then
        for _, c in ipairs(recipe.categories) do
            if c == cat then return true end
        end
    end
    return false
end
```

## Non-breaking patterns (125 matches, left untouched)

| Bucket | Pattern | Count | Why safe |
|--------|---------|-------|----------|
| E | `type = "recipe-category"` definitions | 5 | Defines categories, doesn't read recipe field |
| G | `crafting_categories = { ... }` on assemblers | 1 | Entity field, not recipe field |
| H | `research_category = nil` on labs | 1 | Lab field, not recipe field |
| K | `category = "resource"` on autoplace-control | 1 | Not a recipe |
| L | `type = category` / iteration variables | 2 | Item type iteration, not recipe |
| M | Local variable named `category` | 15 | Just Lua string variables |
| N | Internal group keys ("ore","chemical") | 3 | Mod-internal concept |
| — | `data.raw["recipe-category"][name]` validation | 1 | Registry still works in 2.1 |

## Version bumps

- DMR: 3.3.6 → **3.4.0**, factorio_version 2.0 → **2.1**
- Richness-or-infinite: 1.3.0 → **1.4.0**, factorio_version 2.0 → **2.1** (0 structural changes needed — already compatible)

## Key takeaway

A typical overhaul mod has 100+ `category` references but only 3–10 are breaking. The classification table (buckets A–N) prevents unnecessary changes that would break entity definitions, autoplace controls, or recipe-category registrations.
