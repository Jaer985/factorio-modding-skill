# DMR + Angel's Smelting Compatibility

## Overview
**Mod**: angelssmelting v0.4.4 by Arch666Angel
**Size**: 37MB repo, 65+ .lua files
**Type**: Complete smelting overhaul — 18 metals, 10+ furnace types, multi-tier progression

## Why it conflicts with DMR

### Duplicate technology prerequisites
The main conflict is not with Angel's Smelting itself, but with the Angel's mods ecosystem sharing technology names:
- `angels-basic-chemistry` is registered by **Angel's Petrochem** (`angelspetrochem`)
- It is used as a prerequisite by BOTH Angel's Petrochem AND Angel's Smelting technologies
- When DMR iterates items to find "original technologies" for replication, it sees `angels-basic-chemistry` from both paths → adds it twice as a prerequisite → "registered more than once" startup crash

### Original tech dependency issue
Angel's Smelting replaces vanilla smelting recipes (iron-plate, copper-plate, etc.) with its own multi-step processes. DMR's replication system would pick up these recipes and their original technologies as prereqs. Since Angel's Smelting runs in a different data phase, the prereq might not exist when DMR checks.

## Patterns learned from Angel's codebase

### Global Namespace Pattern
```lua
if not angelsmods then angelsmods = {} end
if not angelsmods.smelting then angelsmods.smelting = {} end
```
Every Angel's mod registers under `angelsmods.<subsystem>` namespace, enabling cross-mod communication. This is a best practice for large mod ecosystems.

### Centralized Override System (OV)
Angel's uses a sophisticated override system that batches all modifications:
```lua
local OV = angelsmods.functions.OV
OV.patch_recipes({...})         -- Batch recipe modifications
OV.disable_technology({names})  -- Batch tech disabling
OV.global_replace_item(from, to) -- Replace all references
OV.execute()                    -- Apply all queued changes
```
Three override phases:
| Phase | File | What runs |
|-------|------|-----------|
| data.lua | (inline) | Basic prototype loading |
| data-updates.lua | smelting-override.lua | Recipe/tech patches |
| data-final-fixes.lua | smelting-override-global.lua | Final global overrides |

### Modular-by-metal organization
Each metal gets its own file for items, recipes, and technologies:
```
prototypes/items/angels-aluminium.lua
prototypes/recipes/smelting-aluminium.lua
prototypes/technology/smelting-technology.lua  (all techs in one 3154-line file)
```

## Application to DMR

1. **Namespace pattern**: DMR could use a global `dmrsa` namespace for cross-mod compatibility data (e.g., which techs are safe to reference).
2. **OV pattern**: DMR's override management is already relatively centralized but could formalize queuing for patches that must apply in a specific order.
3. **Deduplication**: The existing "belt-and-suspenders dedup pass" in DMR's data-final-fixes.lua correctly handles the Angel's duplicate prereq case.
