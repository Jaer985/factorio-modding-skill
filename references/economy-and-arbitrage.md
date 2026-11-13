# Energy pricing and recycle arbitrage

## The break-even rule

If a recipe is priced in energy and a recycler can return a fraction of its parts, the craft is
arbitrage-safe iff the energy it costs is worth at least what recycling returns:

    t = parts_bill / (f * R)      -- parts_bill = sum(amount * that ingredient's replication MJ)

With Space Age 25 percent recycler yield that is parts_bill / (4 * R). Price the recipe exactly
there: below it the loop is free energy (a 200 s craft on a 68.5 GJ parts bill hands the recycler
27x its electricity); far above it the item is unplayably slow for no extra safety.

- Apply the floor AFTER every other clamp and let it outrank them -- a ceiling applied later
  re-opens the loop.
- The floor must cover the mod OWN machines. The scan that asks what recipe produces this
  ingredient typically skips the mod own recipes, so its machines get no floor and recycle for many
  times their own cost. Assert coverage with a dump query over the mod own item names, not just
  vanilla ones.
- A cost multiplied later (a secondary machine taking 3x the base time) re-introduces absurdities:
  a 49.7 h per-attempt recipe. Clamp or cap the FINAL number, not just the base.
- Recompute the whole distribution after any change: count recipes per time band and list the worst
  eight with before/after values. One wrong divisor moved 71 items past a design ceiling once.

## Derived-value passes mis-price fluids

A pass that derives a price from how long a machine would take to craft this defaults exotic
inputs (water: 500 s/craft) and pushes fluids up to the ceiling. Declare fluid prices explicitly --
water is free in game, so it must never be the most expensive thing to replicate.

## Productivity effects: docs are not proof

The prototype docs place change-recipe-productivity on the RECIPE (allow_productivity), not on the
machine allowed_effects. When a whole design (a duplication ladder, a 50 GJ into 100 GJ endgame)
hangs on which of the two governs, prove it with one real craft in the headless engine before
publishing the claim: a dump-data run cannot answer a runtime question.

## Generator guards worth having

- Never emit a technology with an empty effect list: deleting a recipe can silently leave the tech
  that granted it with nothing. Assert effects is not empty for every generated tech in the dump.
- Keep fuel and energy blacklists declared, and verify their effect by counting what vanished. The
  count tells you whether the blacklist caught the intended items or an entire class by side effect
  (20 fuels x 4 qualities hides 80 missing recipes behind a 12-item expectation).
