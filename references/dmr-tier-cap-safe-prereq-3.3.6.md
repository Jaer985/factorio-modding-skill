# DMR 3.3.6 — Tier cap + safe original-tech prereqs

## Context

User reported "blue bottles in T5" from Bob's mods. The dynamic cost-solver assigned T5 because Bob's intermediate chemicals are unlocked by technologies requiring space science, even though the ingredient chain is T1-T2.

Separately, the original item technologies as prerequisites for replication techs were blanket-disabled (v3.3.4, due to aai-loaders-sane / moon-eneas deleting techs in data-final-fixes). This meant replication techs had no gating: you could replicate an item without having researched its normal crafting technology.

## Changes

### 1. cost-solver.lua — Tier cap (line 290-306)

**Before:**
```lua
local unlock_tech = recipe_tech_map[recipe.name]
if unlock_tech then
    local tech_tier = CostSolver.get_tier_from_tech(unlock_tech)
    max_tier = math.max(max_tier, tech_tier)
end
```

**After:**
```lua
local unlock_tech = recipe_tech_map[recipe.name]
if unlock_tech then
    local tech_tier = CostSolver.get_tier_from_tech(unlock_tech)
    local ingredient_tier = max_tier
    max_tier = math.max(max_tier, tech_tier)
    if max_tier > ingredient_tier + 1 then
        max_tier = ingredient_tier + 1
    end
end
```

**Effect**: An item whose ingredients max out at T2 but whose tech requires space science now caps at T3 instead of T5.

### 2. dynamic-generator.lua — Safe original-tech prereqs (individual path, line 269-284)

**Before:** Entire section was commented out with `[DISABLED]`.

**After:**
```lua
local original_recipe = data.raw.recipe[name]
if original_recipe then
    local recipe_obj = CostSolver.recipe_map[name]
    if recipe_obj then
        local original_tech = CostSolver.recipe_tech_map[recipe_obj.name]
        if original_tech and not original_tech.hidden and data.raw.technology[original_tech.name] then
            add_prereq(prerequisites, original_tech.name)
        end
    end
end
```

### 3. dynamic-generator.lua — Safe original-tech prereqs (grouped path, line 487-494)

**Before:** Same `[DISABLED]` block.

**After:**
```lua
for original_tech_name, _ in pairs(group.original_techs) do
    if data.raw.technology[original_tech_name] then
        add_prereq(prerequisites, original_tech_name)
    end
end
```

## Design rationale

### Why not keep prereqs disabled?

The blanket-disable was a shotgun fix: it prevented crashes (orphaned prereqs) but also removed all gating. Players could research replication for items they had no ability to craft normally. The safe re-enable restores the gate for the 95% case where the tech exists, and gracefully skips it for the 5% where another mod deleted it.

### Alphabetical ordering protection

The data-final-fixes.lua strip pass (existing in DMR since v3.3.3) handles orphaned prereqs. When the deleting mod sorts BEFORE `dark-matter-replicators-reborn` alphabetically (e.g., `aai-loaders-sane` → `d`), DMR's strip runs after and removes orphaned prereqs. When the deleting mod sorts AFTER (rare, `z` mods), the strip runs first and doesn't catch it — but this is the same failure mode as the old disabled approach, just with better behavior in the common case.

### Tier cap vs hard tier limit

The `ingredient_tier + 1` formula is chosen because:
- It's dynamic: works with any mod's tier depth
- It preserves legitimate high-tier items (promethium's ingredients are T5 → stays T5)
- It only fires on discrepancy (simple ingredients + endgame tech)
