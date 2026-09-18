# AAI Industry + Krastorio2 Power Bridge — Worked Example

## The Problem

AAI Industry adds an early-game progression where the `electric-lab` technology (which unlocks the vanilla `lab` recipe) is gated behind `electronics` and `kr-stone-processing`. Krastorio2 modifies the same tech tree (adding `kr-automation-core`, changing `electronics`, etc.). The result: a player with ~150 mods (K2 + Space Age + AAI + 5dim + Bob's + dozens of planet mods) can find their early tech tree with no reachable path to basic electricity or automation.

The tech card shows Automation as "Unavailable" with "Researched by Craft [Item: Electric lab]" — but no `electric-lab` entity exists; `electric-lab` is a **technology** that unlocks the lab building.

## Tech Tree (as loaded with both mods)

```
kr-automation-core  (auto-grants when prereqs met)
         ↓
electricity  (prerequisite: fuel-processing)
         ↓
automation  (no unit, no trigger)  → unlocks assembling-machine-1
         ↓
electronics  (unit: kr-basic-tech-card + automation-science-pack, 10×10)
         ↓
electric-lab  (unit: automation-science-pack, 100×10)  → unlocks lab
```

## Debugging Process

### Step 1: Isolate via log
Created a `data-final-fixes.lua` debug mod that dumps the full structure of `automation`, `electric-lab`, `electronics`, `kr-automation-core`, and all labs' `research_category`. Logged every technology with `category = "crafting"` and every technology with `craft-item` triggers.

### Step 2: Identify the blocker
- `automation`: category=nil, prereqs={electricity, kr-automation-core}, effects=assembling-machine-1, no unit
- `electric-lab`: category=nil, enabled=true, prereqs={electronics, kr-stone-processing}, effects=lab, has unit (100 automation science packs)
- `electronics`: enabled=true, prereqs={automation, automation-science-pack}, has unit
- All labs have `research_category = nil`
- Zero `craft-item` triggers exist across all loaded mods

### Step 3: Attempted fixes

| Attempt | What | Result |
|---------|------|--------|
| 1 | Remove `electronics` prereq from `electric-lab` | Prereq removed, but user still sees "Electric lab" on tech card |
| 2 | Add `craft-item` trigger for `burner-lab` to `automation` | Applied in data-final-fixes but overwritten by other mods |
| 3 | Prefix with `zzz-` to run last | Windows NTFS enumeration not reliably alphabetical |
| 4 | Runtime `control.lua` with `tech.researched = true` | Most reliable: bypasses all prototype overwrites |

### Step 4: Why data-final-fixes kept failing

Multiple overhauls (science-spread, nulls-k2so-tweaks, xy-k2so-enhancements) all modify the same technology objects. On Windows, NTFS enumeration doesn't guarantee alphabetical order, so `zzz-` prefix tricks don't reliably place a mod last. The **runtime fallback** is the only reliable solution for tech-tree deadlocks in heavy modpacks.

## Key Lessons

1. **"Researched by Craft [Item: X]" is NOT a trigger** — it's the lab-matching display. The lab type named "X" has `research_category` matching the tech's `category`.

2. **`electric-lab` is a TECHNOLOGY, not an entity** — internal name `electric-lab`, enables `lab` recipe. Not from vanilla or K2; added by tech-tree reorganization mods.

3. **`tech.researched = true` bypasses all prerequisites** — no prototype changes needed, no mod order concerns, works unconditionally at runtime.

4. **Pattern for runtime fixes**: `on_player_crafted_item` → check item name → `force.technologies[name].researched = true`

5. **Verify dependency versions**: Before setting `"mod >= X.Y.Z"` in info.json, check the user's installed version via their mod-list.json or the portal API. A mismatch blocks the entire mod from loading.
