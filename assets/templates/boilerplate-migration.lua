-- boilerplate-migration.lua
-- Semantic Migration Pipeline for Factorio 2.0 / Space Age
-- Manages schema versions and storage layout transformations.

local MigrationManager = {}

-- Define mod name (replace with your actual mod name)
local MOD_NAME = "my-mod-name"

-- Accumulative sequence of migrations
-- Keys are target semantic versions (must be strictly sequential)
local migrations = {
  ["1.1.0"] = function(mod_storage)
    log("Applying storage migration for version 1.1.0")
    -- Example transformation: migrate legacy layout
    if mod_storage.my_entities then
      -- Perform structural changes, table re-indexing, etc.
    end
  end,
  
  ["1.2.0"] = function(mod_storage)
    log("Applying storage migration for version 1.2.0")
    -- Example transformation: add new structures
    mod_storage.new_feature_state = {}
  end
end

--- Simple semantic version comparison helper (assumes standard major.minor.patch)
-- @param v1 string First version
-- @param v2 string Second version
-- @return boolean True if v1 < v2
local function version_less_than(v1, v2)
  local function parse_version(v)
    local parts = {}
    for part in string.gmatch(v, "%d+") do
      table.insert(parts, tonumber(part))
    end
    return parts
  end

  local p1 = parse_version(v1)
  local p2 = parse_version(v2)

  for i = 1, math.max(#p1, #p2) do
    local n1 = p1[i] or 0
    local n2 = p2[i] or 0
    if n1 < n2 then return true end
    if n1 > n2 then return false end
  end
  return false
end

--- Execute the migration checks
-- @param event_data table Event payload from on_configuration_changed
function MigrationManager.run(event_data)
  local changes = event_data.mod_changes and event_data.mod_changes[MOD_NAME]
  if not changes then return end

  local old_version = changes.old_version
  local new_version = changes.new_version

  -- Case A: Newly installed mod in an existing save
  if not old_version then
    log("Mod " .. MOD_NAME .. " newly installed. Skipping migrations, schema initialized.")
    return
  end

  -- Case B: Mod update detected, perform migration sequence
  local mod_storage = storage[MOD_NAME]
  if not mod_storage then return end

  log("Checking migrations for " .. MOD_NAME .. " from " .. old_version .. " to " .. new_version)

  -- Gather and sort target migration versions
  local versions = {}
  for v in pairs(migrations) do
    table.insert(versions, v)
  end
  
  table.sort(versions, function(a, b)
    return version_less_than(a, b)
  end)

  -- Run migrations sequentially
  for _, version in ipairs(versions) do
    -- If old_version < version <= new_version
    if version_less_than(old_version, version) and not version_less_than(new_version, version) then
      log("Running migration " .. version .. " for " .. MOD_NAME)
      
      -- Wrap in pcall to isolate errors and prevent game crashes/desyncs
      local success, err = pcall(migrations[version], mod_storage)
      if not success then
        error("CRITICAL: Failed to apply migration " .. version .. " on " .. MOD_NAME .. ": " .. tostring(err))
      end
    end
  end
end

return MigrationManager
