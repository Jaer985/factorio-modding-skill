# Prototype registries & data-stage audit fixes (Factorio 2.x)

Lecciones de clase del audit batch-3 de DMR (dump real 138 mods, sep-2026).
Aplican a CUALQUIER mod que genere prototypes dinámicamente (data-final-fixes)
y lo audite contra un dump de modlist real.

## 1. data.raw.item NO es el único registry de items

Factorio 2.x separa clases de items en registries propios. Un guard
defensivo `data.raw.item[name]` los escupe todos:

| Registry | Qué contiene | Ejemplo del dump |
|---|---|---|
| `item` | items genéricos | fast-inserter |
| `tool` | **science packs** y herramientas | apicultural-science-pack, dmrsa-tenemut |
| `ammo` | munición | piercing-rounds (66 en dump) |
| `module` | módulos | speed-module (39) |
| `capsule` | cápsulas | (35) |
| `movement-bonus-equipment`, `energy-shield-equipment`, `night-vision-equipment`, `generator-equipment`, ... | equipo equipable (una registry POR categoría) | aircraft-afterburner |

- **Síntoma típico**: "142 targets con quality sin recipes de refiner" — el
  guard por registry estrecho los salta en silencio.
- **Fix de clase**: resolver de prototypes multi-registry
  (`{item, ammo, module, capsule, tool}` en orden) en UN helper y usarlo
  en TODOS los guards del archivo.
- **Pitfall de debugging**: si un item "no existe" en tu shard/dump, verificá
  en qué registry cae ANTES de concluir que no existe. Un science pack type
  `tool` no aparece en la sección `item` del dump — una hora se fue en el
  misterio de "apicultural-science-pack ruteada a gleba sin explicación"
  cuando el check inicial miraba la gaveta equivocada (y sí: era spoilable,
  la regla gleba era correcta).

## 2. Señales estructurales > patrones de nombre

- `place_as_equipment_result` (en el PROTO) marca equipo equipable aunque el
  nombre no contenga "-equipment". 4 leaks reales (aircraft-afterburner,
  aircraft-energy-shield, angels-cab-energy-interface-mk1,
  manual-color-module) escapaban a TODO patrón de nombre y escaparían a
  cualquier mod nuevo con nombres creativos. El guard estructural los
  captura a todos; excepciones de clase (solar/battery) se aplican igual.
- Para routing planetario: `default_import_location` y producer
  `surface_conditions` identifican items exclusivos de planeta EXACTAMENTE —
  las heurísticas por keyword del nombre dejan escapar todo lo que no
  matchea (13 items de fulgora en bandas numéricas).

## 3. Herencia cruzada por prefijo vacío

`mod_prefix(name)` que retorna `""` para nombres SIN guión hace que DOS
items de mods distintos sin guión compartan "prefijo" (`sulfur` vanilla vs
`biosulfur` de Bio Ind) → el item vanilla hereda la tech del mod ajeno
(gleba T5). Fix de clase: prefijo vacío ≠ match — requiere prefijo REAL
compartido (ambos con guión y mismo segmento).

## 4. Tus propias techs entran al reverse-map

Si generás techs `dmrsa-replication-N` (una por tier) y después construís
un mapa tech→items desde TODAS las techs con unlock-recipe, tus propias
techs entran y `normalize_tech_base()` colapsa los `-N` en UN mirror
→ self-mirror roto (replicadores 1/2/4/5 en una tech t5, el tier-3
secuestrado por la tech de otro planeta). Fix: filtrar `dmrsa%-` del
reverse-map ANTES de llenarlo (blast radius = solo tus items propios).

## 5. Anti-patrón: max-SCL-wins para elegir la tech de un item

Elegir la tech desbloqueadora con MAYOR science level hace que items
tempranos queden gated detrás de techs endgame (solid-fuel →
planet-discovery-aquilo T5; lubricant/sulfur → bioflux T5). Modlists
grandes re-gatean recipes de vanilla todo el tiempo. Fix de clase:
TECH_REDIRECT manual por item (dump-proven) para los casos visibles, y
regla de selección preferente por SCL más CERCANO al tier del solver, no
el máximo.

## 6. Invariantes de routing dinámico

- Un `planet_suffix` nuevo debe referenciar una categoría `replication-<X>`
  EXISTENTE y una key del dict `planetary_unlocks` — asignar "space" sin
  categoría crashea la carga. Antes de añadir una rama de routing:
  verificar categoría + key.
- VERIFICAR EN EL DUMP cada nombre de tech/item que hardcodeás
  (TECH_REDIRECT, MOD_PACK_LEVELS, exclusiones) antes de escribir el patch.
  Un nombre inexistente (`planetaris-gold-processing`) es un prereq
  inválido en producción. Un query de 30s vs un crash del mod.
- La inferencia dinámica de niveles (packs desconocidos) debe tener CAP:
  el max-anchor sobre-ancla packs mid-game a T5 vía co-consumo en techs
  endgame (62 mirrors inflados en el dump). Tier 5 = solo tablas/familias
  explícitas.

## 7. Locale/code drift

- Descripción de setting que dice "multiplicador (cost × (1+pen))" mientras
  el código aplica "aditivo (cost + pen)" = el jugador tunea con el modelo
  mental equivocado. Al cambiar la SEMÁNTICA de un setting, auditar su
  descripción EN y ES.
- Toda setting necesita key en `[mod-setting-name]` Y
  `[mod-setting-description]` (el nombre cae al raw key con "Unknown key"
  en el log). Contarlas: names == descs.
- Verificar realidad de line-endings con bytes (CRLF vs LF) antes de
  asumir la convención documentada — el doc puede estar stale.

## 7. Listas single-source sincronizadas

Cuando el mismo set de items vive en varias decisiones (gate de tier, filtro
de hidden, whitelist de elegibilidad), declara UNA lista por archivo y
mantenelas sincronizadas con comentario cruzado ("mirrors X, keep in sync").
Caso real DMR D17: los 6 chunks espaciales viven en `SPACE_CHUNKS`
(mirror-generator: gate t5+gravity0), `SPACE_CHUNK_TARGETS` (target-mapper:
filtro de hidden) y `ELIGIBILITY_WHITELIST` (target-mapper: obtenibilidad) —
auric/bismuth faltaban en la whitelist y escapaban TODA la cadena hasta
llegar por accidente vía un swallow de steam-recycler.

## 8. Debug de filtros por capas

Si un check de test falla para un item que "debería" pasar, NO asumas que
la capa obvia (el filtro que acabás de tocar) es la culpable. El pipeline
de exclusión tiene CAPAS en orden (prefijo propio → blacklist → elegibilidad
→ exclusiones v4 → hidden) y el fallo puede estar en una capa DIFERENTE a
la editada. Caso real: test de chunks falló tras arreglar el filtro de
hidden; la causa era la ELIGIBILITY_WHITELIST (otra capa, otro bloque).
Método: correr el item contra cada capa en orden, no adivinar.

## 9. Spread por nivel: elegibilidad dinámica + routing por membresía

Para des-colapsar cadenas `-N` (un mirror por nivel de tech), la elegibilidad
se computa DINÁMICAMENTE de la modlist cargada (no hardcodear cadenas —
principio "adaptable a cualquier modlist"). Filtros dump-validated:
1. la tech PLAIN de nivel 1 existe (si no, la cadena espejo rompe contigüidad);
2. niveles contiguos 1..deepest;
3. deepest >= 3 (cadenas 1-2 no tienen brecha real);
4. cada nivel se queda con >=1 item (atribución: min nivel cuya tech
   desbloquea una recipe productora del item; huérfanos → deepest);
5. span de tiers >= 2 (si no, el split no cambia gameplay, solo ruido).

Y el routing de items a su nivel es por MEMBRESÍA (`map[item]`
pre-construido), no por iteración de las techs del item: iterar techs puede
desviar un item al fallback de best-tech y dejar un mirror de nivel VACÍO →
crash "Non-contiguous levels". El map garantiza base + niveles no vacíos.
En el loop de tier, los mirrors por-nivel toman el tier de sus ITEMS
(costo/máquina), NO el SCL de la tech original — un level-N tech investiga
con packs profundos mientras sus items son mid-game (ese es el punto del
spread).

## 10. Rebalance grande = simulación read-only ANTES de tocar código

Para rebalances que tocan todo el dataset (re-escala de costos, cambio de
routing global): NO implementar directo. Fase intermedia: dispatch 1-2
subagentes READ-ONLY que (a) diseñan el modelo concreto, (b) lo simulan en
Python sobre el dump, (c) entregan el antes/después (distribución por tier,
% en bordes, outliers, regresiones). Presentar los números al usuario →
implementar solo con OK. La lección del gate test 4.2.0 (depth clamp infló
458/474 mirrors a t5 — detectado EN el dump, después de implementar) es la
razón: el rebalance equivocado se ve en la simulación, no en código.
Baseline de la sim = código vigente recategorizado con las reglas actuales,
no el dump crudo de una versión vieja.

## Workflow del fix (validado)

1. Backup de archivos a tocar → `backups/<batch>-pre/`.
2. Evidencia del dump ANTES del patch (nombres, flags, categorías).
3. Patch → `luac5.2 -p <file>` → suite completa (los 4 test files).
4. Tests de regresión NUEVOS para cada fix de clase (fixture que reproduce
   el leak + check del comportamiento esperado).
5. Docs del proyecto al día (ROADMAP/AGENTS) con lo aplicado vs lo
   pendiente de decisión — separar "bug con fix claro" de "decisión de
   diseño".
6. Rebalance global (costos/routing): SIMULACIÓN read-only primero (ver §10)
   — presentación con números al usuario antes del patch.
