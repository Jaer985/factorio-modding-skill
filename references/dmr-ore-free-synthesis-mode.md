# Ore-free / "generate it from electricity" mode (DMR v4.3, generalizable)

Trigger: a request to (a) stop spawning an ore in the world, (b) obtain the
material from power instead, or (c) make research independent of a mod's own
intermediate. Reference implementation: DMR `dmrsa-tenemut-source`
(Ore patches / Ore patches + synthesis / Synthesis only) + the Dark Matter
Synthesizer.

## 1. An ingredient-less recipe is legal — and needs three guards

`RecipePrototype.ingredients` is **optional** in the 2.1 docs, so
`ingredients = {}` is a real "energy only" recipe: an assembling machine runs
it on `energy_required` and pays nothing but electricity. Cost per result is
`energy_usage × energy_required` — a 1 MW machine with `energy_required = 4`
costs 4 MJ per item, against ≈225 kJ per ore for a vanilla electric mining
drill (90 kW × `mining_time` 2.5 s).

Without all three of these, "energy only" means free items:

| Guard | Where | Why |
|---|---|---|
| `hide_from_player_crafting = true` | recipe | an unlocked ingredient-less recipe is **hand-craftable** in the crafting menu → infinite free items. Recipe categories do NOT block hand-crafting. |
| `hidden = true` — only for recipes no player ever selects | recipe | `hidden` removes the recipe from the machine's recipe picker entirely: a machine whose recipes are ALL hidden presents an EMPTY picker and cannot be used at all. `hide_from_player_crafting` is the hand-crafting guard; `hidden` is a different switch with a different victim. |
| `allow_productivity = false` | recipe | productivity modules/beacons multiply a recipe whose input is nothing (same failure class as removing productivity from `allowed_effects`). |
| `module_slots = 0` + `allowed_effects = {}` | entity | `allowed_effects` also governs **beacons** — they key off the effects list, not the slots — so ANY listed effect is amplifiable from outside: `speed` erases the energy cost per item, and `consumption` lets efficiency beacons cut the very draw the cost model is defined on. Leave the list empty unless an effect is part of the design. |

Also set `allow_decomposition = false` (no raw cost exists to decompose) and
`auto_recycle = false`.

## 2. Removing a resource from worldgen without breaking saves

Keep the `resource` prototype in EVERY mode and gate only these four things:

1. `resource.autoplace = nil` (build the spec only when worldgen is on — the
   spec carries `control = <name>`, so...)
2. ...do NOT ship the `autoplace-control` prototype while the spec is absent
   (control-without-spec is harmless; spec-without-control is the combination
   the prototype loader validates),
3. do not call `resource_autoplace.initialize_patch_set(name, true)`,
4. do not inject `planet.map_gen_settings.autoplace_controls[name]` /
   `autoplace_settings.entity.settings[name]` (usually in `data-updates.lua`).

Dropping the prototype instead makes every save that already has patches fail
to load. Document that the change only affects NEW maps — patches already
generated stay where they are.

## 3. Bootstrap techs must be reachable with vanilla packs only

If the material's tech needed the mod's own pack (or a mod tech as prereq), the
mode hard-locks: you would need the item to research the machine that makes the
item. Keep `prerequisites = { <vanilla tech> }` with
`{ <vanilla science pack> }` packs, and do not make it a prerequisite of the
normal entry tech — a side branch keeps the mode optional for everyone else.

## 4. "No cost" techs (the empty-`unit.ingredients` bug)

Every path that builds `unit.ingredients` needs an `if #packs == 0` fallback,
because a tech with an empty list renders without a cost: `make_research_unit`
(technologies) and every `add_research_pack` implementation (dynamic generator,
mirror generator). When a setting strips the mod's pack from a tech, substitute
the tier's OWN vanilla packs — a single tier-1 fallback cheapens every tier.

## 5. Testing data-stage gating without Factorio (lua5.2 only)

Prototype files can be exercised for real from the test suite:

```lua
local captured = {}
_G.data = { raw = { resource = {}, item = {}, technology = {} },
    extend = function(_, protos)
        for _, p in ipairs(protos) do table.insert(captured, p) end
    end }
_G.settings = { startup = { ["dmrsa-tenemut-source"] = { value = "Synthesis only" } } }
_G.mods = {}
package.preload["resource-autoplace"] = function()
    return { initialize_patch_set = function() end,
             resource_autoplace_settings = function(t) return { control = t.name } end }
end
local chunk = assert(loadfile(MOD .. "prototypes/raw-resources.lua"))
assert(pcall(chunk))
-- then assert on `captured`: which prototypes exist, and with which fields
```

Run it once per mode and assert the DIFFERENCES (resource present but
`autoplace == nil`, no `autoplace-control`, machine absent in the default mode).
This catches self-gating early-returns and the exploit guards long before a gate
test in the real game. Pitfall hit while writing it: the stub's `data:extend`
receives BOTH a single prototype table and an array — branch on `protos.type`,
and register technologies into `data.raw.technology` as you go (the mod reads
that table in the same data stage).

## 6. Engine risk to confirm in the gate test

An ingredient-less recipe is documented as legal, but the only authoritative
check is the real game: run one load in "Synthesis only" and watch for a
prototype error on the synthesis recipe. Fallback if the engine rejects it: make
the single ingredient a free renewable fluid (water) — which also means adding a
fluid box to the machine.
