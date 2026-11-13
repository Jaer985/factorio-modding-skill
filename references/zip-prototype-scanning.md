# Scanning mod zips for prototypes — parsing traps + sub-agent split

Regex/brace scanning of mod zips in Python (`zipfile` + regex — no `unzip` needed) has five
traps that cost real runs:

1. **`type = "item"` matches inside recipe ingredients.** An entry
   `{type = "item", name = "X", amount = N}` regex-matches an item prototype. Filter
   candidate blocks by top-level keys: real items have `name` + `type` but NOT `amount`.
2. **Prototype blocks include their outer braces.** Top-level keys sit at depth 1 inside
   the block text — skip the outer `{`/`}` when scanning for them.
3. **Ingredients/results tables**: strip the table's outer braces before iterating, or the
   whole table parses as one ingredient (silently keeping only the first name).
4. **Sanitize strings and comments before brace counting** (blank the literals, keep
   length) so braces inside strings cannot corrupt block boundaries; slice the ORIGINAL
   text by the sanitized indices for content.
5. **Runtime recipe rewrites beat static parsing.** Scan for
   `bobmods.lib.recipe.add_ingredient / set_ingredient / set_ingredients / replace_ingredient`
   calls (`set_ingredients` takes a whole table, the others one entry). Do NOT filter
   dynamic edges by "recipe exists in the scanned zips" — tier-1 parts are consumed by
   BASE-GAME recipes (`construction-robot`, `logistic-robot`) that are not in the modlist.

CRLF line endings (`\r\n`) are the norm in Factorio zips: use `\s` regex classes, never
assume `\n`-only text.

Working parser: `scripts/parse_mod_prototypes.py` (args = zip paths; emits
`items_step` / `subgroups` / `produce-consume` JSON). Per-mod findings:
`references/bobs-mod-step-items.md`.

## Sub-agent split for a large modlist

Split the zip list across 3 `delegate_task` leaf agents (e.g. by mod family) with the SAME
script and a JSON output contract (`{items_step: [...], subgroups_interesantes: {...}}`).
- Have each agent WRITE its JSON to its OWN file as the deliverable — not just the final
  message, so partial work survives a limit or a failure.
- Give each agent its own script filename: a shared `/tmp/*.py` gets overwritten by whoever
  runs last.
- The consumed-by-≤N = "step item" heuristic OVER-excludes massively; the upstream fork's
  manual exclusion lists are the ground truth, not the graph.
