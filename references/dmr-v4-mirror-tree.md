# DMR v4.0 — Mirror Tree (árbol espejo) + Factorio 2.1

Diseñado e implementado 2026-08-12. Zip `dark-matter-replicators-reborn_4.0.0.zip`
(108 archivos, 4.7MB) construido, tests verdes (test_mirror 30/30, run_tests
34/34, step_filter ALL PASS).

## ⚠️ ESTADO ACTUAL 2026-08-13: gate test — 4 errores encontrados y RESUELTOS
El gate test del usuario en Factorio 2.1.14 pasó por 4 errores de carga, todos
resueltos en el zip final:
1. `Error in assignID: item with name 'dmrsa-replication-lab' does not exist` —
   causa: `assembler2pipepictures()` eliminada como función global en 2.1;
   `replicators.lua` fallaba SILENCIOSAMENTE (safe_require traga el error) →
   el item nunca se definía. Fix: `require("__base__/prototypes/entity/
   assembler-pictures").assembler2pipepictures` (tabla, SIN paréntesis, con
   prefijo `__base__/` — el require sin prefijo no resuelve desde otro mod).
   Afectaba a replicators.lua Y planetary-replicators.lua.
2. `Technology dmrsa-mirror-angels-chlorine-processing: Non-contiguous levels:
   2, followed by 4` — causa: la tech espejo toma la tech ORIGINAL como prereq
   directo; su science-pack level (2-3) es más superficial que su profundidad
   real en el árbol (4). Fix: `MirrorGenerator.get_tech_tree_depth()` —
   función recursiva memoizada y cycle-safe; tier = max(science_level,
   tree_depth) cuando dmrsa-require-original-tech=ON.
3. El MISMO error persistía aunque el fix 2 estaba en el zip — causa: faltaban
   las deps opcionales de Angel's en info.json (`? angelspetrochem` etc.);
   DMR corría su data-final-fixes ANTES que Angel's → el depth se calculaba
   con prereqs incompletos. Fix: +12 deps Angel's (mismo patrón A5 que Bob's).
4. El MISMO error persistía otra vez — causa RAÍZ real: las techs de Angel's
   son CADENAS NIVELADAS (`angels-chlorine-processing-1..4`). Factorio trata
   techs con sufijo `-N` como NIVELES de una tech base compuesta; generar un
   mirror por nivel (`dmrsa-mirror-angels-chlorine-processing-1..4`) creaba
   una compuesta cuyos niveles deben ser CONTIGUOS — como el nivel -3 no
   desbloqueaba items replicables (recipes excluidas), su mirror se saltaba y
   la cadena quedaba 1,2,4 sin el 3. Fix: `normalize_tech_base()` — quitar el
   sufijo `-N` y agrupar TODA la cadena en UN mirror, con prereq = el nivel
   más profundo existente (`mirror_deepest`). Pitfall Lua: `string.find(name,
   "%-%d+$")` NO captura el número (sin paréntesis) — usar `"%-(" .. "%d+" ..
   ")$"` o el tie-breaker de profundidad es un no-op.
Lección general: un fix de generación dinámica que lee el grafo de techs de
OTROS mods (recipe_tech_map, tree depth, prereqs) NO funciona sin las deps
opcionales de CADA familia overhaul presente en el modlist, y las cadenas de
techs con sufijo numérico requieren agruparlas en UNA sola tech (ver
`references/factorio-2.1-breaking-changes.md` secciones Pipe pictures +
Non-contiguous + Leveled-tech chains).
Backup de reversión intacto: `backups/dark-matter-replicators-reborn_3.7.1-source-backup.tar.gz`.

## ⚠️ CORRECCIÓN 2026-08-23 (gate test 4.2.0): el depth clamp INFLÓ los tiers — el fix real era la normalización de cadenas -N

El gate test 4.2.0 (dump real, 138 mods) destapó el efecto colateral del fix #2:
usuario reportó "porque logistic science pack, chemical science pack estan en tier 5"
+ "parece que muchas cosas se subieron de tiers". Dump-verificado:

- Mirrors de science packs mal: `logistic`=5 (debía 1), `military`=5 (debía 2),
  `chemical`=5 (debía 3), `production/utility`=5 (debía 3), `automation`=2 (debía 1).
- De 474 mirror techs: **216 con tier > SCL** (subidos por el clamp) y **154 con SCL
  nil** (fallback a max item tier).
- El deep modded tree (SA + planetaris + bob) da profundidades reales enormes:
  chemical=22, production=25, utility=29, space=39, promethium=80. `tier =
  max(SCL, depth)` → TODO lo que esté a depth ≥5 se va a 5.

**INSIGHT CLAVE**: el depth clamp (fix #2, 2026-08-13) fue un Band-Aid intermedio. El
error real "Non-contiguous levels" lo causaban las CADENAS NIVELADAS (`-N`), resueltas
por `normalize_tech_base()` (fix #4). El clamp quedó activo y distorsiona la
progresión completa en árboles de mods grandes. Dirección del fix (diseñada, PENDIENTE
de implementar + gate test): QUITAR el clamp (o caparlo a la banda de progresión) y
FORZAR los science packs por tabla de progresión.

**SEGUNDO INSIGHT**: para science packs, SCL NO es la señal correcta — la tech que
DESBLOQUEA el pack usa packs de TIER INFERIOR (el research `chemical-science-pack`
usa automation+logistic → SCL=1, pero el PACK es tier 3). El tier de un science pack =
su POSICIÓN DE PROGRESIÓN (tabla v3.5.17: auto/logi=1, mili=2, chem/prod/util=3,
planetary=4, space/cryo/prom=5, mods gold/alien=5, numbered `science-pack-N` →
max(2,min(5,N))). Para el mirror: función `science_item_tier(name)` con el MISMO mapeo
de `CostSolver.get_tier_from_tech` (cost-solver.lua ~línea 400 — fuente canónica),
aplicada ANTES de SCL/fallback/depth para cualquier ítem con "science-pack".
OJO al orden de branches: `advanced%-logistic` (→3) DEBE chequearse ANTES del
substring genérico `logistic` (→1), o bob-advanced-logistic vuelve a caer a 1
(lección v3.7.0).

## v4.1.0 — Quality Refiner (2026-08-16)
Feature nueva (la calidad NO sale del replicador normal; sale de una máquina
dedicada). Ver `references/factorio-2.1-breaking-changes.md` para los 4 errores
de prototipo 2.1 que salieron en el gate test (independent_probability, icon en
recipes quality, icon en techs, repeat_count del shadow) — ya documentados ahí.
Resumen del feature:
- `dmrsa-refiner` (assembling-machine, categoría `dmrsa-refining`): sube items
  replicables +1 grado de calidad, NUNCA salta (normal→uncommon→rare→epic→
  legendary). Probabilidades decrecientes por escalón (1% / 0.5% / 0.25% /
  0.1%), pérdida 5% del item por ciclo, reintento con el mismo item el resto.
- Recipe por item×escalón (4 por item replicable), generadas por
  `lib/refiner-generator.lua` tras el mirror (lee las recipes dmrsa-repl-* para
  el coste energético base → ×10). Ingredients con `quality` fijo; results con
  `independent_probability`. `hidden=true` + categoría propia (solo visibles en
  el refiner). Gate: solo se genera si `data.raw["quality"]["uncommon"]` existe.
- El refiner NO acepta módulos (module_slots=0) — la probabilidad ES el balance
  (quality modules romperían la escalera).
- Setting `dmrsa-replicator-quality` (default "Normal only"): el replicador
  normal pone `quality="normal"` en sus recipes (fiel: replica materia normal);
  "Allow quality" = modo permisivo (el viejo comportamiento).
- Tech `dmrsa-replication-refining` (materials-5 + tech quality vanilla).
- Tests: dmr-tests/test_refiner.lua (41 checks). Placeholder gráfico: sprite
  propio replicator-5.png con tint obsidiana-violeta (NUNCA sprite vanilla — ver
  la lección "own sprite" en breaking-changes).
- Pitfall de test harness: `data:extend(...)` se llama como `data:extend(...)`;
  en el mock, `data.extend = function(self, tbl) ... end` (el primer arg es
  self) — si el mock usa `function(tbl)`, el método recibe `data` como tbl y el
  assert falla.

## v4.2 (diseño abierto 2026-08-22) — baseline inflado por OUTPUTS de proceso
**Síntoma del usuario**: `dmrsa-replication-materials-1` desbloquea "muchísimas
cosas" con mods grandes. Dump 4.1.0 real (138 mods): materials-1 = **108 items**
(vs 16 del diseño). 1716 recipes dmrsa-repl-* (vs 945 del 3.7.1).

**Causa raíz (confirmada con dump)**: el mirror adjudica la tech original por
`unlock-recipe` con **recipe-name == item-name** (asunción 1:1). Los items que
son OUTPUTS de recipes de proceso (petroquímica/electrólisis/crushing de
Angel's: `angels-gas-hydrogen`, `angels-mineral-sludge`, `angels-geode-*`,
`angels-ore1..6`, `angels-liquid-*`, `angels-crystal-*`) no tienen recipe con su
propio nombre → el mirror no encuentra su tech → caen al baseline tier 1.
Ejemplo real: `angels-gas-hydrogen` ← `angels-water-separation` ← tech
`angels-basic-chemistry` (el unlock-recipe apunta a la recipe productora, no al
item).

**Método de diagnóstico (reusable, Python sobre data-raw-dump.json)**:
1. construir `produced_by[item] = [recipe...]` iterando `recipe.results`
2. construir `recipe_tech[recipe] = [tech...]` iterando
   `tech.effects` (type==unlock-recipe), filtrando techs dmrsa-* y hidden
3. para cada item baseline, ver si alguna recipe productora está unlocked por
   una tech (excluir recipes `*-recycling`, `recycling`, `empty-*/fill-*`).
⚠️ Pitfall de regex (mordió 2×): en Python los patrones NO usan el escape Lua
`%-`; escribir `r'-armor$'` con guion normal. `r'%-armor$'` matchea el literal
`%-armor` y no filtra nada.

**Fix IMPLEMENTADO (v4.2.0, 2026-08-22)**: adjudicar la tech vía las recipes
productoras, con 2 salvaguardas contra falsos positivos:
1. no-minable (los `data.raw.resource` no heredan tech ajena — coal/iron-ore/etc.
   son baseline legítimos aunque otra recipe los produzca como byproduct)
2. mismo prefijo de mod (un item angels-* solo hereda de recipes angels-*).
   + excluir explícitamente la tech `recycling` del reverse-map (filtró como
   falsa "tech original" de `angels-ore1-crushed`) y las recipes
   `*-recycling`/`empty-*`/`*-unbarrel`.
Resultado medido (re-simulación CORREGIDA sobre el dump): materials-1
108 → 25 items legítimos (coal, ores base, burner, plates base,
water/steam/crude-oil...); espejo 1328 → 1497 techs. Modificación en
`lib/mirror-generator.lua` (pass 4b: `item_process_techs`) + `data-final-fixes`.

**Pitfall de la simulación (mordió 2×): `.match()` ≠ `.search()` en Python.** La
simulación predijo materials-1=30 y decía que plastic-bar/resin/rubber iban a
mirror tech; el JUEGO (correcto) los dejaba en baseline tier 1. Causa: usé
`re.compile(r'-recycling$').match(rname)` — `.match()` ANCLA al inicio del
string, así que `"plastic-bar-recycling".match("-recycling$")` falla y la recipe
NO se excluía → el item heredaba la tech falsa "recycling" → espejo. En Lua
`string.find` es SEARCH, por eso el juego difiere. Regla: en sims Python de la
lógica Lua siempre usar `.search()`, y ante una discrepancia sim-vs-juego
revisar las exclusiones de la sim antes de creerle al framework.

**Pitfall de diseño descubierto**: los overhaul mods REDIRECT los unlocks
vanilla a sus propias recipes — con Bob's/Angel's la tech `plastics`
desbloquea `bob-plastic-pipe`/`angels-solid-plastic`, NO `plastic-bar` (que
queda sin NINGUNA tech en el mapa, ni hidden). Consecuencia: items base como
plastic-bar/resin/rubber/wax/polysaccharides no tienen tech que les
corresponda → baseline → caían a materials-1 regalados. Solución: el override
de tier por nombre (ver MOD_ORE_TIERS en cost-solver) también cubre MATERIALES
no-ores (plastic-bar→3, resin/rubber/wax/polysaccharides/sulfuric-acid/
nitrogen/nitric-acid→3, ammoniacal/lava/blood/lymph/royal-jelly→4, sand→2...).

**Fix de techs materials (locale + pack)**: las 5 techs `dmrsa-replication-materials-N`
no definían `localised_name` explícito (dependían de key por-tier → renderizaba
key cruda si faltaba) y `make_research_unit` podía dejar `ingredients = {}`
cuando el pack tenemut no se detectaba (el tenemut es un TOOL prototype, no
item) → la tech parecía "sin costo de research". Fixes: `localised_name = {
"technology-name.dmrsa-materials-tech", def.tier }` (template explícito) y
fallback de pack que usa CUALQUIER material DMR existente si el especificado
falla (nunca ingredients vacío).

**Issue separado (no lo toca el fix)**: con 138 mods el cost-solver se degrada —
iron-plate/copper-plate cayeron de tier 3 (dump 3.7.1) a tier 1 (dump 4.1.0)
porque más ciclos de recipes resuelven a 1. Los ores de mods (angels-ore1..6,
planetaris-*) también caen a tier 1. Si se retoma, ampliar MOD_ORE_TIERS /
revisar el cost-solver, no el mirror.

## v4.2 FIX (2026-08-23): depth clamp REMOVED + science packs forced — tier inflation
**Síntoma (gate test 4.2.0)**: "muchas cosas se subieron de tiers", logistic/chemical
science pack en tier 5. Dump real (138 mods): **458/474 mirror techs en replication-5** (97%).

**Causa raíz (2 causas apiladas)**:
1. El **tree-depth clamp** (`tier = max(science_level, get_tech_tree_depth(orig_tech))`,
   añadido en el gate test de 4.0 como cinturón-y-tirantes contra "Non-contiguous levels")
   infla TODO con modlists reales: chemical-science-pack tiene depth 22,
   promethium-science-pack depth 80 (la profundidad del árbol modded NO es la progresión).
2. Los **science packs sin force**: el SCL de la tech que desbloquea un pack ≠ el tier de
   progresión del pack (chemical-pack se investiga con packs t1 → SCL=1, pero el PACK es
   progresión tier 3; su recipe además se inflaba por la cadena del cost-solver).

**Fix aplicado en lib/mirror-generator.lua**:
- RECIPES: `local sci_forced = PACK_LEVELS[name] or MOD_PACK_LEVELS[name]; if sci_forced then tier = sci_forced end`
  tras el override de tenemut.
- MIRRORS: `forced_science_tier` = max PACK_LEVELS/MOD_PACK_LEVELS sobre los ITEMS del grupo
  (lookup EXACTO por tabla, sin heurísticas de nombre sobre items arbitrarios); si existe,
  fuerza el tier antes del branch SPREAD_TECHS/SCL.
- **Depth clamp ELIMINADO** (comentario explica por qué). El hazard REAL de contigüidad eran
  las cadenas niveladas `-N` y eso ya lo cubre `normalize_tech_base()`. Si Factorio vuelve a
  rechazar un mirror específico por contigüidad, arreglar ESA cadena — no todo el árbol vía depth.
- `get_tech_tree_depth()` queda definida pero sin llamadas (por si se necesita diagnóstico).

**Resultado FINAL (sim fiel al código + inferencia adaptable activa, ver sección siguiente)**:
distribución 0/4/8/4/458 → **88/15/144/3/180** (+44 fallback cost-solver).
Science packs exactos: auto/logi=1, military=2, chem/prod/util=3, planetarios=4,
space/cryo/prom=5. (La primera sim reportó 253 en t1 porque NO replicaba
`mirror_deepest` — ver pitfall de fidelidad de simulación abajo.)

**Lección general**: un clamp defensivo contra un error de carga concreto ("Non-contiguous")
que escala con la PROFUNDIDAD DEL ÁRBOL es una bomba de tiempo con overhaul mods — el árbol
modded tiene profundidades de 20-80 que nada tienen que ver con la progresión 1-5. Validar
siempre la DISTRIBUCIÓN resultante sobre el dump real antes de publicar (Counter de prereqs
replication-N), no solo la ausencia de crash.

### v4.2 continuación (mismo día, 2026-08-23): ADAPTABILITY + fidelidad de simulación + handoff
- **DECISIÓN DE DISEÑO (usuario): el mod debe ser ADAPTABLE a cualquier modlist, no
  solo la nuestra.** Implementado como `ensure_inferred_pack_levels()` en
  mirror-generator.lua — IMPORTANTE: declarar ANTES de `pack_level` o los upvalues
  resuelven como globals nil (mordido y corregido en vivo). Packs desconocidos se
  anclan dinámicamente: `level(P) = max nivel-tabla entre las techs visibles no-hidden
  que consumen P`, excluyendo kitchen-sinks (>8 ingredientes distintos) para que
  mega-techs endgame no arrastren packs tempranos a L5. Un pase, sin recursión,
  derivado solo de niveles ya tabulados → sin ciclos. Getter testeable:
  `MirrorGenerator.get_inferred_pack_level()` (+5 tests en test_mirror.lua → 54 checks).
  Medido en dump 138 mods: galvanization/golden/planetaris/apicultural/token-bio → L5.
- **PITFALL de fidelidad de simulación (nueva instancia de la clase sim-vs-código)**:
  al simular tiers del mirror en Python HAY QUE replicar `mirror_deepest` — resolver el
  base name a su nivel más profundo `-N` existente antes de calcular SCL (índice regex
  base→nivel sobre los nombres reales del dump). La sim sin esto reportó 253 techs en
  tier 1; la fiel dio 90 — y el usuario detectó la anomalía ("revisa los tier 1 porque
  hay demasiados"). Regla: cuando una sim contradice la intuición del usuario, auditar
  PRIMERO la fidelidad de la sim al código Lua antes de proponer cambios de diseño.
  Los 90 t1 resultaron legítimos: SCL=1 REAL de la modlist del usuario (Bob's mueve
  advanced-circuit a green science; Angel's metallurgy-1/2/ore-crushing SON early game).
- **Handoff entre agentes (patrón del proyecto)**: el repo root mantiene `AGENTS.md`
  como doc de estado para agentes externos — opencode lo lee automáticamente al trabajar
  en esa carpeta. Contenido: qué es el mod, estado exacto (portal vs local), fixes del
  gate test con causas raíz, decisiones de diseño vigentes, arquitectura y orden de
  carga, workflows verificados, pitfalls críticos, issues abiertos. MANTENERLO al día
  tras cada cambio mayor de estado; es el contrato Hermes↔opencode.
- **BATCH F1-F4 — APLICADO (2026-08-23, v4.2.1 lista**; specs originales en
  `research/nosotros-fix-specs.md`): gate test PASÓ → 4.2.0 publicado → batch único.
  F1 `%-vequip$` (6 Angel's vehiculares: burner-generator, fusion-reactor,
  repair/construction-roboport, heavy-energy-shield + rocket-defense hidden —
  MECANISMO del escaparate: son `type="item"` con `place_as_equipment_result`,
  así que también se salvan del registry de vehículos, no solo de bob-vehicle-*/equipment),
  F2 `^rpg_.*_potion$` (8 pociones), F3 `MOD_ORE_TIERS` floors (ver §consumibles).
  Tests: test_mirror 49→68 (+19: 5 vequip + 8 potions + anti-colisión
  `angels-accessory` KEPT — ojo: el fixture KEPT necesita recipe productora en el
  mock o falla el filtro de elegibilidad, no la exclusión).
- **INSIGHT: recycling-circularity hace replicables items drop-only** — las recipes
  `-recycling` autogeneradas (disabled, hidden) CUENTAN como productoras en la regla
  de elegibilidad, así que un item cuya única recipe es su propio `-recycling` pasa
  el filtro (confirmado: existen `dmrsa-repl-rpg_*` en el dump = eran replicables).
  Sobre el dump, la sim con ports que EXCLUYEN recycling del mapa de productores da
  delta −5 (solo vequip) mientras el juego real da −13: discrepancia esperada entre
  sim y juego — reconciliar contando las recipes en la regla de elegibilidad de la
  MISMA forma que `is_produced_by_recipe` del código, no como `build_recipe_map`.
- **Anomalía fission-construction-robot VERIFICADA (dump)**: sin recipe productora
  real (solo `-recycling` disabled + `-macerating` que la CONSUME; nunca unlocked por
  tech), `hidden_in_factoriopedia=true`, `place_result` a entidad construction-robot
  propia → probablemente entregado por script/evento o huérfano del mod. KEEP t3
  mantenido; verificar obtención in-game cuando se pruebe 4.2.1.
- **Estado 4.2.1**: zip construido (114 files, parity portal sin ROADMAP/FAQ, version
  bump en info.json, changelog prepend NORMAL — el accumulated-NOTE solo aplica cuando
  hay múltiples versiones sin publicar, no en patches), suite 68+54+41+step_filter
  PASS, privacy CLEAN. RESUELTO: usuario sube el zip al portal desde su PC;
  **GitHub push de 4.2.1 SKIPPEADO por decisión del usuario** (solo portal esta vez)
  — el AGENTS.md quedó documentado con esa decisión. Lección de flujo: para ESTE
  usuario el push a GitHub es por-versión OPCIONAL — preguntar antes de pushear, no
  asumir; el push en sí puede requerir aprobación del gate de comandos (`rm -rf` del
  clon temporal + force push → se bloquea esperando consentimiento).

## Balance: tenemut replicable SOLO a tier 5 (2026-08-13, "Dominio de la Materia Oscura")
Decisión del usuario: el tenemut (materia prima del mod / moneda de research)
NO se replica hasta el tier 5 — cierre de ciclo temático: llegas al
replicator-5 → dominas la materia oscura → puedes replicar SU materia prima.
El resto de items `dmrsa-*` (scoop, transducer, conduit, lab, replicadores)
SIGUE sin replicarse (anti-loop).
Implementación (2 archivos):
- `lib/target-mapper.lua`: la regla anti-loop de prefijo `dmrsa-` ahora
  EXCLUYE solo `name ~= gprefix .. "tenemut"` — el tenemut pasa el filtro.
- `lib/mirror-generator.lua`: en el bucle de recipes, `if name == gprefix ..
  "tenemut" then tier = 5 end` — cae al baseline tier 5 → se desbloquea con
  `replication-materials-5` (máquina tier 5 + conduit).
Alternativa descartada: tier 4 (haría triviales los packs de tier 5); replicar
desde el principio (rompería TODO el balance del mod). Los DERIVADOS del
tenemut (scoop/transducer/conduit) podrían replicarse en su tier natural sin
romper nada (el cuello de botella sigue siendo el tenemut minado) — quedó como
decisión futura; el usuario prefirió mantenerlos NO replicables por ahora.

## Por qué existe
El sistema v3.x categoría→tier (ver skill dmr-category-tier-refactor) NO gateaba
la progresión de verdad. Análisis dump: 46% de items en `general` (sin piso),
503 items cuyo tier no coincidía con el science level de su tech original, y 25
offenders endgame en tier 3 (requester-chest, mech-armor, nuclear-fuel, ...).
Causa raíz: el cost-solver (cadena de ingredientes) es una mala señal de
progresión; la señal correcta es la TECH ORIGINAL del item.

## El sistema
- UNA tech de replicación por cada tech ORIGINAL del juego: "Replication:
  Logistic System" desbloquea las recipes de replicación de TODOS los items que
  esa tech desbloquea.
- Grouped Categories ELIMINADO. Las categorías (shape/alloy/chemical/...) quedan
  SOLO como subgroups visuales del menú de crafting.
- Tier de cada mirror tech = science level de su tech original (automation/
  logistic=1, military=2, chemical/production/utility=3, planetary=4,
  space/cryogenic/promethium=5). Packs de mods: bob-science-pack-gold,
  bob-alien-science-pack-* → 5 (tabla MOD_PACK_LEVELS).
- Cadena de progresión: replication-N (máquina) → replication-materials-N
  (materiales base del tier, con tenemut/scoop/transducer/conduit) → mirror
  techs (prereq: máquina + materials + tech original si
  dmrsa-require-original-tech=ON).
- threshold=1: toda tech original con ≥1 item replicable genera su mirror
  (sin tamaño mínimo de grupo).
- Items SIN tech original (ores, fluidos, placas, básicos vanilla, ~88-93) →
  baseline, desbloqueados por la materials tech de su tier.
- Items planetarios (50, subgroup dmrsa-replication-resources) mantienen su
  routing a las planetary techs (vulcanus/fulgora/gleba/aquilo).

## Exclusiones v4.0 (144 items) — aprobadas por el usuario 2026-08-12
EXCLUIDOS (1-solo-uso, no producción masiva): guns (11), armor (10), combat
capsules (10: patrones grenade/capsule/explosives/poison/slowdown/defender/
distractor/destroyer/fire/laser-robot), vehículos (27: car/tank/spider-vehicle/
locomotive/cargo-wagon/fluid-wagon/artillery-wagon), vehicle equipment (50:
bob-vehicle-*), personal equipment (36: `*-equipment$` EXCEPTO solar/battery).
KEPT (uso masivo): munición (55, aliens), fuel cells (10, reactores), seeds (3,
Gleba), raw-fish (curar), solar panels + baterías (9).

## Archivos
- `lib/mirror-generator.lua` (NUEVO) — recipes + reverse map (tech → items) +
  mirror techs + attach baseline→materials. Devuelve planetary_unlocks.
- `lib/target-mapper.lua` — `is_v4_excluded()` (tipos + patrones).
- `data-final-fixes.lua` — PASS 0 elige Mirror (default) vs Individual (legacy);
  PASS 6 (re-attach) ELIMINADO (innecesario: reverse map se construye con datos
  finales y el prereq ES la tech original).
- `prototypes/technologies/technologies.lua` — 5 techs replication-materials-N
  (effects vacíos, se llenan en generate()).
- `settings.lua` — `dmrsa-require-original-tech` (bool, default true);
  `dmrsa-tech-distribution`: "Mirror" (default) / "Individual" (legacy v3.x).
- `defines.lua` — dmrsa_is_v21() ELIMINADO (2.1 only, categories array).
- `info.json` — 4.0.0, factorio_version "2.1".
- `prototypes/recipes/dynamic-generator.lua` — se mantiene como generador legacy
  Individual; grouped desactivado (use_grouped_techs=false).
- locale en/es-ES — dmrsa-mirror-tech, dmrsa-materials-tech,
  replication-materials-1..5, setting require-original-tech. 2026-08-14:
  `dmrsa-matter-conduit` renombrado a "Nanophase Conduit" (EN) / "Conducto
  nanofase" (ES) — único renaming aplicado del lote propuesto.
- `dmr-tests/test_mirror.lua` (NUEVO) — 30 checks: get_tech_science_level +
  exclusiones v4.0. Correr con lua5.2.

## Renaming de materiales + nuevo item tier 5 (PROPUESTA 2026-08-13 → DESCARTADA en su mayoría 2026-08-14)
El usuario quería rehacer los iconos de tenemut/scoop/transducer/conduit, renombrarlos
y AGREGAR UN ITEM NUEVO para el tier 5 (hoy el tier 5 reutiliza matter-conduit en
`technologies.lua` materials_defs: `{tier=5, pack=gprefix.."matter-conduit"}` y en
`tier_material_pack()` del mirror-generator: tier 4 Y 5 → matter-conduit).
Propuesta original (tema: progresión de dominio sobre la realidad): Tenemut (se mantiene),
**Resonance Latch** (hoy scoop), **Atomic Loom** (hoy transducer), **Nanophase Conduit**
(hoy conduit), **Genesis Loom** (NUEVO item `dmrsa-genesis-loom`, cierra el arco con el
tenemut tier-5). IMPORTANTE (si se retoma): mantener los IDs internos y cambiar SOLO display
names vía locale → cero riesgo de saves rotos; el tier 5 sí es ID nuevo + recipe. Tocará:
dark-matter.lua, base-recipes.lua, technologies.lua (pack tier 5), tier_material_pack(),
locale EN/ES, iconos.
**ESTADO FINAL 2026-08-14 (decisión del usuario)**: el renaming completo NO convenció y se
DESCARTÓ. Solo se aplicó `matter-conduit` → "Nanophase Conduit" (EN) / "Conducto nanofase"
(ES) en locale — sin tocar IDs, recipes ni techs. Genesis Loom queda SIN implementar
(shelved, no hay fecha). Los iconos IA se descartaron por completo (ver abajo). No retomar
el renaming ni Genesis Loom sin petición explícita del usuario.

## Generación de iconos por API (2026-08-13 verificado → 2026-08-14 DESCARTADO)
Ver `references/dmr-icon-assets-generation.md`. ESTADO FINAL: el usuario DESCARTÓ la
generación de imágenes por IA (Gemini dio cartoon ×2, Canva Pro dio renders 3D) y pidió
eliminar las referencias e investigación. Datos verificados que quedan documentados ahí por
si algún día se retoma: opencode-go NO genera imágenes (25 modelos, todos chat/texto);
GOOGLE_API_KEY y OPENROUTER_API_KEY válidas en el archivo de env del perfil
local; Google free-tier
429 quota 0 para modelos de imagen; OpenRouter tiene los modelos pero la cuenta requiere
ajustar data-policy en openrouter.ai/settings/privacy (404). El prompt de familia coherente
(paleta #0a0a14/#7c3aed) y el anti-cartoon/anti-3D anchoring también están en esa referencia.

## Números (dump 3.7.1, Bob's+SA)
945 items → 144 excluidos → 801 replicables → 713 con tech original → ~417
mirror techs (300 single + ~117 multi) + 5 materials + 4 planetary ≈ 426 techs
(vs 945 individuales en v3.x).

## Preferencias de workflow del usuario (observadas 2026-08-12)
- Design-first: brainstorming con opciones A/B/C/D → elegir → VERIFICAR con
  datos del dump ANTES de implementar.
- Cuando el usuario referencia una opción del brainstorm ("la opción A", "el
  umbral", "individual"), RE-LEER todos los mensajes desde ese punto antes de
  interpretar — el shorthand puede significar algo distinto a la lectura obvia
  ("individual" = threshold-1 mirror, NO techs por item; el malentendido costó
  varios round-trips).
- Rediseños grandes: mantener la versión publicada intacta, crear backup tar.gz
  antes de tocar, trabajar con seguridad de reversión.
- Quality support: IMPLEMENTADO en v4.1.0 (Quality Refiner) — ver sección
  v4.1.0 arriba. Baseline inflado por outputs de proceso (v4.2): IMPLEMENTADO
  en v4.2.0 (fix process-output techs + override universal de tier de
  materiales) — ver sección v4.2. Pendiente para otra iteración: la
  degradación global del cost-solver con 138 mods (iron-plate 3→1) y el review
  del modlist final tras el gate test.
