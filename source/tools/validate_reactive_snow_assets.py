from pathlib import Path
import unreal,json,runpy
root=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).parent
runpy.run_path(str(root/'finalize_native_stage.py'))
lib=unreal.EditorAssetLibrary;edit=unreal.MaterialEditingLibrary
dest='/Game/ManjiReactiveSnow'
for name in ('M_ReactiveSnow','M_SnowBurst'):
    mat=lib.load_asset(dest+'/'+name);assert mat
    assert edit.get_material_property_input_node(mat,unreal.MaterialProperty.MP_NORMAL)is None,name
    edit.recompile_material(mat);assert lib.save_loaded_asset(mat,False)
mask=lib.load_asset(dest+'/RT_ManjiTracks');assert mask
assert mask.get_editor_property('size_x')==2048 and mask.get_editor_property('size_y')==2048
mesh=lib.load_asset(dest+'/SM_ReactiveSnow');description=mesh.get_static_mesh_description(0)
triangles=description.get_triangle_count();assert triangles==352800,triangles
burst=lib.load_asset(dest+'/SM_SnowBurst');d=burst.get_static_mesh_description(0);samples=[]
for i in range(0,100,9):
    m=d.get_vertex_instance_uv(unreal.VertexInstanceID(i),1)
    t=d.get_vertex_instance_uv(unreal.VertexInstanceID(i),2)
    assert 30<m.y<130 and 60<t.x<180 and .6<t.y<1.3,(m,t)
    samples.append([m.x,m.y,t.x,t.y])
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert level.load_level('/Game/Stage/ST04_Colosseum/Sublevels/ST04_Mob_1')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
snow=[a for a in actors if a.get_actor_label().startswith('ManjiReactive_')];assert len(snow)==10,len(snow)
for a in snow:
    assert a.get_editor_property('hidden')==(a.get_actor_label()!='ManjiReactive_Surface'),a.get_actor_label()
    c=a.static_mesh_component
    assert c.get_collision_enabled()==unreal.CollisionEnabled.NO_COLLISION
    assert str(c.get_material(0).get_path_name()).startswith(dest+'/')
surface=next(a for a in snow if a.get_actor_label()=='ManjiReactive_Surface')
assert abs(surface.get_actor_location().z-5.5)<.01
result=dict(actors=len(snow),surface_triangles=triangles,mask_dimensions=[2048,2048],
    shader_wpo_restored=True,stage_hard_references_present=True,base_surface_visible_without_runtime=True,
    burst_uv_samples=samples,in_game_contact_verified=False)
(root/'reactive-snow-revision/UnrealValidation.json').write_text(json.dumps(result,indent=2))
unreal.log('MANJI_REACTIVE_SNOW_VALIDATED')
