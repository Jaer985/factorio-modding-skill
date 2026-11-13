<!-- Split out of SKILL.md on 20261101T050205Z; body is verbatim bullet text from the original
     'Common pitfalls' section, grouped by theme. Index: SKILL.md. -->

# Pitfalls — tiers, cost model, science packs and balance

- **Item subgroup categorization**: items MUST use mod-defined subgroups, not
  vanilla (e.g. `"production-machine"`). Vanilla subgroups leak the item into
  the wrong inventory tab.

- **Locale-defined subgroup/category names**: any new `type="item-subgroup"` /
  `type="recipe-category"` requires a locale entry or Factorio displays the
  raw key.

- **Recipe-category coverage gap**: when Factorio releases new expansions, all
  category-keyed lookup tables need a coverage pass. **And SA category names
  drift** — verify against the live data dump, never trust remembered names:
  real SA categories are `cryogenics`, `electromagnetics`, `metallurgy`,
  `organic`, `captive-spawner-process`, `hand-crafting` — NOT
  `cryogenic`/`electromagnetic`/`metallurgic`/`organic-or-egg`. DMR v3.5.7
  added entries under the wrong names, so foundry (metallurgy), electromagnetic
  plant, cryogenic plant, and biochamber (organic) recipes silently fell to
  the neutral 1.0 fallback. Extraction recipe: grep `category = "X"` and
  `categories = { ... }` literals from
  `space-age/prototypes/recipe.lua` and diff against your table's keys.
  See `references/dmr-machine-efficiency-sa-category-drift.md`.

- **BASE_RESOURCE_COSTS coverage gap**: every minable resource (vanilla, SA,
  mod-added) must have an entry, otherwise the cost-solver's recursive fallback
  assigns tier 1 — items meant for endgame become available from the simple
  replicator. Cross-reference against official Factorio data dumps.

- **Fluid-without-recipe tier gap**: fluids that are passive building outputs
  (no crafting recipe) fall through the same gap. Need a separate
  `FLUID_TIER_OVERRIDES` table for fusion-plasma and similar SA fluids.

- **Category-name → tier-floor → required-tech chain**: name substrings (`plate`, `brick`) land
  items in `alloy`/`shape` with tier floors ≥ 2, so items that feel early-game need chemical
  research. By design, but it surprises players; the detection rule and the full chain live in
  `references/audit-and-release.md`.

- **Cost-solver fallback tier pollution**: `solve_cost`'s two hardcoded fallbacks (cycle →
  tier 1, unknown recipe → tier 2) pin overhaul-mod intermediates at the bottom and flood
  low-tier grouped techs with mid/late-game items. Fix: both fallbacks go through
  `recipe_tech_map` → `get_tier_from_tech()` when the unlock tech exists, and skip the
  `ingredient_tier + 1` cap when the ingredients resolved to tier 1 (ambiguous between simple
  and degraded). Full chain in `references/audit-and-release.md`.
 - **Target blacklist for non-replicable utility items** (v3.5.12): the target
 mapper includes EVERY item of `item`/`tool`/`spidertron-remote`/etc. types by
 default. Player-carried UI utilities have no replication value and pollute
 the tech lists: red-wire, green-wire, copper-wire, artillery-targeting-remote,
 discharge-defense-remote, spidertron-remote, blueprint, blueprint-book,
 deconstruction-planner, upgrade-planner, copy-paste-tool, cut-paste-tool,
 selection-tool, rail-planner. Also exclude **filled barrels** (fill-<fluid>-barrel
 and <fluid>-barrel patterns) — they let players duplicate fluids without a
 replication recipe for the fluid itself; keep the empty `barrel` replicable.
 Implement as a `TARGET_BLACKLIST` lookup set + a pattern predicate in
 `lib/target-mapper.lua` (the original fork had NO such mechanism — only
 self-replication prefix + hidden-item filters). User reports of "why can I
 replicate red wire / spidertron remote" are the trigger.
 - **SA item-name drift** (v3.5.13): Space Age internal names change between
  data versions and are easy to get stale. DMR had `carbonaceous-asteroid-chunk`
  but the real SA name is `carbonic-asteroid-chunk` — a silent failure: the
  item wasn't in `BASE_RESOURCE_COSTS` (fell to low-tier fallback) AND missed
  the hidden-item whitelist in target-mapper. When mapping SA items, verify
  exact names against the live data dump
  (`raw.githubusercontent.com/wube/factorio-data/master/space-age/prototypes/`),
  never trust memory or older code. User symptom: an asteroid/SA item shows in
  an early replication tier when it should be tier 4-5.
 - **Category-split by progression tier** (v3.5.14): when a whole replication
  category is gated too late vs vanilla (all modules at tier 5, all weapons at
  tier 4), split it into base + advanced subcategories keyed on name patterns.
  DMR: `module` (tier 3) vs `module-advanced` (`*-module-3`, tier 4);
  `military` (tier 3: pistol/shotgun/magazines/grenades) vs `military-advanced`
  (uranium/artillery/explosive-rocket/cluster/spidertron/nuke, tier 5). Steps:
  (1) add both keys to `repltypes.lua` with distinct tiers; (2) in
  `get_item_category`, return the advanced key when name matches advanced
  patterns; (3) add locale entries for BOTH new keys in `[replcategory-name]`
  EN + ES — parity check mandatory. Player symptom: "I don't see modules or
  weapons to replicate at tier 3" — the category floor was too high, not a bug
  in generation.
 - **Placeable items use [entity-name] locale, not [item-name]** (v3.5.21):
  any `type = "item"` with `place_result` (chests, furnaces, miners,
  inserters, electric poles, assemblers, walls, labs — 93 in base) has its
  display name in `[entity-name]`, NOT `[item-name]`. Building a
  LocalisedString `{ "item-name." .. name }` for these produces
  `Unknown key: "item-name.X" replication (Recipe)` warnings at runtime for
  EVERY placeable item. Detection: when the user pastes a batch of
  `Unknown key: "item-name.X"` warnings where X are placeables, the fix is in
  the `loc_prefix` selection: check `item_proto.place_result` → use
  `entity-name`. This is the SAME class as the `"?"` parameter pitfall —
  locale namespace selection must match where the name actually lives.
 - **Replication subgroups by category** (v3.5.21): to make the replicator
  crafting menu navigable, register one `item-subgroup` per replication
  category (`dmrsa-replication-<cat>` mirroring `replcategory-name` keys) and
  set the dynamic recipe's `subgroup` from `item_category` instead of tier.
  Keep the tier subgroups defined (backward compat). Planetary items used to be forced
  onto `replication-resources`; since v4.5.1 they keep their CATEGORY subgroup — the planet
  gate is already enforced by the machine category, and that override is what left 65
  recipes (all four planet science packs, recyclers, soils) in a single row. Requires
  locale entries in `[item-subgroup-name]`
  for ALL 16 category subgroups in EN + ES — parity check mandatory. Addresses
  player feedback "create subgroups for replication so that is easier to find
  it".
 - **Lab inputs PASS 4 — include tier-5 packs + defensive warn** (v3.5.22):
  the replication-lab's `inputs` must accept every science pack that grouped
  techs require. The SA pack list was only the 4 planetary packs; tier 5
  techs also need `space-science-pack` and `promethium-science-pack`. After
  the add-loop, run a second loop that WARNS if any intended pack is still
  missing (or if the lab/inputs table is nil) — surfaces "no lab will accept
  all the science packs" at load time instead of failing silently at research.
 - **Startup string-setting for cosmetic order** (v3.5.23): a `string-setting`
  with `allowed_values` is the clean way to expose a display-order choice
  ("DMR Item First" vs "Science Pack First"). Wrap the insertion in a tiny
  local helper (`add_research_pack(packs, pack, is_dmr_item)`) that
  `table.insert(..., 1, pack)` for the DMR item when the setting is
  "Science Pack First" — apply in BOTH individual and grouped flows (they
  have identical research_packs blocks; grep for the comment marker and patch
  with replace_all). Cosmetic changes must be flagged as Features, not fixes.
 - **Icon mipmaps misrender in copied icons** (v3.5.24): when you copy an
  item's `icons` array into a bordered 128x128 tech icon via deep_copy,
  KEEPING `icon_mipmaps` misrenders (shows only the top-left corner) for
  large/custom-icon items — mipmaps belong to the original rendering
  pipeline, not to your rescaled composite. Always `spec.icon_mipmaps = nil`
  on copied layers and nil-safe `icon_size` per layer (`if type(isize) ~=
  "number" or isize <= 0 then isize = 64 end`). Inherited from upstream
  0.8.0; symptom: "item shows only its top-left corner on the tech icon".
 - **Idle animation without new assets**: a dimmed `idle_animation` on the SAME
  sprite sheet makes a machine visibly stop when starved — zero new art. The
  load-time rules (frame_count / animation_speed) and the art-not-frame scaling
  rule live in `references/machine-graphics-pitfalls.md`; gate graphics_set
  changes on the in-game test, not on review.
 - **Version bump: minor jump with accumulated changelog** (v3.6.0): when
  many patch releases have piled up since the last PORTAL-published version
  (here: 3.5.19 published, 3.5.20-3.5.25 local only), a minor bump (3.6.0) is
  appropriate — but the changelog entry must SUMMARIZE everything the portal
  audience hasn't seen (features / changes / bugfixes sections), with the
  individual entries still below for reference. Keep `factorio_version` at
  the value players actually run unless you've decided to drop older support
  (dual-compat code means 2.0 declaration still loads fine on 2.1; bumping to
  "2.1" would exclude 2.0 players). Update ALL docs in the same pass:
  ROADMAP "última versión publicada" line, mod-portal-description.md
  (settings table defaults like grouped cost multiplier 5→10, stale item
  names like carbonaceous, new features list), FAQ GitHub link (points at the
  upstream fork — update to the maintainer's repo). A stale docs pass after a
  big release is cheap; skip it and the portal description lies about the mod.
  - **Step-item filter for overhaul mods** (v3.6.3): with Bob's/Angel's/K2, the
  dynamic target-mapper includes hundreds of one-step intermediates (bearing
  balls, internal projectiles/warheads, roboport parts, grinding/polishing
  wheels, robot sub-parts, small alien artifacts, processor components) that
  are NOT worth replicating — they only feed one more recipe. They pollute the
  replication lists and tech trees. Fix: hybrid filter in target-mapper —
  LEVEL 1: name patterns (`%-bearing%-ball$`, `%-projectile$`, `%-warhead$`,
  `roboport%-antenna%-`, `roboport%-chargepad%-`, `roboport%-door%-`,
  `%-grinding%-wheel$`, `%-polishing%-wheel$`); LEVEL 2: explicit exclusion
  list (ground truth from the upstream fork's `replvar` calls in
  `replications/bob.lua` — bearing balls, gem consumables, projectiles,
  roboport parts, robot brains/tools/frames, small alien artifacts,
  `bob-basic-electronic-components`, `bob-electronic-components`).
  **CRITICAL LESSON**: do NOT use a consumer-graph heuristic ("item consumed
  by ≤N recipes = step") — it over-excludes massively (460+ items including
  aluminium plates, science packs, machines, gear wheels). The graph cannot
  distinguish "valuable material used in few recipes" from "useless step";
  the upstream's manual judgment (replvar) IS the ground truth. Vanilla items
  must never be excluded. Test with a Lua harness (dmr-tests/test_step_filter.lua)
  asserting step items are excluded and real materials are kept.
  **Sweep ALL replications/*.lua, not just bob.lua**: the upstream fork has
  per-mod files (angel.lua, yuoki.lua, many_mods.lua, krastorio2.lua, ...).
  `replvar` with no cost = exclusion (extract with
  `re.findall(r'replvar\("([^"]+)"', src)` and check if a cost arg follows).
  angel.lua excludes 14 petrochem intermediates (gas-*, liquid-nitric-acid,
  solid-sodium-*); bob.lua excludes base bullets too (bob-bullet, bob-ap-bullet,
  ... not just X-bullet-projectile) plus silicon-carbide and
  long-handed-inserter. Files with only repltech_recipe calls are whitelist
 assignments (category/tier for known items), not exclusions — no action
 needed for the dynamic generator.
 **Reusable analyzer**: `/tmp/bob_step_analysis.py` (from the 2026-08-11
 subagent batch) parses Bob's zips with a comment-aware Lua block parser and
 cross-references ALL recipes in the modlist (including `bobmods.lib.recipe.*`
 dynamic edits, which wire ~90% of Bob's consumption). Re-run it with
 different `TARGETS` when adding new overhaul mods to detect their step
 items automatically. Note: ~0 step items have `hidden` flags — the explicit
 filter is required, the hidden filter alone misses them all.
 **Eligibility rule — the real junk-tech killer** (v3.6.4): the deepest
 cause of "useless research" with mods is NOT mis-tiering — it's that the
 dynamic target-mapper includes items the player can NEVER obtain
 legitimately: phantom/spawn-only items (no producing recipe, not minable,
 not hidden — e.g. factorissimo `factory-*` internals, drop-only artifacts,
 future mod internals). Fix in target-mapper: an item is eligible iff
 produced by ANY recipe OR minable (`data.raw.resource` has an entry) OR in
 an explicit whitelist (asteroid chunks, bob alien artifacts, SA plants —
 legitimate no-recipe items). The produced-set is built lazily from
 `data.raw.recipe` results (handle `recipe.normal.results` for 2.0).
 This scales to FUTURE mods with zero maintenance — unlike per-mod exclusion
 lists. Test: fixture with a phantom item (no recipe, not minable) must be
 excluded while craftables/minables/whitelisted stay (17/17 PASS).
 **Auto-hide empty categories** (v3.6.4): after the dynamic generator runs,
 count recipes per category subgroup (`dmrsa-replication-<cat>`) in a
 data-final-fixes PASS; if a category has ZERO recipes, set
 `data.raw["item-subgroup"][sg] = nil` so the replicator crafting menu shows
 no empty tabs. Zero config beats nihil's 16 per-category bool settings —
 the same UX problem solved automatically. Tier fallback subgroups are never
 removed.
 - **Evaluate upstream features BEFORE porting; prefer automatic over
   config-heavy** (2026-08-11, nihil fork review): after mining the upstream
   fork for exclusion data, the user asked \"realmente vale la pena? O podemos
   hacerlo mas avanzado y mejor?\" about the remaining nihil features. Verdict
   that landed: DON'T port per-category `repltype-<name>` bool settings (16
   checkboxes = config noise; user wants minimal-viable), DON'T port
   device2-5 categories (our cost-solver already computes tiers dynamically —
   redundant), DON'T port per-mod whitelists (our dynamic generation replaced
   that approach). DO consider: auto-hide empty replication categories (if a
   category has no items after step filtering, don't generate its subgroup/
   techs — zero config, automatic), and research-difficulty-style global
   balance multipliers (we already have them). **Implemented 3.6.4**: PASS 5
   in data-final-fixes counts recipes per category subgroup and removes empty
   ones (`data.raw[\"item-subgroup\"][sg] = nil`). Rule: when reviewing an
   upstream fork for features, classify each as (a) port as-is, (b) port
   improved/automated, (c) skip — justify skips with the user's
   minimal-viable + automation preference. See
   `references/dmr-nihil-feature-evaluation.md`.
 - **Mod-ore tier mapping in the dynamic resource fallback** (v3.7.0 A1): the
   `initialize_base_resources()` fallback used to map EVERY unlisted minable
   resource to tier 1 / cost 1.5. With Bob's/Angel's that made endgame ores
   (gold, tungsten, gems, thorium) replicable from the tier-1 replicator.
   Fix pattern: `MOD_ORE_TIERS` — an ordered array of {pattern, tier} pairs
   matched by substring against the result name, applied inside the fallback
   (tin/lead/zinc/nickel/silver/quartz/graphite/sulfur→2, bauxite/rutile/cobalt/
   chrome/manganese→3, gold/thorium/tungsten/titanium/platinum→4, gem/iridium/
   osmium/neodymium→5), with cost scaled ~tier^1.5. Order matters: specific
   materials first (tungsten before tin). This is the SAME class as the
   BASE_RESOURCE_COSTS coverage gap — the static table covers vanilla/SA, the
   material map covers mod-added ores automatically.
   **B5 follow-up (v3.7.0)**: verify the pattern list against the ACTUAL ore
   names in the dump — `"gem"` alone does NOT match Bob's individual gem ores
   (`bob-amethyst-ore`, `bob-diamond-ore`, `bob-emerald-ore`, `bob-ruby-ore`,
   `bob-sapphire-ore`, `bob-topaz-ore`), which bobores generates from
   `bob-gem-ore`; they silently fell to the tier-1 fallback (dump-verified:
   assigned 1, real 5). Add explicit per-variant patterns (amethyst, diamond,
   emerald, ruby, sapphire, topaz → 5). General rule: when a mod generates
   N named variants from one base material, the material map needs each
   variant name, not just the base — the dump's `resource.json` section is
   the ground truth for what actually exists.
 - **Overhaul-mod military patterns** (v3.7.0 A2): the `military-advanced`
   category (tier 5) originally matched only vanilla endgame ordnance
   (uranium/artillery/cluster/nuke/spidertron). With Bob's, endgame weapons
   (bob-sniper-rifle, bob-gatling-gun, bob-laser-rifle, bob-plasma-*,
   bob-laser-turret-3..5, bob-power-armor-mk3/4/5, bob-tank-2/3) fell into
   `military` (tier 3) and were replicable too early. Fix: extend the pattern
   list with mod-endgame name patterns (`sniper`, `laser%-rifle`, `gatling`,
   `plasma`, `turret%-[3-9]`, `armor%-mk[3-9]`, `mech%-`, `tank%-[2-9]`).
   Do NOT relax the ingredient_tier+1 cap to fix this — name patterns are
   more reliable and avoid false positives.
 - **Fluid eligibility + step filter** (v3.7.0 B1): the target-mapper's fluid
   loop only filtered gprefix+hidden; step items and phantom fluids were
   replicable directly (Angel's petrochem gas/liquid intermediates, mod fluid
   internals). Fix: apply `is_step_item` AND an eligibility check to fluids —
   `is_produced_by_recipe OR is_minable_resource OR CostSolver.is_known_resource`
   (expose a `CostSolver.is_known_resource(name)` checking BASE_RESOURCE_COSTS
   + FLUID_TIER_OVERRIDES). Keep water/crude-oil/steam/fusion-plasma eligible;
   exclude gas-ammonia (step) and phantom fluids.
 - **MACHINE_EFFICIENCY substring fallback** (v3.7.0 A3): the machine-efficiency
   table only covered vanilla/SA categories; Bob's categories (bob-assembling-*,
   bob-electrolysis, bob-mixing-furnace, electronics, ...) fell to neutral 1.0.
   Two-part fix: (1) explicit entries for the most common Bob's categories
   (assembling-1..6=56/90, chemical/mixing-furnace=1/3, electrolysis=140/81,
   distillery/air-pump=14/9, void/water-pump/barrelling=1.0, electronics=56/90);
   (2) substring fallback in the lookup loop — `string.find(cat, "smelt")`→1/3,
   `"chem"`→56/90, `"electro"`/`"centri"`→140/81, `"distill"`/`"refin"`/
   `"petro"`/`"oil"`→14/9, `"assembl"`/`"craft"`→56/90, `"crush"`/`"void"`→1.0.
   Generalizes to future overhaul mods without per-mod entries.
 - **Overhaul-mod auto-detection for defaults** (v3.7.0 C1): instead of asking
   the player to tune balance when running Bob's/Angel's/K2, detect the mods in
   settings.lua (`OVERHAUL_MOD_NAMES` list) and raise the default of the
   grouped-tech cost multiplier (10.0→15.0). Zero-config; the setting stays
   user-overridable. Document the auto-adjust in the setting description in
   BOTH locales (parity check mandatory).
 - **Locale descriptions can contradict actual behavior** (v3.7.0 D2): after a
   balance/progression change, audit descriptions against the CODE, not the
   other way around. DMR's `dmrsa-replication-3` tech description still said
   tier 3 was "gated by planetary replication technologies" — FALSE since
   v3.5.17 moved the Chemical Replicator BEFORE the planets (it uses chemical
   science packs only). `replication-penalty` said "added to the cost" when the
     code multiplied by `(1 + penalty)` — NO LONGER TRUE SINCE v4.2: the penalty
     is a FIXED +0.5 SUM (original DMR model), the setting
     `dmrsa-cost-calculation-method` was REMOVED from the menu, and
     `replstats-energy-base/-factor` were removed too (unused since the
     PER_TIER_MW table). When the user says descriptions "feel
   outdated" ("se sienten obsoletas"), the audit order is: (1) grep the actual
   tier gating / multiplier semantics in code; (2) rewrite EN + ES for EVERY
   changed key; (3) verify parity with a script that parses both locale files,
   diffs key sets per section (`[section]` blocks), and asserts old false text
   is gone (the "texto viejo" check). Remember the item/entity duplication
   pitfall: placeable replicators have BOTH `[item-description]` AND
   `[entity-description]` — patch both (use replace_all when the string is
   identical in both sections), and the same key can appear in multiple
   User preference: he chose the FULL refresh (correct + modernize lore
   + polish) when offered options — the old memory note "eligió opción A
   mínima" was from an earlier offer; when HE asks to refresh descriptions he
   wants them all fixed, not the minimum.
   **Lore tone (2026-08-11, D2b)**: after the one-liner pass, the user said
   "incluyo un nuevo lore me parece mejor" and picked the ATMOSPHERIC option —
   misterio/descubrimiento tone, 2-3 sentences per piece, lore that matches
   the mod's CURRENT scope (Space Age, planetary replicators, dynamic
   generation), NOT the original fork's near-vanilla narrative (long
   paragraphs about "dark matter passing through matter" felt outdated and
   clashed with the mod's status). Do not offer "minimal one-liners" as the
   final state — he prefers atmospheric lore written for the current mod.
   **Pitfall — lore rewrites drop factual stats**: the rewrite of
   dmrsa-replicator-gleba lost its "3x speed" (crafting_speed is 3.0 in
   planetary-replicators.lua) while keeping "100% freshness" — inconsistent
   with the other planetary descriptions and wrong vs the code. Verify AFTER
   a lore/description pass that gameplay-relevant numbers (crafting_speed
   multipliers, freshness %, tier gating facts) survive in BOTH locales —
   extend the parity audit to assert "3x"/"5x" presence per planetary
   replicator, not just key parity + old-text-gone. Reusable checker:
   `scripts/audit_locale_parity.py <locale_dir> --forbid "old text" ...
   --require "KEY:3x"` (also does the per-section key-parity diff; exit 0 =
   clean).
 - **Dump-driven audit with `--dump-data`** (2026-08-11, v3.7.0): when a
   balance bug involves mod interactions (prereqs, tiers, steps), don't guess —
   have the user run `factorio.exe --dump-data` on their PC (writes
   `script-output/data-raw-dump.json`, a single JSON with ALL prototypes, in
   the write dir; on Windows `%APPDATA%\Factorio\script-output\`). Then load it
   in Python and REPLICATE the mod's logic (recipe_map, tech_map, category
   classification) against the REAL data. This found 118 items with missing
   original-tech prereqs that static code review could never see.
   Pitfalls: (a) the dump reflects the INSTALLED mod version — if the user
   hasn't installed your latest local changes, the dump shows the OLD behavior;
   (b) Python regex is NOT Lua — `%-` is Lua's literal-hyphen escape, in
   Python it's just `-`; (c) replicate build_recipe_map's recycling/barreling
   exclusion or you'll resolve to recycling recipes; (d) the settings dump
   (mod-settings-dump.json) shows the player's actual config.
 - **Load-order prereq race (v3.7.0 A4/A5)**: the dynamic generator runs in
   data-updates, but overhaul mods define their unlock-recipe tech effects in
   THEIR data-updates/data-final-fixes — so recipe_tech_map is incomplete at
   generation time and original-tech prereqs get silently skipped (118 items
   with Bob's). Two-part fix: (1) declare optional dependencies in info.json
   (`? bobplates`, `? bobwarfare`, ...) so DMR's data-final-fixes runs AFTER
   theirs; (2) add a data-final-fixes PASS that rebuilds recipe_tech_map from
   FINAL data and re-attaches missing prereqs. CRITICAL pitfall: in the re-
   attach pass resolve the source recipe by EXACT name (`data.raw.recipe[item]`),
   NEVER via a rebuilt CostSolver.recipe_map — by then the dmrsa-repl-* recipes
   (0 ingredients) exist and build_recipe_map prefers fewest-ingredient recipes,
   so it resolves to YOUR OWN replication recipe → self-prereq cycle.

- **Science-pack substring detection too broad** (v3.7.0, found via dump log):
  the science-tier override in dynamic-generator matched
  `string.find(name, "logistic")` which ALSO matches
  `bob-advanced-logistic-science-pack` → forced the Bob's advanced pack to
  tier 1 (log: "Science tier force bob-advanced-logistic-science-pack:
  cost-solver=3 -> 1"). When matching science packs by name, anchor patterns
  (`logistic%-science%-pack$`) or check more specific patterns
  (`advanced%-logistic`) FIRST. Same class as the exact-match vs variant
  pitfalls — the substring direction matters both ways (too narrow AND too
  broad).
