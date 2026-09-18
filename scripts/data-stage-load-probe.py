#!/usr/bin/env python3
"""Data-stage load probe for a Factorio mod, without launching Factorio.

Surfaces runtime errors that data.lua's safe_require swallows (pcall+log)
and which later appear as misleading assignID failures. Run from the Docker
sandbox after `pip install --user --break-system-packages lupa`.

Usage:
    python3 data-stage-load-probe.py /path/to/mod  [data.lua data-updates.lua ...]

Mocks the globals a Factorio data-stage file expects. Game prototype libs
(assembler2pipepictures, pipecoverspictures, resource-autoplace, ...) are mocked
as empty-returning — their ABSENCE in the probe is a FALSE POSITIVE, not the
real error. Verify against wube/factorio-data that the real game provides them
before trusting a probe failure on those lines.
"""

import sys
import lupa
from lupa import LuaRuntime

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    mod_dir = sys.argv[1].rstrip("/")
    files = sys.argv[2:] or ["data.lua", "data-updates.lua", "data-final-fixes.lua"]

    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(f"package.path = '{mod_dir}/?.lua;' .. package.path")

    # Preload helper modules the mod requires (extend as needed)
    import os
    preloads = {}
    for rel in ("defines", "lib.helpers"):
        p = os.path.join(mod_dir, rel.replace(".", "/") + ".lua")
        if os.path.exists(p):
            with open(p) as f:
                preloads[rel] = f.read()
    for name, src in preloads.items():
        lua.execute(f"package.preload['{name}'] = function() {src} end")

    # Mock globals
    lua.globals().settings = lua.eval("{}")
    lua.globals().settings.startup = lua.eval("{}")
    lua.globals().data = lua.eval("{}")
    lua.globals().data.raw = lua.eval("{}")
    lua.globals().mods = lua.eval("{}")
    lua.globals().log = lambda *a: print("[log]", " ".join(str(x) for x in a))
    lua.globals().data.extend = lambda *a: None
    # Game prototype libs (false positives if the probe fails on these)
    for name in ("assembler2pipepictures", "assembler3pipepictures",
                 "assembler4pipepictures", "pipecoverspictures"):
        lua.globals()[name] = lambda: lua.eval("{}")
    lua.globals().circuit_connector_definitions = lua.eval("{}")
    lua.execute("defines = { direction = { north=0, east=2, south=4, west=6 } }")

    ok_all = True
    for f in files:
        path = os.path.join(mod_dir, f)
        if not os.path.exists(path):
            print(f"❌ {f}: file not found")
            ok_all = False
            continue
        code = f"""
        local chunk = loadfile('{path}')
        local ok, err = xpcall(chunk, function(e) return debug.traceback(e, 2) end)
        if not ok then print('❌ {f}:\\n' .. tostring(err)) else print('✅ {f}: OK') end
        """
        lua.execute(code)

    sys.exit(0 if ok_all else 1)

if __name__ == "__main__":
    main()
