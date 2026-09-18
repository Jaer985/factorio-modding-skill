# DMR Original Fork Analysis — nihilistzsche/dark-matter-replicators-space-age

Reference: `https://github.com/nihilistzsche/dark-matter-replicators-space-age` (v2.0.4)
Our version: `dark-matter-replicators-reborn` (v3.4.0 → v3.5.0)

## Architecture comparison

| Aspect | Original fork | Our version |
|--------|--------------|-------------|
| **Item discovery** | Manual tables per mod (bob.lua=617 lines, vanilla.lua=9KB) | Dynamic via TargetMapper + CostSolver |
| **Tier assignment** | Category→fixed tier (repltypes: ore=1, element=2, etc.) | Computed from ingredient chain depth + science packs |
| **Categories** | 15 (ore, element, shape, alloy, chemical, device2-5, life, module, science, exotic, magic, alien) | 7 (ore, chemical, alloy, module, science, general, organic) |
| **Cost system** | `replvar` variables + manual cost entries per item | Recursive ingredient-chain solver |
| **Prerequisites** | Smart: auto-resolve recipe→items, recipe→tech, remove redundant | Basic: dedup only, no transitive reduction |
| **Tech distribution** | Individual tech per item/group | Grouped Categories (primary), Individual, Base Game |
| **SA planetary** | Minimal | Full: 4 planetary replicators + planet-specific categories |
| **Machine efficiency** | `replvar("smelting", 1/3)` etc. adjusts cost by machine type | Not implemented (added as optional in v3.5.0) |

## Key findings

### 1. Category→tier system (ported as core fix)

The original's most important design decision: **category determines tier, not computation**.

```lua
-- Original repltypes:
ore = {tier = 1}
element = {tier = 2}
shape = {tier = 2}
alloy = {tier = 3}
chemical = {tier = 3}
device2 = {tier = 2}  device3 = {tier = 3}
device4 = {tier = 4}  device5 = {tier = 5}
```

This completely avoids the tier misassignment bug. A plate is always tier 3 (alloy), regardless of whether its ore is shallow or deep in the tech tree.

**Our hybrid approach**: category→floor tier, cost-solver can push higher. Implemented in `lib/repltypes.lua` with 18 categories.

### 2. Machine efficiency (ported as optional)

The original used `replvar` to define cost multipliers per recipe category:
```lua
replvar("smelting", 1/3)        -- Electric furnace: 33% of baseline
replvar("oil-processing", 14/9)  -- Oil refinery: 155% of baseline
replvar("centrifuging", 140/81)  -- Centrifuge: 173% of baseline
```

These represent the relative efficiency of different machine types. More efficient machines = cheaper to replicate. Added to our cost-solver as optional setting `dmrsa-use-machine-efficiency` (default false).

### 3. Smart prerequisite resolution (partially ported)

The original's `process-prereqs.lua` does:
- Converts recipe references to item prereqs (if a recipe is needed, all its replicatable ingredients become prereqs)
- Converts recipe references to tech prereqs (finds the technology that unlocks a recipe)
- Removes redundant prereqs (if A requires B and B requires C, C is removed from A)
- Handles disabled categories by replacing them with their own prereqs

Our code already had dedup; the redundant removal was added in this port.

### 4. Locale already had 15 categories

Our locale (both EN and ES) already had entries for element, shape, life, exotic, magic, alien, device2-5 in the `[repltype-setting]` and `[repltype-tech]` sections — they just weren't wired up in code. The `[replcategory-name]` section was missing them and was updated.

### 5. What we kept from our version

- **Dynamic item discovery**: TargetMapper scans all item types automatically
- **Grouped technology distribution**: Original had individual techs only
- **SA planetary replicators**: Vulcanus, Fulgora, Gleba, Aquilo with specialized machines
- **Recursive cost solver**: More accurate cost computation than manual variables
- **data-final-fixes safety net**: Strip orphaned prereqs, fix lab inputs

## Files compared

| Original file | Our equivalent | Delta |
|--------------|---------------|-------|
| `prototypes/repltypes.lua` | `lib/repltypes.lua` (NEW) | Ported 15 categories + added military, organic, general |
| `prototypes/repltypes-data.lua` | `data.lua` (partial) | Subgroups auto-created, explicit definitions not needed |
| `prototypes/repltable/process-costs.lua` | `lib/cost-solver.lua` | Different approach entirely (manual vars vs recursive solver) |
| `prototypes/repltable/process-prereqs.lua` | `dynamic-generator.lua` | Smart prereq features ported selectively |
| `prototypes/repltable/process-actual-creation.lua` | `dynamic-generator.lua` | Category tech creation + icon layering |
| `prototypes/repltable/table-creation.lua` | N/A | Table init functions not needed |
| `prototypes/replications/bob.lua` (34KB) | N/A | Dynamic discovery replaces this |
| `prototypes/replications/vanilla.lua` (9KB) | N/A | Dynamic discovery replaces this |
| `prototypes/functions.lua` | `lib/helpers.lua` | Similar utility functions |
| `data-final-fixes.lua` | `data-final-fixes.lua` | Both clean up, different specifics |
| `settings.lua` | `settings.lua` | Mostly same settings + our additions |
