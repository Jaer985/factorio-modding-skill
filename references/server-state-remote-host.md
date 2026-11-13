# Where the project lives — server vs laptop

Canonical inventory, written 2026-10-30 when the Factorio work was ported to a
second Hermes installation (the laptop). Read this **before** claiming anything
about project files, versions or published state when the working tree you are
in does not obviously contain them.

## Current split (2026-10-30, after the move)

| What | Where it runs now |
|---|---|
| The 5 Factorio skills | Windows desktop (`default` profile) |
| `factorio-morning-tech-briefing` | Windows desktop, job `d847e8444e36`, `0 10 * * 2,5`, deliver `telegram,discord` |
| Discord platform | Windows desktop; `#hermes` is a free-response channel (no mention needed) |
| Same job on the server | `6a440e5b5801` — **paused** (do not re-enable; two copies = two briefings) |
| Project tree | working copy `C:\Users\JAER\Documents\Projects\factorio\Factorio-Modding` (593 files, 229.512.547 B); `debian-server` keeps its copy as **backup** — never edit it in place, sync from Windows with `ssh debianserver 'tar cf - -C ~/projects Factorio-Modding' \| tar xf -` |

Cron runs on the desktop block `execute_code` and shell `-c` scripting (no user
present to approve), so a briefing job there must gather with web tools and
`read_file`/`search_files`, not local Python one-liners.

## The authoritative copy is on `debian-server`

Host `debian-server` (Debian, `192.168.1.5`, Tailscale `100.108.25.125`), user
`jaer`, Hermes home `~/.hermes`.

```
~/projects/Factorio-Modding/                    # 221 MB, source of truth
├── .hermes.md                       # project context file
├── MOD-RESEARCH-NOTES.md            # cross-mod research notes
├── dark-matter-replicator/          # the DMR mod
│   ├── AGENTS.md
│   ├── dark-matter-replicators-reborn_3/       # unpacked tree: info.json, lua/, locale/
│   ├── dark-matter-replicators-reborn_4.*.zip  # release artifacts (4.0.0 … 4.8.0)
│   ├── dumps/                      # data-raw-dump.json (`factorio --dump-data`)
│   ├── dmr-tests/                  # in-game test scenarios (behaviour gate)
│   ├── current-modlist/            # modlist for test runs
│   ├── research/                   # 70 MB: audits, v4x-audit, gate docs
│   ├── github-sync/                # 13 MB, the GitHub-published mirror
│   ├── archivados/                 # 23 MB of old versions
│   └── backups/
└── Richness-or-infinite/           # older second mod, 1.4.0
```

## What still works without the tree

- Portal API reads (versions, downloads, discussion threads) and changelog
  parsing — network only.
- Reading/writing Lua **if** the sources were synced or the zip was unpacked.
- Anything else — a release build, `dmr-tests`, `dumps/` audits, `portal-state-check.py`
  against local files — needs the tree.

## Getting the tree onto a second machine

Cheapest first:
1. `git clone` the mod's GitHub repo (`github-sync/` mirror). Gives Lua + locale,
   not the dumps, test scenarios or research notes.
2. Over the LAN: `rsync -a jaer@192.168.1.5:projects/Factorio-Modding/ ./` (SSH
   server is up on the host; the client machine needs a key or the password).
3. Regenerate what is missing locally: `factorio --dump-data` produces
   `dumps/data-raw-dump.json` (see `headless-engine-gate.md` for the invocation
   and the Windows path quirk).

**Rule**: the server copy stays canonical. Never silently build or publish from a
partial laptop tree — a divergent second copy is exactly the drift the release
ritual exists to catch. If a file is missing, say so and ask for a sync instead
of inventing its contents.

## Credentials — never travel

```
~/.hermes/secrets/factorio-cookie-session.sh    # portal cookie session
~/.hermes/secrets/factorio-cookie-session.txt   # same, plain text
~/.hermes/secrets/factorio-portal.key           # portal API key
```

Needed only to upload a release or read authenticated portal data. On another
machine: create a **new** API key on the portal (Profile → API keys) and store it
in that machine's `~/.hermes/secrets/`. Never send these through chat, never
commit them.

## Bot tokens are per installation

Each machine runs its **own** Telegram bot and its **own** Discord app. The same
token on two gateways makes them long-poll the same updates: messages split or
drop, both answer in the same channel. Moving a channel therefore means *removing*
it from the old machine, never duplicating it.

## Server-side automation (for reference)

| thing | where |
|---|---|
| cron `factorio-morning-tech-briefing` | default profile, id `6a440e5b5801`, `0 10 * * 2,5`, delivers `telegram:504791090` |
| its skill | `~/.hermes/skills/software-development/factorio-modding/` |
| sibling skills | `factorio-mod-research`, `factorio-mod-data-analysis`, `factorio-mod-prototype-parsing`, `dmr-category-tier-refactor` |
| gateways | systemd user units `hermes-gateway*.service` |
| WhatsApp bridges | `scripts/whatsapp-bridge/bridge.js --mode bot`, ports 3000 / 3100 / 3101 |

Cutover rule: the server job stays enabled until the new machine delivers a real
briefing; only then `hermes cron pause 6a440e5b5801`.
