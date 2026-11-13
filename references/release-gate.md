# Release gate - the ordering that catches a broken release

Order: build -> gate on the built bytes -> independent review -> fix -> rebuild -> re-gate -> hash ->
announce. Skipping the middle steps is how a mod ships feature-less (wrong directory copied),
uncompressed, or with a changelog the game silently drops.

## 1. Build

- The zip's internal root must be the mod directory WITH the version suffix
  (`<name>_<version>/`, matching `info.json`'s `version`) and it must be the only root entry.
- Exclusions before zipping: research/, specs/, test dirs, .git, __pycache__, .env, editor backups,
  dotfiles. Verify by listing the archive, not by trusting the exclusion list.
- Python pitfall: `zipfile.ZipInfo(path)` defaults to ZIP_STORED, and the archive-level
  `compression=` argument never reaches entries built this way, so everything ships uncompressed.
  Set `compress_type=zipfile.ZIP_DEFLATED, compresslevel=9` on every ZipInfo, then assert the size
  actually dropped.
- Put a require-graph check in the builder (every module reachable from data*.lua, zero broken
  requires). That is what catches a silent removal: the engine loads the data stage with no errors
  and ships a feature missing from the tech tree.

## 2. Gate the packaged bytes

Extract the built zip into a scratch mods dir, point --mod-directory at it, run the headless engine
(see `references/headless-engine-gate.md`) and assert on the dump. A gate run against the working
 tree proves nothing about the artifact.

## 3. Changelog format (the parser is unforgiving)

The in-game changelog viewer parses strictly and drops what it cannot parse; the damage is invisible
in the file and only shows as a missing release in the viewer.

- Newest version first. Each section is 99 dashes, then `Version: X.Y.Z`, then `Date: Y-MM-DD`.
- A separator whose next line is not `Version:` swallows the block. The classic cause is a DOUBLED
  separator at a block boundary when prepending a new version.
- Category lines: exactly two leading spaces and a trailing colon. A two-space line without the
  colon parses as neither category nor entry.
- Continuation lines: exactly six leading spaces. Deeper indentation has shipped tolerated, but it
  is a spec violation worth fixing while the file is open.
- No trailing whitespace; no literal quotes wrapped around entry text.
- Verify mechanically after editing: separators == Version lines == Date lines, every separator's
  next line starts with `Version:`, and no line ends in a space.

## 4. Portal and upload

- `description` (info.json body) and the portal SUMMARY are separate fields; the summary cap is 500
  chars. Keep the description under it so the same text can be reused verbatim.
- Thumbnail is asked as a square PNG - check the dimensions in the builder.
- Filename must be exactly `name_version.zip`, and the version must be strictly newer than the
  newest release the portal lists (check the live portal API before announcing).
- Before upload, re-hash and paste the sha256 into the checklist: a builder re-run rewrites the
  artifact even when the bytes are identical, so a hash taken earlier is not the hash you upload.
- Pair the upload with a check script that diffs the portal API against the version quoted in
  the announcement channel, so a stale announcement fails loudly instead of staying wrong for weeks.

## 5. In-game gate test (the behaviour gate)

The headless gate proves the packaged bytes LOAD; it never proves a machine behaves. What is left is
the author's-PC test, and its only durable form is a checked-in list:
`research/gate-test-<version>.md`.

- Write the list BEFORE the upload. A release shipped on the headless gate alone accumulates an
  unrun behaviour list that nobody can reconstruct afterwards.
- Order by RISK, not by chronology: brand-new entities first, surfaces that were broken in an
  earlier release second, cosmetics last.
- Every item needs a PASS criterion carrying a NUMBER taken from the prototype (`energy_usage`,
  recipe `ingredients`, `energy_required`, the fuel_value/consumption ledger). "Draws the right
  power" is not a test; "draws 250 MW" is.
- NEVER copy acceptance numbers from an older gate list - re-derive each from the source. Old lists
  outlive the balance changes that invalidated them.
- When two docs disagree about behaviour, do not pick a winner in prose: mark the item
  `CONFLICT TO RESOLVE`, state what each source claims, and let the test decide. Either outcome is
  useful; a silent pick is not.
- Behaviour the headless gate cannot see, so it belongs on the list: recipe pickers, fuel slots
  accepting and refusing items, burn duration under PARTIAL load, module slots, sprite centring,
  neighbour bonuses.
- Fixed report format: `number -> PASS/FAIL: what you saw` plus the log path and one screenshot. A
  free-form review cannot be ticked off, and the screenshot catches what the log never mentions.
- Any FAIL stops the release chain - a later release must not paper over it.
