---
name: factorio-modding
description: "Trigger: Factorio modding, Lua, prototype, control.lua, data.lua, recipe, technology, desync, migration. Full-stack Factorio 2.0/Space Age modding with zero-assumption, compatibility-first, research-driven development."
license: MIT
metadata:
  author: Jaer985
  version: "2.0"
---

# Factorio Modding API Skill

Runtime contract for developing, debugging, and maintaining Factorio 2.0/Space Age mods.

---

## Activation Contract

Load this skill when working with any of these patterns (file or task context):

| Context | Triggers |
|---------|----------|
| **File patterns** | `**/info.json`, `**/control.lua`, `**/data.lua`, `**/settings.lua`, `**/data-updates.lua`, `**/data-final-fixes.lua`, `**/settings-updates.lua`, `**/settings-final-fixes.lua`, `**/migrations/*.lua`, `**/migrations/*.json` |
| **Task keywords** | `factorio`, `modding`, `prototype`, `recipe`, `technology`, `desync`, `control.lua`, `data.raw`, `planet`, `quality`, `space-platform`, `space-elevator`, `entity-ghost`, `remote.add_interface`, `migration`, `fluidbox`, `collision_mask`, `surface`, `LuaGuiElement`, `script.on_event`, `storage`, `settings.lua`, `locale`, `changelog.txt` |

---

## Hard Rules (NEVER violate these)

### Zero-Assumption Principle
**Never assume — always verify.** Every external dependency, API method, prototype field, event parameter, and data structure MUST be verified against these sources before use:
1. [Factorio Lua API docs](https://lua-api.factorio.com/latest) — runtime, prototype, auxiliary
2. [wube/factorio-data](https://github.com/wube/factorio-data) — base game prototypes
3. [data.raw reference](https://wiki.factorio.com/Data.raw) — complete prototype index
4. Web search for 2.0+ specific behavior when docs are unclear

If you cannot verify a method signature, prototype field, or event parameter via these sources, **stop and research** before writing code.

### Lua Environment (Lua 5.2.1)
- **BANNED**: `os`, `io`, `coroutine`, `dofile`, `loadfile` — will crash the game.
- **Relative requires DISABLED**: use absolute paths: `require("util")`, `require("__mod-name__.folder.file")`.
- **Determinism is LAW**: `pairs()`/`next()` follow insertion order (except first 1024 numeric keys). Never use real-world timers, RNG without `game.create_random_generator()`, or anything that breaks MP determinism.

### Storage & State
- **`storage` NOT `global`**: Factorio 2.0 uses `storage` for persistent state. `global` is legacy.
- **NO `storage` writes in `on_load`**: `on_load` is strictly read-only. Use it only for `script.register_metatable()` and conditional event re-registration.
- **NO file-scope state**: Never store dynamic state in local variables declared at module scope. All mutable state lives in `storage`.

### Data Stage Safety
- **Guard every access**: Always check `if data.raw[type][name] then ... end` before modifying existing prototypes in `data-updates.lua` and `data-final-fixes.lua`.
- **Stage ordering**: `data.lua` → `data-updates.lua` → `data-final-fixes.lua`. Understand what runs where.
- **Tech/Recipe resets**: Do NOT run `force.reset_recipes()` or `force.reset_technologies()` manually — Factorio 2.0 engine handles this on migrations.

### Desync Prevention
- Identical event registration across all clients — if conditional, recreate identically in `on_load` from `storage`.
- Use deterministic `math.random()` or `game.create_random_generator()`.
- No I/O, no real-world clocks, no non-deterministic branching.
- Event filters (`script.on_event` with filter tables) are MANDATORY for high-frequency events.

### Compatibility & Licensing
- **License check first**: Before reading/modifying external mod code, check `info.json` `license` field and any `LICENSE` file.
- **All Rights Reserved / Proprietary**: Do NOT copy or modify source. Interact ONLY via public remote interfaces.
- **Open Source**: Comply with the specific license (MIT, Apache, GPL, etc.). Preserve copyright notices.
- **Safe inter-mod calls**: Always check `remote.interfaces[interface_name]` before calling another mod's API.
- **Namespace ALL names**: Prefix every prototype name, setting, remote interface, and locale key with your mod name to avoid collisions.

### UPS Performance
- **Event filtering**: Use filter tables in `script.on_event` for `on_built_entity`, `on_player_mined_entity`, etc.
- **Throttle `on_tick`**: If unavoidable, execute every N ticks: `if event.tick % 60 == 0 then`.
- **Minimize `on_tick` scope**: Never iterate all entities every tick. Use `storage` for state tracking.

---

## Decision Gates

| Situation | Action |
|-----------|--------|
| Need to use an API method or prototype field | **STOP** → Verify signature in [Lua API docs](https://lua-api.factorio.com/latest) before writing code |
| Modifying another mod's prototype | **STOP** → Check license, verify prototype exists, use `data-updates.lua` not `data.lua` |
| Error or unexpected behavior | **STOP** → Read `log()` output, check `script-output/` files, search factorio.com bug reports |
| Performance concern | **STOP** → Profile with in-game time commands, apply event filtering, throttle ticks |
| Migration needed | Use JSON rename migration for simple renames. Use Lua migration script only for complex `storage` transforms |
| Adding a dependency on another mod | Use optional dependency `"? mod-name"` unless truly required. Guard all interop calls |
| Unsure about 2.0 vs legacy API | **STOP** → Research [changelog](https://factorio.com/blog/) or API docs. 2.0 changed many signatures to single-table args |
| Writing GUI code | Use `player.gui.relative` for attached UIs. Always verify `player.controller_type` before accessing GUI |
| Working with surfaces | Never hardcode `game.surfaces[1]`. Use `entity.surface`, `event.surface_index`, `surface.platform` for space platforms |

---

## Execution Steps

When implementing, modifying, or debugging a Factorio mod:

### Phase 1: Context & Requirements
1. Read `info.json` — note mod name, version, factorio_version, dependencies, license.
2. Read existing stage files: `data.lua`, `data-updates.lua`, `data-final-fixes.lua`, `control.lua`, `settings.lua`.
3. Read existing `migrations/` and `locale/` for context.
4. Identify which stage(s) the new code belongs to (data vs control).

### Phase 2: Research & Verification
1. For every prototype type/field you plan to use → verify in [prototype docs](https://lua-api.factorio.com/latest/index-prototype.html).
2. For every runtime method/event → verify in [runtime docs](https://lua-api.factorio.com/latest/index-runtime.html).
3. For existing prototype references → check [wube/factorio-data](https://github.com/wube/factorio-data).
4. If behavior is unclear → web search for "Factorio 2.0 [topic]" or check the [forums](https://forums.factorio.com/).

### Phase 3: Implementation
1. Follow the stage ordering: settings → data → data-updates → data-final-fixes → locale → control.
2. Prefix ALL custom prototypes and settings with your mod name.
3. Add locale entries for EVERY custom prototype, setting, and named entity.
4. Add migrations for any rename or storage structure change.
5. Update `changelog.txt` with the change.

### Phase 4: Verification
1. Check for common errors: nil access on `data.raw`, missing locale keys, unguarded inter-mod calls.
2. Verify desync safety: no `storage` writes in `on_load`, deterministic-only operations.
3. Verify UPS profile: filtered events, throttled ticks, no global iteration.
4. Check `log()` output for warnings.

---

## Output Contract

When finishing Factorio modding work, return:
- **Files modified/created** — list with paths and summary of each change.
- **Stage** — which stage(s) were affected (data, control, settings, locale, migrations).
- **Verification notes** — desync safety, UPS impact, compatibility checks performed.
- **Risks** — known edge cases, inter-mod conflicts, missing locale entries, untested surfaces.
- **Research done** — what was verified against official docs, what was researched externally.

---

## References

All detailed patterns, examples, and deep dives are in `references/`:

| File | Covers |
|------|--------|
| `references/01-patterns.md` | All code patterns: boilerplate, prototypes, GUIs, remote interfaces, migrations |
| `references/02-troubleshooting.md` | Debugging, error patterns, desync hunting, log analysis |
| `references/03-compatibility.md` | Inter-mod compatibility, safe interop, namespace conventions |
| `references/04-research-protocol.md` | Zero-assumption deep dive, web research workflow |
| `references/05-lua-performance.md` | Factorio-specific Lua optimization, UPS tuning |
| `references/06-cpp-engine.md` | C++ engine additions in 2.0, API changes, migration from 1.1 |
| `assets/templates/` | Boilerplate: control.lua, data.lua, settings.lua, info.json |

### Authoritative Sources
- [Factorio Lua API (latest)](https://lua-api.factorio.com/latest) — Start here for ALL API questions
- [Prototype API Reference](https://lua-api.factorio.com/latest/index-prototype.html)
- [Runtime API Reference](https://lua-api.factorio.com/latest/index-runtime.html)
- [Auxiliary API & Mod Structure](https://lua-api.factorio.com/latest/index-auxiliary.html)
- [wube/factorio-data](https://github.com/wube/factorio-data) — Base game prototype definitions
- [data.raw Wiki](https://wiki.factorio.com/Data.raw) — Complete prototype type index
- [Lua 5.2 Reference Manual](https://www.lua.org/manual/5.2/)
- [Factorio Changelogs](https://factorio.com/blog/) — Track 2.0+ changes
- [Factorio Modding Forum](https://forums.factorio.com/viewforum.php?f=25)
- [Unofficial Factorio Modding Wiki](https://wiki.factorio.com/Modding)
