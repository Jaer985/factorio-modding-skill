# DMR + aai-loaders-sane Compatibility Fix (v3.3.4)

## Bug report
**User**: meinkraft8 — "Conflict with Sane AAI Loaders"
**Error at startup**:
```
Error in assignID: technology with name 'aai-loader' does not exist.
It was removed by aai-loaders-sane.
Source: dmrsa-grouped-repl-2-general-tech (technology)
```

## Root cause

The `aai-loaders-sane` mod removes the vanilla `aai-loader` technology so loaders are unlocked via normal logistics techs instead. DMR's `dynamic-generator.lua` (called from `data-updates.lua`) was adding external original item technologies as prerequisites for its grouped replication technologies. Since `aai-loader` existed at data-updates time, it was added as a prereq.

Two separate issues prevented the v3.3.3 `data-final-fixes.lua` strip pass from catching it:

### 1. Load order dependency (primary cause)
Between unrelated mods (no dependency relationship), all three data phases order by **mod name alphabetically**:
- `data.lua`: alphabetical
- `data-updates.lua`: alphabetical
- `data-final-fixes.lua`: alphabetical

`aai-loaders-sane` sorts BEFORE `dark-matter-replicators-reborn` alphabetically (`a` < `d`). This means:

- In `data-final-fixes.lua`: aai-loaders-sane runs FIRST (removes `aai-loader`), DMR runs SECOND. **This should work** — DMR's strip pass sees `aai-loader` is already gone and removes it from prereqs.

BUT Factorio's documentation on the exact ordering is ambiguous. The bug proves that in practice, DMR's strip pass ran BEFORE aai-loaders-sane's removal (or the ordering reversed), causing the strip to miss it.

**Conclusion**: `data-final-fixes.lua` stripping is NOT a reliable fix when you can't control load order. The only robust fix is to not depend on external mod technologies.

### 2. Lua pattern `-` quantifier bug (secondary)
The v3.3.3 `data-final-fixes.lua` used:
```lua
if string.sub(tech_name, 1, #gprefix) == gprefix and tech.prerequisites then
```
This uses `string.sub` (no pattern parsing) so it was SAFE from this bug.

BUT: the tier extraction for orphan tech handling used:
```lua
local tier_match = string.match(orphan_name, gprefix .. "replication%-([1-5])")
```
Here `gprefix = "dmrsa-"` produces the pattern `dmrsa-replication%-([1-5])`. The `-` after `dmrsa` is NOT escaped in the Lua pattern — it's interpreted as a lazy quantifier (0+ of preceding `a`), causing `a-` to match just the single `a` and break the pattern. Result: `tier_match` was always `nil`.

**Fix**: Always escape hyphens in prefix patterns:
```lua
local prefix_pat = gprefix:gsub("%-", "%%-")
```
This produces `dmrsa%-` which matches the literal `dmrsa-`.

## Fix applied (v3.3.4)

### Layer 1: Prevention (dynamic-generator.lua)
Removed the addition of external original item technologies as prerequisites for BOTH grouped and individual replication techs. The replication tier requirements (`dmrsa-replication-{N}`) are sufficient to gate these technologies, and the original tech is almost always already researched by the time the player reaches that tier.

### Layer 2: 3-pass safety net (data-final-fixes.lua)
Rewrote `data-final-fixes.lua` with three passes:

| Pass | Scope | Action |
|------|-------|--------|
| PASS 1 | All `dmrsa-*` technologies | Strip missing prereqs, deduplicate |
| PASS 2 | ALL technologies in the game | Strip any prereq referencing a deleted DMR tech (cascading failure protection) |
| PASS 3 | DMR orphans (0 prereqs left) | Reassign unlocks to baseline `dmrsa-replication-{N}`, then hide + disable |

### Fixes for both individual and grouped techs
Both `use_individual_techs` and `use_grouped_techs` code paths in `dynamic-generator.lua` had the same vulnerability. Both were fixed.

## Files changed
- `prototypes/recipes/dynamic-generator.lua` — Sections B (individual) and C (grouped) disabled
- `data-final-fixes.lua` — 3-pass rewrite with proper `%-` escaping
- `info.json` — 3.3.3 → 3.3.4
- `changelog.txt` — New entry

## Testing
- Prefix detection: `dmrsa-*` techs detected, non-DMR techs ignored, `dmrs` (without hyphen) correctly rejected
- Tier extraction: `dmrsa-replication-{N}` and `dmrsa-grouped-repl-{N}-*` both extract correct tier
- Prereq stripping: `aai-loader` correctly removed from `dmrsa-grouped-repl-2-general-tech`
- Orphan detection: techs with 0 prereqs correctly identified (except `replication-1` which is intentionally root)

## Cross-reference
- Mod portal discussion: https://mods.factorio.com/mod/dark-matter-replicators-reborn/discussion/6a43a68e68833cea37912fe0
- GitHub repo: https://github.com/Jaer985/dark-matter-replicators-reborn_3
