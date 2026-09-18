# Bob's mod family — step-item geography (DMR replicator audit, 2026-08-11)

Source: static analysis of `current-modlist/` zips with
`scripts/parse_mod_prototypes.py` (bobores_2.1.2, bobmining_2.1.0,
boblogistics_2.1.1, bobinserters_2.0.3; recipes cross-referenced across ALL
modlist zips incl. dynamic `bobmods.lib.recipe.*` edits).

## Which Bob mod owns which item class
- **bobores**: raw ores only (`bob-gem-ore`, `bob-diamond-ore`, ... 7 gems +
  nickel/cobalt/tungsten etc. via data-updates). NO crushed/chunk/processed
  intermediates — ore processing lives in Angel's mods, not Bob's.
- **bobmining**: endpoint machines (drills, pumpjacks, water-miner,
  areadrills, steam-drills). No step items.
- **bobinserters**: endpoint inserters. No step items.
- **boblogistics**: the ONLY one of the core 4 with step items — roboport
  parts + robot sub-parts (see below), plus endpoint pipes/chests/
  belts/roboports/robots.
- **bobplates / bobwarfare / bobassembly** (separate audit): hold the
  name-pattern step items — gear wheels, bearings (incl. `bob-brass-bearing`,
  `bob-nitinol-bearing`), projectiles/warheads, grinding/polishing wheels,
  robot parts, ammo parts, electronic components.

## Name-pattern reality check
Patterns `crushed|chunk|processed|intermediate|part|gear-wheel|bearing|
projectile|warhead` matched **zero** items in the core 4 mods. If a
replication audit searches those patterns only, it finds nothing in
ores/mining/logistics/inserters — the parts live in subgroups, not names.

## The 27 step items in the core 4 mods (all in boblogistics)
All: `subgroup` = parts subgroup, produced by exactly 1 recipe
(`<same-name>` recipe), consumed as ingredients only (never placed), no
`hidden` flag anywhere in the 4 mods.

| subgroup | items | consumed_by (examples) |
|---|---|---|
| bob-robot-parts | bob-flying-robot-frame-2/3/4, bob-robot-brain(-2/-3/-4), bob-robot-tool-construction(-2/-3/-4), bob-robot-tool-logistic(-2/-3/-4) | robot recipes: bob-construction-robot-2..5, bob-logistic-robot-2..5, bob-distractor-robot, bob-destroyer-robot, bob-laser-robot; brain-N consumed by brain-(N+1) |
| bob-roboport-parts-antenna | bob-roboport-antenna-1..4 | bob-roboport-1..4, bob-logistic-zone-expander(-2..4), bob-logistic-zone-interface, bob-robochest |
| bob-roboport-parts-charge | bob-roboport-chargepad-1..4 | bob-robo-charge-port(-2..4), bob-robo-charge-port-large(-2..4), bob-roboport-N, bob-logistic-zone-interface-N |
| bob-roboport-parts-door | bob-roboport-door-1..4 | bob-robochest(-2..4), bob-roboport-N |

## CRITICAL for DMR target-mapper
- **Tier-1 parts feed BASE-GAME recipes**: `bob-robot-brain`,
  `bob-robot-tool-construction`, `bob-robot-tool-logistic` are consumed by
  vanilla `construction-robot` / `logistic-robot` (Bob's replaces their
  ingredients via `set_ingredients("logistic-robot", {...})`). Excluding
  them from replication breaks vanilla robot crafting — handle explicitly.
- The v3.6.3 step-item filter's LEVEL 2 explicit exclusion list
  (from upstream `replvar` in `replications/bob.lua`) is the ground truth;
  this audit confirms the pattern coverage (roboport-antenna/chargepad/door,
  robot brains/tools/frames).
- Do NOT use a consumer-graph heuristic ("consumed by ≤N recipes = step") —
  it over-excludes 460+ items incl. aluminium plates and science packs.
