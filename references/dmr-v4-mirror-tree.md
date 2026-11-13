# DMR v4.0 — Mirror Tree + Factorio 2.1

Designed and implemented 2026-08-12. Zip `dark-matter-replicators-reborn_4.0.0.zip`
(108 files, 4.7MB) built, tests green (test_mirror 30/30, run_tests
34/34, step_filter ALL PASS).

## ⚠️ CURRENT STATUS 2026-08-13: gate test — 4 errors found and RESOLVED
The user's gate test in Factorio 2.1.14 passed 4 load errors, all
resolved in the final zip:
1. `Error in assignID: item with name 'dmrsa-replication-lab' does not exist` —
   cause: `assembler2pipepictures()` removed as a global function in 2.1;
   `replicators.lua` was failing SILENTLY (safe_require swallows the error) →
   the item was never defined. Fix: `require("__base__/prototypes/entity/
   assembler-pictures").assembler2pipepictures` (table, NO parentheses, with
   `__base__/` prefix — the require without prefix does not resolve from another mod).
   Affected replicators.lua and planetary-replicators.lua.
2. `Technology dmrsa-mirror-angels-chlorine-processing: Non-contiguous levels:
   2, followed by 4` — cause: the mirror tech takes the ORIGINAL tech as a direct
   prereq; its science-pack level (2-3) is shallower than its real depth
   in the tree (4). Fix: `MirrorGenerator.get_tech_tree_depth()` —
   memoized recursive and cycle-safe function; tier = max(science_level,
   tree_depth) when dmrsa-require-original-tech=ON.
3. The SAME error persisted even though fix 2 was in the zip — cause: missing
   optional Angel's deps in info.json (`? angelspetrochem` etc.);
   DMR ran its data-final-fixes BEFORE Angel's → the depth was calculated
   with incomplete prereqs. Fix: +12 Angel's deps (same A5 pattern as Bob's).
4. The SAME error persisted again — ROOT CAUSE: Angel's techs
   are LEVELED CHAINS (`angels-chlorine-processing-1..4`). Factorio treats
   techs with `-N` suffix as LEVELS of a composite tech; generating a
   mirror per level (`dmrsa-mirror-angels-chlorine-processing-1..4`) created
   a composite whose levels must be CONTIGUOUS — since level -3 did not
   unlock replicable items (recipes excluded), its mirror was skipped and
   the chain ended up 1,2,4 without 3. Fix: `normalize_tech_base()` — strip the
   `-N` suffix and group the ENTIRE chain into ONE mirror, with prereq = the deepest
   existing level (`mirror_deepest`). Lua pitfall: `string.find(name,
   "%-%d+$")` does NOT capture the number (no parentheses) — use `"%-(" .. "%d+" ..
   ")$"` or the depth tie-breaker is a no-op.
General lesson: a dynamic generation fix that reads the tech graph of
OTHER mods (recipe_tech_map, tree depth, prereqs) does not work without the optional
deps of EVERY overhaul family present in the modlist, and tech chains with
numeric suffix require grouping them into a SINGLE tech (see
`references/factorio-2.1-breaking-changes.md` sections Pipe pictures +
Non-contiguous + Leveled-tech chains).
Reversion backup intact: `backups/dark-matter-replicators-reborn_3.7.1-source-backup.tar.gz`.

## ⚠️ FIX 2026-08-23 (gate test 4.2.0): the depth clamp INFLATED tiers — the real fix was the -N chain normalization

Gate test 4.2.0 (real dump, 138 mods) exposed the side effect of fix #2:
user reported "because logistic science pack, chemical science pack are in tier 5"
+ "it seems like many things were bumped up in tiers". Dump-verified:

- Science pack mirrors wrong: `logistic`=5 (should be 1), `military`=5 (should be 2),
  `chemical`=5 (should be 3), `production/utility`=5 (should be 3), `automation`=2 (should be 1).
- Of 474 mirror techs: **216 with tier > SCL** (bumped by the clamp) and **154 with SCL
  nil** (fallback to max item tier).
- The deep modded tree (SA + planetaris + bob) produces enormous real depths:
  chemical=22, production=25, utility=29, space=39, promethium=80. `tier =
  max(SCL, depth)` → EVERYTHING at depth ≥5 goes to 5.

**KEY INSIGHT**: the depth clamp (fix #2, 2026-08-13) was an intermediate Band-Aid. The
real "Non-contiguous levels" error was caused by LEVELED CHAINS (`-N`), resolved
by `normalize_tech_base()` (fix #4). The clamp remained active and distorts the
entire progression in large mod trees. Fix direction (designed, PENDING
implementation + gate test): REMOVE the clamp (or cap it to the progression band) and
FORCE science packs by progression table.

**SECOND INSIGHT**: for science packs, SCL is NOT the right signal — the tech that
UNLOCKS the pack uses LOWER-TIER packs (the `chemical-science-pack` research
uses automation+logistic → SCL=1, but the PACK is tier 3). A science pack's tier =
its PROGRESSION POSITION (table v3.5.17: auto/logi=1, mili=2, chem/prod/util=3,
planetary=4, space/cryo/prom=5, mods gold/alien=5, numbered `science-pack-N` →
max(2,min(5,N))). For the mirror: `science_item_tier(name)` function with the SAME mapping
as `CostSolver.get_tier_from_tech` (cost-solver.lua ~line 400 — canonical source),
applied BEFORE SCL/fallback/depth for any item with "science-pack".
Watch the branch order: `advanced%-logistic` (→3) MUST be checked BEFORE the
generic substring `logistic` (→1), or bob-advanced-logistic falls back to 1
(lesson v3.7.0).

## v4.1.0 — Quality Refiner (2026-08-16)
New feature (quality does NOT come from the normal replicator; it comes from a dedicated
machine). See `references/factorio-2.1-breaking-changes.md` for the 4 prototype 2.1 errors
that appeared in the gate test (independent_probability, icon in
recipes quality, icon in techs, repeat_count of the shadow) — already documented there.
Feature summary:
- `dmrsa-refiner` (assembling-machine, category `dmrsa-refining`): upgrades replicable
  items +1 quality tier, NEVER skips (normal→uncommon→rare→epic→
  legendary). Decreasing probabilities per step (1% / 0.5% / 0.25% /
  0.1%), 5% item loss per cycle, retries with the same item for the remainder.
- Recipe per item×step (4 per replicable item), generated by
  `lib/refiner-generator.lua` after the mirror (reads dmrsa-repl-* recipes for
  base energy cost → ×10). Ingredients with fixed `quality`; results with
  `independent_probability`. `hidden=true` + own category (only visible in
  the refiner). Gate: only generated if `data.raw["quality"]["uncommon"]` exists.
- The refiner does NOT accept modules (module_slots=0) — the probability IS the balance
  (quality modules would break the ladder).
- Setting `dmrsa-replicator-quality` (default "Normal only"): the normal replicator
  sets `quality="normal"` in its recipes (faithful: replicates normal material);
  "Allow quality" = permissive mode (old behavior).
- Tech `dmrsa-replication-refining` (materials-5 + vanilla quality tech).
- Tests: dmr-tests/test_refiner.lua (41 checks). Placeholder graphic: own
  replicator-5.png sprite with obsidian-violet tint (NEVER vanilla sprite — see
  "own sprite" lesson in breaking-changes).
- Test harness pitfall: `data:extend(...)` is called as `data:extend(...)`;
  in the mock, `data.extend = function(self, tbl) ... end` (first arg is
  self) — if the mock uses `function(tbl)`, the method receives `data` as tbl and the
  assert fails.

## v4.2 (open design 2026-08-22) — baseline inflated by process OUTPUTS
**User symptom**: `dmrsa-replication-materials-1` unlocks "a huge amount of
things" with large mods. Real 4.1.0 dump (138 mods): materials-1 = **108 items**
(vs 16 from design). 1716 dmrsa-repl-* recipes (vs 945 from 3.7.1).

**Root cause (confirmed with dump)**: the mirror assigns the original tech by
`unlock-recipe` with **recipe-name == item-name** (1:1 assumption). Items that
are OUTPUTS of process recipes (Angel's petrochemistry/electrolysis/crushing:
`angels-gas-hydrogen`, `angels-mineral-sludge`, `angels-geode-*`,
`angels-ore1..6`, `angels-liquid-*`, `angels-crystal-*`) do not have a recipe with their
own name → the mirror cannot find their tech → they fall to baseline tier 1.
Real example: `angels-gas-hydrogen` ← `angels-water-separation` ← tech
`angels-basic-chemistry` (the unlock-recipe points to the producing recipe, not the
item).

**Diagnostic method (reusable, Python on data-raw-dump.json)**:
1. build `produced_by[item] = [recipe...]` iterating `recipe.results`
2. build `recipe_tech[recipe] = [tech...]` iterating
   `tech.effects` (type==unlock-recipe), filtering dmrsa-* and hidden techs
3. for each baseline item, check if any producing recipe is unlocked by
   a tech (exclude `*-recycling`, `recycling`, `empty-*/fill-*` recipes).
⚠️ Regex pitfall (bit twice): in Python patterns do NOT use the Lua escape
`%-`; write `r'-armor$'` with a normal hyphen. `r'%-armor$'` matches the literal
`%-armor` and filters nothing.

**Fix IMPLEMENTED (v4.2.0, 2026-08-22)**: assign tech via producing
recipes, with 2 safeguards against false positives:
1. no-minable (`data.raw.resource` do not inherit foreign tech — coal/iron-ore/etc.
   are legitimate baseline even though another recipe produces them as byproduct)
2. same mod prefix (an angels-* item only inherits from angels-* recipes).
   + explicitly exclude the `recycling` tech from the reverse-map (filtered as
   false "original tech" of `angels-ore1-crushed`) and `*-recycling`/`empty-*`/
   `*-unbarrel` recipes.
Measured result (CORRECTED re-simulation on dump): materials-1
108 → 25 legitimate items (coal, base ores, burner, base plates,
water/steam/crude-oil...); mirror 1328 → 1497 techs. Changes in
`lib/mirror-generator.lua` (pass 4b: `item_process_techs`) + `data-final-fixes`.

**Simulation pitfall (bit twice): `.match()` ≠ `.search()` in Python.** The
simulation predicted materials-1=30 and said plastic-bar/resin/rubber would
mirror a tech; the GAME (correctly) kept them at baseline tier 1. Cause: I used
`re.compile(r'-recycling$').match(rname)` — `.match()` ANCHORS to the start of the
string, so `"plastic-bar-recycling".match("-recycling$")` fails and the recipe
was NOT excluded → the item inherited the false "recycling" tech → mirror. In Lua
`string.find` is SEARCH, that is why the game differs. Rule: in Python sims of
Lua logic always use `.search()`, and when a sim-vs-game discrepancy appears
review the sim exclusions before trusting the framework.

**Design pitfall discovered**: overhaul mods REDIRECT vanilla unlocks
to their own recipes — with Bob's/Angel's the `plastics` tech
unlocks `bob-plastic-pipe`/`angels-solid-plastic`, NOT `plastic-bar` (which
has NO tech on the map, not even hidden). Consequence: base items like
plastic-bar/resin/rubber/wax/polysaccharides have no corresponding tech →
baseline → they were freebies in materials-1. Solution: the name-based tier
override (see MOD_ORE_TIERS in cost-solver) also covers non-ore MATERIALS
(plastic-bar→3, resin/rubber/wax/polysaccharides/sulfuric-acid/
nitrogen/nitric-acid→3, ammoniacal/lava/blood/lymph/royal-jelly→4, sand→2...).

**Materials tech fix (locale + pack)**: the 5 `dmrsa-replication-materials-N`
techs did not define an explicit `localised_name` (relied on per-tier key → rendered
raw key if missing) and `make_research_unit` could leave `ingredients = {}`
when the pack tenemut was not detected (tenemut is a TOOL prototype, not
item) → the tech appeared to have "no research cost". Fixes: `localised_name = {
"technology-name.dmrsa-materials-tech", def.tier }` (explicit template) and
pack fallback that uses ANY existing DMR material if the specified one
fails (never empty ingredients).

**Separate issue (not touched by the fix)**: with 138 mods the cost-solver degrades —
iron-plate/copper-plate dropped from tier 3 (dump 3.7.1) to tier 1 (dump 4.1.0)
because more recipe cycles resolve to 1. Mod ores (angels-ore1..6,
planetaris-*) also drop to tier 1. If revisited, expand MOD_ORE_TIERS /
review the cost-solver, not the mirror.

## v4.2 FIX (2026-08-23): depth clamp REMOVED + science packs forced — tier inflation
**Symptom (gate test 4.2.0)**: "many things were bumped up in tiers", logistic/chemical
science pack in tier 5. Real dump (138 mods): **458/474 mirror techs in replication-5** (97%).

**Root cause (2 stacked causes)**:
1. The **tree-depth clamp** (`tier = max(science_level, get_tech_tree_depth(orig_tech))`,
   added in the 4.0 gate test as belt-and-suspenders against "Non-contiguous levels")
   inflates EVERYTHING with real modlists: chemical-science-pack has depth 22,
   promethium-science-pack depth 80 (modded tree depth is NOT the progression).
2. **Unforced science packs**: the SCL of the tech that unlocks a pack ≠ the pack's
   progression tier (chemical-pack is researched with t1 packs → SCL=1, but the PACK is
   progression tier 3; its recipe was also inflated by the cost-solver chain).

**Fix applied in lib/mirror-generator.lua**:
- RECIPES: `local sci_forced = PACK_LEVELS[name] or MOD_PACK_LEVELS[name]; if sci_forced then tier = sci_forced end`
  after the tenemut override.
- MIRRORS: `forced_science_tier` = max PACK_LEVELS/MOD_PACK_LEVELS across the group's
  ITEMS (EXACT table lookup, no name heuristics on arbitrary items); if present,
  forces the tier before the SPREAD_TECHS/SCL branch.
- **Depth clamp REMOVED** (comment explains why). The REAL contiguity hazard was
  the leveled `-N` chains, already covered by `normalize_tech_base()`. If Factorio again
  rejects a specific mirror for contiguity, fix THAT chain — not the whole tree via depth.
- `get_tech_tree_depth()` remains defined but uncalled (in case diagnostics are needed).

**FINAL RESULT (faithful sim to code + active adaptable inference, see next section)**:
distribution 0/4/8/4/458 → **88/15/144/3/180** (+44 cost-solver fallback).
Exact science packs: auto/logi=1, military=2, chem/prod/util=3, planetary=4,
space/cryo/prom=5. (The first sim reported 253 in t1 because it did NOT replicate
`mirror_deepest` — see simulation fidelity pitfall below.)

**General lesson**: a defensive clamp against a specific load error ("Non-contiguous")
that scales with TREE DEPTH is a time bomb with overhaul mods — the modded
tree has depths of 20-80 that have nothing to do with the 1-5 progression. Always
validate the resulting DISTRIBUTION on the real dump before publishing (Counter of prereqs
replication-N), not just the absence of a crash.

### v4.2 continuation (same day, 2026-08-23): ADAPTABILITY + simulation fidelity + handoff
- **DESIGN DECISION (user): the mod must be ADAPTABLE to any modlist, not
  just ours.** Implemented as `ensure_inferred_pack_levels()` in
  mirror-generator.lua — IMPORTANT: declare BEFORE `pack_level` or the upvalues
  resolve as nil globals (hit and fixed live). Unknown packs are
  anchored dynamically: `level(P) = max table-level among visible non-hidden techs
  that consume P`, excluding kitchen-sinks (>8 distinct ingredients) so that
  endgame mega-techs do not drag early packs to L5. A single pass, no recursion,
  derived only from already-tabulated levels → no cycles. Testable getter:
  `MirrorGenerator.get_inferred_pack_level()` (+5 tests in test_mirror.lua → 54 checks).
  Measured on 138-mod dump: galvanization/golden/planetaris/apicultural/token-bio → L5.
- **SIMULATION FIDELITY PITFALL (new instance of the sim-vs-code class)**:
  when simulating mirror tiers in Python you MUST replicate `mirror_deepest` — resolve the
  base name to its deepest existing `-N` level before computing SCL (regex index
  base→level over real dump names). The sim without this reported 253 techs in
  tier 1; the faithful one gave 90 — and the user spotted the anomaly ("check tier 1 because
  there are too many"). Rule: when a sim contradicts user intuition, audit
  FIRST the sim's fidelity to the Lua code before proposing design changes.
  The 90 t1 turned out to be legitimate: REAL SCL=1 from the user's modlist (Bob's moves
  advanced-circuit to green science; Angel's metallurgy-1/2/ore-crushing ARE early game).
- **Cross-agent handoff (project pattern)**: the repo root maintains `AGENTS.md`
  as state doc for external agents — opencode reads it automatically when working
  in that folder. Contents: what the mod is, exact status (portal vs local), gate test fixes with
  root causes, current design decisions, architecture and load order,
  verified workflows, critical pitfalls, open issues. KEEP it up to date
  after each major state change; it is the Hermes↔opencode contract.
- **BATCH F1-F4 — APPLIED (2026-08-23, v4.2.1 ready**; original specs in
  `research/nosotros-fix-specs.md`): gate test PASSED → 4.2.0 published → single batch.
  F1 `%-vequip$` (6 Angel's vehicular: burner-generator, fusion-reactor,
  repair/construction-roboport, heavy-energy-shield + rocket-defense hidden —
  MECHANISM of the escape: they are `type="item"` with `place_as_equipment_result`,
  so they also escape the vehicle registry, not just bob-vehicle-*/equipment),
  F2 `^rpg_.*_potion$` (8 potions), F3 `MOD_ORE_TIERS` floors (see §consumables).
  Tests: test_mirror 49→68 (+19: 5 vequip + 8 potions + anti-collision
  `angels-accessory` KEPT — note: the KEPT fixture needs a producing recipe in the
  mock or the eligibility filter fails, not the exclusion).
- **INSIGHT: recycling-circularity makes drop-only items replicable** — the auto-generated
  `-recycling` recipes (disabled, hidden) COUNT as producers in the eligibility
  rule, so an item whose only recipe is its own `-recycling` passes
  the filter (confirmed: `dmrsa-repl-rpg_*` exist in the dump = they were replicable).
  On the dump, the sim with ports that EXCLUDE recycling from the producer map gives
  delta −5 (only vequip) while the real game gives −13: expected discrepancy between
  sim and game — reconcile by counting recipes in the eligibility rule the
  SAME way as `is_produced_by_recipe` in the code, not like `build_recipe_map`.
- **fission-construction-robot anomaly VERIFIED (dump)**: no real producing
  recipe (only disabled `-recycling` + `-macerating` which CONSUMES it; never unlocked by
  tech), `hidden_in_factoriopedia=true`, `place_result` to own construction-robot
  entity → probably delivered by script/event or orphaned from the mod. KEEP t3
  maintained; verify in-game acquisition when testing 4.2.1.
- **v4.2.1 status**: zip built (114 files, parity with portal without ROADMAP/FAQ, version
  bump in info.json, changelog prepend NORMAL — accumulated-NOTE only applies when
  there are multiple unpublished versions, not in patches), suite 68+54+41+step_filter
  PASS, privacy CLEAN. RESOLVED: user uploads zip to portal from their PC;
  **GitHub push of 4.2.1 SKIPPED per user decision** (portal only this time)
  — AGENTS.md was updated with that decision. Workflow lesson: for THIS
  user the GitHub push is per-version OPTIONAL — ask before pushing, do not
  assume; the push itself may require gate command approval (`rm -rf` of the
  temp clone + force push → blocks waiting for consent).

## Balance: tenemut replicable ONLY at tier 5 (2026-08-13, "Dark Matter Dominance")
User decision: tenemut (mod raw material / research currency)
is NOT replicable until tier 5 — thematic cycle closure: you reach
replicator-5 → you master dark matter → you can replicate ITS raw material.
All other `dmrsa-*` items (scoop, transducer, conduit, lab, replicators)
remain non-replicable (anti-loop).
Implementation (2 files):
- `lib/target-mapper.lua`: the anti-loop prefix rule for `dmrsa-` now
  EXCLUDES only `name ~= gprefix .. "tenemut"` — tenemut passes the filter.
- `lib/mirror-generator.lua`: in the recipe loop, `if name == gprefix ..
  "tenemut" then tier = 5 end` — falls to baseline tier 5 → unlocked with
  `replication-materials-5` (tier 5 machine + conduit).
Discarded alternative: tier 4 (would make tier 5 packs trivial); replicable
from the start (would break ALL mod balance). Tenemut DERIVATIVES
(scoop/transducer/conduit) could be replicated at their natural tier without
breaking anything (bottleneck is still mined tenemut) — left as a future
decision; user preferred to keep them non-replicable for now.

## Why it exists
The v3.x category→tier system (see skill dmr-category-tier-refactor) did NOT gate
the progression for real. Dump analysis: 46% of items in `general` (no floor),
503 items whose tier did not match the science level of their original tech, and 25
endgame offenders in tier 3 (requester-chest, mech-armor, nuclear-fuel, ...).
Root cause: the cost-solver (ingredient chain) is a bad signal for
progression; the correct signal is the item's ORIGINAL TECH.

## The system
- ONE replication tech for each ORIGINAL game tech: "Replication:
  Logistic System" unlocks the replication recipes for ALL items that
  tech unlocks.
- Grouped Categories ELIMINATED. Categories (shape/alloy/chemical/...)
  remain ONLY as visual subgroups in the crafting menu.
- Tier of each mirror tech = science level of its original tech (automation/
  logistic=1, military=2, chemical/production/utility=3, planetary=4,
  space/cryogenic/promethium=5). Mod packs: bob-science-pack-gold,
  bob-alien-science-pack-* → 5 (table MOD_PACK_LEVELS).
- Progression chain: replication-N (machine) → replication-materials-N
  (base materials for the tier, with tenemut/scoop/transducer/conduit) → mirror
  techs (prereq: machine + materials + original tech if
  dmrsa-require-original-tech=ON).
- threshold=1: every original tech with ≥1 replicable item generates its mirror
  (no minimum group size).
- Items WITHOUT original tech (ores, fluids, plates, basic vanilla, ~88-93) →
  baseline, unlocked by the materials tech of their tier.
- Planetary items (50, subgroup dmrsa-replication-resources) keep their
  routing to the planetary techs (vulcanus/fulgora/gleba/aquilo).

## Exclusions v4.0 (144 items) — approved by user 2026-08-12
EXCLUDED (single-use, no mass production): guns (11), armor (10), combat
capsules (10: grenade/capsule/explosives/poison/slowdown/defender/
distractor/destroyer/fire/laser-robot patterns), vehicles (27: car/tank/spider-vehicle/
locomotive/cargo-wagon/fluid-wagon/artillery-wagon), vehicle equipment (50:
bob-vehicle-*), personal equipment (36: `*-equipment$` EXCEPT solar/battery).
KEPT (mass use): ammo (55, aliens), fuel cells (10, reactors), seeds (3,
Gleba), raw-fish (healing), solar panels + batteries (9).

## Files
- `lib/mirror-generator.lua` (NEW) — recipes + reverse map (tech → items) +
  mirror techs + attach baseline→materials. Returns planetary_unlocks.
- `lib/target-mapper.lua` — `is_v4_excluded()` (types + patterns).
- `data-final-fixes.lua` — PASS 0 chooses Mirror (default) vs Individual (legacy);
  PASS 6 (re-attach) ELIMINATED (unnecessary: reverse map is built with final
  data and the prereq IS the original tech).
- `prototypes/technologies/technologies.lua` — 5 replication-materials-N techs
  (empty effects, filled in generate()).
- `settings.lua` — `dmrsa-require-original-tech` (bool, default true);
  `dmrsa-tech-distribution`: "Mirror" (default) / "Individual" (legacy v3.x).
- `defines.lua` — dmrsa_is_v21() ELIMINATED (2.1 only, categories array).
- `info.json` — 4.0.0, factorio_version "2.1".
- `prototypes/recipes/dynamic-generator.lua` — kept as legacy Individual
  generator; grouped disabled (use_grouped_techs=false).
- locale en/es-ES — dmrsa-mirror-tech, dmrsa-materials-tech,
  replication-materials-1..5, setting require-original-tech. 2026-08-14:
  `dmrsa-matter-conduit` renamed to "Nanophase Conduit" (EN) / "Conducto
  nanofase" (ES) — only renaming applied from the proposed batch.
- `dmr-tests/test_mirror.lua` (NEW) — 30 checks: get_tech_science_level +
  v4.0 exclusions. Run with lua5.2.

## Material renaming + new tier 5 item (PROPOSAL 2026-08-13 → MOSTLY DISCARDED 2026-08-14)
User wanted to redo tenemut/scoop/transducer/conduit icons, rename them
and ADD A NEW ITEM for tier 5 (today tier 5 reuses matter-conduit in
`technologies.lua` materials_defs: `{tier=5, pack=gprefix.."matter-conduit"}` and in
`tier_material_pack()` of mirror-generator: tier 4 AND 5 → matter-conduit).
Original proposal (theme: progression of mastery over reality): Tenemut (kept),
**Resonance Latch** (today scoop), **Atomic Loom** (today transducer), **Nanophase Conduit**
(today conduit), **Genesis Loom** (NEW item `dmrsa-genesis-loom`, closes the arc with
tenemut tier-5). IMPORTANT (if revisited): keep internal IDs and change ONLY display
names via locale → zero broken-save risk; tier 5 is indeed a new ID + recipe. Will touch:
dark-matter.lua, base-recipes.lua, technologies.lua (pack tier 5), tier_material_pack(),
locale EN/ES, icons.
**FINAL STATUS 2026-08-14 (user decision)**: the full renaming was not convincing and was
DISCARDED. Only applied `matter-conduit` → "Nanophase Conduit" (EN) / "Conducto nanofase"
(ES) in locale — without touching IDs, recipes, or techs. Genesis Loom remains UNIMPLEMENTED
(shelved, no date). AI icons were fully discarded (see below). Do not resume
renaming or Genesis Loom without explicit user request.

## API icon generation (2026-08-13 verified → 2026-08-14 DISCARDED)
See `references/dmr-icon-assets-generation.md`. FINAL STATUS: user DISCARDED
AI image generation (Gemini gave cartoon ×2, Canva Pro gave 3D renders) and asked
to remove references and research. Verified data still documented there in case
some day it is revisited: opencode-go does NOT generate images (25 models, all chat/text);
GOOGLE_API_KEY and OPENROUTER_API_KEY valid in ~/.hermes/.env; Google free-tier
429 quota 0 for image models; OpenRouter has the models but the account requires
adjusting data-policy in openrouter.ai/settings/privacy (404). The coherent family prompt
(palette #0a0a14/#7c3aed) and anti-cartoon/anti-3D anchoring are also in that reference.

## Numbers (dump 3.7.1, Bob's+SA)
945 items → 144 excluded → 801 replicable → 713 with original tech → ~417
mirror techs (300 single + ~117 multi) + 5 materials + 4 planetary ≈ 426 techs
(vs 945 individual in v3.x).

## User workflow preferences (observed 2026-08-12)
- Design-first: brainstorming with A/B/C/D options → choose → VERIFY with
  dump data BEFORE implementing.
- When the user references a brainstorm option ("option A", "the
  threshold", "individual"), RE-READ all messages from that point before
  interpreting — the shorthand may mean something different from the obvious reading
  ("individual" = threshold-1 mirror, NOT per-item techs; the misunderstanding cost
  several round-trips).
- Major redesigns: keep the published version intact, create backup tar.gz
  before touching, work with revert safety.
- Quality support: IMPLEMENTED in v4.1.0 (Quality Refiner) — see section
  v4.1.0 above. Baseline inflated by process outputs (v4.2): IMPLEMENTED
  in v4.2.0 (fix process-output techs + universal materials tier override) —
  see section v4.2. Pending for another iteration: global cost-solver
  degradation with 138 mods (iron-plate 3→1) and final modlist review
  after the gate test.
