"""Create a self-contained, hard-referenced snow layer in the native stage."""
from pathlib import Path
import unreal,json
unreal.load_module('StaticMeshEditor')
project=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
source=project.parent/'reactive-snow-source';dest='/Game/ManjiReactiveSnow'
lib=unreal.EditorAssetLibrary;edit=unreal.MaterialEditingLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools()
def asset(name,cls,factory):
    return lib.load_asset(dest+'/'+name)if lib.does_asset_exist(dest+'/'+name)else tools.create_asset(name,dest,cls,factory)
def node(mat,cls,**values):
    o=edit.create_material_expression(mat,cls)
    for k,v in values.items():o.set_editor_property(k,v)
    return o
def link(a,pin,b,slot):assert edit.connect_material_expressions(a,pin,b,slot)
def custom(mat,code,inputs,kind,prop=None):
    o=node(mat,unreal.MaterialExpressionCustom,code=code,output_type=kind)
    names=[]
    for name,origin,pin in inputs:
        i=unreal.CustomInput();i.set_editor_property('input_name',name);names.append(i)
    o.set_editor_property('inputs',names)
    for name,origin,pin in inputs:link(origin,pin,o,name)
    if prop is not None:assert edit.connect_material_property(o,'',prop)
    return o
def material(name,blend):
    o=asset(name,unreal.Material,unreal.MaterialFactoryNew());edit.delete_all_material_expressions(o)
    o.set_editor_property('blend_mode',blend);o.set_editor_property('two_sided',True)
    o.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
    return o
f1=unreal.CustomMaterialOutputType.CMOT_FLOAT1;f3=unreal.CustomMaterialOutputType.CMOT_FLOAT3
mask=asset('RT_ManjiTracks',unreal.TextureRenderTarget2D,unreal.TextureRenderTargetFactoryNew())
for k,v in dict(size_x=2048,size_y=2048,clear_color=unreal.LinearColor(0,0,0,0),
    render_target_format=unreal.TextureRenderTargetFormat.RTF_RGBA8).items():mask.set_editor_property(k,v)
assert lib.save_loaded_asset(mask,False)
snowtex=lib.load_asset(dest+'/T_SnowAlbedo')if lib.does_asset_exist(dest+'/T_SnowAlbedo')else None
if not snowtex:snowtex=lib.duplicate_asset('/Game/ManjiValleyFinal/MV_T6_1002521E',dest+'/T_SnowAlbedo')
assert snowtex
for k,v in dict(never_stream=True,lod_bias=0,mip_gen_settings=unreal.TextureMipGenSettings.TMGS_SHARPEN2,
    compression_settings=unreal.TextureCompressionSettings.TC_EDITOR_ICON).items():snowtex.set_editor_property(k,v)
assert lib.save_loaded_asset(snowtex,False)

stamp=material('M_ManjiTrackStamp',unreal.BlendMode.BLEND_ADDITIVE)
uv=node(stamp,unreal.MaterialExpressionTextureCoordinate)
inputs=[('UV',uv,'')];code='float2 mask=float2(0,0);\n'
for i in range(4):
    seg=node(stamp,unreal.MaterialExpressionVectorParameter,parameter_name=f'Segment{i}',default_value=unreal.LinearColor())
    settings=node(stamp,unreal.MaterialExpressionVectorParameter,parameter_name=f'Settings{i}',default_value=unreal.LinearColor())
    inputs.extend([(f'Segment{i}',seg,''),(f'EndY{i}',seg,'A'),(f'Settings{i}',settings,'')])
    code+=f'''if(Settings{i}.r>0.000001){{
float2 a=Segment{i}.rg,b=float2(Segment{i}.b,EndY{i}),delta=b-a;
float u=saturate(dot(UV-a,delta)/max(dot(delta,delta),1e-10));
float d=length(UV-a-delta*u)/Settings{i}.r;
float groove=1-smoothstep(.43,1,d);
float rim=smoothstep(.78,1.04,d)*(1-smoothstep(1.04,1.4,d));
mask=max(mask,float2(groove,rim)*Settings{i}.g);
}}\n'''
custom(stamp,code+'return float3(mask,0);',inputs,f3,unreal.MaterialProperty.MP_EMISSIVE_COLOR)

surface=material('M_ReactiveSnow',unreal.BlendMode.BLEND_MASKED)
surface.set_editor_property('opacity_mask_clip_value',.32)
world=node(surface,unreal.MaterialExpressionWorldPosition)
tracks=node(surface,unreal.MaterialExpressionTextureObjectParameter,parameter_name='TrackMask',texture=mask,
    sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
uv=node(surface,unreal.MaterialExpressionTextureCoordinate,u_tiling=42.0,v_tiling=42.0)
texture=node(surface,unreal.MaterialExpressionTextureSample,texture=snowtex);link(uv,'',texture,'UVs')
common='''float2 uv=saturate((World.xy+4200)/8400);
float2 track=saturate(Texture2DSampleLevel(Tracks,TracksSampler,uv,0).rg);
float q=length(World.xy/float2(3650,3080));
float border=(1-q)*3200+22*sin(World.x*.009)*cos(World.y*.007);
float cover=smoothstep(-40,160,border);
'''
custom(surface,common+'''float depth=smoothstep(.06,.90,track.r);
float ridge=4*track.g*(1-smoothstep(.12,.75,track.r));
return float3(0,0,cover*(18*(1-depth)+ridge));''',
    [('World',world,''),('Tracks',tracks,'')],f3,unreal.MaterialProperty.MP_NORMAL)
custom(surface,common+'return cover*(1-smoothstep(.76,.97,track.r));',
    [('World',world,''),('Tracks',tracks,'')],f1,unreal.MaterialProperty.MP_OPACITY_MASK)
color=custom(surface,common+'''float2 dx=float2(1.0/2048,0),dy=dx.yx;
float gx=Texture2DSampleLevel(Tracks,TracksSampler,uv+dx,0).r-Texture2DSampleLevel(Tracks,TracksSampler,uv-dx,0).r;
float gy=Texture2DSampleLevel(Tracks,TracksSampler,uv+dy,0).r-Texture2DSampleLevel(Tracks,TracksSampler,uv-dy,0).r;
float shade=clamp(.94+(gx-gy)*.28,.66,1.05);
return Base*float3(.67,.73,.81)*shade;''',
    [('World',world,''),('Tracks',tracks,''),('Base',texture,'RGB')],f3)
exposure=node(surface,unreal.MaterialExpressionEyeAdaptationInverse);link(color,'',exposure,'')
assert edit.connect_material_property(exposure,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)

burst=material('M_SnowBurst',unreal.BlendMode.BLEND_TRANSLUCENT)
shape=node(burst,unreal.MaterialExpressionTextureCoordinate)
motion=node(burst,unreal.MaterialExpressionTextureCoordinate,coordinate_index=1)
timing=node(burst,unreal.MaterialExpressionTextureCoordinate,coordinate_index=2)
time=node(burst,unreal.MaterialExpressionTime)
born=node(burst,unreal.MaterialExpressionScalarParameter,parameter_name='BornTime',default_value=-10000.0)
world=node(burst,unreal.MaterialExpressionWorldPosition);center=node(burst,unreal.MaterialExpressionObjectPositionWS)
camera=node(burst,unreal.MaterialExpressionCameraPositionWS)
custom(burst,'''float t=max(0,Time-Born);
float2 view=Camera.xy-Center.xy;
float2 right=normalize(float2(-view.y,view.x)+float2(.00001,0));
float2 speed=float2(cos(Motion.x),sin(Motion.x))*Motion.y;
float3 p=Center+float3(speed*t,Timing.x*t-150*t*t);
float size=3.5+4*t;
p+=float3(right*(Shape.x-.5)*size,(Shape.y-.5)*size);
return p-World;''',
    [('Time',time,''),('Born',born,''),('Shape',shape,''),('Motion',motion,''),('Timing',timing,''),
     ('World',world,''),('Center',center,''),('Camera',camera,'')],f3,unreal.MaterialProperty.MP_NORMAL)
custom(burst,'''float t=Time-Born;
float disc=1-smoothstep(.1,.5,length(Shape-.5));
return disc*(1-smoothstep(Timing.y*.5,Timing.y,t))*step(0,t)*.8;''',
    [('Time',time,''),('Born',born,''),('Shape',shape,''),('Timing',timing,'')],f1,unreal.MaterialProperty.MP_OPACITY)
color=node(burst,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.7,.79,.9))
exposure=node(burst,unreal.MaterialExpressionEyeAdaptationInverse);link(color,'',exposure,'')
assert edit.connect_material_property(exposure,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
for mat in (stamp,surface,burst):edit.recompile_material(mat);assert lib.save_loaded_asset(mat,False)

opt=unreal.FbxImportUI();opt.import_as_skeletal=False;opt.import_mesh=True
opt.import_materials=False;opt.import_textures=False;opt.static_mesh_import_data.combine_meshes=True
opt.static_mesh_import_data.auto_generate_collision=False;opt.static_mesh_import_data.generate_lightmap_u_vs=False
mesh_editor=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem);meshes={}
for name,mat in [('SM_ReactiveSnow',surface),('SM_SnowBurst',burst)]:
    task=unreal.AssetImportTask()
    for k,v in dict(filename=str(source/(name+'.fbx')),destination_path=dest,automated=True,replace_existing=True,save=True,options=opt).items():task.set_editor_property(k,v)
    tools.import_asset_tasks([task]);mesh=lib.load_asset(task.imported_object_paths[0]);mesh.set_material(0,mat)
    settings=mesh_editor.get_lod_build_settings(mesh,0);settings.set_editor_property('use_full_precision_u_vs',True)
    mesh_editor.set_lod_build_settings(mesh,0,settings)
    mesh.set_editor_property('positive_bounds_extension',unreal.Vector(200,200,200))
    mesh.set_editor_property('negative_bounds_extension',unreal.Vector(200,200,20))
    assert lib.save_loaded_asset(mesh,False);meshes[name]=mesh
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert level.load_level('/Game/Stage/ST04_Colosseum/Sublevels/ST04_Mob_1')
for a in actors.get_all_level_actors():
    if a.get_actor_label().startswith('ManjiReactive_'):actors.destroy_actor(a)
def actor(label,tag,mesh,mat,z):
    a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,z));a.set_actor_label(label)
    a.set_editor_property('tags',[unreal.Name(tag)]);a.set_actor_hidden_in_game(True)
    c=a.static_mesh_component;c.set_editor_property('mobility',unreal.ComponentMobility.MOVABLE)
    c.set_static_mesh(mesh);c.set_material(0,mat);c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    c.set_editor_property('cast_shadow',False);c.set_editor_property('receives_decals',False)
    return a
actor('ManjiReactive_Surface','ManjiValleyReactiveSnow',meshes['SM_ReactiveSnow'],surface,5.5).set_actor_hidden_in_game(False)
actor('ManjiReactive_StampResources','ManjiValleyStampAssets',meshes['SM_SnowBurst'],stamp,-3500)
for i in range(8):actor(f'ManjiReactive_Burst_{i}','ManjiValleySnowBurst',meshes['SM_SnowBurst'],burst,-3500)
assert level.save_current_level()
(source/'WorldOffsetMaterials.json').write_text(json.dumps(['M_ReactiveSnow','M_SnowBurst'],indent=2))
unreal.log('MANJI_REACTIVE_SNOW_ASSETS_READY')
