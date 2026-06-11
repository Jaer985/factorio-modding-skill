# Factorio Modding — 2.0 C++ Engine Changes & API Migration

Deep dive into the architectural changes introduced in Factorio 2.0/Space Age and how they affect modding.

---

## The Big Picture: What 2.0 Changed

Factorio 2.0 moved significant portions of the game logic from Lua to C++ for performance. This means:

- **Less Lua code needed** — many common patterns are now engine-native
- **Some Lua APIs removed** — replaced by C++ equivalents
- **New constraints** — some things that worked in Lua now have C++ guards
- **Better performance** — engine-level operations are faster than Lua equivalents

---

## Major API Changes

### 1. Storage Replaces Global

```lua
-- 1.1 (deprecated in 2.0)
global.my_data = {}

-- 2.0 (required)
storage.my_data = {}
```

**Why:** The `storage` table is managed by the C++ engine for desync-safe persistence. The old `global` table still works but is deprecated.

**Impact:** 
- `storage` is available in all control stage callbacks
- `on_load` is READ ONLY for `storage`
- `storage` persists across saves just like `global` did

### 2. Single-Table Arguments

Many 2.0 API methods changed from positional arguments to single-table (named) arguments:

```lua
-- 1.1: positional
game.create_surface("my-surface", map_gen_settings)
game.get_player(1)

-- 2.0: named table
game.create_surface({name = "my-surface", settings = map_gen_settings})
game.get_player({index = 1})
```

**Check the API docs for every method you use.** The migration is per-method, not global.

### 3. Improved Collision System

```lua
-- 1.1 (deprecated)
collision_mask = {"item-layer", "floor-layer"}

-- 2.0 (required)
collision_mask = {
  layers = {
    ["item-layer"] = true,
    ["floor-layer"] = true
  }
}
```

**New layer names in 2.0:**
- `"item-layer"`, `"floor-layer"`, `"object-layer"`, `"player-layer"`, `"water-tile"`
- `"doodad-layer"`, `"elevated-layer"`, `"transport-belt-layer"`, `"pipe-layer"`

**Custom collision layers:**
```lua
-- Define in data.lua
local custom_layer = {
  type = "collision-layer",
  name = "my-mod-layer"
}

-- Use in entities
collision_mask = {
  layers = {
    ["my-mod-layer"] = true,
    ["floor-layer"] = true
  }
}
```

### 4. Automatic Tech/Recipe Reset

```lua
-- 1.1: Required after adding technologies
force.reset_recipes()
force.reset_technologies()

-- 2.0: HANDLED BY ENGINE. Do NOT call these.
-- Calling them will cause double-reset errors.
```

**What the engine does automatically:**
- Researched technologies are preserved
- Recipes are unlocked based on current tech level
- New recipes/techs are automatically available

### 5. Event Signature Changes

```lua
-- 1.1: Simpler event payloads
script.on_event(defines.events.on_built_entity, function(event)
  -- event.entity, event.player_index
end)

-- 2.0: Richer event payloads with filtering built in
script.on_event(defines.events.on_built_entity, function(event)
  -- event.entity, event.player_index, event.surface_index
  -- event.tick, event.created_by_migration
end, {filter = {name = "my-entity"}})
```

---

## New 2.0 Features Relevant to Modding

### Surface Platform Property

```lua
-- Check if a surface is a space platform
if entity.surface.platform then
  -- This is a space platform, handle differently
  log("Platform name: " .. entity.surface.platform.name)
end

-- Platform state
if surface.platform then
  local state = surface.platform.state
  -- defines.space_platform_state.on_planet
  -- defines.space_platform_state.in_space
  -- defines.space_platform_state.on_planet_orbit
end
```

### Quality System (C++ Native)

Quality is now a first-class C++ concept, not a mod:

```lua
-- Item quality (C++ native, no Lua mod needed)
local quality = item_stack.quality -- LuaQualityPrototype
log("Quality: " .. quality.name) -- "normal", "uncommon", "rare", "epic", "legendary"

-- Recipe quality control
local recipe = {
  type = "recipe",
  name = "my-recipe",
  allow_quality = true,           -- can produce quality items
  quality_affects_product = false, -- ingredients quality doesn't affect output
}

-- Entity ghost quality
if entity.type == "entity-ghost" then
  local ghost_quality = entity.quality
  log("Ghost quality: " .. ghost_quality.name)
end
```

### Elevated Rails (C++ Native)

```lua
-- Elevated rail support is engine-native
-- Mods can define rail-ramp prototypes
local rail_ramp = {
  type = "rail-ramp",
  name = "my-rail-ramp",
  -- connection points for elevated rail network
}
```

### Space Age: New C++ Systems

| System | Description |
|--------|-------------|
| **Space platforms** | C++ managed surfaces with orbital mechanics |
| **Planetary logistics** | Automatic cargo delivery between surfaces |
| **Space elevator** | Static C++ entity linking surface to orbit |
| **Asteroid collector** | C++ managed entity for space resources |
| **Cargo landing pad** | Centralized logistics hub per surface |

---

## API Migration Table

### Runtime API (control.lua)

| 1.1 Called | 2.0 Equivalent | Notes |
|------------|----------------|-------|
| `game.get_player(index)` | `game.get_player({index = index})` | Table arg |
| `game.get_surface(name)` | `game.get_surface({name = name})` | Table arg |
| `game.create_surface(name, settings)` | `game.create_surface({name = name, settings = settings})` | Table arg |
| `entity.orderup()` | REMOVED | Use `entity.teleport()` |
| `entity.orderdown()` | REMOVED | Use `entity.teleport()` |
| `global.*` | `storage.*` | Migration required |
| `force.reset_recipes()` | DO NOT CALL | Engine handles it |
| `force.reset_technologies()` | DO NOT CALL | Engine handles it |
| Running `pairs` on `game.players` | Same but faster | C++ iterator optimization |
| `script.on_event(id, handler, filters)` | Same but `filters` richer | Filter improvements |
| `player.gui.screen` | Same | No change |
| `player.gui.relative` | **NEW** | Attach UI to machine interfaces |
| `remote.add_interface()` | Same | No change |
| `game.create_random_generator()` | Same | No change |
| `surface.find_entities_filtered()` | Same + more filters | `position`, `to_be_deconstructed` etc. |

### Prototype API (data stage)

| 1.1 Pattern | 2.0 Pattern | Notes |
|-------------|-------------|-------|
| Old collision_mask array | New `layers` dictionary table | BREAKING |
| Old fluidbox format | Enhanced fluidbox | New pipe simulation |
| Recipe ingredients/results | Same | `type` field now standard |
| Technology unit | Enhanced | `research_trigger` support |
| `type = "tile"` | Same + elevated rail | New tile flags |
| `type = "entity-ghost"` | Same + quality | `ghost.quality` |
| Equipment grid | Same | No change |
| `render_mode_required` | **NEW** | Control rendering layers |

---

## C++ Engine Performance Implications for Mods

### What's Faster in 2.0

| Operation | 2.0 vs 1.1 |
|-----------|-------------|
| `pairs(game.players)` | C++ native iterator, 5-10x faster |
| `pairs(game.surfaces)` | C++ native iterator, 5-10x faster |
| `surface.find_entities_filtered()` | Optimized spatial hash, 2-3x faster |
| `entity.valid` | O(1), no Lua overhead |
| `storage` access | Similar to `global` |
| Event dispatch with filters | C++ side filtering, Lua only runs for matches |

### What's Slower (or Different)

| Operation | Note |
|-----------|------|
| Heavy `on_tick` with no filters | Still the same performance trap |
| Frequent `serpent.line()` | Not optimized, still Lua |
| Deeply nested table operations | Same Lua performance as 1.1 |

---

## Key Takeaways for Mod Developers

1. **Check the API docs before porting** — don't assume 1.1 signatures work.
2. **Use `storage` not `global`** — migration is simple but critical.
3. **Don't call `reset_recipes()` or `reset_technologies()`** — the engine handles it.
4. **Update collision masks** — the old format will crash.
5. **Use table arguments** — many 2.0 methods require named tables.
6. **Leverage event filters** — they're faster in 2.0 with C++ side filtering.
7. **Quality is native** — you don't need a mod for quality tiers.
8. **Space platforms are special surfaces** — use `surface.platform` to detect them.
9. **Test with Space Age enabled** — even if you don't depend on it, players will use it.
10. **Read the changelog** — every 2.0.x release may tweak API signatures.
