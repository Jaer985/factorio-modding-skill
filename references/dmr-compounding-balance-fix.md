# DMR Compounding Balance Fix — Diminishing Returns

Applied in v3.3.5 (2026-07-01) to fix exponential crafting times in Recursive Steps (Compounding) mode.

## Problem

The compounding formula applied `1.5x` penalty on `dark_matter` and `1.25x` on `time` at **every recursion level**. For deep recipe chains (logistic science pack ~depth 6), the factor was `1.5^6 = 11.4x`, producing **2,780s (46 min)** per craft.

## Fix

Changed compounding to use **diminishing returns by depth**:

```lua
local dm_factor = 1.0 + (penalty / math.max(1, depth + 1))
local time_factor = 1.0 + (penalty * 0.5 / math.max(1, depth + 1))
```

Where `depth` tracks how many recipe hops the current computation is from the root item.

### Effects

| Depth | Old factor | New factor |
|-------|-----------|------------|
| 0     | 1.50x     | 1.50x      |
| 1     | 2.25x     | 1.88x      |
| 2     | 3.38x     | 2.19x      |
| 3     | 5.06x     | 2.46x      |
| 4     | 7.59x     | 2.71x      |
| 5     | 11.39x    | 2.93x      |
| 6     | 17.09x    | 3.14x      |

The sequence `1.5, 1.25, 1.167, 1.125, 1.1, 1.083...` converges, preventing exponential blowup while preserving the "deeper = more expensive" design.

## Repository structure

### `lib/cost-solver.lua` changes

1. **Function signature**: `solve_cost(name, visited, is_root, depth)` — added `depth` parameter.
2. **Cache discipline**: `solved_cache` stores RAW (unpenalized) values. Penalty is applied at return time based on caller depth, not stored. This prevents compounding of already-compounded values cached at different depths.
3. **Cache return path**: When a cached item is looked up in compounding mode, the penalty is applied based on the **caller's** depth (not the depth at which it was originally solved), giving correct chain-length-dependent cost.
4. **Ingredient recursion**: `CostSolver.solve_cost(ing_name, visited, false, depth + 1)` — increments depth for each recipe hop.
5. **Compounding formula**: Uses `penalty / (depth + 1)` per level.

### `prototypes/recipes/dynamic-generator.lua` changes

- Hard cap on `dark_matter_cost` (which sets `energy_required`): **600s maximum**.
- Prevents any single replication recipe from taking more than 10 min base (before replicator speed multipliers).
- The cap only affects complex items (science packs, rocket parts) with deep chains; normal items (plates, circuits, engines) are well under it.

## Locking effect

With a T5 replicator (speed 16x), the effective craft time for a capped item is:
- `600 / 16 = 37.5s` per pack
