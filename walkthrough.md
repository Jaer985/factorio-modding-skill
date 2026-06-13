# Factorio Modding Skill — Final Audit & Walkthrough

This document records the complete set of 15 structural, logical, and performance corrections applied to the templates and reference guides of the `factorio-modding` skill to ensure compatibility with Factorio 2.0 / Space Age, safety against multiplayer desyncs, and robustness for autonomous agent environments (such as OpenCode).

---

## Technical Audit & Fixes applied

### 1. Robust Lifecycle & Event Tracking (Memory Leak Prevention)
* **Files:** [05-lua-performance.md](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/references/05-lua-performance.md) & [boilerplate-control.lua](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/assets/templates/boilerplate-control.lua)
* **Issue:** Cleaning up `storage.my_entities` only on `on_player_mined_entity` caused massive memory leaks if entities were destroyed by Biters, mined by robots (`on_robot_mined_entity`), died (`on_entity_died`), or deleted by other mod scripts (`script_raised_destroy`). Pointers remained indexed to null tables forever.
* **Fix:** Structured consolidated creation handlers (covering players, robots, and scripts) and destruction handlers (covering players, robots, death, and script-raised destroy) to ensure complete cleanup coverage.

### 2. Locality & String Interning Optimization
* **Files:** [05-lua-performance.md](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/references/05-lua-performance.md) & [boilerplate-control.lua](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/assets/templates/boilerplate-control.lua)
* **Issue:** Storing surface names (`entity.surface.name`) required resolving C++ string objects, causing memory fragmentation and slow serialization. Similarly, checking `game.tick` every event registers unnecessary global lookups.
* **Fix:** Utilized `event.surface_index` (integer) and `event.tick` from the Factorio 2.0 event structure, ensuring O(1) reads and minimal memory footprints.

### 3. Mid-Game Scan Migration (Initialization Guard)
* **Files:** [05-lua-performance.md](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/references/05-lua-performance.md) & [boilerplate-control.lua](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/assets/templates/boilerplate-control.lua)
* **Issue:** Declaring tables only in `on_init` caused missing tracking databases when a mod was added to a save game mid-game (since `on_init` only runs on new world creations).
* **Fix:** Integrated a retrospective scanning routine inside `on_configuration_changed` that runs `find_entities_filtered` across all surfaces to populate the database upon the first installation.

### 4. Loop Correctness & Batch Iteration (Data Starvation & next() Safety)
* **Files:** [05-lua-performance.md](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/references/05-lua-performance.md) & [boilerplate-control.lua](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/assets/templates/boilerplate-control.lua)
* **Fix:** Implemented a robust stateful `next()` cursor saved in `storage` with a key existence guard (`if current_key and not my_entities[current_key] then current_key = nil`) to reset safely on external deletions, and prevented cursor advancement when deleting orphaned entities during the loop.

### 5. State Mutation via Remote Interface (Desync Prevention)
* **File:** [boilerplate-control.lua](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/assets/templates/boilerplate-control.lua)
* **Fix:** Imported Factorio's native `util` library and wrapped all API return values in `util.table.deepcopy()` to prevent external mods from mutating our storage.

### 6. API Query Complexity (O(N) to O(1) Optimization)
* **File:** [boilerplate-control.lua](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/assets/templates/boilerplate-control.lua)
* **Fix:** Added a tracked `entity_count` counter inside isolated storage, maintaining it at insertion, deletion, and cleanup for O(1) complexity.

### 7. Technology Research Trigger Semantics
* **File:** [01-patterns.md](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/references/01-patterns.md)
* **Fix:** Replaced the fluid `"crude-oil"` with solid `"iron-ore"` for `mine-entity` triggers, aligning with standard engine validation rules.

### 8. Multi-Agent Storage Isolation (OpenCode Standards)
* **Files:** [boilerplate-control.lua](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/assets/templates/boilerplate-control.lua) & [05-lua-performance.md](file:///C:/Users/jaer1/.gemini/skills/factorio-modding/references/05-lua-performance.md)
* **Fix:** Isolated variables under `storage["my-mod-name"]` instead of writing keys directly to the global `storage` space, preventing collisions during multi-agent merges.

---

### Legacy Fixes recap
9. **Data Stage Icons Arrays:** Changed `icons = icon(...)` to `icons = {icon(...)}` in `boilerplate-data.lua`.
10. **Event-Based Interop:** Switched `defines.events.on_custom_event_name` to dynamic remote interface event ID mapping.
11. **C++ Event Filters Syntax:** Fixed malformed filter definitions in `06-cpp-engine.md` to use nested arrays `{{filter = "name", name = "my-entity"}}`.
12. **Technology Ingredients Standard:** Standardized ingredients to the 2.0 object format `{type = "item", name = "...", amount = 1}` in `boilerplate-data.lua`.
13. **Module-Scope Locality Caching:** Cached standard library pointers (`pairs`, `util`) at module scope.
14. **Fluidbox 2.0 Schema Adaptations:** Added input/output fluidbox structural checks inside prototype safe-update routines in `01-patterns.md`.
15. **Validity Guards:** Included O(1) `game.get_entity_by_unit_number()` lookups with `.valid` validation prior to hot-path modifications.
