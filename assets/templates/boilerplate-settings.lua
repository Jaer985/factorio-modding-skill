-- settings.lua
-- Generated from factorio-modding skill template
-- Factorio 2.0 / Space Age compatible

data:extend({
  -- ==========================================
  -- Startup Settings (require restart)
  -- ==========================================
  {
    type = "startup-setting",
    name = "my-mod-enable-feature",
    setting_type = "bool-setting",
    default_value = true,
    order = "a"
  },
  {
    type = "startup-setting",
    name = "my-mod-difficulty-mult",
    setting_type = "double",
    default_value = 1.0,
    minimum_value = 0.1,
    maximum_value = 10.0,
    order = "b"
  },

  -- ==========================================
  -- Runtime Global Settings
  -- ==========================================
  {
    type = "runtime-global-setting",
    name = "my-mod-rate-multiplier",
    setting_type = "double",
    default_value = 1.0,
    minimum_value = 0.01,
    maximum_value = 100.0,
    order = "c"
  },

  -- ==========================================
  -- Runtime Per-User Settings
  -- ==========================================
  {
    type = "runtime-per-user-setting",
    name = "my-mod-show-notifications",
    setting_type = "bool-setting",
    default_value = true,
    order = "d"
  },
  {
    type = "runtime-per-user-setting",
    name = "my-mod-display-mode",
    setting_type = "string-setting",
    default_value = "compact",
    allowed_values = {"compact", "detailed", "minimal"},
    order = "e"
  }
})
