# DMR Quality Refiner (v4.1.0) — implementation source of truth

Design settled with the user on 2026-08-16 after a brainstorm (options A/B/C/D):
the user rejected "just allow quality on replicators" and asked for something
"balanceado acorde y fiel" — a dedicated refining machine with risk/reward.
When the user says "exploremos más opciones" after a clarify, they want
balance/philosophy nuances of the SAME feature, not a rerun of the same
options — bring harder trade-off analysis.

## Concept (what the user asked for, verbatim intent)

- A SEPARATE machine: feed ONE item, it attempts to raise quality +1 grade
  (never skips: normal→uncommon→rare→epic→legendary).
- +1% chance per cycle to upgrade, DECREASING per tier; energy ×10; a risk of
  losing the item. "fast inserter → 1% ciclos repetitivos hasta activar ese 1%
  (porcentaje que disminuye por tier)".
- Only REPLICABLE items are refinable (philosophy: the refiner refines what
  the replicator network already masters — weapons/armor/vehicles are out).
- Placeholder graphics: vanilla assembler sprites with violet/black-obsidian
  tint. Lore EN/ES explaining why only replicables.

## Final numbers (user-approved)

| Step | Success | Retry (same item) | Loss |
|---|---|---|---|
| → uncommon | 1% (0.01) | 0.94 | 5% |
| → rare | 0.5% (0.005) | 0.945 | 5% |
| → epic | 0.25% (0.0025) | 0.9475 | 5% |
| → legendary | 0.1% (0.001) | 0.949 | 5% |

Energy per cycle = 10 × the replication recipe's `energy_required`.

## Critical technical facts learned

1. **Recipe `results` support per-result probability + fixed `quality`** — that
   is the whole mechanic in one recipe: `results = {
   {type="item", name=X, amount=1, quality=from, independent_probability=retry_p},
   {type="item", name=X, amount=1, quality=to, independent_probability=p}}`.
   **IMPORTANT (gate-test proof, 2026-08-16): in Factorio 2.1 the key is
   `independent_probability`, NOT `probability`** — loading with `probability`
   errors: "'probability' property on a product prototype was renamed into
   'independent_probability'". Use `independent_probability` for independent
   per-result chances (pumpjack-style); `probability` now means
   cumulative/summed. Fix the generator AND the test assert together. There is
   NO runtime code needed; probabilities that don't sum to 1 = the rest is NO
   OUTPUT (the 5% loss).

2. **Recipe `ingredients` accept a `quality` field** — `{type="item",
   name=X, amount=1, quality="uncommon"}` restricts the input to that quality,
   which is what makes the ladder not-skippable. One recipe per (item, step)
   is required (4 per replicable item, ~3200 total with Bob's — the engine
   handles it, same as the vanilla recycler's thousands of recycling recipes).

3. **Quality variants are NOT accessible in the data stage.** Factorio expands
   quality AFTER all mod data stages: `data-raw-dump.json` shows 0 items with
   quality suffixes and 0 recipes with a `quality` field even when the quality
   mod is active (verified with real dump: quality-module recipes present,
   `sSasha__quality-lib__*-recycling` recipes present, but NO `-uncommon`
   item prototypes). Iterating quality variants in data-final-fixes is
   IMPOSSIBLE — "quality as replication targets" is dead on arrival. The
   engine-side expansion is invisible to mods.

4. **Quality gate**: `data.raw["quality"]` exists always (at least "normal");
   `data.raw["quality"]["uncommon"] ~= nil` means a quality mod is active.
   Use this as the gate for any quality-dependent subsystem. The whole
   refiner subsystem (entity/tech/recipes) only exists when the gate passes.

5. **`quality = "normal"` on a recipe forces normal output** — used on all
   replication recipes by default (new setting `dmrsa-replicator-quality`,
   "Normal only" default). Fluids have no quality → never set the field on
   fluid recipes.

6. **Graphics ground truth from the dump, never memory.** The 2.x
   assembling-machine-1 sprites are NOT the 1.1-era 132×132: the dump shows
   width=214 height=226 frame_count=32 line_length=8 scale=0.58. Extracting
   `graphics_set.animation.layers` from `data-raw-dump.json` eliminates
   load-error risk for placeholder graphics. Also: dump of a MODDED modlist
   shows Bob's contamination (assembling-machine-2 had a bobassembly mask
   layer) — prefer the unmodified vanilla entity.

7. **A module-less machine is the balance lever**: `module_slots = 0` +
   `allowed_effects = { "consumption" }` on the refiner. Quality modules
   would multiply the fixed result probabilities (breaking the ladder) and
   productivity would double the retry outputs.

## Files

- `prototypes/entities/refiner.lua` — recipe-category `dmrsa-refining`,
  item-subgroup `dmrsa-refining`, item `dmrsa-refiner`, entity
  (assembling-machine, tint {r=0.35,g=0.25,b=0.65}), recipe
  (replicator-4 + processing-unit 15 + matter-conduit 10), technology
  `dmrsa-replication-refining` (prereqs: replication-materials-5 + vanilla
  `quality` tech if present; matter-conduit packs; icon REQUIRED in 2.1;
  effects unlock `dmrsa-refiner`). Whole file early-returns when quality gate
  fails.
  **Placeholder graphics — FINAL state after the gate-test cascade**: the
  original assembler-1 sprite plan FAILED to load on the Bob's+Angel's+SA
  modlist (shadow `repeat_count` then shadow-sheet XOR 50x166 then
  `__base__/....png not found` because Bob's replaces the assembler entity and
  its graphics). Final fix: use DMR's OWN `replicator-5.png` sprite (113x91,
  frame_count 33, line_length 11, `animation_speed = 1/3`, shift
  {0.4, 0.1}) with the obsidian-violet tint — a mod's own sprite cannot
  disappear. See `references/factorio-2.1-breaking-changes.md` → the
  "Don't reproduce vanilla sprites" section for the full cascade + robust
  pattern. Do NOT re-introduce the vanilla assembler-1 path.
- `lib/refiner-generator.lua` — `RefinerGenerator.generate()`: iterates
  `data.raw.recipe` for prefix `dmrsa-repl-`, takes results[1] (skip fluid,
  skip dmrsa-* own items, skip missing items), emits 4 hidden recipes per
  item into category `dmrsa-refining`. Runs in data-final-fixes AFTER
  MirrorGenerator.generate() (needs the real dmrsa-repl-* energy costs).
- `settings.lua` — `dmrsa-replicator-quality` string-setting ("Normal only" /
  "Allow quality", default "Normal only").
- `lib/mirror-generator.lua` — replication recipes get `quality = "normal"`
  unless the setting is "Allow quality" (never for fluid targets).
- `dmr-tests/test_refiner.lua` — 37 checks. Mock gotcha: `data:extend` is
  called as a METHOD (`data:extend({...})`), so the mock must be
  `function(self, tbl)` or the first arg (self) is mistaken for the table.

## Locale CFG editing pitfall (hit twice, cost two restores)

The `locale/*/dark-matter-replicators.cfg` files are CRLF + very long lines.
Parsing with `re.split(r'(?m)^(\[[^\]]+\])\s*$', txt)` and rebuilding with a
wrong index stride CORRUPTED the file twice (headers/bodies swapped, sections
lost). Reliable pattern:

- Read with Python default newline handling (auto-normalizes CRLF→LF for
  processing), then write with `newline='\n'`.
- Walk the file LINE BY LINE, track the current section from `[...]` headers,
  buffer body lines per section, flush appending new keys at the section end.
- Verify after: header count == expected (16), every new key present.
- If corrupted: restore from the GitHub repo (`raw.githubusercontent.com/
  Jaer985/dark-matter-replicators-reborn_3/main/locale/...`) — the repo just
  pushed acts as a clean backup. This session restored both locales twice.
- Locale key requirements: entity-name + entity-description AND item-name +
  item-description must BOTH carry the text for placeable machines (no
  fallback between item/entity descriptions — known pitfall); recipe-name
  template with `__1__`/`__2__` placeholders must get exactly 2 args;
  mod-setting-name + mod-setting-description in both languages.

## Mirror-vs-baseline dump audit (for "materials-N desbloquea demasiado" reports)

When the user says a materials tech unlocks too much, reproduce the mirror
assignment against `data-raw-dump.json` before touching code. Working recipe
(2026-08-16, DMR v4.1 + Bob's):

1. **Tier of each item** = the replication recipe's category, parsed with a
   PLAIN-hyphen regex: `re.match(r'^dmrsa-replication-(\d+)$', cat)`.
   Factorio 2.0 dumps store it in `recipe.category` (string); 2.1 dumps in
   `recipe.categories[1]` (array). Handle both.
2. **Planetary categories are NOT baseline**: `dmrsa-replication-vulcanus/
   fulgora/gleba/aquilo` items route to planetary techs — exclude them from
   the materials buckets (they silently fall to tier 1 via a None→1 fallback
   and inflate `materials-1`).
3. **Tech→item map**: walk every NON-dmrsa, non-hidden technology's
   `effects`; the `unlock-recipe.recipe` value is the ORIGINAL recipe name,
   which by DMR convention EQUALS the item name. Look up `repl[eff['recipe']]`
   (keyed by ITEM name) — looking up `'dmrsa-repl-' .. recipe` fails
   (those keys don't exist) and reports "0 items with original tech".
4. **Apply the v4.x exclusion set in the audit** (dump 3.7.x predates the
   144-item exclusions): filter weapons/armor/capsules/vehicles/equipment
   patterns so the baseline matches what v4.x actually produces.
5. **Classify the leftovers before calling it a bug**:
   - Ores (minables) and fluids → legitimate baseline (no unlock tech).
   - `enabled = true` recipes (Bob's base belts/assemblers, Yuoki everything)
     → legitimate baseline by design.
   - Items whose unlock tech EXISTS in the dump but the mirror missed them →
     load-order problem: add `? <mod>` optional deps to info.json (A5
     pattern) so DMR's data-final-fixes runs after that mod's. Re-audit
     info.json whenever a new mod family joins the modlist.
   Real numbers from the 3.7.1 dump (Bob's+SA+quality) after corrections:
   852/945 items have original techs (mirror) and materials-1 holds only 16
   (12 vanilla tier-1 basics + bob-basic-transport-belt,
   bob-burner-assembling-machine, bob-chlorine, bob-resin — all enabled=true
   / no-unlock). If the user's REAL dump shows far more, the extra items are
   mods missing from optional deps, not a mirror bug.

User expectation to honor: mod items that HAVE an unlock tech should be
behind their mirror tech, never granted by a materials-N tech — a "free
unlock" feeling in materials is a red flag for him (`"deberian estar detras
de la tech que les corresponde"`).

## Python dump-audit regex trap (repeated twice in this session)

Lua's `%-` escape does NOT carry to Python `re`: `r'dmrsa%-replication%-(\d+)$'`
matches the LITERAL `%-` (nothing) and fails SILENTLY — every tier collapsed
to fallback 1 and the v4.0 exclusion patterns matched zero items, yet the
output looked plausible. Always write dump patterns with plain `-`. Symptom
check: if a tier regex "always returns 1" or an exclusion list "excludes
nothing", re-examine the hyphens first.

## User preferences reconfirmed

- Design-first: option rounds must be informed by dump data and by balance
  philosophy, not just feature possibilities ("tendria que ser balanceado
  acorde y fiel").
- He approved this design on the FIRST substantive proposal after the second
  round; the "setting + dedicated machine" combo landed. He hates
  scope-creep; implement exactly what was approved.
- Next steps for v4.1.0: gate test on PC 2.1 (refiner loads, violet tint,
  recipes listed in refiner, replicator normal-only), then portal + GitHub
  push.