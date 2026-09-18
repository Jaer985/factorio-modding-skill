# DMR 4.x — Research Mirror design (agreed 2026-08-12)

> **STATUS: IMPLEMENTED as v4.0.0 (2026-08-12).** Zip
> `dark-matter-replicators-reborn_4.0.0.zip` built (108 files, 4.7MB), tests
> green (test_mirror 30/30, run_tests 34/34, step_filter ALL PASS), locale
> parity OK. Pending: user updates Factorio to 2.1 → gate test → dump 2.1 →
> portal + GitHub. For implementation details (files, MirrorGenerator
> structure) see `references/dmr-v4-mirror-tree.md`; this file is the design
> history.

## Why this design exists

User reported: "lo de basic, shape, alloy, etc... no está funcionando, al final
puedo desbloquear cualquier cosa" — the category system doesn't gate real
progression. Dump analysis (data-raw-dump.json 3.7.1) confirmed:

- **503/945 items** whose replication tier ≠ their original tech's science level
- **25 endgame offenders at tier 3** (requester-chest, buffer-chest,
  energy-shield-mk2, lightning-rod, aai-warehouse-*, mech-armor, tesla-ammo,
  nuclear-fuel, artillery-turret...) — replicable from the Chemical Replicator
  pre-planets (SA auto-recycling recipes made them "produced", and the
  cost-solver pinned them low)
- **440 items (46%)** in `general` category (no tier floor — cost-solver decides)
- Root cause: the cost-solver (ingredient chain) is a BAD progression signal;
  the original tech's science level is the RIGHT signal

## Brainstorm options (4) — user's decisions

- **A: sample-based replication** (replicator learns from a physical sample,
  runtime control.lua) → user wants it as a SETTING, deferred ("para otro
  momento")
- **B: research mirror** (each original tech → its own replication tech) →
  **CHOSEN as the base** ("creo que B es la opcion mas sensata porque no se
  desbloquea todo a la vez")
- **C: machine-as-physical-barrier** (replicator capacity limits like assembler
  ingredient count) → not chosen
- **D: tier = max(original tech, category)** → safety-net / plan B

## Agreed design

- **Research mirror with threshold=1**: EVERY original tech gets its own
  replication tech ("Replication: logistic-system" unlocks replication recipes
  for ALL items that tech unlocks), including 1-item techs. User's "individual"
  means **threshold=1**, NOT tech-per-item (see Pitfalls — this confused the agent).
- **Tier of each mirror tech = science level of its original tech** (1-5), NOT
  cost-solver → automatically fixes the 25 endgame offenders.
- **Prereqs**: original tech + tier machine + materials tech of that tier.
- **Grouped-by-category techs are ELIMINATED**; categories (shape/alloy/chemical...)
  remain only as visual crafting subgroups.
- **Materials techs** (NEW, 5): `dmrsa-replication-materials-1..5`, one per tier,
  unlocking baseline items (ores, fluids, plates with no original tech).
  Prereq: `replication-N`; research pack: tenemut (T1) / dark-matter-scoop (T2) /
  dark-matter-transducer (T3) / matter-conduit (T4,T5). **Materials tech is a
  prereq of ALL mirror techs in that tier** — user: "para poder replicar
  necesitas conocer los materiales" (philosophy: machine → materials → items).
- **Baseline items** (no original tech): 71 → materials techs; 17 planetary →
  their own planetary techs (unchanged).
- **Setting: require original-tech prereq** ("investigar el objeto propio para
  replicarse") ON/OFF — the original-tech prereq becomes configurable, not fixed.
- **Setting: sample-based (A)** — future option.

## Exclusion rules — the MASS-USE principle

User's principle: exclude ONE-TIME personal items; anything with mass/repetitive
use STAYS replicable ("objetos de uso masivo deben poderse replicar").

| Category | Items | Decision |
|---|---|---|
| Guns | 11 | ❌ exclude |
| Armor | 10 | ❌ exclude |
| Combat capsules | 10 | ❌ exclude |
| Vehicles (car/tank/spider/wagons/locos) | 27 | ❌ exclude |
| Vehicle equipment (bob-vehicle-*) | 50 | ❌ exclude |
| Personal equipment | 36 | ❌ exclude EXCEPT solar/batteries |
| **Solar panels + batteries** | 9 | ✅ KEEP (mass use) |
| **Ammo** | 55 | ✅ KEEP (mass use vs aliens) |
| **Fuel cells** | 10 | ✅ KEEP (reactors) |
| **Seeds** | 3 | ✅ KEEP (Gleba agriculture) |
| **raw-fish** | 1 | ✅ KEEP (healing while escaping aliens) |

Total excluded: **144**. Remaining replicable: **801**.

## Numbers (dump 3.7.1)

945 items → 144 excluded → 801 replicable → 713 with original tech →
**417 mirror techs** (T1=119, T2=22, T3=193, T4=10, T5=73) + 5 materials +
4 planetary ≈ **426 techs** (~55% fewer than the 945 individual techs today).

## Quality

The mod does NOT replicate quality items currently — ROADMAP item for future
brainstorming (anotado 2026-08-12 por Jaer985).

## Backup / rollback

The 3.7.1 source is frozen as the stable line. Backup:
`backups/dark-matter-replicators-reborn_3.7.1-source-backup.tar.gz` (verified:
info.json 3.7.1 + changelog 3.7.1 inside). Rollback:
`tar xzf backups/dark-matter-replicators-reborn_3.7.1-source-backup.tar.gz`.

## Pitfalls / lessons

- **User's "individual" = mirror threshold 1, NOT tech-per-item.** The agent
  interpreted it as the existing "Individual Technologies" mode and went down a
  wrong path; user had to correct twice ("Me refiero al umbral a partir de
  uno", "volvamos otra vez... no me estás entendiendo"). When the user refers
  to a brainstorm option, re-read the option's definition before assuming.
- **"Es un fork / punto y aparte" meant BACKUP + don't touch 3.7.1 until
  confirmed — NOT a GitHub fork.** Create the backup, work on the copy/future
  version, keep the published line intact.
- Python dump-analysis pitfalls (recurring): don't name scripts `types.py`
  (stdlib `types` collision → "partially initialized module" circular import);
  tech `unit.ingredients` are list-style `['pack-name', 1]`; filter None tiers
  before `Counter()` or `sorted()` (TypeError comparing None/int).
