# DMR Dual-Compat 2.0 + 2.1 — Worked Example (v3.5.0)

Date: 2026-08 (session after v3.5.0 release attempt)
Mod: Dark Matter Replicators Reborn
Problem: mod declared `factorio_version: "2.1"` with `categories = {...}` recipes failed to load on Factorio 2.0 with:

```
Error in assignID: item with name 'dmrsa-replication-lab' does not exist.
At ROOT.recipe.dmrsa-replication-lab.results[0].name
Source: dmrsa-replication-lab (recipe).
```

## Root cause

Factorio 2.0 does not know the `categories` (array) recipe field — that was introduced in 2.1 (renamed from `category` string). A recipe prototype defined with an unknown field is rejected at data stage, which cascades: the recipe never registers its item result, and assignID reports the item as missing. The error message is misleading — it points at the item, but the real failure is the recipe field format.

## Fix — version detection helper

`defines.lua` (loaded first via `require("defines")` in every data-stage file):

```lua
function dmrsa_is_v21()
    if not data or not data.raw or not data.raw.recipe then return false end
    local iron_plate = data.raw.recipe["iron-plate"]
    if iron_plate then return iron_plate.categories ~= nil end
    for _, recipe in pairs(data.raw.recipe) do
        if recipe.categories then return true end
    end
    return false
end
```

Detects version from base game data rather than hardcoding. Must be called AFTER `data.raw.recipe` is populated (i.e. inside generate(), not at defines.lua top level).

## Changes across the mod

1. **info.json**: `"factorio_version": "2.1"` → `"2.0"` (2.0 is a MINIMUM; a 2.0-declared mod loads on 2.1 too)

2. **dynamic-generator.lua** recipe construction — branch on version:
   ```lua
   local repl_recipe = { type = "recipe", name = recipe_name, ... }  -- no category field yet
   if dmrsa_is_v21() then
       repl_recipe.categories = { category }
   else
       repl_recipe.category = category
   end
   ```

3. **cost-solver.lua `recipe_has_category()`** — handle both formats (2.0 string, 2.1 array):
   ```lua
   local function recipe_has_category(recipe, cat)
       if recipe.categories then
           for _, c in ipairs(recipe.categories) do
               if c == cat then return true end
           end
       end
       if recipe.category == cat then return true end
       return false
   end
   ```

4. **cost-solver.lua machine-efficiency detection** — read either format:
   ```lua
   local recipe_categories = recipe.categories
   if not recipe_categories and recipe.category then
       recipe_categories = { recipe.category }
   end
   if not recipe_categories and recipe.normal then
       recipe_categories = recipe.normal.categories
       if not recipe_categories and recipe.normal.category then
           recipe_categories = { recipe.normal.category }
       end
   end
   ```

## Debugging technique that found this (no PC needed)

The mod uses `safe_require` in data.lua which swallows per-file load errors via pcall. A runtime error in any data-stage file is silently logged and loading continues → assignID fails later with a misleading message. To surface the REAL failing file without launching Factorio, simulate the data stage with `lupa` (LuaJIT for Python):

```bash
pip install --user --break-system-packages lupa
```

Then in a Python script: preload `lib.helpers` and `defines` via `package.preload`, mock the globals (`settings.startup`, `data.raw`, `mods`, `log`, `data:extend`, `assembler2pipepictures`, `pipecoverspictures`, `defines.direction`, `circuit_connector_definitions`), and `loadfile` each data-stage file under `pcall`/`xpcall` with `debug.traceback`. This isolates exactly which file throws and at which line.

Caveats:
- `execute_code` runs in a different interpreter than `terminal` — install lupa and run the probe via `terminal("python3 << 'PYEOF' ...")`.
- Game prototype libs (`assembler2pipepictures`, `resource-autoplace`, etc.) must be mocked as empty-returning functions; their ABSENCE in the probe is a false positive, not the real error. Confirm the real game has them (e.g. check wube/factorio-data for `assembler2pipepictures` in `base/prototypes/entity/assembler-pictures.lua`) before trusting a probe failure on those lines.
- `data:extend` mock should be a Python callable that records what was extended (Lua tables come through as lupa table objects — inspect via `lua.table` APIs, not Python dict indexing).

## Zip packaging note

Portal requires the inner folder = mod name (`dark-matter-replicators-reborn/`) inside the zip, not files at root and not a versioned folder name. Verify `info.json` sits at `<mod-name>/info.json`. See skill SKILL.md → "Package for portal upload".
