# DMR — nihil fork feature evaluation (2026-08-11)

After mining `dark-matter-replicators-space-age_2.0.4` for the step-item
exclusion data, the user asked whether the REMAINING upstream features were
worth porting: "realmente vale la pena? O podemos hacerlo mas avanzado y
mejor?" This is the evaluation that landed. Re-check before re-implementing
any of these — the verdicts below reflect user preferences (minimal-viable,
automatic > config-heavy).

## What nihil has that DMR (Jaer985 fork) does NOT

| Feature | nihil impl | Verdict | Why |
|---|---|---|---|
| Per-category enable settings | `repltype-<name>` bool-setting generated for every repltype (ore, element, shape, alloy, chemical, device2-5, life, module, exotic, magic, alien, science) — 16 checkboxes | ❌ SKIP | Config noise; user wants minimal-viable. If a category bothers a player, a global "hide" toggle or auto-hide-empty is better than 16 toggles |
| Research multiplier per category | `research_multiplier = 0.5` on `element` repltype | ⚠️ PORT-IMPROVED | Balance fine-tuning is real, but better as global difficulty (already have `dmrsa-research-difficulty`) or a single per-category table, not scattered fields |
| device2-5 categories (by complexity) | 4 categories: Very Simple/Simple/Complex/Very Complex | ❌ SKIP | Our cost-solver already computes tiers dynamically from ingredient chains; fixed complexity buckets are the OLD approach we replaced |
| `upgrade = true` on module repltypes | Marks module techs as upgrades (different UX in tech tree) | ⚠️ LOW | Minor UX polish; only matters for individual-tech mode |
| Per-mod whitelists (`repltech_recipe` in replications/*.lua) | 19 files hand-listing category/tier per item per mod | ❌ SKIP | Our dynamic generation replaces this; only the `replvar` EXCLUSIONS were worth mining (done in v3.6.3) |
| Item-group `inventory_order`/`order` metadata | group = "g", order = "e" | ⏭ Trivial | Copy if it improves tab position |

## What the review produced instead (better/automated)

1. **Auto-hide empty replication categories** — if a category has no items
   after step filtering, don't generate its subgroup or techs. Zero config,
   automatic. NOT YET IMPLEMENTED (backlog).
2. **Step-item hybrid filter** (v3.6.3) — already shipped; the real
   high-value output of the nihil review.
3. **Global research difficulty** (v3.5.16) — already shipped; covers the
   per-category multiplier intent in one setting.

## Process rule

When reviewing an upstream fork for features, classify each candidate as:
(a) port as-is, (b) port improved/automated, (c) skip. Justify every (c)
against the user's minimal-viable + automation preference instead of
silently porting everything.
