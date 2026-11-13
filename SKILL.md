---
name: factorio-modding
description: "Trigger: Factorio modding, Lua, prototype, control.lua, data.lua, recipe, technology, desync, migration. Full-stack Factorio 2.0/2.1/Space Age modding — prototype definition, runtime scripting, version migration, changelog research, dump-driven audits, and compatibility-first development."
license: MIT
metadata:
  author: Jaer985
  version: "3.1"
---
# Factorio Modding

## Where the project lives

The authoritative tree is the **Windows laptop** (moved there 2026-10-30):
`C:\Users\JAER\Documents\Projects\factorio\Factorio-Modding\dark-matter-replicator\` — `dark-matter-replicators-reborn_3/`
is the mod source, next to `dmr-tests/`, `research/`, `github-sync/` and `backups/` (moved under `factorio/`
after the 2026-11 project reorg; the older `Projects\Factorio-Modding` path no longer exists). The old tree on
`debian-server` is a copy that may lag. Split, sync and what never travels: `references/server-state-remote-host.md`.

Test runner on this machine: **real Lua 5.2.4** (`lua52` on PATH, from `%LOCALAPPDATA%\hermes\tools\lua52\`):
`cd dmr-tests && lua52 run_tests.lua` → 54 passed, 0 failed.

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
6. **Consolidation brief — one file, read BEFORE any code changes.** Merge the per-subsystem
   reports into `research/<ver>-audit/brief-<ver>.md`, deduplicated by root cause (one entry per
   cause, citing every report that found it, never an entry no report contains), sections in this
   order: release blockers · broken mechanics · exploits **each with its measured multiplier** ·
   consistency/dead weight · ideas · **DECISIONS ONLY THE AUTHOR CAN TAKE** (options + your
   recommendation + an approval handle like `F-2a`/`F-2b` so he can answer in one line) ·
   **VERIFIED CORRECT — DO NOT TOUCH** · ordered action plan with S/M/L effort. The
   decisions/verified sections are what make it reviewable: he approves the plan first, then the
   fixes are applied.
7. **Audit graphics like code.** Sprite geometry is checkable, not subjective: compare each
   declared `width/height/frame_count/line_length/scale` against the PNG header; compute the art's
   bounding box from the alpha channel and compare it to the entity's collision/selection box (a
   scale derived from the *frame* size instead of the *art inside it* renders a machine small and
   off-centre); md5 the alpha masks across sheets — identical masks mean every tier is one reused
   silhouette. `--dump-data` gives every sprite path a prototype claims, so missing paths are a
   mechanical diff.

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


## Chance-based products and "automatic" claims (2.1)

- **`independent_probability` rolls each product on its own** — ProductPrototypeBase (2.1.x) states the products
  "may use different roll value", so several can be given by one craft; `shared_probability` is the single roll
  compared against ranges (non-overlapping ranges = mutually exclusive). A generator that writes
  `retry = 1 - loss - p` on two `independent_probability` products gets `keep=(1-p)*retry`, `up=p*(1-retry)`,
  `both=p*retry`, `nothing=(1-p)*(1-retry)` — at 0.94/0.05 that is 4.7 % free duplicates and 5.7 % destroyed,
  not the documented 1 % loss. Use `shared_probability` for keep/upgrade/destroy, or write the joint
  distribution down and re-derive every pacing number from it. Assert the joint distribution in `dmr-tests`,
  never the two probabilities separately. Full worked case: `references/dmr-quality-refiner-v4.1.md`.
- **A changelog line or code comment that says "automatic" is a hypothesis, not a receipt.** Prove it by
  grepping the tree for the ONE call that would implement it (`grep -rn crafter_output`): reading the output
  inventory is not moving it, and a crafting machine never consumes its own output.
- **`entity.set_recipe()` empties a crafting machine's input inventory.** Any one-recipe-per-quality-step
  design that repoints recipes therefore deletes every stack that does not match the new ingredient. Repoint
  only when the input is empty or single-quality, or drain it first.
- **A "it does nothing" report is a count, not an impression.** Compute the expectation from the shipped odds
  before judging (e.g. 20/40/80/100 cycles per quality step) and quote the p-value of the observed count —
  "0 upgrades in 100 cycles" is a bug at p≈0.6 %, "same item out" at 20 cycles is the design.

## Pitfalls — four themed files, load the one that matches the symptom

The pitfall history (~67 KB, one entry per bug class since v3.5.x) was split out of this file on 2026-11-01;
it is **verbatim**, grouped by the topic of each entry's lead-in. Read the matching file **before** patching —
every entry names the symptom that triggers it.

- `references/pitfalls-data-stage.md` — load order, `data.lua`/`data-updates`/`data-final-fixes`, `safe_require`
  swallowing errors, optional-dependency races, target-mapper/step/eligibility filters, `on_init` guards,
  the dynamic generator.
- `references/pitfalls-tiering-balance.md` — tiers, cost-solver, cost model and bands, science-pack anchoring,
  categories, machine efficiency, fluids, research difficulty, balance levers.
- `references/pitfalls-audits-and-dumps.md` — the audit-then-bulk-fix cycle, dump-driven diagnosis, subagent
  batches, receipts that lie, verification habits.
- `references/pitfalls-misc.md` — Lua vs Python pattern semantics, naming/wording drift, small one-off traps.
- `references/pitfalls-release.md` — zip receipts, changelog and version bumping, GitHub push, privacy scan,
  portal upload and announcements.

## References — crafted playbooks

Annotated catalogue with the trigger for each file: **`references/reference-index.md`** (the old "See also"
list, kept verbatim). Files currently present:

- `references/aai-k2-power-bridge.md`
- `references/audit-and-release.md`
- `references/bobs-mod-step-items.md`
- `references/dmr-2.1-category-audit.md`
- `references/dmr-3.5.1-orphan-tech-audit.md`
- `references/dmr-aai-loaders-compatibility.md`
- `references/dmr-angels-petrochem-compatibility.md`
- `references/dmr-angels-smelting-compatibility.md`
- `references/dmr-bobs-mod-structure.md`
- `references/dmr-bobs-science-pack-detection.md`
- `references/dmr-bobs-tier-misassignment.md`
- `references/dmr-briefing-monitor-list.md`
- `references/dmr-category-tier-system.md`
- `references/dmr-compounding-balance-fix.md`
- `references/dmr-cost-solver-balance.md`
- `references/dmr-cost-solver-test-harness.md`
- `references/dmr-dual-compat-2.0-2.1.md`
- `references/dmr-dump-data-diagnostics.md`
- `references/dmr-dump-driven-audit.md`
- `references/dmr-github-publishing.md`
- `references/dmr-icon-assets-generation.md`
- `references/dmr-machine-efficiency-sa-category-drift.md`
- `references/dmr-moon-eneas-compatibility.md`
- `references/dmr-nihil-feature-evaluation.md`
- `references/dmr-ore-free-synthesis-mode.md`
- `references/dmr-original-fork-analysis.md`
- `references/dmr-original-mod-study.md`
- `references/dmr-quality-refiner-v4.1.md`
- `references/dmr-research-mirror-4x-design.md`
- `references/dmr-roadmap-modernization-2026-08-09.md`
- `references/dmr-space-age-lab-inputs.md`
- `references/dmr-test-suite.md`
- `references/dmr-tier-cap-safe-prereq-3.3.6.md`
- `references/dmr-tier-gating-redesign.md`
- `references/dmr-tier-rebalance-plan.md`
- `references/dmr-v3.5.0-audit-findings.md`
- `references/dmr-v4-mirror-tree.md`
- `references/dmr-v4-tier-redesign-analysis.md`
- `references/dmr-v42-audit-findings.md`
- `references/dmr-v42-cost-model-b2.md`
- `references/dmr-yuoki-compatibility.md`
- `references/dump-audit-subagents.md`
- `references/economy-and-arbitrage.md`
- `references/engine-level-verification.md`
- `references/factorio-2.0-runtime-migration-patterns.md`
- `references/factorio-2.1-breaking-changes.md`
- `references/factorio-cost-solver-pitfalls.md`
- `references/headless-engine-gate.md`
- `references/machine-graphics-pitfalls.md`
- `references/mod-portal-upload.md`
- `references/portal-discussion-scraping.md`
- `references/power-machine-prototypes.md`
- `references/prototype-feature-probe-ab.md`
- `references/prototype-registry-audit.md`
- `references/release-gate.md`
- `references/release-push-and-privacy.md`
- `references/server-state-remote-host.md`
- `references/tech-deadlock-diagnosis.md`
- `references/zip-prototype-scanning.md`
