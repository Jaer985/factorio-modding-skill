# Factorio Modding — Code Patterns Reference

Complete code patterns for Factorio 2.0/Space Age modding. Use these as templates and reference implementations.

---

## Table of Contents

- [A. control.lua Boilerplate (2.0)](#a-controllua-boilerplate-20)
- [B. info.json Schema](#b-infojson-schema)
- [C. settings.lua Definition Pattern](#c-settingslua-definition-pattern)
- [D. data.lua Prototype Pattern](#d-datalua-prototype-pattern)
- [E. Safe data-updates.lua](#e-safe-data-updateslua)
- [F. Remote Interface & Relative GUI](#f-remote-interface--relative-gui)
- [G. Ghost Quality & Debugging](#g-ghost-quality--debugging)
- [H. Space Platform Events](#h-space-platform-events)
- [I. Migration Pattern (Lua)](#i-migration-pattern-lua)
- [J. Prototype Name Migration (JSON)](#j-prototype-name-migration-json)
- [K. English Locale Pattern](#k-english-locale-pattern)

---

## A. control.lua Boilerplate (2.0)

```lua
-- control.lua

-- 1. Main Initialization
script.on_init(function()
  -- Initialize storage structures
  storage.players = storage.players or {}
  storage.settings = storage.settings or {}
end)

-- 2. Save Game Load (Do NOT write to storage here)
script.on_load(function()
  -- Re-register custom metatables or dynamic events if any
  -- script.register_metatable("my_class", my_class_metatable)
end)

-- 3. Mod/Game Configuration Changes
script.on_configuration_changed(function(data)
  -- Handle migrations/updates in runtime state
end)

-- 4. Event Handler Example with Filtering
script.on_event(defines.events.on_built_entity, function(event)
  local entity = event.entity
  if not (entity and entity.valid) then return end

  -- Handle entity logic
  local player = game.get_player(event.player_index)
  if player and player.controller_type == defines.controllers.remote then
    -- Handle remote view interaction
  end
end, {
  {filter = "name", name = "my-custom-entity"}
})
```

---

## B. info.json Schema

```json
{
  "name": "my-mod-name",
  "version": "1.0.0",
  "title": "My Mod Title",
  "author": "Author Name",
  "factorio_version": "2.0",
  "dependencies": ["base >= 2.0", "? space-age >= 2.0"],
  "quality_required": false,
  "space_platform_required": false,
  "license": "MIT"
}
```

**Key fields:**
- `factorio_version`: MUST be `"2.0"` for 2.0/Space Age mods
- `dependencies`: `"base >= 2.0"` minimum. Use `"? mod-name"` for optional, `"(?) mod-name"` for optional+hidden
- `quality_required`: set `true` if your mod absolutely needs the Quality expansion
- `space_platform_required`: set `true` if your mod needs Space Age
- `license`: ALWAYS specify. Can be SPDX identifier (MIT, GPL-3.0-only, Apache-2.0) or "All Rights Reserved"

---

## C. settings.lua Definition Pattern

```lua
-- settings.lua
data:extend({
  {
    type = "startup-setting",
    name = "my-mod-startup-toggle",
    setting_type = "boolean",
    default_value = true,
    order = "a"
  },
  {
    type = "runtime-global-setting",
    name = "my-mod-richness-mult",
    setting_type = "double",
    default_value = 1.0,
    minimum_value = 0.1,
    maximum_value = 10.0,
    order = "b"
  },
  {
    type = "runtime-per-user-setting",
    name = "my-mod-notify-enabled",
    setting_type = "bool-setting",
    default_value = true,
    order = "c"
  }
})
```

**Setting types:**
- `"startup-setting"` — requires game restart to change. Use for world-gen affecting values.
- `"runtime-global-setting"` — can be changed at runtime, affects all players.
- `"runtime-per-user-setting"` — each player has their own value.

**Setting value types:**
- `"bool-setting"` — boolean
- `"double"` — floating point number (with min/max)
- `"int-setting"` — integer (with min/max)
- `"string-setting"` — text

---

## D. data.lua Prototype Pattern

```lua
-- data.lua (Planet, Quality, Tech Triggers & Fluidboxes)

-- Custom quality tier
local legendary_plus = {
  type = "quality",
  name = "legendary-plus",
  icon = "__my-mod-name__/graphics/icons/legendary-plus.png",
  icon_size = 64,
  level = 6,
  color = {r = 0.8, g = 0.2, b = 0.9},
  next_quality = nil,
  beacon_power_multiplier = 2.5,
  mining_drill_productivity_bonus = 0.5,
  science_pack_productivity_bonus = 0.3
}

-- Custom planet with music integration
local my_planet = {
  type = "planet",
  name = "custom-planet",
  icon = "__my-mod-name__/graphics/icons/custom-planet.png",
  icon_size = 128,
  gravity_pull = 12,
  distance = 25,
  orientation = 0.15,
  magnitude = 1.0,
  subgroup = "planets",
  map_gen_settings = {
    terrain_segmentation = 1.5,
    water = 0.5,
    autoplace_controls = {
      ["coal"] = { frequency = 1.5, size = 1.2, richness = 2.0 }
    }
  },
  surface_properties = {
    ["pressure"] = 1000,
    ["temperature"] = 285,
    ["magnetic-field"] = 50
  },
  song = {
    playlist = {
      {
        music_track = "custom-music-track-name",
        volume = 0.6
      }
    }
  }
}

-- Technology using triggers (not science packs)
local trigger_tech = {
  type = "technology",
  name = "custom-trigger-tech",
  icon = "__my-mod-name__/technology/trigger-tech.png",
  icon_size = 256,
  effects = {
    {
      type = "unlock-recipe",
      recipe = "custom-item"
    }
  },
  research_trigger = {
    type = "mine-entity",
    entity = "crude-oil",
    amount = 500
  }
}

-- Recipe where quality scaling is disabled
local custom_recipe = {
  type = "recipe",
  name = "custom-item",
  energy_required = 5,
  ingredients = {
    {type = "item", name = "iron-plate", amount = 10}
  },
  results = {
    {type = "item", name = "custom-item", amount = 1}
  },
  allow_quality = true,
  quality_affects_product = false
}

data:extend({legendary_plus, my_planet, trigger_tech, custom_recipe})
```

**Prototype types commonly extended:**
- `item`, `recipe`, `technology`, `fluid`, `damage-type`
- `assembling-machine`, `furnace`, `mining-drill`, `offshore-pump`
- `inserter`, `transport-belt`, `underground-belt`, `splitter`
- `container`, `logistic-container`, `infinity-container`
- `planet`, `space-connection`, `asteroid-chunk`
- `quality`, `damage-type`, `module`, `equipment-grid`
- `projectile`, `beam`, `artillery-projectile`, `ammo`
- `explosion`, `smoke`, `fire`, `corpse`
- `tile`, `recipe-category`, `item-group`, `item-subgroup`
- `custom-input`, `shortcut`, `tips-and-tricks`

---

## E. Safe data-updates.lua

```lua
-- data-updates.lua

-- Safely modify base recipe
if data.raw["recipe"]["iron-plate"] then
  table.insert(data.raw["recipe"]["iron-plate"].ingredients, {type = "item", name = "stone", amount = 1})
end

-- Safely modify a pipe/fluidbox on a machine
-- NOTE: Factorio 2.0 split fluid_boxes into input_fluid_box / output_fluid_box
-- for some prototypes. Always check the new schema first, then fall back.
if data.raw["assembling-machine"]["assembling-machine-1"] then
  local machine = data.raw["assembling-machine"]["assembling-machine-1"]

  local new_fluid_box = {
    production_type = "input",
    pipe_picture = assembler3pipepictures(),
    pipe_covers = pipecoverspictures(),
    volume = 1000,       -- 2.0: replaces base_area
    pipe_connections = {{flow_direction = "input", direction = defines.direction.north, position = {0, -1}}}
  }

  if machine.input_fluid_box then
    -- Factorio 2.0 native schema: single input_fluid_box (not an array)
    -- To add a second input, you must convert to fluid_boxes array format
    -- or modify the existing input_fluid_box properties.
    -- Example: update pipe connections on existing input
    machine.input_fluid_box.pipe_connections[#machine.input_fluid_box.pipe_connections + 1] =
      new_fluid_box.pipe_connections[1]
  elseif type(machine.fluid_boxes) == "table" then
    -- Legacy schema fallback: fluid_boxes is an indexable array
    table.insert(machine.fluid_boxes, new_fluid_box)
  end
end
```

**Rules of thumb:**
- `data-updates.lua` — for MODIFYING existing prototypes. Safest place for cross-mod tweaks.
- `data-final-fixes.lua` — for ensuring your changes are LAST. Use when you need final say.
- ALWAYS guard every access with `if data.raw[...][...] then`.
- Never delete from `data.raw` — set amounts to 0 or disable instead.

---

## F. Remote Interface & Relative GUI

```lua
-- control.lua (Interoperability, Settings Validation & UI)

-- Safe reading of Settings
local function get_richness_multiplier()
  local val = settings.global["my-mod-richness-mult"].value
  if type(val) ~= "number" or val <= 0 then
    return 1.0 -- safe fallback boundary
  end
  return val
end

-- Define Remote Interface
remote.add_interface("my_mod_api", {
  get_mod_state = function(player_index)
    if not storage.players[player_index] then return nil end
    return storage.players[player_index].state
  end,
  trigger_mod_action = function(player_index, value)
    storage.players[player_index] = storage.players[player_index] or {}
    storage.players[player_index].value = value
  end
})

-- Relative GUI Definition
local function create_relative_gui(player)
  local relative_frame = player.gui.relative.add({
    type = "frame",
    name = "my_custom_relative_frame",
    caption = "Custom Control Panel",
    anchor = {
      gui = defines.relative_gui_type.assembling_machine_select,
      position = defines.relative_gui_position.right
    }
  })

  relative_frame.add({
    type = "button",
    name = "action_btn",
    caption = "Activate"
  })
end
```

**Remote interface patterns:**
- Namespace your interface: `"your_mod_name"` not `"api"`.
- Always return `nil` for invalid queries (don't error).
- Document your remote interface in your mod description/README.

**Relative GUI anchors:**
- `defines.relative_gui_type.assembling_machine_select`
- `defines.relative_gui_type.furnace_select`
- `defines.relative_gui_type.locomotive_select`
- `defines.relative_gui_type.cargo_wagon_select`
- `defines.relative_gui_type.fluid_wagon_select`
- `defines.relative_gui_type.roboport_select`
- `defines.relative_gui_type.storage_tank_select`
- `defines.relative_gui_type.radar_select`

---

## G. Ghost Quality & Debugging

```lua
-- control.lua (Debugging and Ghost Management)

-- Safe Sandbox Logging
local function dump_debugging_data(event_name, data_table)
  log("MyMod Debug: Event " .. event_name .. " triggered.")
  -- Write serialized table to script-output/mymod-debug.txt
  helpers.write_file("mymod-debug.txt", helpers.table_to_json(data_table) .. "\n", true)
end

-- Listening to built ghosts and retrieving quality
script.on_event(defines.events.on_built_entity, function(event)
  local entity = event.entity
  if not (entity and entity.valid) then return end

  if entity.type == "entity-ghost" then
    local ghost_quality = entity.quality.name
    dump_debugging_data("ghost_built", {
      name = entity.ghost_name,
      quality = ghost_quality,
      tick = event.tick
    })
  end
end)
```

**Ghost entity fields (2.0+):**
- `entity.ghost_name` — prototype name of the ghosted entity
- `entity.quality` — `LuaQualityPrototype`, access `.name`
- `entity.ghost_type` — type of the ghosted entity
- `entity.expires` — bool, whether the ghost has a build timer
- `entity.expires_after_ticks` — remaining ticks if expires

---

## H. Space Platform Events

```lua
-- control.lua (Space Platform Event Handling)

script.on_event(defines.events.on_space_platform_built_tile, function(event)
  local platform = event.platform
  if not platform then return end

  local player = game.get_player(event.player_index)
  if player then
    player.print("Tile built on platform: " .. platform.name)
  end
end)

-- Space platform state change
script.on_event(defines.events.on_space_platform_state_changed, function(event)
  local platform = event.platform
  if not platform then return end

  local new_state = platform.state -- defines.space_platform_state enum
  log("Platform " .. platform.name .. " state: " .. tostring(new_state))
end)
```

**Space platform events (2.0+):**
- `on_space_platform_built_entity` — entity built on platform
- `on_space_platform_mined_entity` — entity mined on platform
- `on_space_platform_built_tile` — tile built on platform
- `on_space_platform_mined_tile` — tile mined on platform
- `on_space_platform_state_changed` — platform state transition

**Platform states (`defines.space_platform_state`):**
- `on_planet` — parked at a planet
- `in_space` — in transit between planets
- `on_planet_orbit` — in orbit around a planet

---

## I. Migration Pattern (Lua)

```lua
-- migrations/2026-06-11_my-mod-name_1.1.0.lua

-- Safe prototype verification before modifying runtime storage
for _, force in pairs(game.forces) do
  if storage.forces and storage.forces[force.name] then
    storage.forces[force.name].unlocked_features = true
  end
end
```

**Migration naming convention:**
`YYYY-MM-DD_ModName_Version.lua`

**Rules:**
- Run only what's needed for this specific version change.
- Always guard checks on `storage` keys (player may join mid-game).
- Use `for _, force in pairs(game.forces)` for force-level changes.
- Use `game.get_surface()` or `game.surfaces` for surface-level changes.
- Never assume a key exists in `storage`.

---

## J. Prototype Name Migration (JSON)

```json
{
  "entity": {
    "old-entity-name": "new-entity-name"
  },
  "item": {
    "old-item-name": "new-item-name"
  },
  "technology": {
    "old-tech-name": "new-tech-name"
  },
  "recipe": {
    "old-recipe-name": "new-recipe-name"
  }
}
```

**When to use JSON vs Lua migration:**
| Scenario | Method |
|----------|--------|
| Simple prototype rename | JSON migration — engine handles it automatically |
| Storage data structure change | Lua migration — runtime script |
| Both rename AND storage changes | JSON migration + Lua migration |

JSON migrations go in `migrations/` with the naming pattern `YYYY-MM-DD_ModName_Version.json`.

---

## K. English Locale Pattern

```ini
[mod-setting-name]
roi-richness-threshold=Richness Threshold
my-mod-startup-toggle=Enable Advanced Extractor
my-mod-richness-mult=Resource Richness Multiplier

[mod-setting-description]
roi-richness-threshold=Define the minimum richness factor required for infinite resource yields.

[entity-name]
custom-extractor-drill=Advanced Extractor Drill

[item-name]
custom-extractor-drill=Advanced Extractor Drill

[planet-name]
custom-planet=Custom Planet

[quality-name]
legendary-plus=Legendary Plus

[technology-name]
custom-trigger-tech=Advanced Oil Prospecting

[recipe-name]
custom-item=Custom Item

[mod-description]
my-mod-name=Description of what my mod does
```

**Locale sections:**
- `[mod-setting-name]` / `[mod-setting-description]` — setting labels
- `[entity-name]` / `[entity-description]` — entity names
- `[item-name]` / `[item-description]` — item names
- `[fluid-name]` / `[fluid-description]` — fluid names
- `[recipe-name]` / `[recipe-description]` — recipe names
- `[technology-name]` / `[technology-description]` — tech names
- `[planet-name]` — planet names
- `[quality-name]` — quality tier names
- `[mod-name]` / `[mod-description]` — mod title/description (from `info.json`)
- `[tips-and-tricks-name]` / `[tips-and-tricks-description]` — tutorial tips

Save at `locale/en/config.cfg` or `locale/en/locale.cfg`. UTF-8 without BOM.
