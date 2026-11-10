from pathlib import Path
import sys
sys.path.insert(0,str(Path('work/t8/lua-deps').resolve()))
from lupa import LuaRuntime
runtime=LuaRuntime();folder=Path('work/t8/reactive-snow-runtime')
for name in ('snow_state','render_bridge'):runtime.globals()[name]=runtime.execute((folder/(name+'.lua')).read_text())
runtime.execute('''
local function obj(t)
 t=t or {};t.IsValid=function()return not t.dead end;return t
end
function FName(n)return n end
local assets={};game_thread=false;px,pz,clock,round=0,80,0,1;loaded,practice=false,true
local function mid()
 return obj({SetVectorParameterValue=function(s,k,v)s[k]=v end,
 SetScalarParameterValue=function(s,k,v)s[k]=v end,SetTextureParameterValue=function(s,k,v)s[k]=v end})
end
local function actor(tag)
 return obj({ActorHasTag=function(_,n)return tag==n end,
 GetFullName=function()return 'StaticMeshActor /Game/Stage/ST04_Colosseum/Sublevels/ST04_Mob_1.'..tag end,
 SetActorHiddenInGame=function(s,h)s.hidden=h end,
 K2_SetActorLocation=function(s,p)s.position=p end,
 StaticMeshComponent=obj({CreateDynamicMaterialInstance=function()return mid()end,GetMaterial=function()return obj()end})})
end
overlay=actor('ManjiValleyReactiveSnow');holder=actor('ManjiValleyStampAssets');boundary=actor('ManjiValleyBoundary');bursts={}
for i=1,8 do bursts[i]=actor('ManjiValleySnowBurst')end
render=obj({draws=0,clears=0,ReadRenderTargetRawPixel=function()return {R=.95,G=.1}end,
 ClearRenderTarget2D=function(s,context)assert(context==overlay,'stage actor must be the world context');assert(game_thread);s.clears=s.clears+1 end,
 DrawMaterialToRenderTarget=function(s,_,_,m)
  assert(game_thread);assert(m.Settings0.R>0)
  s.draws=s.draws+1
 end})
local characters={}
for id=0,1 do
 local mesh=obj({DoesSocketExist=function(_,n)return n=='L_Foot'or n=='R_Foot'end,
 GetSocketLocation=function(_,n)return {X=px+id*100+(n=='L_Foot'and -12 or 12),Y=0,Z=pz-80}end})
 characters[id]=obj({GetMeshComponent=function()return mesh end})
end
local mob=obj({IsPracticeMode=function()return practice end,GetTargetPlayer=function(_,id)return characters[id]end})
local battle=obj({GetMobManager=function()return mob end,
 GetFighterPosition=function(_,id)return {X=px+id*100,Y=0,Z=pz}end,
 GetFloorHeightByPlayerID=function()return 0 end,GetBattleRound=function()return round end})
local world=obj({GetFullName=function()return 'World /Game/Battle/Maps/PolarisBattlePL.PolarisBattlePL'end})
package.preload.UEHelpers=function()error('Regression: Tekken Practice has no possessed Pawn')end
package.preload.snow_state=function()return snow_state end
package.preload.render_bridge=function()return render_bridge end
function StaticFindObject(n)
 if n:find('PolarisBlueprintLibrary')then return battle end
 if n:find('KismetRenderingLibrary')then return render end
 if n:find('GameplayStatics')then return obj({GetTimeSeconds=function()return clock end})end
 return assets[n]or obj({dead=true})
end
function LoadAsset(n)assert(game_thread);assets[n]=obj()end
function FindAllOf()
 if not loaded then return {}end
 local all={overlay,holder,boundary};for _,b in ipairs(bursts)do all[#all+1]=b end;return all
end
hooks={};function RegisterHook(path,f)hooks[path]=f end
function ExecuteInGameThread(f)game_thread=true;f();game_thread=false end
function LoopAsync(_,f)loop=f end
function tick(n)for i=1,n or 1 do clock=clock+.05;loop()end end
''')
runtime.execute((folder/'main.lua').read_text())
runtime.execute('''
tick(25);assert(render.draws==0 and overlay.hidden==nil)
loaded=true;tick(25);assert(overlay.hidden==false and render.draws==1)
local draws=render.draws;px=10;tick();assert(render.draws==draws+1,'four feet must be batched into one draw')
hooks['/Script/Polaris.PolarisCharacterActor:OnDown'](nil,{get=function()return {player_id=0}end})
tick();assert(bursts[1].hidden==false and bursts[1].position.Z==6,'burst must originate on floor')
draws=render.draws;tick();assert(render.draws==draws,'stationary contact must not draw each frame')
pz=140;tick();assert(render.draws==draws,'airborne feet must not clear snow')
pz=80;tick();assert(render.draws>draws and bursts[2].hidden==false,'landing must produce a burst')
local clears=render.clears
hooks['/Script/Polaris.PolarisCharacterActor:OnResetPlayerPhysics']();tick();assert(render.clears==clears+1)
assert(bursts[1].hidden==true and bursts[2].hidden==true)
px=400;tick();assert(render.clears==clears+2,'practice teleport must reset both players together')
round=2;tick();assert(render.clears==clears+3)
draws=render.draws;practice=false;tick();assert(overlay.hidden==true and render.draws==draws)
''')
print('PASS: automatic stage activation, asset load on game thread, real-foot contacts, batching, air/landing, floor bursts, round/practice/teleport reset, mode exit')
