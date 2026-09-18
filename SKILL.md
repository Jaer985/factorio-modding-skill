---
name: factorio-modding
description: "Trigger: Factorio modding, Lua, prototype, control.lua, data.lua, recipe, technology, desync, migration. Full-stack Factorio 2.0/2.1/Space Age modding — prototype definition, runtime scripting, version migration, changelog research, dump-driven audits, and compatibility-first development."
license: MIT
metadata:
  author: Jaer985
  version: "3.0"
---
## See also

- `references/prototype-registry-audit.md` — **prototype registries** (science
  packs are `tool`; ammo/module/capsule/equipment have OWN registries —
  `data.raw.item` guards silently skip 142+ targets), structural signals
  (`place_as_equipment_result`, `surface_conditions`) beating name patterns,
  empty-prefix cross-mod inheritance (`sulfur`↔`biosulfur`), self-mirror
  collapse, max-SCL-wins anti-pattern, dynamic-routing invariants (verify
  every hardcoded name in the dump BEFORE patching), locale/code drift,
  inference-cap for unknown pack levels — validated on the DMR batch-3
  audit (138-mod dump). Load when adding data-stage guards, dynamic routing,
  or auditing against a real-modlist dump.
- `references/audit-and-release.md` — DMR v3.5.2→v3.6.0 cycle: audit pitfalls
  (false-positive duplicates), data-final-fixes PASS 3 patterns, locale
  section mapping, zip release convention, **version-numbering policy**
  (minor bump when many unpublished patches accumulate; keep factorio_version
  at lowest supported; ONE accumulated changelog entry since the last
  PUBLISHED portal version — check the portal API, not local changelog),
  settings order collisions, **LocalisedString `"?"` parameter pitfall**
  (2.x treats `"?"` as a KEY, not positional — legacy fork syntax renders
  dynamic recipes/techs as "Replication: parameter-0/1/..."),
  **LocalisedString numeric-parameter pitfall** (prototype localised strings
  REJECT numbers at load — always tostring(); v4.2.0 gate test), subgroup
  categorization + locale-defined subgroup/category names, **item vs entity
  description duplication** (no automatic fallback between
  `[item-description]` and `[entity-description]`), **recipe-category
  coverage gap** (MACHINE_EFFICIENCY vs SA category-name drift: real SA
  names are `cryogenics/electromagnetics/metallurgy/organic/
  captive-spawner-process`, NOT `cryogenic/electromagnetic/metallurgic` —
  wrong names silently fall to the 1.0 fallback;
  see `references/dmr-machine-efficiency-sa-category-drift.md`),
  **exact-match vs substring variant names** (`*-cold/*-hot/*-molten` —
  `name == "X"` silently fails; use string.find), dead-code fields,
  **`BASE_RESOURCE_COSTS` coverage gap** (every minable resource in the
  table or cost-solver falls back to tier 1), **fluid-without-recipe tier
  gap** (FLUID_TIER_OVERRIDES for passive outputs like `fusion-plasma`).
  Load when: audit, release, locale scan, orphan tech bug, "parameter-N"
  literal in-game, wrong crafting tab/tier, startup crash naming a tech
  "removed by <mod>", any "weird text/location in-game".

- `references/dmr-moon-eneas-compatibility.md` — load-order race when another
  mod deletes a tech your dynamic generation references (spidertron-unit).
  The v3.5.15 fix: declare `? <mod>` optional dependency to force
  data-final-fixes ordering. Generalizes to aai-loaders-sane and any mod with
  alternative progression. Load when you see "Error in assignID: technology
  with name 'X' does not exist. It was removed by <mod>."

- `references/dmr-github-publishing.md` — repo facts + auth for pushing DMR
  to GitHub: public repo `Jaer985/dark-matter-replicators-reborn_3`, root =
  the mod source dir, branch `main`, remote was stale (3.2.1) vs local 3.6.0.
  **Working token (verified 2026-08-12): the GitHub token stored in the
  profile env file is a real token for Jaer985 — use it for pushes
  (per-profile config values are placeholders)**. Includes the full
  release-gate publishing checklist (bump → docs → zip → receipt → git →
  portal) and the minor-bump accumulated-changelog rule. **Before any push
  run `scripts/check-no-private-data.py <tree>`** (flags tokens, private
  paths, secret filenames, cfg-outside-locale) on both the git tree and the
  zip — see the GitHub-push / private-data-scan sections in
  `references/audit-and-release.md`. Also covers the clone→sync→push pattern
  for the source dir that is NOT a git repo (no `.git`), and deleting the
  stale `roadmap.txt` in favor of `ROADMAP.md`.

- `references/dmr-test-suite.md` — **the cost-solver test suite is BUILT and
  PASSING (9/9)**. Location: `dmr-tests/` OUTSIDE the mod source dir (never
  packaged into the zip). Run: `cd dmr-tests && lua5.2 run_tests.lua`.
  **Factorio 2.x embeds Lua 5.2, NOT 5.1** — the cost-solver uses
  `goto`/`::label::` (5.2 syntax), so the harness must run on `lua5.2`
  (`sudo apt-get install -y lua5.2`). Key harness detail: Factorio
  auto-assigns `prototype.name = <table key>`; the harness `load_recipe/...`
  helpers replicate this, otherwise `recipe_tech_map[recipe.name]` silently
  no-ops and tech-tier mapping breaks in tests. Fixtures reproduce every tier
  bug from v3.5.8–v3.5.20 (fusion-plasma→5, promethium-chunk→5, carbonic→4,
  chemical-science-pack→3, cyclic pairs, mid-item→3 via tech mapping).
  Extend fixtures in `fixtures_recipes.lua` + asserts in `run_tests.lua`.

- `references/release-push-and-privacy.md` — pre-push privacy scan (user
  mandate: "verifica que no se suba nada privado"), GitHub token validation
  BEFORE push (401 vs 403-denied-to-other-account diagnostics), rsync-less
  repo sync pitfall, and remote-vs-local version check. Load before pushing a
  release to GitHub or uploading a zip to the mod portal.
  **Pitfall (2026-08-22)**: `check-no-private-data.py` flags the literal
  STRING of a credential env-var NAME anywhere in the source tree — even in
  docs that merely MENTION where the token lives (a ROADMAP line naming the
  env var and its home path tripped the scan). The real value was never in
  the tree; the NAME alone is enough to fail. Fix: never write a real
  env-var name (nor the vars' HOME path) into any file that ships in the
  mod folder or gets pushed — paraphrase ("el token de GitHub vive en el
  .env del perfil — ver skill").

- `references/dmr-dump-data-diagnostics.md` — getting a Factorio 2.x data dump
  from the user's Windows PC (`factorio.exe --dump-data` → ONE file
  `script-output/data-raw-dump.json`, ~90MB, SCP not Telegram), reading the
  load log as a bug detector, and replicating the cost-solver's
  build_recipe_map/build_tech_map in Python to find every tech missing its
  original-tech prereq in one batch pass. Load when the user reports
  "item X at tier N without prerequisite" or tier weirdness with a real
  modlist. Root cause it exposed: DMR builds recipe_tech_map in data-updates
  BEFORE Bob's defines its unlock-recipe effects → 118/868 prereqs silently
  missing (fix direction A4/A5: data-final-fixes re-add pass + optional
  deps).

- `references/dmr-dump-driven-audit.md` — the full end-to-end workflow for
  dump-driven audits (v3.7.0): user-side dump commands + SCP transfer,
  Python slicing of data-raw-dump.json, exact replication of
  build_recipe_map/build_tech_map/solve_cost (with recycling/barreling
  exclusion and the exact-name resolution pitfall), the missing-prereq
  cross-check, tier-underestimation diagnosis (generation ran early vs
  genuinely cheap), locale EN/ES parity audit script, and the Python zip
  build + in-zip receipt (host has no `zip` binary). Load BEFORE any
  Load BEFORE any balance/prereq/tier audit against a real modlist.

  - `references/dump-audit-subagents.md` — **load when the user asks to audit a
    big data dump "por partes" with subagents** ("hace una investigacion a fondo
    del dump por partes, pon multiples subagentes... tu solo seras el
    orquestador"): the validated orchestration playbook — CONTEXT.md first
    (state + already-fixed so children don't rediscover), split by DOMAIN
    (ores/baseline/techs/planets/costs/...), batches of ≤3, append batch
    findings to CONTEXT between rounds ("NO duplicar"), each child writes a
    full report + returns only the executive summary, VERIFY report files after
    (child claims are self-reports). Includes the v4.2 report schemas and
    reusable insights (dump = installed version; sim-vs-game contradiction =
    suspect .match/`%-` translation; overhaul mods redirect vanilla unlocks →
    items with NO tech go baseline).

- `references/dmr-tier-gating-redesign.md` — **load when the user asks to
  redesign/improve the tier-category progression** ("las categorías no están
  funcionando / al final puedo desbloquear cualquier cosa"). Dump-verified
  diagnosis (3.7.0 + 3.7.1 dumps): category tier is a FLOOR only; `general`
  (46% of ~945 recipes) has no floor → cost-solver dominates; mid-game vanilla
  items (electronic-circuit, fast-inserter, engine-unit) sink to tier 1;
  grouped-tech prev-tier chain is inconsistent. The mismatch-audit technique
  (cross-check every dmrsa-repl-* tier vs the item's ORIGINAL unlock tech's
  highest science pack) found 503/945 mismatches — 25 endgame items
  (logistic chests, mech-armor, artillery, tesla) DOWNGRADED to tier 3-4, the
  literal "desbloquear cualquier cosa" symptom. CRITICAL: baseline machine
  techs (dmrsa-replication-N) skip PASS 6 re-attach → baseline items lose the
  original-tech gate; any redesign must fix that. **FINAL DECISION 2026-08-13
  (user-corrected — read the DECISION section, do NOT re-interpret)**:
  Research Mirror with **threshold=1** (every ORIGINAL tech gets its own
  "Replication: <tech>" tech, even single-item techs — the user's "individual"
  meant mirror threshold=1, NOT the per-item Individual Technologies mode);
  tier = original tech's science level; exclusions guns/armor/combat-capsules/
  vehicles = 58 (AMMO KEPT — mass-use vs aliens); grouped-by-category techs
  removed, categories become visual subgroups only; sample-based replication
  deferred as `dmrsa-replication-mode` setting; hybrid max(orig, category) =
  plan B. Candidate NEXT major version (4.x) — 3.7.1 kept intact with revert
  backup at `backups/dark-matter-replicators-reborn_3.7.1-source-backup.tar.gz`
  ("punto y aparte" = backup, NOT a git fork — user correction). NOT
  implemented yet.
  Use `scripts/dmr_tier_distribution.py <dump> --sample N` to see the
  real distribution before redesigning.

- `references/dmr-research-mirror-4x-design.md` — FINAL refined 4.x design
  (2026-08-12/13, supersedes the exclusion numbers in dmr-tier-gating-redesign):
  research mirror threshold=1 (every original tech → "Replication: <tech>"),
  tier = original tech's science level (NOT cost-solver), grouped-by-category
  techs removed → categories become visual subgroups only, and the NEW
  **materials techs** chain (`dmr-replication-materials-1..5`, one per tier,
  prereq of ALL mirror techs in that tier — user: "para poder replicar
  necesitas conocer los materiales"). Exclusion set FINAL = 144 items: guns,
  armor, combat capsules, vehicles, vehicle equipment, personal equipment
  EXCEPT solar panels + batteries; **AMMO / fuel cells / seeds / raw-fish KEPT**
  (mass-use principle: "objetos de uso masivo deben poderse replicar").
  Result: 801 replicable → 417 mirror techs + 5 materials + 4 planetary ≈ 426.
  Quality NOT replicated (ROADMAP, future brainstorming). Backup for revert:
  `backups/dark-matter-replicators-reborn_3.7.1-source-backup.tar.gz`
  ("punto y aparte" = backup, NOT a git fork — user correction).
  **IMPLEMENTED 2026-08-12 as v4.0.0** (zip built, tests green). **Gate test
  PASSED 2026-08-13 on Factorio 2.1.14** — 4 load errors found and fixed
  (assembler2pipepictures 2.1 API, tree-depth clamp, Angel's optional deps,
  leveled-tech chain normalization). See the ESTADO ACTUAL section of
  `references/dmr-v4-mirror-tree.md` for the full sequence; **tenemut is now
  replicable ONLY at tier 5** ("Dominio de la Materia Oscura", user decision
  2026-08-13). For the implementation details (files touched,
  MirrorGenerator structure, test_mirror.lua, workflow preferences) see
  `references/dmr-v4-mirror-tree.md` — that is the implementation source of
  truth; this file is the design history.

- `references/factorio-2.1-breaking-changes.md` — **load when working on any
  Factorio 2.1 code path or hitting a load error on 2.1**: recipe
  `category`→`categories` migration, removed recipe categories, science packs
  as plain items, quality scaling, `assembler2pipepictures` now a DATA TABLE
  in `__base__/prototypes/entity/assembler-pictures.lua` (NOT a global
  function — reference without parentheses, and from another mod the require
  MUST be `__base__/`-prefixed), the safe_require phantom-assignID diagnosis
  path, and the **Non-contiguous technology levels** class: (a) direct prereq
  deeper than the tech's tier → clamp to tree depth (memoized cycle-safe);
  (b) leveled-tech chains (`name-N` = Factorio levels of ONE base tech) →
  generate ONE tech per chain, not one per level, or a skipped middle level
  breaks contiguity with "Non-contiguous levels: N, followed by M".
  Also documents what does NOT change in 2.1 (category registry,
  crafting_categories, tech category, resource category) to avoid false
  positives during audits, plus the **placeholder-graphics fragility rule**
  (v4.1.0): don't reproduce a vanilla entity sprite (assembler-1) with
  hardcoded rects — Bob's/overhaul mods replace and resize those sheets, so
  the rect errors and the `__base__/...png` path can vanish
  ("File ... not found"). For placeholder machine art use the mod's OWN proven
  sprite (replicator-5) with a `tint`, or ship a copy of the PNG in your
  graphics/ dir; never depend on a vanilla sheet an overhaul mod owns.
  **2.1.15 (2026-08-24) additions also covered here**: the **circuit connector
  layer migration** (REMOVED `LoaderPrototype::circuit_connector_layer`,
  `RailSignalPictureSet::circuit_connector_render_layer`,
  `CraftingMachineGraphicsSet::circuit_connector_layer` +
  `circuit_connector_secondary_draw_order`,
  `MiningDrillGraphicsSet::circuit_connector_layer` +
  `circuit_connector_secondary_draw_order` — migrate to
  `CircuitConnectorSprites::render_layer` + `secondary_draw_order`; four
  default render layers changed silently); **`LuaGroup` → `LuaItemGroup` +
  `LuaItemSubGroup` rename** (REPLACED, no alias — `prototypes.group` is gone,
  use `prototypes.item_group` / `prototypes.item_sub_group`);
  **`LuaSimulation::get_widget_position` reworked** (data/data2 strings removed,
  now 1-based indexing); `LuaControl::opened` supports map-editor tile +
  permissions/server-config/player-mgmt/alerts GUI; `EntityPrototype::ghost_build_sound`;
  `RocketSiloPrototype::rocket_parts_storage_cap` accepts 0; SA "Transport
  belt capacity 2" now requires "Inserter capacity bonus 7" (may shift DMR
  mirror-tier assignments for belt/inserter items — re-verify with dump).

- `references/dmr-v4-mirror-tree.md` — **v4.0 IMPLEMENTATION (2026-08-12)**:
  the mirror-tree architecture as built: `lib/mirror-generator.lua` (recipes +
  reverse map tech→items + mirror techs + baseline→materials attach),
  `is_v4_excluded()` in target-mapper (144-item exclusion set), data-final-fixes
  PASS 0 choosing Mirror vs Individual (legacy), PASS 6 re-attach REMOVED
  (unnecessary — reverse map built from final data, prereq IS the original
  tech), 5 `replication-materials-N` techs, `dmrsa-require-original-tech`
  setting (default ON), Factorio 2.1-only (categories array, dmrsa_is_v21
  removed), dmr-tests/test_mirror.lua (30 checks: get_tech_science_level +
  v4.0 exclusions). Numbers: 945 items → 144 excluded → 801 → 417 mirror techs.
  Includes the 2026-08-13 gate-test sequence (4 load errors fixed) and the
  tenemut-tier-5 balance decision ("Dominio de la Materia Oscura"). Renaming
  state 2026-08-14: full material-renaming proposal (Resonance Latch / Atomic
  Loom / Genesis Loom) DISCARDED by user; only `matter-conduit` → "Nanophase
  Conduit" applied (locale EN/ES). AI icon generation DISCARDED entirely
  (user: "elimina lo de gemini/canva") — do not propose it again unless asked.
  **User workflow preferences (2026-08-12)**: design-first (options A/B/C/D →
  pick → verify with dump data BEFORE implementing); when the user references
  a brainstorm option, RE-READ all messages from that point — shorthand can
  mean something non-obvious ("individual" = mirror threshold=1, NOT per-item
  techs; misreading cost several round-trips); major redesigns keep the
  published version intact + create a tar.gz backup first ("punto y aparte" =
  backup, not a git fork). Load BEFORE any v4.x tier/tech work.
  **Also covers v4.1 (Quality Refiner, see dmr-quality-refiner-v4.1.md) and
  **Also covers v4.2 (2026-08-22)**: the baseline-inflation fix — items that are OUTPUTS of
    overhaul-mod processing recipes (angels-gas-*, mineral-sludge...) inherit the
    tech of their SAME-MOD producing recipe; the universal material-tier override
    (MOD_ORE_TIERS applied to EVERY solve_cost result, longest-match); materials
    techs get explicit localised_name template + hardened pack fallback.
    Dump-verified: materials-1 108 → 25 items. Pitfalls inside: `.match()` vs
    `.search()` in Python sims, and overhaul mods redirect vanilla unlocks
    (plastics → bob-plastic-pipe, plastic-bar has NO tech).
    **Also covers v4.2 gate test (2026-08-23)**: THREE load/balance bugs found on
    first real load — (1) prototype localised strings REJECT numeric parameters at
    load (`tostring()` the tier; numbers are runtime-only), (2) tenemut tool lived in
    raw-resources.lua which loads AFTER technologies.lua → item_exists false → silent
    fallback substitution (load-order-sensitive item_exists; items belong in the
    items file loaded first), (3) tree-depth clamp inflated 458/474 mirrors to tier 5
    (REMOVED; contiguity is handled by leveled-chain normalization) + science packs
    now FORCED to progression tier by exact table. **ADAPTABILITY decision (user):
    unknown mod science packs are anchored DYNAMICALLY** via
    `ensure_inferred_pack_levels()` (level = max table-known level among visible
    consumer techs, kitchen-sinks >8 ingredients excluded) — declare BEFORE pack_level
    or upvalues resolve nil. Simulation-fidelity pitfall: Python tier sims MUST
    replicate `mirror_deepest` (-N chain resolution) before computing SCL — an
    unfaithful sim reported 253 t1 mirrors vs the real 90 and tripped a user audit.
    Also documents the repo-root AGENTS.md handoff contract for external agents
    (opencode reads it automatically; keep it current after major state changes).

- `references/dmr-v42-audit-findings.md` — **load ANY time v4.2/v4.3 balance
  work resumes** ("materiales-1", "rebalance", "techs por tier", "fórmula de
  costos"): the consolidated 138-mod dump audit (research/v42-audit/ on disk).
  **ALL B decisions CLOSED AND IMPLEMENTED 2026-08-22** (do NOT re-ask): B1 =
  split saturated `-N` chains only (opción C, IMPLEMENTED); B2 = cost scale
  IMPLEMENTED (fórmula `clamp(min(vanilla,solver)×CT(3-7)×machine×por-tier
  (1.5-3.5), bandas FIJAS 2.7-16/5.3-32/10.6-64/20-120/33.3-200)`, clamp sobre
  el LOTE de fluidos, speed_factor 1.6 (speeds 1/1.6/2.56/4.1/6.55), kW
  1/3/8/15/30 MW, planetarios 40/80, refiner ×3 + 4MW, cross-tier recursivo
  ya en el código — ver `references/dmr-v42-cost-model-b2.md` para el diseño
  final completo);
  B3 = 6 Bob gems replicable tier 5 (implemented; the 10 "Angel's minerals"
  DON'T EXIST — child hallucination); B4 = science packs refinable ALLOWED;
  B5 = combat capsules/
  mines/robots REPLICABLE in vanilla tier (REVERSED the v4.0 exclusion — the
  A-fix blacklist of combat robots was undone the same day). Ships fixes:
  `%-equipment%-%d+$` versioned-equipment exclusion, TECH_REDIRECT/
  BASELINE_FORCE pattern for warp-processed unlocks, BOB_GEM_ORES whitelist.
  Pitfalls inside: Lua array-vs-SET lookup, subagent-hallucinated item names
  must be dump-verified, broad planet-routing substrings.

- `references/dmr-original-mod-study.md` — FULL study of the upstream original
  (`dark-matter-replicators-space-age_2.0.4` zip in `archivados/`): declarative
  per-mod replication tables (repltech_*/replvar), the recipe-chain + machine
  variable cost model (vars = kW/speed/270), ore rarity costs (mining_time/
  base_density×8, gem-ore var 200), category tiers (ore1 element2 shape2 alloy3
  chemical3 device2-5 life5 module5 science manual), research unit (tier×25,
  t1/t5 double, no item_count), energy ramp 2.5x vs speed 2x (high tiers LESS
  efficient — the portal's "lower tiers most energy efficient"), SA EVERYTHING
  device5 (mech-armor/fusion-reactor-equipment INCLUDED), science packs t3-5
  (planetarios 5), exclusions (bob 44, angel 14 — replvar-no-cost pattern),
  replicators themselves replicable (upgrade=true). Load when the user asks
  "cómo lo hace el mod original" / fidelity vs upstream. Full writeup:
  `research/dmr-original-mod-study.md`.
- `references/dmr-icon-assets-generation.md` — **load when the user asks to
  generate/redesign DMR icon assets via AI. FINAL DECISION 2026-08-14: AI
  image generation DISCARDED by user** (Gemini cartoon ×2, Canva Pro 3D
  renders; user: "elimina lo de gemini/canva y la generacion de los iconos").
  Do NOT propose AI assets again unless explicitly asked. The file keeps the
  verified provider facts (opencode-go has NO image generation — 25 chat-only
  models, no /images endpoint; Google AI image models need billing, free tier
  is quota 0 → 429; OpenRouter image models blocked until data-policy relaxed
  at openrouter.ai/settings/privacy → 404) and the anti-cartoon/anti-3D
  prompt anchoring (sticker-style / geometric-polygons / no-glow vocabulary;
  reference image beats style text) for the unlikely day they retry.

- `references/dmr-yuoki-compatibility.md` — **load when adding Yuoki
  Industries compatibility** ("agregale compatibilidad de yuoki"). The
  upstream fork (`nihilistzsche/dark-matter-replicators-space-age`,
  `prototypes/replications/yuoki.lua`) is the ground truth: signs
  (y_greensign/y_rwtechsign/ypfw_trader_sign/ye_science_blue) are faction
  currency = NOT replicable; Yuoki has NO static techs (recipes enabled=true)
  → its items fall to the materials/baseline path in the mirror tree, not
  mirror techs. **ANTI-PATTERN (2026-08-14)**: do NOT add a blanket
  `place_result` exclusion — dump-verified it kills 208 mass-use base items
  (chests/belts/inserters/furnaces/solar/accumulators); the upstream
  replicated Yuoki machines anyway. Needed: `? Yuoki` load-order + signs
  blacklist only; machine exclusion (if any) must be entity-type-scoped.
  Full item inventory breakdown (112 machines vs 163 materials) inside.
  **STATUS 2026-08-14: PAUSED by user** until Yuoki is updated to 2.1 and in
  the modlist — blacklist (19 items: 10 inserters, 1 bunker, 8 basements) +
  `? Yuoki` + signs are IMPLEMENTED; the per-item machine review (procesado/
  refinado/mastercrafted/ultimate) is deferred, pending list lives in
  ROADMAP.md (entry "Compatibilidad Yuoki Industries"). See the PAUSE section.
  Also documents the portal-403→GitHub-source workaround for getting mod
  code when the portal download is Cloudflare-blocked.

- `references/dmr-quality-refiner-v4.1.md` — **load for any quality-related
  DMR work** (the Quality Refiner, `dmrsa-replicator-quality` setting, or "can
  we replicate quality items?" questions). Implementation source of truth:
  user-approved numbers (1%→0.5%→0.25%→0.1%, 5% loss, energy ×10 — ×3 since
  v4.2 B2 rebalance, never skip), the recipe mechanics (`results` with `probability` + fixed
  `quality`; `ingredients` with a `quality` field), the **quality expansion
  happens AFTER all mod data stages** (quality variants are invisible in
  data-final-fixes and in --dump-data — "quality as replication targets" is
  impossible), the quality gate `data.raw["quality"]["uncommon"]`, the
  graphics-from-dump pattern (assembler-1 2.x is 214×226/32f/line 8/scale
  0.58, NOT the 1.1-era 132×132; modded dumps contaminate entities — pick
  the unmodified vanilla one), a module-less machine as the balance lever,
  and the **locale CFG editing pitfall** (regex-split corruption hit twice →
  line-by-line section tracking, CRLF normalize, verify header count, restore
  from GitHub raw if corrupted). Also documents the **mirror-vs-baseline
  dump audit** (for \"materials-N desbloquea demasiado\" reports: category tier
  regex with PLAIN hyphens, planetary categories are not baseline, tech→item
  by recipe-name==item-name convention, enabled=true items are legit baseline
  vs load-order misses → add `? <mod>` deps) and the silent Python `%-` regex
  trap (matches the literal, everything collapses to tier 1 / exclusions to
  nothing — looks plausible, wrong).

# Factorio Modding

## Stack
- **Language**: Lua 5.2 (Factorio's embedded Lua)
- **API Docs**: https://lua-api.factorio.com/latest/
- **Changelog**: https://raw.githubusercontent.com/wube/factorio-data/master/changelog.txt
- **Wiki**: https://wiki.factorio.com/Version_history
- **Mod Portal**: https://mods.factorio.com

## Project layout
```
<mod-name>/
├── info.json              # Metadata: name, version, factorio_version, dependencies
├── data.lua               # Prototype definitions (items, recipes, entities, tech)
├── data-updates.lua       # Modifies existing prototypes from base/other mods
├── data-final-fixes.lua   # Last-stage prototype changes (cloning, patching)
├── control.lua            # Runtime logic (events, on_tick, combat, GUI)
├── settings.lua           # User-facing configuration
├── prototypes/            # Modular prototype files (split for maintainability)
│   ├── items/
│   ├── entities/
│   ├── recipes/
│   ├── technologies/
│   └── raw-resources/
├── lib/                   # Pure-Lua helpers (cost-solver, target-mapper, etc.)
├── locale/
│   ├── en/
│   └── es-ES/             # Spanish (Spain) + other languages as needed
└── graphics/              # Sprites, icons, sounds
```

## Mandatory audit-then-bulk-fix workflow

When the user reports a bug OR you discover one through static analysis, follow
this sequence (NEVER patch-rebuild-discover-patch-rebuild):

1. **STOP** — do not patch immediately.
2. **Enumerate ALL violations of the same class** across the entire codebase.
3. **Build a checklist** organized by bug class.
4. **Patch ALL of them in one batch**, even across multiple files.
5. **Rebuild ONCE** and verify all fixes landed.

See `references/audit-and-release.md` for the full playbook, including the
"enumerate → fix all → verify once" pattern that this session repeatedly
violated (v3.5.4 missed the 4th call site, v3.5.5 missed 9 locale entries, v3.5.8
missed the fluoroketone variants).

**Implemented in v3.5.14 (RDD flow)**: `references/dmr-tier-rebalance-plan.md`
— lowered module/military tier floors (module 5→3, military 4→3), added
`module-advanced` (4) and `military-advanced` (5) categories, split
`get_item_category` classification. Landed as v3.5.14 with receipt 15/15 PASS.
If you revisit tier logic, load this reference first so you don't re-audit
from scratch.

## Batch QA-audit playbook (swarm over a real-modlist dump)

Code fixes on this mod are only REAL once validated against the user's live
modlist dump (~122MB JSON from `--dump-data`, 138 mods). Static review alone
missed load-order crashes, tier inflation and cost-scale inversions in past
releases. Established pattern (batches 1-2, extended batch 3 in flight for
4.2.1 → results land in `research/v42-audit/<subsystem>.md`):

1. **CONTEXT.md first** in `research/<ver>-audit/`: (a) everything ALREADY
   fixed (agents must not re-report it), (b) dump conventions (dmrsa-repl-*
   categories = tier, spoil/planet routing rules, Python `.search()` not
   `.match()`), (c) mandatory output format: full report → file, executive
   summary only → message.
2. **Batch = parallel subagents, one subsystem each** (batch 3 = 6:
   mirror-generator, cost-solver, target-mapper, refiner+data-final-fixes
   passes, planetary routing, release integrity). Shard the dump first for
   RAM safety (see `multi-agent-orchestration` skill) — agents must never
   load the full dump in parallel.
3. **Findings are HYPOTHESES**, format `item | actual | expected | source
   (mirror/baseline/tech) | severity | confidence`. The user verifies
   finding-by-finding and OKs each before any fix — never batch-apply audit
   findings unconfirmed.
4. **Known-issues register**: AGENTS.md §11 is the source of truth; every
   new batch reads it + CONTEXT.md before hunting (avoids duplicate work).
5. **After user confirmation**: apply as an F-batch (F1-F4 style), add
   regression tests to `dmr-tests/` (test_mirror §2 pattern), then full
   suite + zip rebuild + content verification before considering it done.

## Runtime localization warnings as bug detectors

Factorio logs "Unknown key: type.parameter-N (Researched)" warnings at
runtime for every LocalisedString that fails to resolve. These warnings are
**high-signal bug indicators that static code review cannot detect** because:

- The LocalisedString syntax can be syntactically valid but semantically wrong
  (correct placeholder count but wrong namespace prefix).
- The locale key may exist in vanilla but Factorio 2.x resolves them through
  specific priority rules that static analysis can't simulate.
- Template changes may leave callers passing the wrong number of parameters
  (e.g. v3.5.10: planetary grouped tech passing 3 params to a 2-placeholder
  template).

**Workflow when the user reports "X appears as literal text Y" or pastes
Factorio log warnings:**

1. Treat every "Unknown key" warning as a real bug, not a cosmetic noise.
   Even one warning per research event adds up across the tech tree.
2. Ask the user for the **specific tech name** (hover the tech) and the
   **full log entry** (set `dmrsa-log-level = "debug"` for richest output).
3. Cross-reference against all `localised_name`/`localised_description` calls
   in the codebase and the locale file's template string.
4. Verify the parameter count matches the template's placeholder count.

This is complementary to static analysis: a mod can pass static review
(every call site looks correct in isolation) and still produce dozens of
runtime warnings when the actual templates and parameter counts don't align.

## Common pitfalls (load `references/audit-and-release.md` for full details)

- **Bulk prototype analysis from zips: regex/brace parsing traps** (2026-08-11,
  Bob's core-mod step-item audit): when scanning mod zips with Python
  (`zipfile` + regex — no `unzip` needed), five traps bit hard:
  (1) **`type = "item"` matches inside recipe ingredients** —
  `{type = "item", name = "X", amount = N}` entries regex-match as item
  prototypes; filter candidate blocks by top-level keys (real items have
  `name` + `type` but NOT `amount`).
  (2) **Prototype blocks include their outer braces** — top-level keys sit at
  depth 1 inside the block text; skip the outer `{`/`}` when scanning for
  top-level keys.
  (3) **Ingredients/results tables**: strip the table's outer braces before
  iterating entries, or the WHOLE table parses as a single ingredient
  (silently losing all but the first name).
  (4) **Sanitize strings/comments before brace counting** (blank string
  literals and `--` comments, keeping length) so braces inside strings
  can't corrupt block boundaries; slice the ORIGINAL text by the sanitized
  indices for content.
  (5) **Bob's rewrites recipes at runtime** — static `ingredients = {...}`
  parsing misses most consumption edges; also scan for
  `bobmods.lib.recipe.add_ingredient / set_ingredient / set_ingredients /
  replace_ingredient` calls (`set_ingredients` takes a whole table, others
  one entry), and DON'T filter dynamic edges by "recipe exists in scanned
  zips" — tier-1 Bob's parts are consumed by BASE-GAME recipes
  (`construction-robot`, `logistic-robot`) that aren't in the modlist.
  CRLF line endings (`\r\n`) are the norm in Factorio zips — `\s` regex
  classes handle them, but don't assume `\n`-only text. Working parser:
  `scripts/parse_mod_prototypes.py` (arg = zip paths; outputs items_step /
  subgroups / produce-consume JSON). Findings for the Bob's core 4 mods:
  `references/bobs-mod-step-items.md`.
  **Parallelize with sub-agents when scanning many mods** (user-suggested,
  2026-08-11, Bob's 14-zip audit): split the modlist across 3 `delegate_task`
  leaf agents (e.g. core 4 / ores-mining-logistics / tech-modules-equipment),
  each with the SAME parsing script and a JSON output contract
  (`{items_step: [...], subgroups_interesantes: {...}}`). The agents iterate
  on parser bugs independently, and the consolidated result returns as one
  message. Pitfalls: (a) agents may hit iteration/summarization limits — have
  them WRITE the JSON to a shared file (`/tmp/bob_steps_output.json`) as the
  deliverable, not just the final message, so partial work survives; (b) the
  consumer-graph heuristic (consumed-by-≤N = step) OVER-excludes massively —
  the upstream fork's manual `replvar` exclusions are the ground truth, not
  the graph; (c) agents editing a shared `/tmp/*.py` overwrite each other —
  give each agent its OWN script filename.

- **LocalisedString `"?"` parameter pitfall**: `"?"` is a KEY for fallback
  selection, NOT a positional parameter. Legacy 0.x syntax
  `{ "?", {item-name.X}, ... }` renders as "parameter-0" in 2.x.
- **Item subgroup categorization**: items MUST use mod-defined subgroups, not
  vanilla (e.g. `"production-machine"`). Vanilla subgroups leak the item into
  the wrong inventory tab.
- **Item vs entity description duplication**: prototypes with both `type="item"`
  and an entity form MUST have description in BOTH `[item-description]` AND
  `[entity-description]`. No automatic fallback.
- **Locale-defined subgroup/category names**: any new `type="item-subgroup"` /
  `type="recipe-category"` requires a locale entry or Factorio displays the
  raw key.
- **Exact-match name bug**: `name == "X"` silently breaks when X has variants
  (`X-cold`, `X-hot`, `X-molten`). Use `string.find(name, "X")` for SA fluids
  and similar.
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
- **Category-name → tier-floor → required-tech chain** (v3.5.9): items with
  substrings like "plate" or "brick" land in `alloy`/`shape` categories with
  tier floors ≥ 2, requiring chemical to research even though the items feel
  early-game to vanilla players. This is by-design but surprises users. See
  audit-and-release.md for the full chain and the proactive detection rule.
- **Template-parameter count mismatch** (v3.5.10): code must pass exactly
  N parameters to a LocalisedString template that defines N `__N__`
  placeholders. Extra positional args are reported by Factorio at runtime as
  "Unknown key: type.parameter-N" — once per extra arg per render. Common
  symptom in logs: `Replication: Unknown key: "item-name.X" (Researched)`.
  Common offenders: changing a template from `__1__` to `__1__ __2__` without
  updating the caller, or leaving a stale literal as a "fallback" that the
  template doesn't have a placeholder for. Fix: match parameter count to
  placeholder count exactly.
- **Cost-solver fallback tier pollution** (v3.5.11): `solve_cost` has two
  hardcoded fallbacks — cycle detection (`tier = 1`) and unknown recipe
  (`tier = 2`). With overhaul mods (Bob's, Angel's, K2), many intermediate
  items hit these fallbacks (cyclic recipes, no direct recipe) and get pinned
  at tier 1/2, flooding low-tier grouped techs with items that should be
  mid/late-game. The mod portal report "Replication: Components (Tier 1)
  contains too much stuff?" (Bob's) exposed this. Fix: make both fallbacks
  use `recipe_tech_map[name]` → `get_tier_from_tech()` when the unlock tech
  exists, and relax the `ingredient_tier + 1` cap when ingredients resolved
  to tier 1 (ambiguous: could be a genuinely simple item OR a degraded cycle
 fallback — skipping the cap lets true tier surface). See audit-and-release.md.
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
  Keep the tier subgroups defined (backward compat) and planetary items on
  `replication-resources`. Requires locale entries in `[item-subgroup-name]`
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
 - **Idle animation without new assets** (v3.5.25 + v3.6.0 FIX): to make an
  assembling-machine visually "turn off" when idle, add `idle_animation` to
  `graphics_set` reusing the SAME sprite sheet plus a dark `tint = {r=0.55,g=0.55,b=0.55,a=0.9}`.
  Factorio shows the dimmed static frame only while the machine has no
  recipe/input and the animated sprite while working — zero new art. Check
  the sprite first (PIL: frame0 vs frame1 mean-abs-diff) to confirm there's
  no distinct "off" frame already; if the sheet animates subtly, tint is the
  right lever.
  **CRITICAL (v3.6.0 load error)**: when `idle_animation` reuses the same
  sprite sheet as `animation`, Factorio 2.x REQUIRES `frame_count` (and
  `line_length`) to MATCH the `animation` values exactly. Setting
  `frame_count = 1, line_length = 1` (to render only frame 0) is REJECTED at
  load: "Error while loading entity prototype ...: Idle animation must have
  the same frame count as animation." The load-clean fix: use the SAME
  frame_count/line_length as `animation` (e.g. 33/11).
  **CRITICAL (v3.6.1 load error)**: do NOT set `animation_speed = 0` on the
  idle to keep it static — Factorio also rejects that: "Animation speed has
  to be greater than 0." Use a tiny positive value (`animation_speed = 0.01`,
  ~55s per 33-frame cycle) which is visually a static dimmed frame but
  satisfies the constraint. If you need a visually different idle, use a
  SEPARATE sprite sheet for idle_animation (then frame_count may differ).
  Lesson: Factorio validates prototype constraints at load that static
  analysis never sees — the user's in-game gate test catches these; run it
  before publishing ANY graphics_set change.
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
- **Check mod portal discussions when the user reports weirdness**: user
  reports of "weird item/tier/name" are often echoed by real player reports on
  `mods.factorio.com/mod/<name>/discussion`. Fetch the discussion thread
  (curl works; browser may not) — it frequently names the exact mod combo
  (e.g. "with Bob's") and symptom that static review can't see. sp518's
  "Components (Tier 1) contains too much stuff" thread drove the v3.5.11 fix.
- **Don't dismiss "X looks weird"** (general principle): user perception of
  weirdness in Factorio is a high-signal bug detector. Audit before
  responding "expected" — multiple times this session the first-pass answer
  was wrong and a deeper read revealed a real bug.
- **Factorio data dump workflow** (2026-08-11, DMR v3.7.0 gate test): when the
  user reports in-game tier/prereq weirdness with a big modlist, ask them to
  run `factorio.exe --dump-data` on their Windows PC (from `bin\x64`, game
  closed). Factorio 2.x writes ONE FILE `script-output/data-raw-dump.json` in
  the write dir — NOT a folder with per-type JSONs (the earlier assumption of
  technology.json/recipe.json/etc. was WRONG; Windows Explorer hides the .json
  extension so it appears as a bare `data-raw-dump` item). The file is ~90MB
  with Bob's — cannot go through Telegram (20MB cap); transfer via SCP to
  the project's `dumps/` directory or 7-Zip first.
  The write-dir log (`factorio-current.log`) is itself highly diagnostic: DMR's
  `helpers.info` lines show the real dynamic mapping per item ("Dynamically
  mapped base resource: bob-tin-ore (Tier 1...)", "Tier override
  bob-sniper-rifle: computed=1 -> category=3 (military)", "Science tier force
  ..."). User's PC paths: write dir `<APPDATA>/Factorio`, game
  `<game-install-dir>`. See
  `references/dmr-dump-data-diagnostics.md` for the full analysis workflow
  (replicating build_recipe_map/build_tech_map from the dump in Python).
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
- **Own-mod resource entity mapped as base resource** (v3.7.0, found via dump
  log): DMR's own `tenemut-near-spawn` resource entity produces
  `dmrsa-tenemut`, so `initialize_base_resources()` maps the mod's own
  research item as a tier-1 base resource ("Dynamically mapped base resource:
  dmrsa-tenemut (Tier 1...)"). The target-mapper's gprefix filter excludes
  dmrsa-* from replication targets, but the cost-solver's resource scan is
  not gprefix-aware. When the mod's own items appear as "dynamically mapped
  base resources", skip names with the mod's own prefix inside
  `initialize_base_resources`.
 - **Lab-inputs defensive validation** (v3.5.22): PASS 4 of data-final-fixes
  adds SA science packs to `replication-lab.inputs` (4 planetary + space +
  promethium). Belt-and-suspenders pattern: after the add-loop, RE-VALIDATE
  that every intended pack is actually present in `lab.inputs`, and warn via
  `helpers.warn` (visible at default log level) if one is missing OR if
  `lab`/`lab.inputs` is nil. The silent failure mode is "no lab will accept
  all the science packs" appearing only at research time; the warn surfaces
  it at load. When extending a data-final-fixes PASS that mutates a
  prototype's array field, always add the verify-after-write loop — insertion
  can fail silently (nil table, wrong prototype name).
 - **Cosmetic research-pack-order setting** (v3.5.23): for a display-order
  setting that must apply at MANY call sites (both the individual-tech flow
  AND the grouped-tech flow in dynamic-generator.lua — the two blocks are
  near-identical and BOTH must be patched, use `replace_all` on the shared
  `table.insert(research_packs, ...)` pattern), extract a local helper that
  reads the setting once:
  ```lua
  local function add_research_pack(research_packs, pack, is_dmr_item)
      local order = helpers.get_startup_setting("dmrsa-research-pack-order", "DMR Item First")
      if order == "Science Pack First" and is_dmr_item then
          table.insert(research_packs, 1, pack)
      else
          table.insert(research_packs, pack)
      end
  end
  ```
  Flag DMR intermediates (`true`) vs vanilla/SA science packs (`false`) so the
  helper can reorder. Cosmetic settings need locale name+description in BOTH
  EN and ES, and the description must say "cosmetic — cost unchanged" so users
  don't expect balance effects. Default MUST preserve historical behavior.
 - **Composite icon layers: drop icon_mipmaps when re-layering icons**
  (v3.5.24): when building a dynamic tech/recipe icon by deep-copying the
  source item's `icons` array and compositing it onto a custom border
  (`get_tech_icons` in dynamic-generator.lua), the copied layers inherit
  `icon_mipmaps` from the original item. Mipmaps belong to the original
  item's OWN rendering pipeline (which renders at multiple scales); copied
  into a 128x128 bordered icon with a different scale, they misrender —
  symptom: only the TOP-LEFT CORNER of the icon shows, for items with
  large/custom icons (inherited upstream 0.8.0 bug). Fix: `spec.icon_mipmaps
  = nil` on every copied layer, plus nil-safe the per-layer `icon_size`
  (`if type(isize) ~= "number" or isize <= 0 then isize = 64 end`) so a
  missing/non-numeric size can't produce a bogus scale. General rule: when
  you re-compose a prototype's icon data into a new container, strip
  fields that only make sense in the original rendering context (mipmaps;
  be suspicious of inherited `scale`/`shift` too). Detection: user reports
  replication tech icons showing only the top-left corner; audit
  `get_tech_icons`-style icon composition, not the source item definitions.
 - **`data:extend({})` with an empty array crashes at load — and a "fix applied
   but duplicated" looks fixed while still broken (2026-08-16, factorissimo-2).**
   `core/lualib/dataloader.lua:23 ... Invalid array of prototypes: {}` with a
   stack through `data:extend` means a mod called `data:extend({})` (or with an
   empty table built at runtime). Classic cause: a function that collects
   prototypes into a table and unconditionally `data:extend(that_table)` even
   when nothing matched (factorissimo's `add_music` extended `new_musics` even
   when the ambient-sound loop found nothing). Fix pattern: guard the extend —
   `local has = false ... if has then data:extend(items) end` (or `if #items > 0
   then`) — never call extend on a possibly-empty array.
   **CRITICAL diagnostic**: when the user says "ya hice el fix" but the SAME
   error persists at a NEWER line number, check whether the fix was applied as
   a REPLACEMENT or an ADDITION. In factorissimo's `space-location.lua` the
   PR #290 fix (wrap `data:extend(new_musics)` in `if has_new_music`) had been
   INSERTED as a NEW line BELOW the original unguarded call, leaving BOTH:
   ```lua
   data:extend(new_musics)                                  -- original, no guard → still crashes
   if has_new_music then data:extend(new_musics) end        -- the "fix" (duplicate)
   ```
   The error then reports the UNGUARDED call's line (136), one line above the
   guard. When patching a zip by rewriting a file, ALWAYS verify after: assert
   the old line is GONE (grep for the bare call) and exactly ONE guarded call
   remains — not just that the fix string is present. A substring `in` check
   for the fix can pass while the broken line still sits adjacent.
   Zip-edit pattern: read entries into memory, rewrite the target file, write a
   new zip, then re-open and print the surrounding lines to confirm the repair.

 - **Verify a roadmap feature doesn't already exist before implementing**
  (v3.5.23 lesson): the ROADMAP item "Power drain configurable" turned out to
  be ALREADY IMPLEMENTED upstream (`replstats-energy-base` + `replstats-energy-factor`
  settings exist in settings.lua with locale EN/ES). Before planning a new
  setting/feature, grep `settings.lua` + `locale/*/*.cfg` for the capability —
  an item inherited from the upstream roadmap can be stale. Mark it `✅ YA
  EXISTE / obsolete` in the ROADMAP instead of re-implementing or deleting it.
  This prevents wasted candidate-freeze → approval → patch cycles on a no-op.
 - **ROADMAP.md long-line edits: don't use `\n` escapes in patch new_string,
   and expect fuzzy-match failure on 500+ char lines** (2026-08-14): ROADMAP
  entries routinely exceed 500 chars (Yuoki pause entry is one line). Two
  traps bit hard: (1) passing the literal two-char sequence `\n` inside
  `new_string` writes backslash-n INTO the file — a single ROADMAP line with
  a literal `\n- [ ]` splits into garbage on the next render; always pass a
  REAL newline (actual line break) in `new_string` to add a new list item.
  (2) The patch tool's fuzzy matcher can fail to locate long unique lines
  even when `old_string` is copied exactly from read_file. Reliable fix:
  `execute_code` with read_file → exact `str.replace(old, new)` (both real
  newlines in `new`) → write_file, then verify the replaced count == 1 and
  re-read the touched lines. Same class as the CRLF receipt pitfall: when a
  string edit on generated/long text misbehaves, do the exact replacement in
  Python instead of fighting the fuzzy matcher.
 - **Locale CFG editing: regex-section split corrupts the file; edit
   line-by-line and verify header count** (2026-08-16, hit twice): parsing
   `locale/*/dark-matter-replicators.cfg` with
   `re.split(r'(?m)^(\[[^\]]+\])\s*$', txt)` and rebuilding with a wrong
   index stride CORRUPTED the file both attempts (headers/bodies swapped,
   sections silently lost). The files are CRLF + very long lines. Reliable
   pattern: read with Python default newline handling (auto-normalizes
   CRLF→LF), walk LINE BY LINE tracking the current `[...]` section, buffer
   body lines per section, flush appending new keys at the section end, write
   with `newline='\n'`; then verify header count == 16 and every new key
   present. If corrupted, restore from the GitHub repo raw
   (`raw.githubusercontent.com/Jaer985/dark-matter-replicators-reborn_3/main/locale/...`)
   — the just-pushed repo acts as a clean backup. For a new placeable machine
   the locale needs BOTH item-name/item-description AND entity-name/
   entity-description (no fallback), a recipe-name template with exactly the
   placeholder count the caller passes, and mod-setting-name +
   mod-setting-description in EN + ES.
 - **Quality variants are engine-expanded AFTER mod data stages — invisible
   to mods** (v4.1.0, dump-verified): `data-raw-dump.json` shows ZERO items
   with quality suffixes and ZERO recipes with a `quality` field even when a
   quality mod is active (quality-module recipes and `sSasha__quality-lib__*`
   recycling recipes ARE present), and recipes with fixed-quality outputs are
   legal (the Quality Refiner uses them). Consequence: "replicate quality
   variants as targets" is impossible from data-final-fixes; quality work
   must use per-recipe fixed quality + probability, or runtime logic. Gate a
   quality-dependent subsystem on `data.raw["quality"]["uncommon"] ~= nil`
   (exists only when a quality mod is active). See
   `references/dmr-quality-refiner-v4.1.md`.
 - **Idle animation to "turn off" a machine visually, no new assets**
  (v3.5.25 + v3.6.0 FIX): an assembling-machine with only a
  `graphics_set.animation` shows that animation even when idle (Factorio
  freezes it on frame 0, but it still looks "on"). To make the machine
  visibly power down when it has no recipe/input, add
  `graphics_set.idle_animation` — the SAME sprite sheet, plus a dark `tint`
  (e.g. `{ r = 0.55, g = 0.55, b = 0.55, a = 0.9 }`):
  ```lua
  graphics_set = {
      animation = { filename = "...replicator-N.png", width = 113, height = 91,
                    frame_count = 33, line_length = 11, animation_speed = 1/3,
                    scale = s, shift = { ... } },
      idle_animation = { filename = "...replicator-N.png", width = 113, height = 91,
                         frame_count = 33, line_length = 11, animation_speed = 0.01,
                         scale = s, shift = { ... },
                         tint = { r = 0.55, g = 0.55, b = 0.55, a = 0.9 } }
  }
  ```
  **CRITICAL (v3.6.0)**: `idle_animation.frame_count`/`line_length` MUST
  equal `animation`'s values when reusing the same sprite sheet — Factorio
  2.x rejects a mismatch at load ("Idle animation must have the same frame
  count as animation").
  **CRITICAL (v3.6.1)**: `animation_speed` MUST be > 0 — Factorio rejects 0
  ("Animation speed has to be greater than 0"). Use `animation_speed = 0.01`
  (visually static, ~55s per 33-frame cycle) to freeze the idle.
  Factorio automatically swaps to `idle_animation` when the machine is not
  working. No new PNG assets required. This is the standard way to satisfy
  the upstream 0.8.0 roadmap item "replicators that turn off visually when
  they have no input". Detection of the need: user says machines "look like
  they're always running" even when starved of input. Sprite sheet geometry
  must be identical between animation and idle_animation (same
  width/height/scale/shift); frame_count/line_length match, and
  animation_speed = 0.01 makes idle static.