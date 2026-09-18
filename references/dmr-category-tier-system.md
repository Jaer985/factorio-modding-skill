# DMR Category→Tier Hybrid System

## Problem

The dynamic recipe generator (v3.4.0) computes tiers via `CostSolver.solve_cost()` based on ingredient chain depth. This is unreliable with overhaul mods (Bob's, Angel's):

- Items with simple ingredients (1 hop to ore) but unlocked by mid-game tech → **tier 1** (too low)
- Items whose tech's custom science packs aren't detected → **tier 1** (too low)
- Items whose tech name contains "advanced" → **tier 5** (too high, false match)

## Two approaches contrasted

### Original fork (nihilistzsche/dark-matter-replicators-space-age)

Table-based: manual per-mod replication tables assign each item to a category.

```lua
repltech_recipe("electronic-circuit", "device3")  -- tier 3
repltech_recipe("processing-unit", "device5")     -- tier 5
repltech_recipe("bob-tin-plate", "alloy")         -- tier 3
```

**Category has fixed tier:**
```lua
repltypes = {
    ore = {tier = 1}, element = {tier = 2}, shape = {tier = 2},
    alloy = {tier = 3}, chemical = {tier = 3},
    device2 = {tier = 2}, device3 = {tier = 3},
    device4 = {tier = 4}, device5 = {tier = 5},
    module = {tier = 5}, life = {tier = 5},
    science = {tier = nil},  -- dynamic
}
```

Strengths: tier is always correct per category.  
Weakness: requires manual tables for every mod (bob.lua = 617 lines).

### Our dynamic generator (Jaer985 v3.4.0)

Auto-discovers items via TargetMapper, computes tier from recipe chain.

Strengths: works with any mod automatically.  
Weakness: tier computation unreliable (the bug this session tracked).

## Hybrid: category→tier with computed tier as reinforcement

```lua
-- 1. Classify item into category (auto-heuristics)
local category = get_item_category(name, target)  -- "alloy", "ore", etc.

-- 2. Category has fixed tier
local category_tier = repltypes[category].tier  -- "alloy" → 3

-- 3. Also compute via cost-solver (for "general" items, or as floor)
local computed_tier = CostSolver.solve_cost(name).tier or 1

-- 4. Final tier = max of both
local tier = category_tier and math.max(category_tier, computed_tier) or computed_tier
```

This ensures:
- An item classified as **alloy** (tier 3) is NEVER tier 1, even if ingredients are shallow
- An item classified as **general** (no fixed tier) uses computed tier
- If cost-solver says 5 but category says 3 → tier 5 (cost-solver wins when higher)

## Auto-classification heuristics (15 categories)

Detection order matters:

1. **ore** (tier 1): type=resource, subgroup=ore/raw-resource, name ends in "-ore"
2. **science** (dynamic): name contains "science-pack"
3. **chemical** (tier 3): type=fluid
4. **module** (tier 5): name contains "module", subgroup=module
5. **organic** (tier 3): SA spoilable items
6. **military** (tier 4): type=gun/ammo/armor/capsule
7. **alloy** (tier 3): name contains "plate"/"alloy"
8. **shape** (tier 2): name contains gear-wheel/pipe/stick/cable/brick/frame/bearing
9. **element** (tier 2): periodic table element names
10. **life** (tier 5): living/fish/spawner items
11. **exotic/magic/alien** (tier 5): keyword match
12. **general** (no fixed tier): everything else → computed tier

## Device2-5 vs "general"

The original had device2-5 for crafted items of increasing complexity. Since we can't auto-classify device tier without manual tables, items not matching the above categories fall into **general** and use computed tier with:
- Better science-pack detection in `get_tier_from_tech()`
- Fallback `find_tech_for_item()` if recipe_tech_map lookup fails
- Secondary validation in `DynamicGenerator.generate()`

## Implementation checklist

- [ ] `lib/repltypes.lua` — new file with category definitions
- [ ] `prototypes/recipes/dynamic-generator.lua` — 15-category `get_item_category()`
- [ ] `prototypes/recipes/dynamic-generator.lua` — tier = max(category_tier, computed_tier)
- [ ] `lib/cost-solver.lua` — tier computation secondary (for general category)
- [ ] `locale/` — add device2-5 and military entries
- [ ] `data.lua` — item-subgroups per category (from original repltypes-data.lua)
- [ ] `settings.lua` — optional: enable/disable per category
