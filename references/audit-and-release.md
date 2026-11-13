# DMR — Audit, Hardening, and Release Workflow

_Distilled from the v3.5.2 → v3.5.17 release cycle on `dark-matter-replicators-reborn`._

## MANDATORY PRE-FLIGHT: comprehensive audit before any patch (v3.5.7 lesson, reinforced v3.5.8)

**This rule supersedes the natural tendency to patch and rebuild iteratively. Apply
before every release cycle.**

When the user reports a bug OR you discover one through static analysis:

1. **STOP**. Do not patch immediately.
2. **Enumerate ALL violations of the same class** across the entire codebase:
   - User reported "replicators in wrong category" → grep ALL `subgroup = "X"` in
     `prototypes/`, cross-reference against the mod's defined `item-subgroup`s,
     find every leak (vanilla OR missing mod subgroups).
   - User reported "weird text in-game" → grep ALL `localised_name`/`localised_description`
     blocks, audit the LocalisedString structure field by field.
   - User reported "wrong tier classification" → audit ALL relevant code paths,
     not just the one that surfaced.
   - User reported "item shows from wrong tier replicator" → check for
     `name == "X"` exact matches vs `string.find(name, "X")` substring matches.
3. **Build a checklist** of every issue found, organized by bug class.
4. **Patch ALL of them in one batch**, even if they span multiple files.
5. **Rebuild ONCE** and verify all fixes landed.

**Evidence from this session** (DMR v3.5.5 cycle):

- User: "the replicators should be inside the Replication category"
- Round 1: fixed `production-machine` subgroup leak on tier 1-5 replicators. Rebuilt zip.
- Round 2: user verified, found tier subgroup locales were missing (5 more entries).
- Round 3: added locales. Rebuilt zip.
- Round 4: user verified, found tier subgroup names in locale were raw (5 more).
- Round 5: added names. Rebuilt zip.

**Five patch-rebuild iterations to fix what was a single audit domain.**
One grep of `subgroup = "X"` values + one locale cross-reference would have
caught all of them upfront.

**Anti-pattern (don't do this)**: patch one leak, rebuild, user finds another
leak of the same class, patch, rebuild. The user gets frustrated because every
round trip is a verification cycle they have to perform. They explicitly asked
in this session: "podemos revisar todo y luego actualizar completo y probar
completo" — that's the signal to switch modes.

**Pattern**: enumerate → fix all → verify once. This is the same lesson from
the `"?"` LocalisedString pitfall (v3.5.4) — that lesson was written but not
applied to the v3.5.5 cycle. **Apply it universally.**

**When you can't enumerate comprehensively in one pass** (e.g. the bug class is
too broad), say so explicitly to the user and propose a phased audit. Don't
discover the audit scope incrementally through patch-rebuild cycles.

## Re-audit before patching (PITFALL)

First-pass audits with a long file often produce false positives. Concrete example from this session:
- Reported `replication-3` technology as "duplicated" in `technologies.lua`
- Reality: two `if/else` branches (`mods["space-age"]` true vs false) writing the same key under mutually exclusive conditions
- Cost: a wasted fix proposal + user time reviewing it

**Rule**: before suggesting a fix from a grep or scan, re-read the actual block with the
surrounding context (the `if` condition, the calling function, the data:extend call). Cheap
to do, expensive to skip. If the file is > 100 lines, re-read the full block at least once
before patching.

## data-final-fixes.lua PASS 3 patterns

The orphan-tech pattern is non-obvious. Three matching cases, in priority order:

1. `dmrsa-replication-N` (N in 1..5) → reassign to `dmrsa-replication-N`
2. `dmrsa-grouped-repl-N-{category}-tech` → reassign to `dmrsa-replication-N`
3. `dmrsa-grouped-repl-{planet}-{category}-tech` → reassign to `dmrsa-replication-{planet}-tech`

**Tier 3 with Space Age is the trap**: the natural `replication-3` target still exists
(hidden placeholder, empty effects) but the original code set `target_tech_name = nil`,
silently losing unlocks. Fix: assign to the placeholder — it has `effects = {}` so
reassigning to it is safe and inert.

**Always include a defensive `helpers.warn(...)` when no pattern matches.** Silent failure
on an unknown orphan shape means future mod combos break without trace.

## Locale audit methodology

Factorio's locale sections are not 1:1 with prototype `type`. The mapping is:

| Prototype `type` | Locale `[name]` | Locale `[description]` |
|---|---|---|
| `item` | `item-name` | `item-description` |
| `recipe` | `recipe-name` | `recipe-description` |
| `technology` | `technology-name` | `technology-description` |
| `lab`, `assembling-machine`, `furnace`, etc. | `entity-name` | `entity-description` |
| `item-group` | `item-group-name` | (none) |
| `item-subgroup` | `item-subgroup-name` | (none) |
| `recipe-category` | `recipe-category-name` | (none) |
| `fluid` | `fluid-name` | `fluid-description` |
| `bool-setting`, `string-setting`, `double-setting`, `int-setting` | `mod-setting-name` | `mod-setting-description` |

**Audit approach** (do this in `execute_code` for accuracy):
1. Walk `prototypes/**/*.lua` for `{ type = "X", name = "..." }` blocks (handle `gprefix .. "..."`).
2. Parse `[section]` blocks in `locale/en/*.cfg` and `locale/es-ES/*.cfg` into maps.
3. Cross-reference: for each defined prototype, check the right `*-name` AND `*-description`
   sections in BOTH locales.
4. Report missing as `(type, locale, name|desc)` tuples.

**Common bugs found by this audit** (DMR example):
- `dmrsa-replication-1..5` (the 5 tier techs) had NO entry in `[technology-name]`. The
  planetary techs (`dmrsa-replication-vulcanus`, etc.) were present, masking the gap.
- `dmrsa-replication-resources`, `dmrsa-replicators` (item subgroups) had no name → shown
  raw to users.
- 4 recipe categories (`dmrsa-replication-vulcanus`, etc.) had no name.
- `dmrsa-use-machine-efficiency` description said "Disabled by default" but `default_value
  = true`. Sync the description with the code, not the other way around.

**Parser gotcha**: `re.finditer(r'\{[^{}]*\}', src)` only matches non-nested blocks. For
data-final-fixes and similar files with nested tables, you need balanced-brace matching
or a manual loop. A block-level `re.search` for `type = "X"` plus `name = "Y"` is faster
and avoids the false positives that drove the "duplicated tech" misread.

**Working parser pattern** (verified on DMR v3.5.3 locale audit):

```python
import re

def find_name_in_block(block, gprefix):
    nm = re.search(r'\bname\s*=\s*((?:"[^"]+"|gprefix\s*\.\.\s*"[^"]*"))', block)
    if not nm: return None
    raw = nm.group(1)
    if raw.startswith('"'):
        return raw.strip('"')
    return gprefix + re.match(r'gprefix\s*\.\.\s*"([^"]*)"', raw).group(1) if gprefix else None

# Per-file: extract gprefix once, then for each { ... } block check both type and name.
# Skip names ending in "-" (truncated gprefix concat) and len < len(prefix) + 2.
```

**Locale sections often missing in older locales**: `[item-subgroup-name]`,
`[recipe-category-name]`. Factorio silently falls back to the raw key name when these
sections are absent. If the audit shows `dmrsa-replication-resources` or
`dmrsa-replication-vulcanus` (recipe-category) as "missing", the fix is to ADD the
section header + entries — don't try to rename or repurpose an existing section.

**Locale parity verification** — always run this after editing both locales to catch
asymmetric keys (e.g. you added `dmrsa-foo` to EN but forgot ES):

```python
import re

def parse_locale(path):
    sections, current = {}, None
    for line in open(path, encoding='utf-8-sig').read().split('\n'):
        line = line.rstrip('\r')                     # CRLF files: strip the CR or every key gains one
        s = line.strip()
        if s.startswith('#') or s.startswith(';'):   # BOTH comment chars — a commented-out key is not
            continue                                 # shipped, and would fake a one-sided entry
        m = re.match(r'^([\w-]+)$', s)
        if m: current = m.group(1); sections[current] = {}
        elif current and '=' in line:
            k, _, v = line.partition('=')
            sections[current][k.strip()] = v.strip()
    return sections

en = parse_locale('locale/en/x.cfg')
es = parse_locale('locale/es-ES/x.cfg')
for sec in ['item-name', 'technology-name', 'mod-setting-description', ...]:
    diff = set(en.get(sec, {})).symmetric_difference(set(es.get(sec, {})))
    if diff: print(f"{sec}: {len(diff)} asymmetric keys: {sorted(diff)[:5]}")
    # untranslated: same non-trivial value in both locales (allow proper nouns)
    same = [k for k in set(en.get(sec, {})) & set(es.get(sec, {}))
            if en[sec][k] == es[sec][k] and len(en[sec][k]) > 6]
    if same: print(f"{sec}: {len(same)} likely untranslated: {sorted(same)[:5]}")
```

If a section reports asymmetric keys, the keys present in only one locale are the bugs
to fix. Both locales must have IDENTICAL key sets for proper i18n.

## Changelog prepend corruption (PITFALL — patch tool gotcha)

When you prepend a new version block to `changelog.txt` using a `patch` whose
`old_string` is the FIRST existing entry (e.g. `"Version: 3.5.1\nDate: ..."`), and your
`new_string` is the new block PLUS the same first existing entry, the result is a
**duplicated header** for the previous version. Concretely:

- Your `new_string` says "Version: 3.5.3 ... block ... Version: 3.5.2"
- But the file's existing structure already has "Version: 3.5.2" as its first entry,
  with its own "Bugfixes:" header two lines below
- After your patch, the file has:
  ```
  Version: 3.5.3
    [your block]
  Version: 3.5.2     ← from your new_string
    Bugfixes:         ← from your new_string
    - ...
    Bugfixes:         ← from the original file, now orphaned
    - ...
  ```
- Worse: subsequent `patch` calls that try to anchor on "  Bugfixes:" near the top
  will succeed by matching the WRONG one, and indent it further each time you try to
  fix it.

**Real example from DMR v3.5.3 release**: I patched the changelog with
`new_string = "Version: 3.5.3 [block]\n\n[separator]\nVersion: 3.5.2\nDate: 2026-08-09"`,
which **included the literal "Bugfixes:" header from 3.5.2's first line**. The file
ended up with two "Bugfixes:" lines back-to-back, and 3 follow-up `patch` calls kept
adding indentation to the wrong one because the search anchors matched differently
each time. Took a Python rebuild script to fix.

**Rule for changelog prepends**:
1. **`new_string` must END at the version DATE line**, not include the version's
   "Bugfixes:" / "Features:" / "Changes:" headers. The patch tool replaces from the
   anchor forward; you want it to replace ONLY the boundary, not duplicate the body.
2. **Verify after each patch** with `head -35 changelog.txt` — count how many
   `  Bugfixes:` headers appear near the top.
3. **If you corrupt it**, don't try to fix with more patches. Read the full file,
   write a Python rebuild script that takes the corrupted file + the canonical
   version block as input, and reconstructs clean. The script is deterministic and
   faster than chained patches.

A working changelog prepend pattern (use this instead of multi-line `patch`):
```python
from pathlib import Path
p = Path('changelog.txt')
existing = p.read_text()
new_block = '''---------------------------------------------------------------------------------------------------
Version: 3.5.3
Date: 2026-08-09
  Bugfixes:
    - [your fix description]
  Changes:
    - [your change description]

'''
# Insert at the very top — DO NOT include any existing content in new_block
p.write_text(new_block + existing)
```

## Locale editing workflow (PITFALL — patch tool gotcha)

The `patch` tool matches on literal text including whitespace. When you patch a large
block in a `.cfg` locale file and then patch AGAIN the same region with a NEW block,
the second patch fails with "Could not find a match" because the on-disk content has
shifted from what you read earlier.

**Concrete example from DMR v3.5.3**: I patched EN's `[entity-description]` (10 lines)
and then tried to patch ES's `[item-description]` (15 lines) using the same multi-line
template. The EN patch worked. The ES patch failed because by then the file had been
read with a partial offset and the exact byte sequence didn't match. I had to break
the ES patch into 5 single-line patches (one per replicator tier).

**Rules for locale file edits with `patch`**:
1. **Prefer single-line patches** for `.cfg` locale files when doing more than one edit.
   Anchor on a known-stable line above and below.
2. **Read the file fresh before each multi-line patch** if you must do them — partial
   reads can leave you with stale content expectations.
3. **Don't try to copy a patch that worked on locale A to locale B** — A and B drift
   fast and you waste cycles on match failures.
4. **For section header additions** (e.g. adding `[recipe-category-name]` to a locale
   that lacks it), use `old_string = "[existing-section-end-marker]" + new_string =
   "[existing-section-end-marker]\n\n[new-section]"`. This anchors reliably.

## patch tool multi-line match failure (PITFALL — v3.5.3 changelog + v3.5.6 ES locale)

When the `patch` tool reports "Could not find a match" against a block of text
that LOOKS identical to what you wrote, the cause is usually one of:

1. **Trailing whitespace / newline differences** — your `old_string` has `\n`
   but the file uses `\r\n`, or vice versa. The patch tool's fuzzy matcher does
   not normalize this.
2. **Invisible characters** — Factorio locale files (especially es-ES) have
   non-ASCII punctuation that your terminal may render as identical to ASCII
   but the tool treats as different. Especially common with curly quotes,
   em-dashes, and accented characters.
3. **Indentation drift** — earlier patches in the same session have shifted
   line numbers and added/removed blank lines, so your anchor block is no
   longer byte-identical even though it visually matches.
4. **Read freshness** — the `patch` tool was given a `read_file` view with a
   partial offset that doesn't match what's now on disk.

### The rule

When a multi-line patch fails 2+ times with "Could not find a match", STOP
trying the same big block. Break the patch into smaller pieces:

- Anchor on a single unique line (e.g. one `dmrsa-X=Y` entry)
- Apply one-line replacements
- Re-read the file after each successful patch to update your mental model

This pattern bit twice in this session:

- **v3.5.3 changelog**: a 20-line patch failed repeatedly because indentation
  drifted each retry. Took a Python rebuild script (`write_file` to `/tmp`,
  `terminal` to execute) to fix deterministically.
- **v3.5.6 ES locale item-description**: a 30-line patch failed 3 times because
  the patch matcher didn't recognize the visible content. Breaking into 6
  single-line patches each anchoring on a unique `dmrsa-replicator-N=` line
  succeeded immediately.

### Generalizes beyond Factorio

Any time you patch a non-trivial locale file (long lines, non-ASCII, mixed
CRLF), prefer N small patches over 1 big patch. The cost of the small-patches
approach is bounded; the cost of a stuck big patch is unbounded retry loops
that all hit the same wall. If the file is so large that even small patches
feel brittle, fall back to a Python rebuild script in `/tmp` — it's faster
and deterministic.

### Diagnostic signal

A failed `patch` followed by "Did you mean one of these sections:" listing
the EXACT text you tried to match is a near-certain sign of one of the four
causes above. Don't retry — switch strategies.

## Zip release procedure

```
# Source folder: dark-matter-replicators-reborn_3/  (note the _3 suffix — your working folder)
# Zip root:      dark-matter-replicators-reborn/    (NO _3 — matches mod name in info.json)
# Zip filename:  dark-matter-replicators-reborn_X.Y.Z.zip
```

**Convention seen in this repo's previous releases (3.5.0, 3.5.1)**: zip uses the mod
name from `info.json` as root, not the working folder name. The `_3` suffix on the
working folder is private to the maintainer.

Build script (use `write_file` + `terminal` to avoid the gateway-restart guard that
flags `hermes` references in heredoc; the `zip` CLI is often NOT installed in the
sandbox — the Python zipfile approach is the primary path, not a fallback):

```python
import zipfile, os
from pathlib import Path
source = Path('/path/to/working_folder')
root = 'mod-name-from-info-json'  # NO _3 suffix
out = '/path/to/release.zip'
# Internal dev docs must NOT ship to the mod portal:
exclude_dirs = {'specs', 'research', '__pycache__'}
exclude_files = {'.DS_Store', 'Thumbs.db', 'ROADMAP.md', 'FAQ.md'}
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
    for r, d, fs in os.walk(source):
        d[:] = [x for x in d if x not in exclude_dirs]
        for fn in fs:
            if fn in exclude_files: continue
            full = Path(r) / fn
            arc = f"{root}/{full.relative_to(source).as_posix()}"
            zf.write(full, arc)
```

**Post-build verification (always do this — it caught a real leak in v3.7.0)**:
- Open the zip and confirm both fixes are in the file (use string containment checks)
- Confirm `info.json` has the new version
- Confirm `changelog.txt` has the new entry at the top
- Confirm the zip root folder matches prior releases (avoids mod-portal upload surprises)
- **Confirm NO internal docs leaked**: `ROADMAP.md`, `FAQ.md`, `specs/`, `research/`
  must be absent from the zip. A first v3.7.0 build passed all fix checks but leaked
  FAQ.md + ROADMAP.md because the exclude filter only covered directories, not files.
  Check explicitly: `leaked = [n for n in names if 'ROADMAP' in n or '/specs' in n or '/research' in n or '/FAQ.md' in n]`
- Run `scripts/check-no-private-data.py` on the BUILT ZIP too, not just the source
  tree — the user mandate is "verifica que no se suba nada privado" and the zip is
  what actually gets uploaded.

## Published-version parity check before ANY release build (v4.2.0, 2026-08-23)

Before building the RELEASE zip, diff your exclude list against the zip that is
ACTUALLY PUBLISHED on the portal (`mods.factorio.com/api/mods/<name>` → download
the last release and inspect it), not against your own last build. The published
4.0.0 shipped WITHOUT `ROADMAP.md`/`FAQ.md`, but the in-dev builds had quietly
regained them (the exclude filter lived only in one ad-hoc build script). Caught
in the parity check right before uploading — otherwise internal docs would have
gone public.

```python
import zipfile, json, urllib.request
rels = json.load(urllib.request.urlopen(f"https://mods.factorio.com/api/mods/{NAME}"))["releases"]
print("portal latest:", rels[-1]["version"])
with zipfile.ZipFile(last_published_zip) as z:
    pub_names = set(z.namelist())
with zipfile.ZipFile(candidate_zip) as z:
    cand_names = set(z.namelist())
print("only in candidate:", sorted(n.split('/',1)[1] for n in cand_names - pub_names))
```

Rule: `EXCLUDE_FILES = {'.gitignore', 'ROADMAP.md', 'FAQ.md'}` + the standard
exclude_dirs (`research/ specs/ dmr-tests/`) live in ONE canonical build recipe;
every rebuild reuses it. After building, verify: file count, no ROADMAP/FAQ/specs/
research leaks, fixes present via string containment, privacy scan CLEAN.

## Mod portal upload — API v2 two-step (init_upload + PUT) and credentials

Portal upload needs a SEPARATE credential from GitHub: `FACTORIO_PORTAL_USER`
(username) + `FACTORIO_PORTAL_TOKEN` (generated at mods.factorio.com → profile →
Upload token). They are NOT in `.env` by default — ask the user or have them add
the vars; do not guess. Two-step flow:

1. `POST https://mods.factorio.com/api/v2/mods/releases/init_upload` with
   basic auth + `--form "file=@<zip>"` → returns JSON with an `upload_url`.
2. `PUT --upload-file <zip> <upload_url>` to actually transfer.
3. Verify with `GET /api/mods/<name>` → latest version == uploaded.

If creds are missing, STOP after preparing everything else (zip verified,
privacy CLEAN, changelog accumulated) and hand the user the exact zip path for a
manual upload — don't block the release on credentials you can't obtain.

**Publication lag (observed, don't fight it)**: `finish_upload` returning `{"success":true}` does
NOT mean the release is public. The public list can keep serving the previous `releases[-1]` for
minutes afterwards. Two rules follow:

- Re-running the upload "to check" comes back HTTP 400
  `{"error":"InvalidModRelease","message":"Release with that version already exists."}` — that
  error is CONFIRMATION the release was recorded server-side, not a failure. Do not retry, and never
  bump the version to get around it: a retry cannot succeed, and a bump publishes a phantom version
  that the real fix then collides with.
- "Published" means the API lists it: poll `GET /api/mods/<name>` until `releases[-1].version` equals
  the new version (also checks `/api/mods/<name>/full`, same store). Until then treat it as
  accepted-but-unpublished: no announcement, no "publicado" claim to the user — they test what the
  portal serves, and the release-identity rule above says the portal is the source of truth.

The one-shot wrapper actually used for releases is
`python3 ~/.hermes/scripts/dmr-portal-upload.py <zip> <mod-name>`; it prints both HTTP steps, so the
response body (including any error JSON) is always visible — read it instead of assuming success
from exit code 0.

## Accumulated changelog header for multi-version portal jumps

When publishing over several unreleased local versions (portal 4.0.0 → shipping
4.2.0 which contains unreleased 4.1.0), prepend an ACCUMULATED headline block to
the top changelog entry: NOTE paragraph listing what's new since the last PORTAL
release (pointing to the individual entries below), then keep the existing
per-version entries untouched. Portal shows only the top entry.

## Version numbering policy (v3.6.0 decision — user-confirmed)

When many patch releases accumulate locally WITHOUT being published to the mod
portal, the next portal release should be a **minor version bump**, not another
patch. Concrete case (2026-08-09): local series reached 3.5.25 while the last
PUBLISHED version was 3.5.19; user said "creo que debemos colocar 3.6.0 por
tantas modificaciones" → released 3.6.0.

Rules:
1. **Minor bump when accumulated unpublished changes are substantial** — the
   v3.6.0 release accumulated 3.5.20→3.5.25 (science tiers, MACHINE_EFFICIENCY
   names, category subgroups, placeable locale fix, research difficulty, pack
   order, icon HD, idle animation, lab validation). That's a feature set, so a
   minor bump signals the scope correctly on the portal.
2. **Keep `factorio_version` at the lowest supported version unless the user
   says otherwise** (user explicitly: "sin subir la version de factorio a 2.1").
   The mod already has dual-compat 2.0/2.1 code (`dmrsa_is_v21()`), so keeping
   `"2.0"` in info.json preserves backward compatibility while 2.1 still works.
   Do NOT auto-bump factorio_version just because the game's latest stable is
   newer — that's a user decision with compat tradeoffs.
3. **Write ONE accumulated changelog entry for the portal release** — since
   portal users never saw 3.5.20–3.5.25, the 3.6.0 entry must summarize
   everything since the last PUBLISHED version, organized as Features /
   Changes / Bugfixes, with a Note explaining factorio_version stayed 2.0.
   Keep all individual version entries below it in changelog.txt (they're the
   detail trail for the repo; the portal shows only the top entry).
4. Flag the **savegame caveat** in the release notes: players upgrading from a
   much older version will see tier-progression changes (chemical before
   planets, science-pack tiers) and researched techs may appear "un-researched"
   in the tech tree. Accepted risk for progression reworks.

Check before proposing a version bump: what is the last version actually on the
mod portal (`mods.factorio.com/api/mods/<name>` → `latest_release.version`),
not what's in the local changelog. The portal version is the source of truth
for what the accumulated entry must cover.

## Settings order collisions (PITFALL)

`order = "X-Y-Z"` in `data:extend` settings is a string. Factorio sorts lexicographically
per segment. Two settings with the same `order` display in arbitrary order and the user
sees them jumbled.

Real example in DMR v3.5.2 audit: `replstats-speed-base` (order `1-1-3`) and
`replication-in-space` (also `1-1-3`) collided. `replication-in-space` was a conditional
extension (`if mods["space-age"]`) that picked a `1-1-3` order by accident — landed in
the tenemut cluster, far from its logical "replication" home. Fix: move to a unique
order like `1-6-1`.

**Rule**: when adding a new conditional setting, audit the existing `order` namespace
first. Settings grouped under `1-*` are the tenemut/resources cluster; `2-*` is research;
`3-*` is more research; `4-*` is replication penalties; `5-*` is tech distribution;
`9-*` is the meta/log tail.

## Log level wiring (PITFALL)

`helpers._should_log(level)` semantics: `msg_priority <= current_priority`. So `warn`
(2) emits error(1) and warn(2) only — info(3) and debug(4) are dropped. **Sanity-check
this is what your call sites expect.**

If your codebase has a closing-summary `helpers.log("summary", "info")` at the end of a
critical phase, the default `warn` setting means the user never sees confirmation that
the phase ran. Either bump the level to `warn` for the summary, or document this in the
`dmrsa-log-level` description so users with `info`/`debug` know to flip the switch for
visibility.

## LocalisedString `"?"` parameter pitfall (CRITICAL — Factorio 2.x)

The `"?"` key in a Factorio LocalisedString is **the KEY**, not a positional parameter.
Per `lua-api.factorio.com/latest/concepts/LocalisedString.html`:

> "if the key is a question mark (`?`), then the first valid parameter will be used.
> A parameter can be invalid if its name doesn't match any string template. If no
> parameters are valid, the last one is returned."

So the legacy 0.x syntax — passed down from the original Dark Matter Replicators fork —
is broken in Factorio 2.x:

```lua
-- BROKEN in Factorio 2.x — "?" counts as positional parameter 0
localised_name = {
    "technology-name.dmrsa-repl-tech",   -- KEY = tech template (uses __1__)
    {                                   -- PARAMETERS (only one slot)
        "?",                            -- positional #1 → renders as "parameter-0"
        { "item-name." .. name },
        { "entity-name." .. name },
        { "fluid-name." .. name },
        name                            -- positional #5 → renders as "parameter-4"
    }
}
```

User-visible symptom: every dynamic recipe and individual technology shows literal
strings like `"Replication: parameter-0"`, `"parameter-1"`, etc. — unjugable because
the player can't tell what unlocks what. Easy to miss in code review because the
structure LOOKS plausible. Only surfaces when the user actually plays the game.

### Fix: precompute the localization prefix in Lua, not in the LocalisedString

Inspect the prototype type (`target.type` in the iteration) and build the right
prefix — `item-name`, `entity-name`, or `fluid-name` — before constructing the
LocalisedString. Then use a single-parameter array:

```lua
local loc_prefix
if target.type == "fluid" then
    loc_prefix = "fluid-name"
elseif target.type == "item" or target.type == "ammo" or target.type == "armor"
    or target.type == "gun" or target.type == "capsule" or target.type == "tool"
    or target.type == "module" or target.type == "item-with-entity-data"
    or target.type == "item-with-tags" or target.type == "spidertron-remote"
    or target.type == "space-platform-starter" then
    loc_prefix = "item-name"
else
    loc_prefix = "entity-name"
end

local repl_recipe = {
    localised_name = {
        "recipe-name.dmrsa-replication-recipe",
        { loc_prefix .. "." .. name }   -- single positional parameter, resolves correctly
    },
    ...
}
```

### Detection rule for audits

`grep -nE '"\\?"' prototypes/**/*.lua` followed by reading the surrounding
`localised_name = { ... }` block. If `"?"` appears INSIDE the parameters array
(not as the key), it's the bug. Apply the same fix pattern uniformly — there are
typically MULTIPLE call sites (recipe, individual tech name, individual tech
description, planetary grouped tech name, etc.) that all need patching.

## Numeric parameters in prototype localised strings are REJECTED at load (v4.2.0 gate test, 2026-08-23)

**Trigger**: startup crash on first load of DMR 4.2.0 (Factorio 2.1.14):

```
Failed to load mods: Error while loading technology prototype "dmrsa-replication-materials-1" (technology):
Value must be a string in property tree at ROOT.technology.dmrsa-replication-materials-1.localised_name[1]
```

**Root cause**: `localised_name = { "technology-name.dmrsa-materials-tech", def.tier }` — the second
parameter is a Lua NUMBER. Factorio 2.x prototype stage validates localised strings with STRING-only
parameters; numbers are allowed only at RUNTIME (`game.translate`), not in the data stage. The error is
reported on the parameters slot of the localised string.

**Why it was hard to catch**: the localised string LOOKS valid per the wiki (runtime LocalisedStrings
accept strings/numbers/booleans) and the code had never been load-tested — the ONLY new localised-string
construct in 4.2.0 was this one (4.0/4.1 had zero numbers in any localised string and loaded fine). The
game had never loaded the 4.2.0 data stage before the gate test.

**Fix**: `tostring()` the numeric parameter:
```lua
localised_name = { "technology-name.dmrsa-materials-tech", tostring(def.tier) },
```

**Audit rule**: before release, scan every `localised_name`/`localised_description` block for bare
numbers in the parameter array:
```python
import re
for m in re.finditer(r'localised_(?:name|description)\s*=\s*\{([^}]*)\}', src):
    body = m.group(1)
    if re.search(r'(?<!["\w.])-?\d+(?:\.\d+)?(?!["\w])', body):
        print("NUMERIC PARAM:", m.group(0))
```
All parameters must be strings (or nested `{ "key" }` tables — those ARE allowed; only raw numbers/booleans
break the load). Same domain as the `"?"` pitfall: LocalisedString structure gets validated at load in ways
the runtime API docs don't warn about.

**Reusable check**: `scripts/scan_localised_numeric_params.py <mod-dir>` under this skill walks all `.lua`
files and flags any localised_name/localised_description array containing a bare numeric parameter.
Run it as part of the pre-release gate alongside the locale parity audit — before building the zip, not
after the user's gate test.

## Prototype defined AFTER its consumer → item_exists false → silent fallback substitution (v4.2.0 gate-test dump, 2026-08-23)

**Symptom**: user reports "Raw Materials (Tier 1) researches with Nanophase Conduit" — the pack is
WRONG for the tier. Dump confirmed: `replication-materials-1` had `unit.ingredients = [["dmrsa-matter-conduit",1]]`.

**Root cause**: load-order bug, not a design bug. The `dmrsa-tenemut` TOOL prototype was defined in
`prototypes/raw-resources.lua`, which `data.lua` required AFTER `prototypes/technologies/technologies.lua`.
So when `make_research_unit(30, {"dmrsa-tenemut"}, 30)` ran, `data.raw.tool["dmrsa-tenemut"]` did not
exist yet → `helpers.item_exists` returned false → the (v4.2-hardened) fallback tried
`matter-conduit` (which WAS loaded) → tier-1 pack silently became Nanophase Conduit. The un-hardened
4.1.0 fallback produced the OTHER symptom of the same bug: an EMPTY ingredients list ("no cost" tech).

**Rules**:
1. `helpers.item_exists`/`fluid_exists` are load-order-sensitive: they only see prototypes ALREADY
   extended. Any file that calls them at data stage must run AFTER the prototypes it checks.
2. When a bug makes a pack/ingredient silently WRONG, enumerate the same class in the dump — here ONLY
   materials-1 mismatched; mirror techs (generated in data-final-fixes) were correct.
3. Item prototypes belong in the items file that loads first; keep resource/entity/particle
   definitions (which reference later machinery) in their own late file. DMR pattern: everything in
   `items/dark-matter.lua` is visible to `technologies.lua`; `raw-resources.lua` only carries
   autoplace-control/resource/particle.

## Replicating tree-depth over a modded dump in Python: MEMOIZE or it times out (2026-08-23)

When replicating `MirrorGenerator.get_tech_tree_depth` against a 138-mod
`data-raw-dump.json` (127MB, ~2,000+ techs with long SA/planetaris/bob chains),
a naive recursive depth function WITHOUT memoization timed out at 300 s. The
Lua original is memoized + cycle-safe (`depth_cache` + `depth_in_progress` →
return 1 on cycle). Port it EXACTLY: dict cache + visiting-set, cycle → 1.
With memo the whole graph resolves in ~2.4 s; the naive version recomputes
overlapping subgraphs exponentially.

Follow-on insight from the same pass: depth values in a big modded tree are
REAL tree depths, not progression — chemical-science-pack=22, promethium=80.
Never treat raw depth as the desired tier; see the depth-clamp correction in
`references/dmr-v4-mirror-tree.md`.

## Machine efficiency / recipe-category coverage gap (v3.5.7 lesson)

DMR's `cost-solver.lua` had a `MACHINE_EFFICIENCY` table mapping `recipe-category` name
to efficiency multiplier. The original fork covered vanilla categories. **After Space
Age was released, 8 new categories were added to the game but never to the table.**

Categories that were missing when DMR 3.5.6 shipped:

```
farming                          -- Agricultural tower
brewing                          -- Biochamber
metallurgic                      -- Foundry
electromagnetic                  -- Electromagnetic plant
cryogenic                        -- Cryogenic plant
organic-or-egg                   -- Agricultural tower egg
crushing                         -- Crusher
crafting-with-fluid-or-recycling -- Mixed fluid/recycling crafting
```

When a recipe's category isn't in the table, the cost-solver falls through to a
neutral 1.0x multiplier (no cost adjustment). So items crafted in Space Age machines
had replication costs that ignored the machine complexity. The user noticed this
implicitly: "todo bien por aca con el dmr con space age hasta los momentos" — they
didn't hit the gap because they were also playing vanilla-tier stuff. If they had
pushed harder on SA endgame, they would have hit balance issues.

**Detection rule** (when auditing any category-keyed lookup table in your mod):

```bash
# List all recipe-category types defined by Factorio 2.x + common mods
grep -rE 'type\s*=\s*"recipe-category"' /path/to/factorio/data/core/ \
  /path/to/space-age/ 2>/dev/null | head -30
```

**Cross-reference against your lookup table**:

```python
defined = {"crafting", "advanced-crafting", "smelting", "chemistry",
           "oil-processing", "centrifuging", "rocket-building",
           "crafting-with-fluid", "recycling"}  # vanilla baseline
sa = {"farming", "brewing", "metallurgic", "electromagnetic", "cryogenic",
      "organic-or-egg", "crushing", "crafting-with-fluid-or-recycling"}
gap = sa - defined  # any category in SA but not in your table
```

**The rule**: when Factorio releases a new expansion that adds recipe categories,
your lookup tables need a coverage pass. Same pattern applies to item-subgroups,
equipment categories, fluid boxes, etc. — anywhere you keyed off vanilla data.

### "Fix all matching patterns in one pass" pitfall

When fixing a recurring bug pattern across multiple call sites, do a single pass
with `grep` first to enumerate ALL occurrences, then patch them all before
rebuilding the zip. Don't patch one, rebuild, discover the second, patch, rebuild,
discover the third — each round trip costs a verification cycle. Real DMR v3.5.4
example: I fixed the recipe path (2 `localised_name` blocks) and rebuilt the zip.
Verification caught `"?"` still in the planetary grouped tech path (1 more block).
Three rounds when one would have sufficed. The pattern: **enumerate → fix all →
verify once**.

## User-play testing as the ultimate audit layer

Static analysis (greps, audit scripts, branch coverage) will NOT catch the
LocalisedString `"?"` bug because the code is syntactically valid Lua and the
test fixtures don't render the LocalisedString. The bug surfaces only when a
human sees `"parameter-N"` in the game UI. **Treat user observations of "weird
text in-game" as first-class bug signals, not as cosmetic complaints.** When a
user reports literal text that looks like code (e.g. `parameter-N`, raw keys,
template variables), go to the prototype definitions, find every `localised_name`
and `localised_description`, and audit the LocalisedString structure field by
field.

## Subgroup categorization pitfall (v3.5.5)

`subgroup = "X"` on an `item` prototype determines which inventory tab the item
appears in. **Items defined in the mod MUST use mod-defined subgroups, not
vanilla subgroups, or they leak into the wrong tab.**

Real DMR v3.5.5 bug: `prototypes/entities/replicators.lua:147` had
`subgroup = "production-machine"` for tier 1-5 replicator items. Result: the
replicators appeared in vanilla "Production" tab alongside vanilla assembling
machines, completely separated from the planetary replicators and lab (which
correctly used `dmrsa-replicators`). User noticed "the replicators should be
inside the Replication category" — visual smoke test caught what static audit
didn't, because the bug was an *absence of connection*, not a malformed string.

**Detection rule** for audits:

```bash
# In prototype files: grep all subgroup assignments and compare against the
# mod's defined subgroups (declared with type = "item-subgroup")
grep -nE 'subgroup\s*=\s*"[^"]*"' prototypes/**/*.lua
grep -nE 'type\s*=\s*"item-subgroup"' prototypes/**/*.lua | head
```

If a `subgroup = "..."` value on an item/recipe/technology prototype is NOT in
the mod's defined-subgroup list, it's a leak into vanilla categories (or into a
non-existent subgroup that renders as a raw key — see the locale audit
methodology above).

**Why this is hard to catch in code review**: the value `"production-machine"`
is a valid vanilla subgroup name, so the code compiles and runs without errors.
Factorio silently accepts it. The bug only surfaces when a player opens the
inventory and looks at where items landed.

## Locale-defined subgroup / category pitfall (v3.5.5)

When you add a new prototype that references a mod-defined subgroup (e.g.
`subgroup = gprefix .. "replication-tier-1"`), the corresponding locale entry
is **mandatory** or Factorio displays the raw key. This is the same root cause
as the "missing tier tech names" bug from v3.5.3 audit, but it applies to
subgroups and recipe categories too.

Real DMR v3.5.5 audit finding: 5 dynamic-recipe subgroups
(`dmrsa-replication-tier-1` through `-5`) were defined in `dark-matter.lua:33-42`
but had NO entries in `[item-subgroup-name]` of either locale. The crafting menu
displayed raw `dmrsa-replication-tier-N` for every dynamically-generated
replication recipe.

**Cross-reference matrix** (use this when adding a new prototype that points to
a mod-defined subgroup or recipe category):

| Prototype defines | Locale MUST contain |
|---|---|
| `type = "item-subgroup", name = gprefix .. "X"` | `[item-subgroup-name]`<br>`gprefix .. "X" = <displayed name>` |
| `type = "recipe-category", name = gprefix .. "X"` | `[recipe-category-name]`<br>`gprefix .. "X" = <displayed name>` |
| `type = "item-group", name = gprefix .. "X"` | `[item-group-name]`<br>`gprefix .. "X" = <displayed name>` |

The locale audit methodology above (parse + cross-reference) catches these
automatically. **Hidden prototypes count too**: a `recipe`/`technology` marked `hidden` still renders
its name in the machine's progress tooltip and the crafting queue, so `recipe-name.<key>` /
`technology-name.<key>` is mandatory in BOTH locales — "nobody can see it" is the wrong assumption,
and the player gets a literal `Unknown key: recipe-name.<key>` in-game. If you skipped that audit because the mod "looked fine in static
review", you missed these.

## "Enumerate → fix all → verify once" generalizes beyond `"?"`

The rule first stated for the `"?"` LocalisedString pitfall (fix all call
sites in one pass, not one-at-a-time) generalizes to **any recurring bug
pattern found by audit**. DMR v3.5.5 had the same shape: user noticed
"replicators are in the wrong category" → I grepped, found 1 leak, patched,
rebuilt, verification found 5 missing locale entries for dynamic subgroups
(different bug class, same domain), patched, rebuilt. Two rounds when one
audit-then-bulk-fix would have caught both.

**Rule**: after a user-visible observation, do the FULL audit first (grep all
related code paths, cross-reference all related locale sections, enumerate all
violations), THEN patch in a single batch, THEN verify once. Don't iterative-
patch-and-rebuild across multiple bug classes.

## [item-description] vs [entity-description] duplication pitfall (v3.5.6)

When a prototype has BOTH a `type = "item"` AND an entity form (replicators,
assembling machines, labs, etc.), Factorio resolves the description differently
depending on context:

- **Item in cursor / inventory tooltip** → reads `[item-description]`
- **Item placed on ground (entity hover)** → reads `[entity-description]`
- **There is NO automatic fallback** between the two sections

### What went wrong in v3.5.3

I rewrote the 5 tier replicator descriptions in `[entity-description]` but
populated `[item-description]` with placeholder text:

```
dmrsa-replicator-1=Mirrors [entity-description] dmrsa-replicator-1.
```

I assumed Factorio would fall back to `[entity-description]` if `[item-description]`
was missing or unhelpful. It doesn't. Players saw the literal placeholder text
when hovering the item in their inventory.

### The rule

When a prototype has both forms, **duplicate the description in BOTH sections**.
Do NOT use cross-reference placeholders. The cost of duplication is far less
than the cost of the bug.

### Detection rule for audits

When you rewrite any description in `[entity-description]`, immediately:

1. Grep the same `dmrsa-X` key in `[item-description]`
2. If the item has a corresponding entity form (`type = "assembling-machine"`,
   `type = "lab"`, `type = "furnace"`, etc.), the descriptions must match
3. Replace any cross-reference placeholder or short stub with the full text

Quick grep pattern:

```bash
# Find items that have both item and entity forms (potential placeholders to fix)
grep -A1 '^\[entity-description\]' locale/en/...cfg | grep 'dmrsa-' | \
  while read key; do
    grep -q "^${key%=*}=Mirrors" locale/en/...cfg && echo "FOUND PLACEHOLDER: $key"
  done
```

### Why this isn't obvious

Factorio's data model treats the item and the entity as separate prototypes that
share a name. The `place_result` field on the item points to the entity, but the
localization layer has no such bridge — each section is queried independently
based on the rendering context.

## Exact-match vs substring for variant-with-suffix names (v3.5.8 lesson)

When matching item/recipe names to determine category routing, **Space Age
introduces variant naming with suffixes**: `fluoroketone-cold`, `fluoroketone-hot`,
`ice`, `melting-ice`, `stone-brick`, `wooden-board`, etc. The "base" name often
doesn't exist as an actual item — only the variants do.

**Anti-pattern (the bug I shipped in v3.5.6 and only caught in v3.5.8)**:

```lua
elseif name == "ice" or string.find(name, "lithium") or name == "fluoroketone" or ...
    -- `name == "fluoroketone"` is EXACT match — never true because the actual
    -- internal names are `fluoroketone-cold` and `fluoroketone-hot`.
    -- Result: both fluoroketone variants routed to generic tier 3 chemical
    -- instead of aquilo (cryogenic). User saw them at the wrong tier.
```

**Rule**: when the base name plausibly has variants (heat states, processing
states, material forms), use `string.find(name, "X")` not `name == "X"`. The
fact that the comparison `name == "X"` is syntactically narrower makes it
silently break when a variant arrives.

**Detection rule for audits**:

```bash
# Find exact-match checks on potentially-variant names
grep -nE 'name\s*==\s*"[a-z][a-z\-_]*"' prototypes/**/*.lua | \
  grep -v "^\s*--" | \
  while read line; do
    base=$(echo "$line" | grep -oE '"[^"]*"' | tr -d '"')
    # If the base word is in any variant like X-cold, X-hot, X-molten, etc.,
    # flag it.
    grep -rE "name\s*=\s*\"${base}-(cold|hot|molten|raw|refined|shaped)\"" \
      prototypes/ data/ 2>/dev/null && echo "VARIANT-NAME BUG: $line"
  done
```

**Known SA variants to watch for** (this list grows with each Factorio version,
but these were the ones in v3.5.8):

- `fluoroketone-cold`, `fluoroketone-hot`
- `ice`, `melting-ice`
- `wood`, `wooden-board` (and other Bob's/SA wood variants)
- `iron-ore`, `copper-ore`, `coal`, `stone` (mining variants)

When the audit finds a variant-name bug, the fix is mechanical: change
`name == "X"` to `string.find(name, "X")` (or one of the more specific pattern
variants depending on what you're matching).

## BASE_RESOURCE_COSTS and similar tier-table coverage gaps (v3.5.9)

The cost-solver pattern `BASE_RESOURCE_COSTS[name] = { cost, time, tier }` is a
manual lookup table that bypasses the recursive cost calculation for known
resources. **If a resource is missing from the table, the recursive path runs
and returns the worst-case tier-1 fallback** because mined resources have
no crafting recipe to derive cost from.

Real DMR v3.5.9 audit: `promethium-asteroid-chunk` (Space Age asteroid chunk
mined from `promethium-asteroid`, requires space platform to mine) was
**missing** from `BASE_RESOURCE_COSTS`. Result:

1. `solve_cost("promethium-asteroid-chunk")` returns tier 1 fallback
2. The recipe `dmrsa-repl-promethium-asteroid-chunk` is created at tier 1
3. User saw promethium asteroid chunk replicable from the simple replicator
4. Item unlocked without needing space science — broken gate

**Detection rule**: every mod-defined or vanilla-mod resource that the user
can mine should be in `BASE_RESOURCE_COSTS`. Use the official Factorio data
dump to enumerate them:

```bash
# Get all resource names defined by Factorio 2.x + SA
grep -rE 'type\s*=\s*"resource"' /path/to/SA-prototypes/ \
  /path/to/base-prototypes/ 2>/dev/null | head
```

**Cross-reference against your table**:

```python
defined_in_cost_solver = {'iron-ore', 'copper-ore', 'coal', 'stone', ...}
all_known_resources = {'iron-ore', 'copper-ore', 'coal', 'stone',
                      'uranium-ore', 'calcite', 'scrap', 'holmium-ore',
                      'tungsten-ore', 'jellynut', 'yumako',
                      'spoiled-organic-substrate',
                      'metallic-asteroid-chunk', 'carbonaceous-asteroid-chunk',
                      'oxide-asteroid-chunk', 'promethium-asteroid-chunk',
                      'promethium-ore'}  # everything user can mine
missing = all_known_resources - defined_in_cost_solver
```

If `missing` is non-empty, add the entries with appropriate tier. **Tier should
reflect when the resource becomes available in vanilla/SA progression**:
`iron-ore` → tier 1, `uranium-ore` → tier 3, asteroid chunks → tier 4,
promethium → tier 5.

## FLUID_TIER_OVERRIDES for fluids without crafting recipes (v3.5.9)

`BASE_RESOURCE_COSTS` handles resources (mined only, no recipe). Fluids that
have a recipe get tiered correctly via the recursive path. But **fluids that
are passive outputs of buildings** (no crafting recipe) fall through the same
way resources do — to a tier-1 fallback.

Real DMR v3.5.9: `fusion-plasma` is the passive output of the SA fusion
reactor. It has no recipe (the reactor produces it directly). Without an
explicit override:

1. `solve_cost("fusion-plasma")` → no recipe found → tier-1 fallback returned
2. Recipe `dmrsa-repl-fusion-plasma` created at tier 1
3. Unlocked from the simple replicator — game-breaking (fusion-plasma is
   endgame post-rocket content)

**The fix**: introduce a separate `FLUID_TIER_OVERRIDES` table for fluids
that have no recipe. Apply the same lookup pattern as `BASE_RESOURCE_COSTS`:

```lua
local FLUID_TIER_OVERRIDES = {
    ["fusion-plasma"] = { dark_matter = 25.0, time = 25.0, tier = 5 },
}

function CostSolver.solve_cost(name, ...)
    ...
    if BASE_RESOURCE_COSTS[name] then
        return BASE_RESOURCE_COSTS[name]
    end

    -- New: fluid overrides for passive-output fluids
    if FLUID_TIER_OVERRIDES[name] then
        return FLUID_TIER_OVERRIDES[name]
    end
    ...
end
```

**Detection rule**: any fluid in `data.raw.fluid` whose `name` does NOT
appear in any recipe's `results` array (as a `type = "fluid"` result) is a
passive output. Examples in Factorio 2.x + SA:

- `fusion-plasma` (fusion reactor output)
- (Check your own mod for similar patterns)

For each such fluid, decide the tier based on when the producing building
unlocks (fusion reactor → space age endgame → tier 5), and add an entry to
`FLUID_TIER_OVERRIDES`.

## Dead-code audit: fields declared but never read (v3.5.7 lesson)

When a Lua table has fields that nothing reads, the field becomes a
localization-drift trap: if a future maintainer updates the English string in
the table but not in the locale file (or vice versa), they think they fixed
something that no one was actually using.

**Detection rule**:

```bash
# For each Lua file, extract table definitions and check field usage
# 1. Get all fields declared in repltypes.X = { ... } blocks
# 2. Grep the codebase for any read of those fields
# 3. If declared but never read → dead code → remove or fix locale references
```

**Real DMR v3.5.7 example**: `lib/repltypes.lua` had a `localized = "..."` field on
every repltype entry (e.g. `localized = "Ores & Raw Resources"`). The field was
NEVER read by any code — display names came from the locale `[replcategory-name]`
section keyed by category name. Dead code carrying hardcoded English strings.
Fixed by removing all `localized` fields and adding a comment explaining the
locale source.

**The more general lesson**: before adding a new field to a Lua table that
mirrors locale data, verify that the field is actually consumed. If only the
locale is read, don't add a redundant `localized` field "for convenience" —
it becomes a maintenance burden and a source of inconsistencies.

## Standard `order` string format (v3.5.7 minor lesson)

Factorio's `order` field on items/recipes/technologies/entities is a string used
for sort order. The convention is short letter sequences: `"a"`, `"aa"`, `"ab"`,
`"b-b-rep"`, etc. Anything else (brackets, mixed alphanumerics with dashes, etc.)
**works** but is non-standard and confusing in code review.

**Non-standard example from DMR**: `order = "f[dark-matter]"` on a hidden item.
Factorio accepted it (it parses as a valid string sort key) but the brackets
made it look like a template reference. Replaced with standard `"z"` to keep
the convention.

**Rule**: use simple letter sequences for `order`. Use brackets only when
you genuinely need to embed a sortable sub-key (and even then, prefer
letter+letter over letter+text).

## Category-name → tier-floor → required-tech chain (v3.5.9 user confusion)

DMR's `repltypes` table assigns each replication category a **tier floor**:
`ore=1, element/shape=2, alloy/chemical/organic=3, military=4, modules/etc.=5`.
Items get classified by name patterns into these categories in
`get_item_category()`, and the tier floor is then applied via
`tier = max(cost_solver_result, category_floor)`. The tech required to
research that tier (e.g. `dmrsa-replication-3` for tier 3) determines the
science packs needed (chemical at tier 2+, space at tier 4+).

**The user-facing consequence** (real interaction from v3.5.9 testing):
"iron plate and copper plate require chemical to replicate" + "stone brick
too". The user reads this as a bug, but it's actually the design:

- `iron-plate` contains the substring `"plate"` → triggers `alloy` category
  (tier 3 floor) → forces chemical research.
- `copper-plate` → same.
- `stone-brick` contains `"brick"` → triggers `shape` category (tier 2 floor)
  → forces chemical research.

Even though iron-plate and stone-brick feel like early-game items to a
vanilla Factorio player, DMR's replication tree classifies them as tier 3
and tier 2 respectively.

**Why this surprises users**: vanilla Factorio progressions teach
"automation+logistic = early game, chemical = mid game, space = end game".
When `iron-plate` requires chemical in DMR's replication tree, it breaks
the intuition.

**Two response options** when a user reports this:

1. **Confirm it's expected**: explain the category-name → tier-floor chain.
   Show the user where in `repltypes` the category is defined and which
   `get_item_category` rule matched their item.
2. **Adjust the classification**: change the `get_item_category` rules so
   "iron-plate" doesn't fall into `alloy`, or change `alloy`'s tier floor
   from 3 to 2. Trade-off: plates become replicable earlier, but the
   progression curve flattens.

**Detection rule for surfacing this proactively**: after `get_item_category`
is updated, list the tier assignment for common vanilla items and flag any
whose classification seems counter-intuitive. Save this as a sanity check
before any release.

```python
# Sanity check: print tier assignment for common vanilla items
for name in ['iron-plate', 'copper-plate', 'steel-plate', 'stone-brick',
             'iron-gear-wheel', 'copper-cable', 'electronic-circuit']:
    cat = get_item_category(name, ...)
    tier = repltypes[cat].get('tier') or 'dynamic'
    print(f"  {name:25s} -> {cat:12s} tier {tier}")
```

If the user later complains "why does iron-plate need chemical", you have
the audit trail and can decide whether to confirm-by-design or change
classification. The first time a user asks, expect this to come up; the
DMR session had it come up at v3.5.9.

## Don't dismiss "X looks weird" — audit harder (general principle)

Multiple times across v3.5.2 through v3.5.9, the user reported something
visual: "replicators in wrong category", "weird text", "scoop requires
chemical", "fluorine shows from simple replicator". **Every one of those
turned into either a real fix or a real clarification that changed my
understanding of the design**. The user's perception of "weird" in Factorio
is a high-signal bug detector because:

1. They see the rendered output, not the source code
2. They're playing with the actual game flow, not test fixtures
3. They've played enough Factorio to know what "should" happen

**When a user reports "X is weird"**, don't ask "do you have a screenshot?"
— go straight to audit. Look at the relevant prototype definition, locale
entry, tech prerequisite chain, or rendering pipeline. If the audit finds
nothing, say "I checked the code path and it looks intentional because
[reason with trace through the actual code]". If the audit finds something,
you've saved a verification cycle.

**The anti-pattern**: confidently answering "no, that's expected" based on a
quick code read, when the actual code path is more subtle than the quick read
suggested. **Three times in this session**, my first-pass "this is expected"
turned into "actually there IS a bug" after deeper investigation:

- v3.5.5: "replicators in wrong category" → user was right, vanilla subgroup leak
- v3.5.7: "audit cleanup" → found BASE_RESOURCE_COSTS missing items that the
  user hadn't reported yet but were definitely wrong
- v3.5.9: "tier 3 chemical barely lets you research the scoop" → turned out to
  be by-design, but only after I traced the full chain through get_item_category,
  repltypes, cost_solver, and tech prerequisites

The fix is always to read the full code path before responding, even when
you think you already understand it. The cost is 1-2 extra read_file calls.
The cost of confidently wrong is a broken release the user has to find.

## Cost-solver fallback tier pollution (v3.5.11, from mod portal report)

**Trigger**: user on the mod portal (sp518, "Replication: Components (Tier 1)
contains too much stuff?", with Bob's) reported that the `Components (Tier 1)`
grouped tech contained items that should unlock after entering Space Age.
The user in this session independently saw the same family of symptoms:
"Replication: Unknown key: fluid-name.parameter-0..8", then
"Replication: Unknown key: item-name.steel-chest (Researched)".

**Root cause**: `CostSolver.solve_cost()` has two hardcoded fallbacks:

```lua
-- cycle detection
local fallback = { dark_matter = 5.0, time = 2.0, tier = 1 }  -- ← tier 1
-- unknown recipe
local fallback = { dark_matter = 10.0, time = 3.0, tier = 2 } -- ← tier 2
```

With overhaul mods (Bob's, Angel's, K2), many intermediate items hit these
fallbacks because:
- their recipes are **cyclic** (A needs B, B needs A) → cycle detection fires → tier 1
- their recipes are **not in `recipe_map`** (filtered as recycling/barreling,
  or the item is a mined resource with no crafting recipe) → unknown → tier 2

The fallback tier then became the **ingredient tier** for downstream items,
and the `ingredient_tier + 1` cap (added v3.3.6 to prevent "blue bottle"
inflation) kept the final tier low even when the item's own unlock tech was
mid/late game. Net effect: endgame/midgame items polluted the Tier 1 grouped
tech, unlocking too early.

**Fix** (v3.5.11):
1. Both fallbacks now use `recipe_tech_map[name]` → `get_tier_from_tech()`
   when the item has an unlock tech, instead of hardcoded 1/2:
   ```lua
   local cycle_tier = 1
   local cycle_tech = recipe_tech_map[name]
   if cycle_tech then
       cycle_tier = CostSolver.get_tier_from_tech(cycle_tech)
   end
   ```
2. The `ingredient_tier + 1` cap now only applies when `ingredient_tier > 1`.
   Rationale: if ingredients resolved to tier 1 it's ambiguous — could be a
   genuinely simple item OR a degraded cycle/unknown fallback. Skipping the
   cap when ingredients are 1 lets the item's true tech tier surface while
   still protecting simple items whose ingredients are legitimately > 1.

**Detection rule**: when a grouped tech named "Tier 1" / "Components" contains
items the player considers mid/late-game, audit the cost-solver fallback
branches (cycle + unknown-recipe), not just the category classification.
The fix pattern is: prefer the item's own unlock-tech tier over a blind
fallback constant.

## GitHub release push — verify token identity & permissions FIRST (v3.6.0)

Before preparing a git commit for the mod repo, verify the token you have
belongs to an account with push rights on that repo. A token can authenticate
fine yet only have `pull` access — you do all the commit prep, then hit
`remote: Permission to <owner>/<repo>.git denied to <login>` at push time.

Check BEFORE doing any work:

```bash
export GITHUB_TOKEN=...   # stored in ~/.hermes/.env as GITHUB_TOKEN=...
# 1. Who is this token? login must match the repo owner (or a collaborator
#    with Write role)
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/user
# 2. What can it do on the target repo? permissions.push must be true
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/<owner>/<repo>"
```

If `login` != owner and `permissions.push` is false, stop and ask the user
for the right token (their main account PAT with `repo` scope) or to add the
token's account as a collaborator with Write role. Don't burn a cycle staging
a commit you cannot push. Real case: DMR 3.6.0 push prepared fully, then 403 —
token was `servicesjmtech-glitch` (pull-only) against `Jaer985/...`.

## Pre-push private-data scan (user asked: "verifica que no se suba nada privado")

Before `git push`, scan the staged tree for secrets and private paths — a
release repo is public. Reusable checker:
`scripts/check-no-private-data.py` (under this skill). It walks a path and
flags: token patterns (`github_pat_`, `ghp_`, `GITHUB_TOKEN`,
`GITHUB_PERSONAL`), private paths (`~`), account names, secret file
names (`.env`, `.pem`, `.key`, `.DS_Store`, `Thumbs.db`), and any `.cfg`
outside `locale/`. Run it on BOTH the git tree and the built zip before
publishing. Also confirm internal dev dirs (`research/`, `specs/` — audits,
PRDs) are excluded from both the repo and the zip; they are not part of the
mod.

## Sync source into a clone — never let cleanup delete .git (v3.6.0)

When preparing a release push by syncing the mod source tree into a standing
clone, the cleanup pass must be blind to `.git`:

- **rsync (preferred when the target has it):**
  ```bash
  rsync -a --delete --exclude '.git/' --exclude 'research/' --exclude 'specs/' \
        --exclude 'bin/' "$SRC"/ "$CLONE"/
  ```
  `--delete` removes anything in the clone missing from the source — **including
  `.git`** — and excluded paths are the ONLY thing the delete pass skips (unless
  `--delete-excluded` is given). So `--exclude '.git/'` IS the preserve set, not
  a speed option; omitting it silently turns the push target into a non-repo
  (`fatal: not a git repository`) and drops the local history.
- **Manual Python/os.walk mirror (no rsync):** a buggy cleanup branch can delete
  top-level files — including `.git` — leaving a non-repo that fails `git status`.
  Prefer copying the source over the destination with an explicit preserve-list
  for files that exist only in the repo (LICENSE, thumbnail.png), and never run
  delete-logic that doesn't special-case `.git`.

**Gate after EVERY sync, either form**: `git status` inside the clone must work
AND the key files must exist (`info.json`, `changelog.txt`, `data.lua`,
`settings.lua`, `authors.txt`, `FAQ.md`). A failing `git status` means the
preserve set was too small — fix the exclude/preserve list and re-sync; commit
only after the gate passes.

**If `.git` is gone**: re-clone the remote and re-sync — the history is safe on
GitHub, so re-downloading is lossless and takes a minute. Re-init (`git init -b
main` + re-add origin) discards the local history; reserve it for commits that
exist nowhere else.

## Check mod portal discussions when the user reports weirdness (v3.5.11)

Real player reports on `mods.factorio.com/mod/<name>/discussion` are a
first-class diagnostic source — they name the exact mod combo (e.g. "with
Bob's") and symptom that static review can't see. When the user says "hay un
reporte/queja sobre X", fetch the thread:

```bash
# The mod portal discussion page is server-rendered; curl works.
curl -sL "https://mods.factorio.com/mod/<name>/discussion/<id>" -H "User-Agent: Mozilla/5.0" -o /tmp/discussion.html
python3 -c "
import re
html = open('/tmp/discussion.html').read()
text = re.sub(r'<[^>]+>', '\n', html)
text = re.sub(r'\n+', '\n', text)
print('\n'.join(l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 3))
"
```

The `<meta property="og:title">` / `og:description` tags contain the thread
title + body even if the page layout changes. sp518's "Replication: Components
(Tier 1) contains too much stuff?" thread directly drove the v3.5.11
cost-solver fix — same bug class the user had already noticed as
"parameter-N" text in-game.

## Target blacklist for non-replicable items (v3.5.12)

**Trigger**: user reported "hay items que no hace falta replicar" — red-wire,
green-wire, and spidertron-remote appeared as replicable before ever unlocking
them. Later: "los barrel llenos de fluidos salen replicables".

**Root cause**: `TargetMapper.get_potential_replication_targets()` iterates ALL
items of the broad `item_categories` list (item, ammo, armor, gun, capsule,
tool, module, item-with-entity-data, item-with-tags, spidertron-remote,
space-platform-starter) plus all non-hidden fluids. The only filters were:
1. `dmrsa-` prefix (self-replication loop prevention)
2. `hidden` flag (with 3 whitelisted asteroid chunks)

There was **NO blacklist mechanism in the original fork** — UI/utility items
were swept in with production materials.

**Fix** (v3.5.12, in `lib/target-mapper.lua`):

```lua
-- Player-carried UI utilities: replicating adds no value and pollutes lists
local TARGET_BLACKLIST = {
    "red-wire", "green-wire", "copper-wire",
    "artillery-targeting-remote", "discharge-defense-remote", "spidertron-remote",
    "blueprint", "blueprint-book",
    "deconstruction-planner", "upgrade-planner",
    "copy-paste-tool", "cut-paste-tool", "selection-tool",
    "rail-planner",
}
local blacklist_set = {}
for _, name in ipairs(TARGET_BLACKLIST) do blacklist_set[name] = true end

-- Filled barrels: containers that duplicate fluids without a fluid recipe.
-- Empty barrel ("barrel") stays replicable.
local function is_filled_barrel(name)
    if name == "barrel" then return false end
    if string.find(name, "%-barrel$") then return true end
    return false
end
```

Then in the item loop:
```lua
if is_valid and blacklist_set[name] then is_valid = false end
if is_valid and is_filled_barrel(name) then is_valid = false end
```

**Filled-barrel naming**: Factorio 2.x generates filled barrels dynamically as
`fill-<fluid>-barrel` (and some mods use `<fluid>-barrel`). Only the empty
`barrel` item is a literal prototype in `base/prototypes/item.lua` — verify with
`grep -rE 'name = "[^"]*barrel[^"]*"'` against the vanilla item dump.

**Detection rule for audits**: when adding a new replication-target mapper (or
extending an existing one), grep the vanilla item dump for UI/utility families
(wire, remote, planner, blueprint, tool, selection) and decide each: is it a
production material or a player-carried utility? The latter belong in the
blacklist. If the user ever says "why is X replicable" for a utility item, the
answer is a blacklist entry, not a balance discussion.

## SA item-name drift (v3.5.13)

**Trigger**: user asked whether "carbonoid asteroid chunk" appearing in the
chemical (tier 3) replication tech was valid, or whether it should wait until
after launching the rocket. It was a bug — the chunk was tier-gated too low.

**Root cause**: the code had `carbonaceous-asteroid-chunk` in two places
(`BASE_RESOURCE_COSTS` in cost-solver.lua and the hidden-item whitelist in
target-mapper.lua), but the real Space Age internal name is
**`carbonic-asteroid-chunk`**. Because the string didn't match, the item:
1. Was NOT in `BASE_RESOURCE_COSTS` → fell to the tier-1/2 fallback path
2. Was NOT in the target-mapper hidden-item whitelist → hidden status mishandled

The item then appeared in an early replication tier (chemical/tier-3 area)
instead of tier 4 where the other asteroid chunks (metallic, oxide, promethium)
live.

**The rule**: Space Age item names are NOT stable across data versions and
WILL drift from what you remember or what older code says. When mapping any
SA item by name, verify the exact internal name against the live data dump
before writing the lookup entry:

```bash
# Verify an SA item name against the live data dump
curl -sL "https://raw.githubusercontent.com/wube/factorio-data/master/space-age/prototypes/item.lua" \
  | grep -E 'name\s*=\s*"(carbonic|carbonaceous)-asteroid-chunk"'
# → name = "carbonic-asteroid-chunk"  (real name)
```

Check `space-age/prototypes/item.lua`, `fluid.lua`, `recipe.lua` as needed.

**Detection rule for audits**: when auditing tier tables (`BASE_RESOURCE_COSTS`,
`FLUID_TIER_OVERRIDES`, whitelists), cross-reference EVERY SA item name against
the live data dump. A stale name is silent — the item just falls through to
the wrong fallback tier. User symptom: an asteroid/SA item appears in an early
replication tier when it should be tier 4-5.

## Category-split by progression tier (v3.5.14)

**Trigger**: user (writing their own opinion for the mod portal, in English) said
"as of now, I don't see any weapons or modules in t3 to be replicated or ammo"
and asked whether to blacklist or create subgroups; portal commenter sp518 asked
"Can we make a separate tech for the modules and weapons?".

**Root cause**: `repltypes.lua` gated whole categories by a single tier floor —
`module` at tier 5 (cryogenic), `military` at tier 4 (space). Every module,
from early-game speed-module to late-game productivity-module-3, was locked
behind cryogenic science. Every weapon from pistol to uranium cannon shell was
locked behind space science. Vanilla unlocks them much earlier (speed-1 with
chemical), so players felt the items were "missing" — they existed, but the
tier floor hid them.

**The fix pattern** (reusable): split the over-gated category into base +
advanced subcategories keyed on name patterns, each with its own tier floor:

```lua
-- lib/repltypes.lua
military = { name = "military", tier = 3, order = "cf" },
military_advanced = { name = "military-advanced", tier = 5, order = "cg" },
module = { name = "module", tier = 3, order = "ea" },
module_advanced = { name = "module-advanced", tier = 4, order = "eb" },
```

```lua
-- prototypes/recipes/dynamic-generator.lua, in get_item_category()
-- Modules: tier 1-2 → base (3), tier 3 → advanced (4)
if string.find(name, "module") or subgroup == "module" then
    if string.find(name, "module%-3") then return "module-advanced" end
    return "module"
end

-- Military: early/mid weapons → base (3), endgame ordnance → advanced (5)
local is_military = ...  -- type/name pattern checks (unchanged)
if is_military then
    if string.find(name, "uranium") or string.find(name, "artillery")
       or string.find(name, "explosive%-rocket") or string.find(name, "cluster")
       or string.find(name, "spidertron") or string.find(name, "nuke")
       or string.find(name, "nuclear") or string.find(name, "explosive%-cannon")
       or string.find(name, "explosive%-uranium") then
        return "military-advanced"
    end
    return "military"
end
```

**Mandatory locale step**: both new category keys need `[replcategory-name]`
entries in EN AND ES (`module-advanced=Advanced Modules` /
`military-advanced=Advanced Military` + Spanish), and the EN/ES parity check
must pass. The grouped tech names derive from these keys
(`dmrsa-grouped-repl-3-module-tech`, `dmrsa-grouped-repl-4-module-advanced-tech`,
etc.) — a missing locale renders the raw key in the tech tree.

**Simulate before building**: write a small script that runs the new
`get_item_category` over the vanilla item dump (modules + weapons) and prints
category+tier, so you can eyeball the classification table before building the
zip. The v3.5.14 table (verified) looked like:

| Item | Category | Tier |
|---|---|---|
| speed-module, speed-module-2, efficiency-module | module | 3 |
| speed-module-3 | module-advanced | 4 |
| pistol, shotgun, firearm-magazine, grenade, defender-capsule, land-mine | military | 3 |
| explosive-rocket, cluster-grenade, uranium-rounds-magazine, artillery-shell | military-advanced | 5 |

**Follow RDD for this class of change**: it's a balance/design change →
standard risk → reliability lens + user consent (proposal → approve → frozen
candidate → patch → receipt → test). The v3.5.14 release was the first run of
the `receipt-driven-development` skill.

## Lua `%-` pattern corruption by the patch tool (v3.5.14 gotcha)

When rewriting a multi-line block that contains a Lua pattern with an escaped
dash (`%-`), the patch may silently insert a space into the escape sequence:
`mine%-` became `mine% -` in the applied diff. That changes the match from
"mine-" to "mine " (with a space) — a silent behavioral change that compiles
fine but never matches.

**Detection**: after any multi-line patch touching `string.find`/`string.match`
patterns, grep for suspicious spaces inside `%` escapes:

```bash
grep -nE '% [a-zA-Z]' prototypes/**/*.lua   # space after %-escape = bug
grep -n 'mine%-' prototypes/recipes/dynamic-generator.lua  # should be intact
```

**Rule**: when your `new_string` contains `%-` sequences, verify them in the
resulting diff; the fuzzy matcher can mangle them. A 2-char visual check in the
diff saves a runtime bug that only surfaces in `string.find` behavior.

## External mod deletes a technology — force load order with optional dependency (v3.5.15)

**Trigger** (startup crash, not runtime):
```
Failed to load mods: Error in assignID: technology with name 'spidertron-unit'
does not exist. It was removed by moon-eneas.
Source: dmrsa-grouped-repl-5-general-tech (technology).
```

**Root cause**: another mod (`moon-eneas`) deletes a technology in its own
`data-final-fixes.lua` (`data.raw.technology["spidertron-unit"] = nil`). DMR
referenced that tech as a prerequisite of a grouped tech created in
data-updates. `data-final-fixes.lua` files run in **dependency order** — if DMR
has no declared dependency on the deleting mod, DMR's data-final-fixes may run
BEFORE the deleting mod's, so the PASS 1 prerequisite-stripper never sees the
deletion, and the invalid prereq survives to the assignID phase → crash.

**Fix** (1 line in `info.json`):
```json
"dependencies": [..., "? moon-eneas"]
```
The optional dependency forces Factorio to run the other mod's data-final-fixes
first, so DMR's PASS 1 strips the now-missing prereq and PASS 3 re-routes any
orphaned grouped tech as designed. No code change needed in data-final-fixes —
the existing PASS 1/3 machinery was correct all along; it just never ran in
the right order.

**Generalization**: ANY external mod that deletes vanilla/moddable technologies
(aai-loaders-sane, moon-eneas, Krastorio tweaks, etc.) → declare it as an
optional dependency to force load order. Same category of conflict documented
in `MOD-RESEARCH-NOTES.md`. When the user reports an assignID error naming an
external mod as the remover, check `info.json` dependencies FIRST before
touching the data-final-fixes logic.

## Research difficulty multiplier setting (v3.5.16)

**Pattern**: startup string-setting (`allowed_values`) + a helper in
`lib/helpers.lua` mapping the setting to multiplier tables, applied at every
tech-creation site:

```lua
function helpers.get_research_difficulty_multipliers()
    local difficulty = helpers.get_startup_setting("dmrsa-research-difficulty", "Easy (Fast)")
    if difficulty == "Medium" then return { reps_mult = 1.5, time_mult = 2.0 }
    elseif difficulty == "High" then return { reps_mult = 3.0, time_mult = 5.0 } end
    return { reps_mult = 1.0, time_mult = 1.0 }
end
```

Apply `math.ceil(count * diff_mult.reps_mult)` / `time * diff_mult.time_mult`
in **every** tech-creation path. In DMR these are:
1. individual techs in `dynamic-generator.lua` (reps + time computed inline)
2. grouped techs in `dynamic-generator.lua` (same, plus the ×5 time gate)
3. static tier techs in `technologies.lua` — inside `make_research_unit`
4. planetary techs in `planetary-tech.lua` — inside its OWN duplicate
   `make_research_unit`

**Pitfall — duplicated helper**: `technologies.lua` and `planetary-tech.lua`
each define a local `make_research_unit` with the same body. Patching only one
leaves the other unscaled. Grep the repo for the helper name before assuming a
single call site: `grep -rn "make_research_unit" prototypes/`.

**Design rules for difficulty settings**:
- Default MUST be the historical behavior (×1/×1) so existing saves and
  expectations don't break.
- Setting name + description must be added to `[mod-setting-name]` AND
  `[mod-setting-description]` in both locales; the description should spell
  out the multiplier table (users need the numbers at a glance).
- If the change also raises a balance constant (here
  `dmrsa-grouped-tech-cost-multiplier` 5.0 → 10.0 so grouped research is at
  least 10× per unlockable), say so explicitly in the changelog — it's a
  behavior change, not a fix.
- Order namespace: settings under `3-*` are research; place new research
  settings adjacent to existing ones (`3-2-2` after `replresearch-space-lock`).

## Hidden placeholder tech side effect — FIXED in v3.5.17 (chemical before planets)

**Symptom** (user, SA game): \\\"el chemical replicator esta con cada planeta, deberia
ser una tech antes de los planetas\\\" — the Chemical Replicator (tier 3) doesn't appear
as a tier-3 tech before the planetary techs; chemicals (petroleum-gas, sulfur, oil)
seem to live with the planets instead of a standalone chemical tier.

**Root cause** — the v3.5.2 \\\"hidden placeholder\\\" fix for SA has a side effect:
in `technologies.lua`, the SA branch defines `dmrsa-replication-3` as:

```lua
hidden = true,
effects = {},          -- unlock-recipe of the replicator-3 REMOVED
prerequisites = { gprefix .. "replication-2" },
```

With SA, `dmrsa-replication-3` is a hidden inert sink (used by data-final-fixes
PASS 3 to re-route orphaned tier-3 unlocks). But the same tech is what would
unlock `dmrsa-replicator-3` (the Chemical Replicator entity) via its
`unlock-recipe` effect — and because effects were emptied, **there is no visible
tech that unlocks the chemical replicator before the planets**. `rep_4_prereqs`
with SA also skips `replication-3` (goes straight to the 3 planetary techs +
processing-unit), so the tier-3 machine is orphaned from the visible tree.

**Diagnosis path that worked**: user says \\\"X machine is tied to planets / missing
from the tree\\\" → don't grep the machine prototypes first. Read the TECHNOLOGY that
would unlock it (`technologies.lua` branch for that tier) and check for
`hidden = true` + `effects = {}`. The v3.5.2 orphan-sink fix is the usual culprit.

**Fix applied in v3.5.17** (user confirmed the design: chemical = tier 3 BEFORE
planets, planetary = tier 4):
1. SA branch of `dmrsa-replication-3`: dropped `hidden`, restored the real
   `unlock-recipe` effect for `dmrsa-replicator-3` (matches the non-SA branch),
   keeps it as the tier-3 visible tech BEFORE the planets.
2. Added `gprefix .. "replication-3"` to `rep_4_prereqs` (SA branch) so the
   chain tier3 → tier4 stays intact.
3. data-final-fixes PASS 3 sink keeps working — `replication-3` stays a valid
   reassignment target whether hidden or not.

**Lesson**: every \\\"hidden placeholder with empty effects\\\" sink tech created to
absorb orphan unlocks also erases the visible unlock path for whatever that tech
would normally unlock (a machine, a recipe). Before hiding a tech, ask: does
anything the player must acquire depend on its effects? If yes, keep the effects
and add the placeholder as a prerequisite of the next tier instead of emptying it.

## Science-pack tier anchoring by name, not cost chain (v3.5.17)

**Trigger** (user, SA): \\\"el chemical science pack termino en tier 5 cuando debe estar
justo en tier 3 de replication\\\" + \\\"el planetary se considera tier 4\\\" +
\\\"production/utility estan alli mismo con tier 3 antes de planetary\\\".

**Root cause**: `chemical-science-pack`'s recipe chain (advanced circuits, engine
units, sulfur, etc.) pushes the cost-solver result to tier 4-5. The `science`
category has `tier = nil` (dynamic), so there is no floor to pull it back to 3.
Same problem would hit any science pack whose recipe chain is deeper than its
intended progression tier.

**User-confirmed progression model** (authoritative — this is the design):

| Science pack | Replication tier |
|---|---|
| automation, logistic | 1 |
| military | 2 |
| chemical, production, utility | 3 (BEFORE planets — production/utility sit at the END of chemical) |
| metallurgic, electromagnetic, agricultural (planetary) | 4 (planets ARE tier 4) |
| space, cryogenic, promethium | 5 |

**Implementation (3 files)**:
1. `dynamic-generator.lua` tier-floor block: when `item_category == "science"`,
   override tier by name pattern (same mapping above) instead of trusting
   `solve_cost`. Pattern order matters: check `automation`/`logistic` first,
   then `military`, then `chemical`/`production`/`utility`, then the three
   planetary names, else default 5 (space/cryo/promethium/unknown).
2. `cost-solver.lua` `get_tier_from_tech`: remap science-pack detection —
   chemical → 3 (was 2), production/utility → 3 (was 4), planetary → 4 (was 3),
   space/cryo/promethium → 5 (unchanged). This propagates to items whose unlock
   tech uses those packs.
3. `technologies.lua` `t_packs`: t3_packs = chemical ONLY (REMOVE the SA
   `table.insert(t3_packs, "metallurgic-science-pack")` — that made tier-3
   research demand a planetary pack, contradicting chemical-before-planets);
   t4_packs (SA) = metallurgic + electromagnetic + agricultural; t5 (SA) =
   space + cryogenic. Note: production/utility do NOT exist in SA — they are
   base-game packs; the non-SA branch keeps them.

**Sanity check before building**: simulate the science-tier function over the 12
known packs and print the tier table — must exactly match the progression above.
Catching one wrong tier at simulation time beats a receipt script catching it in
the zip.

**Receipt verify-script false FAIL** (same release): receipt scripts that slice
file content with `split('\\n')` or multi-line markers fail on CRLF (`\\r\\n`)
files and report false FAILs. When a receipt check FAILs, confirm the failure is
in the CHECKER, not the artifact — grep the SOURCE files directly for the marker
before distrusting the zip. Prefer direct `in` content checks over positional
slices; for branch-specific checks (SA vs non-SA `if/else`), anchor on a unique
comment line that only exists in that branch.

## Planetary classification overrides BASE_RESOURCE_COSTS tier (v3.5.18)

**Trigger** (user, SA): \\\\\\\"scrap replication debe ser en su planeta\\\\\\\" — scrap was
replicable from the simple replicator instead of requiring the Fulgora planetary
replicator.

**Gotcha**: `scrap` already had `BASE_RESOURCE_COSTS[\"scrap\"] = { dark_matter = 0.6, time = 0.6, tier = 1 }` in cost-solver.lua. Seeing tier=1 there might suggest it's a simple early item — but the tier floor from BASE_RESOURCE_COSTS is only the cost-solver's answer. The **planetary classification block** in `dynamic-generator.lua` runs AFTER the tier override and can redirect the recipe to a planetary category regardless of the computed tier:

```lua
elseif string.find(name, "holmium") or string.find(name, "scrap")
       or name == "superconducting-cable" or name == "electromagnetic-science-pack" then
    category = gprefix .. "replication-fulgora"
    planet_suffix = "fulgora"
```

So an item with tier=1 in the cost tables can still end up on a planetary
replicator. When the user says "X should be on planet Y", the fix is ONE
`string.find`/`name ==` clause added to the right `elseif` branch — verify the
branch (gleba/vulcanus/fulgora/aquilo) matches the item's vanilla source planet
before patching. No cost-solver change needed.

**Detection rule**: for any SA planetary-exclusive resource (scrap→Fulgora,
calcite/tungsten→Vulcanus, yumako/jellynut→Gleba, ice/lithium/fluoroketone→Aquilo),
check the planetary classification block has a matching clause. Missing clause =
item falls to the generic tier replicator at its cost-solver tier.

## Science-pack tier must be FORCED absolute, not just a floor (v3.5.19)

**Trigger** (user, SA): "el chemical science pack replication research esta con
matter conduit cuando deberia ser dark matter transducer en acorde con el tier 3" —
the chemical-science-pack replication research used **matter-conduit** (the tier-4/5
research material) instead of **dark-matter-transducer** (the tier-3 material).

**Root cause**: the v3.5.17 science-pack override only RAISED the floor:

```lua
if tier < science_tier then tier = science_tier end
```

But `dynamic-generator.lua` tier logic is "category = FLOOR; cost-solver can still
push HIGHER". For science packs the cost-solver DOES push higher: the
chemical-science-pack recipe chain (advanced circuits, engine units, sulfur)
resolves to tier 4-5, so even with the floor set to 3 the final tier stays 4-5,
and the research-pack selection (`tier == 3 → dark-matter-transducer`,
`tier 4/5 → matter-conduit`) picked matter-conduit. A floor-only override is
insufficient whenever the cost-solver's answer exceeds the intended tier.

**Fix**: force the science tier ABSOLUTE (both directions):

```lua
if tier < science_tier then
    tier = science_tier
end
if tier > science_tier then
    tier = science_tier
end
```

Equivalently, set `tier = science_tier` unconditionally inside the `science`
branch. Science packs are the one class where the NAME defines the progression
position — the recipe chain must never override it.

**General rule**: floor-only overrides (`if tier < floor`) are correct for
material categories where recipe complexity legitimately raises the tier. They
are WRONG for any item whose tier is defined by design position (science packs,
planetary-exclusive items). For those, force absolute both up AND down.

**Detection**: user says "X research uses the wrong pack/material" → trace the
research-pack selection (`elseif tier == 3 then ... transducer ... elseif tier
in {4,5} then ... conduit ...`) and the tier computation feeding it. If a
name-based override exists but only raises the tier, that's the bug.



## Release-identity three-way match, single-source builder, changelog lint (pre-upload)

Version drift is a *release blocker*, not a paperwork issue — each of these ships something wrong
or gets the upload rejected:

1. **Three-way match before building**: `info.json` `version` == top `changelog.txt` `Version:` block
   == version in the zip filename. All three are written by hand and drift independently; a tree full
   of NEW code carrying the LAST published number is a duplicate-version reject on the portal (or a
   silent re-upload that breaks the changelog contract for everyone who already has that version).
   The portal API (`/api/mods/<name>` → `releases[-1].version`) is the source of truth for what is
   already published, not the local changelog.
2. **The builder must read the version from `info.json`** — never hardcode `OUT=..._<ver>.zip` plus a
   list of assertions for the old version's strings. A hardcoded builder cannot produce the next
   version, and its failing assertions invite hand-edits that skip newly added files.
3. **Assert the built zip contains every file any module requires — from the ZIP, not the tree.**
   `safe_require`/`pcall` degrades a missing module into a log line, so a mis-built zip loads "fine"
   with the whole new feature silently absent and the gate still exits 0. Checking only `data.lua`'s
   own requires is NOT enough: the requires that bite are transitive (`lib/init.lua`,
   `prototypes/entities/*` reaching into `lib/`). Build the require GRAPH — regex
   `(?:safe_require|require)\s*\(\s*"([^"]+)"\s*\)` over EVERY `.lua` inside the zip — and assert
   every **mod-internal** edge resolves to a file in `zip.namelist()`. Skip vanilla edges:
   `__base__/`-`__core__/` prefixed paths and bare lualib names (`util`, `resource-autoplace`) that
   the engine resolves from core/base. Then run the engine gate against the extracted ZIP's bytes,
   never the source tree — the zip is what ships.
4. **Changelog lint the in-game parser enforces** (the portal accepts the file as plain text, so
   violations ship broken and silent): every `-----` separator must be followed by a `Version:` line;
   category headers are the known two-space-indented forms (a bare `NOTE:` or odd indent creates an
   orphan block that re-parents the entries below it); no trailing whitespace. The WHOLE file ships,
   so lint every historical version block too, not just the one you added. Run the lint before
   upload, not after a player reports it.
5. **After publishing, sync the announcement channels**: `python3 ~/.hermes/scripts/dmr-release-announce.py --check`
   compares the portal API against the Discord announcement post (exit 1 = stale or missing; `--fix`
   updates the post in place). Make it a checklist step so the announcement never lags the release
   again.
6. **Run the gate at least once with `--check-unused-prototype-data`** (on the zipped build): it
   surfaces recipes bound to a category that no longer exists, orphaned prototypes and lost
   references that a normal `--dump-data` load only warns about — or accepts silently.
7. **Every number you publish comes from the dump of the shipped zip, not from memory or the dev
   tree.** Changelog claims, portal description and FAQ promises (machine draws, cycle times,
   research costs, multiplier totals) are verified by querying `data-raw-dump.json` for the exact
   prototype. A balance fix lands, the claim written before it survives in the prose, and the portal
   then contradicts the game.
8. **Project docs must not carry release state** — "built but not uploaded", "current version:
   X.Y.Z", "1,120 downloads" go wrong the moment you publish. Any fact that the portal knows
   (version, download count, what shipped) is fetched from `/api/mods/<name>` at need, and docs say
   WHERE to get it instead of freezing a snapshot. A doc that claims a release is un-uploaded after
   it went live is worse than no doc: it sends the next session to re-do work already done.

## State review — the roadmap is a claim set, not a fact

When the user asks to review a mod's roadmap / project state ("vamos a revisar el roadmap"),
the doc is the CLAIM set; the artifacts decide what is true. Order of truth, highest first:

1. **Published** — `curl -s "https://mods.factorio.com/api/mods/<name>"` → `releases[-1]` is what
   players actually have (`version`, `released_at`, `file_name`) plus `downloads_count`. Public
   endpoint, no auth, no cookie.
2. **Shipped bytes** — `unzip -p <zip> <mod-root>/info.json | grep '"version"'` and
   `unzip -l <zip> | grep -i <feature>`. The zip root is the mod NAME taken from `info.json`, so
   the inner path carries no version and no working-folder suffix — don't guess a versioned
   directory name when grepping the archive.
3. **Source** — `info.json` version vs the FIRST `Version:` block of `changelog.txt` (newest block
   sits at the top of the file).
4. **Behaviour** — run the suite (`cd dmr-tests && lua5.2 run_tests.lua`; it lives BESIDE the
   source dir, not inside it) and read the newest `research/apply-*.md` receipt as a claim to
   re-run, not as evidence.
5. **Prose** — `ls -la --time-style=long-iso ROADMAP.md FAQ.md README.md mod-portal-description.md`
   and compare each mtime against the newest source file. Prose older than the last release has
   not re-checked its own claims.

Then report: real state first (mark every line as verified this session or not), the backlog split
into doc debt / needs the user's in-game data / technical debt / parked decisions, and close with
ONE concrete next action.

Pitfalls:
- A roadmap's status header ("published X, in development Y, info.json still Z") is a frozen
  snapshot that goes wrong on the next publish. Verify every clause against the artifact; never
  quote the header as state. Same rule as "project docs must not carry release state" above.
- Publishing does not update the prose players read: `info.json`'s one-line description ships
  inside the zip, while the portal description page is a separate document. Check both — they
  drift independently, and a shipped feature missing from the page is publish debt no player
  reports and no gate catches.
- Release-adjacent docs and the per-version builders (`research/build_*.py`) live in the PROJECT
  dir, one level ABOVE the source dir. A `ls`/`find` scoped to the source dir reports them missing,
  which reads as "the docs don't exist" and produces a wrong conclusion.
- Several repos can carry a `ROADMAP.md`. Pick the one by last-modified + active work, state the
  assumed target in one line, and proceed: one wrong guess costs a reply, a clarifying round costs
  a whole turn.
- `scripts/portal-state-check.py <source-dir>` runs steps 1-3 plus the doc mtimes in one shot and
  prints a DRIFT line per disagreement. The individual commands above are the verified fallback if
  the wrapper misbehaves.

## Applying an approved audit batch with parallel subagent chains

When a decision batch is approved, splitting the work across subagent chains is how a large mod gets
fixed in one pass instead of serial patch-rebuild cycles:

1. **Partition by disjoint files, never by topic.** Each chain owns whole files (economy logic /
   prototypes+art / locale+docs). Topic partitions on a shared file guarantee merge conflicts and
   wasted work; disjoint files also let chains run truly in parallel.
2. **Each chain writes its own receipt file** (`research/apply-<area>.md`): what changed, the
   before/after numbers, what it tested and with what command, and — critically — anything it was
   BLOCKED from doing (write-protected paths must be recorded, not worked around; `AGENTS.md` and
   other guarded files get their intended edit transcribed into the receipt for the author to apply).
3. **Each chain proves its own slice** (targeted dump query + the test suites it can run). This does
   NOT prove the combination.
4. **You verify the MERGED artifact yourself, after all chains land**: run the full test suite and
   the engine gate against the merged tree, then rebuild and re-gate the zip. Each chain only ever
   loaded its own snapshot — the merge is a state nobody has tested, and combination bugs (an
   invariant split across two chains' files, a constant one chain renamed that another still
   asserts) only surface there.
4. **Re-read each receipt's numbers against the merged dump** rather than trusting the receipt: a
   chain reports what it believes it did, and the receipt is a self-report just like a final answer.

## Enabling a gated feature: trace every downstream pass, not just the gate

A feature that a whitelist/gate decides "eligible" ships only if NO later pass deletes the item.
Each of these bit on the same feature (restoring replicator self-replication after it had been
disabled for many versions):

- **A whitelist intent is dead code if a name-based veto runs later.** One module decides "is this
  a target" with an explicit whitelist; a later module vetoes the same items by NAME (own-machine,
  own-prefix, hidden) before the whitelist is read. Both modules read as correct in isolation, the
  feature never ships, and no test catches it. Rule: when module A gates on membership and module B
  has a name/shape veto that runs later, the veto is the real decision — verify by probing the
  SHIPPED prototype (recipe exists + a sane `energy_required`), never by reading the whitelist.
  Same class as "an existence guard only sees what loaded BEFORE it".
- **Every later re-pricing or re-filtering pass can independently delete the item.** Opening the
  name veto exposed the item to a parts-bill clamp and a recycler-loop re-pricing block, each of
  which re-priced it (3695-15612 s) and then a ceiling filter removed it. After opening a gate,
  re-run the count probe until the shipped count stops moving; a single-pass fix is a guess.
- **`is_burnable` is not a fuel class.** A burnable test accepts sub-MJ materials (a 100 kJ tree
  seed, a 250 kJ spoilage stack) and then those materials inherit the fuel-class treatment:
  productivity on their replication recipe, fuel-exclusion from the price fixpoint. Gate a fuel
  class on a joule threshold (`fuel_value >= 1 MJ`), the smallest legitimate fuel; sub-MJ burnables
  are materials and must price like materials. Measured: 18 → 16 recipes with `allow_productivity`.
- **"Tier 1 has too much stuff" is a tier-RULE complaint, not a list complaint.** The tier is
  `max(pack_tier, chain_tier)` and complexity only scales TIME (capped), so an item's tier is
  decided by the science pack that unlocks it, not by how deep its recipe chain is. Before
  proposing per-item moves, MEASURE: count recipes per tier and compute each tier-1 item's chain
  depth against `data.raw` (the data-stage probe pattern). Deep items in a basic tier prove the
  rule is wrong, not the list; the fix is a rule change (a complexity floor or a class rule),
  because a hand list never survives a modlist change.
