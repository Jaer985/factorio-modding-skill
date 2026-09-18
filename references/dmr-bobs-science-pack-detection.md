# Bob's mods: Science pack patterns & tier detection gaps

Analyzed 2026-07-19. Bob's mods v3.0.0 for Factorio 2.1.

## Bob's custom science packs

| Pack name | Type | Equivalent vanilla | Used in |
|-----------|------|-------------------|---------|
| `bob-advanced-logistic-science-pack` | item | utility-science-pack | Replaces `utility-science-pack` in some techs via `bobmods.lib.tech.replace_science_pack()` |
| `bob-science-pack-gold` | item | endgame (tier 5) | Alien research techs (paired with alien-color packs) |
| `bob-alien-science-pack-{color}` | item | endgame (tier 5) | 6 colors: blue, orange, purple, yellow, green, red |
| `bob-advanced-logistic-science-pack` | item | utility (tier 4) | Added to `logistic-system` via `bobmods.lib.tech.add_science_pack()` |

## Actual tech ingredient patterns found

### bobplates technology.lua (early-mid game)
All techs use ONLY vanilla science packs:
```
automation-science-pack  → not checked by get_tier_from_tech
logistic-science-pack    → not checked
chemical-science-pack    → checked ("chemical" → tier 2) ✓
production-science-pack  → checked ("production" → tier 4) ✓
```

**Critical gap**: automation and logistic are NEVER matched by any pattern. A tech with only `automation-science-pack` + `logistic-science-pack` → `get_tier_from_tech` returns 1 (default).

### bobplates technology-metal.lua (mid-late game)
Uses automation + logistic + chemical + production packs. Production IS detected.

### bobplates technology-updates.lua (alien replace)
Alien research techs get their ingredients REPLACED:
```lua
data.raw.technology["bob-alien-blue-research"].unit.ingredients =
    { { "bob-science-pack-gold", 1 }, { "bob-alien-science-pack-blue", 1 } }
```

These packs contain NO vanilla science packs:
- `"bob-science-pack-gold"` → contains "gold" → no pattern matches
- `"bob-alien-science-pack-blue"` → contains "alien", "blue" → no pattern matches
- Result: `get_tier_from_tech` returns 1 → these techs are classified as tier 1

### bobtech technology-updates.lua (replacement patterns)
```lua
-- Replaces utility-science-pack with bob-advanced-logistic-science-pack
bobmods.lib.tech.replace_science_pack("destroyer", "utility-science-pack", "bob-advanced-logistic-science-pack")

-- Adds the pack alongside vanilla packs
bobmods.lib.tech.add_science_pack("logistic-system", "bob-advanced-logistic-science-pack", 1)

-- Space Age: adds packs to existing techs
bobmods.lib.tech.add_science_pack("bob-tungsten-processing", "space-science-pack", 1)
bobmods.lib.tech.add_science_pack("bob-tungsten-processing", "metallurgic-science-pack", 1)
```

`bob-advanced-logistic-science-pack` contains "advanced" → matches tier 5 pattern (string.find(name, "advanced")). It replaces utility (tier 4) but is classified as tier 5 — conservatively correct but imprecise.

### With Space Age enabled
Bob's also adds vanilla Space Age packs to its techs:
- `space-science-pack` → detected ("space" → tier 5) ✓
- `metallurgic-science-pack` → detected ("metallurgic" → tier 3) ✓

## Current `get_tier_from_tech` pattern coverage

**Checked** (existing):
- "chemical" → tier 2 ← catches chemical-science-pack
- "metallurgic" → tier 3 ← catches metallurgic-science-pack  
- "electromagnetic" → tier 3
- "agricultural" → tier 3
- "production" → tier 4 ← catches production-science-pack
- "utility" → tier 4 ← catches utility-science-pack
- "space" → tier 5 ← catches space-science-pack
- "cryogenic" → tier 5
- "promethium" → tier 5
- "singularity" → tier 5
- "matter" → tier 5
- "advanced" → tier 5 ← CATCHES bob-advanced-logistic-science-pack (but classifies as tier 5 instead of 4)

**NOT checked** (gap):
- "automation" → no match → tier stays default
- "logistic" → no match
- "military" → no match
- "alien" → no match
- "gold" → no match
- "bob" → no match (mod prefix not considered)

## Defensive recommendation

See 4-layer defense plan in the session: 
1. Broaden `get_tier_from_tech` patterns (add "military" → tier 2, "logistic" → tier 1, "alien" → tier 4, "gold" → tier 5)
2. Add secondary validation in `DynamicGenerator.generate()` — independently verify tier against original tech
3. Build dynamic science-pack tier map from all tech ingredients
4. Improve `recipe_tech_map` fallback when primary lookup fails
