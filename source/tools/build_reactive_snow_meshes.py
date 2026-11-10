"""Snow uses real displaced geometry; effect bursts are reused from a pool."""
from pathlib import Path
import bpy,json,math,random
out=Path('work/t8/reactive-snow-source');out.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def export(name,vertices,faces,uvs):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    for channel,values in enumerate(uvs):
        layer=mesh.uv_layers.new(name='UVMap'if channel==0 else f'UV{channel+1}')
        for loop in mesh.loops:
            u,v=values[loop.vertex_index];layer.data[loop.index].uv=(u,1-v)
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    for p in mesh.polygons:p.use_smooth=True
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.fbx(filepath=str((out/(name+'.fbx')).resolve()),use_selection=True,
        object_types={'MESH'},axis_forward='-Y',axis_up='Z',bake_anim=False)
    return obj
n=420;size=84;vertices=[];uv=[];faces=[]
for y in range(n+1):
    for x in range(n+1):
        vertices.append((-size/2+size*x/n,-size/2+size*y/n,0));uv.append((x/n,y/n))
for y in range(n):
    for x in range(n):
        a=y*(n+1)+x;faces.append((a,a+1,a+n+2,a+n+1))
sheet=export('SM_ReactiveSnow',vertices,faces,[uv])
random.seed(6806);v=[];f=[];uv0=[];motion=[];timing=[]
for i in range(40):
    angle=random.random()*math.tau;speed=random.uniform(35,125);vz=random.uniform(70,170);life=random.uniform(.65,1.25)
    start=len(v)
    for x,z,u,w in ((-1,-1,0,0),(1,-1,1,0),(1,1,1,1),(-1,1,0,1)):
        v.append((x,0,z));uv0.append((u,w));motion.append((angle,speed));timing.append((vz,life))
    f.append((start,start+1,start+2,start+3))
burst=export('SM_SnowBurst',v,f,[uv0,motion,timing])
(out/'MeshValidation.json').write_text(json.dumps(dict(grid_spacing_cm=20,vertices=len(vertices),
    quads=len(faces),triangles=len(faces)*2,snow_height_cm=18,burst_flakes=40,burst_pool=8),indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str((out/'ReactiveSnow.blend').resolve()))
print('REACTIVE_SNOW_MESHES_READY',len(vertices),len(faces)*2,flush=True)
