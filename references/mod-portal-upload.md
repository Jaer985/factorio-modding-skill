# Publishing a release to the Factorio mod portal

## Flow (API key with `ModPortal: Upload Mods` usage)

1. `POST https://mods.factorio.com/api/v2/mods/releases/init_upload`
   - header `Authorization: Bearer <api key>`
   - form field **`mod` = mod name** (not the file)
   - → `{"upload_url": "https://uploads-nf.mods.factorio.com/upload/mod/token/<JWT>"}`
2. `POST <upload_url>` multipart, field **`file` = the zip** → `{"success": true}`

Ready-made script: `~/.hermes/scripts/dmr-portal-upload.py <zip> <mod-name>` (key file:
`~/.hermes/secrets/factorio-portal.key`, chmod 600).

## Pre-flight gate: assert the artifact identity in the SAME command as the upload

The uploader ships whatever bytes it is handed, and the tree can be rebuilt between the gate run and
the upload (a subagent chain still writing ships a half-edited file that fails to parse). So put the
asserts in the same shell invocation, before the script runs:

1. `sha256sum <zip>` == the sha256 recorded by the gate that tested this build — fail the command on
   mismatch rather than re-checking afterwards.
2. `unzip -p <zip> <mod>/info.json | grep '"version"'` == the version you mean to publish.
3. `unzip -p <zip> <mod>/changelog.txt | sed -n '2p'` == `Version: <same version>` — the changelog
   header is what players read, and a stale one stays invisible until they do.

Then run the uploader and read its two verdict lines: `init_upload: HTTP 200` followed by
`finish_upload … {"success":true}`.

## The trap that costs an hour: the upload token is a JWT

The `upload_url` contains a JWT (`eyJ…`). Hermes' secret-redaction layer masks JWT-shaped
strings in **tool output**, so a token that round-trips through the conversation comes back
elided (`.../token/eyJ1c2...imjE`) and the portal answers
`Forbidden: Invalid upload token, please refresh and try again`.

- Never split the flow across two tool calls (init in one, upload in the next) — the token dies.
- Do **both requests inside one process/script**, so the token never enters the transcript.
- If a response must be inspected, trust the *length*, not the string (192 chars = a real token).
- A response body that arrives elided is *not* proof of a server bug or a MITM: check
  `content-length` against the bytes received and the TLS issuer before chasing ghosts.

## Verifying the upload (do this — `success:true` is the server's word, not the portal's state)

- The public JSON API is **URL-cached**: `GET /api/mods/<name>` can keep serving the previous
  release for many minutes. Append a cache-buster (`?cb=1`) and it returns the truth.
- The upload is also processed **asynchronously**: even `/full` can list the previous latest for a
  few minutes after `finish_upload` answers `{"success":true}`. Poll `/full?cb=<fresh nonce>`
  (new nonce per attempt) until your zip's `sha1` shows up in a release; until a bounded wait
  expires, absence is processing lag, not a failed upload — `success:true` plus the matching sha1
  is what gets reported, never the page's first render.
- Proof the portal holds *your* bytes: `GET /api/mods/<name>/full?cb=2` → the release's `sha1`
  must equal `sha1sum <your local zip>`.
- The mod page (`/mod/<name>`) shows `Latest Version: <ver> (just now)`; the Downloads tab
  (`/mod/<name>/downloads`) lists version + game version. Download buttons are login-gated,
  so the API `sha1` is the practical byte-level check.
- Other `/api/v2/...` paths (mods, releases, edits) return 404 HTML — do not build on them.
- The public `/api/mods/<name>` response has **no `latest_release` field** — assert on `releases[-1]`
  (`version`, `released_at`, `sha1`, `info_json.factorio_version`) plus the release count, instead of
  a field that is not there.

## Updating the portal text fields (Mod details API)

`POST https://mods.factorio.com/api/v2/mods/edit_details` — multipart, `Authorization: Bearer <key>`,
field `mod` plus any of `title summary description faq category tags license homepage source_url
deprecated`. Requires an API key with the **`ModPortal: Edit Mods`** usage; one key can carry both
usages (a key with only Upload Mods answers `InvalidApiKey`/`Forbidden` here).

Script: `~/.hermes/scripts/portal-edit-details.py`

- `update <mod> <desc-file> <faq-file>` — pushes the repo's `mod-portal-description.md` and `FAQ.md`.

**`test <mod>` is also the pre-flight for any text edit**: it re-sends the current title, so it
proves whether the key carries the Edit Mods usage while touching nothing. An expired browser
session is irrelevant on this path — only discussion replies need one — and telling the user to
paste the text by hand when an API route exists is a self-inflicted extra step.

Verify: `GET /api/mods/<name>/full?cb=<nonce>` (the API is URL-cached — always bust it), normalize
CRLF and compare the stored `description` / `faq` to the local files; `/mod/<name>` and
`/mod/<name>/faq` render them for the public. Left alone deliberately: `category`, tags and license (no local source of truth; the mod's own
`info.json` keeps the owner's choice). `summary` is hand-maintained: the description's intro plus
the feature clause, ~340 chars — keep the two in step when the description changes.

## Still manual: anything inside the zip

The release stream (`info.json`, `changelog.txt`, thumbnail) has no edit path — those bytes only
change with a **new release**, so updating the in-game description means bumping the version and
uploading again. Portal text fields are covered by the Mod details API above.

## Announcing the release in Discord (bilingual, one canonical post)

Publishing does not end at the portal: the announcement post must name the version players just
received. One script owns it — `~/.hermes/scripts/dmr-release-announce.py`:

- `--check` — exit 0 when the post matches the portal's published version, exit 1 = **drift**, printing
  both sides. Run it after every upload; it is also the alert that tells you an upload happened
  elsewhere.
- `--post --en-file <en> --es-file <es>` — **rewrites the existing post in place** (one canonical
  announcement; never append a second), then reads the post back and confirms the version it carries.
- The bullet files are EN + ES blocks written from the `changelog.txt` entry: features / changes /
  bugfixes, each a `•` line. No version header — the post builds its own header plus the portal and
  changelog links.
- **Every bilingual deliverable must LABEL each language** (🇪🇸 / 🇬🇧 headings, or `[ES]`/`[EN]`
  prefixes) — the Discord announcement, the `changelog.txt` entry that ships in the zip, and the
  in-repo docs. Concatenating the ES block and the EN block with no separator is a DEFECT, not a
  style choice: neither readers nor later tooling can tell where one language ends. The scripts take
  separate `--en-file/--es-file` for exactly this reason; a third script that posts a changelog gets
  the same two labelled files, never one merged blob.
- After an upload, assert on the **whole release list**, not only `releases[-1]`: a same-day follow-up
  release can REPLACE the previous entry (the count stays flat and the superseded version disappears),
  so claim anything about the old version only after looking at the list.

Hard limit: the whole post must be ≤ 2,000 chars and the header + links eat ~400 of it, so the two
bullet sets together need ≈ 1,300 chars or less. The script **refuses** an over-limit post (exit 2,
reporting the exact count) instead of truncating — trim the bullets, never skip the check.

## Docs pass after every release (one sweep, same day)

A release that changes player-visible behaviour leaves stale claims behind in several places.
Sweep them in one pass, then commit so the repo does not lag the portal:

1. **Repo state lines** — the version/status block at the top of README + AGENTS (published
   version, gates run, checksum).
2. **ROADMAP** — status header + a closed entry: what shipped, the *measured* cause, the gate used.
3. **FAQ** — one question per user-visible behaviour change, naming the version it landed in.
4. **`mod-portal-description.md`** — the portal's Information tab, pushed via
   `portal-edit-details.py update` (and `summary` kept in step, ~340 chars).
5. **Profile knowledge file** — version, sha1, tag, and any procedure this release corrected.
6. **Docs-only commit** (`docs: ... for <version>`) pushed separately from the release commit.

Skipping the sweep is how the portal ends up describing an older mod than the zip it ships.

## Discussion replies: a different door than releases

A reply inside a `/mod/<name>/discussion` thread is not a release, and the release APIs above do
not cover it.

- **Verify the session BEFORE promising a post.** Fetch the page and confirm you are logged in
  (no `Log in` render). An expired cookie makes you anonymous while the page still renders, so
  "I posted" is only reportable after reading the thread back and seeing the reply there.
- **No endpoint → hand over the draft.** Discussion replies have no public-API path; give the
  user a ready-to-paste answer instead of improvising an upload route for a comment.
- Length and voice are governed by the `comment-writer` skill: one short plain sentence
  acknowledging the report, technical detail in the changelog and repo, not in the thread.
