#!/usr/bin/env python3
"""portal-state-check.py -- what is actually published vs what the repo claims.

    python3 scripts/portal-state-check.py <mod-source-dir> [--zip-dir DIR] [--name MODNAME]

Truth hierarchy, highest first:
  1. https://mods.factorio.com/api/mods/<name>   players' reality (public, no auth)
  2. the built zip: info.json version + file list
  3. the source tree: info.json + changelog.txt top block
  4. ROADMAP / README / FAQ / portal-description prose  -- snapshots, never facts

Prints one line per source, then a DRIFT line per disagreement, so a
"let's review the roadmap" session starts from the artifacts instead of the doc.
Reports only: exit code is always 0.
"""
import argparse
import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path


def portal_state(name):
    url = "https://mods.factorio.com/api/mods/{}".format(name)
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            data = json.load(response)
    except Exception as exc:                     # offline / typo in the name
        return None, "portal unreachable ({})".format(exc)
    releases = data.get("releases") or []
    if not releases:
        return None, "portal returned no releases"
    last = releases[-1]
    return {
        "version": last.get("version"),
        "released_at": last.get("released_at"),
        "releases": len(releases),
        "downloads": data.get("downloads_count"),
        "file_name": last.get("file_name"),
    }, None


def file_version(path):
    try:
        return json.loads(path.read_text()).get("version")
    except Exception as exc:
        return "unreadable ({})".format(exc)


def changelog_top_version(path):
    try:
        text = path.read_text(errors="replace")
    except Exception:
        return None
    match = re.search(r"^Version:\s*(\S+)", text, re.M)
    return match.group(1) if match else None


def zip_facts(zpath):
    """-> (root, info.json version, file count). The zip root is the mod NAME
    (no _N working-folder suffix and no version in the inner path)."""
    try:
        with zipfile.ZipFile(zpath) as zf:
            names = zf.namelist()
            roots = {n.split("/", 1)[0] for n in names if "/" in n}
            root = sorted(roots)[0] if len(roots) == 1 else "<mixed: {} roots>".format(len(roots))
            version = None
            try:
                version = json.loads(zf.read("{}/info.json".format(root))).get("version")
            except Exception:
                pass
            return root, version, len(names)
    except Exception as exc:
        return None, "unreadable ({})".format(exc), 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir")
    parser.add_argument("--zip-dir",
                        help="directory holding the built zips (default: the source dir's parent)")
    parser.add_argument("--name", help="portal mod name (default: info.json 'name')")
    args = parser.parse_args()

    src = Path(args.source_dir).resolve()
    info_path = src / "info.json"
    if not info_path.exists():
        sys.exit("no info.json under {}".format(src))

    name = args.name or json.loads(info_path.read_text()).get("name")
    local_ver = file_version(info_path)
    change_ver = changelog_top_version(src / "changelog.txt")

    print("MOD        {}".format(name))
    print("SOURCE     {}".format(src))
    print("LOCAL      info.json={}  changelog_top={}".format(local_ver, change_ver))

    pub, err = portal_state(name)
    if err:
        print("PORTAL     {}".format(err))
    else:
        print("PORTAL     latest={}  releases={}  downloads={}  at={}".format(
            pub["version"], pub["releases"], pub["downloads"], pub["released_at"]))

    zip_dir = Path(args.zip_dir).resolve() if args.zip_dir else src.parent
    zips = sorted(zip_dir.glob("{}_*.zip".format(name)), key=lambda p: p.stat().st_mtime)
    zip_ver = None
    if zips:
        latest = zips[-1]
        root, zip_ver, count = zip_facts(latest)
        print("ZIP        {}  root={}  info.json={}  files={}".format(
            latest.name, root, zip_ver, count))
    else:
        print("ZIP        none matching {}_*.zip in {}".format(name, zip_dir))

    # Prose freshness: anything mtime-older than the newest source file has not re-checked itself.
    newest_src = max((p.stat().st_mtime for p in src.rglob("*") if p.is_file()), default=0)
    for doc in ("ROADMAP.md", "FAQ.md", "README.md", "mod-portal-description.md"):
        path = src / doc if (src / doc).exists() else src.parent / doc
        if not path.exists():
            continue
        mtime = path.stat().st_mtime
        print("DOC        {:<26} {}".format(doc, "STALE?" if mtime < newest_src else "ok"))

    if not err and pub["version"] != local_ver:
        print("DRIFT      portal={} != info.json={}  (published?)".format(
            pub["version"], local_ver))
    if local_ver != change_ver:
        print("DRIFT      info.json={} != changelog top={}".format(local_ver, change_ver))
    if zip_ver is not None and zip_ver != local_ver:
        print("DRIFT      zip={} != info.json={}  (rebuild before publishing)".format(
            zip_ver, local_ver))
    print("REPORT ONLY -- exit 0; every fix is a hand decision.")


if __name__ == "__main__":
    main()
