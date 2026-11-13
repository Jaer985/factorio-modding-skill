<!-- Split out of SKILL.md on 20261101T050205Z; body is verbatim bullet text from the original
     'Common pitfalls' section, grouped by theme. Index: SKILL.md. -->

# Reference index — the full 'See also' catalogue (verbatim from SKILL.md)

## See also

- `references/server-state-remote-host.md` — **where the project actually lives**:
  the authoritative tree on `debian-server` (`~/projects/Factorio-Modding/`,
  221 MB, specs/dumps/dmr-tests/research), what still works without it, how to sync
  it to a second machine, and the three things that never travel (project tree,
  portal credentials, bot tokens). Read this before claiming a file exists or a
  version is current when the tree is not in front of you.
- `scripts/portal-state-check.py` — one command answers "what is actually published vs what the
  repo claims": portal API + built zip + source info.json/changelog + doc mtimes, with a DRIFT
  line per disagreement. Run it before answering any roadmap / project-state review.
- `references/headless-engine-gate.md` — prove the mod on the real engine: headless
  build + per-run config, gate the **packaged bytes**, `--dump-data` assertions against
  the post-final-fixes state, RCON/console quirks.
- `references/power-machine-prototypes.md` — `burner-generator` vs `reactor`, the
  private-fuel-category lock, the joule ledger, partial-load burn, art-not-frame scaling.
- `references/machine-graphics-pitfalls.md` — idle states on a reused sprite sheet and
  the load-time frame_count / animation_speed rules.
- `references/release-gate.md` §5 — the in-game behaviour gate
  (`research/gate-test-<version>.md`): PASS numbers re-derived from source, doc-vs-doc
  conflicts as ❓ items.
- `references/dmr-ore-free-synthesis-mode.md` — ore-free mode: ingredient-less
  recipe guards, worldgen removal that keeps saves, data-stage gating tests.
- `references/prototype-registry-audit.md` — prototype registries beyond
  `data.raw.item` (science packs are `tool`; ammo/module/capsule/equipment have
  OWN registries — an item-only guard silently skips 142+ targets), structural
  signals over name patterns, cross-mod inheritance, dynamic-routing invariants
  (verify every hardcoded name in the dump BEFORE patching), locale/code drift.
  Load when adding data-stage guards, dynamic routing, or auditing a real-modlist dump.
- `references/audit-and-release.md` — the DMR release cycle: audit pitfalls
  (false-positive duplicates), data-final-fixes PASS 3 patterns, locale section
  mapping, zip release convention, **version-numbering policy** (minor bump when
  many unpublished patches accumulate; keep factorio_version at lowest supported;
  ONE accumulated changelog entry since the last PUBLISHED portal version — check
  the portal API, not the local changelog), settings order collisions. Load when:
  audit, release, locale scan, orphan tech bug, startup crash naming a tech
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
  **Working token (verified 2026-08-12): `GITHUB_TOKEN` in
  `~/.hermes/.env` is a real token for Jaer985 — use it for pushes
  (profile config values are placeholders — the old coder/sysadmin values are gone)**. Includes the full
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
  BEFORE push (401 vs 403 = other-account token), repo-sync preserve-set rule
  (`.git` vs rsync/mirror cleanup), remote-vs-local version check. Load before
  any GitHub push or portal upload.
  **Pitfall (2026-08-22)**: `check-no-private-data.py` flags the literal
  STRING of an env-var NAME (e.g. `GITHUB_TOKEN`) anywhere in the source
  tree — even in docs that merely MENTION where the token lives (a ROADMAP
  line "token GITHUB_TOKEN en ~/.hermes/.env" tripped the scan). The real
  value was never in the tree; the NAME alone is enough to fail. Fix: never
  write a real env-var name (nor the vars' HOME path) into any file that
  ships in the mod folder or gets pushed — paraphrase ("el token de GitHub
  vive en el .env del perfil — ver skill").

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

- `references/mod-portal-upload.md` — publishing a version to the Factorio mod portal:
  pre-flight artifact gate (sha256 + `info.json` version + changelog header asserted in the same
  command as the upload), the JWT upload-token trap, cache-busted API verification, the Mod details
  API for description/FAQ, and the Discord release announcement (`dmr-release-announce.py`,
  bilingual, ≤2,000 chars, rewrite-in-place). Load when a version must be published or verified on
  the portal, or when the announcement is stale.
