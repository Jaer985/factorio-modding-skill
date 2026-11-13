<!-- Split out of SKILL.md on 20261101T050205Z; body is verbatim bullet text from the original
     'Common pitfalls' section, grouped by theme. Index: SKILL.md. -->

# Pitfalls — data stage, load order and prototype lifecycle

- **A data-stage skip has no echo at runtime — guard every consumer.** A prototype that a
  `data.lua`/`data-updates` conditional declines to define (no optional mod present: `quality`,
  `space-age`, an overhaul) still gets *named* by runtime code — `on_init`, `on_nth_tick`, GUI
  builders, `prototypes.entity["x"]` lookups — and the engine answers **"Unknown entity name: x"**
  as a hard load error, not a nil. So (a) every reference to a conditionally-defined name carries
  the same guard (`if not prototypes.entity["x"] then return end`), and (b) the release gate runs
  at least once on a modlist with that optional feature **removed** — the default modlist cannot
  see the branch, and a base-only crash ships silently otherwise.

- **Bulk prototype scanning from mod zips** — 5 parsing traps, the working parser
  (`scripts/parse_mod_prototypes.py`) and the sub-agent split recipe live in
  `references/zip-prototype-scanning.md`; scan zips with `zipfile` + regex, CRLF
  is the norm.



- **Item vs entity description duplication**: prototypes with both `type="item"`
  and an entity form MUST have description in BOTH `[item-description]` AND
  `[entity-description]`. No automatic fallback.

- **Optional deps must cover EVERY overhaul family** (v4.0, 2026-08-13): the
  A5 fix only declared Bob's mods (`? bobplates` etc.). When Angel's joined the
  modlist, DMR's data-final-fixes could still run BEFORE angelspetrochem's, so
  the mirror generator's tree-depth calculation (`get_tech_tree_depth`) saw
  incomplete prereqs → mirror tiers stayed too low → load-time
  "Non-contiguous levels: 2, followed by 4". Fix: add `? angelssmelting /
  ? angelsrefining / ? angelsindustries / ? angelspetrochem /
  ? angelsbioprocessing / ? angelsaddons-*` to info.json (same A5 pattern).
  RULE: whenever dynamic generation reads OTHER mods' techs (recipe_tech_map,
  tree depth, prereqs), the optional deps must name EVERY overhaul family in
  the player's modlist — re-audit info.json when a new family is added. Same
  class as the safe_require pitfall: the failure is silent (tier just stays
  low / a prereq is skipped) and only the dump or the load log reveals it.
 - **Parametrized-recipe placeholder items** (v3.7.0 B4): Factorio 2.0
   parametrized recipes (KS_Power etc.) create synthetic items named
   `parameter-N` (subgroup `parameters`). They are NOT real items and must be
   excluded from target-mapper (`string.find(name, "^parameter%-%d+$")`). The
   dump audit found dmrsa-repl-parameter-0..9 recipes generated from them.
 - **Mod internal packed-state items `*-instantiated`** (v3.7.1, factorissimo):
   factorissimo's `factory-1/2/3-instantiated` and `space-factory-1/2/3-instantiated`
   are `item-with-tags` internal items (the mined/packed form of factory
   entities) with INDIRECT `localised_name` (`{"item-name.factory-packed",
   {"entity-name.space-factory-X"}}`) — the direct key `entity-name.<name>` does
   NOT exist, so a replication recipe for them logs
   `Unknown key: "entity-name.space-factory-X-instantiated"` at runtime. They
   leak past the v3.6.4 eligibility rule because Space Age AUTO-GENERATES
   `<name>-recycling` recipes that PRODUCE them → `is_produced_by_recipe()` is
   true. Fix: `"%-instantiated$"` pattern in STEP_NAME_PATTERNS (same
   internal-item class as parameter-N). Diagnosis path: user pastes "unknown
   key: entity-name.X-instantiated" → grep the mod zip for `*-instantiated`
   prototypes (item-with-tags) + check the dump's recipe map for the
   auto-generated recycling recipe. General rule: any item that is an entity's
   mined/packed form (name = entity-name + `-instantiated`) is an internal
   state, never a replication target — the SA recycling-recipe side effect
   means eligibility checks alone can't catch these; name patterns are the
   reliable lever.
 - **safe_require swallows prototype load errors → phantom assignID crash**
   (v4.0 diagnosis path, 2026-08-12): DMR's `data.lua` wraps every prototype
   require in `pcall` (`safe_require`) that only LOGS failures. A runtime
   error inside a prototype file (e.g. `replicators.lua: attempt to index
   global 'defines'`) does NOT abort loading — the file's items silently never
   get defined, and the REAL symptom appears much later as
   `Error in assignID: item with name 'X' does not exist` at the recipe that
   references that item (recipe defined fine, item missing). Diagnosis path:
   (1) the assignID error names the ITEM, not the file — grep which prototype
   file defines that item; (2) replicate data.lua's load order in a lua5.2
   harness (mock `data = {raw={}, extend=function() end}`, `mods={}`,
   `settings={startup={}}`, `log=print`) and pcall-require each module to
   surface the REAL runtime error the safe_require swallowed; (3) stub the
   Factorio global helpers the file uses (`assembler2pipepictures`,
   `pipecoverspictures`, `defines.direction`) or the harness reports
   "attempt to index global 'defines'" which may be a MOCK artifact, not the
   real game error — confirm against `factorio-current.log` which shows the
   actual `[DarkMatterReplicators] ERROR loading ...` line with traceback.
   DMR v4.0.0 hit this: zip built/tests green but game failed at load with
   `item with name 'dmrsa-replication-lab' does not exist` — item defined in
   `prototypes/entities/replicators.lua`, recipe in `base-recipes.lua`.
 - **search_files/ripgrep does NOT understand Lua's `%-` escape**: this
   session repeatedly searched `dmrsa%-replication%-lab` (Lua literal-hyphen
   pattern) via search_files and got 0 matches while `grep -rn` found the
   files — ripgrep treats `%-` as literal `%` followed by `-`, NOT as
   hyphen-escape. When a search_files pattern returns nothing suspicious,
   retry with plain `-` (ripgrep needs no escaping for `-` outside character
   classes) or fall back to `grep -rn` in terminal. Same root class as the
   Python-vs-Lua regex escape differences already documented for dump parsing.
 - **Lua patterns: `-` is a LAZY QUANTIFIER, not a literal hyphen** (v4.2,
   2026-08-22, MOD_ORE_TIERS): in `string.find(name, "gold-ore")` the `-`
   means "0+ of the previous char, lazily" — the pattern silently FAILS to
   match a literal hyphenated name. Every literal hyphen in a Lua pattern
   MUST be escaped `%-`. Worse, when a table of substring patterns is scanned
   in order, an unescaped composite pattern never wins AND simpler patterns
   match INSIDE composite names: `"angels-platinum-ore"` contains `"tin"`
   (platinum!), so `tin`-mapping won with tier 2. Two-part fix used in
   DMR v4.2: (1) escape every hyphen in stored patterns (`"angels%-ore"`);
   (2) when scanning for a material override, return the LONGEST matching
   pattern, not the first — substrings of composite names can't steal the
   match. Same root class as the Python-vs-Lua escape pitfall: escaping
   conventions differ per language, and "match order" assumptions break when
   names are substrings of other names.
 - **Python `re.match()` ≠ Lua `string.find` semantics** (v4.2, 2026-08-22):
   when replicating the mod's Lua logic in a Python dump sim, `re.match()`
   anchors the pattern at the START of the string, so a suffix exclusion like
   `-recycling$` never matches `spaceship-scrap-recycling` → the sim resolves
   items through recycling recipes and predicts MORE mirror-tech items than
   the real game (Lua `string.find` = substring search anywhere). Symptom: the
   user's in-game report contradicts your "dump-validated" numbers. ALWAYS use
   `re.search()` (or `pattern in name`) when the source Lua uses
   `string.find`. The sim is a compiler for Lua pattern semantics: escape
   escape hyphens (`%-`→`-`), SEARCH not MATCH, and longest-match when a scan
      picks one of several patterns.
    - **Crafting speed is the hidden time divisor when calibrating replication
      costs** (v4.2 B2, 2026-08-22): the "nominal" `energy_required` of a
      replication recipe is NOT the time the player experiences — each
      replicator tier has `crafting_speed = 1/2/4/8/16` (`speed_factor = 2.0`),
      so real time = nominal ÷ speed. Calibrate bands against the REAL time or
      the user reports "es muy rápido": with bands 2-12/4-24/8-48/15-90/25-150s
      the ACTUAL felt time was a uniform 1.6-12s on EVERY tier (t5 16x crushed
      its 25-150s to 2-9s). Two levers, often both: (1) reduce `speed_factor`
      (2.0 → ~1.6-1.75) so the high tiers aren't ×16 faster; (2) raise the
      nominal bands. ALSO: lower `crafting_speed` raises energy-per-recipe
      (kW × more real time) — the "energy much higher" balance request gets
      stronger on high tiers, so never change speed without re-checking the
      energy model. When the user says "también banda nominal / la velocidad
      aumenta", they mean the speed-progression: re-run the real-time table
      per scenario before picking a dose.
      **RESOLVED 2026-08-22 (user picked option B + kW downshift)**: speed_factor
      2.0 → 1.6 and bands ×1.33 (2.7-16/5.3-32/10.6-64/20-120/33.3-200) → real
      ~2.7-30.5s. The user's rule "si es más lento debe ser más económico":
      kW was shifted DOWN from 1/4/16/40/100 to 1/3/8/15/30 MW so ENERGY PER
      RECIPE STAYS INVARIANT (same ~MJ, slower but cheaper grid, 30MW at t5).
      The cross-tier recursion (tier-N replicator accepts replication-1..N;
      t5 mass-produces basic inserters at 0.46s/13.7MJ vs 3s/3MJ on t1) was
      ALREADY in the code — verify, don't re-implement. Final model:
      `references/dmr-v42-cost-model-b2.md`.
    - **Fluid LOT clamp — multiply ×fluid_qty BEFORE the band, never after**
      (v4.2 B2): unit fluid costs are near-zero (water solver ≈ 0.03s); clamping
      per-unit then multiplying by the lot (default 25) makes water
      2s × 25 = 50s/lot — worse than the old model. `raw × fluid_qty` FIRST,
      then `clamp(raw, lo, hi)` so the band governs the LOT (~2s/lot for water).
    - **0-ingredient recipes + productivity = FREE duplication exploit** (v4.2
      refino, original-mod study): replication recipes have `ingredients = {}`
      by design; if the replicator's `allowed_effects` includes `productivity`,
      every productivity module multiplies output for free (no inputs to tax).
      Remove `"productivity"` from allowed_effects on EVERY machine that runs
      dynamic recipes — replicators AND planetary replicators (a sweep almost
      missed planetary-replicators.lua; grep `allowed_effects` across
      `prototypes/entities/*.lua`). The quality path stays the Refiner
      (module-less → probability IS the balance).
    - **Penalty semantics: upstream = +0.5 FIXED SUM, not a multiplier**
      (v4.2 refino): the fork's decaying multiplier (1 + penalty/depth,
      applied at the memoized-cache read AND the main solve return) inflated
      long recipe chains and contradicted the setting description ("added to
      the cost"). Fixed to `dark_matter + penalty`, `time + penalty×0.5` at
      BOTH call sites (miss the second → cache-hit vs cache-miss costs
      diverge). The `dmrsa-cost-calculation-method` setting became legacy —
      rewrite its EN+ES descriptions or the Options screen lies about
      behavior. NOTE: `is_root`/`depth` params remain in solve_cost but are
      now unused by the penalty path.
    - **Zip `in`-string verify-checks false-positive on comments** (v4.2
      refino): checking `'"productivity"' not in file_text` FAILS when the
      patch comment merely mentions the word. Verify the EXACT field
      (`grep -n "allowed_effects" file` → read the actual value), not a
      whole-file substring; same class as the receipt-verify false-FAIL
      pitfall (confirm the failure is in the CHECKER, not the artifact).
    - **Machine-layer detection is structural, no per-mod tables** (v4.2 B2):
      to make "machines" (assemblers, centrifuges, labs, solar panels, steam
      engines — user: "todo ese tipo de maquinas solar panels steam engine etc")
      pay a per-tier multiplier: precompute a `machine_entities` set by scanning
      `data.raw` for (a) prototype kinds in an infra-type list (assembling-
      machine/furnace/mining-drill/lab/centrifuge/solar-panel/accumulator/
      storage-tank/boiler/reactor/... ) and (b) ANY entity with
      `crafting_categories`/`crafting_speed`; then `is_machine(item)` = its
      `place_result` (or itself) is in the set. Catches factorissimo factories
      automatically (their entities are `storage-tank` type, verified in dump),
      Bob's/Angel's/SE machines via crafting, zero per-mod lists. See
      `references/dmr-v42-cost-model-b2.md` for the full model (constants,
      power ramp, refiner ×3, planetary 40/80 MW, difficulty caps now inert).
 - **Lore/descriptions must match current behavior** (v3.7.0 D2/D3): upstream
   fork lore (long narrative paragraphs) conflicted with the mod's actual
   scope. Rewrite lore as short atmospheric 2-3 sentence pieces telling the
   real progression (tenemut→scoop→transducer→conduit→planetary), preserve
   real numbers (3x/5x speeds verified against prototypes), and keep EN/ES
   parity (audit keys per section, 0 missing). Descriptions that contradict
   behavior are bugs (e.g. tier 3 "gated by planets" was false since v3.5.17).
 - **Generate mod content in data-final-fixes, not data-updates** (v3.7.0 A6,
   the ROOT-CAUSE lesson): any dynamic generation that reads OTHER mods'
   recipes/techs MUST run in data-final-fixes (or after declaring optional deps),
   NOT data-updates. Running DynamicGenerator.generate() in data-updates meant
   Bob's recipes/unlock-recipe effects didn't exist yet → dump-proven: 118 items
   lost original-tech prereqs (replicable from tier 1) AND 367 items were
   under-tiered (bob-destroyer-robot assigned 1, real 5; solar-panel 1→4).
   Moving generate() to data-final-fixes PASS 0 + optional deps
   (`? bobplates` etc. in info.json to order DMR AFTER the mods) fixes BOTH
   classes from complete data. Keep the data-updates file for autoplace/surface
   conditions that don't depend on other mods. A PASS that re-attaches missing
   prereqs stays as a safety net (it must resolve source recipes by EXACT name
   `data.raw.recipe[item]`, never via a rebuilt recipe_map — the mod's own 0-
   ingredient replication recipes poison the fewest-ingredient preference and
   create self-prereq cycles).
 - **Modded item tiers are only trustworthy from complete data**: when the user
   reports "item X in tier 1 but it's endgame", first check WHICH data the
   generator saw. Simulating the cost-solver against the FINAL dump
   (data-raw-dump.json) reveals whether the tier is wrong because the item is
   genuinely cheap (→ accept, prereq gates it) or because generation ran early
   (→ move generation later). The prereq original + correct tier are the two
   levers; a low tier is acceptable IF the original tech prereq blocks access.
 - **data-final-fixes load-order race** (v3.5.15): when another mod deletes a
  technology your dynamic generation referenced (moon-eneas deletes
  `spidertron-unit`, aai-loaders-sane deletes `aai-loader` techs), the crash
  "Error in assignID: technology with name 'X' does not exist. It was removed
  by <mod>." appears at startup. Your `data-updates.lua` adds the prereq while
  the tech still exists; the other mod deletes it in its data-final-fixes; your
  data-final-fixes PASS-1 strip runs in UNORDERED sequence relative to the other
  mod unless you declare a dependency. Fix: add `? <mod-name>` (optional
  dependency) to info.json to force your data-final-fixes to load AFTER the
  other mod's. Detection: startup crash naming a vanilla tech + "removed by
  <mod>" — check info.json dependencies for that mod. See
  `references/dmr-moon-eneas-compatibility.md`.
 - **Research difficulty multiplier setting** (v3.5.16): pattern for a
  startup string-setting (`allowed_values = {"Easy (Fast)","Medium","High"}`)
  mapped by a helpers function to `{reps_mult, time_mult}` tables, applied
  with `math.ceil(count * mult)` / `time * mult` at EVERY tech-creation site
  (individual, grouped, tier, planetary). Default must preserve historical
  behavior (×1/×1). Pitfall: `technologies.lua` AND `planetary-tech.lua` each
  define their own local `make_research_unit` with the same body — grep for
  the helper name (`grep -rn "make_research_unit" prototypes/`) before
  assuming a single call site, or one file stays unscaled. Locale needs
  entries in `[mod-setting-name]` AND `[mod-setting-description]` in both EN
  and ES, and the description should spell out the multiplier table. If the
  change also raises a balance constant, flag it as a behavior change in the
  changelog, not a fix.
  **v3.7.0 D1 refactor — single source of truth + absolute values**: when the
  user later asks to scale a hardcoded cap (the 600s recipe-time limit) by
  difficulty AND to "make the other numbers match", the clean end state is
  ONE table (`helpers.get_research_difficulty_values()`) returning all axes
  per difficulty — `{cost, time, cap, replic_mult}` — so they can never
  desync:
  Easy=25/5s/600s/×1.0 (historical, reads the player's `replresearch-*` settings),
  Medium=50/15s/1000s/×1.5, High=100/30s/1800s/×2.0, Very Hard=200/45s/3200s/×3.0
  (new difficulty added to `allowed_values`).
  **v4.2 (user: "subimos los tiempos de replicación por la dificultad")**: the
  4th axis `replic_mult` scales the ACTUAL replication recipe times —
  mirror-generator multiplies raw AND bands (`clamp(raw×mult, lo×mult,
  hi×mult)`) so EVERYTHING rises, not just the raw; the difficulty cap stays
  as the safety net. Without this, a difficulty that only scaled research
  felt like it did nothing to the replicators.
  Keep `get_research_difficulty_multipliers()`
  as a DERIVED backward-compat alias (`reps_mult = cost/25`, `time_mult = time/5`)
  so old call sites still work; update BOTH tech-creation sites (individual +
  grouped) to use the absolute values, and feed the cap through the same table.
  **User-correction lesson**: when the user proposes a numeric scale
  ("Cost: 10 50 100 200 / Time: 5 15 30 45"), they may give ABSOLUTE values
  AND may not remember the current default — they said Easy cost "10" but
  then corrected to 25 ("el easy no me acordaba cuanto era"). ALWAYS confirm
  whether the base difficulty keeps the historical default before treating
  the first number as the new default; the table's Easy branch must read the
  existing player settings so nothing changes for existing saves.
 - **Hidden placeholder tech side effect** (v3.5.16 diagnosis): the v3.5.2
  orphan-sink fix made the SA branch of `dmrsa-replication-3` a hidden inert
  tech (`hidden = true, effects = {}`). Side effect: the Chemical Replicator
  (`dmrsa-replicator-3`) has NO visible tech unlocking it before the planets —
  its `unlock-recipe` effect was emptied. User symptom: \\\"el chemical replicator
  esta con cada planeta, deberia ser una tech antes de los planetas\\\" (machine
  appears tied to planets / missing from the visible tree). Diagnosis path:
  read the TECHNOLOGY that would unlock the machine (check the SA branch for
  `hidden = true` + `effects = {}`), not the machine prototype. Fix direction:
  keep the real unlock effect on the tier tech and add the placeholder as a
  prereq of the next tier instead of emptying effects. Every hidden
  placeholder-with-empty-effects tech erases the visible unlock path for
  whatever it would unlock — before hiding a tech, ask if anything the player
  must acquire depends on its effects.
 - **Science-pack replication tier anchoring** (v3.5.17 + v3.5.19): science packs must be
  tiered BY NAME, not by the cost-solver recipe chain — `chemical-science-pack`'s
  recipe chain (advanced circuits, engine units, sulfur) pushes it to tier 4-5,
  so without an override it never shows in the Chemical Replicator tier 3.
  User-confirmed progression model: **automation/logistic = 1, military = 2,
  chemical/production/utility = 3 (BEFORE planets — production/utility sit at
  the end of chemical), planetary (metallurgic/electromagnetic/agricultural) =
  4, space/cryogenic/promethium = 5**. Implementation touches 3 files:
  (1) `dynamic-generator.lua` tier-floor block — for `item_category == "science"`
  override tier by name pattern (same mapping) instead of trusting `solve_cost`;
  (2) `cost-solver.lua` `get_tier_from_tech` — chemical→3 (was 2), production/
  utility→3 (was 4), planetary→4 (was 3), space/cryo/promethium→5; (3)
  `technologies.lua` `t_packs` — t3_packs = chemical ONLY (remove the SA
  `metallurgic-science-pack` insert so tier 3 research does not demand a
  planetary pack), t4_packs = the three planetary packs (SA) or production
  (non-SA), t5 = space+cryogenic. Also make the SA branch of `dmrsa-replication-3`
  VISIBLE with the real `unlock-recipe` effect and add `replication-3` to
  `rep_4_prereqs`. Sanity check after: simulate the science-tier function for
  the 12 known packs and print the tier table — it must exactly match the
  progression above.
  **v3.5.19 follow-up (CRITICAL)**: the initial override only raised the floor
  (`if tier < science_tier then tier = science_tier`), but the cost-solver can
  also return a HIGHER tier than the science pack's progression position (e.g.
  chemical-science-pack → tier 5 via its recipe chain). Result: the pack's
  replication research used the tier 4/5 research material (matter-conduit)
  instead of the tier 3 material (dark-matter-transducer). Fix: FORCE the tier
  absolutely — set `tier = science_tier` unconditionally (or add a second
  `if tier > science_tier then tier = science_tier` branch). For science packs
  the name IS the truth; the cost-solver chain is irrelevant. User symptom:
  "chemical science pack replication research está con matter conduit cuando
  debería ser dark matter transducer".
  **v3.6.3 follow-up (t2_packs)**: the same progression logic applies to the
  CORE replication techs in `technologies.lua`. `t2_packs` included
  `chemical-science-pack`, making `replication-2` (transducer, replicator-2)
  demand chemical before it should — chemical is TIER 3, so tier 2 must be
  automation+logistic ONLY. Check every `tN_packs` array against the
  progression model, not just the science-pack replication tiers. User
  symptom: "replication 2 se movio a chemical science pack" — the tier-2
  core tech was gated behind a tier-3 pack.
 - **Receipt verify-script false FAIL** (v3.5.17 lesson): zip receipt scripts
  that slice file content with `split('\\n')` or multi-line markers fail on
  CRLF (`\\r\\n`) files and report false FAILs, wasting cycles re-verifying
  code that is actually correct. When a receipt check FAILs, confirm the
  failure is in the CHECKER, not the artifact: grep the SOURCE files directly
  for the marker before distrusting the zip. Prefer direct `in` content checks
  (`'unlock-recipe' in tl`) over positional slices; for branch-specific checks
  (SA vs non-SA `if/else` blocks), anchor on a unique comment line that only
  exists in that branch.
 - **Planetary classification overrides BASE_RESOURCE_COSTS tier** (v3.5.18):
  an item can be tier 1 in the cost-solver tables yet still route to a
  planetary replicator, because the planetary classification block in
  `dynamic-generator.lua` runs AFTER the tier override and can redirect the
  recipe to a planetary category (`scrap` → `replication-fulgora`). When the
  user says "X should be on planet Y", the fix is ONE `string.find`/`name ==`
  clause added to the right `elseif` branch (gleba/vulcanus/fulgora/aquilo) —
  verify the branch matches the item's vanilla source planet before patching;
  no cost-solver change needed. Missing clause = item falls to the generic
  tier replicator at its cost-solver tier.
  - **Settings locale parity audit** (v3.6.2): every startup/runtime setting in
  `settings.lua` MUST have BOTH a name in `[mod-setting-name]` AND a
  description in `[mod-setting-description]` in EN + ES. A setting with only a
  description (or only a name) renders `Unknown key:
  "mod-setting-name.<setting>"` in the Options screen — visible only at
  runtime, invisible to static review of the settings themselves. DMR 3.6.2:
  `replication-penalty` had a description but no name; `replstats-speed-base`/
  `energy-base`/`pollution-base` had names but no descriptions. Run a parity
  audit before every release: extract `name = "X"` from settings.lua, parse
  both locale sections, diff. Reuse
  `dmr-tests`-adjacent script pattern:
  ```python
  setting_names = set(re.findall(r'name\s*=\s*"([^"]+)"', settings_src))
  # parse [mod-setting-name] and [mod-setting-description] from en/es cfg
  # assert setting_names == en_names == es_names == en_desc == es_desc
  ```

- **Prereq silently missing — dynamic generation runs BEFORE other mods'
  unlock-recipe effects** (v3.7.0, found via dump: 118/868 Bob's items): the
  dynamic generator builds `recipe_tech_map` (from tech effects `unlock-recipe`)
  in `data-updates`, but overhaul mods (Bob's) define their unlock effects in
  data-updates/data-final-fixes that run AFTER DMR's generation. Result: items
  that DO have a real unlock tech (bob-brass-chest→bob-brass-processing,
  bob-defender-robot→defender, bob-mech-brain→bob-walking-vehicle) get a
  replication tech with ONLY the tier-machine prereq (`['dmrsa-replication-1']`)
  — the original-tech prereq is silently omitted (no crash, no warn). This is
  the REVERSE of the v3.5.15 load-order race (there a mod DELETED a tech; here
  mods ADD unlock effects after DMR already snapshotted the map). Detection:
  dump-data + Python cross-check of every `dmrsa-tech-repl-<item>-tech` against
  `recipe_tech_map[item]`. Fix direction: (A4) new data-final-fixes PASS that
  rebuilds recipe_tech_map with final data and re-adds missing original-tech
  prereqs to already-generated techs; (A5) optional deps in info.json
  (`? bobplates`, `? bobwarfare`, ...) to force DMR data-final-fixes AFTER
  Bob's, same pattern as v3.5.15. Also remember the gate-test lesson: the user
  plays a REAL modlist (Bob's+SA+quality+CMO) — always verify against the real
  dump, never trust static review alone for prereq wiring.
