-- boilerplate-dispatcher.lua
-- Modular Event Dispatcher for Factorio 2.0 / Space Age
-- Optimizes main loop overhead and simplifies module coupling.

local dispatcher = {
  handlers = {}
}

-- Module-scope caching for hot path performance
local pairs = pairs
local table_insert = table.insert

--- Register a callback for a specific event
-- @param event_id number The event ID (from defines.events)
-- @param handler_name string Unique identifier for this callback
-- @param callback function The callback function to execute
-- @param filters table Optional filter table for high-frequency events (mandatory for on_built, etc.)
function dispatcher.register(event_id, handler_name, callback, filters)
  if filters then
    -- High-frequency events MUST use engine-level C++ filters
    script.on_event(event_id, callback, filters)
  else
    -- General events are multiplexed inside a single handler to reduce main loop overhead
    if not dispatcher.handlers[event_id] then
      dispatcher.handlers[event_id] = {}
      script.on_event(event_id, function(event)
        for _, handler in pairs(dispatcher.handlers[event_id]) do
          handler(event)
        end
      end)
    end
    dispatcher.handlers[event_id][handler_name] = callback
  end
end

--- Deregister a callback
-- @param event_id number The event ID
-- @param handler_name string Unique callback identifier
function dispatcher.deregister(event_id, handler_name)
  if dispatcher.handlers[event_id] then
    dispatcher.handlers[event_id][handler_name] = nil
  end
end

return dispatcher
