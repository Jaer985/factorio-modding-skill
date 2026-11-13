#!/usr/bin/env python3
"""Download a Factorio mod zip from the mod portal using session cookie.

Usage:
    export FACTORIO_MOD_PORTAL_COOKIE="<session-value>"
    ./download-mod.py <mod-name> [output-dir]
"""
import json
import os
import sys
import urllib.error
import urllib.request

MOD_NAME = sys.argv[1] if len(sys.argv) > 1 else sys.exit(f"Usage: {sys.argv[0]} <mod-name> [output-dir]")
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "."

COOKIE = os.environ.get("FACTORIO_MOD_PORTAL_COOKIE")
if not COOKIE:
    print("Error: FACTORIO_MOD_PORTAL_COOKIE not set.", file=sys.stderr)
    print("Source it: source ~/.hermes/secrets/factorio-cookie-session.sh", file=sys.stderr)
    sys.exit(1)

# Get latest release
url = f"https://mods.factorio.com/api/mods/{MOD_NAME}"
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

releases = data.get("releases", [])
if not releases:
    sys.exit(f"No releases found for {MOD_NAME}")

r = releases[-1]
version = r["version"]
dl_path = r["download_url"]
print(f"{MOD_NAME} v{version}")

# Download
dl_url = f"https://mods.factorio.com{dl_path}"
dl_req = urllib.request.Request(dl_url)
dl_req.add_header("Cookie", f"session={COOKIE}")

os.makedirs(OUT_DIR, exist_ok=True)
outfile = os.path.join(OUT_DIR, f"{MOD_NAME}_{version}.zip")

with urllib.request.urlopen(dl_req) as resp, open(outfile, "wb") as f:
    f.write(resp.read())

# Verify via zip magic bytes (self-contained — avoids depending on the `file`
# binary, which may be missing in sandboxes). A login HTML page is returned
# when the session cookie is missing/expired (HTTP 403 is raised before this).
with open(outfile, "rb") as f:
    magic = f.read(4)
if magic == b"PK\x03\x04":
    size = os.path.getsize(outfile)
    print(f"OK: {outfile} ({size // 1024} KB)")
else:
    os.remove(outfile)
    print(f"FAIL: not a zip archive (magic={magic!r}) — cookie expired or login required", file=sys.stderr)
    sys.exit(1)
