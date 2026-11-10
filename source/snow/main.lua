local Snow=require('snow_state')
local Bridge=require('render_bridge')
local root='/Game/ManjiReactiveSnow/'
local current,queued,scan=nil,false,0
local function log(s) print('[ManjiSnow] '..s..'\n') end
local function valid(o) return o~=nil and o:IsValid() end
local function point(v) return {x=v.X,y=v.Y,z=v.Z} end
local function try(f) local ok,v=pcall(f); if ok then return v end end
local function asset(name)
    local path=root..name..'.'..name
    local o=StaticFindObject(path)
    if not valid(o) then LoadAsset(path); o=StaticFindObject(path) end
    assert(valid(o),'missing cooked asset '..path);return o
end
local function defaults(path)
    local o=StaticFindObject(path);assert(valid(o),'missing defaults '..path);return o
end
local function name_string(n)
    if type(n)=='string' then return n end
    return try(function()return n:ToString()end) or tostring(n)
end
local function foot_mesh(character)
    local mesh=try(function()return character:GetMeshComponent()end)
    if not valid(mesh) then mesh=try(function()return character.MasterMesh end) end
    if not valid(mesh) then return end
    for _,p in ipairs({{'foot_l','foot_r'},{'L_Foot','R_Foot'},{'l_foot','r_foot'},
        {'Bip01 L Foot','Bip01 R Foot'},{'b_l_foot','b_r_foot'},{'LFoot','RFoot'},{'j_foot_l','j_foot_r'}}) do
        local l,r=FName(p[1]),FName(p[2])
        if mesh:DoesSocketExist(l) and mesh:DoesSocketExist(r) then
            log('foot bones '..p[1]..' / '..p[2]);return {mesh=mesh,left=l,right=r}
        end
    end
    local count=try(function()return mesh:GetNumBones()end) or 0
    local left,right
    for i=0,count-1 do
        local bone=mesh:GetBoneName(i);local n=name_string(bone):lower()
        if (n:find('foot',1,true)or n:find('ankle',1,true)) and not n:find('ik',1,true) then
            if n:match('^l[_ ]')or n:match('[_ ]l$')or n:find('left',1,true)then left=bone end
            if n:match('^r[_ ]')or n:match('[_ ]r$')or n:find('right',1,true)then right=bone end
        end
    end
    if left and right then
        log('discovered foot bones '..name_string(left)..' / '..name_string(right))
        return {mesh=mesh,left=left,right=right}
    end
    log('foot bones unavailable; using a conservative grounded root contact')
end
local function stop()
    if current then
        if valid(current.overlay)then current.overlay:SetActorHiddenInGame(true)end
        for _,b in ipairs(current.bursts or {})do if valid(b.actor)then b.actor:SetActorHiddenInGame(true)end end
    end
    current=nil
end
local function read_fighters(s)
    local list={}
    for id=0,1 do
        local p=point(s.battle:GetFighterPosition(id));local floor=s.battle:GetFloorHeightByPlayerID(id)
        if math.abs(p.x)>4500 or math.abs(p.y)>4500 or math.abs(floor)>180 then return end
        list[id+1]={root=p,floor=floor,feet={}}
    end
    if math.abs(list[1].root.x-list[2].root.x)+math.abs(list[1].root.y-list[2].root.y)<2 then return end
    return list
end
local diagnostic
local function waiting(reason)
    if reason~=diagnostic then log('waiting: '..reason);diagnostic=reason end
end
local function discover()
    local battle=StaticFindObject('/Script/Polaris.Default__PolarisBlueprintLibrary')
    if not valid(battle)then waiting('battle library');return end
    local mob=battle:GetMobManager()
    if not valid(mob)then waiting('mob manager');return end
    if not mob:IsPracticeMode()then waiting('Practice battle');return end
    local overlay,holder;local bursts,boundaries={},{}
    for _,a in ipairs(FindAllOf('StaticMeshActor')or {})do
        if valid(a)then
            if a:ActorHasTag(FName('ManjiValleyReactiveSnow'))then overlay=a end
            if a:ActorHasTag(FName('ManjiValleyStampAssets'))then holder=a end
            if a:ActorHasTag(FName('ManjiValleySnowBurst'))then bursts[#bursts+1]={actor=a}end
            if a:ActorHasTag(FName('ManjiValleyBoundary'))then boundaries[#boundaries+1]=a end
        end
    end
    if not valid(overlay)or not valid(holder)then waiting('tagged Manji Valley stage actors');return end
    -- Tekken Practice has no conventional possessed Pawn. The stage actor is
    -- a valid WorldContextObject without UEHelpers' PlayerController lookup.
    local world=overlay
    local s={world_name=overlay:GetFullName(),world=world,overlay=overlay,mob=mob,battle=battle,
        feet={},air={},baseline={},knockdowns={},bursts=bursts,next_burst=0,ticks=0,boundaries={}}
    local fighters=read_fighters(s);if not fighters then waiting('valid fighter positions and floor');return end
    s.rendering=defaults('/Script/Engine.Default__KismetRenderingLibrary')
    s.gameplay=defaults('/Script/Engine.Default__GameplayStatics')
    local target=asset('RT_ManjiTracks')
    s.surface=overlay.StaticMeshComponent:CreateDynamicMaterialInstance(0,asset('M_ReactiveSnow'),FName('None'))
    assert(valid(s.surface),'surface MID failed');s.surface:SetTextureParameterValue(FName('TrackMask'),target)
    local stamp=holder.StaticMeshComponent:CreateDynamicMaterialInstance(0,asset('M_ManjiTrackStamp'),FName('None'))
    assert(valid(stamp),'stamp MID failed');s.stamp=stamp
    for _,a in ipairs(boundaries)do
        local c=a.StaticMeshComponent
        local m=c:CreateDynamicMaterialInstance(0,c:GetMaterial(0),FName('None'))
        if valid(m)then s.boundaries[#s.boundaries+1]=m end
    end
    for id=0,1 do
        local c=mob:GetTargetPlayer(id)
        if valid(c)then s.feet[id+1]=foot_mesh(c)end
        s.baseline[id+1]=fighters[id+1].root.z-fighters[id+1].floor
    end
    for _,b in ipairs(bursts)do
        b.material=b.actor.StaticMeshComponent:CreateDynamicMaterialInstance(0,asset('M_SnowBurst'),FName('None'))
        assert(valid(b.material),'burst MID failed');b.actor:SetActorHiddenInGame(true)
    end
    s.bridge=Bridge.new(Snow,s.rendering,world,target,stamp,function(p)
        if #bursts==0 then return end
        s.next_burst=s.next_burst%#bursts+1;local b=bursts[s.next_burst]
        local now=s.gameplay:GetTimeSeconds(world)
        b.actor:K2_SetActorLocation({X=p.x,Y=p.y,Z=p.z+6},false,{},true)
        b.material:SetScalarParameterValue(FName('BornTime'),now)
        b.actor:SetActorHiddenInGame(false);b.expires=now+1.4
        log('impact snow burst')
    end)
    s.bridge:practice_reset();overlay:SetActorHiddenInGame(false);current=s
    log('ACTIVE automatic Practice snow; RT=2048; pooled bursts='..#bursts)
    log('fighter roots '..fighters[1].root.z..' / '..fighters[2].root.z..'; floor '..fighters[1].floor)
end
local function step()
    if not current then
        if scan<=0 then scan=20;discover()
        else scan=scan-1 end
        return
    end
    local s=current
    if not valid(s.overlay)or not valid(s.mob)or not s.mob:IsPracticeMode()then stop();return end
    local world=s.world
    local observed=read_fighters(s);if not observed then return end
    for _,m in ipairs(s.boundaries)do
        if valid(m)then
            for i,f in ipairs(observed)do
                m:SetVectorParameterValue(FName('Fighter'..(i-1)),{R=f.root.x,G=f.root.y,B=f.floor,A=1})
            end
            m:SetScalarParameterValue(FName('TrackingReady'),1)
        end
    end
    if s.reset then
        s.bridge:practice_reset();s.air={};s.knockdowns={};s.reset=false
        for _,b in ipairs(s.bursts)do b.actor:SetActorHiddenInGame(true);b.expires=nil end
        log('practice reset: tracks cleared')
    end
    for i,f in ipairs(observed)do
        local h=f.root.z-f.floor-s.baseline[i];local old=s.air[i]or 0;local feet=s.feet[i]
        if feet and valid(feet.mesh)then
            local l=point(feet.mesh:GetSocketLocation(feet.left));local r=point(feet.mesh:GetSocketLocation(feet.right))
            if math.abs(l.x-f.root.x)+math.abs(l.y-f.root.y)<190 and math.abs(r.x-f.root.x)+math.abs(r.y-f.root.y)<190 then f.feet={l,r}end
        elseif h<20 then
            f.feet={{x=f.root.x,y=f.root.y,z=f.floor}}
        end
        f.down=(h<=18 and old>35)or s.knockdowns[i]or false
        if f.down then s.knockdowns[i]=nil end
        s.air[i]=h
    end
    s.bridge:tick(s.battle:GetBattleRound(),observed);s.ticks=s.ticks+1
    local now=s.gameplay:GetTimeSeconds(world)
    for _,b in ipairs(s.bursts)do if b.expires and now>b.expires then b.actor:SetActorHiddenInGame(true);b.expires=nil end end
    if s.bridge.marks>0 and not s.probed then
        local m=s.bridge.last
        local pixel=s.rendering:ReadRenderTargetRawPixel(world,s.bridge.target,
            math.floor((m[1]+m[3])*.5*2048),math.floor((m[2]+m[4])*.5*2048),false)
        log('GPU mask probe R='..tostring(pixel.R)..' G='..tostring(pixel.G));s.probed=true
    end
    if s.ticks%200==0 then log('tracking: marks='..s.bridge.marks..' draws='..s.bridge.draws..' clears='..s.bridge.clears)end
end
local function hook(path,callback)
    local ok,err=pcall(RegisterHook,path,callback)
    if not ok then log('optional hook unavailable: '..path..' '..tostring(err))end
end
hook('/Script/Polaris.PolarisCharacterActor:OnDown',function(_,param)
    if current then
        local id=try(function()return param:get().player_id end)
        if id==0 or id==1 then current.knockdowns[id+1]=true end
    end
end)
hook('/Script/Polaris.PolarisCharacterActor:OnResetPlayerPhysics',function()
    if current then current.reset=true end
end)
local last_error
LoopAsync(50,function()
    if not queued then
        queued=true
        ExecuteInGameThread(function()
            queued=false
            local ok,err=pcall(step)
            if not ok then
                if tostring(err)~=last_error then log('ERROR '..tostring(err));last_error=tostring(err)end
                pcall(stop);scan=40
            end
        end)
    end
    return false
end)
log('loaded; waiting for native Manji Valley Practice, no hotkey required')
