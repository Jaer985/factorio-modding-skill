# Factorio Modding Skill — Complete Audit & Refactoring Walkthrough

This document records the complete set of 12 structural, logical, and performance corrections applied to the templates and reference guides of the `factorio-modding` skill to ensure compatibility with Factorio 2.0 / Space Age, safety against multiplayer desyncs, and robustness for autonomous agent environments (such as OpenCode).

---

## Technical Audit & Fixes applied

### 1. Loop Correctness & Batch Iteration (Data Starvation & Crashes)
* **Files:** [05-lua-performance.md](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/references/05-lua-performance.md) & [boilerplate-control.lua](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/assets/templates/boilerplate-control.lua)
* **Issue A (Data Starvation):** The initial template processed batches using `pairs` and interrupted the loop when reaching `batch_size`. Since `pairs` doesn't preserve iteration order, the same first items were processed repeatedly while others suffered from starvation.
* **Issue B (Invalid Key to Next Crash):** Traversal using `next(table, key)` crashes with "invalid key to 'next'" if `key` is deleted from the table (either by orphan cleanup during the loop, or externally by other events).
* **Fix:** Implemented a robust stateful `next()` cursor saved in `storage`. Added a key existence guard (`if current_key and not my_entities[current_key] then current_key = nil`) to reset safely on external deletions, and prevented cursor advancement when deleting orphaned entities during the loop.

### 2. State Mutation via Remote Interface (Desync Prevention)
* **File:** [boilerplate-control.lua](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/assets/templates/boilerplate-control.lua)
* **Issue:** The `get_entity_data` API returned raw references to tables stored in `storage`. In Lua, tables are passed by reference, enabling third-party mods to directly mutate internal state, causing multiplayer desyncs.
* **Fix:** Imported Factorio's native `util` library and wrapped the returned payloads in `util.table.deepcopy()`.

### 3. API Query Complexity (O(N) to O(1) Optimization)
* **File:** [boilerplate-control.lua](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/assets/templates/boilerplate-control.lua)
* **Issue:** `get_entity_count` walked the entire `storage.my_entities` table on every call to sum items (O(N)), locking the main thread needlessly on high entity counts.
* **Fix:** Added a tracked `entity_count` counter inside isolated storage, maintaining it at insertion (`on_built_entity`), deletion (`on_player_mined_entity`), and cleanup (`on_tick`) for O(1) complexity.

### 4. Technology Research Trigger Semantics
* **File:** [01-patterns.md](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/references/01-patterns.md)
* **Issue:** The `mine-entity` research trigger example used `crude-oil`. Crude oil is a fluid resource processed via pumpjacks, which does not fit the mechanical validation of "mining".
* **Fix:** Replaced with `"iron-ore"`, a solid minable resource, aligning with the engine's validation rules.

### 5. Multi-Agent Storage Isolation (OpenCode Standards)
* **Files:** [boilerplate-control.lua](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/assets/templates/boilerplate-control.lua) & [05-lua-performance.md](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/references/05-lua-performance.md)
* **Fix:** Isolated variables under `storage["my-mod-name"]` instead of writing keys directly to the global `storage` space. This avoids namespace collisions when multi-agent codebases are merged.

---

### Phase 1 Audit Legacy Fixes (Recap)
6. **Data Stage Icons Arrays:** Changed `icons = icon(...)` to `icons = {icon(...)}` in `boilerplate-data.lua` to prevent C++ array property loader crashes.
7. **Event-Based Interop:** Replaced invalid `defines.events.on_custom_event_name` lookups with `script.generate_event_name()` and dynamic subscription via remote interfaces.
8. **C++ Event Filters Syntax:** Fixed malformed filter definitions in `06-cpp-engine.md` to use nested arrays `{{filter = "name", name = "my-entity"}}`.
9. **Technology Ingredients Standard:** Standardized automation pack ingredients in `boilerplate-data.lua` to the 2.0 object format `{type = "item", name = "...", amount = 1}`.
10. **Module-Scope Locality Caching:** Cached standard library pointers (`pairs`, `util`) and Factorio API methods locally at the top of control files to bypass Lua hash tables.
11. **Fluidbox 2.0 Schema Adaptations:** Added input/output fluidbox structural checks inside prototype safe-update routines in `01-patterns.md`.
12. **Validity Guards:** Included O(1) `game.get_entity_by_unit_number()` lookups with `.valid` validation prior to hot-path modifications.
