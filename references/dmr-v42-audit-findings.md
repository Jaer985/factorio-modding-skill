# DMR v4.2.0 — Deep dump audit findings (2026-08-22, 138-mod modlist)

Full reports live on disk: `~/projects/Factorio-Modding/dark-matter-replicator/research/v42-audit/`
(CONSOLIDADO.md + ores.md + baseline.md + techs.md + planets.md + costos.md +
distribucion.md + exclusiones.md + refiner.md + cost-model.md). Load this ref
BEFORE resuming the v4.2/v4.3 balance work so the pending decisions and the
already-shipped fixes are not re-discovered.

## What shipped in v4.2.0 (already implemented, tests 171 PASS)
- **Fix 1 (mirror)**: process-output tech inheritance — items that are OUTPUTS of
  same-mod producing recipes (no recipe named after them) inherit the recipe's
  unlocking tech (guards: item non-minable, same mod prefix, recycling/barreling
  excluded). Result: materials-1 108 → 25 legit items; mirror 1328 → 1457.
- **Fix 2 (cost-solver)**: MOD_ORE_TIERS became a UNIVERSAL floor on every
  solve_cost return (base resources, recipe chain, cycle/unknown fallbacks),
  longest-match selection (escaped `%-` patterns). Table extended for ores AND
  non-ore baseline materials (plastic-bar/resin/rubber/wax/polysaccharides/
  sulfuric-acid/nitrogen/nitric-acid→3; ammoniacal-solution/lava/blood/lymph/
  royal-jelly→4; sand/gas-natural→2; thermal-water/multi-phase-oil→3; rpg_→3).
- **Materials techs**: explicit localised_name template (dmrsa-materials-tech)
  + hardened pack fallback (never empty ingredients — the tenemut pack is a TOOL
  prototype; a missing detect rendered "no research cost").
- **Audit A-fixes (bug fixes shipped same day)**:
  * Versioned Bob's personal equipment `-equipment-2..6` excluded via
    `%-equipment%-%d+$` (plain `%-equipment$` never matched the versioned names);
    solar/battery equipment stays KEPT.
  * Bob's combat robots/drones/ant mines were blacklisted in the A-fixes,
    **BUT REVERTED the same day by user decision B5** (they are REPLICABLE in
    their vanilla tier — see Decisions below). Current state: combat robots,
    capsules, mines all replicable; only weapons/armor/vehicles/versioned
    personal equipment + factory-circuit-connector + bob-spidertron-cannon
    remain excluded.
  * Planet routing: fulgora "scrap" matcher no longer catches spaceship-scrap;
    foundry + lava route to vulcanus.
  * **NEW PATTERN (reusable)**: TECH_REDIRECT / BASELINE_FORCE tables in
    mirror-generator.lua — manual original-tech overrides for items whose
    homonym unlock was warped by mod re-gates. carbon + spaceship-scrap →
    space-platform; burner-pumpjack → baseline (its only unlock in this
    modlist is cryovolcanic-power/Aquilo L5).
- Zip always rebuilt at `dark-matter-replicators-reborn_4.2.0.zip`.
- **B3 shipped (2026-08-22)**: Bob's 6 gem ores replicable at tier 5 — they
  are ITEMS whose only producing recipes are `-recycling` (excluded from
  build_recipe_map), so the solver found no path AND the phantom-item
  eligibility rule rejected them. Fix TWO parts: (a) `BOB_GEM_ORES` SET
  whitelist in target-mapper bypassing eligibility; (b) entries in
  BASE_RESOURCE_COSTS (45 DM, tier 5) so solve_cost has a path.
  **Pitfall: a Lua table built as an ARRAY (`{"a","b"}`) looked up by NAME
  (`set["a"]`) returns nil — whitelists must be built as SETS
  (`for _,n in ipairs({...}) do SET[n]=true end`).**
- **B5 shipped (2026-08-22)**: combat capsules + mines + combat robots are
  REPLICABLE in their vanilla tier (reverses the v4.0 "1-solo-uso"
  exclusion for them): `COMBAT_CAPSULE_PATTERNS` block deleted from
  is_v4_excluded, combat-robot names removed from V42_EXCLUDED. They route
  through the normal mirror → their original tech (grenade→military-2,
  poison→military-3, cliff-explosives→cliff-explosives,
  defender-capsule→defender, land-mine→land-mine, bob-laser-robot-capsule→
  bob-laser-robot...). Only weapons/armor/vehicles/versioned personal
  equipment stay excluded. Test mirror asserts updated: capsules/robots/
  mines/gems ~= nil.
- Tests: **171 checks PASS** (test_mirror 46).

## User decisions — B items CLOSED 2026-08-22 (do NOT re-ask)
1. **B1: split `-N` tech collapse → OPCIÓN C — IMPLEMENTED 2026-08-22**: the
   10 candidates reduced to 7 REAL chains after dump (bob-oil-processing
   absent; angels-oil-processing and bob-electronics single-level). Split
   per level: automation (6), logistics (6, incl `logistics-0`), logistic-
   system (3), bob-robo-modular (4), angels-metallurgy (5),
   angels-advanced-chemistry (5), angels-nitrogen-processing (4). Mirror
   466 → 492 (+26). KEY mechanic: each leveled mirror's TIER = the cost-
   solver tiers of its ITEMS (not the original tech's science level) —
   asm-6 gates behind replication-4 instead of unlocking with asm-1.
   Contiguity verified before coding: every level has ≥1 replicable item
   (base=1, -N=N; logistics works because Bob's `-0` fills level 0).
   Known colateral: angels-advanced-chemistry-1 mixes 6×tier1 + 1×tier3 →
   mirror sits tier 3 (max) — accepted (Angel's chem is tier 3).
2. **B2: cost scale — IMPLEMENTED 2026-08-22 (user-approved final shape).**
   The Opción-C simulation was the seed; the user asked for a MORE WORKED
   formula, clarified intent three times (across-the-board time, energy as
   the real lever, machine layer), then confirmed the final package and
   added the machine-multiplier-per-tier refinement. FINAL IMPLEMENTED
   SHAPE (lib/mirror-generator.lua + replicators.lua + refiner*):
   ```
   base_e   = min(vanilla_energy, solver_tax)   -- never pricier than
   fabricating it nor than its real chain
   mm       = is_machine(item) and MACHINE_MULT[tier] or 1
   raw      = base_e × CT_MULT[tier] × mm
   if fluid then raw = raw × fluid_qty end       -- LOT clamp BEFORE band
   cost     = clamp(raw, BAND_LO[tier], BAND_HI[tier])   -- bands FIXED
   ```
   - min(vanilla, solver) is the KEY: use the item's OWN recipe
     data.raw.recipe[name] energy when it exists (1399/1600 items), else
     the solver_tax. WITHOUT vanilla → solver only. Keeps MACHINE_EFFICIENCY
     alive where the chain dominates (smelting 1/3 keeps plates cheap) and
     bounds absurd chains (centrifuge min(4,600)=4).
   - CT_MULT flat per tier (user: "no tanto el multiplicador de tiempo,
     para que sea mas across the board"): 3/4/5/6/7 for tiers 1-5.
   - **BANDS ARE FIXED** (NOT hi×2 as earlier designed): t1 2-12, t2 4-24,
     t3 8-48, t4 15-90, t5 25-150 nominal (real = ÷ crafting_speed
     1/2/4/8/16). The machine multiplier pushes the raw; the fixed hi caps
     the worst case (t5 machine ≤150s nominal ≈ 9s real at speed 16).
   - **MACHINE_MULT PER TIER** (user's close-of-package refinement, 2026-08-22):
     1.5 / 2 / 2.5 / 3 / 3.5 for tiers 1-5 (replaces the earlier flat ×2).
     DETECTION structural & mod-compatible: pre-pase data.raw once; mark
     entity names as machines when their prototype type ∈ {assembling-
     machine, furnace, mining-drill, lab, centrifuge, rocket-silo, reactor,
     heat-exchanger, boiler, generator, steam-engine, steam-turbine,
     offshore-pump, roboport, beacon, radar, turret, artillery-turret,
     solar-panel, accumulator, storage-tank, pump, electric-energy-interface,
     burner-generator} OR they carry crafting_categories/crafting_speed
     (catches ANY mod machine on standard types). is_machine(item) = its
     place_result is in the set, or its own type is in the list.
     **factorissimo VERIFIED: its factories are storage-tank entities →
     caught automatically** (factory-1 463s → 12s). Solar/accumulator
     explicitly included by the user.
   - **ENERGY is the real balance lever**: replicator kW PER-TIER TABLE
     PER_TIER_MW = {1, 4, 16, 40, 100} in replicators.lua (replaces the
     old exponential 256kW×2.5^(tier-1), whose settings replstats-energy-
     base/-factor are now LEGACY, kept for save compat, unused). Planetary
     replicators stay 400/800 MW (verified in planetary-replicators.lua;
     new t5 100MW shrinks the gap 40-80× → 4-8× — coherent). The
     replication-lab (60kW) eats tenemut+scoop as research inputs →
     tenemut UNTOUCHED.
   - **REFINER**: ENERGY_MULT lib/refiner-generator.lua = 10 → 3 (×10 of
     rebalanced costs = 6000s+ endgame, unplayable; ×3 keeps the quality
     premium playable). Refiner entity kW 1MW → 6MW (prototypes/entities/
     refiner.lua). Science packs refinable = allowed (B4).
   - **FLUID LOT CLAMP (critical, implemented)**: clamp applies AFTER
     × fluid_qty (25) — clamping the unit cost would make water
     0.03s→2s/unit → 50s/batch. In code: raw_cost = raw_cost * fluid_qty
     THEN clamp(raw_cost, BAND_LO, BAND_HI).
   - Simulation sanity numbers (dump-verified): belt 3s, iron-plate 6s,
     plastic-bar 3s (234→3), centrifuge 48s (12s real, machine ×2.5),
     asm-1 4.5s, electric-furnace 48s, stack-inserter 25s (1.6s real),
     steam 12s, space-science-pack 15s, explosives 25s, land-mine 25s,
     solar-panel 12s, steam-engine 4.5s, roboport 24s.
   - VERIFIED during the deep check (do not re-verify): there is NO
     internal 600 cap in cost-solver.lua (grep 0) — the only cap is
     helpers.get_replication_time_cap() (per difficulty) in
     mirror-generator; under the new bands it never activates (stays as
     safety net). Difficulty therefore stops affecting replication time
     (research only) — documented in changelog. Speed modules shorten real
     time and lower energy per recipe (note, not a bug).
   - Tests: 171 PASS (test_refiner asserts updated to 3x5=15).
   - **CLOSE-OF-PACKAGE TODO (user paused once)**: review the 1.5-3.5x
     machine spread against real gate-test data; confirm factorissimo
     factory-2/3/4; watch planetary replicators with the new times.
   - **NOT IN B2 (recorded as idea)**: dmrsa-dark-matter economy is
     ORPHANED (scoop produces it, repl recipes ingredients={} consume
     nothing; tenemut only consumed by research). User: "se usa un monton,
     no hace falta nada alli" — a future layer could consume dark-matter as
     a repl ingredient, but the user declined it as a needed change.
3. **B3: gems only → IMPLEMENTED**: the 6 Bob gem ores ARE replicable now
   (bob-amethyst/diamond/emerald/ruby/sapphire/topaz-ore → tier 5, 45 DM,
   BASE_RESOURCE_COSTS). The subagent-reported "10 Angel's minerals"
   (angels-mineral-tin/...) DO **NOT EXIST** in the dump — child hallucinated
   them from patterns; discarded.
4. **B4: refiner science packs → ALLOWED** (documented as endgame sink);
   refiner cost scale handled in B2.
5. **B5: combat consumables REPLICABLE** (reverses part of the v4.0
   exclusion): turrets (KEEP, machines), ALL mines (land-mine, bob mines),
   ALL combat capsules (grenade→military-2, poison/slowdown→military-3,
   cliff-explosives→cliff-explosives, defender/distractor/destroyer-capsule →
   their combat techs, bob-fire-capsule→military-3) and combat robots/drones
   (→ their bob warfare techs) replicate in their VANILLA tier (via the
   original-tech mirror — never earlier). raw-fish stays on gleba (late
   access = tier-4 replicator). The 16 consumables with no producing recipe
   (depleted cells, potions, preserved science...) are flagged to CHECK later
   — not decided.

## Workflow lessons (resume-able)
- User chooses "fix A first (undeniable bugs), discuss B (design) later" — for
  audit results always split presentation into (A) bugs with code fixes ready
  vs (B) design decisions; implement A on approval without waiting for B.
- The audit used 9 subagents in 3 batches of 3 (see dump-audit-subagents.md
  playbook): CONTEXT.md state file, per-batch "already found — don't
  duplicate", children write full report files + return exec summaries only.
- Dump = installed version, NOT latest local code — user's in-game report of
  v4.1 behavior vs my v4.2 sim was expected; always ask which zip is installed
  before chasing "sim-vs-game" contradictions.
- **Verify every subagent-reported item name against the dump before
  implementing** (2026-08-22): the B3 ore agent reported 10 "Angel's
  minerals" (angels-mineral-tin/lead/...) — NONE exist
  (`item=False, producers=[]`). Children can hallucinate names from naming
  patterns. Cross-check with a one-liner over the dump (`it in
  dump['item']`, producers from data.raw.recipe) before writing any code.
- **Broad planet-routing substrings catch the wrong items** (2026-08-22):
  the fulgora matcher `string.find(name, "scrap")` routed spaceship-scrap to
  FULGORA (a space item). Same class as the science-pack substring pitfall —
  anchor planet matchers (`name == "scrap" or (find "scrap%-" and not find
  "spaceship")`) or list exact names. foundry + lava needed explicit
  `name ==` additions to the vulcanus branch.
- **Elite/utility items as capsules** (2026-08-22): artillery-targeting-remote
  and discharge-defense-remote are `type = "capsule"` — when B5 made ALL
  capsules replicable, the REMOTES must still be excluded (TARGET_BLACKLIST
  catches them by name). B5 = "combat consumables replicable", NOT "every
  capsule type replicable".