# DMR Original Mod Study — dark-matter-replicators-space-age 2.0.4 (nihilistzsche fork)

Fuente: `archivados/dark-matter-replicators-space-age_2.0.4.zip` (extraíble con Python; SIN unzip en el sandbox).
Estudio completo 2026-08-22 → informe largo en `research/dmr-original-mod-study.md`. Este resume lo que hay que recordar:

## El modelo del original (lo que "ellos hacen")
- **Costos DECLARATIVOS por mod**: `replications/<mod>.lua` (vanilla 226 líneas, bob 617, yuoki 151...) con `repltech_recipe/item/item_table/ore/raw/element` + `replvar(name, cost)`.
- **Costo = cadena de ingredientes + cargo de máquina**: cost part `{type="recipe"}` descompone la recipe en Σ ingredientes replicables + var(category)×(energy_required−0.5). Las vars de categoría = kW/speed/270 de la máquina real: `""`=56/90 (AM3), smelting=1/3, oil-processing=14/9, chemistry=56/90, centrifuging=140/81, rocket-building=25/27. Bob las REDEFINE (máquinas más eficientes → costos más bajos).
- **Ores**: cost = var("ore")×mining_time/base_density×8 (raros = caros; thorium 2.5/0.9 gigante; gemas Bob var 200).
- **Tiers por categoría**: ore=1, element=2 (research×0.5), shape=2, alloy=3, chemical=3, device2..5=2..5, life=5, module=5 (-1 → 4), science=manual.
- **Research**: count = tier×25 (t1/t5 ×2), time=5, packs DMR por tier (tenemut/scoop/transducer/conduit), SIN item_count.
- **Máquinas**: speed 2^(t−1) (1..16x), energía 256kW×2.5^(t−1) (256kW..10MW) — energy_factor > speed_factor → tiers altos MENOS eficientes. cross-tier recursivo (categories = 1..tier). Módulos permitidos: +speed/+consumption/+productivity/+quality/+pollution. Space-lock setting (default 6=off).
- **Prereqs**: tech del tier + (ingredientes de la recipe → sus repltechs) + la TECH ORIGINAL (cuando recipe no enabled) + redundancy pruning + splice de categorías deshabilitadas.
- **Science packs original**: automation 3, logistic 4, military 4, chemical 4, production 5, utility 5, space 5; SA todo device5.
- **SA: TODO device5** (foundry, biochamber, mech-armor, fusion-reactor-equipment, ores planetarios tier 5). NO hay planetarios en el original.
- **Exclusiones**: replvar(name) SIN cost = exclusion (bob 44: bearings/roboport-parts/projectiles/warheads; angel 14: gas-*, nitric-acid...).
- **Los replicadores 1-5 y los items DMR se REPLICAN** (replicator-N device3-5 upgrade=true, tenemut t1, scoop t2, transducer t3, conduit t4).
- **replication-penalty**: +0.5 FIJO por item (suma) — en nuestro fork se multiplica (1+penalty) — semántica DIFERENTE, documentado en audit-and-release.

## Divergencias con nuestro v4.2
Estado 2026-08-22 (el refino completo tomó las 5 implementables; las 3 restantes siguen como "no tocar sin pedir"):
- ✅ REPLICADORES propios: original los replica → IMPLEMENTADO (whitelist + tier forzado, ver Refino).
- ✅ RESEARCH: original NO × item_count → IMPLEMENTADO (10×tier fijo).
- ✅ ORES raros: coste por rareza → IMPLEMENTADO (mining_time×2 en dinámicos).
- ✅ PRODUCTIVITY en replicadores: removed (exploit del upstream corregido).
- ✅ PENALTY: +0.5 suma, fiel al original.
- ⏸️ Equipo personal: original replica mech-armor/fusion-reactor-equipment (device5); nosotros excluido (v4.0 usuario) — NO tocar sin pedir.
- ⏸️ Science planetarios: original tier 5; nosotros t4 (B4) — NO tocar sin pedir.
- ⏸️ Módulos: original -1 en 4, 2/3 en 5; nosotros básico tier 3 — NO tocar sin pedir.

## Refino IMPLEMENTADO (2026-08-22, user: "haz el refino completo")

Tras presentar las divergencias del estudio, el usuario tomó las 5. Patrones de implementación reutilizables:

1. **Replicadores DMR replicables** — patrón "whitelist + tier forzado" (como tenemut/gemas):
   - `target-mapper.lua`: `DMR_REPLICATOR_WHITELIST = {dmrsa-replicator-1..5}` y la excepción al filtro gprefix (`and name ~= gprefix.."tenemut" and not DMR_REPLICATOR_WHITELIST[name]`).
   - `mirror-generator.lua`: `REPLICATOR_TIER = {replicator-1=1, ..., replicator-5=5}` aplicado sobre `local tier = solved.tier or 1` — cada replicador cae en su propia tech espejo (fiel al `repltech_recipe(device3-5, upgrade=true)` del original).
2. **Rareza de ores** — en `CostSolver.initialize_base_resources()` (bloque de minables dinámicos): `base_cost = base_cost + (res.minable.mining_time or 0.75) * 2` — los ores de mod con mining lento (tungsten 5 → +10) pagan más que los comunes aunque no suban de tier. SÓLO afecta minables sin entrada estática en BASE_RESOURCE_COSTS; los vanilla quedan intactos.
3. **Research sin ×item_count** — `mirror-generator.lua` reps: `math.ceil(repetitions * (diff_vals.cost / 25))` (10×tier fijo; el original cobra por TECH tier×25). materials-1 pasó de 250 → 10 reps.
4. **Quitar "productivity"** de `allowed_effects` en replicadores — con recipes de 0 ingredientes la productividad es duplicación gratis (exploit del upstream). La calidad sale por el Refinador (sin modules).
5. **Penalty = +0.5 FIJO (suma)** — en `solve_cost` la rama cached: `dark_matter = cached.dark_matter + penalty; time = cached.time + penalty*0.5` — reemplaza el multiplicador decayente (1+penalty/depth) que inflaba cadenas largas y contradecía la descripción "added to the cost". Ojo: el setting `dmrsa-cost-calculation-method` quedó SIN EFECTO (ambas ramas suman) — documentado en changelog.

## Workflow lesson (2026-08-22)

Durante la implementación del paquete B2 el usuario envió un "Espera" out-of-band para realinear el paquete completo (recapituló punto por punto, luego confirmó "toma la b"). Lección: en sesiones de DISEÑO activo (fórmulas de balance + decisión interactiva), antes de lanzar los parches hay que confirmar el PAQUETE COMPLETO en una sola recap — el usuario lo espera explícitamente ("expandamos con ejemplos", "verifiquemos antes de modificar algo"). Un patch a medias aceptado NO implica que el siguiente del lote esté aprobado: cada decisión nueva (cross-tier, tabla de kW, dosis de speed) requiere su propia confirmación con datos (tabla de opciones + casos concretos, p.ej. el basic inserter).

## Pitfalls fresh (esta pasada)
- El zip del original NO se puede abrir con `unzip` en el sandbox (no instalado) — usar `execute_code` con zipfile.
- `replvar("gem-ore", 200)` — gemas Bob = coste variable enorme, no una entrada de tier.
- El comentario de bob.lua que justifica los costs: "more efficient machines → replication costs reduced" — la justificación conceptual del MACHINE_EFFICIENCY.
- El `Ingredient_count = -0` — 0-ingredient recipes (lore: "haha no ingredients").