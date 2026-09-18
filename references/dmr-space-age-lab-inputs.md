# DMR Space Age — Lab Inputs Crash (v3.3.x)

## Bug Report (Jul 6 2026)

**Thread**: `6a4bc19920bc2715492734f2` — "Cant work with space-age" (Higara123)
**Link**: https://mods.factorio.com/mod/dark-matter-replicators-reborn/discussion/6a4bc19920bc2715492734f2

### Reproduction

1. Enable only: **Base + space-age + quality + elevated-rails + DMR**
2. Startup crashes with:
```
Technology dmrsa-grouped-repl-vulcanus-chemical-tech: there is no lab that
will accept all of the science packs this technology requires.

Science packs: metallurgic-science-pack, dmrsa-dark-matter-scoop
```
3. Disabling Space Age → game starts normally.

### Why grouped techs trigger it

When **Grouped Categories** tech distribution is active, DMR generates
`dmrsa-grouped-repl-<planet>-<category>-tech` technologies that require
both the DMR-specific science pack (`dmrsa-dark-matter-scoop`) AND the
planet's science pack (e.g. `metallurgic-science-pack` for Vulcanus).

In **Individual Technologies** mode this doesn't happen because each item's
tech only needs its tier's DMR pack — no planet-specific pack is bundled
with a DMR pack in the same tech.

### Fix applied (v3.3.5) — Belt-and-suspenders

The old approach used a Lua ternary in data.lua:
```lua
inputs = (mods["space-age"] and { include planets... } or { dmr only })
```

This failed for the user. Replaced with a two-layer approach:

1. **data.lua**: Lab always defined with only the 4 base DMR science items
   (tenemut, scoop, transducer, conduit) + `research_category = nil`
2. **data-final-fixes.lua**: If Space Age active, inject the 4 planetary
   science packs into the lab's `inputs` list (with dedup check)

This guarantees the packs are present at final load time regardless of
any `mods[]` evaluation quirks at definition time.

### Files changed

| File | Change |
|------|--------|
| `prototypes/entities/replicators.lua` | `inputs` simplified to 4 DMR items unconditionally; added `research_category = nil` |
| `data-final-fixes.lua` | PASS 4: adds planet packs to lab inputs when Space Age active |

### Why `research_category = nil` matters

The replication-lab had no explicit `research_category`. The engine default
may not match technologies with no `category` field (which is the case for
all dynamically-generated grouped techs). Setting `research_category = nil`
explicitly tells the engine "this lab accepts any tech category".

### Status

- **Fixed in**: v3.3.5 (2026-07-08)
- **Tests needed**: enable Base + space-age + quality + elevated-rails + DMR
  with Grouped Categories tech distribution, start a new game on Nauvis,
  verify no load error.
