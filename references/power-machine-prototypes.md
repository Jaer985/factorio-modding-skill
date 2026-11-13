# Power machines - prototype type, fuel lock, joule ledger

Anything that eats fuel and makes power is one of two prototype types, and the choice decides the
plumbing, the module surface and the balance ledger.

## `burner-generator`: fuel in, electricity out - no heat stage

- `burner` is the FUEL side; `energy_source` is the ELECTRIC OUTPUT side; `max_power_output` is the
  cap. A `reactor` is the same physics routed into the vanilla heat-exchanger/turbine chain, which
  costs a 5x5 machine, a water line and the exchanger/turbine hardware behind it.
- Ledger in ONE place: burn seconds = fuel_value / max_power_output. Choose the consumption so the
  division is exact (e.g. 25 GJ / 41.6667 MW = 600.0 s) and keep ONE shared ledger for every machine
  that burns the same fuel, so two machines compare to the gram. When two machines offer the same
  joules, say in the header which one wins on FOOTPRINT and which on plumbing - otherwise a later
  pass "balances" the joules apart.
- `burner.effectivity` never above 1.0: above 1 is free energy.
- Partial load is a TEST, not a bug: a burner-generator draws fuel as demanded, so a light grid
  makes one unit last LONGER than the ledger says. Put that on the gate list explicitly.
- No `module_slots`, no `allowed_effects`, no beacon interaction - the type is not a crafting
  machine, so the exclusion surface does not exist. Do not declare exclusion fields for a surface
  that is structurally absent.
- No neighbour interaction of any kind: it is not a reactor.

## `reactor`: fuel in, heat out

- `neighbour_bonus = 0` and no `neighbour_connectable` for a reactor that must not stack with
  itself (Space Age's own non-breeder heating tower is built exactly this way). The default bonus
  is how a 25 GJ fuel cell pays out 37.5-43.75 GJ through a 2x2 block.
- `scale_energy_usage = false` keeps the burn constant (vanilla reactor behaviour) so the ledger
  number is real and not "up to".
- The heat it produces only reaches the grid through the vanilla chain - count the exchangers and
  turbines as part of the machine's real price when writing a build recipe.

## The fuel lock - one private category, checked in BOTH directions

- Give the fuel item a PRIVATE `fuel_categories` entry, and list that entry only in the machines
  that may burn it. A fuel that keeps a vanilla category fits every vanilla burner, including the
  reactor with the neighbour bonus above.
- Locking the MACHINE is not enough: the lock lives on the fuel item's own categories list.
- Test both directions in the gate list: the machine refuses coal, nuclear fuel, uranium cells and
  fusion cells, and the vanilla machines refuse the mod's fuel. Only a dropped item proves it -
  reading the prototype does not.

## Placeholder graphics

- Scale the ART inside the frame, never the frame: measure the solid region (alpha >= 250) of the
  sheet, derive scale from the art width in tiles and shift by the art's own offset inside the
  frame, then confirm the sprite is centred in its collision box. Scaling the frame leaves the art
  off-centre and too tall, and the error only shows on screen - see
  `machine-graphics-pitfalls.md`.
- Reference the mod's OWN sheet for placeholders: an overhaul modlist replaces vanilla sheets, so a
  vanilla path can vanish or change size under the player.
