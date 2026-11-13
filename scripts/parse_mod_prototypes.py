#!/usr/bin/env python3
"""Bulk static analysis of Factorio mod zips: extract item/recipe prototypes and
resolve produce/consume edges (static tables + dynamic bobmods.lib.recipe.* calls).

Usage:
    python3 parse_mod_prototypes.py [mod1.zip mod2.zip ...]

Default target mods: Bob's core set (bobores/bobmining/boblogistics/bobinserters).
Recipes are cross-referenced across ALL zips in the modlist directory, so
consumption by other mods (and base-game recipe names referenced dynamically)
is captured.

Output: JSON at /tmp/bob_step_items.json with:
  items_step            — suspicious items (parts-subgroup OR name-pattern match)
                          with producido_por/consumido_por/hidden
  subgroups_interesantes— subgroup -> [items] for bob-*/parts subgroups
  items_bob_subgroup    — ALL items in bob-*/parts subgroups (name+subgroup)
  patron_matches        — pattern -> [items]
  stats

Read-only; never modifies the zips. Verified against bobores_2.1.2,
bobmining_2.1.0, boblogistics_2.1.1, bobinserters_2.0.3 (2026-08-11).
"""
import zipfile, re, json, os, sys

MODLIST = "~/projects/Factorio-Modding/dark-matter-replicator/current-modlist"
DEFAULT_TARGETS = ["bobores_2.1.2.zip", "bobmining_2.1.0.zip",
                   "boblogistics_2.1.1.zip", "bobinserters_2.0.3.zip"]
PATTERNS = ["crushed", "chunk", "processed", "intermediate", "part",
            "gear-wheel", "bearing", "projectile", "warhead"]
OUT = "/tmp/bob_step_items.json"

TYPE_RE = re.compile(r'type\s*=\s*["\'](\w[\w-]*)["\']')
NAME_RE = re.compile(r'name\s*=\s*["\']([^"\']+)["\']')
STR_RE = re.compile(r'["\']([^"\']+)["\']')


def sanitize(text):
    """Copy of text with string literals and -- comments blanked (same length)."""
    n = len(text)
    out = list(text)
    i = 0
    while i < n:
        c = text[i]
        if c in ('"', "'"):
            q = c
            j = i + 1
            while j < n:
                if text[j] == '\\':
                    j += 2
                    continue
                if text[j] == q:
                    break
                j += 1
            for k in range(i, min(j + 1, n)):
                out[k] = ' '
            i = j + 1
        elif c == '-' and i + 1 < n and text[i + 1] == '-':
            j = text.find('\n', i)
            if j == -1:
                j = n
            for k in range(i, j):
                out[k] = ' '
            i = j
        else:
            i += 1
    return ''.join(out)


def enclosing_block(text, pos):
    """Return (start, end) of the { ... } table block containing pos in sanitized text."""
    depth = 0
    i = pos
    start = None
    while i >= 0:
        c = text[i]
        if c == '}':
            depth += 1
        elif c == '{':
            if depth == 0:
                start = i
                break
            depth -= 1
        i -= 1
    if start is None:
        return None
    depth = 0
    for j in range(start, len(text)):
        c = text[j]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return (start, j + 1)
    return None


def balanced_value(seg, vstart):
    s = seg[vstart:].lstrip()
    if not s:
        return None
    if s[0] == '{':
        depth = 0
        for j, c in enumerate(s):
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return s[:j + 1]
        return None
    m = re.match(r'[^,\n}]+', s)
    return m.group(0).strip() if m else None


def key_value(block, key):
    m = re.search(r'(?m)^\s*' + key + r'\s*=\s*', block)
    if not m:
        return None
    return balanced_value(block, m.end())


def top_level_keys(block):
    """Set of top-level key names in a prototype block.
    NOTE: block includes outer braces -> keys sit at depth 1; skip outer '{'/'}'."""
    keys = set()
    depth = 0
    i = 1  # skip outer '{'
    n = len(block) - 1
    while i < n:
        c = block[i]
        if c == '{':
            depth += 1; i += 1; continue
        if c == '}':
            depth -= 1; i += 1; continue
        if depth == 0:
            m = re.match(r'\s*([A-Za-z_]\w*)\s*=\s*', block[i:])
            if m:
                keys.add(m.group(1))
                i += m.end()
                continue
        i += 1
    return keys


def parse_item(block):
    nm = NAME_RE.search(block)
    if not nm:
        return None
    keys = top_level_keys(block)
    # ingredient entries {type="item", name="X", amount=N} are NOT item prototypes
    if 'amount' in keys or 'type' not in keys:
        return None
    sub = None
    m = re.search(r'subgroup\s*=\s*["\']([^"\']+)["\']', block)
    if m:
        sub = m.group(1)
    flags = []
    fv = key_value(block, 'flags')
    if fv:
        flags = STR_RE.findall(fv)
    return {'name': nm.group(1), 'subgroup': sub, 'flags': flags,
            'hidden': 'hidden' in flags}


def parse_entry_components(value):
    """From ingredients/results table value -> list of (type, name).
    Handles {type="item", name="X", amount=N} and {"X", N} short form.
    NOTE: strip the table's outer braces first or the whole table parses
    as a single entry."""
    out = []
    if not value:
        return out
    if value[0] == '{' and value[-1] == '}':
        value = value[1:-1]
    depth = 0
    n = len(value)
    entries = []
    cur_start = None
    for j, c in enumerate(value):
        if c == '{':
            if depth == 0:
                cur_start = j
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0 and cur_start is not None:
                entries.append(value[cur_start:j + 1])
    for e in entries:
        m = re.search(r'type\s*=\s*["\']([\w-]+)["\']', e)
        nm = NAME_RE.search(e)
        if nm and (m is None or m.group(1) in ('item', 'fluid', 'recipe', 'module')):
            out.append((m.group(1) if m else 'item', nm.group(1)))
        elif not m:
            sm = STR_RE.match(e)
            if sm:
                out.append(('item', sm.group(1)))
    return out


def parse_recipe(block):
    nm = NAME_RE.search(block)
    if not nm:
        return None
    ing = key_value(block, 'ingredients')
    res = key_value(block, 'results')
    if res is None:
        r2 = re.search(r'result\s*=\s*["\']([^"\']+)["\']', block)
        res_items = [r2.group(1)] if r2 else []
    else:
        res_items = [n for t, n in parse_entry_components(res) if t == 'item']
    ing_items = [n for t, n in parse_entry_components(ing)] if ing else []
    return {'name': nm.group(1), 'ingredients': ing_items, 'results': res_items}


def dynamic_recipe_edges(text):
    """Scan for bobmods.lib.recipe.add_ingredient/add_result/replace_*/set_* calls.
    Yields (recipe_name, item_name, kind) where kind in {'consume','produce'}.
    Bob's wires most part consumption through these runtime calls, not static
    ingredients tables. set_ingredients takes a whole table (yield each name)."""
    for fn, kind in (('add_ingredient', 'consume'), ('remove_ingredient', 'consume'),
                     ('replace_ingredient', 'consume'), ('set_ingredient', 'consume'),
                     ('set_ingredients', 'consume'),
                     ('add_result', 'produce'), ('remove_result', 'produce'),
                     ('replace_result', 'produce')):
        pat = re.compile(r'recipe\.' + fn + r'\s*\(')
        for m in pat.finditer(text):
            depth = 0
            j = m.end() - 1
            while j < len(text):
                c = text[j]
                if c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            args = text[m.end():j]
            rm = re.match(r'\s*["\']([^"\']+)["\']', args)
            if not rm:
                continue
            rname = rm.group(1)
            rest = args[rm.end():]
            if fn == 'set_ingredients':
                for im in re.finditer(r'name\s*=\s*["\']([^"\']+)["\']', rest):
                    yield (rname, im.group(1), fn, kind)
                continue
            im = re.search(r'name\s*=\s*["\']([^"\']+)["\']', rest)
            if im:
                iname = im.group(1)
            else:
                sm = re.search(r'["\']([^"\']+)["\']', rest)
                iname = sm.group(1) if sm else None
            if iname:
                yield (rname, iname, fn, kind)


def lua_files(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            if info.filename.endswith('.lua'):
                try:
                    yield info.filename, z.read(info).decode('utf-8', errors='replace')
                except Exception:
                    pass


def scan_blocks(path, ptype, parse_fn, acc):
    found = 0
    for fname, content in lua_files(path):
        san = sanitize(content)
        for m in TYPE_RE.finditer(content):
            if m.group(1) != ptype:
                continue
            block = enclosing_block(san, m.start())
            if block is None:
                continue
            # slice ORIGINAL text by sanitized indices (strings intact)
            parsed = parse_fn(content[block[0]:block[1]])
            if parsed is None:
                continue
            parsed['file'] = fname
            acc.append(parsed)
            found += 1
    return found


def main():
    targets = sys.argv[1:] or DEFAULT_TARGETS
    items = []
    recipes = []

    for mod in targets:
        path = os.path.join(MODLIST, mod)
        before = len(items)
        scan_blocks(path, 'item', parse_item, items)
        print(f"[items] {mod}: {len(items) - before}")

    all_zips = sorted(f for f in os.listdir(MODLIST) if f.endswith('.zip'))
    for mod in all_zips:
        path = os.path.join(MODLIST, mod)
        before = len(recipes)
        scan_blocks(path, 'recipe', parse_recipe, recipes)
        if len(recipes) > before:
            print(f"[recipes] {mod}: {len(recipes) - before}")

    items_by_name = {}
    for it in items:
        items_by_name.setdefault(it['name'], it)
    recipes_by_name = {}
    for r in recipes:
        recipes_by_name[r['name']] = r

    produces = {}
    consumes = {}
    for rname, r in recipes_by_name.items():
        for res in r['results']:
            produces.setdefault(res, []).append(rname)
        for ing in r['ingredients']:
            consumes.setdefault(ing, []).append(rname)

    # dynamic edges: DON'T filter by "recipe exists in scanned zips" — Bob's
    # tier-1 parts are consumed by BASE-GAME recipes (construction-robot,
    # logistic-robot) which aren't in the modlist.
    for mod in all_zips:
        path = os.path.join(MODLIST, mod)
        for fname, content in lua_files(path):
            for rname, iname, fn, kind in dynamic_recipe_edges(content):
                if fn.startswith('remove'):
                    continue
                target = consumes if kind == 'consume' else produces
                if rname not in target.get(iname, []):
                    target.setdefault(iname, []).append(rname)

    matched = []
    for it in items_by_name.values():
        pats = [p for p in PATTERNS if p in it['name']]
        if pats:
            it2 = dict(it)
            it2['patrones'] = pats
            matched.append(it2)
    matched.sort(key=lambda x: x['name'])

    # suspicious = parts-subgroup items (criterion 1) OR name-pattern matches (2)
    suspect_names = set()
    for it in items_by_name.values():
        sub = it['subgroup'] or ''
        if 'part' in sub.lower():
            suspect_names.add(it['name'])
    for it in matched:
        suspect_names.add(it['name'])

    items_step = []
    for nm in sorted(suspect_names):
        it = items_by_name.get(nm)
        if it is None:
            continue
        items_step.append({
            'name': nm,
            'subgroup': it['subgroup'],
            'producido_por': sorted(set(produces.get(nm, []))),
            'consumido_por': sorted(set(consumes.get(nm, []))),
            'hidden': it['hidden'],
            'patrones': [p for p in PATTERNS if p in nm],
            'flags': it['flags'],
        })

    subgroup_items = {}
    all_subgroups = {}
    for it in items_by_name.values():
        sub = it['subgroup']
        if sub:
            all_subgroups.setdefault(sub, []).append(it['name'])
            if sub.startswith('bob') or 'part' in sub.lower():
                subgroup_items.setdefault(sub, []).append(it['name'])
    for k in subgroup_items:
        subgroup_items[k] = sorted(subgroup_items[k])

    items_bob = [{'name': it['name'], 'subgroup': it['subgroup']}
                 for it in sorted(items_by_name.values(), key=lambda x: x['name'])
                 if it['subgroup'] and (it['subgroup'].startswith('bob') or 'part' in it['subgroup'].lower())]

    result = {
        'mods_analizados': targets,
        'items_step': items_step,
        'subgroups_interesantes': subgroup_items,
        'items_bob_subgroup': items_bob,
        'patron_matches': {p: sorted([it['name'] for it in matched if p in it['name']]) for p in PATTERNS},
        'stats': {
            'items_totales': len(items_by_name),
            'recipes_totales_modlist': len(recipes_by_name),
            'items_step_count': len(items_step),
        },
    }
    with open(OUT, 'w') as f:
        json.dump(result, f, indent=1, ensure_ascii=False)
    print(f"\nWROTE {OUT}")
    print("items_step:", len(items_step))
    print("patron_matches:", json.dumps({p: len(v) for p, v in result['patron_matches'].items()}))
    print("stats:", json.dumps(result['stats']))


if __name__ == '__main__':
    main()
