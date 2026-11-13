# Machine graphics - idle states and sprite geometry

## Idle animation without new assets

- Add `idle_animation` to `graphics_set` reusing the SAME sprite sheet plus a dark
  `tint = {r=0.55,g=0.55,b=0.55,a=0.9}`: the engine shows the dimmed static frame while the machine
  has no recipe/input and the animated sprite while it works. Zero new art.
- Check the sprite first (PIL: frame0 vs frame1 mean-abs-diff). If the sheet already animates
  subtly, tint is the wrong lever - there is no distinct "off" frame to reuse.
- LOAD RULE: when `idle_animation` reuses the animation's sheet, `frame_count` (and `line_length`)
  must MATCH. `frame_count = 1, line_length = 1` is rejected at load: "Idle animation must have the
  same frame count as animation."
- LOAD RULE: never `animation_speed = 0` to freeze the idle - rejected with "Animation speed has to
  be greater than 0." Use a tiny positive value (0.01, roughly one cycle per 55 s on a 33-frame
  sheet), which reads as a static dimmed frame. A visually DIFFERENT idle needs a separate sprite
  sheet, where frame_count may differ.
- Factorio validates prototype constraints at load that static analysis never sees: gate any
  `graphics_set` change on the in-game test, not on review.

## Sprite geometry when placing art in a box

- Measure the solid (alpha >= 250) region of the frame instead of trusting the frame box, compute
  scale from the art width in tiles and shift to cancel the art's own bias, then verify on screen
  that the sprite is centred in its collision box. A scaling error is invisible in the prototype
  and obvious in play.
