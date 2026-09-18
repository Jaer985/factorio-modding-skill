# Dump-audit with subagents — orchestrator playbook

**Load when the user asks to audit a big data dump "por partes" with multiple
subagents** ("hace una investigacion a fondo del dump por partes, pon
multiples subagentes... tu solo seras el orquestador"). Validated 2026-08-22
on the DMR v4.2 audit (127MB `data-raw-dump.json`, 138-mod modlist, 9 child
tasks in 3 batches).

## Orchestrator flow that worked

1. **Write CONTEXT.md FIRST** in the output dir (`research/<audit>/CONTEXT.md`):
   dump path, modlist, "lo que YA está corregido" (children must not
   rediscover/fix known things), dump conventions (2.1 recipes use
   `categories` ARRAY, `dmrsa-repl-*` naming, planetary routing heuristics,
   exclusions, the `.match()`/`%-` pitfalls), and the output contract.bat
2. **Split by DOMAIN, one task = one report file**: ores / baseline / techs /
   planets / costs / distribution / exclusions / refiner / cost-model design.
   Do NOT split by file size — domain audit questions are what the user wants
   answered.
3. **Batches of ≤3** (`max_concurrent_children` limit for this user). After
   each batch, append its findings to CONTEXT.md under a
   `## Hallazgos del BATCH N (ya encontrados — NO duplicar)` heading BEFORE
   dispatching the next batch — prevents duplicate work and cross-batch
   contradictions.
4. **Every child gets**: goal + context + required output path. Explicitly
   tell it: write the FULL report to `<dir>/<name>.md`, return ONLY an
   executive summary (top findings + file path), use python3 stdlib, load the
   dump ONCE, do NOT edit the mod, state findings as hypotheses backed by
   real dump numbers.
5. **VERIFY after each batch**: read the report files — a child's "written"
   claim is a self-report, not proof. Check the top lines of each file.
6. Model choice: deepseek-v4-flash was plenty; each child took ~120–315s.

## Report schema that worked

| audit | columns |
|---|---|
| ores / baseline | item \| tier actual (dump) \| tier propuesto \| justificación |
| techs | item \| tech asignada \| techs candidatas \| sospecha \| recomendación |
| planets | item \| planeta actual \| planeta propuesto \| evidencia (spoil_ticks/ingredients/names) |
| costs | item \| tier \| energy_required \| ratio vs vanilla \| acción |

Every report opens with a **scope/limits** line (e.g. "el dump es PRE-fix, los
tiers mostrados no incluyen el override v4.2") so findings aren't misattributed
to current code.

## Reusable insights from the v4.2 audit

- **The dump reflects the INSTALLED version** — if the user hasn't installed
  the latest zip, the dump shows OLD behavior. When a child's numbers differ
  from your sim, check which version the dump came from before changing code.
- **Sim-vs-game contradiction → suspect the sim's language translation**
  (match vs search, `%-` escaping, longest-match choice), not the mod.
- **Overhaul mods REDIRECT vanilla unlocks**: `plastics` unlocks
  `bob-plastic-pipe` / `angels-solid-plastic`, NOT `plastic-bar` — so items
  can have NO unlocking tech at all and go baseline even though "vanilla" had
  a tech. Check the actual unlock graph, never intuition.
- **Quantity before proposing to revert a design decision**: the tech `-N`
  collapse (345 folded techs, 680 items) was a deliberate v4.0 choice; the
  distribution task quantified (608 versioned techs, 345 folded) before
  proposing per-tier mirrors.
- Angular finding worth double-checking in future mods: **cost-scale rot**
  (tier-1 items 200–400s vs tier-5 items 1–3s, global 600s cap flattening
  everything) — the cost-solver's clamp interacts with the tier floor.

## Files from the v4.2 run

Reports: `research/v42-audit/ores.md`, `baseline.md`, `techs.md`, `planets.md`,
`costos.md`, `distribucion.md` (+ `exclusiones.md`, `refiner.md`,
`cost-model.md` if batch 3 finished). Intermediate scripts children left in
the same dir (`_core.py`, `_audit.py`, `_planets_*.py`...) are disposable; the
CONTEXT.md pattern is the reusable part.