# DMR Cost-Solver: Compounding Balance

## Problem

In `lib/cost-solver.lua`, the **Recursive Steps (Compounding)** cost-calculation method applies a penalty multiplier at every recursion level. With a default penalty of 0.5:

```
dark_matter_cost = ingredient_cost × (1.0 + penalty)   # 1.5× per level
```

This produces **exponential blowup**: a chain of depth 6 yields 1.5⁶ ≈ 11.4× multiplier. Logistic science packs ended up taking 2,780 seconds (46 minutes) — absurd for a consumable.

## Diminishing Returns Fix

The fix replaces the flat per-level penalty with a **depth-based diminishing factor**:

```lua
-- Instead of:
dark_matter = final_dm * (1.0 + penalty)            -- 1.5× always
time = final_time * (1.0 + penalty * 0.5)           -- 1.25× always

-- Use:
local dm_factor = 1.0 + (penalty / math.max(1, depth + 1))
local time_factor = 1.0 + (penalty * 0.5 / math.max(1, depth + 1))
```

Where `depth` is the number of recipe hops from the root item being replicated:
- Root item: depth = 0 → factor = 1 + 0.5/1 = 1.5×
- Direct ingredient: depth = 1 → factor = 1 + 0.5/2 = 1.25×
- Ingredient's ingredient: depth = 2 → factor = 1 + 0.5/3 = 1.17×
- Converges to 1.0× at large depths.

### Code changes

Three locations in `solve_cost()`:

1. **Cache return** (solved_cache hit for compounding mode): apply diminishing factor using the **caller's** depth (not the original solver's depth).

2. **Ingredient recursion**: pass `depth + 1` to each ingredient call so it knows its depth:
   ```lua
   local solved = CostSolver.solve_cost(ing_name, visited, false, depth + 1)
   ```

3. **Compounding return**: compute factor with `depth + 1` for self, apply to final_dm and final_time.

### Critical cache change

**Do NOT overwrite `solved_cache` with penalized values.** The cache must store only **RAW (unpenalized)** costs. Penalty is applied at return time based on the caller's current depth. This prevents:
- Double-compounding when an item is referenced from multiple chains at different depths
- Cache poisoning from a shallow-first access that would give wrong results for deeper access

## Safety Net: Hard Cap

Even with diminishing returns, some complex items can still produce high costs. Add a hard cap in `dynamic-generator.lua`:

```lua
if dark_matter_cost > 600 then
    dark_matter_cost = 600
end
```

600 seconds = 10 minutes base. With T5 replicator speed (16×), this becomes 37.5s — reasonable for endgame.

## Results After Fix

| Item | Before (old compounding) | After (diminishing + cap) |
|------|--------------------------|---------------------------|
| Iron plate | 1.5s | 1.5s |
| Electronic circuit | 12s | 12s |
| Engine unit | 69s | 69s |
| Electric engine unit | 197s | 197s |
| Logistic science pack (T1) | 2,780s (46min) | 600s (10min) |
| Logistic science pack (T5) | 174s | 37.5s |

## Convergence Table

| Depth | Old Factor (1.5^depth+1) | New Factor (diminishing) |
|-------|--------------------------|--------------------------|
| 0 | 1.50× | 1.50× |
| 1 | 2.25× | 1.88× |
| 2 | 3.38× | 2.19× |
| 3 | 5.06× | 2.46× |
| 4 | 7.59× | 2.71× |
| 5 | 11.39× | 2.93× |
| 6 | 17.09× | 3.14× |
| 8 | 38.44× | 3.52× |

The new factor **converges** to ~3.5×, while the old factor grows without bound.
