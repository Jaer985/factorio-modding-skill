# Tech Deadlock Diagnosis

## Common deadlock patterns

### 1. Lab-gated technology

**Symptoms**: "Researched by Craft [Item: X]" on tech card, tech shows (Unavailable), no craft-item triggers found in any mod.

**Root cause**: The technology has `category = "crafting"` which only matches a lab with `research_category = "crafting"`. If that lab isn't available (recipe broken, entity not placed), the tech is permanently unavailable.

**Diagnosis**:
```lua
-- In data-final-fixes.lua debug mod:
for name, tech in pairs(data.raw.technology) do
  if tech.category == "crafting" then
    log("debug: tech '" .. name .. "' has category=crafting")
  end
end
for name, lab in pairs(data.raw["lab"] or {}) do
  log("debug: lab '" .. name .. "' research_category=" .. tostring(lab.research_category))
end
```

**Fix**: Change the tech's category to match an available lab, or change the lab's `research_category`.

### 2. Missing prerequisite technology

**Symptoms**: "Prerequisite technology X does not exist" in log.

**Root cause**: Mod A depends on a tech from Mod B, but Mod B's version removed or renamed it.

**Fix**: Strip invalid prerequisites in data-final-fixes.lua:
```lua
for name, tech in pairs(data.raw.technology) do
  if tech.prerequisites then
    local valid = {}
    for _, p in ipairs(tech.prerequisites) do
      if data.raw.technology[p] then table.insert(valid, p) end
    end
    tech.prerequisites = valid
  end
end
```

### 3. Missing recipe ingredient

**Symptoms**: Recipe won't show in crafting menu, or Factorio errors at load.

**Root cause**: A mod changed a recipe to use an item that doesn't exist or was removed by another mod.

**Fix**: Validate ingredients and replace only the missing ones:
```lua
for name, recipe in pairs(data.raw.recipe) do
  if recipe.ingredients then
    local valid = {}
    for _, ing in ipairs(recipe.ingredients) do
      local iname = ing.name or ing[1]
      if iname and (data.raw.item[iname] or data.raw.fluid[iname]) then
        table.insert(valid, ing)
      end
    end
    recipe.ingredients = #valid > 0 and valid or nil
  end
end
```

## Debug workflow

1. Create a minimal debug mod (info.json + data-final-fixes.lua)
2. Use `log()` to dump prototype structures at load time
3. Check `factorio-current.log` for your tagged output
4. Key things to inspect: `technology.category`, `technology.unit.trigger`, `lab.research_category`, recipe ingredients
5. Iterate: add more logging, reload, read log
6. Once you understand the structure, create the fix

## The "Craft [Item: X]" distinction

| Display | Actual mechanism | How to detect |
|---------|-----------------|---------------|
| "Craft [Item: X]" + "Unavailable" | Lab-gated tech (category matches a specific lab) | Scan `technology.category` + `lab.research_category` |
| "Craft [Item: X]" + progress bar | craft-item trigger | Scan `technology.unit.trigger` for `type = "craft-item"` |

If you scan ALL technologies and find ZERO craft-item triggers, the display is always lab-based, never trigger-based.
