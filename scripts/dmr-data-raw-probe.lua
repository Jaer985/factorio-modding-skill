-- DMR data.raw invariant probe.
-- HOW TO RUN: copy this file as `data-final-fixes.lua` into a throwaway probe mod next to
-- the BUILT ZIP (never next to the source tree) and run the real engine:
--   mkdir -p /tmp/gate/mods && cp dark-matter-replicators-reborn_X.Y.Z.zip /tmp/gate/mods/
--   mkdir -p /tmp/gate/mods/zzz-probe_0.0.1
--   info.json: {"name":"zzz-probe","version":"0.0.1","factorio_version":"2.1",
--               "dependencies":["dark-matter-replicators-reborn"]}
--   cp this file /tmp/gate/mods/zzz-probe_0.0.1/data-final-fixes.lua
--   factorio --mod-directory /tmp/gate/mods --dump-data >/tmp/gate/log 2>&1
--   grep ' DMRPROBE ' /tmp/gate/log
--
-- WHY data-final-fixes: it is the LAST view of the prototypes, after every mod (and the
-- mirror generator) has rewritten them — the same state the player loads. Asserting on the
-- source tree only proves the text you wrote, not the recipes the game shipped.
--
-- A silent deletion never shows up as an error: a recipe dropped by a clamp, a ceiling or an
-- exclusion leaves NO trace in the log. Only a per-tier COUNT catches it — compare the counts
-- against the previous version, not just against zero.

local MARK = "DMRPROBE "
local percat, prod, selfrepl = {}, {}, {}

for name, r in pairs(data.raw.recipe or {}) do
  if name:match("^dmrsa%-repl%-") then
    local cat = (r.categories and r.categories[1]) or "?"
    percat[cat] = (percat[cat] or 0) + 1
    if r.allow_productivity then prod[#prod + 1] = name end
    if name:match("dmrsa%-%-%-?replicator") then selfrepl[#selfrepl + 1] = name end
    if name:match("replicator") then
      log(string.format("%sSELF %s time=%s cat=%s", MARK, name,
        tostring(r.energy_required), cat))
    end
  end
end

local cats = {}
for c, n in pairs(percat) do cats[#cats + 1] = string.format("%s=%d", c, n) end
table.sort(cats)
log(MARK .. "TIERCOUNTS " .. table.concat(cats, " "))
log(MARK .. "PRODUCTIVITY count=" .. #prod .. " [" .. table.concat(prod, ", ") .. "]")

-- The replication tab layout: subgroup order decides row order, item order decides position
-- inside the row. Both are locale-independent — never assert them from the locale file.
for _, sg in ipairs({"dmrsa-replication-resources", "dmrsa-replicators", "dmrsa-power"}) do
  local s = data.raw["item-subgroup"][sg]
  log(MARK .. "SUBGROUP " .. sg .. " order=" .. tostring(s and s.order))
end

for _, nm in ipairs({"dmrsa-replication-lab", "dmrsa-replicator-1", "dmrsa-refiner"}) do
  local e = data.raw.lab[nm] or data.raw["assembling-machine"][nm]
  log(string.format("%sMACHINE %s speed=%s slots=%s", MARK, nm,
    tostring(e and (e.researching_speed or e.crafting_speed)),
    tostring(e and e.module_slots)))
end

log(MARK .. "DONE")
