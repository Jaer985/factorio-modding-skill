# DMR — Yuoki Industries Compatibility (researched 2026-08-14)

Research result when the user asks to add Yuoki compatibility ("agregale
compatibilidad de yuoki", "revisa el mod original en busca de la compatibilidad").

## Where the ground truth lives

The UPSTREAM fork has a full per-mod compat file that the dynamic 4.x system
replaced:

- Repo: `nihilistzsche/dark-matter-replicators-space-age` (the fork DMR derives
  from — search GitHub for it; Jaer985's repo only has recent history).
- File: `prototypes/replications/yuoki.lua` (150 lines) — loaded from
  `data.lua` via `if mods["Yuoki"] then require(...) end`.
- Its system: `replvar("recipe", cost)` cost overrides, `repltech_recipe(...)`
  category/tier assignments, `repltech_item_table(...)` groupings, and
  `replvar(..., 0)` = NOT replicable. This is manual per-mod tables — the
  dynamic mirror tree (4.x) replaces it, but the JUDGMENT (which items are
  worth replicating) is still the ground truth.

## Yuoki Industries mod facts (1.2.x, from source)

- Portal name: `Yuoki`, title "Yuoki Industries". No static technologies in
  data.lua (`--require("prototypes.technology")` is commented out) — recipes
  are `enabled = true` from the start. Implications for the mirror tree:
  Yuoki items have NO original tech → they fall to the materials/baseline
  path, NOT mirror techs.
- Size: 1522 items, 362 static recipes, 77 fluids, 95 assembling-machines,
  148 items with `place_result` (machines/buildings).
- **Signs are faction currency, NOT production** — the upstream explicitly
  excludes the 4 signs (`y_greensign`, `y_rwtechsign`, `ypfw_trader_sign`,
  `ye_science_blue`) with cost 0: "signs represent what other factions are
  willing to do for you... can't be replicated at all". In the dynamic system
  these would otherwise enter as normal items.
- Upstream judgment highlights: pure elements merged into plate techs
  (y-pure-iron/y-pure-copper → based on iron/copper plate ×2), exotic chains
  (unicomp N4, fuelnium, mixed) tiered 1-4, alien artifacts tier 2-4,
  machine parts device3-4, modules tier 4.

## What the 4.0 dynamic system needs (fix plan)

1. **`? Yuoki` in info.json** — load-order (same A5 pattern as Bob's/Angel's).
   IMPLEMENTED 2026-08-14.
2. **Signs blacklist** — add the 4 sign names to TARGET_BLACKLIST (faction
   currency, not production). IMPLEMENTED 2026-08-14 in `is_v4_excluded`.
3. Ammo stays replicable (mass-use principle, consistent with 4.x).
4. **Per-item blacklist `YUOKI_EXCLUDED` (19 items)** — IMPLEMENTED
   2026-08-14 in `lib/target-mapper.lua`:
   - 10 inserters (y-inserter-s4, y-inserter-smart-*, y_inserter_diagonal,
     y_inserter_evade_shortL/R, y_inserter_smart_LL/RR, y_inserter_smart_leftR2/
     rightR2) — Bob's inserters already cover them, Yuoki's add no value
   - 1 storage (y-rare-m1bunker-log) — storage building, not production
   - 8 basements (y_basement_4x4a, y_basement_5x5a..5x5f, y_basement_5x5f2) —
     one-per-base placement buildings
   - Everything else decided per-item by the user; NOT a blanket filter.

## ⏸️ PAUSE 2026-08-14 — decision deferred until Yuoki is 2.1

The user reviewed `YUOKI_EXCLUDED`'s inserters/storage/basements and said the
rest he'll "ver poco a poco" — then **explicitly paused the whole Yuoki review**:
"lo dejamos así mientras, cuando tengamos yuoki en la modlist lo revisamos, por
ahora no ha sido actualizado a la 2.1". **Do NOT resume the machine/item
decision process until Yuoki is updated to 2.1 AND present in the modlist.**
The full pending per-item list (procesado 16, refinado 5, mastercrafted 8,
ultimate 6, sueltos 13) is recorded in ROADMAP.md under the entry
"Compatibilidad Yuoki Industries (PAUSA registrada 2026-08-14...)" — read
that entry when the trigger fires to continue exactly where it stopped.
Confirmed KEPT while paused: logistic chests (j-dl-buffer/provider/request,
y-rare-chest-log), y_signal_pole, 8 lamps, 7 pipes, y_wood_wall, energy (6),
storage tanks (7), robots (4), fuel (2), turrets (4), y-small-stirling-engine.
The `? Yuoki` optional dep is harmless while Yuoki is absent — it only orders
data-final-fixes when the mod IS installed.

## ⛔ CRITICAL — the universal `place_result` filter is an ANTI-PATTERN (2026-08-14)

The first fix plan proposed excluding every item whose prototype has
`place_result` as the mod-agnostic "machine = one-time use" lever. **This was
WRONG — dump-verified.** 208 base-game items with `place_result` are mass-use
production that MUST stay replicable:

- **Chests**: wooden/iron/steel-chest, requester/provider/storage/buffer-chest
  (logistic chests were deliberately moved to tier 5 as endgame offenders)
- **Belts/splitters**: transport/fast/express-belt, underground, splitter
- **Inserters**: burner/inserter/fast/long-handed
- **Furnaces/miners**: stone/steel/electric-furnace, burner/electric-mining-drill
  (**stone-furnace is in the deliberate tier-1 baseline**)
- **Infra**: pipes, poles, walls, solar panels, accumulators (solar/batteries
  were kept by explicit user decision — mass-use)

`place_result` cannot distinguish "machine placed once" (reactor, rocket-silo)
from "mass-produced building" (chest, belt, inserter). **Do NOT add a blanket
place_result exclusion.** If the user still wants machine exclusion, it must be
entity-type-scoped (assembling-machine/furnace/mining-drill/boiler/reactor/
turbine registries) and must preserve chests/belts/inserters/furnaces.

Also note: the UPSTREAM fork **replicated Yuoki machines** (y_solar_dish
device4, y_crystalizer device3, robots device5) — machines were never "the
problem" for the original author. The user's final direction (2026-08-14) was
to ANALYZE the items and decide which stay — see the inventory breakdown below.

## Yuoki item inventory (from source, 2026-08-14) — decision input

~275 Yuoki-only items (prefixes y-, y_, yi_, j-, j_, ye_, ypfw_):

- **112 machines** (`place_result`): processing line (y-crusher, y-dirtwasher,
  y-heat-form-press, y-mining-drill, y_crystalizer, y_smelter), mastercrafted
  (y_boiler4_mc, y_steam_turbine_mc), ultimate (y-alien-infuser, y-stargate),
  energy (y-stirling-solar-dish, y_alien_solar), storage/fluids
  (y-tank-1000..8000, y_mftank), inserters (~10 y-inserter-*),
  logistics chests (j-dl-buffer/provider/request), robots (yi_construction/
  logistic-robot), basements (y_basement_*), pipes, lamps, boilers, turrets/mines.
- **163 materials** (no `place_result`):
  - intermediates (~61): y-slag, y_slag_brick, y-basic-t1/t2-mf, y_tile_slag*
  - raw (~13): y_crystal_dust, y-coal-dust, y-richdust, y_crystal2, y-toxic-dust
  - ammo (13): y_ammo_plasma, y_ammo_flame, y-bullet-case — KEEP (mass-use)
  - modules (12): y-speed-module-1, y-green-module-1, y-pink-module-* — KEEP
  - components (9): y_structure_element, y-chip-1/2, y-bluegear
  - fuel (9): y_mox1fuel, y_mox2fuel, y-mixed-fuel, y-fuel-cell-c
  - energy (9): y-accumulator-*, y-battery-single-use*, y_compensator_25
  - metal (3): y-pure-iron, y-pure-copper, y_chip_plate
  - logistics (10): y-heat-pipe, y-inserter-fast, lamps, pipes — KEEP
  - walls (4): y-rare-wall-*, y-wall-forcefield — KEEP (mass defense)
  - weapons (6): yi_minigun, yi_lasergun, y_turret_laser22f12 — already
    excluded by type gun
  - equipment (10): yi_armor_gray/red/gold, yi_equip_* — already excluded by
    equipment pattern
  - signs (4): y_greensign, y_rwtechsign, ypfw_trader_sign, ye_science_blue —
    excluded (blacklist)
- Existing rules already handle: weapons (type gun), equipment (armor/
  equipment patterns), signs (new blacklist). Ammo/modules/components/fuel/
  energy/walls all stay under the mass-use principle.

**Recommendation (2026-08-14, SUPERSEDED by the PAUSE)**: the original plan
was to let the 112 machines ENTER like the upstream did — consistent with
chests/belts/inserters/furnaces staying replicable. The user instead chose to
decide per item (inserters out, bunker out, basements out, the rest "poco a
poco"), then paused the whole review until Yuoki ships a 2.1 build. When it
does, resume from the ROADMAP entry's pending list — machines are NOT
automatically excluded; each of procesado/refinado/mastercrafted/ultimate
needs the user's call.

## Technique: portal download 403 → get source from GitHub

`mods.factorio.com/api/mods/<name>` gives releases with `download_url`, but a
plain `curl`/Python download returns **403 (Cloudflare)**. Workaround: search
GitHub for the author's source repo (`api.github.com/search/repositories?q=...`)
and `git clone --depth 1`. Worked for Yuoki (`Yuoki-Industries/yuoki`). The
GitHub version may lag the portal release (repo 1.2.21 vs portal 1.2.23) —
fine for prototype analysis, but note the version gap when quoting numbers.
