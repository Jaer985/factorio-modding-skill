# Dump-driven audit workflow (DMR v3.7.0, 2026-08-11)

When the user reports tier/prereq/step weirdness with a real modlist, the
fastest reliable diagnosis is a **data-raw dump from the user's PC** plus a
**Python simulation of the mod's own logic** against that dump. This catches
load-order races and data-completeness bugs that static code review cannot
see (proven: 118 missing prereqs + 367 under-tiered items with Bob's).

## 1. Get the dump (user side, Windows)

- Close Factorio. Open `cmd`, cd to the game's `bin\x64`:
  `cd "<game-install-dir>\bin\x64"`
- Run: `factorio.exe --dump-data`
- Output: ONE file in the write dir:
  `C:\Users\<USER>\AppData\Roaming\Factorio\script-output\data-raw-dump.json`
  (Factorio 2.x writes a single JSON, NOT a folder of per-type files; Windows
  Explorer hides the .json extension so it shows as bare `data-raw-dump`).
- ~90MB with Bob's — too big for Telegram (20MB cap). Transfer via SCP:
  `scp data-raw-dump.json <user>@<host>:<project-dumps-dir>/`
  or 7-Zip first (JSON compresses ~10-20%).
- ALSO grab `%APPDATA%\Factorio\factorio-current.log` — DMR's `helpers.info`
  lines are a live trace of what the generator decided per item
  ("Dynamically mapped base resource: bob-tin-ore (Tier 1, Cost 1.5)",
  "Science tier force bob-advanced-logistic-science-pack: cost-solver=3 -> 1").
- CRITICAL: the dump reflects the INSTALLED mod version. If the user hasn't
  installed your latest local changes, the dump shows OLD behavior — state
  this in the analysis.

## 2. Load and slice the dump (Python)

```python
import json
with open("dumps/data-raw-dump.json") as f:
    raw = json.load(f)
# raw is keyed by prototype type: raw["recipe"], raw["technology"],
# raw["item"], raw["resource"], raw["fluid"], ...
essential = {k: raw[k] for k in ["recipe","technology","item","resource","fluid"]
             if k in raw}
with open("/tmp/raw_essential.json","w") as f: json.dump(essential, f)
```

## 3. Replicate build_recipe_map exactly

The cost-solver's recipe_map picks the FEWEST-ingredient recipe per product
and EXCLUDES recycling/barreling recipes. Replicate both or your prereq/
tier simulation resolves to recycling recipes (1 ingredient) and misses the
real unlock tech:

```python
def has_cat(r, cat):
    cats = r.get("categories")
    return cat in cats if cats else r.get("category") == cat

recipe_map = {}
for rname, r in recipes.items():
    if has_cat(r, "recycling") or rname.endswith("-recycling"): continue
    if has_cat(r, "barreling") or rname.startswith("empty-") or "-unbarrel" in rname: continue
    results = r.get("results") or ([{"name": r["result"], "amount": r.get("result_count",1)}] if r.get("result") else [])
    for prod in results:
        pname = prod.get("name") if isinstance(prod, dict) else (prod[1] if isinstance(prod,list) and len(prod)>1 else None)
        if not pname: continue
        if pname not in recipe_map or ing_count(r) < ing_count(recipe_map[pname]):
            recipe_map[pname] = r
```

## 4. Replicate build_tech_map + prereq cross-check

- `recipe_tech_map[recipe_name] = tech_name` from every tech effect
  `{type="unlock-recipe", recipe=...}`.
- For each DMR individual tech (`dmrsa-tech-repl-<item>-tech`), read its
  `prerequisites`; if `recipe_tech_map.get(item)` exists and is NOT in the
  prereq list → missing-prereq bug. Batch it: one pass over all techs gives
  the full count (DMR: 118/868 missing with Bob's).
- RESOLUTION PITFALL: when simulating a data-final-fixes re-attach pass, look
  up the source recipe by EXACT name (`data.raw.recipe[item]`), never via a
  rebuilt recipe_map. By data-final-fixes the mod's own `dmrsa-repl-*` recipes
  (0 ingredients) exist and build_recipe_map prefers fewest-ingredient → it
  resolves to YOUR OWN replication recipe → self-prereq cycle.

## 5. Replicate solve_cost (tier simulation)

Port the cost-solver to Python (BASE_RESOURCE_COSTS, FLUID_TIER_OVERRIDES,
MOD_ORE_TIERS, MACHINE_EFFICIENCY + substring fallback, get_tier_from_tech,
cycle detection, ingredient_tier+1 cap). Then:

- Compare assigned tier (from each DMR tech's `dmrsa-replication-N` prereq)
  vs simulated tier from FINAL data → find under-tiered items (DMR: 367,
  incl. bob-destroyer-robot assigned 1 real 5, solar-panel 1→4).
- Diagnose the ROOT: if tiers are wrong because generation ran early
  (data-updates), the fix is structural — move generate() to
  data-final-fixes PASS 0 + optional deps (`? bobplates` etc.) to order after
  the mods. If the item is genuinely cheap, accept the low tier because the
  original-tech prereq gates access.
- Lua vs Python: `%-` is Lua's literal-hyphen escape; in Python it's just
  `-`. Don't port Lua patterns verbatim.
- Exclusions in Python sims MUST use `.search()`, never `.match()` (mordió 2×
  en el audit v4.2): `.match()` ANCLA al inicio del string, así que
  `re.compile(r'-recycling$').match("plastic-bar-recycling")` devuelve None y
  la recipe no se excluye → la simulación hereda una tech falsa y manda el
  item a mirror en vez de baseline. En Lua `string.find` es SEARCH (busca en
  toda la cadena) — por eso el JUEGO da un resultado distinto al de la sim.
  Regla: ante discrepancia sim-vs-juego, revisa las exclusiones/filtros de la
  simulación ANTES de creerle al framework; y al construir la sim escribe
  `\.search` desde el principio.

## 6. Locale parity audit (after any description/setting change)

Parse both locale files into `{section: {key: value}}`, diff key sets per
section (report missing in ES and missing in EN), and assert old false text
is gone:

```python
import re
def parse_sections(path):
    sections, cur = {}, None
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n\r")
        if not line or line.startswith("#"): continue
        m = re.match(r"^\[([^\]]+)\]$", line)
        if m: cur = m.group(1); sections.setdefault(cur, {}); continue
        if cur and "=" in line:
            k, v = line.split("=", 1); sections[cur][k] = v
    return sections
en = parse_sections("locale/en/dark-matter-replicators.cfg")
es = parse_sections("locale/es-ES/dark-matter-replicators.cfg")
```

After a lore/description rewrite, ALSO assert gameplay-relevant facts survived
in both locales — e.g. planetary replicators must still say "3x"/"5x"
(crafting_speed from planetary-replicators.lua: vulcanus/fulgora/gleba=3.0,
aquilo=5.0) and "100% freshness" for gleba. A rewrite that keeps the poetic
line but drops the number is a silent doc bug (DMR v3.7.0: gleba lost "3x
speed" mid-rewrite, caught only by this check).

## 7. Zip build + receipt (no `zip` binary on host)

Build with Python zipfile; root folder is the mod NAME (not the source dir
suffix): arc = `dark-matter-replicators-reborn/...`. EXCLUDE internal docs:
`ROADMAP.md`, `FAQ.md`, `specs/`, `research/`, `__pycache__`, `.DS_Store`.
Verify inside the zip: version matches info.json, key files present, no
leaked internal docs, and run `check-no-private-data.py` on the source tree
before building. Receipt checks can read files from inside the zip
(`z.read("dark-matter-replicators-reborn/lib/helpers.lua")`) — this is what
actually ships, stronger than checking source.
