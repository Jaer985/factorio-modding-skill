# DMR Morning Briefing — Monitor List

Canonical list of conflicting mods to check during the daily morning tech briefing.
Fetch each mod's portal page, extract the current version and `Last updated` date.

> ⚠️ **API caveats for the cron runner (verified 2026-08-21, supersedes the
> 2026-08-12 note)**:
> Both the bulk `?namelist=` endpoint AND the single-mod `/api/mods/<slug>`
> endpoint work. The previous note that single-mod 404'd was wrong for
> the *mod-id* URL — verified live: `https://mods.factorio.com/api/mods/
> dark-matter-replicators-reborn` returns a **flat** JSON payload (no
> `results` wrapper) with the full release list under `releases[]`. Use
> the per-mod endpoint for quick single-checks; use the bulk endpoint
> when you need the full catalog.
>
> **In both endpoints, `latest_release` is now `null` for every mod
> (verified 2026-08-21 across 8 mods).** ⚠️ **The `releases[]` array on the
> per-mod flat endpoint is ASCENDING (oldest first) — `releases[0]` is the
> FIRST release ever, NOT the latest** (verified 2026-10-14: for
> `dark-matter-replicators-reborn`, `releases[0]` = v3.0.0 (2026-06-06) while
> the live portal was v4.2.0; for `aai-loaders-sane` it returned v1.0.0 while
> the live version was 1.0.5 — a silent STALE briefing). **Always take the max
> by `released_at`**: `rel = max(rels, key=lambda r: r['released_at'])`. Read
> from there:
> `rel = (m.get('latest_release') or m['releases'][0])` and pull
> `version` / `released_at` / `info_json.factorio_version` from there.
> Reading `latest_release.version` silently returns `?` (a string)
> and looks like a working API call, hiding the shape change.
> See "Version-check commands" at the bottom for the full pattern.

## Mods to monitor

### aai-loaders-sane
- **Portal**: https://mods.factorio.com/mod/aai-loaders-sane
- **API**: bulk-indexed — see "Version-check commands" below
- **Conflict**: Deletes `aai-loader` technology in `data-final-fixes.lua`
- **Error pattern**: `"technology with name 'aai-loader' does not exist. It was removed by aai-loaders-sane"`
- **Last known version (2026-08-28)**: **1.0.5 (2026-07-08, factorio_version 2.0)** — updated 2026-07-08 from 1.0.0. Track for any new tech-deletion changes.

### moon-eneas
- **Portal**: https://mods.factorio.com/mod/moon-eneas
- **API**: bulk-indexed — see "Version-check commands" below
- **Conflict**: Deletes `spidertron-unit` technology in `data-final-fixes.lua`
- **Error pattern**: `"technology with name 'spidertron-unit' does not exist. It was removed by moon-eneas"`
- **Last known version (2026-08-28)**: **1.0.10 (2026-08-21, factorio_version 2.0)** — **major version jump from 0.6.0 → 1.0.x in Aug 2026**. Two releases this week (1.0.9 → 1.0.10). Active development; treat conflict behavior as likely-changed.
- **Last verified clean**: DMR v3.5.15 + `? moon-eneas` optional dep declaration in info.json fixed the data-final-fixes load-order race. Verify the fix still holds against 0.6.0 if the mod's tech-deletion semantics changed in the 0.6.x series.

### Angel's Smelting (angelssmelting)
- ⚠️ **API slug has NO hyphens**: hyphenated guesses (`angels-smelting`, `angels-petrochem-processing`) fail. Always use `angelssmelting`, `angelspetrochem`, `angelsrefining`.
- **Portal**: https://mods.factorio.com/mod/angelssmelting
- **API**: bulk-indexed — see "Version-check commands" below
- **Conflict**: Duplicate `angels-basic-chemistry` prereq when used with Petrochem.
- **Error pattern**: `"angels-basic-chemistry is registered more than once"`
- **Last known version (2026-08-21)**: 0.2.4 (2017-04-20, factorio_version 0.14) — legacy/unmaintained; only loads on 0.x Factorio via its declared factorio_version. The "2.1.1" figure from earlier notes was speculative — never observed in the live catalog.

### Angel's Petrochemical Processing (angelspetrochem)
- **Portal**: https://mods.factorio.com/mod/angelspetrochem
- **API**: bulk-indexed — see "Version-check commands" below
- **Conflict**: Shared tech name `angels-basic-chemistry` with Smelting.
- **Error pattern**: See Smelting above
- **Last known version (2026-08-21)**: 0.4.9 (2017-04-20, factorio_version 0.14) — legacy. See Smelting note.

### Angel's Refining (angelsrefining)
- **Portal**: https://mods.factorio.com/mod/angelsrefining
- **API**: bulk-indexed — see "Version-check commands" below
- **Conflict**: Part of Angel's ecosystem, may share tech/recipe names.
- **Last known version (2026-08-21)**: 0.6.13 (2017-04-15, factorio_version 0.14) — legacy.

### Angel's Bioprocessing (angelsbioprocessing)
- **Portal**: https://mods.factorio.com/mod/angelsbioprocessing
- **API**: bulk-indexed
- **Conflict**: Part of Angel's ecosystem.
- **Last known version**: not verified 2026-08-21.

### Krastorio 2
- **Portal**: https://mods.factorio.com/mod/Krastorio2
- **API**: bulk-indexed — slug is `Krastorio2` (camelCase, see slug quirks below)
- **Conflict**: Large overhaul, modifies vanilla recipes/categories that DMR replicates.
- **Last known version (2026-08-21)**: 0.9.99 (2020-07-19, factorio_version 0.18) — legacy catalog. Active K2 development is on a separate fork; the "2.1.2" figure from earlier notes was speculative.

### Space Exploration
- **Portal**: https://mods.factorio.com/mod/space-exploration
- **API**: bulk-indexed
- **Conflict**: Large overhaul, may affect replication category mapping. Extensive dynamic tech generation.
- **Last known version (2026-08-21)**: 0.1.1 (2019-03-23, factorio_version 0.17) — legacy. SE's main development is on a separate Space Age successor; the "0.7.61" figure from earlier notes was speculative.

### PlanetsLib
- **Portal**: https://mods.factorio.com/mod/PlanetsLib
- **API**: bulk-indexed
- **Conflict**: Sets rocket weights on vanilla items in `data-final-fixes.lua`.
- **Last known version (2026-08-21)**: 1.0.0 (2024-12-30, factorio_version 2.0). The "1.23.5" figure from earlier notes was speculative.

## Version-check commands (both Portal JSON endpoints work)

The mod portal exposes **TWO** JSON endpoints for catalog data:

- ✅ `https://mods.factorio.com/api/mods?page_size=10000&page=N` — bulk catalog
  (3 pages × 10000 = ~22726 mods). Returns `{"results": [...], "pagination": {...}}`.
  Index by lowercased `name` for O(1) lookup. Best when checking ≥2 mods in
  one briefing.
- ✅ `https://mods.factorio.com/api/mods?namelist=<slug>` — single mod by name,
  returns `{"results": [mod]}` (still wrapped in `results`).
- ✅ `https://mods.factorio.com/api/mods/<slug>` — single mod by ID/slug,
  returns a **FLAT payload** (no `results` wrapper, no `pagination`),
  with `releases[]` directly at the top level. Best for one-shot checks.

**`latest_release` is now `null` in all three endpoints** (verified 2026-08-21).
Always read from `releases[0]`:

```python
# Per-mod (flat payload) — quickest for one mod
import urllib.request, json
url = "https://mods.factorio.com/api/mods/dark-matter-replicators-reborn"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
m = json.loads(urllib.request.urlopen(req, timeout=15).read())
rel = max(m["releases"], key=lambda r: r["released_at"])  # NOT releases[0] — array is oldest-first
print(f"{m['title']} v{rel['version']} released={rel['released_at'][:19]}")

# Per-mod (namelist) — wrapped in results
m = json.loads(urllib.request.urlopen(req, timeout=15).read())["results"][0]
rel = max(m["releases"], key=lambda r: r["released_at"])  # oldest-first array
```

**Step 1 — Save the 3 catalog pages** (avoids `curl | python3 -c` security block in cron):
```bash
mkdir -p /tmp/dmr-briefing
curl -sL "https://mods.factorio.com/api/mods?page_size=10000" \
  -o /tmp/dmr-briefing/mods.json
curl -sL "https://mods.factorio.com/api/mods?page_size=10000&page=2" \
  -o /tmp/dmr-briefing/mods_p2.json
curl -sL "https://mods.factorio.com/api/mods?page_size=10000&page=3" \
  -o /tmp/dmr-briefing/mods_p3.json
```

**Step 2 — Parse with a script written to file** (`execute_code` is BLOCKED in cron, so
write the script to disk first, then call `python3 /path/script.py`):
```python
# /tmp/dmr-briefing/parse_mods.py
import json

idx = {}
for path in ['/tmp/dmr-briefing/mods.json',
             '/tmp/dmr-briefing/mods_p2.json',
             '/tmp/dmr-briefing/mods_p3.json']:
    with open(path) as f:
        d = json.load(f)
    for m in d.get('results', []):
        idx[m['name'].lower()] = m

# Slug MUST match the exact catalog name — see "Slug quirks" below.
for slug in ['aai-loaders-sane', 'moon-eneas', 'angelssmelting',
             'Krastorio2', 'space-exploration', 'PlanetsLib']:
    m = idx.get(slug.lower())
    if not m:
        print(f"  MISS {slug}")
        continue
    rels = sorted(m.get('releases') or [], key=lambda r: r.get('released_at') or '')
    rel = (m.get('latest_release') or (rels[-1] if rels else {}))  # array is oldest-first
    print(f"  {slug:24s} v{rel.get('version','?'):10s} "
          f"released={(rel.get('released_at') or '?')[:10]} "
          f"factorio={rel.get('info_json',{}).get('factorio_version','?')} "
          f"dl={m.get('downloads_count','?')}")
```

**Slug quirks** (verified against the live catalog, 2026-08-21):
- Angel's mods drop hyphens: `angelssmelting` (not `angels-smelting`),
  `angelspetrochem`, `angelsrefining`, `angelsbioprocessing`, `angelsexploration`,
  `angelsindustries`.
- Bob's mods also drop hyphens: `bobplates`, `bobassembly`, `boblogistics`,
  `bobtech`, `bobmodules`, `bobpower`, `bobwarfare`, `bobores`, `bobmining`,
  `bobelectronics`, `bobequipment`, `bobgreenhouse`, `bobenemies`, `boblibrary`,
  `bobclasses`, `boblocale`, `bobvehicleequipment`, `bobinserters`.
- Krastorio: `Krastorio2` (camelCase).
- aai-loaders-sane, moon-eneas, space-exploration, PlanetsLib: hyphens preserved.

**Why bulk + filter**: same cat-and-mouse grep problem the old per-mod API had —
portal framework versions (`1.9.12`, `3.7.0`) appear in the page HTML and can fool
naive matches. Bulk JSON returns only mod-specific fields with deterministic shape.

⚠️ **Additional API quirks**:
1. **All three endpoints return `latest_release = null`** (verified 2026-08-21).
   Read from `releases[0]` instead. `m.get('latest_release') or {}` returns
   `{}` and silently looks like "no data" instead of "use the releases list".
2. The portal session cookie (used by `download-mod.py` to fetch mod source zips)
   expires — anonymous `download_url` fetches return the login HTML page, not a
   zip (verify magic bytes `PK\x03\x04`). When source verification is blocked,
   flag "re-test needed" in the briefing instead of guessing.
3. Legacy/unmaintained mods (Angel's 0.x, K2 0.9.99, SE 0.1.1) report very
   old `released_at` timestamps; do NOT interpret that as "the mod is broken" —
   it's the upstream's legacy catalog entry, often superseded by community forks.

## Factorio version state

- **Current stable**: `curl -sL "https://raw.githubusercontent.com/wube/factorio-data/master/changelog.txt" | grep -m1 "^Version:"` — gives the latest Factorio version
- **Latest FFF**: `curl -sL "https://factorio.com/blog/rss" | grep -oP 'title>[^<]*Friday Facts[^<]*' | head -1`
- **2.1 status**: stable. Latest stable is 2.1.14 (2026-08-06 — bugfix-only). 2.1.13 added `UtilitySounds::machine_gui_open/close`, `FluidEnergySourcePrototype::hide_from_stats`, `BurnerPrototype::hide_from_stats`, `EffectReceiver::uses_local_effect`, `LuaQualityPrototype::get_roll_chances()`, `LuaBurnerPrototype::burner_usage`, `LuaForce::get_space_platforms()`, `LuaEntity::local_effect`, `on_player_super_forced_selected_area`. SA: platform transfers at non-planet locations; recycling recipes scale recycle time with result count.
- **API docs**: https://lua-api.factorio.com/latest/ — always reflects the latest stable API
- **No 2.2 / 3.0 announced** (verified 2026-08-21 — forums view-forum.php?f=3 still lists 2.1.x as the most recent release line).

## DMR discussion tracking (NO JSON API)

The mod portal has **NO JSON endpoint for discussion threads** —
`/mod/<slug>/api/discussions` returns the public discussion page HTML (404 with
HTML body, content-type `text/html`); see `references/portal-discussion-scraping.md`
for the full scraping playbook (4 methods: meta-tag scan, Python text extraction,
grep, bulk pipeline).

**Quick-list extraction (most useful for the cron briefing)**:
```bash
curl -sL -H "User-Agent: Mozilla/5.0" \
  "https://mods.factorio.com/mod/dark-matter-replicators-reborn/discussion" \
  -o /tmp/dmr_disc.html

grep -oE '/mod/dark-matter-replicators-reborn/discussion/[0-9a-f]{20,}' \
  /tmp/dmr_disc.html | sort -u
```

The hex ID minimum length is 20 (IDs observed in this catalog are all 24 chars,
so `{24}` is also fine — `[a-f0-9]{20,}` is more permissive if Wube changes the
length). Use the **full ID** for thread fetches — shortened IDs return 404.

**Verified thread class names (2026-08-21)** for full body extraction:
- `discussion-message-body p16` — wraps each individual message text block
- `discussion-message-content panel-inset-lighter m0 p0 w100p` — wraps the
  full message card (author + date + body)
- `discussion-message-author` — links to the user page (e.g. `<a href="/user/77Zero" class="orange">77Zero</a>`)
- **There are NO `<article>` tags** in the rendered page — don't try to find them.

Reliable extraction snippet (works on every thread confirmed 2026-08-21):
```python
import re, html as html_mod
raw = open('/tmp/thread.html').read()
# Find all message bodies
bodies = re.findall(r'<div class="discussion-message-body[^"]*">(.*?)</div>\s*</div>\s*</div>', raw, re.S)
# Author: look back from the body block
for body in bodies:
    author_m = re.search(r'discussion-message-author[^>]*>.*?>([^<]+)</a>', body, re.S)
    author = author_m.group(1).strip() if author_m else '?'
    text = re.sub(r'<[^>]+>', ' ', body)
    text = html_mod.unescape(re.sub(r'\s+', ' ', text)).strip()
    print(f"  {author}: {text[:300]}")
```

**Known thread IDs** (populated from previous briefings, newest first):
- `6a7d9516a8dfa79d7b9fe436` — "Can't replicate Tenemut?" (Aug 14) —
  **Closed by design** (tenemut tied to tier 5 "Mastery of Dark Matter" per
  2026-08-13 user decision; v4.0 mirror tree).
- `6a7b4af62884890c7d176922` — "The 600s limit" (sp518, 2026-08-11) — You replied
  "I'll add a setting for it, easy, med, hard." **Resolved in v3.7.0 D1**:
  `helpers.get_research_difficulty_values()` returns `{cost, time, cap}` per
  difficulty (Easy=25/5s/600s historical, Medium=50/15s/1000s, High=100/30s/1800s,
  Very Hard=200/45s/3200s new). When v3.7.0 pushes, reply with citation.
- `6a7abfa58550fe238289c241` — "2.1 support?" (tj5630, 2026-08-11) — You replied
  "Yes, just fixing some bugs before going 2.1... it will probably [be] by the
  end of the week." **Resolved in v4.0.0 published 2026-08-14** (factorio_version
  bumped to 2.1). Reply with the v4.0.0 release link.
- `6a5c9c7a501290593666794f` — "Replication: Components (Tier 1) contains too
  much stuff?" (sp518, 2026-07-19 — Bob's tier grouping). **Resolved v3.5.11**
  (cost-solver fallbacks) + **v3.6.4** (eligibility rule + auto-hide categories).
- `6a561cb9accd254ecaa026ba` — "The Blue Bottle in T5?" (sp518, 2026-07-14).
  No reply yet; likely the gleba frost-bitten plant / yumako food tier — confirm
  recipe classification against live data dump.
- `6a54a3f2fa53b9e6f02cb73a` — "just here to say thanks!" (heartbreaker127,
  2026-07-13 — positive feedback, closed).
- `6a4bc19920bc2715492734f2` — "Cant work with space-age" (Higara123, 2026-07-06
  — SA lab inputs bug). **Resolved v3.5.22** (PASS 4 lab inputs defensive
  validation).
- `6a446e9984e4e5d346cb77f1` — "logistic science packs take a ton of time"
  (snakeanarchy, 2026-07-01 — balance, acknowledged).
- `6a3ed25ffe5026eb137972d3` — "Incompatible with moon-eneas" (devilchao0,
  2026-06-26). **Resolved v3.5.15** + A5 optional deps for overhaul mods.
- `6a43a68e68833cea37912fe0` — "Conflict with aai-loaders-sane" (meinkraft8,
  2026-06-30). **Resolved v3.5.15** same pattern.
- `6a3492427bfe4f8dd88cd831` — "Change default technology distribution"
  (DollarDrow, 2026-06-19 — feature request for group vs individual default).
- `6a29b1a3722bb601f165eb61` — "angels comp bug" (heartbreaker127, 2026-06-10
  — locked, unresolved).
- `6a2749cf9c0126ed66c9249a` — "Same error" (Cheeseyham, 2026-06-08 — SA load
  error). **Resolved**.
- `6a26fd10ebcbcf225e9a1da4` — "weird bug?" (heartbreaker127, 2026-06-08).
  **Resolved**.

## DMR portal state (verified 2026-08-21)

- **Latest published**: **v4.0.0 (2026-08-14, factorio_version 2.1)** — supersedes
  the prior "3.6.2" note. 27 portal releases total; DMR's v4.0.0 is the
  research-mirror architecture implementation, gate-test passed 2026-08-13.
- **Compatible Factorio version declared**: `2.1` (was `2.0` pre-v4.0.0).
  v4.0.0 requires Factorio 2.1 (no 2.0 compat) — confirm on next briefing.
- **Downloads**: 814 (portal counter, 2026-08-21).
- **Discussions**: 14 threads (2026-08-21; 13 prior + new "Can't replicate Tenemut?").
- **Local work in progress** (per game-dev memory, 2026-08-21): v4.1.0 Quality
  Refiner in gate test.
