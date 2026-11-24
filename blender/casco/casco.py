import bpy, bmesh, math, sys
from mathutils import Vector

OUT = sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else '/tmp/casco.png'
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def mat_black():
    m = bpy.data.materials.new('NegroBrillante'); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (0.008, 0.008, 0.009, 1)
    p.inputs['Roughness'].default_value = 0.12
    p.inputs['Coat Weight'].default_value = 1.0
    p.inputs['Coat Roughness'].default_value = 0.02
    return m
def mat_visor():
    m = bpy.data.materials.new('VisorHumo'); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (0.02, 0.025, 0.03, 1)
    p.inputs['Roughness'].default_value = 0.03
    p.inputs['Metallic'].default_value = 0.3
    return m
def mat_matte():
    m = bpy.data.materials.new('NegroMate'); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (0.012, 0.012, 0.012, 1)
    p.inputs['Roughness'].default_value = 0.55
    return m
def mat_white():
    m = bpy.data.materials.new('Blanco'); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (0.9, 0.9, 0.9, 1)
    p.inputs['Roughness'].default_value = 0.4
    return m
BLACK, VISOR, MATTE, WHITE = mat_black(), mat_visor(), mat_matte(), mat_white()

def boolean(obj, cutter, op='DIFFERENCE'):
    md = obj.modifiers.new('b', 'BOOLEAN'); md.object = cutter; md.operation = op; md.solver = 'EXACT'
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(cutter)

def box(name, loc, dim, rot=(0,0,0), bev=0):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = (dim[0]/2, dim[1]/2, dim[2]/2)
    bpy.ops.object.transform_apply(scale=True)
    if bev:
        b = o.modifiers.new('bv','BEVEL'); b.width = bev; b.segments = 8
        bpy.ops.object.modifier_apply(modifier='bv')
    return o

def shell_shape(v, s=1.0):
    # v: point on unit sphere -> helmet shell. X forward, Z up.
    x, y, z = v
    X, Y, Z = x*1.15, y*0.88, z*1.08
    # back pulled out and up into a tail toward the spoiler
    if x < 0:
        t = -x
        X -= 0.28*t**3 * max(0, 0.6+z)
        Z += 0.10*t**2 * max(0, z)
    # flatter top front, fuller chin
    if x > 0 and z < 0: X += 0.30*x*(-z)
    # slight side taper toward bottom
    if z < 0: Y *= 1 - 0.12*(-z)
    return Vector((X*s, Y*s, Z*s))

def make_shell(name, s=1.0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=1)
    o = bpy.context.object; o.name = name
    for vt in o.data.vertices:
        vt.co = shell_shape(vt.co.normalized(), s)
    bpy.ops.object.shade_smooth()
    return o

# ---------- shell ----------
shell = make_shell('Casco')
# neck opening / bottom cut (tilted: lower at chin, higher at back)
boolean(shell, box('c1', (0, 0, -1.30), (5, 3, 1.6), rot=(0, math.radians(9), 0)))
# visor opening
boolean(shell, box('c2', (1.15, 0, 0.08), (1.3, 1.55, 0.56), rot=(0, math.radians(-12), 0), bev=0.2))
shell.data.materials.append(BLACK)

# rear spoiler: wedge fin on top-back
bm = bmesh.new()
pts = [(-0.20, 1.03), (-1.50, 0.42), (-1.42, 0.02), (-0.85, 0.38)]  # (x,z) profile
w = 0.42
vs = [bm.verts.new((x, -w, z)) for x, z in pts] + [bm.verts.new((x, w, z)) for x, z in pts]
bm.faces.new(vs[:4][::-1]); bm.faces.new(vs[4:])
for i in range(4):
    j = (i+1) % 4
    bm.faces.new((vs[i], vs[j], vs[j+4], vs[i+4]))
me = bpy.data.meshes.new('spoiler'); bm.to_mesh(me)
sp = bpy.data.objects.new('Aleron', me); sc.collection.objects.link(sp)
bv = sp.modifiers.new('bv', 'BEVEL'); bv.width = 0.10; bv.segments = 6
sp.modifiers.new('sub', 'SUBSURF').levels = 2
bpy.context.view_layer.objects.active = sp
for m in list(sp.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)
sp.data.materials.append(BLACK)
bpy.ops.object.select_all(action='DESELECT'); sp.select_set(True); bpy.ops.object.shade_smooth()

# ---------- visor ----------
vis = make_shell('Visor', 1.025)
cut = box('keep', (1.15, 0, 0.09), (1.4, 1.75, 0.68), rot=(0, math.radians(-12), 0), bev=0.24)
boolean(vis, cut, 'INTERSECT')
sol = vis.modifiers.new('s', 'SOLIDIFY'); sol.thickness = 0.02
vis.data.materials.append(VISOR)

# surface-placed details via raycast
dg = bpy.context.evaluated_depsgraph_get()
def on_surface(x, z, side=-1):
    o = Vector((x, side*3, z)); hit, loc, nor, _ = shell.ray_cast(o, Vector((0, -side, 0)))
    return (loc, nor) if hit else (None, None)
loc, nor = on_surface(0.42, 0.10)
if loc:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.075, depth=0.04, location=loc + nor*0.01)
    c = bpy.context.object; c.rotation_mode='QUATERNION'; c.rotation_quaternion = nor.to_track_quat('Z','Y')
    c.data.materials.append(MATTE); bpy.ops.object.shade_smooth()
for side in (-1, 1):
    for i in range(3):
        loc, nor = on_surface(1.02 + i*0.03, -0.30 - i*0.07, side)
        if not loc: continue
        bpy.ops.mesh.primitive_cube_add(location=loc)
        v = bpy.context.object; v.scale = (0.11, 0.02, 0.012)
        v.rotation_mode='QUATERNION'; v.rotation_quaternion = nor.to_track_quat('Y','Z')
        v.data.materials.append(MATTE)
sol = shell.modifiers.new('s', 'SOLIDIFY'); sol.thickness = 0.03

# ---------- floor, lights, camera ----------
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -0.62))
bpy.context.object.is_shadow_catcher = True
FL = mat_matte(); FL.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.04,0.04,0.04,1)
bpy.context.object.data.materials.append(FL)

world = bpy.data.worlds.new('W'); sc.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (1, 1, 1, 1)
nt = world.node_tree; bg = nt.nodes['Background']
bg2 = nt.nodes.new('ShaderNodeBackground'); bg2.inputs[0].default_value = (0.03, 0.03, 0.03, 1)
lp = nt.nodes.new('ShaderNodeLightPath'); mix = nt.nodes.new('ShaderNodeMixShader')
nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs[0]); nt.links.new(bg2.outputs[0], mix.inputs[1])
nt.links.new(bg.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], nt.nodes['World Output'].inputs[0])

def area(loc, rot, size, power, sx=None):
    bpy.ops.object.light_add(type='AREA', location=loc, rotation=rot)
    l = bpy.context.object.data; l.energy = power; l.shape = 'RECTANGLE'
    l.size = size; l.size_y = sx or size
area((0, -1.5, 4.0), (math.radians(20), 0, 0), 5, 700, 1.2)          # long top strip -> highlight on crown
area((3.5, -3, 1.0), (math.radians(80), 0, math.radians(50)), 2, 400)
area((-4, -2, 1.5), (math.radians(75), 0, math.radians(-60)), 3, 300)

bpy.ops.object.camera_add(location=(1.4, -8.0, 0.45))
cam = bpy.context.object; sc.camera = cam; cam.data.lens = 68
bpy.ops.object.empty_add(location=(-0.15, 0, 0.05)); tgt = bpy.context.object
tc = cam.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'

r = sc.render
r.engine = 'CYCLES'; sc.cycles.samples = int(sys.argv[-1]) if sys.argv[-1].isdigit() else 64
sc.cycles.use_denoising = False
r.resolution_x, r.resolution_y = 736, 920
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
r.film_transparent = True
sc.use_nodes = True; nt = sc.node_tree
rl = nt.nodes['Render Layers']; comp = nt.nodes['Composite']
ao = nt.nodes.new('CompositorNodeAlphaOver'); ao.inputs[1].default_value = (0.96,0.96,0.96,1)
nt.links.new(rl.outputs['Image'], ao.inputs[2]); nt.links.new(ao.outputs[0], comp.inputs[0])
r.filepath = OUT
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT.rsplit('.',1)[0] + '.blend')
