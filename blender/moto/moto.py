# Moto 2T clásica para juego — modelo sin texturas, piezas independientes.
# Uso: blender -b --factory-startup -P moto.py -- <carpeta_salida> [muestras]
# Ejes: X = adelante, Y = izquierda de la moto, Z = arriba. Suelo en Z = 0. Unidades: metros.
import bpy, bmesh, math, sys, os
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else '/tmp/moto'
SAMPLES = int(argv[1]) if len(argv) > 1 else 32
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ---------------------------------------------------------------- coordenadas
# Todo se mide sobre la foto de referencia (1024x1024 px) y se convierte a metros.
K = 0.00208  # m por px (distancia entre ejes 600 px ~ 1.25 m)
def P(px, py, y=0.0):
    return Vector(((px - 245) * K, y, (985 - py - (px - 245) * 0.058) * K))

REAR_AXLE = P(245, 835)
FRONT_AXLE = P(845, 800)
FORK_TOP = P(693, 470)
FORK_DIR = (FORK_TOP - FRONT_AXLE).normalized()
FORK_LEN = (FORK_TOP - FRONT_AXLE).length
_perp = Vector((-FORK_DIR.z, 0, FORK_DIR.x))          # perpendicular hacia atrás
if _perp.x > 0: _perp = -_perp
STEER_PT = FRONT_AXLE + FORK_DIR * 0.60 + _perp * 0.045  # centro de la pipa
SWING_PIVOT = P(485, 790)

# ---------------------------------------------------------------- materiales (colores planos, sin texturas)
def mat(name, col, metal=0.0, rough=0.5, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*col, 1)
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = rough
    p.inputs['Coat Weight'].default_value = coat
    m.diffuse_color = (*col, 1)
    return m
ROJO = mat('Pintura_Roja', (0.55, 0.025, 0.012), rough=0.25, coat=1.0)
NEGRO = mat('Negro', (0.02, 0.02, 0.02), rough=0.45)
CROMO = mat('Cromo', (0.9, 0.9, 0.9), metal=1.0, rough=0.08)
ALU = mat('Aluminio', (0.7, 0.7, 0.72), metal=1.0, rough=0.35)
GOMA = mat('Goma', (0.015, 0.015, 0.015), rough=0.85)
DORADO = mat('Dorado', (0.8, 0.55, 0.2), metal=1.0, rough=0.3)
AZUL = mat('Cable_Azul', (0.02, 0.05, 0.4), rough=0.4)

# ---------------------------------------------------------------- colecciones
def coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or sc.collection).children.link(c)
    return c
C_MOTO = coll('Moto')
C = {k: coll(k, C_MOTO) for k in
     ('Chasis', 'Carroceria', 'Motor', 'Escape', 'Direccion', 'Rueda_Delantera', 'Rueda_Trasera', 'Basculante', 'Transmision', 'Mandos')}

# ---------------------------------------------------------------- geometría
def spline(ctrl, per):
    if per <= 1 or len(ctrl) < 3:
        if per <= 1: return list(ctrl)
    c = [ctrl[0]] + list(ctrl) + [ctrl[-1]]
    out = []
    for i in range(1, len(c) - 2):
        p0, p1, p2, p3 = c[i - 1], c[i], c[i + 1], c[i + 2]
        for j in range(per):
            t = j / per
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(ctrl[-1])
    return out

def tube(ctrl, rad, n=16, p=2.0, per=8, caps=True, closed=False, ref=None):
    """Barrido de una sección superelíptica (semiancho w, semialto h) a lo largo de un camino."""
    rad = [(r, r) if isinstance(r, (int, float)) else r for r in rad]
    if len(rad) == 1: rad = rad * len(ctrl)
    if closed:
        pts, rs = list(ctrl), [Vector((r[0], r[1], 0)) for r in rad]
    else:
        pts = spline([Vector(c) for c in ctrl], per)
        rs = spline([Vector((r[0], r[1], 0)) for r in rad], per)
    m = len(pts); V, F = [], []
    for i, pt in enumerate(pts):
        if closed: T = pts[(i + 1) % m] - pts[i - 1]
        else: T = pts[min(i + 1, m - 1)] - pts[max(i - 1, 0)]
        T.normalize()
        r0 = ref or (Vector((0, 1, 0)) if abs(T.y) < 0.9 else Vector((0, 0, 1)))
        S = (r0 - r0.dot(T) * T).normalized(); U = T.cross(S)
        w, h = rs[i].x, rs[i].y
        for j in range(n):
            a = 2 * math.pi * j / n
            ca, sa = math.cos(a), math.sin(a)
            cx = math.copysign(abs(ca) ** (2 / p), ca); cz = math.copysign(abs(sa) ** (2 / p), sa)
            V.append(pt + S * (w * cx) + U * (h * cz))
    rings = m if closed else m - 1
    for i in range(rings):
        i2 = (i + 1) % m
        for j in range(n):
            j2 = (j + 1) % n
            F.append((i * n + j, i * n + j2, i2 * n + j2, i2 * n + j))
    if caps and not closed:
        F.append(tuple(range(n))[::-1]); F.append(tuple(range((m - 1) * n, m * n)))
    return V, F

def cyl(a, b, r, n=24, p=2.0, w=None):
    return tube([a, b], [(w or r, r)], n=n, p=p, per=1)

def circle_pts(center, r, n=64, a0=0, a1=2 * math.pi, axis='Y'):
    out = []
    for i in range(n):
        a = a0 + (a1 - a0) * i / n
        out.append(center + Vector((math.cos(a) * r, 0, math.sin(a) * r)))
    return out

def merge(*parts):
    V, F = [], []
    for v, f in parts:
        o = len(V); V += v; F += [tuple(i + o for i in face) for face in f]
    return V, F

def obj(name, geo, material, col, smooth=True, sub=0, origin=None):
    V, F = geo
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in V], [], F)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    for poly in me.polygons: poly.use_smooth = smooth
    try:
        me.use_auto_smooth = True; me.auto_smooth_angle = math.radians(40)
    except AttributeError:
        pass
    o = bpy.data.objects.new(name, me); col.objects.link(o)
    me.materials.append(material)
    if sub:
        s = o.modifiers.new('Suavizado', 'SUBSURF'); s.levels = sub; s.render_levels = sub
    # origen: punto dado o centro de la geometría
    piv = origin if origin is not None else sum((Vector(v) for v in V), Vector()) / len(V)
    me.transform(Matrix.Translation(-piv)); o.location = piv
    return o

def loft_x(prof, p=3.0, n=24, per=6):
    """Pieza de carrocería a partir de perfiles laterales: (px, py_arriba, py_abajo, semiancho_m)."""
    ctrl, rad = [], []
    for px, top, bot, hw in prof:
        a, b = P(px, top), P(px, bot)
        ctrl.append((a + b) / 2); rad.append((hw, (a.z - b.z) / 2))
    return tube(ctrl, rad, n=n, p=p, per=per)

def mirror_y(geo):
    V, F = geo
    return [Vector((v.x, -v.y, v.z)) for v in V], [f[::-1] for f in F]

# ================================================================ RUEDAS
def wheel(tag, c, tire_h, tire_w, rim_r, colname, disc=False):
    cl = C[colname]; parts = {}
    tire_r = 0.312 - tire_h / 2
    parts['Llanta'] = obj(f'{tag}_Llanta', tube(circle_pts(c, tire_r, 72), [(tire_w / 2, tire_h / 2)], n=20, p=2.3, closed=True), GOMA, cl, origin=c)
    parts['Rin'] = obj(f'{tag}_Rin', tube(circle_pts(c, rim_r, 72), [(0.022, 0.010)], n=12, p=3, closed=True), CROMO, cl, origin=c)
    hub_w = 0.11 if not disc else 0.10
    hub = merge(cyl(c + Vector((0, -hub_w / 2, 0)), c + Vector((0, hub_w / 2, 0)), 0.035 if disc else 0.075, n=32),
                cyl(c + Vector((0, -0.07, 0)), c + Vector((0, 0.07, 0)), 0.012, n=12))
    parts['Manzana'] = obj(f'{tag}_Manzana', hub, ALU, cl, origin=c)
    sp = []
    for k in range(36):
        side = 1 if k % 2 else -1
        a = 2 * math.pi * k / 36
        a2 = a + side * math.radians(28)
        fr = 0.045 if disc else 0.08
        p0 = c + Vector((math.cos(a) * fr, side * (hub_w / 2 - 0.008), math.sin(a) * fr))
        p1 = c + Vector((math.cos(a2) * (rim_r - 0.008), side * 0.008, math.sin(a2) * (rim_r - 0.008)))
        sp.append(cyl(p0, p1, 0.0022, n=6))
    parts['Rayos'] = obj(f'{tag}_Rayos', merge(*sp), CROMO, cl, smooth=False, origin=c)
    if disc:
        d = tube(circle_pts(c + Vector((0, -0.062, 0)), 0.1, 64), [(0.0025, 0.03)], n=8, p=8, closed=True)
        car = [cyl(c + Vector((0, -0.062, 0)), c + Vector((math.cos(a) * 0.075, -0.062, math.sin(a) * 0.075)), 0.008, n=8)
               for a in [i * 2 * math.pi / 6 for i in range(6)]]
        parts['Disco'] = obj(f'{tag}_Disco_Freno', merge(d, *car), DORADO, cl, origin=c)
    else:
        parts['Corona'] = obj(f'{tag}_Corona', tube(circle_pts(c + Vector((0, 0.07, 0)), 0.095, 48), [(0.003, 0.02)], n=8, p=8, closed=True), ALU, C['Transmision'], origin=c)
    return parts

rear = wheel('Rueda_Trasera', REAR_AXLE, 0.085, 0.095, 0.232, 'Rueda_Trasera')
front = wheel('Rueda_Delantera', FRONT_AXLE, 0.075, 0.08, 0.232, 'Rueda_Delantera', disc=True)

# ================================================================ DIRECCIÓN
cd = C['Direccion']
def along(t, y=0.0): return FRONT_AXLE + FORK_DIR * t + Vector((0, y, 0))
for side, nm in ((-1, 'Der'), (1, 'Izq')):
    y = side * 0.085
    obj(f'Barra_Horquilla_{nm}', cyl(along(0.22, y), along(FORK_LEN + 0.01, y), 0.017), CROMO, cd)
    obj(f'Botella_Horquilla_{nm}', merge(cyl(along(-0.03, y), along(0.30, y), 0.024),
                                       cyl(along(0, y), along(0, y) + Vector((0, -side * 0.03, 0)), 0.02)), ALU, cd)
    obj(f'Tapon_Horquilla_{nm}', cyl(along(FORK_LEN, y), along(FORK_LEN + 0.025, y), 0.02), NEGRO, cd)
for t, nm in ((0.50, 'Inferior'), (FORK_LEN - 0.04, 'Superior')):
    c0 = along(t)
    back = c0 + _perp * 0.05
    obj(f'Tijera_{nm}', merge(tube([c0 + Vector((0, -0.115, 0)), c0 + Vector((0, 0.115, 0))], [(0.025, 0.02)], n=16, p=4, per=1),
                              tube([c0, back], [(0.04, 0.018)], n=16, p=4, per=1)), NEGRO, cd)
# manubrio (ligeramente hacia atrás y elevado)
hb = [P(632, 438, -0.37), P(645, 436, -0.27), P(678, 452, -0.13), P(684, 456, 0.0), P(678, 452, 0.13), P(645, 436, 0.27), P(632, 438, 0.37)]
obj('Manubrio', tube(hb, [0.011], n=12, per=6), CROMO, cd)
for side, nm in ((-1, 'Der'), (1, 'Izq')):
    obj(f'Puno_{nm}', cyl(P(632, 438, side * 0.37), P(640, 437, side * 0.27), 0.017, n=16), GOMA, cd)
    obj(f'Maneta_{nm}', tube([P(650, 436, side * 0.25), P(610, 430, side * 0.30), P(585, 428, side * 0.34)], [(0.006, 0.004)], n=8, p=4, per=4), ALU, cd)
    obj(f'Soporte_Maneta_{nm}', cyl(P(648, 437, side * 0.22), P(648, 437, side * 0.26), 0.016, n=12), NEGRO, cd)
g0 = P(700, 452); gdir = (FORK_DIR * 0.7 + _perp * 0.7).normalized()
obj('Velocimetro', merge(cyl(g0, g0 + gdir * 0.05, 0.045, n=32), cyl(g0 + gdir * 0.05, g0 + gdir * 0.055, 0.04, n=32)), DORADO, cd)
obj('Tablero_Base', tube([P(690, 470), P(705, 455)], [(0.05, 0.012)], n=12, p=4, per=1), NEGRO, cd)
# guardabarros delantero elevado
fc = FRONT_AXLE
fender_pts = [fc + Vector((math.cos(a) * 0.39, 0, math.sin(a) * 0.39)) for a in [math.radians(d) for d in range(52, 134, 4)]]
obj('Guardabarros_Delantero', tube(fender_pts, [(0.058, 0.016)], n=20, p=2.6, per=2), ROJO, cd)
for side in (-1, 1):
    obj(f'Soporte_Guardabarros_{"Der" if side < 0 else "Izq"}',
        tube([along(0.20, side * 0.085), along(0.33, side * 0.06)], [0.006], n=8, per=1), NEGRO, cd)
obj('Caliper_Freno_Del', tube([fc + Vector((-0.085, -0.062, 0.06)), fc + Vector((-0.04, -0.062, 0.10))], [(0.022, 0.03)], n=16, p=4, per=1), NEGRO, cd)
obj('Cable_Freno_Del', tube([fc + Vector((-0.06, -0.08, 0.09)), along(0.45, -0.11), P(700, 470, -0.15), P(655, 440, -0.24)], [0.004], n=6, per=6), NEGRO, cd)
obj('Cable_Acelerador', tube([P(640, 440, -0.22), P(740, 450, -0.12), P(770, 520, 0), P(720, 620, 0.02), P(560, 660, 0.05)], [0.004], n=6, per=6), NEGRO, cd)

# ================================================================ CHASIS
cc = C['Chasis']
steer_a = STEER_PT - FORK_DIR * 0.09; steer_b = STEER_PT + FORK_DIR * 0.09
obj('Pipa_Direccion', cyl(steer_a, steer_b, 0.03, n=24), NEGRO, cc)
frame = [
    tube([steer_b - FORK_DIR * 0.02, P(650, 545), P(560, 575), P(485, 607)], [0.022], n=14),
    tube([steer_a, P(700, 625), P(668, 700), P(655, 770)], [0.02], n=14),
]
for s in (-1, 1):
    y = s * 0.085
    frame += [
        tube([P(485, 607, y * 0.4), P(485, 607, y), P(330, 605, y), P(180, 600, y)], [0.013], n=10),
        tube([P(485, 607, y), P(488, 700, y), SWING_PIVOT + Vector((0, y, 0))], [0.015], n=10),
        tube([P(478, 700, y), P(400, 672, y), P(332, 652, y)], [0.012], n=10),
        tube([P(655, 770, 0), P(650, 790, y * 0.7), P(615, 835, y * 0.7), P(520, 838, y * 0.8), SWING_PIVOT + Vector((0, y, 0))], [0.014], n=10),
    ]
frame.append(tube([P(180, 600, -0.085), P(172, 600, -0.05), P(172, 600, 0.05), P(180, 600, 0.085)], [0.013], n=10, ref=Vector((0, 0, 1))))
frame.append(cyl(SWING_PIVOT + Vector((0, -0.1, 0)), SWING_PIVOT + Vector((0, 0.1, 0)), 0.018, n=16))
obj('Chasis', merge(*frame), NEGRO, cc)
obj('Soporte_Placa', tube([P(200, 600), P(190, 625), P(195, 640)], [(0.04, 0.005)], n=12, p=4, per=3), NEGRO, cc)

# ================================================================ CARROCERÍA
cb = C['Carroceria']
obj('Tanque', loft_x([(466, 545, 615, 0.07), (505, 512, 622, 0.12), (580, 498, 624, 0.15), (650, 499, 612, 0.15),
                      (695, 515, 588, 0.11), (716, 540, 570, 0.06)], p=2.6, n=32), ROJO, cb, sub=1)
obj('Tapa_Tanque', cyl(P(600, 507) + Vector((0, 0, -0.005)), P(600, 507) + Vector((0, 0, 0.012)), 0.035, n=24), CROMO, cb)
obj('Asiento', loft_x([(133, 552, 580, 0.09), (155, 536, 590, 0.125), (300, 536, 598, 0.14), (420, 547, 603, 0.14),
                       (470, 562, 607, 0.12), (492, 585, 608, 0.07)], p=3.2, n=32), NEGRO, cb, sub=1)
obj('Bandeja_Asiento', loft_x([(180, 598, 618, 0.10), (330, 600, 622, 0.11), (475, 605, 626, 0.10)], p=6, n=16), NEGRO, cb)
obj('Tapa_Lateral', loft_x([(345, 626, 678, 0.10), (420, 620, 703, 0.12), (505, 617, 717, 0.125), (548, 620, 705, 0.11),
                            (558, 628, 682, 0.07)], p=4, n=24), ROJO, cb, sub=1)

# ================================================================ MOTOR
cm = C['Motor']
obj('Carter', loft_x([(492, 728, 795, 0.11), (520, 712, 818, 0.12), (600, 735, 828, 0.12), (645, 738, 805, 0.115),
                      (660, 745, 770, 0.09)], p=4, n=28), ALU, cm, sub=1)
obj('Tapa_Clutch', merge(tube([P(588, 770, -0.115), P(588, 770, -0.15)], [(0.088, 0.075)], n=32, p=2.6, per=1),
                         tube([P(588, 770, -0.15), P(588, 770, -0.158)], [(0.06, 0.05)], n=32, p=2.6, per=1)), ALU, cm)
obj('Tapa_Magneto', tube([P(530, 760, 0.115), P(530, 760, 0.145)], [(0.07, 0.07)], n=32, p=2.2, per=1), ALU, cm)
cy0, cy1 = P(600, 742), P(612, 650)
cax = (cy1 - cy0).normalized()
fins = [tube([cy0 + cax * (0.012 + i * 0.016), cy0 + cax * (0.017 + i * 0.016)], [(0.09, 0.095 + (0.006 if i % 2 else 0))], n=20, p=5, per=1) for i in range(7)]
fins.append(tube([cy0, cy0 + cax * 0.125], [(0.055, 0.06)], n=20, p=2.5, per=1))
obj('Cilindro', merge(*fins), NEGRO, cm, smooth=False)
obj('Culata', tube([cy0 + cax * 0.125, cy0 + cax * 0.185, cy0 + cax * 0.197], [(0.10, 0.10), (0.098, 0.098), (0.08, 0.08)], n=24, p=5, per=1), ALU, cm, sub=1)
obj('Bujia', cyl(cy0 + cax * 0.19 + Vector((0.03, 0, 0)), cy0 + cax * 0.24 + Vector((0.045, 0, 0)), 0.01, n=12), CROMO, cm)
obj('Cable_Bujia', tube([cy0 + cax * 0.24 + Vector((0.05, 0, 0)), P(680, 615, -0.04), P(705, 600, -0.03), P(690, 625, 0.03), P(600, 640, 0.05), P(560, 640, 0.06)], [0.005], n=8, per=6), AZUL, cm)
obj('Carburador', merge(cyl(P(500, 720), P(562, 715), 0.028, n=20), cyl(P(530, 716), P(530, 690), 0.02, n=16)), ALU, cm)
obj('Pinon_Salida', tube(circle_pts(P(510, 785, 0.11), 0.035, 24), [(0.003, 0.01)], n=6, p=8, closed=True), ALU, C['Transmision'], origin=P(510, 785, 0.11))

# ================================================================ ESCAPE (lado derecho, -Y)
ce = C['Escape']
pipe = [P(650, 725, -0.03), P(672, 738, -0.05), P(684, 770, -0.07), P(672, 808, -0.09), P(640, 830, -0.10),
        P(580, 845, -0.11), P(500, 852, -0.12), P(420, 852, -0.13), P(370, 840, -0.135), P(330, 828, -0.14)]
prad = [0.02, 0.021, 0.024, 0.03, 0.038, 0.046, 0.046, 0.036, 0.022, 0.016]
obj('Expansion', tube(pipe, prad, n=24, per=8), CROMO, ce)
muf = [P(345, 830, -0.15), P(170, 798, -0.155)]
obj('Silenciador', tube(muf, [(0.042, 0.042)], n=28, per=1), CROMO, ce)
obj('Punta_Silenciador', merge(cyl(P(175, 799, -0.155), P(160, 796, -0.155), 0.03, n=20), cyl(P(160, 796, -0.155), P(150, 794, -0.155), 0.015, n=16)), ALU, ce)
obj('Abrazadera_Silenciador', tube([P(300, 820, -0.155), P(300, 760, -0.12), P(320, 705, -0.09)], [(0.008, 0.012)], n=8, p=4, per=4), NEGRO, ce)

# ================================================================ BASCULANTE Y SUSPENSIÓN TRASERA
cs = C['Basculante']
arms = []
for s in (-1, 1):
    y = s * 0.095
    arms.append(tube([SWING_PIVOT + Vector((0.01, y, 0)), REAR_AXLE + Vector((0.02, y, 0)), REAR_AXLE + Vector((-0.04, y, 0))], [(0.012, 0.024)], n=16, p=5, per=1))
arms.append(cyl(SWING_PIVOT + Vector((0, -0.105, 0)), SWING_PIVOT + Vector((0, 0.105, 0)), 0.024, n=20))
arms.append(tube([SWING_PIVOT + Vector((-0.12, -0.09, 0.01)), SWING_PIVOT + Vector((-0.12, 0.09, 0.01))], [(0.012, 0.012)], n=12, p=4, per=1))
obj('Basculante', merge(*arms), NEGRO, cs, origin=SWING_PIVOT)
obj('Eje_Trasero', cyl(REAR_AXLE + Vector((0, -0.12, 0)), REAR_AXLE + Vector((0, 0.12, 0)), 0.011, n=12), CROMO, cs, origin=REAR_AXLE)
obj('Brazo_Freno_Trasero', tube([REAR_AXLE + Vector((0, -0.065, 0)), REAR_AXLE + Vector((0.06, -0.065, -0.07)), P(470, 838, -0.07)], [(0.004, 0.008)], n=8, p=4, per=1), NEGRO, cs)

cr = C['Chasis']
for s, nm in ((-1, 'Der'), (1, 'Izq')):
    y = s * 0.112
    top, bot = P(332, 652, y), P(292, 812, y)
    ax = (top - bot).normalized(); L = (top - bot).length
    coil = []
    turns = 11; steps = turns * 16
    S = Vector((0, 1, 0)); U = ax.cross(S).normalized()
    for i in range(steps + 1):
        t = i / steps; a = 2 * math.pi * turns * t
        coil.append(bot + ax * (0.06 + t * (L - 0.14)) + (S * math.cos(a) + U * math.sin(a)) * 0.03)
    obj(f'Resorte_Amortiguador_{nm}', tube(coil, [0.0045], n=6, per=1), NEGRO, cr, origin=(top + bot) / 2)
    obj(f'Cuerpo_Amortiguador_{nm}', merge(cyl(bot, bot + ax * (L * 0.55), 0.018, n=16), cyl(bot + ax * (L * 0.5), top, 0.011, n=12),
                                          cyl(top - ax * 0.07, top - ax * 0.05, 0.036, n=20), cyl(bot + ax * 0.04, bot + ax * 0.055, 0.036, n=20),
                                          cyl(top + Vector((0, -0.015, 0)), top + Vector((0, 0.015, 0)), 0.014, n=12),
                                          cyl(bot + Vector((0, -0.015, 0)), bot + Vector((0, 0.015, 0)), 0.014, n=12)), CROMO, cr, origin=(top + bot) / 2)

# ================================================================ TRANSMISIÓN
ct = C['Transmision']
rc, fcn = REAR_AXLE + Vector((0, 0.07, 0)), P(510, 785, 0.07)
rr, fr = 0.098, 0.038
d = fcn - rc; ang = math.atan2(d.z, d.x)
chain = []
for i in range(41):  # arco trasero (lado de atrás)
    a = ang + math.pi / 2 + math.pi * i / 40
    chain.append(rc + Vector((math.cos(a) * rr, 0, math.sin(a) * rr)))
for i in range(21):  # arco delantero
    a = ang - math.pi / 2 + math.pi * i / 20
    chain.append(fcn + Vector((math.cos(a) * fr, 0, math.sin(a) * fr)))
dense = []
for i in range(len(chain)):
    a, b = chain[i], chain[(i + 1) % len(chain)]
    k = max(1, int((b - a).length / 0.01))
    dense += [a.lerp(b, j / k) for j in range(k)]
obj('Cadena', tube(dense, [(0.005, 0.006)], n=6, p=6, closed=True), NEGRO, ct)

# ================================================================ MANDOS
ck = C['Mandos']
for s, nm in ((-1, 'Der'), (1, 'Izq')):
    obj(f'Estribo_{nm}', merge(cyl(P(585, 858, s * 0.10), P(585, 858, s * 0.21), 0.016, n=14),
                              cyl(P(585, 858, s * 0.08), P(585, 858, s * 0.11), 0.01, n=10)), GOMA, ck)
obj('Pedal_Freno', tube([P(585, 845, -0.11), P(620, 855, -0.12), P(655, 852, -0.14)], [(0.006, 0.01)], n=8, p=4, per=4), CROMO, ck)
obj('Palanca_Cambios', tube([P(540, 790, 0.13), P(590, 835, 0.15), P(640, 840, 0.16)], [(0.006, 0.009)], n=8, p=4, per=4), CROMO, ck)
obj('Pedal_Arranque', tube([P(560, 760, -0.16), P(520, 790, -0.17), P(470, 800, -0.18)], [(0.007, 0.01)], n=8, p=4, per=4), CROMO, ck)
obj('Parador_Lateral', tube([P(520, 845, 0.10), P(470, 880, 0.14), P(420, 900, 0.16)], [0.009], n=8, per=4), NEGRO, ck)

# ================================================================ JERARQUÍA PARA JUEGO
def empty(name, loc, col, rot=None):
    e = bpy.data.objects.new(name, None); col.objects.link(e)
    e.empty_display_type = 'ARROWS'; e.empty_display_size = 0.15
    e.matrix_world = Matrix.Translation(loc) @ (rot.to_matrix().to_4x4() if rot else Matrix())
    return e
def parent(child, par):
    mw = child.matrix_world.copy(); child.parent = par; child.matrix_world = mw

root = empty('Moto_Raiz', Vector((0, 0, 0)), C_MOTO)
rot_steer = FORK_DIR.to_track_quat('Z', 'X')   # Z local = eje de dirección
e_steer = empty('Pivote_Direccion', STEER_PT, C['Direccion'], rot_steer)
e_swing = empty('Pivote_Basculante', SWING_PIVOT, C['Basculante'])
e_fw = empty('Eje_Rueda_Delantera', FRONT_AXLE, C['Rueda_Delantera'])
e_rw = empty('Eje_Rueda_Trasera', REAR_AXLE, C['Rueda_Trasera'])
bpy.context.view_layer.update()
for e in (e_steer, e_swing): parent(e, root)
parent(e_fw, e_steer); parent(e_rw, e_swing)
for o in list(C['Rueda_Delantera'].objects):
    if o is not e_fw: parent(o, e_fw)
for o in list(C['Rueda_Trasera'].objects):
    if o is not e_rw: parent(o, e_rw)
for o in list(C['Direccion'].objects):
    if o is not e_steer: parent(o, e_steer)
for o in list(C['Basculante'].objects):
    if o is not e_swing: parent(o, e_swing)
for k in ('Chasis', 'Carroceria', 'Motor', 'Escape', 'Transmision', 'Mandos'):
    for o in C[k].objects:
        if o.parent is None: parent(o, root)
# la corona gira con la rueda trasera
cor = bpy.data.objects['Rueda_Trasera_Corona']; parent(cor, e_rw)

# ================================================================ ESCENA DE RENDER
def light(loc, rot, size, power):
    bpy.ops.object.light_add(type='AREA', location=loc, rotation=rot)
    l = bpy.context.object; l.data.energy = power; l.data.size = size
    return l
studio = coll('Estudio')
for l in (light((0.5, -3, 3), (math.radians(45), 0, 0), 3, 350),
          light((3, 1, 2.5), (math.radians(50), 0, math.radians(110)), 2, 160),
          light((-2.5, 2, 2), (math.radians(60), 0, math.radians(-130)), 2, 300)):
    for c in l.users_collection: c.objects.unlink(l)
    studio.objects.link(l)
bpy.ops.mesh.primitive_plane_add(size=30, location=(0.6, 0, 0))
fl = bpy.context.object; fl.name = 'Piso'; fl.is_shadow_catcher = True
for c in fl.users_collection: c.objects.unlink(fl)
studio.objects.link(fl)
world = bpy.data.worlds.new('Mundo'); sc.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (1, 1, 1, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = 0.3

r = sc.render; r.engine = 'CYCLES'; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = False
r.film_transparent = True
sc.view_settings.view_transform = 'Standard'
sc.use_nodes = True; nt = sc.node_tree
ao = nt.nodes.new('CompositorNodeAlphaOver'); ao.inputs[1].default_value = (1, 1, 1, 1)
nt.links.new(nt.nodes['Render Layers'].outputs['Image'], ao.inputs[2]); nt.links.new(ao.outputs[0], nt.nodes['Composite'].inputs[0])

bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam
for c in cam.users_collection: c.objects.unlink(cam)
studio.objects.link(cam)
tgt = bpy.data.objects.new('Objetivo_Camara', None); studio.objects.link(tgt)
tc = cam.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'

def shot(name, loc, target, w, h, ortho=None, lens=50):
    cam.location = loc; tgt.location = target
    if ortho: cam.data.type = 'ORTHO'; cam.data.ortho_scale = ortho
    else: cam.data.type = 'PERSP'; cam.data.lens = lens
    r.resolution_x, r.resolution_y = w, h
    r.filepath = os.path.join(OUT, name); bpy.ops.render.render(write_still=True)

views = argv[2].split(',') if len(argv) > 2 else ['lateral', 'tres_cuartos', 'frente_izq']
if 'lateral' in views:   # misma vista que la foto (lado derecho)
    shot('render_lateral.png', Vector((0.62, -6, 0.55)), Vector((0.62, 0, 0.55)), 1024, 1024, ortho=2.13)
if 'tres_cuartos' in views:
    shot('render_tres_cuartos.png', Vector((3.2, -3.0, 1.4)), Vector((0.62, 0, 0.5)), 1200, 900, lens=50)
if 'frente_izq' in views:
    shot('render_izquierda_atras.png', Vector((-2.4, 3.2, 1.3)), Vector((0.62, 0, 0.5)), 1200, 900, lens=50)

# ================================================================ EXPORTAR
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'moto.blend'))
for o in bpy.data.objects: o.select_set(False)
for o in C_MOTO.all_objects: o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'moto.glb'), export_format='GLB', use_selection=True, export_apply=True)
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'moto.fbx'), use_selection=True, use_mesh_modifiers=True,
                         apply_scale_options='FBX_SCALE_ALL', object_types={'EMPTY', 'MESH'})

# resumen
dg = bpy.context.evaluated_depsgraph_get(); tot = 0; n = 0
for o in C_MOTO.all_objects:
    if o.type == 'MESH':
        m = o.evaluated_get(dg).to_mesh(); tri = sum(len(p.vertices) - 2 for p in m.polygons); tot += tri; n += 1
        o.evaluated_get(dg).to_mesh_clear()
print(f'RESUMEN piezas={n} triangulos={tot}')
