# DMR icon / asset generation by API (2026-08-13, verified state)

> **FINAL DECISION 2026-08-14 (user): AI image generation is DISCARDED for DMR.**
> After Gemini (cartoon icons ×2) and Canva Pro Magic Media (3D renders) both
> failed to match Factorio's style, the user ended the effort: "elimina lo de
> gemini/canva y la generacion de los iconos/imagenes con ia, lo mismo de las
> referncias y la investigacion eliminalo". Actions taken: deleted
> `dmr-icon-reference.md` / `.pdf`, cancelled the renaming proposal (only
> `matter-conduit` → "Nanophase Conduit" kept, applied to locale EN/ES), and
> closed the kanban free-image research. **Do NOT propose AI asset generation
> for DMR again unless the user explicitly asks.** If they ever do, the
> verified provider facts and the anti-cartoon prompt anchoring below are the
> starting point — but the default answer is: assets stay as-is until
> hand-crafted (Canva Pro manual editor / Inkscape), which the user declined
> for now ("no tengo las habilidades").

Context: user wants to redo the DMR material icons (tenemut, scoop/resonance-latch,
transducer/atomic-loom, conduit/nanophase-conduit, + new genesis-loom) with a coherent
"dark matter" family look, and asked whether opencode-go can generate images.

## Verified: opencode-go CANNOT generate images (2026-08-13)
- Base URL from auth.json: `https://opencode.ai/zen/go/v1` (NOT /api/v1 — that 403s).
- `/models` (with browser User-Agent, Cloudflare error 1010 without it) lists 25 models,
  ALL text/chat: minimax-m3/m2.7/m2.5, kimi-k3/k2.7-code/k2.6/k2.5, glm-5.2/5.1/5,
  deepseek-v4-pro/flash, qwen3.x-*, mimo-v2-pro/omni/v2.5-pro/v2.5, hy3, gpt-5.6-luna, grok-4.5.
- No `/images/generations` endpoint (404). Chat test: `mimo-v2-omni` → deprecated
  ("migrate to xiaomi/mimo-v2.5"), `mimo-v2.5` → "I'm a text-based AI assistant...
  I can only provide text responses."
- Conclusion: for DMR icon art, do NOT try opencode-go. Use Google or OpenRouter below.

## Verified providers with working keys (in the local profile env file)
### Google AI Studio (`GOOGLE_API_KEY`)
- Key valid: `generativelanguage.googleapis.com/v1beta/models?key=...` returns 50 models.
- Image models exist: `gemini-2.5-flash-image`, `gemini-3-pro-image`,
  `gemini-3.1-flash-image`, etc.
- BUT free tier gives HTTP 429 "Quota exceeded for metric:
  generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0"
  for ALL image models → image generation requires billing enabled on the Google account.
- Request shape that reaches the API (use when billing is enabled):
  POST `.../v1beta/models/<model>:generateContent?key=<GK>` with
  `{"contents":[{"parts":[{"text":"..."}]}],"generationConfig":{"responseModalities":["IMAGE"]}}`;
  parse `candidates[0].content.parts[].inlineData.data` (base64) + `.mimeType`.
- TTS note: gemini-2.5-flash-preview-tts exists too (unrelated to icons).

### OpenRouter (`OPENROUTER_API_KEY`)
- Key valid: `/api/v1/models` returns 411 models; image-capable include
  `google/gemini-3.1-flash-image`, `google/gemini-3-pro-image`,
  `openai/gpt-5-image`, `openai/gpt-5-image-mini`, `google/gemini-2.5-flash-image`.
- BLOCKED until user changes data policy: all image models return HTTP 404
  "No endpoints available matching your guardrail restrictions and data policy.
  Configure: https://openrouter.ai/settings/privacy". User must relax privacy
  settings (or whitelist image providers) before these work.
- Chat completion request shape (OpenAI-compatible):
  POST `https://openrouter.ai/api/v1/chat/completions` with
  `{"model":"<id>","messages":[{"role":"user","content":"...image..."}]}`;
  image output arrives as `choices[0].message.content[]` parts with
  `type=image_url` (data: URL or http URL).

## Prompt family (coherent dark-matter look for all 5 icons)
Base prompt template (64x64 item icon or 128x128 tech border):
```
Factorio mod item icon, <SIZE> PNG, transparent background, centered,
flat vector style, crisp edges, no text, no border frame. Deep space black
background (#0a0a14) with violet glow (#7c3aed), faint white particle specks.
Subject: <SUBJECT>. Single subject centered filling ~80% of canvas, subtle
purple glow rim. Color palette: #0a0a14 bg, #7c3aed / #a78bfa violet glow,
#e2e8f0 highlights, #1e293b metallic dark.
```
Subjects: tenemut = crystalline mineral cluster; resonance latch = crystal claw
gripping an energy wisp; atomic loom = lattice/weave core; nanophase conduit =
circuit-bone tube; genesis loom = full hexagon core with re-weaving rings.
Ask for all 5 in ONE session so the family stays consistent.

## Anti-cartoon / anti-3D prompt anchoring (2026-08-13, user-tested)

User hit the SAME failure three times: Gemini gave "cartoon" icons twice
(once after a long 15-rule prompt — "esta alucinando una cosa extraña",
then "imagenes cartoon feas"), and Canva Pro's Magic Media AI gave "3D
clusters" (rendered crystals). Root cause is the PROMPT VOCABULARY, not the
model: to an image model, "flat vector" reads as LOGO DESIGN → cartoon, and
the words "crystal / energy / glow / light" are 3D-render magic words that
push every diffusion-style model toward a Diablo/Path-of-Exile look.

### The 3 anchors that force 2D game-sprite style
Replace vague style words with concrete, dataset-anchored ones:
1. **"2D game sprite / sticker style"** — the datasets contain MILLIONS of
   flat stickers; "sticker style" anchors 2D harder than "flat vector".
   "Nintendo-era inventory icon" also works.
2. **"geometric polygons, not smooth crystals"** — saying "crystal" summons
   3D renders; "sharp angular shards, geometric polygons" stays 2D.
3. **"solid color, hard dark outline, no gradients, no glow, no bloom,
   no lighting, no reflections, no perspective"** — each 3D cue named
   explicitly so the model stops applying it. "Orthographic top-down view,
   ZERO depth" reinforces.

Anti-cartoon base (replaces the "flat vector" template above):
```
Flat 2D game asset, sticker style, orthographic top-down view, ZERO depth,
ZERO 3D. Pixel-art-like shading: each surface is a single solid color with
a hard darker outline. No gradients, no lighting, no gloss, no reflections,
no glow, no bloom, no perspective.
Color palette ONLY: #0a0a14 background, #7c3aed, #a78bfa, #4c1d95 (purple
family), #1e293b (dark metal). Thin dark outline around every shape.
Subject: [sharp angular shards / claw gripper / lattice beams / waveguide
tube / forge core — geometric polygons, not smooth organic shapes].
```
Correction loop when it still drifts: reply *"No — look at the reference
image again and copy its rendering exactly"* (Gemini), or *"Remove all 3D
rendering. Make it look like a 2D paper sticker with flat colors"* (Canva).
The STRONGEST lever is a reference image: upload the actual current icon
(`tenemut.png`) and say "same style as reference" — one real sprite beats
ten style rules. For consistency across the 5-icon family, keep all
generations in ONE session/conversation.

### Canva Pro as editor (user has Canva Pro, 2026-08-13)
Canva Pro's Magic Media AI has the same cartoon/3D drift — do not expect
better results from its generator. BUT Canva Pro is a GOOD MANUAL EDITOR
for this: Factorio icons are just geometric shapes with 2-3 solid tones,
so hand-building with shapes + solid fills gives a guaranteed match
(~15-20 min per icon). Workflow: custom 64x64 canvas → Elements/Shapes
(polygon, triangle for crystal facets, rectangle for metal) → solid fill
from the palette → thin dark outline per shape → Download PNG transparent.
Use BG Remover (Pro) when the generator output has a background. Inkscape
(free, SVG-native) is the higher-fidelity alternative with exact
stroke/fill control and direct 64/128 PNG export.

## Where icons live
- `graphics/icons/` (64px item icons: tenemut.png, dark-matter-scoop.png,
  dark-matter-transducer.png, matter-conduit.png, replicator-1..5.png, replication-lab.png)
- `graphics/icons/borders/` (128px tech borders: tech-device2..5, tech-ore, tech-chemical,
  tech-science, tech-module, tech-alloy, tech-*-category + repl-* variants).
- Composite tech icons built in `lib/mirror-generator.lua` `get_tech_icons()`:
  border layer (128) + item icon centered (scale 64/isize).

## Icon reference PDF for Gemini (2026-08-13) — the working workflow
User: "gemini siempre me da iconos que no concuerdan con lo que tenemos" — a text
prompt alone is NOT enough context. The fix that landed: build a **reference PDF
with the CURRENT icons embedded + lore + palette** so the image model sees the
existing art before generating. Delivered as
`dmr-icon-reference.pdf` in the project directory
(3 pages, 18 embedded images: the 4 current material icons + replicator-5 as
genesis-loom reference + all 9 tech borders + machine icons).

Build recipe (PEP 668 host → use a venv):
```bash
python3 -m venv /tmp/pdfenv && /tmp/pdfenv/bin/pip install reportlab
```
Then generate with reportlab Platypus (SimpleDocTemplate + Table rows of
[Image, name, lore] with a light border; PageBreak before the borders/machines
section). Structure that worked:
- p1: what the mod is, MANDATORY palette (#0a0a14 / #7c3aed / #a78bfa /
  #e2e8f0 / #1e293b), style rules (flat vector, no text, 64px items / 128px
  tech), then Tenemut with its current icon + design goal.
- p2: Resonance Latch / Atomic Loom / Nanophase Conduit (current icon +
  redesign direction: claw/gripper, lattice/loom, waveguide) + Genesis Loom
  (NEW — reference replicator-5 style).
- p3: the 9 tech border frames + machine icons for overall style reference.

Each item gets: full lore (2-3 atmospheric sentences matching the D2/D3 tone) +
explicit design goal ("it is MINED, not crafted" for tenemut). Ask the model to
match the family (same palette + lighting across all 5). Script was one-off in
/tmp; if regenerating, keep the same structure — it was verified via pypdf
(page count + embedded image count per page).
Also 2026-08-13: delegated the "free image generation path" research via the
internal kanban tracker (`kanban create ... --assignee agent`) —
opencode-go/Google/OpenRouter were all verified non-free or blocked (see above);
the kanban task is the open thread for a no-billing route (Pollinations, Stable
Horde, local ComfyUI on the weak Quadro P620 4GB, etc.).
