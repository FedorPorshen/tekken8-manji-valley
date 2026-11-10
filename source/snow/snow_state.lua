-- Unreal centimetres. Engine-independent contact, impact and reset logic.
local Snow = {}; Snow.__index = Snow
local function distance(a,b) return math.sqrt((a.x-b.x)^2+(a.y-b.y)^2) end
function Snow.new(draw,burst,clear)
    return setmetatable({draw=draw,burst=burst,clear=clear,players={}},Snow)
end
function Snow:reset()
    self.players={}; self.clear()
end
function Snow:update(round,fighters)
    if self.round~=round then self:reset(); self.round=round end
    for i,f in ipairs(fighters) do
        local old=self.players[i]
        if old and distance(f.root,old.root)>220 then self:reset(); break end
    end
    for i,f in ipairs(fighters) do
        local old=self.players[i]
        if f.down and not(old and old.down) then
            local impact={x=f.root.x,y=f.root.y,z=f.floor}
            self.draw(impact,impact,58,.98); self.burst(impact,58)
        end
        local feet={}
        for k,foot in ipairs(f.feet) do
            local contact=foot.z-f.floor
            if contact>=-40 and contact<=24 then
                local last=old and old.feet[k]
                if not last then self.draw(foot,foot,18,.95); feet[k]=foot
                elseif distance(last,foot)>=4 then self.draw(last,foot,18,.95); feet[k]=foot
                else feet[k]=last end
            end
        end
        self.players[i]={root={x=f.root.x,y=f.root.y,z=f.root.z},feet=feet,down=f.down}
    end
end
return Snow
