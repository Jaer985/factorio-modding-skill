# Factorio Modding — Compatibility & Inter-Mod Patterns

Preventing and managing conflicts between mods.

---

## The Golden Rule of Mod Compatibility

**Your mod is not the only mod.**

Players use 50+ mods simultaneously. Every assumption you make about "how the world works" will be broken by some other mod. Design for coexistence from day one.

---

## Namespace Everything

Every prototype, setting, remote interface, and locale key MUST be prefixed with your mod name.

```lua
-- ❌ BAD: generic name, WILL conflict
data:extend({
  type = "item", name = "super-drill",
  type = "recipe", name = "super-drill",
})

-- ✅ GOOD: namespaced
data:extend({
  type = "item", name = "my-mod-super-drill",
  type = "recipe", name = "my-mod-super-drill",
})
```

**What to namespace:**
- Prototype names (`item`, `recipe`, `entity`, `technology`, `fluid`, etc.)
- Setting names (`settings.lua` — all `name` fields)
- Remote interface namespaces (`remote.add_interface("my_mod_api", ...)`)
- GUI element names (`player.gui.screen["my-mod-frame"]`)
- Locale keys (they're auto-namespaced by mod name, but be explicit)
- Custom event IDs (use `script.generate_event_name()`)
- `storage` table keys

---

## Dependency Management

### Dependency Syntax in info.json

| Syntax | Meaning |
|--------|---------|
| `"base >= 2.0"` | Required: base game version 2.0 or higher |
| `"my-mod"` | Required: specific mod |
| `"? my-mod"` | Optional: use it if present, skip if not |
| `"(?) my-mod"` | Optional + hidden: don't show in dependency list |
| `"! my-mod"` | Incompatible: crash if both are enabled |
| `"~ my-mod"` | Load after this mod |

### Choosing the Right Dependency Level

```json
{
  "dependencies": [
    "base >= 2.0",
    "? space-age >= 2.0",
    "? my-optional-compat-mod >= 1.0.0"
  ]
}
```

- **Hard dependency** (`"mod-name"`): Only when your mod LITERALLY doesn't function without it.
- **Optional dependency** (`"? mod-name"`): When your mod has enhanced features but works without it.
- **Incompatible** (`"! mod-name"`): When the combination is known to crash or conflict with no workaround. Avoid when possible.

### Stage Loading Order

```
base (settings) → mod A (settings) → mod B (settings) →
base (data) → mod A (data) → mod B (data) →
base (data-updates) → mod A (data-updates) → mod B (data-updates) →
base (data-final-fixes) → mod A (data-final-fixes) → mod B (data-final-fixes)
```

**Use `data-updates.lua` for compatibility-focused changes:**
- It runs after all mods' `data.lua`, so all prototypes exist.
- It runs BEFORE `data-final-fixes.lua`, so other mods can override.
- If you MUST have the last word, use `data-final-fixes.lua`.

**Use `(?)` or `~` for load ordering:**
- `"(?) my-mod"` + `"~ my-mod"` ensures your mod loads after another for data stage ordering.

---

## Safe Cross-Mod Interaction Patterns

### Pattern 1: Remote Interface Discovery

```lua
-- Safe remote call pattern
local function call_remote(mod_name, function_name, ...)
  if not remote.interfaces[mod_name] then
    return nil, "mod not present"
  end
  if not remote.interfaces[mod_name][function_name] then
    return nil, "function not available"
  end
  return remote.call(mod_name, function_name, ...)
end

-- Usage
local result, err = call_remote("other-mod-api", "get_data", player_index)
if result then
  -- use result
else
  -- gracefully handle missing mod/function
end
```

### Pattern 2: Event-Based Interop

Instead of direct remote calls, use events for loose coupling:

```lua
-- Mod A fires a custom event
script.raise_event(defines.events.on_custom_event_name, {
  mod_name = "my-mod",
  data = some_data
})

-- Mod B listens (if present)
script.on_event(defines.events.on_custom_event_name, function(event)
  if event.mod_name == "my-mod" then
    -- react to my-mod's event
  end
})
```

### Pattern 3: Signal-Based Communication

Use signal channels for communication between mods:

```lua
-- Write a signal to a global signal channel
storage.signals = storage.signals or {}
storage.signals["my-mod-channel"] = storage.signals["my-mod-channel"] or {}
storage.signals["my-mod-channel"].some_value = 42
```

Document signal channels in your README so other mod authors can use them.

---

## Guard Patterns

### Guarded data-lua Modifications

```lua
-- data-final-fixes.lua
-- NEVER assume a prototype exists

-- Item modification
if data.raw["item"]["iron-plate"] then
  data.raw["item"]["iron-plate"].stack_size = 200
end

-- Recipe modification
if data.raw["recipe"]["iron-plate"] then
  table.insert(data.raw["recipe"]["iron-plate"].ingredients,
    {type = "item", name = "stone", amount = 1})
end

-- Technology modification
if data.raw["technology"]["automation"] then
  data.raw["technology"]["automation"].unit.count = 20
end

-- Entity modification (check full path)
if data.raw["assembling-machine"]["assembling-machine-1"] then
  local machine = data.raw["assembling-machine"]["assembling-machine-1"]
  if machine and machine.crafting_speed then
    machine.crafting_speed = machine.crafting_speed * 1.1
  end
end
```

### Guarded Control Stage

```lua
-- Reading settings safely
local function get_setting(name)
  local setting = settings.global[name]
  if not setting then return nil end
  return setting.value
end

-- Guarded storage access
local function get_player_data(player_index)
  if not storage.players then return nil end
  return storage.players[player_index]
end

-- Entity validity check (ALWAYS)
script.on_event(defines.events.on_built_entity, function(event)
  local entity = event.entity
  if not (entity and entity.valid) then return end
  -- Now safe to use entity
end)

-- Surface existence check
local function get_surface(name)
  local surface = game.surfaces[name]
  if not surface then return nil end
  return surface
end
```

---

## Mod Conflict Detection

### At Mod Load Time

```lua
-- data.lua or data-final-fixes.lua
-- Detect conflicting mods and warn the user
local function detect_conflicts()
  local conflicts = {}

  -- Check for known incompatible mods
  if script.get_mod_setting("conflicting-mod-setting") then
    table.insert(conflicts, "Conflicting mod detected")
  end

  -- Check for mods that modify the same prototypes
  if remote.interfaces["some-other-mod"] then
    log("Warning: MyMod detected some-other-mod which may conflict")
  end

  return conflicts
end
```

### At Runtime

```lua
-- Check if another mod consumed/cancelled our event
script.on_event(defines.events.on_built_entity, function(event)
  local entity = event.entity
  if not (entity and entity.valid) then return end

  -- If using script_raised_built, check for mod interop
  if event.created_by_migration then
    -- Skip migration-spawned entities
    return
  end
end)
```

---

## Compatibility Testing Checklist

Before release, verify:

- [ ] All prototypes are namespaced with mod name
- [ ] All settings are namespaced
- [ ] All remote interfaces are namespaced
- [ ] Every `data.raw` access is guarded
- [ ] Every event handler checks `.valid`
- [ ] Every `storage` access has fallback
- [ ] Every setting read has type validation
- [ ] Optional dependencies use `"? mod-name"` syntax
- [ ] Remote calls check `remote.interfaces` first
- [ ] `data-final-fixes.lua` has no unguarded accesses
- [ ] No hardcoded surface indices
- [ ] Custom event names don't conflict (use `script.generate_event_name()`)
- [ ] Tested with and without optional dependencies
- [ ] Tested with 10+ random mods enabled
- [ ] Tested in multiplayer (if applicable)

---

## Version Compatibility

```json
{
  "factorio_version": "2.0",
  "dependencies": [
    "base >= 2.0",
    "? space-age >= 2.0"
  ]
}
```

- Use `"base >= 2.0"` not `"base = 2.0"` to allow minor updates.
- If your mod works with both base 2.0 and Space Age, use `"? space-age"` to enable enhanced features.
- Never use version ranges unless you've tested those specific versions.

---

## Deprecation & Migration Policy

When renaming or restructuring your mod:

1. **Don't break saves.** Always provide JSON migration for prototype renames.
2. **Don't break other mods.** Keep deprecated remote interfaces working for at least one major version.
3. **Document breaking changes** in `changelog.txt` with **BOLD** markers.
4. **Increment major version** for compatibility-breaking releases.
