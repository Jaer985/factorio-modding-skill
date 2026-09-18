# Factorio 2.0 Runtime Migration Patterns

## Context: Richness-or-infinite v1.3.0 audit (2026-07-01)

This mod clones resource prototypes in `data-final-fixes.lua` (adding `infinite=true`, disabling autoplace) and swaps them in at runtime via `on_chunk_generated`. The Factorio 2.0 migration exposed two classes of runtime API breakage.

## Pattern 1: `LuaEntityPrototype` dropped `.category`

**Error**:
```
LuaEntityPrototype doesn't contain key category.
  __Richness-or-infinite/control.lua:76: in function 'is_fluid_resource'
```

**Root cause**: `prototypes.entity[name].category` was removed from the runtime wrapper (`LuaEntityPrototype`) in Factorio 2.0. The raw data table (`data.raw.resource[name].category`) still has the field — this affects **only control.lua** (runtime), not data-final-fixes.lua (data stage).

**Fix**: Replace `.category` with `.resource_category`:
```lua
-- Factorio 1.x (broken in 2.0):
if proto.category == "basic-fluid" then ...

-- Factorio 2.0:
if proto.resource_category == "basic-fluid" then ...
```

**Relevant resource_category values**: `"basic-solid"` (ores), `"basic-fluid"` (crude oil, natural gas).

## Pattern 2: `LuaEntityPrototype` dropped `.normal`

**Error**:
```
LuaEntityPrototype doesn't contain key normal.
  __Richness-or-infinite/control.lua:194: in function <control.lua:42>
```

**Root cause**: Same as above — `normal` (base yield amount) exists on raw prototype tables but not on `LuaEntityPrototype` at runtime. In 1.x it was accessible; in 2.0 it throws.

**Fix**: Wrap in `pcall` with a sensible default:
```lua
local infinite_proto = prototypes.entity[infinite_name]
local fluid_normal = 60000  -- standard fluid resource base
if infinite_proto then
  local ok, val = pcall(function() return infinite_proto.normal end)
  if ok and val then fluid_normal = val end
end
```

**Typical defaults**: 300 for solid resources, 60000 for fluid resources.

## The `pcall` pattern for safe runtime prototype access

This generalizes to ANY property that may exist in the data stage but not on `LuaEntityPrototype` at runtime:

```lua
local function safe_proto_value(proto, field, default)
  if not proto then return default end
  local ok, val = pcall(function() return proto[field] end)
  if ok and val ~= nil then return val end
  return default
end

-- Usage:
local normal = safe_proto_value(prototypes.entity[name], "normal", 300)
```

The raw prototype table (`data.raw.*`) and the runtime wrapper (`prototypes.entity.*`) diverge on property access patterns. Properties that are always safe at runtime (like `.resource_category`) don't need pcall; ones you're unsure about should use it.

## Checklist for Factorio 2.0 audits

When reviewing a mod for 2.0 compatibility, check these runtime-specific patterns:

- [ ] `prototypes.entity[name].category` → `.resource_category` (if checking fluid vs solid)
- [ ] `prototypes.entity[name].normal` → pcall fallback (if reading base yield)
- [ ] `prototypes.entity[name].minable` — verify still works (should be fine in 2.0)
- [ ] `prototypes.entity[name].infinite` — verify still works (should be fine in 2.0)
- [ ] `entity.amount` — resource entity amount (should be fine in 2.0)
- [ ] `entity.fluidbox` — removed; use direct `LuaEntity` fluid methods
- [ ] `entity.active` → `entity.disabled_by_script`
- [ ] `entity.minable` write → `entity.minable_flag`
- [ ] `recipe.category` → `recipe.categories` (array) in both data stage AND control.lua
- [ ] `settings.global[...]` — verify setting type is correct (runtime-global vs startup)
