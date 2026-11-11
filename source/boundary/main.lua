local boundaryTag = FName('ManjiValleyBoundary')
local leftFoot = FName('L_Foot')
local rightFoot = FName('R_Foot')
local parameterNames = {FName('Fighter0'), FName('Fighter1')}
local hidden = {R=0, G=0, B=0, A=1}
local active, queued, ticksUntilScan, lastError

local function valid(object)
    return object ~= nil and object:IsValid()
end

local function clear(state)
    if state and valid(state.material) then
        for _, parameter in ipairs(parameterNames) do
            state.material:SetVectorParameterValue(parameter, hidden)
        end
    end
end

local function findBoundary()
    local battle = StaticFindObject('/Script/Polaris.Default__PolarisBlueprintLibrary')
    if not valid(battle) then return end

    for _, actor in ipairs(FindAllOf('StaticMeshActor') or {}) do
        if valid(actor) and actor:ActorHasTag(boundaryTag) then
            local component = actor.StaticMeshComponent
            local material = component:CreateDynamicMaterialInstance(0, component:GetMaterial(0), FName('None'))
            if valid(material) then
                print('[ManjiBoundary] Boundary material connected\n')
                return {actor=actor, material=material, battle=battle}
            end
        end
    end
end

local function fighterPosition(character)
    if not valid(character) then return hidden end

    -- R/G are Unreal world X/Y and B indicates a valid fighter position.
    local mesh = character:GetMeshComponent()
    if not valid(mesh) then mesh = character.MasterMesh end
    if valid(mesh) and mesh:DoesSocketExist(leftFoot) and mesh:DoesSocketExist(rightFoot) then
        local left = mesh:GetSocketLocation(leftFoot)
        local right = mesh:GetSocketLocation(rightFoot)
        return {R=(left.X+right.X)*0.5, G=(left.Y+right.Y)*0.5, B=1, A=1}
    end

    local location = character:K2_GetActorLocation()
    return {R=location.X, G=location.Y, B=1, A=1}
end

local function update()
    if active and (not valid(active.actor) or not valid(active.material)) then
        clear(active)
        active = nil
    end
    if not active then
        ticksUntilScan = (ticksUntilScan or 1) - 1
        if ticksUntilScan > 0 then return end
        ticksUntilScan = 20
        active = findBoundary()
        if not active then return end
    end

    local mob = active.battle:GetMobManager()
    if not valid(mob) then
        clear(active)
        return
    end
    for index, parameter in ipairs(parameterNames) do
        active.material:SetVectorParameterValue(parameter, fighterPosition(mob:GetTargetPlayer(index-1)))
    end
end

LoopAsync(50, function()
    if not queued then
        queued = true
        ExecuteInGameThread(function()
            local ok, err = pcall(update)
            if not ok then
                local message = tostring(err)
                if message ~= lastError then
                    print('[ManjiBoundary] ' .. message .. '\n')
                    lastError = message
                end
                pcall(clear, active)
                active = nil
                ticksUntilScan = 20
            end
            queued = false
        end)
    end
    return false
end)
