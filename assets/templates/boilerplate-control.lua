-- control.lua
-- Generated from factorio-modding skill template
-- Factorio 2.0 / Space Age compatible

-- ============================================
-- Module-scope caching (Locality of Reference)
-- ============================================
local pairs = pairs
local get_entity = game.get_entity_by_unit_number
local get_player = game.get_player
local table_deepcopy = require("util").table.deepcopy

-- ============================================
-- Debug Toggle (set false before release)
-- ============================================
local DEBUG = false

local function debug_log(...)
  if not DEBUG then return end
  log("[MyMod]", ...)
end

local function debug_dump(filename, data)
  if not DEBUG then return end
  helpers.write_file("my-mod/" .. filename, helpers.table_to_json(data) .. "\n", true)
end

-- ============================================
-- Initialization
-- ============================================
script.on_init(function()
  storage["my-mod-name"] = {
    players = {},
    my_entities = {},
    entity_count = 0,
    iterator_keys = {}
  }
  debug_log("Mod initialized")
end)

script.on_load(function()
  -- Re-register metatables if any
  -- script.register_metatable("my_class", my_class_metatable)
  debug_log("Mod loaded")
end)

script.on_configuration_changed(function(data)
  -- Handle mod version migrations
  debug_log("Configuration changed")

  -- Mid-game initialization scan (if mod is added to an existing save)
  local changes = data.mod_changes and data.mod_changes["my-mod-name"]
  if changes and not changes.old_version then
    local mod_storage = storage["my-mod-name"]
    if not mod_storage then return end

    local count = 0
    for _, surface in pairs(game.surfaces) do
      for _, entity in pairs(surface.find_entities_filtered({name = "my-mod-entity"})) do
        if not mod_storage.my_entities[entity.unit_number] then
          mod_storage.my_entities[entity.unit_number] = {
            unit_number = entity.unit_number,
            surface_index = surface.index,
            position = entity.position,
            created_tick = game.tick
          }
          count = count + 1
        end
      end
    end
    mod_storage.entity_count = count
  end
end)

-- ============================================
-- Event Handlers
-- ============================================

-- Track placed/created entities (covers players, robots, and scripts)
local built_events = {
  defines.events.on_built_entity,
  defines.events.on_robot_built_entity,
  defines.events.script_raised_built
}

local function handle_entity_creation(event)
  local entity = event.entity
  if not (entity and entity.valid) then return end

  local mod_storage = storage["my-mod-name"]
  if not mod_storage then return end

  if entity.name == "my-mod-entity" then
    mod_storage.my_entities[entity.unit_number] = {
      unit_number = entity.unit_number,
      surface_index = event.surface_index or entity.surface.index,
      position = entity.position,
      created_tick = event.tick or game.tick
    }
    mod_storage.entity_count = mod_storage.entity_count + 1
  end
end

for _, event_id in ipairs(built_events) do
  script.on_event(event_id, handle_entity_creation, {{filter = "name", name = "my-mod-entity"}})
end

-- Clean up removed/destroyed entities (covers mined, robot mined, died, and scripts)
local destruction_events = {
  defines.events.on_player_mined_entity,
  defines.events.on_robot_mined_entity,
  defines.events.on_entity_died,
  defines.events.script_raised_destroy
}

local function handle_entity_removal(event)
  local entity = event.entity
  if not entity then return end

  local mod_storage = storage["my-mod-name"]
  if mod_storage and mod_storage.my_entities[entity.unit_number] then
    mod_storage.my_entities[entity.unit_number] = nil
    mod_storage.entity_count = mod_storage.entity_count - 1
  end
end

for _, event_id in ipairs(destruction_events) do
  script.on_event(event_id, handle_entity_removal, {{filter = "name", name = "my-mod-entity"}})
end

-- Timed processing (stateful batch iterator)
-- Uses next() to persist hash pointer across ticks.
-- Resolves unit_number → LuaEntity via game.get_entity_by_unit_number()
-- and garbage-collects orphaned entries when entities are invalidated.
script.on_event(defines.events.on_tick, function(event)
  local mod_storage = storage["my-mod-name"]
  if not mod_storage then return end

  local batch_size = 50
  local current_key = mod_storage.iterator_keys.my_entities

  -- Guard: If the tracked key was deleted externally, reset iterator to beginning
  if current_key and not mod_storage.my_entities[current_key] then
    current_key = nil
  end

  for _ = 1, batch_size do
    local key, entity_data = next(mod_storage.my_entities, current_key)
    if not key then
      -- Wrapped around the full table — reset and stop
      mod_storage.iterator_keys.my_entities = nil
      return
    end

    local entity = get_entity(key)
    if entity and entity.valid then
      -- Process entity safely
      -- entity_data contains { unit_number, surface, position, created_tick }
      current_key = key
    else
      -- Entity destroyed externally — garbage collect the orphaned entry
      mod_storage.my_entities[key] = nil
      mod_storage.entity_count = mod_storage.entity_count - 1
      -- Do NOT advance current_key to key, as key was deleted.
      -- current_key remains the last valid key (or nil) for the next next() call.
    end
  end

  mod_storage.iterator_keys.my_entities = current_key
end)

-- ============================================
-- Remote Interface
-- ============================================
remote.add_interface("my_mod_api", {
  get_version = function()
    return "1.0.0"
  end,

  get_entity_data = function(unit_number)
    local mod_storage = storage["my-mod-name"]
    if not (mod_storage and mod_storage.my_entities[unit_number]) then return nil end
    return table_deepcopy(mod_storage.my_entities[unit_number])
  end,

  get_entity_count = function()
    local mod_storage = storage["my-mod-name"]
    return mod_storage and mod_storage.entity_count or 0
  end
})

-- ============================================
-- Settings Helpers
-- ============================================
local function get_setting(name)
  local setting = settings.global[name]
  if not setting then return nil end
  return setting.value
end

local function get_player_setting(player_index, name)
  local player = game.get_player({index = player_index})
  if not player then return nil end
  local setting = settings.get_player_settings(player)[name]
  if not setting then return nil end
  return setting.value
end
