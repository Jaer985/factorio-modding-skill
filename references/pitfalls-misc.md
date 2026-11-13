<!-- Split out of SKILL.md on 20261101T050205Z; body is verbatim bullet text from the original
     'Common pitfalls' section, grouped by theme. Index: SKILL.md. -->

# Pitfalls — misc (Lua patterns, subagents, wording)

- **An existence guard only sees what loaded BEFORE it** — a
  `data.raw.<type>["name"]` test inside a `data.lua` file answers false for
  everything defined later: your own other prototype files (e.g. your own
  `technologies.lua`), other mods' `data-updates`, every `data-final-fixes`.
  Declare the reference name plainly and let the final-fixes prereq pass
  (`pass-prereqs.lua`) strip entries that do not exist; probe `data.raw` only
  from `data-updates`/`data-final-fixes`. For prerequisites the empty result is
  far worse than a missing optional gate: a prerequisite-less tech reads as
  orphaned and the orphan pass (`pass-orphans.lua`) DISABLES it — `hidden = true`,
  `enabled = false`, unit rewritten to a 1× tenemut / 1 s placeholder, unlocks
  reassigned elsewhere — while the load still exits 0.

- **Aggregate fan-out assertions per key, not across the list.** Any effect list
  that fans out over N recipes (`unlock-recipe`, `change-recipe-productivity`)
  summed flat multiplies N×M and reports nonsense; group by target (recipe)
  first, then assert that per-key total.

- **Two rules that only fail in-game**: `hidden = true` on a recipe also removes it
  from the MACHINE'S own recipe picker — machine-only recipes use
  `hide_from_player_crafting`; and `change-recipe-productivity` ACCUMULATES across a
  tech ladder, so every node emits the SAME increment (tier-scaled sums to +600 %).

- **Exact-match name bug**: `name == "X"` silently breaks when X has variants
  (`X-cold`, `X-hot`, `X-molten`). Use `string.find(name, "X")` for SA fluids
  and similar.

- **Template-parameter count mismatch** (v3.5.10): code must pass exactly
  N parameters to a LocalisedString template that defines N `__N__`
  placeholders. Extra positional args are reported by Factorio at runtime as
  "Unknown key: type.parameter-N" — once per extra arg per render. Common
  symptom in logs: `Replication: Unknown key: "item-name.X" (Researched)`.
  Common offenders: changing a template from `__1__` to `__1__ __2__` without
  updating the caller, or leaving a stale literal as a "fallback" that the
  template doesn't have a placeholder for. Fix: match parameter count to
  placeholder count exactly.

- **Don't dismiss "X looks weird"** (general principle): user perception of
  weirdness in Factorio is a high-signal bug detector. Audit before
  responding "expected" — multiple times this session the first-pass answer
  was wrong and a deeper read revealed a real bug.
