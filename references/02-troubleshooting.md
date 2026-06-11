# Factorio Modding — Troubleshooting & Debugging

Structured approach to finding and fixing errors in Factorio mods.

---

## Debugging Tools

### 1. `log()` — Your Primary Tool

```lua
log("MyMod: entering on_built_entity handler")
log("MyMod: entity name = " .. tostring(entity.name))
log("MyMod: storage state = " .. serpent.line(storage))
```

**Where to find logs:**
- Windows: `%APPDATA%/Factorio/script-output/` (for `helpers.write_file`)
- Windows: `%APPDATA%/Factorio/factorio-current.log` (for `log()` output)
- Linux: `~/.factorio/script-output/` and `~/.factorio/factorio-current.log`
- macOS: `~/Library/Application Support/factorio/script-output/` and `factorio-current.log`

### 2. `helpers.write_file()` — For Complex Data

```lua
-- Write Lua table as JSON to script-output/
helpers.write_file("my-mod-debug.json", helpers.table_to_json(data), false)

-- Append mode for continuous logging
helpers.write_file("my-mod-debug.log", "Tick " .. game.tick .. ": " .. message .. "\n", true)
```

### 3. In-Game Commands

```
/c game.player.print("MyMod: " .. serpent.line(storage))
/c for k, v in pairs(storage) do game.player.print(k .. " = " .. tostring(v)) end
/c game.player.print(tostring(remote.interfaces["my_mod_name"]))
```

**Enable commands:** `/c` requires the mod to have `"enable_pvp"` in `info.json` (lame, won't work from a mod). Use `/c` in single-player or as admin.

### 4. Lua REPL via Command

```
/c local function dump(t) for k,v in pairs(t) do game.player.print(k.."="..tostring(v)) end end
```

Don't commit REPL commands — they're for interactive debugging only.

---

## Common Error Categories

### Category 1: Data Stage Crashes

**Error: `Error while running on_init: ... entity name is nil`**
→ Prototype not registered. Check `data.lua` / `data-updates.lua` for `data:extend()`.
→ Mismatched name between `data.lua` and `info.json` dependencies.

**Error: `Unknown prototype type: "xyz"`**
→ Misspelled prototype type. Check [prototype types](https://lua-api.factorio.com/latest/index-prototype.html).
→ Common misspellings: `"assembling-machine"` (not `"assembler"`), `"mining-drill"` (not `"miner"`).

**Error: `Table contains no values` in data:extend()**
→ Empty table passed to `data:extend({})`. All prototypes were filtered out by guards.
→ Check `if` conditions that may have falsely skipped all entries.

**Error: `Unknown key: "some_field"` (during startup)**
→ Prototype field doesn't exist for this type. Remove it or check the correct field name.
→ Factorio 2.0 is strict about unknown keys in prototypes.

### Category 2: Control Stage Errors

**Error: `attempt to index a nil value`**
→ Most common error. Something is `nil` that shouldn't be.
→ Accessing `data.raw[type][name]` that doesn't exist → add guard.
→ Accessing `event.entity` that was already removed → check `.valid`.
→ Accessing `storage[key]` before initialization → use `storage[key] or default`.

**Error: `attempt to call a nil value`**
→ Function doesn't exist. Misspelled method or method is 2.0-only.
→ Remote interface doesn't exist: check `remote.interfaces[name]` before calling.

**Error: `Unknown event ID` or `Invalid event filter`**
→ Event ID not valid for this Factorio version. Check `defines.events`.
→ Event filter uses wrong format. Check [event filtering API](https://lua-api.factorio.com/latest/events.html).

### Category 3: Desyncs

**Symptom: Game desyncs only in multiplayer**

| Cause | Solution |
|-------|----------|
| `storage` writes in `on_load` | `on_load` is READ ONLY. Move writes to `on_init` or event handlers |
| Conditional event registration | Re-register events identically in `on_load` based on `storage` values |
| Non-deterministic iteration | `pairs()` is deterministic in Lua 5.2 for tables without numeric keys, but beware of custom `__pairs` metamethods |
| Using `math.random()` without seed | Factorio seeds it deterministically, but calling it at different times on different clients breaks determinism |
| Reading filesystem or real-time clock | `os.clock()`, `os.time()`, file I/O are BANNED |
| Entity iteration order differs | Never rely on the order entities are returned — sort or use a deterministic key |

**Desync hunting:**
1. Enable desync logging in config: `write-desync-data=true` in `config/config.ini`
2. Load the desync dump in single-player
3. Compare `storage` contents between the desynced clients
4. Add `log()` calls at strategic points to trace state divergence

### Category 4: GUI Errors

**Error: `LuaGuiElement is nil`**
→ Element was destroyed but code still holds reference.
→ Player logged out and their GUI was cleaned up.
→ Check `.valid` before operating on any GUI element:
```lua
if player.gui.screen["my-frame"] and player.gui.screen["my-frame"].valid then
  -- operate
end
```

**Error: `Cannot add child of type X to parent of type Y`**
→ Wrong element hierarchy. Check [LuaGuiElement types](https://lua-api.factorio.com/latest/LuaGuiElement.html).
→ Common mistake: adding a `table` to a `frame` vs adding to a `flow`.

**Error: `Style not found: my_custom_style`**
→ Style not registered in `style.lua` or prototype styles.
→ Check if style name is spelled correctly in both definition and usage.

### Category 5: Migration Errors

**Error: `Error while running migration`**
→ Migration script references prototype or entity that doesn't exist in this save.
→ Use guarded access: `if game.surfaces["nauvis"] then ... end`.
→ Migration ran twice (missing version guard).

**Error: `storage key doesn't exist`**
→ Migration assumes a key was created by an earlier version.
→ Always guard: `if storage.my_key then ... end`.

---

## Debugging Flowchart

```
Mod crashing?
│
├─ When does it crash?
│  ├─ On load/startup → DATA STAGE issue
│  │  ├─ Prototype definition wrong
│  │  ├─ data.lua/data-updates.lua syntax error
│  │  ├─ Missing locale key (warning, not crash)
│  │  └─ Dependency missing
│  │
│  ├─ On save load → MIGRATION or STORAGE issue
│  │  ├─ Migration script error
│  │  ├─ Storage structure mismatch
│  │  └─ Missing migration file
│  │
│  └─ On specific action → CONTROL STAGE issue
│     ├─ Event handler error
│     ├─ GUI interaction error
│     └─ Remote interface error
│
├─ What does the log say?
│  ├─ Read factorio-current.log
│  ├─ Search for "Error while running" or "Warning"
│  ├─ Check script-output/ for your debug files
│  └─ Match the line number to your code
│
└─ How to reproduce?
   ├─ Minimal test case in isolated world
   ├─ Disable other mods to isolate conflict
   └─ Step-by-step replication
```

---

## Debug Mode Pattern

Use a global debug toggle in your mod:

```lua
-- At the top of control.lua
local DEBUG = false -- Toggle for development

-- Debug helper
local function debug_log(...)
  if not DEBUG then return end
  log("MyMod: ", ...)
end

-- Debug write helper
local function debug_dump(filename, data)
  if not DEBUG then return end
  helpers.write_file("my-mod/" .. filename, helpers.table_to_json(data) .. "\n", true)
end
```

**Never ship with DEBUG = true.** Set it to `false` before release.

---

## Common Factorio 2.0 Breaking Changes

| 1.1 Pattern | 2.0 Pattern | Symptom if wrong |
|---|---|---|
| `global` table | `storage` table | Data lost on save/reload |
| Positional args | Single-table args | `nil` errors on method calls |
| Old collision_mask format | New `layers` dictionary | Collision not working |
| `force.reset_recipes()` | Auto-handled by engine | Duplicate reset errors |
| `game.get_player()` | `game.get_player(index)` — takes table | Error in 2.0.7+ |
| `entity.orderup()` removed | Use `entity.teleport()` | "attempt to call nil value" |
| `script.on_event` with filters | Updated filter format | Filter silently ignored |
| `on_pre_build` event | Replaced by `on_entity_created` | Event not firing |

---

## Profiling Performance

In-game commands to measure UPS impact:

```
/c local s = game.tick; for i = 1, 1000 do -- your_operation end; game.print((game.tick - s) .. " ticks")
/c game.print(serpent.line(game.get_script_time()))
```

**Offline profiling:** Use the [Factorio Mod Debug](https://mods.factorio.com/mod/debugger) mod or the in-game debug overlay (F4 → show-time-usage).

**Always profile with representative entity counts.** A mod that's fine with 100 entities may destroy UPS with 10,000.
