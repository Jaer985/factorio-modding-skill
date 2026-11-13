# DMR — Release push & pre-push privacy verification

_From the v3.6.0 release session (2026-08-11). Covers pushing the mod source to
GitHub and the mandatory privacy scan the user asked for ("verifica que no se
suba nada privado") before any upload — repo push OR mod portal zip._

## Pre-push privacy scan (MANDATORY before any upload)

The user explicitly requires verifying nothing private ships. Run this against
BOTH the git staging area AND the zip contents. Scriptable pattern:

```python
# Check repo or zip contents for leaks
sensitive_pats = ['github_pat_', 'ghp_', 'GITHUB_TOKEN', 'GITHUB_PERSONAL',
                  '~', 'servicesjmtech', 'password', 'api_key', 'secret']
name_pats = ['.env', '.pem', '.key', '.ds_store', 'thumbs.db']
# For each file (text): content scan for sensitive_pats
# For each file name: check name_pats
```

For the zip, also verify:
- Top-level root is exactly `dark-matter-replicators-reborn/` (portal convention)
- NO internal dev docs (`research/`, `specs/` — SDD artifacts, PRDs, audit notes).
  These were found inside the zip in v3.6.0 prep because the build script only
  excluded `.DS_Store`/`Thumbs.db`. Fix: add `'research', 'specs'` to
  `exclude_patterns` in the build script AND remove them from the git repo.
- `dmr-tests/` must stay OUT of the mod source dir (it lives at the repo
  parent level so it never packages) — verify it's not inside the zip.

Result to report: "NO LEAKS — repo clean" with the count of scanned files.

## GitHub token validation BEFORE push (avoid wasted push attempts)

Session lesson: three tokens were tried; the first was VALID but belonged to a
different account with read-only access; the next two returned 401. The push
failed with `remote: Permission to <owner>/<repo>.git denied to <token-owner>.`
Only AFTER the failure did we discover the token's permissions were pull-only.

**Pattern — validate token + repo permission FIRST:**

```bash
export GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | cut -d= -f2 | tr -d '\n\r')
# 1. Who owns the token?
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/user
#   → "login": "<account>" — compare with the repo owner
# 2. What permissions does it have on the TARGET repo?
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/<owner>/<repo>"
#   → "permissions": {"admin":..., "push":..., "pull":...}
#   push must be true; a fine-grained PAT must have Contents: Read and write
```

Diagnostics:
- `401 Bad credentials` → token invalid/expired/miscopied. Do NOT retry push.
- `403 Permission to X denied to Y` → token is VALID but owned by a different
  account (Y ≠ repo owner) or lacks write scope. Check `permissions.push`.
- `login: None` + `"message": "Bad credentials"` → same as 401.

Store the working token in `~/.hermes/.env` as `GITHUB_TOKEN=...` (the
github-auth skill reads it from there). Note: a token that works for API read
may still lack push on the target repo — the `/repos/<owner>/<repo>`
permissions check is the only reliable gate.

## Manual repo sync when rsync is unavailable (PITFALL)

The rsync form of the same preserve-set rule (plus the post-sync `git status`
gate) lives in `audit-and-release.md` → "Sync source into a clone — never let
cleanup delete .git"; use it whenever rsync exists. Fallback for hosts without
`rsync`, where a Python mirror script must be careful:

- **Copy phase**: walk source, copy every file (overwrite) into the clone.
- **Cleanup phase**: for top-level entries in the clone, delete only files that
  are NOT in `src_top` AND NOT in `preserve` (e.g. `LICENSE`, `thumbnail.png`,
  `.git`). The first implementation deleted ALL top-level files except preserve
  (including freshly-copied source files) because the top-level branch didn't
  compare against `src_top` — it deleted unconditionally. Always re-list after
  sync and assert key files exist (`info.json`, `changelog.txt`, `data.lua`,
  `settings.lua`, `authors.txt`, `FAQ.md`).

## Working push script pattern (v4.2.0, verified 2026-08-23)

The full GitHub release push fits a single /tmp bash script (write with
write_file, run once, DELETE after — the token ends up embedded in the clone's
`.git/config`): validate token via API → `rm -rf` old clone → clone with
`https[REDACTED]github.com/...` → wipe tree except `.git`
(`find . -mindepth 1 -maxdepth 1 -not -name '.git' -exec rm -rf {} +`) →
`cp -a "$SRC"/. .` → `rm -rf specs research __pycache__ dmr-tests` + delete
`*.pyc` → assert key files exist (info.json, changelog.txt, data*.lua,
settings.lua, authors.txt, LICENSE, thumbnail.png, ROADMAP.md) → commit with
`-c user.name=Jaer985 -c user.email=jaer985@users.noreply.github.com` → tag
`vX.Y.Z` → `push origin main --tags --force` → verify `git ls-remote` →
`rm -rf` the clone. v4.2.0 pushed this way: main + tag at `07af544`.

Note: ROADMAP.md IS committed to the repo (it always has been) but is EXCLUDED
from the portal zip — different artifacts, different rules.

## Keep the clone or delete it?

- Token embedded in the clone's `.git/config` (the script pattern above) →
  **delete the clone once the push is verified**; that is the only reason that
  pattern wipes it.
- Push through the `gh` CLI / credential helper → no secret is stored in the
  clone, so **KEEP it** as the standing sync dir (sits beside the source as
  `github-sync/`): the next release is one `rsync` + `git add -A` + commit instead
  of clone + wipe + copy.
- Never embed a token in a clone you intend to keep.

## Commit message lives OUTSIDE the working tree

Write the message into the scratch dir (`~/.hermes/cache/scratch/…`) and pass it
with `git commit -F`. A message file written inside the clone gets swept up by
`git add -A` and ships in the commit — move it out before staging if it was
written there.

## Post-push: read the CONTENT back, not just the ref

`git ls-remote` / a clean `git push` exit 0 only proves the ref moved — it says
nothing about what is ON `main`. The DMR repo is public, so the receipt needs no
auth:

```bash
gh api repos/<owner>/<repo>/commits/main --jq '.sha[0:7] + "  " + .commit.message[0:70]'
gh api repos/<owner>/<repo>/contents/info.json --jq '.content' | base64 -d   # version + factorio_version
gh api repos/<owner>/<repo>/contents/changelog.txt --jq '.content' | base64 -d | head -3
gh api repos/<owner>/<repo>/git/trees/main?recursive=1 --jq '[.tree[]|select(.type=="blob")]|length'
```

Assert the commit subject, the `info.json` version, the top `Version:` block of
the changelog, and the blob count against what you intended to publish. Local
`git status` proves nothing about the remote — the API response is the receipt.

## Mod portal credentials are separate from GitHub (v4.2.0)

Uploading to mods.factorio.com requires `FACTORIO_PORTAL_USER` +
`FACTORIO_PORTAL_TOKEN` (profile → upload token). They were NOT in `.env`; the
session ended with everything else done and the user doing the final upload
manually with the prepared zip. If you hit missing portal creds: prepare the zip
fully (parity-checked, privacy CLEAN, accumulated changelog), then hand the user
the absolute path — don't block or improvise auth.

## Version-bump release pattern (v3.6.0)

See SKILL.md "Version bump: minor jump with accumulated changelog" — plus:
when bumping a release that will be pushed to GitHub, first check the REMOTE
state (`curl https://raw.githubusercontent.com/<owner>/<repo>/main/info.json`)
— the remote can be far behind local (remote was 3.2.1 when local was 3.6.0),
which means the push is a full content replacement, not an incremental diff.
