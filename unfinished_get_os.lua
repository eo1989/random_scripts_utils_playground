--[[
some functions to play around with.
check ~/dev/lua_dev/*.lua for more knowledge stuffs
]]

os = require("os")

function os.splitpath(s)
  return s:match(s, "(.-)([^\\]-([^%.]+))$") -- should return {/Users/eo/ or} C:\Path\, directory.ext, ext
end

function os.getOS()
  if package.config:sub(1, 1) == '\\' then
    return 'windows'
  elseif package.config:sub(1, 1) == '/' then
    return 'macOS'
  else
  end
  
end
