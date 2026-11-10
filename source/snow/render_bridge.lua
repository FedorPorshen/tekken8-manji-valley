local Bridge={}; Bridge.__index=Bridge
function Bridge.new(Snow,rendering,world,target,stamp,burst)
    local self=setmetatable({pending={},draws=0,marks=0,clears=0},Bridge)
    self.rendering,self.world,self.target,self.stamp=rendering,world,target,stamp
    self.state=Snow.new(function(a,b,radius,depth)
        local ax,ay=(a.x+4200)/8400,(a.y+4200)/8400
        local bx,by=(b.x+4200)/8400,(b.y+4200)/8400
        local r=radius/8400
        if math.max(ax,bx)<-r or math.max(ay,by)<-r or math.min(ax,bx)>1+r or math.min(ay,by)>1+r then return end
        self.pending[#self.pending+1]={ax,ay,bx,by,r,depth}
    end,burst,function()
        self.pending={}; rendering:ClearRenderTarget2D(world,target,{R=0,G=0,B=0,A=0})
        self.clears=self.clears+1
    end)
    return self
end
function Bridge:flush()
    for first=1,#self.pending,4 do
        for slot=0,3 do
            local m=self.pending[first+slot]
            self.stamp:SetVectorParameterValue('Segment'..slot,m and {R=m[1],G=m[2],B=m[3],A=m[4]} or {R=0,G=0,B=0,A=0})
            self.stamp:SetVectorParameterValue('Settings'..slot,m and {R=m[5],G=m[6],B=0,A=0} or {R=0,G=0,B=0,A=0})
            if m then self.last=m; self.marks=self.marks+1 end
        end
        self.rendering:DrawMaterialToRenderTarget(self.world,self.target,self.stamp)
        self.draws=self.draws+1
    end
    self.pending={}
end
function Bridge:tick(round,fighters)
    self.state:update(round,fighters); self:flush()
end
function Bridge:practice_reset() self.state:reset() end
return Bridge
