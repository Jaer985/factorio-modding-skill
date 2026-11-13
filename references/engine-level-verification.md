# Engine-level verification: headless `--create` + probe mod

Any claim about a prototype field or runtime API behavior ("this field enables X", "entity type Y
supports Z") is verified on the real engine, headless, in ~2 minutes. Documentation is not evidence:
the wiki lags, and absence-of-field semantics (0 vs nil vs false) is where the bugs hide. Load when
about to assert that a prototype field or an entity API call does something.

## Procedure

1. **Throwaway probe mod in the scratch dir** (never inside the shipped tree, never in the zip).
   `info.json` with `factorio_version` matching the target, and a `control.lua` that only does
   `script.on_init`: create a surface, place the entity, call the API under test, then
   `log("[PROBE] " .. msg)`. The tag lands in `<write-data>/factorio-current.log`. Empty surfaces
   (`game.create_surface("probe")`) are fine and skip map-generation cost.
2. **Custom config + mod dir**: `--config cfg.ini` with
   `read-data=__PATH__executable__/../../data` and `write-data=<scratch>`; `--mod-directory mods`
   containing base + every dependency (quality, space-age, recycler, elevated-rails as needed) +
   your mod renamed `name_X.Y.Z` + the probe. Then:
   `factorio --config cfg.ini --mod-directory mods --create x.zip`. No world is generated, so it
   finishes in seconds.
3. **Always run an A/B**: once with the field/patch removed, once with it, in two scratch dirs.
   A single run cannot distinguish "the field does nothing" from "the test is wrong"; the failing
   baseline is what makes it a proof.
4. **Assert on the log, not the exit code** — `--create` exits 0 even when the probe errored or the
   mod failed to load. Grep `\[PROBE\]` and also grep the engine's error signature
   (`non-recoverable error`).
5. **Test the premise, then the fix**: reproduce the reported failure first, change, re-run. A
   probe that only runs on the fixed tree proves nothing about the bug it claims to fix.
6. **Cleanup**: delete the scratch dir; verify the shipped tree contains no probe files before
   building the release zip.

## Pitfalls

- **A connector object existing proves nothing about wire support.**
  `entity.get_or_create_connector()` returns an object even for entities with no circuit support;
  the only meaningful assertion is `connector.connect_to()` returning true AND
  `entity.get_circuit_network(...)` returning non-nil. Absent `circuit_wire_max_distance` on a
  prototype means distance 0: `connect_to()` fails silently (false return, nil error string) and the
  network reads nil while the connector still "exists". Never conclude support from existence.
- **Assert the surface you will actually use.** `set_circuit_condition` succeeding proves nothing
  about whether the player can see the setting in the GUI — if the entity can't render it, the
  feature is invisible. `set_enabled` / `set_recipe` returning an error string when the entity has
  no circuit network is the EXPECTED failure mode; assert the error text, not a bare boolean.
- **Wrong `circuit_connector_index` reads as a working-but-empty test.** Prototype connectors are
  numbered, and using the assembler index on an entity that declares a different one silently
  returns nil. Print the index you used next to the result.
- **Measure a suspected interaction before writing state for it.** A defensive flag that suppresses
  script behavior when a player "might have overridden" it adds state that can silently disable the
  feature forever, while the conflict it prevents may not exist. Run the interaction in the engine
  first (does changing a recipe by hand empty the machine's inventory? If yes, the script never sees
  the item it would have fought over) and delete the guard rather than ship it.

## Reference output shape

```
[PROBE] START
[PROBE] dmrsa-replicator-1 connect_to ok=true err=true a=true b=true
[PROBE] dmrsa-replicator-1 network=true
[PROBE] dmrsa-replicator-1 set_circuit_condition ok=true err=nil enabled_before=true
[PROBE] END
```

`ok=true err=true` = connect_to returned true AND the error string was nil. Print both: a bare `ok`
hides the difference between "refused" and "refused with a reason".
