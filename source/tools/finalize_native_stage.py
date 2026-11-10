from pathlib import Path
import unreal,json,math
unreal.load_module('StaticMeshEditor')
lib=unreal.EditorAssetLibrary;edit=unreal.MaterialEditingLibrary
root=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).parent
names=json.loads((root/'native-stage-source/WorldOffsetMaterials.json').read_text())
specs=json.loads((root/'native-stage-source/MaterialManifest.json').read_text())
for path in ['/Game/ManjiValleyFinal/M_ValleySnowfall']+['/Game/ManjiValleyNative/'+n for n in names]:
    mat=lib.load_asset(path);assert mat,path
    assert edit.get_material_property_input_node(mat,unreal.MaterialProperty.MP_NORMAL) is None,path
    edit.recompile_material(mat);assert lib.save_loaded_asset(mat,False)
snow=lib.load_asset('/Game/ManjiValleyNative/NativeSnowfall')
description=snow.get_static_mesh_description(0)
samples=[]
for i in range(0,min(256,description.get_vertex_instance_count()),7):
    value=description.get_vertex_instance_uv(unreal.VertexInstanceID(i),2)
    assert .1<=value.x<=1.01 and 200<=value.y<=6600,(i,value)
    samples.append([value.x,value.y])
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert level.load_level('/Game/Stage/ST04_Colosseum/Sublevels/ST04_Mob_1')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
native_meshes=[a for a in actors if isinstance(a,unreal.StaticMeshActor) and str(a.get_actor_label()).startswith('T6Original_NativeValley_')]
mesh_specs=json.loads((root/'native-stage-source/MeshManifest.json').read_text())
assert len(native_meshes)==len(mesh_specs),len(native_meshes)
for actor in native_meshes:
    for mat in actor.static_mesh_component.get_materials():
        assert mat and str(mat.get_path_name()).startswith('/Game/ManjiValleyNative/'),str(mat)
texture_rows=[]
for path in lib.list_assets('/Game/ManjiValleyNative',recursive=False):
    texture=lib.load_asset(path)
    if not isinstance(texture,unreal.Texture2D):continue
    assert texture.get_editor_property('never_stream'),path
    assert texture.get_editor_property('lod_bias')==0,path
    assert texture.get_editor_property('compression_settings')==unreal.TextureCompressionSettings.TC_EDITOR_ICON,path
    row=dict(name=texture.get_name(),never_stream=True,lod_bias=0,lossless_import=True)
    for key in ('blueprint_get_size_x','blueprint_get_size_y'):
        if hasattr(texture,key):row[key]=getattr(texture,key)()
    texture_rows.append(row)
for name,spec in specs.items():
    if not spec.get('fire'):continue
    mat=lib.load_asset('/Game/ManjiValleyNative/M_'+name)
    assert mat.get_editor_property('blend_mode')==unreal.BlendMode.BLEND_ADDITIVE,name
    texture=lib.load_asset('/Game/ManjiValleyNative/T6_'+spec['diffuse'])
    assert texture.get_editor_property('mip_gen_settings')==unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS,name
boundary=lib.load_asset('/Game/ManjiValleyNative/NativeArenaBoundary')
assert boundary and 189<boundary.get_bounding_box().max.z<191,boundary.get_bounding_box()
hd_specs=json.loads((root/'native-stage-source/HDTextureManifest.json').read_text())
hd_rows=[]
for key,record in hd_specs.items():
    tex=lib.load_asset('/Game/ManjiValleyNative/'+Path(record['path']).stem)
    assert tex and tex.blueprint_get_size_x()==2048 and tex.blueprint_get_size_y()==2048,key
    assert tex.get_editor_property('mip_gen_settings')==unreal.TextureMipGenSettings.TMGS_SHARPEN2,key
    for name,spec in specs.items():
        if spec['diffuse']!=key:continue
        mat=lib.load_asset('/Game/ManjiValleyNative/M_'+name)
        samplers=[x for x in unreal.ObjectIterator(unreal.MaterialExpressionTextureSample)if x.get_outer()==mat]
        assert any(x.get_editor_property('texture')==tex for x in samplers),(name,key)
    hd_rows.append(dict(key=key,asset=tex.get_path_name(),width=2048,height=2048))
(root/'native-revision/UnrealTextureSettings-after.json').write_text(json.dumps(texture_rows,indent=2))
(root/'native-stage-source/UnrealValidation.json').write_text(json.dumps(dict(
    native_mesh_actors=len(native_meshes),native_materials=len(specs),world_offset_materials=names,
    snowfall_uv_samples=samples,normal_input_empty_after_wpo_patch=True,
    native_material_references_valid=True,validated_resident_lossless_textures=len(texture_rows),
    additive_fire_with_isolated_atlas_frames=True,proximity_frost_wall_height_cm=190,
    hd_texture_references=hd_rows,
    game_visual_verification=False),indent=2))
unreal.log('MANJI_NATIVE_WPO_AND_UV_READY')
