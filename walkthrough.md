# Factorio Modding Skill — Unified Walkthrough

This document registers all 9 structural and logical corrections applied to the templates and reference guides of the `factorio-modding` skill to ensure compatibility with Factorio 2.0 / Space Age and robustness for autonomous agent environments like OpenCode.

---

## Technical Audit & Fixes applied

### Phase 1: Engine and Loop Corrections

1. **Staggered Iteration (Tick Throttling)**
   - **File:** [05-lua-performance.md](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/references/05-lua-performance.md) & [boilerplate-control.lua](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/assets/templates/boilerplate-control.lua)
   - **Bug:** The `#` operator was used on associative tables (keyed by `unit_number` maps), which evaluates to `0` in Lua 5.2.1 and silently prevented any execution of the loops.
   - **Fix:** Refactored to a stateful iterator using `next()` to safely persist progress across ticks.

2. **Entity Validity Guard Checks**
   - **File:** [boilerplate-control.lua](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/assets/templates/boilerplate-control.lua)
   - **Bug:** Mod iterated data without resolving entity pointers or checking `.valid`, causing potential crashes if entities were mined/destroyed by external mods or gameplay.
   - **Fix:** Integrated `game.get_entity_by_unit_number()` checking for validity and garbage collecting invalid pointers. Also resolved a bug in [05-lua-performance.md](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/references/05-lua-performance.md) where `surface.find_entity()` was incorrectly called with a `unit_number` instead of position.

3. **Fluidbox 2.0 Schema Adaptations**
   - **File:** [01-patterns.md](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/references/01-patterns.md)
   - **Bug:** Modified `fluid_boxes` directly, but Factorio 2.0 split many prototypes into explicit `input_fluid_box` and `output_fluid_box` parameters.
   - **Fix:** Implemented a type check cascade that safely detects `input_fluid_box` (2.0 native schema) first, falling back to the legacy `fluid_boxes` array format.

4. **Module-Scope Locality Caching**
   - **File:** [05-lua-performance.md](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/references/05-lua-performance.md) & [boilerplate-control.lua](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/assets/templates/boilerplate-control.lua)
   - **Enhancement:** Cached frequent standard library functions (`pairs`, `math_min`) and API calls (`game.get_player`, `game.get_entity_by_unit_number`) at module scope to completely avoid hash lookups at 60 UPS.

---

### Phase 2: Structural and Syntax Corrections

5. **Data Stage Icons Arrays (Crash Fix)**
   - **File:** [boilerplate-data.lua](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/assets/templates/boilerplate-data.lua)
   - **Bug:** Assigned the return value of `icon(name, size)` (a single table dictionary `{ icon = ..., icon_size = ... }`) directly to `icons` (plural). The Factorio engine crashes immediately with `Property icons is not an array`.
   - **Fix:** Wrapped the `icon` helper returns inside an array format `{ icon(...) }` for all `icons` definitions (items, recipes, technologies).

6. **Event-Based Interoperability (API Break Fix)**
   - **File:** [03-compatibility.md](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/references/03-compatibility.md)
   - **Bug:** Code instructed to trigger and listen via `defines.events.on_custom_event_name`. However, `defines.events` is a static, C++ controlled read-only enum. Generating custom events returns a dynamic integer ID which does NOT get injected there.
   - **Fix:** Replaced with the correct public interface registration pattern. Mod A registers and shares the event ID via `remote.add_interface`, and Mod B retrieves it to subscribe.

7. **C++ Event Filters Syntax Alignment**
   - **File:** [06-cpp-engine.md](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/references/06-cpp-engine.md)
   - **Bug:** Documented filter parameters in event registration using `{filter = {name = "my-entity"}}` which is malformed.
   - **Fix:** Aligned with Factorio 2.0 structure using nested arrays: `{{filter = "name", name = "my-entity"}}`.

8. **Technology Research Ingredients Standard**
   - **File:** [boilerplate-data.lua](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/assets/templates/boilerplate-data.lua)
   - **Enhancement:** Converted array shorthand research ingredients (`{"automation-science-pack", 1}`) to the formal Factorio 2.0 standard object format `{type = "item", name = "automation-science-pack", amount = 1}` to avoid deprecation warnings.

9. **OpenCode Multi-Agent Storage Isolation**
   - **File:** [boilerplate-control.lua](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/assets/templates/boilerplate-control.lua) & [05-lua-performance.md](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/references/05-lua-performance.md)
   - **Best Practice:** Prevented global namespace pollution under the engine-persisted `storage` table. Isolated mod variables within namespaces such as `storage["my-mod-name"]` so merged agentic files do not collide.
