# MACHINE_EFFICIENCY — Space Age recipe-category name drift (audited post-v3.5.7)

_Discovered during the v3.5.14–v3.5.19 release cycle audit. This is the
follow-up to the v3.5.7 "extend MACHINE_EFFICIENCY to 8 SA categories" fix —
that fix used WRONG category names, so it did not actually cover the SA
machines it was meant to cover._

## The bug

DMR's `lib/cost-solver.lua` has a `MACHINE_EFFICIENCY` table mapping
recipe-category name → cost multiplier. v3.5.7 added what the author thought
were the 8 SA categories. But the keys did NOT match the real SA internal
names:

| Category the code used (v3.5.7) | Real SA category name | Result |
|---|---|---|
| `metallurgic` | `metallurgy` | ❌ no match → neutral 1.0 |
| `electromagnetic` | `electromagnetics` | ❌ no match → neutral 1.0 |
| `cryogenic` | `cryogenics` | ❌ no match → neutral 1.0 |
| `organic-or-egg` | `organic` | ❌ no match → neutral 1.0 |
| `farming` | (not a base SA category) | dead entry (harmless) |
| `brewing` | (not a base SA category) | dead entry (harmless) |
| `crushing` | `crushing` | ✅ correct |
| `crafting-with-fluid-or-recycling` | (combination, real names are `crafting-with-fluid` + `recycling`) | partial |

Also **missing entirely**: `captive-spawner-process` (biter spawner in
biochamber — SA endgame) and `hand-crafting`.

## How to extract the real list

```python
import urllib.request, re
req = urllib.request.Request(
    'https://raw.githubusercontent.com/wube/factorio-data/master/space-age/prototypes/recipe.lua',
    headers={'User-Agent': 'Mozilla/5.0'})
data = urllib.request.urlopen(req, timeout=15).read().decode(errors='replace')

all_cats = set()
for m in re.finditer(r'category\s*=\s*"([^"]+)"', data):
    all_cats.add(m.group(1))
for m in re.finditer(r'categories\s*=\s*\{\s*"([^"]+)"', data):
    all_cats.add(m.group(1))
for m in re.finditer(r'categories\s*=\s*\{\s*"([^"]+)"\s*,\s*"([^"]+)"', data):
    all_cats.add(m.group(1)); all_cats.add(m.group(2))
# diff against MACHINE_EFFICIENCY keys
```

Verified real SA recipe-category strings (from `space-age/prototypes/recipe.lua`):

```
advanced-crafting, captive-spawner-process, chemistry, crafting,
crafting-with-fluid, crushing, cryogenics, electromagnetics,
hand-crafting, metallurgy, oil-processing, organic, recycling, smelting
```

## Fix (APPLIED in v3.5.20 — receipt 14/14 PASS)

The four wrong keys were corrected and the missing ones added in v3.5.20:

```lua
["metallurgy"] = 1/3,                     -- Foundry (like smelting)
["cryogenics"] = 1.0,                     -- Cryogenic plant
["electromagnetics"] = 1.0,               -- Electromagnetic plant
["organic"] = 1.0,                        -- Biochamber
["captive-spawner-process"] = 1.5,        -- Biochamber biter spawner (complex)
["hand-crafting"] = 1.0,                  -- neutral
```

The wrong-name keys were REMOVED (dead entries just confuse future audits).
`farming`/`brewing` kept for mod compatibility (some mods use those names even
though vanilla SA uses `organic`).

**Verification pattern used**: after patching, grep the source for BOTH the new
keys present AND the old keys absent:
```bash
grep -n '\["metallurgy"\]\|\["electromagnetics"\]\|\["cryogenics"\]\|\["organic"\]' lib/cost-solver.lua
grep -n '\["metallurgic"\]\|\["electromagnetic"\]\|\["cryogenic"\]\|\["organic-or-egg"\]' lib/cost-solver.lua  # should be empty
```

## Lesson for future audits

- **SA internal names drift and pluralize unexpectedly** (`-ics` suffix on
  `cryogenics`/`electromagnetics`, `metallurgy` not `metallurgic`, `organic`
  not `organic-or-egg`). Never trust the name you remember or the name in a
  previous fix — extract from the live data dump.
- A "coverage pass" that adds keys under wrong names is WORSE than no pass:
  it looks done, produces no errors, and silently leaves the fallback active.
  Always verify the added keys match `category =` literals in the dump.
- User symptom to watch for: replication cost of SA-machine items (foundry
  plates, EM-plant circuits, cryo-plant fluids) feels off / cheaper than
  expected → suspect MACHINE_EFFICIENCY name drift.
