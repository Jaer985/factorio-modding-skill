-- data.lua
-- Generated from factorio-modding skill template
-- Factorio 2.0 / Space Age compatible

-- ============================================
-- Helper: Icon specification
-- ============================================
local function icon(name, size)
  return {
    icon = "__MOD__/graphics/icons/" .. name .. ".png",
    icon_size = size or 64
  }
end

-- ============================================
-- Items
-- ============================================
local items = {
  {
    type = "item",
    name = "my-mod-item",
    localised_name = {"item-name.my-mod-item"},
    localised_description = {"item-description.my-mod-item"},
    icons = {icon("my-mod-item", 64)},
    stack_size = 100,
    subgroup = "my-mod-items",
    order = "a"
  }
}

-- ============================================
-- Recipes
-- ============================================
local recipes = {
  {
    type = "recipe",
    name = "my-mod-item",
    localised_name = {"recipe-name.my-mod-item"},
    icons = {icon("my-mod-item", 64)},
    energy_required = 5,
    ingredients = {
      {type = "item", name = "iron-plate", amount = 10}
    },
    results = {
      {type = "item", name = "my-mod-item", amount = 1}
    },
    allow_quality = true,
    quality_affects_product = true,
    enabled = false -- must be unlocked via technology
  }
}

-- ============================================
-- Technologies
-- ============================================
local technologies = {
  {
    type = "technology",
    name = "my-mod-tech",
    localised_name = {"technology-name.my-mod-tech"},
    icons = {icon("my-mod-tech", 256)},
    effects = {
      {type = "unlock-recipe", recipe = "my-mod-item"}
    },
    prerequisites = {"automation"},
    unit = {
      count = 50,
      ingredients = {
        {type = "item", name = "automation-science-pack", amount = 1}
      },
      time = 30
    },
    order = "a"
  }
}

-- ============================================
-- Item Group & Subgroup
-- ============================================
local groups = {
  {
    type = "item-group",
    name = "my-mod",
    localised_name = {"item-group-name.my-mod"},
    icon = "__MOD__/graphics/icons/group-icon.png",
    icon_size = 64,
    order = "d"
  },
  {
    type = "item-subgroup",
    name = "my-mod-items",
    localised_name = {"item-subgroup-name.my-mod-items"},
    group = "my-mod",
    order = "a"
  }
}

-- ============================================
-- Extend all prototypes
-- ============================================
data:extend(items)
data:extend(recipes)
data:extend(technologies)
data:extend(groups)
