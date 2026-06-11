# Factorio Modding — Research Protocol & Zero-Assumption Development

## The Zero-Assumption Principle

**Never assume — always verify.**

Factorio's modding API evolves constantly. What worked in 1.1 may be deprecated, renamed, or removed in 2.0. What a third-party mod does may change between versions. What a forum post says may be outdated.

### What This Means in Practice

| ❌ Bad (Assumption) | ✅ Good (Verification) |
|---------------------|----------------------|
| "I think this method takes positional args" | Check the runtime API docs for the exact signature |
| "This prototype field probably exists" | Check `wube/factorio-data` or prototype API docs |
| "This mod exposes that remote call" | Check `remote.interfaces["mod_name"]["function"]` before calling |
| "This setting will be there" | Validate settings with type checking and fallback values |
| "This entity will be on Nauvis" | Use `entity.surface`, never hardcode `game.surfaces[1]` |
| "This key exists in storage" | Use `storage.key or default` pattern |
| "This event will have this field" | Check runtime API docs for the event's parameter table |

---

## Research Workflow

When you encounter an unknown API, prototype, behavior, or error:

### Step 1: RTFM (Read The Factorio Manual)

Always start here:

```
https://lua-api.factorio.com/latest
```

| What you need | Which docs |
|---------------|------------|
| Event parameters, runtime methods, game objects | [Runtime API](https://lua-api.factorio.com/latest/index-runtime.html) |
| Prototype structure, fields, mandatory values | [Prototype API](https://lua-api.factorio.com/latest/index-prototype.html) |
| Mod structure, file layout, helper functions | [Auxiliary API](https://lua-api.factorio.com/latest/index-auxiliary.html) |
| All prototype types that exist in the game | [data.raw Wiki](https://wiki.factorio.com/Data.raw) |
| What base game prototypes look like | [wube/factorio-data](https://github.com/wube/factorio-data) |

**Pro tip:** Use the search function in the API docs. Every page has JSON definitions at the bottom showing full structure.

### Step 2: Search Factorio Resources

If the API docs don't answer your question:

1. **Search the official Factorio forums**: `site:forums.factorio.com [your-topic]`
2. **Search Reddit**: `site:reddit.com/r/factorio [your-topic]`
3. **Search the Factorio Wiki**: `site:wiki.factorio.com [your-topic]`
4. **Search GitHub**: `site:github.com factorio [your-topic]`
5. **Search existing mods on the portal**: Check how other mods implement similar features

### Step 3: Search the Web

When Factorio-specific sources aren't enough:

1. **Web search for Lua patterns**: `lua 5.2 [technique]` — Factorio uses Lua 5.2.1
2. **Web search for specific error messages**: Include "Factorio" in the query
3. **Check the Factorio GitHub issue tracker** for known bugs or feature requests
4. **Use web search with `websearch` tool**: `feature: websearch` — trigger with phrases like "search", "look up", "find", "investigate", "research"

### Step 4: Verify Before Using

Before writing code that uses a researched API or pattern:

1. Confirm the API method exists in the **latest** runtime/prototype docs
2. Check the parameter table format (2.0+ uses named tables for many functions)
3. Verify the return types match what you expect
4. Test edge cases: nil values, empty tables, invalid indices

---

## Research Decision Tree

```
Need to use an API/prototype/behavior?
│
├─ Is it in the Lua API docs?
│  ├─ YES → Use it, verify signature matches
│  └─ NO →
│      ├─ Is it a base game prototype?
│      │  ├─ YES → Check wube/factorio-data
│      │  └─ NO →
│      │      ├─ Is it a common community pattern?
│      │      │  ├─ YES → Search forums/Reddit
│      │      │  └─ NO →
│      │      │      └─ Web search with "Factorio 2.0" prefix
│      │      └─ Still unclear?
│      │         └─ Search Reddit, forums, GitHub issues
│
Got conflicting information?
│
├─ Official API docs > wube/factorio-data > forums > Reddit > mod source code
└─ If still conflicting → test in-game with a minimal script
```

---

## Web Research Commands

When you need external research during Factorio modding:

| What you need | Command trigger |
|---------------|-----------------|
| API method or event details | `websearch: Factorio 2.0 [method name]` |
| Prototype field structure | `websearch: Factorio API [prototype type]` |
| Error message debugging | `websearch: Factorio [error message]` |
| Community patterns | `websearch: Factorio modding [pattern]` |
| Lua technique | `websearch: Lua 5.2 [technique]` |
| Check if something is a known bug | `websearch: factorio bug [behavior]` |

**Always cite your sources** — if you found the answer in a forum post, GitHub issue, or API docs, mention where so the developer can verify.

---

## Safe Exploration Patterns

When testing unknown behavior:

```lua
-- Safe logging for API exploration
local function explore_api()
  -- Log the type and contents of an unknown value
  log("Entity type: " .. tostring(entity.type))
  log("Entity name: " .. tostring(entity.name))

  -- Check if a method exists before calling
  if entity.some_method then
    local result = entity.some_method()
    log("Result type: " .. type(result))
  end

  -- Safely iterate unknown table
  if type(some_table) == "table" then
    for k, v in pairs(some_table) do
      log(tostring(k) .. " => " .. tostring(v))
    end
  end
end
```

**Never commit exploratory code.** Use a dedicated debug switch:

```lua
local DEBUG = false -- set to true during exploration, false before release
if DEBUG then
  helpers.write_file("debug-output.txt", helpers.table_to_json(data) .. "\n", true)
end
```

---

## Source Authority Hierarchy

When multiple sources conflict, trust in this order:

1. **Official Factorio Lua API docs** (latest) — authoritative
2. **wube/factorio-data GitHub repo** — base game source of truth
3. **In-game testing with `log()`** — empirical evidence
4. **Official Factorio changelogs** — confirms what changed
5. **Factorio forums** (modding section) — developer-verified answers
6. **Unofficial Factorio Wiki** — community-maintained
7. **Reddit r/factorio** — wider community knowledge
8. **Third-party mod source code** — check license before reading!

**When in doubt, test in-game.** A 10-line test script in `control.lua` is faster and more reliable than guessing.
