# DMR + Angel's Petrochemical Processing Compatibility

## Overview
**Mod**: angelspetrochem v2.0.3 by Arch666Angel
**Size**: 168KB zip, 50+ .lua files
**Type**: Complete oil/gas/chemical processing overhaul — multi-phase oil, gas chains, water chemistry
**Dependencies**: angelsrefining, ?bobplates, ?bobelectronics

## How the DMR conflict actually worked

### The `angels-basic-chemistry` duplicate prereq issue

This technology is **registered once** by Angel's Petrochem in `prototypes/technology/petrochem-basic-chemistry.lua`:

```lua
data:extend({
  {
    type = "technology",
    name = "angels-basic-chemistry",
    prerequisites = { "automation" },
    effects = { { type = "unlock-recipe", recipe = "angels-liquifier" }, ... },
    ...
  },
})
```

It is used as a prerequisite by technologies in BOTH Angel's Petrochem AND Angel's Smelting. The error DMR users saw (`"Technology prerequisite 'angels-basic-chemistry' is registered more than once"`) was NOT caused by two mods defining the same tech. It was caused by DMR's own iteration logic: when DMR scanned items to find their "original technologies," it discovered the same tech name (`angels-basic-chemistry`) from multiple paths (both a petrochem item and a smelting item) and tried to insert it as a prerequisite multiple times.

**Fix**: deduplicate the prerequisite list before creating the technology prototype. DMR v3.3.3 added a final dedup pass; v3.3.4 removed external original techs as prereqs entirely.

## Patterns learned from Angel's Petrochem codebase

### OV (Override) System — shared across all Angel's mods

Defined in a shared library (`angelsmods.functions.OV`), the override system provides:

| Method | Purpose |
|--------|---------|
| `OV.add_prereq(tech, prereq)` | Add prerequisite with built-in dedup |
| `OV.remove_prereq(tech, prereq)` | Remove prerequisite |
| `OV.patch_recipes({...})` | Batch recipe ingredient/result/energy changes |
| `OV.disable_recipe({names})` | Disable recipes |
| `OV.disable_technology({names})` | Disable technologies |
| `OV.converter_fluid(old, new)` | Replace a fluid throughout ALL recipes (dynamic) |
| `OV.global_replace_item(old, new)` | Replace all item references globally |
| `OV.remove_output(recipe, item)` | Remove specific output from a recipe |
| `OV.execute()` | Apply all queued overrides |

Key insight: overrides are **queued** in data-updates and data-final-fixes, then batch-applied via `OV.execute()` at the end of each phase. This prevents ordering issues within a single file.

### Trigger System — cross-mod feature flags

```lua
angelsmods.trigger = angelsmods.trigger or {}
angelsmods.trigger.plastic = true
angelsmods.trigger.resin = mods["bobelectronics"] and true or false
```

These flags are checked by other Angel's mods to conditionally enable/disable features. If Petrochem defines `trigger.plastic = true`, Smelting knows it can rely on plastic-related recipes existing.

### Namespace tree

```
angelsmods =
  ├── smelting       (angelssmelting)
  ├── petrochem      (angelspetrochem)
  ├── refining       (angelsrefining)
  ├── industries     (angelsindustries)
  ├── functions      (shared lib — OV, hide, move_item, allow_productivity)
  └── trigger        (cross-mod feature flags)
```

### Three-phase override execution

| Phase | File | Overrides applied |
|-------|------|-------------------|
| data.lua | (inline) | Prototype loading only — no OV calls |
| data-updates.lua | petrochem-override.lua | Base game patches, Angel's cross-mod patches, Bob's patches → `OV.execute()` |
| data-final-fixes.lua | petrochem-global-override.lua | Global/residual overrides → `OV.execute()` again |

### Modular file organization

```
prototypes/
├── buildings/       → Each building type gets its own file
├── generation/      → World generation (natural gas, etc.)
├── global-override/ → Final-stage patches (per target mod)
├── override/        → Per-mod override files (base-game, angelsrefining, bobplates, etc.)
├── recipes/         → Entity recipe modifications
└── technology/      → Technology definitions
```

## Application to DMR

1. **Shared helper library**: DMR's `lib/helpers.lua` is already a good start. Angel's `functions` library is the gold standard — we could expand helpers with an `OV`-like system for DMR's own patches.
2. **Trigger flags**: Could be useful if DMR ever needs cross-mod coordination (e.g., `dmrsa.trigger.processed_ores = true`).
3. **The `angels-basic-chemistry` lesson**: The "registered more than once" error was in DMR's own code, not in Angel's. Always trace the actual error source before blaming cross-mod interaction.
