# DMR roadmap modernization — case study 2026-08-09

## Context

DMR (Dark Matter Replicators Reborn) is a fork chain:
- pre-0.3 jamupsi → 0.17 chipgeekjr → 18 Honktown → 2.0 nihilistzsche → 3.0+ Jaer985 (current maintainer)

The `roadmap.txt` in the mod root was inherited from upstream and frozen at the
0.17/0.18 era. It contained items like:

```
0.7.14+ - Eventual Future Things
    Use overrides or something to reorder the science packs in the replication selector
    Add replication of Darkstar Utilities ores and items once that mod works with Factorio 0.17
0.8.0 - Graphical Polish
    Fix a bug where replication icons for items with high resolution icons only show the upper left corner
0.8.1 - Replication-based Scenario
    Create a scenario in which no ores are generated but the player starts with some electrical grid items
```

These version anchors (`0.7.14+`, `0.8.0`, `0.8.1`) are NOT mod versions — they're
hopes-and-dreams tags from a maintainer who stopped at pre-2.0. The current mod is
at **v3.5.1** with `factorio_version: "2.0"`.

## What went wrong in triage

When the user asked "¿qué tenemos pendiente?" I summarized the file content as
"pendiente real" — quoting items like "power drain configurable de replicators"
and "OmniMatter + tenemut from omnite" as if they were the current maintainer's
plans. **They are not.** The user caught this immediately: "roadmap ese es viejo, no?".

## Detection checklist (use BEFORE quoting any roadmap item)

```bash
# 1. Check who wrote the roadmap
cat authors.txt
# If the current maintainer is not the original roadmap author, the file is
# likely inherited.

# 2. Compare roadmap version anchors against info.json
grep -E "^\s*0\.|^\s*[1-9]\." roadmap.txt | head -5
cat info.json | grep '"version"'
# If roadmap uses 0.x and info.json says 3.x, the roadmap is upstream.

# 3. Cross-check roadmap items against changelog.txt — anything in
#    changelog.txt is SHIPPED, not pending.
grep -i "Darkstar\|OmniMatter\|scenario.*no.*ores" changelog.txt
```

## Resolution

1. **Borrar el `roadmap.txt` heredado** (user said: "borralo directamente")
2. **Crear `ROADMAP.md` nuevo** based on:
   - `changelog.txt` history (qué se acaba de cerrar)
   - `info.json` (versión y factorio_version actuales)
   - Code state real (grep por features mencionadas, ej. `dmrsa-use-machine-efficiency` en settings.lua)
   - Issues conocidos en runtime (lo que el user reporta en juego)
3. **Estructura del nuevo ROADMAP.md**:
   - ✅ Cerrado recientemente (últimos 3-4 changelog blocks)
   - 🔴 Patch series próximo (v3.5.2, v3.5.3)
   - 🟡 v3.6.0 (features QoL)
   - 🟢 v3.7.0+ (features mayores)
   - 🔧 Backlog técnico
   - 📋 Procedimiento de release
   - 🎯 Prioridad inmediata (esta semana)

## Key takeaway for future sessions

**Forks inherit documentation debt as much as code debt.** Before treating any
`roadmap.txt` / `TODO.md` / `CHANGELOG.md` in a forked mod as the current
maintainer's voice, run the detection checklist above. If the file is
inherited, surface that explicitly to the user — don't synthesize a "current
plan" out of upstream hopes.

The user values "clean slates over iterating broken fixes" and prefers honest
"this is stale, should I delete or modernize?" over false confidence.
