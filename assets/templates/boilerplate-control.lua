-- control.lua
-- Generated from factorio-modding skill template
-- Factorio 2.0 / Space Age compatible

-- ============================================
-- Module-scope caching (Locality of Reference)
-- ============================================
local pairs = pairs
local get_entity = game.get_entity_by_unit_number
local get_player = game.get_player

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
  storage.players = {}
  storage.my_entities = {}
  debug_log("Mod initialized")
end)

script.on_load(function()
  -- Re-register metatables if any
  -- script.register_metatable("my_class", my_class_metatable)
  debug_log("Mod loaded")
end)

script.on_configuration_changed(function(data)
  -- Handle mod version migrations
  -- Check data.mod_changes to determine what changed
  debug_log("Configuration changed")
end)

-- ============================================
-- Event Handlers
-- ============================================

-- Track placed entities
script.on_event(defines.events.on_built_entity, function(event)
  local entity = event.entity
  if not (entity and entity.valid) then return end

  if entity.name == "my-mod-entity" then
    storage.my_entities[entity.unit_number] = {
      unit_number = entity.unit_number,
      surface = entity.surface.name,
      position = entity.position,
      created_tick = game.tick
    }
  end
end, {{filter = "name", name = "my-mod-entity"}})

-- Clean up mined entities
script.on_event(defines.events.on_player_mined_entity, function(event)
  local entity = event.entity
  if entity and storage.my_entities[entity.unit_number] then
    storage.my_entities[entity.unit_number] = nil
  end
end, {{filter = "name", name = "my-mod-entity"}})

-- Timed processing (stateful batch iterator)
-- Uses next() to persist hash pointer across ticks.
-- Resolves unit_number → LuaEntity via game.get_entity_by_unit_number()
-- and garbage-collects orphaned entries when entities are invalidated.
script.on_event(defines.events.on_tick, function(event)
  local batch_size = 50
  storage.iterator_keys = storage.iterator_keys or {}
  local current_key = storage.iterator_keys.my_entities

  for _ = 1, batch_size do
    local key, entity_data = next(storage.my_entities, current_key)
    if not key then
      -- Wrapped around the full table — reset and stop
      storage.iterator_keys.my_entities = nil
      return
    end

    current_key = key
    local entity = get_entity(key)
    if entity and entity.valid then
      -- Process entity safely
      -- entity_data contains { unit_number, surface, position, created_tick }
    else
      -- Entity destroyed externally — garbage collect the orphaned entry
      storage.my_entities[key] = nil
    end
  end

  storage.iterator_keys.my_entities = current_key
end)

-- ============================================
-- Remote Interface
-- ============================================
remote.add_interface("my_mod_api", {
  get_version = function()
    return "1.0.0"
  end,

  get_entity_data = function(unit_number)
    if not storage.my_entities[unit_number] then return nil end
    return storage.my_entities[unit_number]
  end,

  get_entity_count = function()
    local count = 0
    for _ in pairs(storage.my_entities) do
      count = count + 1
    end
    return count
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
