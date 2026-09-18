# Bob's Mods Structure — DMR Compatibility Reference

Version researched: bobplates 3.0.0, bobtech 3.0.0 (2026-07-19)
Source: Manual inspection of downloaded mod source + Mod Portal API

## Key findings for DMR tier assignment

### Science packs used by Bob's

| Pack name | Equivalent | Usage in techs |
|-----------|------------|----------------|
| `automation-science-pack` | Vanilla red | Used in ALL bobplates techs |
| `logistic-science-pack` | Vanilla green | Used in most bobplates techs |
| `chemical-science-pack` | Vanilla blue | Used in mid/high bobplates techs |
| `production-science-pack` | Vanilla white | Used in tungsten, nitinol, air-comp-4 (tier 4 equivalent) |
| `space-science-pack` | Vanilla | Added to bob-tungsten-processing with SA enabled |
| `metallurgic-science-pack` | SA | Added to bob-tungsten-processing with SA enabled |
| `military-science-pack` | Vanilla | Used in alien research techs |
| `bob-advanced-logistic-science-pack` | Custom (replaces utility) | Replaces utility-science-pack in `destroyer` tech. Added to `logistic-system` tech. |
| `bob-science-pack-gold` | Custom endgame | Used in alien research techs (INGREDIENTS, not as a tech ingredient itself — the alien tech ingredients get REPLACED to use only gold+alien-color packs) |
| `bob-alien-science-pack-*` (blue, orange, purple, yellow, green, red) | Custom endgame | Used as tech ingredients in alien research after replacement |

### Critical: get_tier_from_tech detection gaps

The current pattern matching in DMR's `get_tier_from_tech` checks `tech.unit.ingredients` for these substrings:
- Tier 2: "chemical"
- Tier 3: "metallurgic", "electromagnetic", "agricultural"
- Tier 4: "production", "utility"
- Tier 5: "space", "cryogenic", "promethium", "singularity", "matter", "advanced"

**NOT caught**: automation, logistic, military, advanced-logistic, gold, alien

For Bob's specifically:

1. **`bob-advanced-logistic-science-pack`** — caught as tier 5 via the "advanced" substring. This over-classifies it (should be tier 4 as utility replacement). Fixed by moving "advanced-logistic" to tier 4 pattern.

2. **`bob-science-pack-gold`** — NOT caught. Contains "gold" not in any current pattern. Fixed by adding `string.find(name, "gold")` to tier 5.

3. **`bob-alien-science-pack-*`** — NOT caught. Contains "alien" not in any pattern. Fixed by adding `string.find(name, "alien")` to tier 5.

4. **alien research techs** — After bobplates' `technology-updates.lua` replaces their unit.ingredients from automation+logistic+military+chemical to `{ bob-science-pack-gold, bob-alien-science-pack-blue }` ONLY (no vanilla packs). With the "gold" and "alien" patterns added, these correctly classify as tier 5.

### Tech ingredient patterns (actual from bobplates)

bobplates techs use ONLY vanilla science packs in their `unit.ingredients`:
- Early: `automation-science-pack` (tier 1)
- Mid: `automation + logistic` (tier 1 — no pattern match → tier 1, which is incorrect for items like bob-nickel-plate that should be tier 2-3)
- Mid-high: `automation + logistic + chemical` (tier 2 from "chemical")
- Late: `automation + logistic + chemical + production` (tier 4 from "production")

The tier cap at `ingredient_tier + 1` limits items from these techs to ingredient_tier + 1. This is why items from production-tier techs (tier 4) with simple ingredients (tier 1) get capped to tier 2.

### Solution architecture

The hybrid category→tier floor system (v3.5.0+) solves this:
- `bob-tin-plate` → classified as `alloy` (tier 3 floor) → tier 3 regardless of ingredient chain
- `bob-nickel-plate` → classified as `alloy` (tier 3 floor) → tier 3
- `bob-cobalt-bearing` → classified as `shape` (tier 2 floor) → tier 2
- Bob's weapons/ammo → classified as `military` (tier 4 floor) → tier 4

### References

- DMR source: `lib/repltypes.lua` — full category definitions with fixed tiers
- DMR source: `lib/cost-solver.lua` — `get_tier_from_tech()` with improved patterns
- DMR source: `prototypes/recipes/dynamic-generator.lua` — `get_item_category()` with 18 categories
- Original fork: https://github.com/nihilistzsche/dark-matter-replicators-space-age
- Bob's mods portal: https://mods.factorio.com/mod/bobplates, https://mods.factorio.com/mod/bobtech
