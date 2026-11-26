# Motor Suzuki AX100 (2T, 98 cc) — piezas independientes para juego (Unity, celular).
# Grupos: 1_Culata · 2_Cilindro · 3_Parte_Baja. Construido en coordenadas del chasis (X adelante, Z arriba).
# Uso: blender -b --factory-startup -P motor_ax100.py -- <salida> [muestras] [vistas]
import bpy, sys, os, math
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
import importlib, geo; importlib.reload(geo)
from geo import *

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else '/tmp/motor'
SAMPLES = int(argv[1]) if len(argv) > 1 else 64
VIEWS = argv[2].split(',') if len(argv) > 2 else ['izq', 'der', 'despiece', 'ensamble', 'alambre']
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

ALU = mat('Motor_Aluminio', (0.72, 0.72, 0.74), metal=1.0, rough=0.32)
ALU_TAPA = mat('Motor_Aluminio_Pulido', (0.8, 0.8, 0.82), metal=1.0, rough=0.18)
NEGRO = mat('Motor_Negro', (0.025, 0.025, 0.028), rough=0.45)
GOMA = mat('Motor_Goma', (0.02, 0.02, 0.02), rough=0.8)
LATON = mat('Motor_Laton', (0.75, 0.55, 0.22), metal=1.0, rough=0.3)
ACERO = mat('Motor_Acero', (0.55, 0.55, 0.57), metal=1.0, rough=0.25)
PLAST = mat('Motor_Plastico', (0.35, 0.35, 0.36), rough=0.5)
CERAM = mat('Motor_Ceramica', (0.9, 0.9, 0.88), rough=0.25)

ROOT_C = bpy.data.collections.new('Motor_AX100'); sc.collection.children.link(ROOT_C)
TMP = bpy.data.collections.new('tmp'); sc.collection.children.link(TMP)
def V3(x, y, z): return Vector((x, y, z))

# ------------------------------------------------------------------ referencias
CRANK = V3(0.660, 0, 0.362)                 # centro del cigüeñal (origen del motor)
TILT = math.radians(20)                     # cilindro inclinado hacia adelante
M = Matrix.Translation(CRANK) @ Matrix.Rotation(TILT, 4, 'Y')   # coords locales del cilindro -> mundo
AX = (M.to_3x3() @ V3(0, 0, 1)).normalized()
def L(x, y, z): return M @ V3(x, y, z)       # punto local del cilindro

pieces = {}   # nombre -> (lista de objetos, material, grupo)
def piece(name, group, material):
    pieces.setdefault(name, {'objs': [], 'mat': material, 'group': group})
    return name
def put(name, part, xf=None):
    o = make_obj(name + '_p', part, None, TMP)
    if xf is not None:
        o.data.transform(o.matrix_basis); o.matrix_basis = Matrix(); o.data.transform(xf)
    pieces[name]['objs'].append(o); return o
def put_plate(name, outline, xf=None, **kw):
    o = plate(name + '_p', outline, TMP, None, **kw)
    if xf is not None: o.data.transform(xf)
    pieces[name]['objs'].append(o); return o

# ================================================================== 1_CULATA
piece('Culata', '1_Culata', ALU)
put('Culata', tube([V3(0, 0, 0.192), V3(0, 0, 0.206)], (0.064, 0.060), n=24, p=5, per=1, simp=False), M)
FIN_Y = (-0.062, -0.048, -0.020, 0.020, 0.048, 0.062)
for y in FIN_Y:
    h = 0.250 if abs(y) < 0.03 else (0.247 if abs(y) < 0.05 else 0.240)
    put_plate('Culata', [(-0.066, 0.204), (0.066, 0.204), (0.066, h - 0.010), (0.052, h), (-0.052, h), (-0.066, h - 0.010)],
              M, plane='XZ', offset=y, thick=0.0042, bev=0.0008, corner=0.004)
for x in (-0.042, 0.042):   # aletas transversales cortas (refuerzo central)
    put_plate('Culata', [(-0.014, 0.204), (0.014, 0.204), (0.014, 0.232), (-0.014, 0.232)],
              M @ Matrix.Rotation(math.pi / 2, 4, 'Z'), plane='XZ', offset=-x, thick=0.004, corner=0.003)
put('Culata', merge(cyl(V3(0, 0, 0.204), V3(0, 0, 0.240), 0.0145, n=16), hollow(V3(0, 0, 0.238), V3(0, 0, 0.242), 0.0145, 0.007, n=16)), M)
put('Culata', cyl(V3(-0.036, -0.013, 0.252), V3(-0.036, 0.013, 0.252), 0.0095, n=12), M)   # oreja del soporte superior
put('Culata', cyl(V3(-0.036, 0, 0.240), V3(-0.036, 0, 0.252), (0.008, 0.010), n=10), M)
piece('Tuercas_Culata', '1_Culata', ACERO)
for sx in (-1, 1):
    for sy in (-1, 1):
        c = V3(sx * 0.050, sy * 0.034, 0.206)
        put('Tuercas_Culata', merge(cyl(c, c + V3(0, 0, 0.007), 0.0062, n=6), cyl(c + V3(0, 0, 0.007), c + V3(0, 0, 0.011), 0.005, n=8)), M)
piece('Bujia', '1_Culata', CERAM)
put('Bujia', merge(cyl(V3(0, 0, 0.240), V3(0, 0, 0.251), 0.0105, n=6), cyl(V3(0, 0, 0.251), V3(0, 0, 0.276), 0.0062, n=12),
                   cyl(V3(0, 0, 0.276), V3(0, 0, 0.284), 0.003, n=8), cyl(V3(0, 0, 0.284), V3(0, 0, 0.287), 0.0045, n=8)), M)

# ================================================================== 2_CILINDRO
piece('Cilindro', '2_Cilindro', NEGRO)
put('Cilindro', tube([V3(0, 0, 0.098), V3(0, 0, 0.192)], (0.046, 0.044), n=24, p=4, per=1, simp=False), M)
put('Cilindro', tube([V3(0, 0, 0.098), V3(0, 0, 0.106)], (0.058, 0.054), n=24, p=5, per=1, simp=False), M)   # base
fin_out = [(-0.066, -0.060), (0.066, -0.060), (0.066, 0.060), (-0.066, 0.060)]
for i in range(6):
    z = 0.114 + i * 0.0142
    put_plate('Cilindro', fin_out, M, plane='XY', offset=z, thick=0.0034, corner=0.014, corner_seg=3)
# puerto de escape (frente) con brida y espárragos
put('Cilindro', tube([V3(0.040, 0, 0.138), V3(0.078, 0, 0.138)], (0.024, 0.020), n=16, p=3, per=1, simp=False), M)
put_plate('Cilindro', [(-0.036, 0.118), (0.036, 0.118), (0.036, 0.158), (-0.036, 0.158)], M,
          plane='YZ', offset=0.078, thick=0.007, bev=0.001, corner=0.008, holes=[(0, 0.138, 0.0155)])
put('Cilindro', hollow(V3(0.070, 0, 0.138), V3(0.0825, 0, 0.138), 0.0155, 0.0135, n=16), M)
# boca de admisión (atrás)
put('Cilindro', tube([V3(-0.040, 0, 0.132), V3(-0.074, 0, 0.132)], (0.022, 0.020), n=16, p=3, per=1, simp=False), M)
put_plate('Cilindro', [(-0.032, 0.112), (0.032, 0.112), (0.032, 0.152), (-0.032, 0.152)], M,
          plane='YZ', offset=-0.074, thick=0.006, corner=0.008)
piece('Esparragos_Cilindro', '2_Cilindro', ACERO)
for sx in (-1, 1):
    for sy in (-1, 1):
        put('Esparragos_Cilindro', cyl(V3(sx * 0.050, sy * 0.034, 0.096), V3(sx * 0.050, sy * 0.034, 0.207), 0.0033, n=6), M)
for sy in (-1, 1):   # espárragos y tuercas del escape
    c = V3(0.082, sy * 0.026, 0.138)
    put('Esparragos_Cilindro', merge(cyl(c - V3(0.006, 0, 0), c + V3(0.012, 0, 0), 0.003, n=6),
                                     cyl(c + V3(0.000, 0, 0), c + V3(0.007, 0, 0), 0.0055, n=6)), M)
piece('Toma_Admision', '2_Cilindro', GOMA)
put('Toma_Admision', merge(
    tube([V3(-0.078, 0, 0.132), V3(-0.100, 0, 0.138), V3(-0.122, 0, 0.152), V3(-0.138, 0, 0.170)], 0.021, n=16, per=6, caps=False),
    hollow(V3(-0.136, 0, 0.168), V3(-0.148, 0, 0.180), 0.024, 0.017, n=16),
    ring_around(L(0, 0, 0) * 0 + V3(-0.118, 0, 0.149), (-0.6, 0, 0.8 * 0 + 0.55), 0.0225, (0.003, 0.0045), n=16, sec=4)), M)
put('Toma_Admision', cyl(V3(-0.078, 0, 0.132), V3(-0.084, 0, 0.133), 0.030, n=16), M)

# ================================================================== 3_PARTE_BAJA
# --- cárter (bloque central, dos mitades con junta) ----------------------------
def dn(pts): return [(x, z - 0.022 if z > 0.36 else z) for x, z in pts]
piece('Carter', '3_Parte_Baja', ALU)
CASE = dn([(0.786, 0.345), (0.772, 0.418), (0.738, 0.458), (0.700, 0.472), (0.640, 0.468), (0.580, 0.452), (0.532, 0.428),
        (0.517, 0.360), (0.522, 0.292), (0.548, 0.250), (0.610, 0.228), (0.720, 0.228), (0.768, 0.255), (0.784, 0.300)])
put_plate('Carter', CASE, plane='XZ', offset=0.0, thick=0.130, bev=0.006, corner=0.022, corner_seg=3, bev_res=1)
cx = sum(p[0] for p in CASE) / len(CASE); cz = sum(p[1] for p in CASE) / len(CASE)
put_plate('Carter', [(cx + (x - cx) * 1.012, cz + (z - cz) * 1.02) for x, z in CASE], plane='XZ', offset=0.0, thick=0.004, corner=0.022)
put('Carter', tube([V3(0, 0, 0.074), V3(0, 0, 0.100)], (0.060, 0.056), n=24, p=5, per=1, simp=False), M)   # asiento del cilindro
# orejas de montaje (pasantes) — coinciden con los anclajes del chasis
MOUNTS = {'Delantero': (V3(0.792, 0, 0.358), 0.029), 'Inferior': (V3(0.645, 0, 0.240), 0.068),
          'Trasero_Sup': (V3(0.538, 0, 0.425), 0.081), 'Trasero_Inf': (V3(0.547, 0, 0.282), 0.081)}
for k, (c, w) in MOUNTS.items():
    put('Carter', hollow(c + V3(0, -w, 0), c + V3(0, w, 0), 0.0135, 0.0058, n=16))
    toward = (V3(cx, 0, cz) - c); toward.y = 0; toward.normalize()
    put('Carter', tube([c, c + toward * 0.035], (0.026 if w < 0.05 else 0.05, 0.011), n=12, p=4, per=1, simp=False))
put('Carter', merge(cyl(V3(0.70, 0, 0.226), V3(0.70, 0, 0.216), 0.010, n=6), cyl(V3(0.70, 0, 0.216), V3(0.70, 0, 0.212), 0.007, n=6)))  # tapón de drenaje

def screws_on(outline, inset, y, side, every=0.055, r=0.0052):
    """Tornillos repartidos por el borde de una tapa."""
    pts = [Vector((x, 0, z)) for x, z in rounded(outline, 0.02, 2)]
    pts = [Vector((p[0], 0, p[1])) for p in pts] if False else [Vector((x, 0, z)) for x, z in rounded(outline, 0.02, 2)]
    c = sum(pts, Vector()) / len(pts); out = []; acc = every
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        seg = (b - a).length; t = 0.0
        while acc + (seg - t) >= every:
            t += every - acc; acc = 0.0
            p = a.lerp(b, t / seg); p = p + (c - p).normalized() * inset
            out.append(merge(cyl(V3(p.x, y, p.z), V3(p.x, y + side * 0.004, p.z), r, n=8),
                             cyl(V3(p.x, y + side * 0.004, p.z), V3(p.x, y + side * 0.0055, p.z), r * 0.75, n=8)))
        acc += seg - t
    return out

piece('Tornilleria', '3_Parte_Baja', ACERO)
# --- tapa del clutch (lado derecho, -Y) ----------------------------------------
piece('Tapa_Clutch', '3_Parte_Baja', ALU_TAPA)
CL = dn([(0.784, 0.335), (0.768, 0.420), (0.725, 0.455), (0.650, 0.458), (0.600, 0.445), (0.588, 0.395), (0.592, 0.300),
      (0.615, 0.272), (0.700, 0.268), (0.760, 0.282)])
put_plate('Tapa_Clutch', CL, plane='XZ', offset=-0.078, thick=0.024, bev=0.005, corner=0.03, corner_seg=3, bev_res=1)
put('Tapa_Clutch', merge(tube([V3(0.715, -0.094, 0.348), V3(0.715, -0.104, 0.348)], 0.054, n=32, per=1, simp=False),
                         tube([V3(0.715, -0.104, 0.348), V3(0.715, -0.106, 0.348)], 0.050, n=32, per=1, simp=False),
                         ring_around(V3(0.715, -0.102, 0.348), (0, 1, 0), 0.054, (0.0025, 0.0025), n=32, sec=4)))
put('Tapa_Clutch', tube([V3(0.625, -0.094, 0.300), V3(0.625, -0.104, 0.300)], 0.017, n=16, per=1, simp=False))  # buje del arranque
for s in screws_on(CL, 0.011, -0.095, -1): put('Tornilleria', s)
for a in range(6):   # tornillos del disco
    ang = 2 * math.pi * a / 6 + 0.3
    p = V3(0.715 + math.cos(ang) * 0.044, -0.106, 0.348 + math.sin(ang) * 0.044)
    put('Tornilleria', cyl(p, p + V3(0, -0.003, 0), 0.0035, n=6))
piece('Eje_Arranque', '3_Parte_Baja', LATON)
spl = [cyl(V3(0.625, -0.104, 0.300), V3(0.625, -0.140, 0.300), 0.0085, n=12)]
for k in range(10):
    a = 2 * math.pi * k / 10
    o = V3(math.cos(a) * 0.009, 0, math.sin(a) * 0.009)
    spl.append(tube([V3(0.625, -0.112, 0.300) + o, V3(0.625, -0.138, 0.300) + o], (0.0018, 0.0018), n=4, per=1, p=6, simp=False))
put('Eje_Arranque', merge(*spl))
piece('Tapon_Aceite', '3_Parte_Baja', PLAST)
put('Tapon_Aceite', merge(cyl(V3(0.640, -0.082, 0.433), V3(0.640, -0.082, 0.456), 0.012, n=16),
                          tube([V3(0.640, -0.082, 0.456), V3(0.640, -0.082, 0.468)], (0.016, 0.006), n=12, per=1, p=6, simp=False)))

# --- lado izquierdo (+Y): tapa del magneto + tapa del piñón ----------------------
piece('Tapa_Magneto', '3_Parte_Baja', ALU_TAPA)
MG = dn([(0.784, 0.335), (0.770, 0.420), (0.728, 0.452), (0.668, 0.455), (0.640, 0.420), (0.640, 0.290), (0.665, 0.262),
      (0.730, 0.262), (0.770, 0.285)])
put_plate('Tapa_Magneto', MG, plane='XZ', offset=0.078, thick=0.024, bev=0.005, corner=0.03, corner_seg=3, bev_res=1)
put('Tapa_Magneto', merge(tube([V3(0.712, 0.094, 0.355), V3(0.712, 0.104, 0.355)], 0.048, n=32, per=1, simp=False),
                          ring_around(V3(0.712, 0.100, 0.355), (0, 1, 0), 0.048, (0.0025, 0.0025), n=32, sec=4)))
for s in screws_on(MG, 0.011, 0.095, 1): put('Tornilleria', s)
piece('Tapa_Pinon', '3_Parte_Baja', ALU)
PN = dn([(0.645, 0.448), (0.590, 0.452), (0.586, 0.400), (0.586, 0.335), (0.600, 0.330), (0.600, 0.270), (0.645, 0.262)])
put_plate('Tapa_Pinon', PN, plane='XZ', offset=0.078, thick=0.024, bev=0.006, corner=0.012, corner_seg=2, bev_res=1,
          holes=[(0.622, 0.383, 0.007)])
for s in screws_on(PN, 0.010, 0.090, 1, every=0.06): put('Tornilleria', s)
piece('Pinon', '3_Parte_Baja', ACERO)
PC = V3(0.590, 0.080, 0.300)
teeth = [cyl(PC + V3(0, -0.004, 0), PC + V3(0, 0.004, 0), 0.030, n=14)]
for k in range(14):
    a = 2 * math.pi * k / 14; d = V3(math.cos(a), 0, math.sin(a))
    teeth.append(tube([PC + d * 0.029, PC + d * 0.037], (0.0035, 0.003), n=4, per=1, p=4, simp=False, ref=V3(0, 1, 0)))
teeth.append(cyl(PC + V3(0, 0.004, 0), PC + V3(0, 0.010, 0), 0.011, n=6))
put('Pinon', merge(*teeth))
piece('Eje_Cambios', '3_Parte_Baja', LATON)
sh = [cyl(V3(0.655, 0.075, 0.252), V3(0.655, 0.118, 0.252), 0.008, n=12)]
for k in range(10):
    a = 2 * math.pi * k / 10; o = V3(math.cos(a) * 0.0085, 0, math.sin(a) * 0.0085)
    sh.append(tube([V3(0.655, 0.098, 0.252) + o, V3(0.655, 0.117, 0.252) + o], (0.0017, 0.0017), n=4, per=1, p=6, simp=False))
put('Eje_Cambios', merge(*sh))
piece('Cable_Magneto', '3_Parte_Baja', NEGRO)
put('Cable_Magneto', merge(tube([V3(0.640, 0.088, 0.408), V3(0.600, 0.100, 0.470), V3(0.560, 0.090, 0.500), V3(0.500, 0.060, 0.520)], 0.0055, n=8, per=6),
                           tube([V3(0.640, 0.084, 0.418), V3(0.615, 0.070, 0.480), V3(0.590, 0.040, 0.520)], 0.0035, n=6, per=6),
                           cyl(V3(0.645, 0.092, 0.410), V3(0.632, 0.092, 0.414), 0.009, n=10)))

# ================================================================== SOPORTE SUPERIOR (motor -> chasis)
piece('Platina_Soporte_Superior', '3_Parte_Baja', ACERO)
HEAD_LUG = L(-0.036, 0, 0.252); TOP = V3(0.636, 0, 0.724)
for y in (-0.016, 0.016):
    put_plate('Platina_Soporte_Superior', [(TOP.x - 0.012, TOP.z + 0.012), (TOP.x + 0.012, TOP.z + 0.012),
                                           (HEAD_LUG.x + 0.014, HEAD_LUG.z - 0.012), (HEAD_LUG.x - 0.014, HEAD_LUG.z - 0.012)],
              plane='XZ', offset=y, thick=0.004, corner=0.01, holes=[(TOP.x, TOP.z, 0.0055), (HEAD_LUG.x, HEAD_LUG.z, 0.0055)])

# ================================================================== CONSTRUIR OBJETOS
groups = {g: bpy.data.collections.new(g) for g in ('1_Culata', '2_Cilindro', '3_Parte_Baja')}
for g in groups.values(): ROOT_C.children.link(g)
root = bpy.data.objects.new('Motor_AX100', None); ROOT_C.objects.link(root); root.location = CRANK; root.empty_display_size = 0.08
group_empty = {}
for g, col in groups.items():
    e = bpy.data.objects.new(g, None); col.objects.link(e); e.location = CRANK; e.parent = root
    e.matrix_parent_inverse = root.matrix_world.inverted(); group_empty[g] = e
bpy.context.view_layer.update()
final = {}
total = 0
for name, d in pieces.items():
    o = join(d['objs'], name) if len(d['objs']) > 1 else d['objs'][0]
    o.name = name; o.data.name = name
    for c in o.users_collection: c.objects.unlink(o)
    groups[d['group']].objects.link(o)
    o.data.materials.clear(); o.data.materials.append(d['mat'])
    bpy.context.view_layer.objects.active = o
    # origen útil: cilindro/culata en el eje del cilindro, resto en el cigüeñal
    if d['group'] == '1_Culata': set_origin(o, L(0, 0, 0.205))
    elif d['group'] == '2_Cilindro': set_origin(o, L(0, 0, 0.100))
    elif name == 'Pinon': set_origin(o, PC)
    else: set_origin(o, CRANK)
    mw = o.matrix_world.copy(); o.parent = group_empty[d['group']]; o.matrix_world = mw
    final[name] = o; n = tri_count(o); total += n
    print(f'PIEZA {name:28s} {n:6d} tris')
bpy.data.collections.remove(TMP)

# anclajes del motor (coinciden con los del chasis)
for k, (c, w) in MOUNTS.items():
    e = anchor('Montaje_' + k, c, ROOT_C, size=0.03); mw = e.matrix_world.copy(); e.parent = root; e.matrix_world = mw
for k, p in {'Montaje_Superior': TOP, 'Salida_Escape': L(0.0825, 0, 0.138), 'Entrada_Carburador': L(-0.148, 0, 0.180),
             'Salida_Cadena': PC}.items():
    e = anchor(k, p, ROOT_C, size=0.03); mw = e.matrix_world.copy(); e.parent = root; e.matrix_world = mw
print(f'RESUMEN piezas={len(final)} total={total} tris')

# ================================================================== ORIENTAR PARA UNITY Y EXPORTAR
root.matrix_world = UNITY_ROT @ root.matrix_world
bpy.context.view_layer.update()
R = lambda v: UNITY_ROT @ Vector(v)
bpy.ops.object.select_all(action='DESELECT')
for o in ROOT_C.all_objects: o.select_set(True)
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'Motor_AX100.fbx'), use_selection=True, object_types={'EMPTY', 'MESH'},
                         apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y', bake_space_transform=True,
                         mesh_smooth_type='FACE', add_leaf_bones=False)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'Motor_AX100.glb'), export_format='GLB', use_selection=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'Motor_AX100.blend'))

# ================================================================== RENDERS
CEN = R(CRANK + V3(0, 0, 0.08))
studio(sc, Vector((CEN.x, CEN.y, 0)))
r = sc.render; r.engine = 'CYCLES'; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = False
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
cam_d = bpy.data.cameras.new('Cam'); cam = bpy.data.objects.new('Cam', cam_d); sc.collection.objects.link(cam); sc.camera = cam
tgt = bpy.data.objects.new('tgt', None); sc.collection.objects.link(tgt)
tc = cam.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
def shot(name, loc, target, lens=55, w=1600, h=1200, platina=False):
    final['Platina_Soporte_Superior'].hide_render = not platina
    cam.location = R(loc); tgt.location = R(target); cam_d.lens = lens
    r.resolution_x, r.resolution_y = w, h; r.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)
    return cam
T = CRANK + V3(0, 0, 0.08)
def project(p):
    from bpy_extras.object_utils import world_to_camera_view
    bpy.context.view_layer.update()
    co = world_to_camera_view(sc, cam, R(p)); return co.x * r.resolution_x, (1 - co.y) * r.resolution_y
labels = {}
if 'izq' in VIEWS: shot('01_lado_izquierdo.png', CRANK + V3(0.55, 0.95, 0.42), T)
if 'der' in VIEWS: shot('02_lado_derecho.png', CRANK + V3(0.55, -0.95, 0.42), T)
if 'despiece' in VIEWS:
    RA = UNITY_ROT.to_3x3()
    def shift(o, v): o.matrix_world = Matrix.Translation(RA @ v) @ o.matrix_world
    moves = [(group_empty['1_Culata'], AX * 0.16), (group_empty['2_Cilindro'], AX * 0.075),
             (final['Tapa_Clutch'], V3(0, -0.09, 0)), (final['Eje_Arranque'], V3(0, -0.09, 0)),
             (final['Tapa_Magneto'], V3(0, 0.09, 0)), (final['Tapa_Pinon'], V3(0, 0.09, 0)), (final['Pinon'], V3(0, 0.05, 0))]
    for o, v in moves: shift(o, v)
    final['Platina_Soporte_Superior'].hide_render = True
    shot('03_despiece.png', CRANK + V3(0.70, 1.0, 0.55), T + V3(0, 0, 0.06), lens=45)
    labels = {'CULATA': project(L(0, 0, 0.29) + AX * 0.16), 'CILINDRO': project(L(0.075, 0, 0.16) + AX * 0.075),
              'PARTE BAJA': project(V3(0.66, 0.12, 0.20))}
    for o, v in moves: shift(o, -v)
    final['Platina_Soporte_Superior'].hide_render = False
    import json; json.dump(labels, open(os.path.join(OUT, 'etiquetas.json'), 'w'))
if 'alambre' in VIEWS:
    WIRE = mat('Alambre', (0.02, 0.02, 0.025), rough=0.6); wires = []
    for o in list(final.values()):
        w = o.copy(); w.data = o.data.copy(); sc.collection.objects.link(w); w.parent = None; w.matrix_world = o.matrix_world.copy()
        m = w.modifiers.new('w', 'WIREFRAME'); m.thickness = 0.0004; m.use_even_offset = False; m.use_replace = True
        w.data.materials.clear(); w.data.materials.append(WIRE); wires.append(w)
    CLAY = mat('Arcilla', (0.55, 0.55, 0.56), rough=0.42); saved = {}
    for o in final.values(): saved[o] = o.data.materials[0]; o.data.materials[0] = CLAY
    shot('04_alambre.png', CRANK + V3(0.55, 0.95, 0.42), T)
    for o, m_ in saved.items(): o.data.materials[0] = m_
    for w in wires: bpy.data.objects.remove(w)
if 'ensamble' in VIEWS:
    chas = os.path.join(HERE, '..', 'chasis', 'salida', 'Chasis_AX100.blend')
    if os.path.exists(chas):
        with bpy.data.libraries.load(chas) as (src, dst): dst.collections = ['Chasis_AX100']
        for c in dst.collections:
            sc.collection.children.link(c)
            for o in c.objects:
                if o.name.startswith('Chasis_LOD1'): o.hide_render = True
        shot('05_en_el_chasis.png', CRANK + V3(1.1, 1.35, 0.55), V3(0.40, 0, 0.48), lens=40, platina=True)
