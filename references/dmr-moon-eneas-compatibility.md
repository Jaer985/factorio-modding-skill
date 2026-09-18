# DMR + moon-eneas Compatibility

## Overview
**Mod**: moon-eneas (Eneas) v0.6.10 by Amelie
**Size**: 50+ .lua files, ~152KB zip
**Type**: Space Age content mod (new planet, entities, lore)

## Why it conflicts with DMR

moon-eneas deletes the `spidertron-unit` technology in its `data-final-fixes.lua` (loaded from `prototypes/patches/tech.lua`):

```lua
local spidertech = data.raw.technology["spidertron-unit"]
if spidertech then
    data.raw.technology["spidertron-unit"] = nil
end
```

DMR was adding `spidertron-unit` as a prerequisite for grouped/individual replication technologies that replicate spidertron-related items. Since DMR adds prereqs in `data-updates.lua` (where `spidertron-unit` exists) and moon-eneas deletes it in `data-final-fixes.lua`, the same load-order race condition as with aai-loaders-sane applies.

## Pattern: Delete-and-replace

moon-eneas depends on `spidertron-unit-07`, which provides the original spidertron technology. Moon-eneas then:
1. Deletes `data.raw.technology["spidertron-unit"]` in data-final-fixes
2. Adds its own `unit-07` entity/recipe system (defined in prototypes/entity/unit-05.lua)

This is the same pattern as aai-loaders-sane: third-party mod providing an alternative progression for vanilla mechanics.

## Fix applied in DMR v3.3.4

Removed external original techs as prerequisites from all dynamically-generated DMR technologies. This prevents the class of bugs regardless of which mod deletes what in data-final-fixes.

## ⚠️ Fix NOT sufficient — crash returned in v3.5.10/3.5.15

The v3.3.4 removal was incomplete: **grouped technologies** (`dmrsa-grouped-repl-*-tech`) still collect `group.original_techs` as prerequisites (dynamic-generator.lua, the `for original_tech_name, _ in pairs(group.original_techs)` block). So a grouped tech whose group contains spidertron items again referenced `spidertron-unit`, and the startup crash returned:

```
Failed to load mods: Error in assignID: technology with name 'spidertron-unit'
does not exist. It was removed by moon-eneas.
Source: dmrsa-grouped-repl-5-general-tech (technology).
```

### Root cause — load-order race

1. DMR's `data-updates.lua` runs → generates grouped techs, checks `data.raw.technology["spidertron-unit"]` which EXISTS at that point → prereq added.
2. moon-eneas's `data-final-fixes.lua` runs → deletes `spidertron-unit`.
3. DMR's `data-final-fixes.lua` PASS 1 (strip missing prereqs) runs — **but in arbitrary order relative to moon-eneas unless a dependency declares ordering**. If DMR's data-final-fixes ran BEFORE moon-eneas's, PASS 1 never saw the deletion and the invalid prereq survived to assignID.

DMR's PASS 1 code is correct (it strips missing prereqs from all `dmrsa-*` techs) — the bug is purely **execution order of data-final-fixes across mods**.

### Fix applied in DMR v3.5.15 — declare optional dependency

```json
"dependencies": [
    "base",
    "? space-age",
    "? moon-eneas"
]
```

`? moon-eneas` (optional) forces Factorio to load DMR's data-final-fixes AFTER moon-eneas's, so PASS 1 sees the deleted tech and strips the prereq; PASS 3 then re-routes any orphaned grouped tech.

### Generalization (class-level rule)

Any time another mod deletes/renames a technology or recipe that your mod may reference, and your cleanup runs in `data-final-fixes.lua`, you MUST declare that mod as an **optional dependency** in info.json to force load order. This applies to aai-loaders-sane (deletes `aai-loader` techs), moon-eneas (deletes `spidertron-unit`), and any future mod that provides alternative progression. The pattern:

1. Identify the mod(s) that delete techs your dynamic generation may reference.
2. Add `? <mod-name>` to info.json dependencies (optional, so it doesn't force install).
3. Verify in a save with both mods that startup succeeds.

See also `references/dmr-aai-loaders-compatibility.md` for the same class of conflict.

## Architecture notes

moon-eneas structure:
```
data.lua → planet, items, fluids, recipes, technologies, entities, categories
data-final-fixes.lua → requires prototypes/patches/tech.lua (spidertron-unit deletion)
                     → removes Eneas trees/decoration from Nauvis autoplace
control.lua → runtime scripts (camera, events, radar, talk, informator)
```

Key takeaway: uses `require()` from data-final-fixes.lua for patch files, keeping the main file clean and patches modular.
