# Chasis Suzuki AX100 — pieza independiente para juego (Unity, celular).
# Referencias: despiece Suzuki AX100 Fig. 23 (FRAME) + fotos de chasis desnudo.
# Uso: blender -b --factory-startup -P chasis_ax100.py -- <salida> [muestras] [vistas]
import bpy, sys, os, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import importlib, geo; importlib.reload(geo)
from geo import *

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else '/tmp/chasis'
SAMPLES = int(argv[1]) if len(argv) > 1 else 64
VIEWS = argv[2].split(',') if len(argv) > 2 else ['tres_cuartos', 'lateral', 'superior', 'trasera', 'alambre', 'detalle']
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

PINTURA = mat('Chasis_Pintura', (0.03, 0.03, 0.035), rough=0.35, coat=0.6)
C = bpy.data.collections.new('Chasis_AX100'); sc.collection.children.link(C)
TMP = bpy.data.collections.new('tmp'); sc.collection.children.link(TMP)
parts = []      # objetos que forman el LOD0
def add(name, geo_part, origin=None):
    o = make_obj(name, geo_part, PINTURA, TMP, origin=origin); parts.append(o); return o
def addp(o): parts.append(o); return o
def V3(x, y, z): return Vector((x, y, z))

# =================================================================== geometría de referencia
RAKE = math.radians(27)
A = V3(-math.sin(RAKE), 0, math.cos(RAKE))          # eje de dirección (hacia arriba)
BACK = V3(-math.cos(RAKE), 0, -math.sin(RAKE))       # perpendicular hacia atrás
HEAD = V3(0.955, 0, 0.770)                           # centro de la pipa
HT_TOP, HT_BOT = HEAD + A * 0.082, HEAD - A * 0.082
PIVOT = V3(0.500, 0, 0.360)                          # eje del basculante
R_HEAD, R_TOP, R_TANK, R_DOWN, R_CRADLE, R_POST, R_RAIL, R_STRUT = 0.0235, 0.019, 0.0135, 0.0175, 0.0135, 0.016, 0.0125, 0.011
Y_PLATE = 0.085

def weld(p, d, r_tube):
    """Cordón de soldadura alrededor de un tubo en el punto p (d = dirección del tubo)."""
    return add('w', ring_around(Vector(p), d, r_tube + 0.0012, (0.0028, 0.0022), n=10, sec=3))

def path_end_dir(ctrl, back=0.0):
    a, b = Vector(ctrl[-2]), Vector(ctrl[-1]); d = (b - a).normalized()
    return b - d * back, d

# =================================================================== PIPA DE DIRECCIÓN
add('pipa', hollow(HT_BOT, HT_TOP, R_HEAD, 0.0165, n=16))
for c in (HT_TOP, HT_BOT):   # labios de las tazas de rodamiento
    s = 1 if c is HT_TOP else -1
    add('labio', hollow(c - A * 0.006 * s, c + A * 0.003 * s, R_HEAD + 0.003, 0.0165, n=16))
# tope de dirección (placa bajo la pipa, con pestañas)
stop_c = HT_BOT + A * 0.012
addp(plate('tope_dir', [(-0.02, -0.032), (0.035, -0.026), (0.042, 0.0), (0.035, 0.026), (-0.02, 0.032)], TMP, PINTURA,
           holes=[(0.0, 0.0, 0.019)], plane='XY', offset=0, thick=0.004))
parts[-1].data.transform(Matrix.Translation(stop_c) @ Matrix.Rotation(-RAKE, 4, 'Y'))
# =================================================================== TUBO SUPERIOR (espina) y tubo del tanque
top = [HEAD + A * 0.050 - BACK * 0.005, HEAD + A * 0.040 + BACK * 0.06, V3(0.80, 0, 0.812), V3(0.64, 0, 0.785), V3(0.50, 0, 0.763), V3(0.47, 0, 0.756)]
add('tubo_superior', tube(top, R_TOP, n=12, per=8))
weld(HEAD + A * 0.040 + BACK * 0.028, (top[2] - top[1]).normalized(), R_TOP)

tank = [HEAD - A * 0.020 - BACK * 0.005, HEAD - A * 0.030 + BACK * 0.05, V3(0.84, 0, 0.712), V3(0.72, 0, 0.705), V3(0.62, 0, 0.728), V3(0.575, 0, 0.770)]
add('tubo_tanque', tube(tank, R_TANK, n=8, per=8))
weld(HEAD - A * 0.028 + BACK * 0.027, (tank[2] - tank[1]).normalized(), R_TANK)
p, d = path_end_dir(tank, 0.016); weld(p, d, R_TANK)

# cartelas (gussets) entre pipa, espina y tubo del tanque, a ambos lados
g_out = [(HT_TOP + BACK * 0.02).xz, (HT_BOT + BACK * 0.02 + A * 0.03).xz, V3(0.86, 0, 0.716).xz, V3(0.835, 0, 0.802).xz]
for y in (-0.0145, 0.0145):
    addp(plate('cartela', [(p.x, p.y) for p in g_out], TMP, PINTURA, holes=[(0.888, 0.760, 0.013)], plane='XZ', offset=y, thick=0.003, corner=0.01, bev=0.0008))

# topes de goma del tanque (delanteros) y oreja trasera del tanque
for s in (-1, 1):
    c0 = V3(0.865, s * 0.012, 0.715)
    add('taco_tanque', merge(cyl(c0, c0 + V3(0, s * 0.040, 0.01), 0.0075, n=12),
                            cyl(c0 + V3(0, s * 0.040, 0.01), c0 + V3(0, s * 0.048, 0.012), 0.0105, n=12)))
addp(plate('oreja_tanque_tras', [(-0.03, -0.025), (0.03, -0.025), (0.03, 0.025), (-0.03, 0.025)], TMP, PINTURA,
           holes=[(0.0, 0.0, 0.0065)], plane='XY', offset=0.0, thick=0.004))
parts[-1].data.transform(Matrix.Translation(V3(0.515, 0, 0.787)))

# =================================================================== TRAVESAÑO CENTRAL (unión espina / tubos traseros)
X_J, Z_J = 0.468, 0.752
add('travesano_central', cyl(V3(X_J, -0.100, Z_J), V3(X_J, 0.100, Z_J), 0.017, n=14))
weld(V3(X_J + 0.004, 0, Z_J + 0.004), (top[-1] - top[-2]).normalized(), R_TOP)

# =================================================================== TUBO BAJANTE (delantero) y nodo
down = [HEAD - A * 0.055 + BACK * 0.0, HEAD - A * 0.075 + BACK * 0.045, V3(0.905, 0, 0.590), V3(0.855, 0, 0.440), V3(0.815, 0, 0.320), V3(0.795, 0, 0.272)]
add('tubo_bajante', tube(down, R_DOWN, n=12, per=8))
weld(HEAD - A * 0.070 + BACK * 0.026, (down[2] - down[1]).normalized(), R_DOWN)
NODE = V3(0.792, 0, 0.262)
add('nodo_cuna', cyl(NODE + V3(0, -0.082, 0), NODE + V3(0, 0.082, 0), 0.018, n=14))
weld(NODE + V3(0.006, 0, 0.018), (down[-1] - down[-2]).normalized(), R_DOWN)

# =================================================================== CUNA DEL MOTOR (doble, inferior)
for s in (-1, 1):
    y = s * 0.072
    cr = [NODE + V3(-0.004, y, 0), V3(0.770, y, 0.214), V3(0.710, y, 0.196), V3(0.580, y, 0.194), V3(0.515, s * 0.078, 0.222), V3(0.492, s * 0.080, 0.290)]
    add('cuna', tube(cr, R_CRADLE, n=10, per=8))
    weld(NODE + V3(-0.010, y, -0.012), (cr[2] - cr[1]).normalized(), R_CRADLE)

# =================================================================== PLACAS DEL PIVOTE DEL BASCULANTE
piv_out = [(0.432, 0.262), (0.548, 0.238), (0.575, 0.312), (0.566, 0.445), (0.508, 0.497), (0.442, 0.460), (0.420, 0.352)]
piv_holes = [(PIVOT.x, PIVOT.z, 0.0105), (0.547, 0.282, 0.0065), (0.538, 0.425, 0.0065), (0.462, 0.300, 0.012)]
for s in (-1, 1):
    addp(plate('placa_pivote', piv_out, TMP, PINTURA, holes=piv_holes, plane='XZ', offset=s * Y_PLATE, thick=0.006, bev=0.0015, corner=0.018, corner_seg=3))
    add('buje_pivote', hollow(PIVOT + V3(0, s * (Y_PLATE - 0.006), 0), PIVOT + V3(0, s * (Y_PLATE + 0.012), 0), 0.017, 0.0105, n=20))
    # refuerzo / aleta interior bajo el pivote
    addp(plate('aleta_pivote', [(0.45, 0.25), (0.53, 0.245), (0.50, 0.31)], TMP, PINTURA, plane='XZ', offset=s * (Y_PLATE - 0.006), thick=0.003))
# tubo transversal entre placas (detrás del pivote)
add('travesano_pivote', cyl(V3(0.452, -Y_PLATE + 0.003, 0.432), V3(0.452, Y_PLATE - 0.003, 0.432), 0.013, n=12))

# =================================================================== TUBOS DEL ASIENTO (bajantes traseros en arco)
for s in (-1, 1):
    y0, y1 = s * 0.076, s * (Y_PLATE - 0.008)
    post = [V3(X_J, y0, Z_J - 0.005), V3(0.440, y0, 0.690), V3(0.425, s * 0.079, 0.595), V3(0.440, s * 0.082, 0.512), V3(0.478, y1, 0.462)]
    add('arco_trasero', tube(post, R_POST, n=10, per=8))
    weld(V3(X_J - 0.004, y0, Z_J - 0.018), (post[1] - post[0]).normalized(), R_POST)
    weld(post[-1] + (post[-2] - post[-1]).normalized() * 0.014, (post[-1] - post[-2]).normalized(), R_POST)

# =================================================================== RIELES DEL ASIENTO (subchasis)
REAR_END_X = -0.335
rails = {}
for s in (-1, 1):
    rl = [V3(X_J, s * 0.093, Z_J), V3(0.380, s * 0.100, 0.746), V3(0.120, s * 0.101, 0.754), V3(-0.150, s * 0.096, 0.772), V3(REAR_END_X, s * 0.090, 0.786)]
    rails[s] = rl
    add('riel_asiento', tube(rl, R_RAIL, n=10, per=6, caps=False))
    # terminación del riel: tapón + oreja con agujero para la parrilla (pieza 9 del despiece)
    e, d = rl[-1], (rl[-1] - rl[-2]).normalized()
    add('tapon_riel', merge(cyl(e - d * 0.002, e + d * 0.003, R_RAIL + 0.0008, n=12)))
    addp(plate('oreja_riel', [(-0.015, -0.012), (0.035, -0.010), (0.035, 0.010), (-0.015, 0.012)], TMP, PINTURA,
               holes=[(0.022, 0.0, 0.0055)], plane='XY', thick=0.004))
    parts[-1].data.transform(Matrix.Translation(e + d * 0.0 + V3(0, 0, -0.006)) @ Matrix.Rotation(math.atan2(d.z, d.x) * 0 + math.pi, 4, 'Z'))
    weld(V3(X_J - 0.006, s * 0.095, Z_J), V3(-1, 0, 0), R_RAIL)

# =================================================================== TIRANTES TRASEROS (pivote -> rieles)
for s in (-1, 1):
    st = [V3(0.468, s * (Y_PLATE - 0.006), 0.450), V3(0.330, s * 0.094, 0.575), V3(0.150, s * 0.100, 0.735), V3(0.128, s * 0.101, 0.752)]
    add('tirante', tube(st, R_STRUT, n=8, per=6))
    weld(V3(0.150, s * 0.100, 0.738), (st[-1] - st[-3]).normalized(), R_STRUT)
    weld(V3(0.462, s * (Y_PLATE - 0.008), 0.458), (st[1] - st[0]).normalized(), R_STRUT)

# =================================================================== TRAVESAÑOS TRASEROS y placa del asiento
for x, z, yr in ((-0.030, 0.766, 0.098), (-0.290, 0.783, 0.091)):
    add('travesano_tras', cyl(V3(x, -yr, z), V3(x, yr, z), 0.0105, n=12))
    for s in (-1, 1): weld(V3(x, s * (yr - 0.012), z), V3(0, s, 0), 0.0105)
# placa del asiento / porta-batería (pieza con agujero central, entre rieles)
addp(plate('placa_asiento', [(0.25, -0.092), (0.355, -0.092), (0.355, 0.092), (0.25, 0.092)], TMP, PINTURA,
           holes=[(0.302, 0.0, 0.022), (0.27, -0.06, 0.006), (0.27, 0.06, 0.006)], plane='XY', offset=0.738, thick=0.003, corner=0.01))
# orejas del asiento (bisagra) y del guardabarros trasero
for s in (-1, 1):
    addp(plate('oreja_asiento', [(0.40, 0.735), (0.44, 0.735), (0.435, 0.705), (0.405, 0.705)], TMP, PINTURA,
               holes=[(0.42, 0.718, 0.005)], plane='XZ', offset=s * 0.100, thick=0.003, corner=0.004))
    addp(plate('oreja_guardabarros', [(-0.10, 0.765), (-0.05, 0.765), (-0.06, 0.735), (-0.09, 0.735)], TMP, PINTURA,
               holes=[(-0.075, 0.748, 0.005)], plane='XZ', offset=s * 0.094, thick=0.003, corner=0.004))

# =================================================================== SOPORTES DE AMORTIGUADORES (superiores)
SHOCK_TOP = {}
for s in (-1, 1):
    yp = s * 0.103
    addp(plate('placa_amortiguador', [(0.120, 0.756), (0.245, 0.752), (0.205, 0.700), (0.165, 0.694)], TMP, PINTURA,
               holes=[(0.185, 0.716, 0.0055)], plane='XZ', offset=yp, thick=0.005, corner=0.012))
    c = V3(0.185, s * 0.106, 0.716)
    add('esparrago_amortiguador', merge(cyl(c, c + V3(0, s * 0.030, 0), 0.0055, n=10),
                                        cyl(c + V3(0, s * 0.002, 0), c + V3(0, s * 0.007, 0), 0.010, n=6)))
    SHOCK_TOP[s] = c + V3(0, s * 0.018, 0)

# =================================================================== SOPORTES DEL MOTOR
ENG = {}
for s in (-1, 1):
    # delantero (en el tubo bajante)
    addp(plate('soporte_motor_del', [(0.835, 0.405), (0.865, 0.355), (0.835, 0.315), (0.770, 0.335), (0.780, 0.385)], TMP, PINTURA,
               holes=[(0.792, 0.358, 0.0055)], plane='XZ', offset=s * 0.034, thick=0.004, corner=0.008))
    # inferior (en la cuna)
    addp(plate('soporte_motor_inf', [(0.600, 0.208), (0.690, 0.206), (0.672, 0.262), (0.618, 0.262)], TMP, PINTURA,
               holes=[(0.645, 0.240, 0.0055)], plane='XZ', offset=s * 0.072, thick=0.004, corner=0.008))
    # colgante superior (bajo la espina)
    addp(plate('soporte_motor_sup', [(0.600, 0.795), (0.670, 0.808), (0.655, 0.708), (0.618, 0.705)], TMP, PINTURA,
               holes=[(0.636, 0.724, 0.0055)], plane='XZ', offset=s * 0.016, thick=0.004, corner=0.008))
ENG['del'] = V3(0.792, 0, 0.358); ENG['inf'] = V3(0.645, 0, 0.240); ENG['sup'] = V3(0.636, 0, 0.724)
ENG['tras_sup'] = V3(0.538, 0, 0.425); ENG['tras_inf'] = V3(0.547, 0, 0.282)

# =================================================================== ESTRIBOS, PARADOR Y TAPAS LATERALES
for s in (-1, 1):
    # base de estribos (bloque con agujero) bajo la cuna
    addp(plate('base_estribo', [(0.680, 0.205), (0.735, 0.205), (0.735, 0.172), (0.680, 0.172)], TMP, PINTURA,
               holes=[(0.7075, 0.186, 0.006)], plane='XZ', offset=s * 0.072, thick=0.012, bev=0.002, corner=0.006))
    # pasador de tapa lateral (tetón de goma)
    c = V3(0.415, s * 0.095, 0.640)
    add('teton_tapa', merge(cyl(c, c + V3(0, s * 0.018, 0), 0.004, n=8), cyl(c + V3(0, s * 0.012, 0), c + V3(0, s * 0.020, 0), 0.0065, n=10)))
    addp(plate('oreja_tapa', [(0.40, 0.65), (0.43, 0.65), (0.43, 0.63), (0.40, 0.63)], TMP, PINTURA, plane='XZ', offset=s * 0.090, thick=0.003, corner=0.004))
# soporte del parador lateral (solo lado izquierdo, +Y)
addp(plate('soporte_parador', [(0.560, 0.200), (0.625, 0.198), (0.615, 0.150), (0.570, 0.150)], TMP, PINTURA,
           holes=[(0.592, 0.170, 0.0065)], plane='XZ', offset=0.083, thick=0.008, bev=0.0015, corner=0.008))
# oreja de pedal de freno (lado derecho, -Y)
addp(plate('oreja_freno', [(0.66, 0.215), (0.70, 0.215), (0.695, 0.185), (0.665, 0.185)], TMP, PINTURA,
           holes=[(0.68, 0.198, 0.005)], plane='XZ', offset=-0.080, thick=0.005, corner=0.005))
# orejas para bobina / regulador en la espina
for x in (0.70, 0.58):
    addp(plate('oreja_bobina', [(x - 0.018, 0.0), (x + 0.018, 0.0), (x + 0.018, 0.026), (x - 0.018, 0.026)], TMP, PINTURA,
               holes=[(x, 0.013, 0.004)], plane='XZ', offset=0.0, thick=0.003, corner=0.004))
    parts[-1].data.transform(Matrix.Translation(V3(0, 0, 0.73 if x > 0.6 else 0.745)))
    pass

# =================================================================== UNIR, ORIGEN, UV
lod0 = join(parts, 'Chasis_LOD0')
for c_ in lod0.users_collection: c_.objects.unlink(lod0)
C.objects.link(lod0)
set_origin(lod0, PIVOT)
bpy.context.view_layer.objects.active = lod0
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=1e-6)
try:
    bpy.ops.uv.average_islands_scale(); bpy.ops.uv.pack_islands(margin=0.004)
except Exception as e:
    print('UV pack omitido:', e)
bpy.ops.object.mode_set(mode='OBJECT')
lod0.data.materials.clear(); lod0.data.materials.append(PINTURA)

# LOD1: versión ligera para distancia
lod1 = lod0.copy(); lod1.data = lod0.data.copy(); lod1.name = 'Chasis_LOD1'; lod1.data.name = 'Chasis_LOD1'
C.objects.link(lod1)
dm = lod1.modifiers.new('dec', 'DECIMATE'); dm.ratio = 0.30; dm.use_collapse_triangulate = True
bpy.context.view_layer.objects.active = lod1; bpy.ops.object.modifier_apply(modifier='dec')
bpy.data.collections.remove(TMP)

# =================================================================== ANCLAJES (puntos de montaje para las demás piezas)
anc = bpy.data.objects.new('Chasis_AX100', None); C.objects.link(anc); anc.empty_display_size = 0.1
anc.location = PIVOT
for o in (lod0, lod1):
    mw = o.matrix_world.copy(); o.parent = anc; o.matrix_world = mw
pts = {
    'Anclaje_Direccion': (HEAD, A.to_track_quat('Z', 'X')),
    'Anclaje_Basculante': (PIVOT, None),
    'Anclaje_Amortiguador_Izq': (SHOCK_TOP[1], None),
    'Anclaje_Amortiguador_Der': (SHOCK_TOP[-1], None),
    'Anclaje_Motor_Delantero': (ENG['del'], None),
    'Anclaje_Motor_Inferior': (ENG['inf'], None),
    'Anclaje_Motor_Superior': (ENG['sup'], None),
    'Anclaje_Motor_Trasero_Sup': (ENG['tras_sup'], None),
    'Anclaje_Motor_Trasero_Inf': (ENG['tras_inf'], None),
    'Anclaje_Tanque_Delantero': (V3(0.865, 0, 0.725), None),
    'Anclaje_Tanque_Trasero': (V3(0.515, 0, 0.790), None),
    'Anclaje_Asiento': (V3(0.42, 0, 0.745), None),
    'Anclaje_Tapa_Lateral_Izq': (V3(0.415, 0.115, 0.640), None),
    'Anclaje_Tapa_Lateral_Der': (V3(0.415, -0.115, 0.640), None),
    'Anclaje_Estribos': (V3(0.7075, 0, 0.186), None),
    'Anclaje_Parador': (V3(0.592, 0.09, 0.170), None),
    'Anclaje_Parrilla_Trasera': (V3(REAR_END_X - 0.02, 0, 0.78), None),
    'Anclaje_Guardabarros_Trasero': (V3(-0.075, 0, 0.748), None),
}
for k, (p, rot) in pts.items():
    e = anchor(k, p, C, rot, size=0.04); mw = e.matrix_world.copy(); e.parent = anc; e.matrix_world = mw

# =================================================================== ORIENTAR PARA UNITY (adelante = -Y en Blender)
anc.matrix_world = UNITY_ROT @ anc.matrix_world
bpy.context.view_layer.update()
R = lambda v: UNITY_ROT @ Vector(v)
print(f'RESUMEN LOD0={tri_count(lod0)} tris  LOD1={tri_count(lod1)} tris  anclajes={len(pts)}')

# =================================================================== EXPORTAR
bpy.ops.object.select_all(action='DESELECT')
for o in C.all_objects: o.select_set(True)
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'Chasis_AX100.fbx'), use_selection=True, object_types={'EMPTY', 'MESH'},
                         apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y', bake_space_transform=True,
                         mesh_smooth_type='FACE', add_leaf_bones=False)
try:
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'Chasis_AX100.glb'), export_format='GLB', use_selection=True)
except Exception as e:
    print('GLB omitido:', e)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'Chasis_AX100.blend'))

# =================================================================== RENDERS DE PRESENTACIÓN
lod1.hide_render = True
CEN = R(V3(0.32, 0, 0.50))
studio(sc, Vector((CEN.x, CEN.y, 0)))
CLAY = mat('Arcilla', (0.55, 0.55, 0.56), rough=0.42)
WIRE = mat('Alambre', (0.02, 0.02, 0.025), rough=0.6)
r = sc.render; r.engine = 'CYCLES'; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = False
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
cam_d = bpy.data.cameras.new('Cam'); cam = bpy.data.objects.new('Cam', cam_d); sc.collection.objects.link(cam); sc.camera = cam
tgt = bpy.data.objects.new('tgt', None); sc.collection.objects.link(tgt)
tc = cam.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
wire_obj = None
def look(mode):
    global wire_obj
    lod0.data.materials[0] = PINTURA if mode == 'pintura' else CLAY
    if mode == 'alambre' and wire_obj is None:
        wire_obj = lod0.copy(); wire_obj.data = lod0.data.copy(); sc.collection.objects.link(wire_obj)
        wire_obj.parent = None; wire_obj.matrix_world = lod0.matrix_world.copy()
        wm = wire_obj.modifiers.new('w', 'WIREFRAME'); wm.thickness = 0.0006; wm.use_even_offset = False; wm.use_relative_offset = False; wm.use_replace = True
        wire_obj.data.materials[0] = WIRE
    if wire_obj: wire_obj.hide_render = mode != 'alambre'
def shot(name, loc, target, lens=50, ortho=None, w=1600, h=1200, mode='arcilla'):
    look(mode)
    cam.location = R(loc); tgt.location = R(target)
    cam_d.type = 'ORTHO' if ortho else 'PERSP'
    if ortho: cam_d.ortho_scale = ortho
    else: cam_d.lens = lens
    r.resolution_x, r.resolution_y = w, h; r.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)
T0 = V3(0.30, 0, 0.50)
if 'tres_cuartos' in VIEWS: shot('01_tres_cuartos.png', V3(1.85, 1.55, 1.25), T0, lens=45)
if 'lateral' in VIEWS:      shot('02_lateral.png', V3(0.30, -4.0, 1.1), V3(0.30, 0, 0.50), ortho=1.55)
if 'superior' in VIEWS:     shot('03_superior.png', V3(0.30, 0, 4.0), V3(0.30, 0.0001, 0.5), ortho=1.55)
if 'trasera' in VIEWS:      shot('04_tres_cuartos_trasera.png', V3(-1.3, -1.6, 1.35), T0, lens=45)
if 'alambre' in VIEWS:      shot('05_alambre.png', V3(1.85, 1.55, 1.25), T0, lens=45, mode='alambre')
if 'detalle' in VIEWS:      shot('06_detalle_pipa.png', V3(1.45, 0.55, 1.05), V3(0.86, 0, 0.74), lens=60, mode='pintura')
if 'pintura' in VIEWS:      shot('07_pintura.png', V3(1.85, 1.55, 1.25), T0, lens=45, mode='pintura')
