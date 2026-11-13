# Proving a player-visible prototype feature at runtime (probe A/B)

Requests like "make it wireable / connectable / settable by circuit" are usually ONE MISSING
PROTOTYPE FIELD, not missing logic. Work this sequence before writing Lua.

## 1. Diff the field against a vanilla peer

Query `script-output/data-raw-dump.json` (from `--dump-data`) for your entity AND for the vanilla
entity of the same type. An absent field means its DEFAULT (0 = feature off), so the absence IS
the diagnosis — a dump that "looks clean" proves nothing. Example: base's assembling-machine
peers declare `circuit_wire_max_distance = 9`; a machine without it cannot take a circuit wire
at all.

## 2. A/B it with a throwaway probe mod

Build the harness once per investigation:

```text
/tmp/<x>/config.ini        [path] read-data=<factorio-install>/../../data  write-data=/tmp/<x>/wd
/tmp/<x>/mods/<yourmod>/   copy of the mod under test
/tmp/<x>/mods/probe_0.0.1/ info.json + control.lua
```

`control.lua` (no `data.lua` needed):

```lua
script.on_init(function()
    local e = game.surfaces[1].create_entity{
        name = "<entity>", position = { 0.5, 0.5 }, force = game.forces.player }
    local ok, err = pcall(function() --[[ call the API under test ]] end)
    log("[PROBE] ok=" .. tostring(ok) .. " err=" .. tostring(err))
    e.destroy()
end)
```

Run and read:

```bash
<factorio>/bin/x64/factorio --config config.ini --mod-directory mods --create a.zip
grep '\[PROBE\]' wd/factorio-current.log
```

Run it against UNPATCHED and PATCHED source (two directories): the difference between the two
logs is the feature. `luac5.2 -p` + headless `--create` still gate the release, but they only
prove the mod LOADS.

## 3. Read the operation's return value, not the absence of an error

A rejected API call usually returns `false`/nil without raising, so "nothing crashed" proves
nothing. Wrap probe calls in `pcall` too: data-stage fields are not all present at runtime —
`recipe.category` throws `LuaRecipePrototype doesn't contain key category` from `control.lua`
although it exists in `data.lua`.

## 4. An object existing != the feature working

`get_wire_connector()` hands back a connector even when `circuit_wire_max_distance = 0`; only
`connect_to()`'s return value tells the truth. Never cite "the handle is there" as proof a
machine is wireable.

## 5. Check what a runtime script already owns

If `control.lua` rewrites a value on a timer (a refiner re-pointing its recipe at the quality of
the item inside it), a player-set value gets snapped back on the next tick. Expose only what the
script does not fight — enable/disable, read contents/recipe — and state the limit in the
changelog instead of shipping a control that loses.

## What one field buys on assembling machines

`circuit_wire_max_distance = 9` alone (no `control_behavior` block required) enables
enable/disable via `circuit_condition`, `get_circuit_network`, and `set_recipe()` of the
machine's own recipes; the circuit "set recipe" mode selects by product, so the recipes must
exist under stable item-derived names for a parameterized blueprint to drive them.
