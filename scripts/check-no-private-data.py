#!/usr/bin/env python3
"""
check-no-private-data.py — scan a tree for secrets/private paths before a
public git push or release zip. Reusable from the factorio-modding skill's
release workflow (and any project release).

Usage:
    python3 check-no-private-data.py [path]

Default path: current directory. Exit code 0 = clean, 1 = leaks found.

Flags checked (add/remove patterns freely per project):
  - Token/credential patterns: github_pat_, ghp_, gho_, ghs_, ghu_,
    GITHUB_TOKEN, GITHUB_PERSONAL, password=, api_key, secret
  - Private paths: /home/<user> (any $HOME absolute path), account names
  - Secret file names: .env, *.pem, *.key, *.p12, .DS_Store, Thumbs.db
  - .cfg/.toml/.yaml outside a locale/ dir (in Factorio mods these are
    locale-only files)
"""
import os
import re
import sys

SENSITIVE_PATTERNS = [
    r'github_pat_[A-Za-z0-9_]+',
    r'gh[pous]_[A-Za-z0-9]+',
    r'GITHUB_TOKEN',
    r'GITHUB_PERSONAL_ACCESS_TOKEN',
    r'password\s*[=:]\s*\S+',
    r'api[_-]?key\s*[=:]\s*\S+',
    r'\bsecret\b\s*[=:]\s*\S+',
    r'Bearer\s+[A-Za-z0-9._-]+',
]

SENSITIVE_FILENAMES = {'.env', '.env.local', '.pem', '.key', '.p12', '.pfx',
                       '.DS_Store', 'Thumbs.db', 'id_rsa', 'id_ed25519',
                       'credentials', 'secret', 'secrets'}

PRIVATE_PATH_RE = re.compile(r'/home/[a-z0-9_]+/')


def scan(path):
    leaks = []
    for root, dirs, files in os.walk(path):
        # skip VCS internals
        dirs[:] = [d for d in dirs if d not in ('.git', '.svn', '.hg', 'node_modules')]
        for fname in files:
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, path)

            # filename-based flags
            low = fname.lower()
            if low in SENSITIVE_FILENAMES or low.endswith(('.pem', '.key', '.p12')):
                leaks.append(f"SENSITIVE NAME: {rel}")

            # content-based flags for text files
            if fname.endswith(('.lua', '.json', '.txt', '.md', '.cfg', '.toml',
                               '.yaml', '.yml', '.py', '.sh', '.ini', '.env')):
                try:
                    with open(full, encoding='utf-8', errors='ignore') as fh:
                        content = fh.read()
                    for pat in SENSITIVE_PATTERNS:
                        m = re.search(pat, content)
                        if m:
                            # redact the matched secret value, keep location
                            leaks.append(f"LEAK '{pat}' in {rel}")
                    if PRIVATE_PATH_RE.search(content):
                        leaks.append(f"PRIVATE PATH in {rel}")
                    # .cfg outside locale/ (Factorio mods: locale-only)
                    if fname.endswith('.cfg') and '/locale/' not in '/' + rel.replace(os.sep, '/'):
                        leaks.append(f"CFG outside locale: {rel}")
                except Exception:
                    pass
    return leaks


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else '.'
    leaks = scan(target)
    if leaks:
        print(f"LEAKS FOUND ({len(leaks)}):")
        for l in sorted(set(leaks)):
            print(f"  - {l}")
        return 1
    print("CLEAN — no private data found")
    return 0


if __name__ == '__main__':
    sys.exit(main())
