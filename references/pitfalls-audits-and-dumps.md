<!-- Split out of SKILL.md on 20261101T050205Z; body is verbatim bullet text from the original
     'Common pitfalls' section, grouped by theme. Index: SKILL.md. -->

# Pitfalls — audits, dumps, diagnosis and verification

- **Exit 0 is not a verdict — assert the dump, not the source.** Later passes
  rewrite source-correct edits in place: after `--dump-data`, query
  `script-output/data-raw-dump.json` for the exact values you changed (recipe
  counts, `prerequisites`, `unit`, `energy_required`, `allow_productivity`), and
  grep the load log for each mutation pass's own warning keyword (`orphan`,
  `warn`) — passes that disable or reassign prototypes warn without failing.

- **LocalisedString `"?"` parameter pitfall**: `"?"` is a KEY for fallback
  selection, NOT a positional parameter. Legacy 0.x syntax
  `{ "?", {item-name.X}, ... }` renders as "parameter-0" in 2.x.

- **Factorio data dump workflow** (2026-08-11, DMR v3.7.0 gate test): when the
  user reports in-game tier/prereq weirdness with a big modlist, ask them to
  run `factorio.exe --dump-data` on their Windows PC (from `bin\x64`, game
  closed). Factorio 2.x writes ONE FILE `script-output/data-raw-dump.json` in
  the write dir — NOT a folder with per-type JSONs (the earlier assumption of
  technology.json/recipe.json/etc. was WRONG; Windows Explorer hides the .json
  extension so it appears as a bare `data-raw-dump` item). The file is ~90MB
  with Bob's — cannot go through Telegram (20MB cap); transfer via SCP to
  `~/projects/Factorio-Modding/dark-matter-replicator/dumps/` or 7-Zip first.
  The write-dir log (`factorio-current.log`) is itself highly diagnostic: DMR's
  `helpers.info` lines show the real dynamic mapping per item ("Dynamically
  mapped base resource: bob-tin-ore (Tier 1...)", "Tier override
  bob-sniper-rifle: computed=1 -> category=3 (military)", "Science tier force
  ..."). User's PC paths: write dir `C:/Users/jaer1/AppData/Roaming/Factorio`,
  game `C:/Program Files (x86)/Steam/steamapps/common/Factorio`. See
  `references/dmr-dump-data-diagnostics.md` for the full analysis workflow
  (replicating build_recipe_map/build_tech_map from the dump in Python).

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
