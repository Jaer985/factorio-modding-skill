# Factorio Modding — Lua Performance & UPS Optimization

Factorio is a performance-critical game. Bad mod code can destroy UPS (Updates Per Second) for thousands of entities. Write efficient code from the start.

---

## The Performance Mindset

**Every Lua instruction runs 60+ times per second.**

A slow `on_tick` handler that takes 1ms will cost 60ms/s — that's 10% of your frame budget gone to ONE handler. With 50 mods, this adds up fast.

---

## High-Frequency Event Optimization

### Always Use Event Filters

```lua
-- ❌ BAD: Runs on EVERY built entity, even irrelevant ones
script.on_event(defines.events.on_built_entity, function(event)
  -- check if it's MY entity...
end)

-- ✅ GOOD: Only runs when MY specific entity is built
script.on_event(defines.events.on_built_entity, function(event)
  -- only runs for "my-mod-custom-assembler"
end, {{filter = "name", name = "my-mod-custom-assembler"}})

-- ✅ EVEN BETTER: Multiple filters
script.on_event(defines.events.on_built_entity, function(event)
  -- runs for any of my entities
end, {
  {filter = "name", name = "my-mod-entity-1"},
  {filter = "name", name = "my-mod-entity-2"},
})
```

**Supported filter types:**
- `"name"` — prototype name
- `"type"` — entity type string
- `"ghost_type"` — ghost entity type
- `"force"` — force (player team)
- `"surface_index"` — surface index

### Throttle `on_tick` — Never Run Every Tick

```lua
-- ❌ BAD: Runs 60 times per second
script.on_event(defines.events.on_tick, function(event)
  for _, entity in pairs(storage.my_entities) do
    -- do work
  end
end)

-- ✅ GOOD: Throttled to once per second
script.on_event(defines.events.on_tick, function(event)
  if event.tick % 60 ~= 0 then return end
  for _, entity in pairs(storage.my_entities) do
    -- do work
  end
end)

-- ✅ BETTER: Staggered processing with stateful iterator
-- NOTE: storage.my_entities is keyed by unit_number (non-sequential).
-- The # operator returns 0 for hash maps, so index-based loops fail silently.
-- Use next() to persist the hash pointer across ticks.
script.on_event(defines.events.on_tick, function(event)
  local mod_storage = storage["my-mod-name"]
  if not mod_storage then return end

  local batch_size = 50
  local current_key = mod_storage.iterator_keys.my_entities

  for _ = 1, batch_size do
    local key, entity_data = next(mod_storage.my_entities, current_key)
    if not key then
      -- Wrapped around — reset pointer and stop this tick
      mod_storage.iterator_keys.my_entities = nil
      return
    end
    current_key = key
    -- process entity_data
  end

  mod_storage.iterator_keys.my_entities = current_key
end)
```

### Use game.tick Instead of on_tick When Possible

```lua
-- Instead of on_tick, check game.tick where you already have an event
script.on_event(defines.events.on_built_entity, function(event)
  local entity = event.entity
  if not (entity and entity.valid) then return end

  -- Use game.tick for time-based logic inside existing events
  storage.last_processed_tick = game.tick
end)
```

---

## Entity & Data Structure Patterns

### Avoid Full Iteration

```lua
-- ❌ BAD: Search all surfaces for your entities every tick
script.on_event(defines.events.on_tick, function(event)
  for _, surface in pairs(game.surfaces) do
    for _, entity in pairs(surface.find_entities_filtered({name = "my-entity"})) do
      -- process
    end
  end
end)

-- ✅ GOOD: Track entities in namespace-isolated storage and update incrementally
script.on_init(function()
  storage["my-mod-name"] = {
    my_entities = {}
  }
end)

script.on_event(defines.events.on_built_entity, function(event)
  local entity = event.entity
  if not (entity and entity.valid) then return end

  local mod_storage = storage["my-mod-name"]
  if not mod_storage then return end

  if entity.name == "my-entity" then
    mod_storage.my_entities[entity.unit_number] = entity
  end
end, {{filter = "name", name = "my-entity"}})

script.on_event(defines.events.on_player_mined_entity, function(event)
  local entity = event.entity
  local mod_storage = storage["my-mod-name"]
  if mod_storage and entity and mod_storage.my_entities[entity.unit_number] then
    mod_storage.my_entities[entity.unit_number] = nil
  end
end, {{filter = "name", name = "my-entity"}})

-- Process only tracked entities
script.on_event(defines.events.on_tick, function(event)
  if event.tick % 60 ~= 0 then return end
  local mod_storage = storage["my-mod-name"]
  if not mod_storage then return end

  for unit_number, entity in pairs(mod_storage.my_entities) do
    if entity.valid then
      -- process
    else
      mod_storage.my_entities[unit_number] = nil -- cleanup invalid
    end
  end
end)
```

### Prefer unit_number Over Entity References

```lua
-- ❌ BAD: Storing entity reference directly (may become invalid)
storage.tracked_entities = {entity} -- entity reference

-- ✅ GOOD: Store unit_number, look up when needed
storage.tracked_entities = {[entity.unit_number] = true}

-- Lookup via deterministic unit_number resolution (2.0+)
-- NOTE: surface.find_entity() takes (name, position), NOT unit_number.
-- Use game.get_entity_by_unit_number() for O(1) lookup by unit_number.
local function get_tracked_entity(unit_number)
  local entity = game.get_entity_by_unit_number(unit_number)
  if entity and entity.valid then return entity end
  return nil
end
```

### Minimize Table Allocations

```lua
-- ❌ BAD: Creates new table every call
local function get_config(player_index)
  return {
    enabled = storage.players[player_index].enabled or false,
    speed = storage.players[player_index].speed or 1
  }
end

-- ✅ GOOD: Read directly, no allocation
local function is_enabled(player_index)
  if not storage.players then return false end
  if not storage.players[player_index] then return false end
  return storage.players[player_index].enabled or false
end
```

---

## Efficient Filtered Search

```lua
-- Use find_entities_filtered with specific filters (fast C++ path)
local entities = surface.find_entities_filtered({
  name = "my-entity",
  force = "player",               -- narrow by force
  limit = 100,                     -- cap results
  area = {{x = -10, y = -10}, {x = 10, y = 10}}  -- restrict area
})

-- Avoid find_entities() without filters (returns ALL entities)
-- ❌ local all = surface.find_entities()

-- Use get_entities() for chunk-specific queries (2.0+)
local chunk_entities = surface.get_entities({area = chunk_area})
```

---

## Locality of Reference

### Module-Scope Caching

Cache Lua standard library methods and frequently-called Factorio APIs at the **module scope** (top of file). This eliminates hash table lookups (`math.`, `table.`, `game.`) on every call inside the event loop at 60 UPS.

```lua
-- At the top of control.lua — module scope
local math_min = math.min
local math_ceil = math.ceil
local table_insert = table.insert
local pairs = pairs

-- Factorio API shortcuts (available after on_init/on_load)
local get_entity = game.get_entity_by_unit_number
local get_player = game.get_player
```

### Event-Scope Caching

Cache per-tick references inside the handler closure:

```lua
-- ❌ BAD: Repeated global lookups
script.on_event(defines.events.on_tick, function(event)
  if event.tick % 60 ~= 0 then return end
  -- game.surfaces and game.players looked up every tick
  for _, player in pairs(game.players) do
    for _, surface in pairs(game.surfaces) do
      -- ...
    end
  end
end)

-- ✅ GOOD: Cache references in locals
script.on_event(defines.events.on_tick, function(event)
  if event.tick % 60 ~= 0 then return end
  local players = game.players
  local surfaces = game.surfaces
  for _, player in pairs(players) do
    for _, surface in pairs(surfaces) do
      -- ...
    end
  end
end)
```

---

## `serpent.line()` vs String Concatenation

```lua
-- ❌ BAD: String concatenation for complex objects
log("Entity: " .. entity.name .. " pos: " .. entity.position.x .. "," .. entity.position.y)

-- ✅ GOOD: Use serpent for structured logging (only in debug mode)
if DEBUG then
  log("Entity dump: " .. serpent.line({name = entity.name, pos = entity.position}))
end
```

**Never use `serpent.line()` in production code paths** — it's slow. Use it only in DEBUG mode or for error reporting.

---

## Summarized Rules

| Rule | Why |
|------|-----|
| Filter ALL high-frequency events | C++ side filters entities before Lua runs |
| Throttle `on_tick` to N > 1 | 60 ticks/s * N handlers = disaster |
| Track entities in storage | `find_entities_filtered` is slow on large surfaces |
| Store `unit_number`, not references | References go invalid; unit_number is stable |
| Cache globals in locals | Lua global lookups are slower than locals |
| No allocation in hot paths | GC pauses destroy UPS |
| Use `game.tick` inside existing events | Avoids creating an `on_tick` handler at all |
| No `serpent.line()` in production | Serialization is expensive |
| Stagger processing across ticks | Spreads cost, prevents frame drops |
| Profile with real entity counts | 10 vs 10,000 entities = very different profile |
