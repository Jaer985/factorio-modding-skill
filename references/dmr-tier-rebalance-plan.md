# DMR — Tier Rebalance Plan (approved 2026-08-09, NOT yet implemented)

_Status: proposal approved by user ("Dale me parece"), candidate was frozen and
reviewed, implementation did NOT start. Next session: implement under the RDD flow
(skill `receipt-driven-development`) — direct route, risk=standard (balance),
then receipt + zip + user test._

## Why

User feedback (own perspective + mod portal user sp518): weapons, modules and
ammo are NOT visible in tier 3 because the code tiers them too high:

- All modules (`speed-module`, `speed-module-2`, `efficiency-module-3`, ...) → category
  `module` → **tier floor 5** (cryogenic science). In vanilla, speed-1 unlocks with
  chemical — gate to cryogenic is far too late.
- All weapons/ammo/armor/capsules → category `military` → **tier floor 4** (space).
  Pistol and firearm-magazine are early-game in vanilla.

sp518 also asked: "Can we make a separate tech for the modules and weapons?"
Answer: with Grouped Categories those grouped techs already exist per category
(`dmrsa-grouped-repl-4-military-tech`, `dmrsa-grouped-repl-5-module-tech`) but they
are gated late. The real fix is tier rebalancing, not new tech structure.

## Current classification (verified against vanilla data dump)

`get_item_category` rules in `prototypes/recipes/dynamic-generator.lua`:

| Item | type | category | tier floor |
|---|---|---|---|
| speed-module / speed-module-2 / speed-module-3 | module | module | 5 |
| efficiency-module / productivity-module (+ -2, -3) | module | module | 5 |
| pistol, submachine-gun, shotgun, combat-shotgun, rocket-launcher, flamethrower | gun | military | 4 |
| firearm-magazine, piercing-rounds-magazine, shotgun-shell, rocket, cannon-shell, uranium-* | ammo | military | 4 |
| grenade, cluster-grenade, defender/poison/slowdown capsule | capsule | military | 4 |
| land-mine | item | military (name match "%-mine") | 4 |

## Approved plan

**1. Lower tier floors in `lib/repltypes.lua`:**
- `module` tier 5 → **3** (chemical)
- `military` tier 4 → **3** (chemical)
- Add `module-advanced` → tier **4** (space)
- Add `military-advanced` → tier **5** (cryogenic)

**2. Split classification in `get_item_category`** (`prototypes/recipes/dynamic-generator.lua`):

Modules:
- `string.find(name, "module%-3")` → `module-advanced` (tier 4)
- everything else with "module" → `module` (tier 3)

Military (after basic military detection):
- advanced patterns → `military-advanced` (tier 5):
  `uranium`, `artillery`, `explosive%-rocket`, `cluster`, `spidertron`,
  `nuke`, `nuclear`, `rocket%-launcher`, advanced `cannon%-shell`
- basic (pistol, shotgun, firearm-magazine, grenade, capsules, land-mine) →
  `military` (tier 3)

**3. Locale additions** (`locale/en/dark-matter-replicators.cfg` + `locale/es-ES/...`):
- `[replcategory-name]`: `module-advanced=Advanced Modules`, `military-advanced=Advanced Military`
- Verify `[repltype-tech]` section has entries too if used for dynamic tech names.
- Run the locale parity check (see audit-and-release.md) after editing both.

**4. Consequences to verify:**
- New grouped tech names: `dmrsa-grouped-repl-3-module-tech`,
  `dmrsa-grouped-repl-4-module-advanced-tech`, `dmrsa-grouped-repl-3-military-tech`,
  `dmrsa-grouped-repl-5-military-advanced-tech` — these need locale in
  `[technology-name]` if they don't fall back to the generic `dmrsa-grouped-repl-tech`.
- `repltypes` `order` values must stay unique after adding 2 categories.
- Savegames keep already-researched techs; only new games see the new progression.

## Risk

- Standard (balance/progression). Requires user consent (already given) + in-game test.
- Trade-off: basic modules/weapons become replicable earlier, progression curve
  flattens slightly — this is the intended fix per user request.

## Receipt checklist (when implementing)

```
RECEIPT v3.5.14 (or next)
- [ ] repltypes: module=3, military=3, module-advanced=4, military-advanced=5
- [ ] get_item_category splits module-3 / advanced military patterns
- [ ] locale EN+ES: module-advanced, military-advanced in [replcategory-name]
- [ ] locale parity EN/ES (script check)
- [ ] sanity: print tier for common vanilla items (iron-plate→alloy/3, speed-module→module/3, pistol→military/3, uranium-rounds→military-advanced/5)
- [ ] zip root + info.json version + changelog
```
