# Librería de geometría compartida para las piezas de moto (Blender 4.x, sin interfaz).
# Convención de modelado: X = adelante, Y = izquierda, Z = arriba, metros, suelo en Z = 0.
# Al exportar para Unity se rota todo para que la moto mire hacia -Y (=> +Z en Unity).
import bpy, bmesh, math
from mathutils import Vector, Matrix

# ------------------------------------------------------------------ caminos
def spline(ctrl, per=12):
    ctrl = [Vector(c) for c in ctrl]
    if len(ctrl) < 3 or per <= 1:
        out = []
        for i in range(len(ctrl) - 1):
            for j in range(max(per, 1)):
                out.append(ctrl[i].lerp(ctrl[i + 1], j / max(per, 1)))
        return out + [ctrl[-1]]
    c = [ctrl[0]] + ctrl + [ctrl[-1]]
    out = []
    for i in range(1, len(c) - 2):
        p0, p1, p2, p3 = c[i - 1], c[i], c[i + 1], c[i + 2]
        for j in range(per):
            t = j / per
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(ctrl[-1])
    return out

def simplify(pts, max_angle=7.0, max_len=0.12):
    """Quita puntos casi alineados: menos polígonos en tramos rectos, más en curvas."""
    if len(pts) < 3: return pts
    keep = [pts[0]]; last_dir = (pts[1] - pts[0]).normalized(); acc = 0.0
    for i in range(1, len(pts) - 1):
        d = (pts[i + 1] - pts[i]).normalized(); acc += (pts[i] - pts[i - 1]).length
        ang = math.degrees(last_dir.angle(d, 0))
        if ang > max_angle or acc > max_len:
            keep.append(pts[i]); last_dir = (pts[i] - keep[-2]).normalized(); acc = 0.0
    keep.append(pts[-1])
    return keep

def frame(T, ref=None):
    r0 = ref or (Vector((0, 1, 0)) if abs(T.y) < 0.9 else Vector((0, 0, 1)))
    S = (r0 - r0.dot(T) * T).normalized()
    return S, T.cross(S)

# ------------------------------------------------------------------ primitivas -> (V, F, UV)
def tube(ctrl, r, n=12, per=12, caps=True, closed=False, p=2.0, ref=None, simp=True, max_angle=7.0):
    """Tubo barrido. r = radio fijo, (w,h) o lista por punto de control. UV cilíndricas."""
    if closed:
        pts = [Vector(c) for c in ctrl]
        rads = r if isinstance(r, list) else [r] * len(pts)
    else:
        pts = spline(ctrl, per)
        if isinstance(r, list):
            rv = [Vector((x, x, 0)) if isinstance(x, (int, float)) else Vector((x[0], x[1], 0)) for x in r]
            rads = [(v.x, v.y) for v in spline(rv, per)]
            if simp:  # mantener correspondencia
                simp = False
        else:
            rads = None
        if simp: pts = simplify(pts, max_angle)
        if rads is None: rads = [r] * len(pts)
    rads = [(x, x) if isinstance(x, (int, float)) else x for x in rads]
    m = len(pts); V, F, UV = [], [], []
    # longitud acumulada para la coordenada v
    L = [0.0]
    for i in range(1, m): L.append(L[-1] + (pts[i] - pts[i - 1]).length)
    circ = 2 * math.pi * max(max(a) for a in rads)
    prevS = None
    for i, pt in enumerate(pts):
        if closed: T = pts[(i + 1) % m] - pts[i - 1]
        else: T = pts[min(i + 1, m - 1)] - pts[max(i - 1, 0)]
        T.normalize()
        if ref is None and prevS is not None:   # transporte paralelo: sin giros raros
            S = (prevS - prevS.dot(T) * T).normalized(); U = T.cross(S)
        else:
            S, U = frame(T, ref)
        prevS = S
        w, h = rads[i]
        for j in range(n + 1):
            a = 2 * math.pi * j / n
            ca, sa = math.cos(a), math.sin(a)
            cx = math.copysign(abs(ca) ** (2 / p), ca); cz = math.copysign(abs(sa) ** (2 / p), sa)
            V.append(pt + S * (w * cx) + U * (h * cz))
            UV.append((j / n * circ, L[i]))
    rings = m if closed else m - 1
    k = n + 1
    for i in range(rings):
        i2 = (i + 1) % m
        for j in range(n):
            F.append((i * k + j, i * k + j + 1, i2 * k + j + 1, i2 * k + j))
    if caps and not closed:
        for ring, rev in ((0, True), (m - 1, False)):
            c = pts[ring]; ci = len(V); V.append(c); UV.append((0, 0))
            base = ring * k
            for j in range(n):
                f = (base + j, base + j + 1, ci)
                F.append(f[::-1] if rev else f)
    return V, F, UV

def cyl(a, b, r, n=16, caps=True):
    return tube([a, b], r, n=n, per=1, caps=caps, simp=False)

def ring_around(c, axis, R, r, n=12, sec=4):
    """Anillo (cordón de soldadura, labio de rodamiento) alrededor de un eje."""
    axis = Vector(axis).normalized(); S, U = frame(axis)
    pts = [c + (S * math.cos(2 * math.pi * i / n) + U * math.sin(2 * math.pi * i / n)) * R for i in range(n)]
    return tube(pts, r if isinstance(r, tuple) else (r, r), n=sec, closed=True)

def hollow(a, b, ro, ri, n=20):
    """Tubo hueco con bordes (pipa de dirección, bujes)."""
    a, b = Vector(a), Vector(b); T = (b - a).normalized(); S, U = frame(T)
    V, F, UV = [], [], []
    rings = [(a, ro), (b, ro), (b, ri), (a, ri)]
    for idx, (c, r) in enumerate(rings):
        for j in range(n + 1):
            ang = 2 * math.pi * j / n
            V.append(c + (S * math.cos(ang) + U * math.sin(ang)) * r)
            UV.append((j / n * 2 * math.pi * ro, idx * (b - a).length))
    k = n + 1
    for i in range(4):
        i2 = (i + 1) % 4
        for j in range(n):
            F.append((i * k + j, i * k + j + 1, i2 * k + j + 1, i2 * k + j))
    return V, F, UV

def merge(*parts):
    V, F, UV = [], [], []
    for part in parts:
        v, f = part[0], part[1]
        uv = part[2] if len(part) > 2 and part[2] else [(0, 0)] * len(v)
        o = len(V); V += list(v); UV += list(uv); F += [tuple(i + o for i in face) for face in f]
    return V, F, UV

def mirror_y(part):
    v, f = part[0], part[1]; uv = part[2] if len(part) > 2 else None
    return [Vector((p.x, -p.y, p.z)) for p in v], [tuple(x[::-1]) for x in f], uv

# ------------------------------------------------------------------ objetos
def box_uv(me, scale=1.0):
    bm = bmesh.new(); bm.from_mesh(me)
    uvl = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            co = l.vert.co
            u, v = [(co.y, co.z), (co.x, co.z), (co.x, co.y)][ax]
            l[uvl].uv = (u * scale, v * scale)
    bm.to_mesh(me); bm.free()

def make_obj(name, part, mat, col, smooth_angle=35, origin=None):
    V, F = part[0], part[1]; UV = part[2] if len(part) > 2 else None
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], [tuple(f) for f in F])
    if UV:
        uvl = me.uv_layers.new(name='UVMap')
        for poly in me.polygons:
            for li in poly.loop_indices:
                uvl.data[li].uv = UV[me.loops[li].vertex_index]
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    if not UV: box_uv(me)
    shade(me, smooth_angle)
    o = bpy.data.objects.new(name, me); col.objects.link(o)
    if mat: me.materials.append(mat)
    piv = Vector(origin) if origin is not None else sum((Vector(v) for v in V), Vector()) / len(V)
    me.transform(Matrix.Translation(-piv)); o.location = piv
    return o

def shade(me, angle=35):
    for p in me.polygons: p.use_smooth = True
    try:
        me.use_auto_smooth = True; me.auto_smooth_angle = math.radians(angle)
    except AttributeError:
        pass

def rounded(pts, rad=0.006, seg=3):
    """Polígono 2D con esquinas redondeadas."""
    out = []; n = len(pts)
    for i in range(n):
        p0, p1, p2 = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % n])
        d0, d1 = (p0 - p1), (p2 - p1)
        r = min(rad, d0.length * 0.45, d1.length * 0.45)
        a, b = p1 + d0.normalized() * r, p1 + d1.normalized() * r
        for s in range(seg + 1):
            t = s / seg
            out.append(((1 - t) ** 2) * a + 2 * (1 - t) * t * p1 + (t ** 2) * b)
    return [(p.x, p.y) for p in out]

def plate(name, outline, col, mat, holes=(), plane='XZ', offset=0.0, thick=0.004, bev=0.0, corner=0.006, hole_seg=10, corner_seg=2, bev_res=0):
    """Placa recortada con agujeros y bordes biselados. outline/holes en coords del plano."""
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '2D'; cu.fill_mode = 'BOTH'
    cu.extrude = max(thick / 2 - bev, 0.0003); cu.bevel_depth = bev; cu.bevel_resolution = bev_res
    def add(pts):
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        for i, (a, b) in enumerate(pts): sp.points[i].co = (a, b, 0, 1)
        sp.use_cyclic_u = True
    add(rounded(outline, corner, corner_seg))
    for (cx, cz, r) in holes:
        add([(cx + math.cos(2 * math.pi * i / hole_seg) * r, cz + math.sin(2 * math.pi * i / hole_seg) * r) for i in range(hole_seg)][::-1])
    tmp = bpy.data.objects.new(name + '_tmp', cu); col.objects.link(tmp)
    if plane == 'XZ':
        tmp.rotation_euler = (math.pi / 2, 0, 0); tmp.location = (0, offset, 0)
    elif plane == 'XY':
        tmp.location = (0, 0, offset)
    elif plane == 'YZ':
        tmp.rotation_euler = (math.pi / 2, 0, math.pi / 2); tmp.location = (offset, 0, 0)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    me.transform(tmp.matrix_world)
    bpy.data.objects.remove(tmp); bpy.data.curves.remove(cu)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.to_mesh(me); bm.free()
    box_uv(me); shade(me, 40)
    o = bpy.data.objects.new(name, me); col.objects.link(o)
    if mat: me.materials.append(mat)
    return o

def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.object; o.name = name; o.data.name = name
    return o

def set_origin(o, pt):
    pt = Vector(pt); mw = o.matrix_world.copy()
    local = mw.inverted() @ pt
    o.data.transform(Matrix.Translation(-local)); o.matrix_world = mw @ Matrix.Translation(local)

def tri_count(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)

def anchor(name, loc, col, rot=None, size=0.05):
    e = bpy.data.objects.new(name, None); col.objects.link(e)
    e.empty_display_type = 'ARROWS'; e.empty_display_size = size
    e.matrix_world = Matrix.Translation(Vector(loc)) @ (rot.to_matrix().to_4x4() if rot else Matrix())
    return e

# ------------------------------------------------------------------ materiales
def mat(name, col, metal=0.0, rough=0.5, coat=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*col, 1)
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = rough
    p.inputs['Coat Weight'].default_value = coat
    m.diffuse_color = (*col, 1)
    return m

# ------------------------------------------------------------------ estudio de presentación
UNITY_ROT = Matrix.Rotation(-math.pi / 2, 4, 'Z')   # X adelante -> -Y adelante

def studio(sc, center, size=2.0, bg=(0.16, 0.16, 0.17)):
    """Fondo curvo gris oscuro + luces suaves, estilo lámina de presentación."""
    col = bpy.data.collections.new('Estudio'); sc.collection.children.link(col)
    # cuenco sin costuras: piso plano que sube en curva por todos lados
    prof = [(0.0, 0.0), (5.0, 0.0)] + [(5.0 + 3.0 * math.sin(math.pi / 2 * i / 10), 3.0 - 3.0 * math.cos(math.pi / 2 * i / 10)) for i in range(1, 11)] + [(8.0, 9.0)]
    bm = bmesh.new(); N = 64; rings = []
    for rr, z in prof:
        rings.append([bm.verts.new((center.x + rr * math.cos(2 * math.pi * k / N), center.y + rr * math.sin(2 * math.pi * k / N), z)) for k in range(N)])
    for i in range(len(rings) - 1):
        for k in range(N):
            k2 = (k + 1) % N
            if i == 0:
                if k == 0: pass
            bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k])) if i > 0 else None
    c0 = bm.verts.new((center.x, center.y, 0))
    for k in range(N):
        bm.faces.new((c0, rings[1][k], rings[1][(k + 1) % N]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('Ciclorama'); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    cyc = bpy.data.objects.new('Ciclorama', me); col.objects.link(cyc)
    me.materials.append(mat('Fondo', bg, rough=0.6))
    def area(name, loc, size_xy, power, color=(1, 1, 1)):
        ld = bpy.data.lights.new(name, 'AREA'); ld.shape = 'RECTANGLE'
        ld.size, ld.size_y = size_xy; ld.energy = power; ld.color = color
        lo = bpy.data.objects.new(name, ld); col.objects.link(lo); lo.location = loc
        d = (center - Vector(loc)).normalized()
        lo.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        return lo
    area('Luz_Cenital', center + Vector((0, 0, 3.2)), (3.0, 1.2), 60)
    area('Luz_Clave', center + Vector((2.2, -2.6, 1.8)), (1.6, 1.6), 90)
    area('Luz_Borde_A', center + Vector((-2.8, 1.5, 1.2)), (0.6, 2.4), 110, (0.9, 0.95, 1.0))
    area('Luz_Borde_B', center + Vector((2.6, 2.4, 1.0)), (0.6, 2.0), 60)
    w = bpy.data.worlds.new('Mundo'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.05, 0.05, 0.055, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
    return col
