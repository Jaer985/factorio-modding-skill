# DMR dump-data diagnostics — replicating the cost-solver against the real dump

_2026-08-11, DMR v3.7.0 gate test. When the user reports tier/prereq weirdness
with a real modlist (Bob's + SA + quality + CMO), static analysis and the
dmr-tests fixtures are NOT sufficient — the final `data.raw` after ALL mods'
data-updates/data-final-fixes is the only ground truth._

## 1. Getting the dump (user's Windows PC)

1. Close Factorio.
2. `cd "C:\Program Files (x86)\Steam\steamapps\common\Factorio\bin\x64"` (user's
   path; write dir is `C:/Users/jaer1/AppData/Roaming/Factorio`).
3. `factorio.exe --dump-data` (~1-5 min, headless, loads ALL active mods).
4. Output: **ONE file** `script-output\data-raw-dump.json` in the write dir —
   NOT a folder with per-type files (Windows Explorer hides `.json`, so it
   shows as a bare `data-raw-dump` item). ~90MB with Bob's.
5. Transfer via SCP (Telegram 20MB cap): `scp data-raw-dump.json
   jaer@<IP>:~/projects/Factorio-Modding/dark-matter-replicator/dumps/`
   or 7-Zip first. Also grab `factorio-current.log` (same dir).

## 2. What the log tells you first (read before the JSON)

`factorio-current.log` `[DarkMatterReplicators]` lines show the ACTUAL
assignments at load time:

- `Dynamically mapped base resource: bob-tin-ore (Tier 1, Cost 1.5)` — every
  minable resource that hit the dynamic fallback, with the tier it got.
  **Grep this for anything that isn't a real ore/fluid**: this session it
  exposed `dmrsa-tenemut` (DMR's OWN research item, from the
  `tenemut-near-spawn` resource entity) and `sulfuric-acid`/`lithium-brine`/
  `fluorine` (Bob's liquid resources) all mapped tier 1.
- `Tier override bob-sniper-rifle: computed=1 -> category=3 (military)` — the
  category floor override; use to spot endgame weapons stuck at tier 3.
- `Science tier force bob-advanced-logistic-science-pack: cost-solver=3 -> 1` —
  **bug signature**: the `string.find(name, "logistic")` science override
  matched `advanced-logistic` and forced Bob's advanced pack to tier 1. Anchor
  patterns (`logistic%-science%-pack$`) or check specific patterns first.
- `Dynamically compiled: 978 replication recipes and 978 technology nodes` —
  total scale.

## 3. Replicating the cost-solver against the dump (Python)

Load the essential sections and rebuild the maps EXACTLY like the mod does:

```python
import json
with open("dumps/data-raw-dump.json") as f:
    raw = json.load(f)
recipes, techs, items = raw["recipe"], raw["technology"], raw["item"]

def results_contain(recipe, name):
    res = recipe.get("results")
    if not res: return recipe.get("result") == name
    for r in res:
        rn = r.get("name") if isinstance(r, dict) else (r[1] if isinstance(r, list) and len(r) > 1 else None)
        if rn == name: return True
    return False

# Rebuild recipe_tech_map like CostSolver.build_tech_map()
recipe_tech_map = {}
for tname, t in techs.items():
    for eff in (t.get("effects") or []):
        if eff.get("type") == "unlock-recipe" and eff.get("recipe"):
            recipe_tech_map[eff["recipe"]] = tname

# Cross-check every DMR individual tech
missing = []
for tname, t in techs.items():
    if not tname.startswith("dmrsa-tech-repl-") or not tname.endswith("-tech"):
        continue
    item = tname[len("dmrsa-tech-repl-"):-len("-tech")]
    orig = recipe_tech_map.get(item)
    prereqs = t.get("prerequisites") or []
    if orig and orig not in prereqs:
        missing.append((item, orig, prereqs))
print(f"{len(missing)} items missing original-tech prereq")
```

**Result this session**: 868 DMR individual techs, 750 with the original prereq,
**118 missing** — every one of them a Bob's item whose unlock tech exists
(`bob-brass-chest`→`bob-brass-processing`, `bob-defender-robot`→`defender`,
`bob-distillery`→`bob-electrolysis-1`, `bob-enriched-fuel`→
`advanced-oil-processing`, `bob-mech-brain`→`bob-walking-vehicle`,
`bob-fast-accumulator`→`electric-energy-accumulators`).

## 4. Root cause (confirmed by the log load order)

DMR generates dynamic techs in `data-updates.lua` and builds `recipe_tech_map`
there — but Bob's defines its tech `unlock-recipe` effects in data-updates /
data-final-fixes that load AFTER DMR's generation (log order: DMR data-updates
at 5.761s, bobplates data-updates 6.2s, boblibrary data-final-fixes 7.28s,
bobplates data-final-fixes 8.45s). The tech map is snapshotted before those
effects exist → prereq silently omitted. This is the REVERSE of the v3.5.15
moon-eneas race (there a mod DELETED a tech; here mods ADD unlock effects after
DMR already built the map).

## 5. Fix direction (A4/A5)

- **A4**: new data-final-fixes PASS that rebuilds `recipe_tech_map` from final
  data and re-adds the missing original-tech prereq to every already-generated
  DMR tech (individual + grouped). Arregla los 118 sin tocar la generación.
- **A5**: optional deps in `info.json` — `? bobplates`, `? bobwarfare`,
  `? bobassembly`, `? boblogistics`, `? bobtech`, `? bobmodules`, `? bobpower`,
  `? bobores`, `? bobmining` — force DMR data-final-fixes AFTER Bob's (same
  pattern as the v3.5.15 `? moon-eneas` fix).
- **B4**: step-filter gap found in the same audit: combat/mech sub-parts NOT in
  STEP_EXPLICIT (`bob-robot-brain-combat*`, `bob-robot-tool-combat*`,
  `bob-mech-brain`, `bob-mech-leg-segment`, drones) still appear as targets.
  Only construction/logistic robot parts were covered by v3.6.3.

## 6. Also visible in the dump this session

- **Phantom `parameter-0..9` items**: some mod generates items literally named
  `parameter-N` (tier-3 chemical classification, `Tier override parameter-0:
  computed=2 -> category=3 (chemical)`). Same "?"-LocalisedString family as the
  v3.5.4 bug but as real targets — consider a name-pattern exclusion
  (`^parameter%-%d+$`) in target-mapper.
- **`dmrsa-tenemut` as base resource**: `initialize_base_resources()` is not
  gprefix-aware — skip names with the mod's own prefix inside it.
