"""Portes du UH-60 : decoupe gauche / droite, os de charniere et de glissiere, proprietes et drivers.
install(rig) sert au fabricant du modele 1.2 et au bouton « Ajouter les portes à ce rig » (rigs 1.0 / 1.1)."""
import math
import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

# porte cockpit : charniere avant, s'ouvre vers l'exterieur ; porte cabine : coulisse vers l'arriere sur rails
DOORS = (
    dict(key='cockpit_l', prop='door_cockpit_l', kind='HINGE', side=1, src='BH_Portes_Cockpit', obj='BH_Porte_Cockpit_G', bone='MCH_Porte_Cockpit_G'),
    dict(key='cockpit_r', prop='door_cockpit_r', kind='HINGE', side=-1, src='BH_Portes_Cockpit', obj='BH_Porte_Cockpit_D', bone='MCH_Porte_Cockpit_D'),
    dict(key='cabin_l', prop='door_cabin_l', kind='SLIDE', side=1, src='BH_Portes_Cabine', obj='BH_Porte_Cabine_G', bone='MCH_Porte_Cabine_G'),
    dict(key='cabin_r', prop='door_cabin_r', kind='SLIDE', side=-1, src='BH_Portes_Cabine', obj='BH_Porte_Cabine_D', bone='MCH_Porte_Cabine_D'),
)
DOOR_PROPS = tuple(d['prop'] for d in DOORS)
COCKPIT_ANGLE = 80.   # ouverture complete de la porte cockpit (degres)
POP = .12             # part de la course consacree a la sortie de la porte cabine (avant de glisser)
VERSION = 1


def has_doors(rig):
    return bool(rig.get('bh_doors')) and all(p in rig for p in DOOR_PROPS)


def door_sources(rig):
    """Objets portes d'origine (un seul maillage pour les deux cotes), enfants du rig."""
    out = {}
    for o in rig.children:
        for name in ('BH_Portes_Cockpit', 'BH_Portes_Cabine'):
            if o.type == 'MESH' and (o.name == name or o.name.startswith(name + '.')):
                out[name] = o
    return out


def can_install(rig):
    if rig is None or rig.type != 'ARMATURE':
        return False, "Aucun rig Black Hawk"
    if has_doors(rig):
        return False, "Les portes sont déjà installées"
    src = door_sources(rig)
    if len(src) < 2:
        return False, "Objets BH_Portes_Cockpit / BH_Portes_Cabine introuvables"
    if rig.data.bones.get('Body') is None:
        return False, "Os Body introuvable"
    return True, ""


def _arm_verts(o, inv):
    me = o.data
    co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    M = np.array(inv @ o.matrix_world)
    return co @ M[:3, :3].T + M[:3, 3]


def _islands(me):
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    lab = -np.ones(len(bm.verts), int); k = 0
    for v in bm.verts:
        if lab[v.index] >= 0:
            continue
        st = [v]; lab[v.index] = k
        while st:
            x = st.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if lab[y.index] < 0:
                    lab[y.index] = k; st.append(y)
        k += 1
    bm.free()
    return lab, k


def _split(o, side, name, inv):
    """Copie de l'objet ne gardant que les faces du cote demande (y > 0 : gauche)."""
    me = o.data.copy(); me.name = name
    M = inv @ o.matrix_world
    bm = bmesh.new(); bm.from_mesh(me)
    dead = [f for f in bm.faces if (M @ f.calc_center_median()).y * side <= 0]
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(me); bm.free()
    n = bpy.data.objects.new(name, me)
    for c in o.users_collection:
        c.objects.link(n)
    for attr in ('visible_camera', 'visible_shadow', 'hide_render'):
        if hasattr(o, attr):
            setattr(n, attr, getattr(o, attr))
    return n


def _fuselage_profile(fus, inv, side, x0, x1, z0, z1, step=.03):
    """|y| maximal du fuselage par case (x, z), echantillonne sur les triangles (pas seulement les sommets)."""
    me = fus.data; me.calc_loop_triangles()
    co = _arm_verts(fus, inv)
    tri = np.zeros(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get('vertices', tri); tri = tri.reshape(-1, 3)
    P = co[tri]
    c = P.mean(1)
    keep = (c[:, 1] * side > 0) & (c[:, 0] > x0 - .3) & (c[:, 0] < x1 + .3) & (c[:, 2] > z0 - .3) & (c[:, 2] < z1 + .3)
    P = P[keep]
    pts = [P.reshape(-1, 3)]
    for a, b in ((1 / 3, 1 / 3), (.6, .2), (.2, .6), (.2, .2), (.5, .5), (.5, 0.), (0., .5)):
        pts.append(P[:, 0] * (1 - a - b) + P[:, 1] * a + P[:, 2] * b)
    # triangles plus grands que la case : subdivision supplementaire
    big = np.linalg.norm(P[:, 1] - P[:, 0], axis=1) + np.linalg.norm(P[:, 2] - P[:, 0], axis=1) > 3 * step
    if big.any():
        Q = P[big]
        for a in np.linspace(0, 1, 9):
            for b in np.linspace(0, 1 - a, max(2, int(9 * (1 - a)))):
                pts.append(Q[:, 0] * (1 - a - b) + Q[:, 1] * a + Q[:, 2] * b)
    S = np.concatenate(pts)
    ix = np.floor(S[:, 0] / step).astype(int); iz = np.floor(S[:, 2] / step).astype(int)
    grid = {}
    for i, k, y in zip(ix, iz, np.abs(S[:, 1])):
        if y > grid.get((i, k), -1.):
            grid[(i, k)] = y
    return grid


def cabin_clearance(door_v, side, grid, travel, step=.03, edge=.08, t0=.1):
    """Ecart lateral mini pour que la porte cabine glisse vers l'arriere sans entrer dans le fuselage.
    Les bandes haute et basse (galets et rails, edge) et le depart dans son propre cadre (t < t0) sont ignores."""
    lo, hi = door_v[:, 2].min(), door_v[:, 2].max()
    v = door_v[::5]
    v = v[(v[:, 2] > lo + edge) & (v[:, 2] < hi - edge)]
    need = 0.
    for t in np.arange(t0, travel + 1e-6, .04):
        ix = np.floor((v[:, 0] - t) / step).astype(int); iz = np.floor(v[:, 2] / step).astype(int)
        for i, k, y in zip(ix, iz, np.abs(v[:, 1])):
            f = grid.get((i, k))
            if f is not None and f - y > need:
                need = f - y
    return need


def _drv(rig, owner, path, idx, expr, **vars_):
    fc = owner.driver_add(path, idx)
    d = fc.driver; d.type = 'SCRIPTED'
    for k, v in vars_.items():
        x = d.variables.new(); x.name = k; x.type = 'SINGLE_PROP'
        t = x.targets[0]; t.id_type = 'OBJECT'; t.id = rig; t.data_path = f'["{v}"]'
    d.expression = expr
    return fc


def _prop(rig, name, value, desc, **kw):
    rig[name] = value
    try:
        rig.id_properties_ui(name).update(description=desc, **kw)
    except Exception:
        pass


def install(rig, context=None, log=print):
    """Ajoute les portes animables au rig. Retourne un resume (dict)."""
    ok, why = can_install(rig)
    if not ok:
        raise RuntimeError(why)
    context = context or bpy.context
    vl = context.view_layer
    src = door_sources(rig)
    arm = rig.data
    old_pose = arm.pose_position
    arm.pose_position = 'REST'; vl.update()
    inv = rig.matrix_world.inverted()
    info = {}
    try:
        # ------------------------------------------------ decoupe gauche / droite
        objs = {}
        rest_mw = {}
        for d in DOORS:
            o = _split(src[d['src']], d['side'], d['obj'], inv)
            objs[d['key']] = o
            rest_mw[d['key']] = src[d['src']].matrix_world.copy()
        vl.update()
        # ------------------------------------------------ geometrie (espace armature, pose de repos)
        geo = {}
        fus = next((o for o in rig.children if o.type == 'MESH' and o.name.startswith('BH_Fuselage')), None)
        for d in DOORS:
            o = objs[d['key']]; v = _arm_verts(o, inv)
            lo, hi = v.min(0), v.max(0)
            if d['kind'] == 'HINGE':
                # charnieres : petits ilots colles au bord avant de la porte
                lab, k = _islands(o.data)
                cs = []
                for i in range(k):
                    p = v[lab == i]
                    if len(p) < 400 and p[:, 0].mean() > hi[0] - .06 and (p[:, 2].mean() - lo[2]) < .6 * (hi[2] - lo[2]):
                        cs.append(p.mean(0))
                if len(cs) >= 2:
                    cs.sort(key=lambda c: c[2]); A, B = Vector(cs[0]), Vector(cs[-1])
                else:  # repli : points les plus en avant du bas de la porte
                    h = hi[2] - lo[2]
                    def front(z0, z1):
                        m = (v[:, 2] > lo[2] + z0 * h) & (v[:, 2] < lo[2] + z1 * h); q = v[m]
                        return Vector(q[q[:, 0].argmax()])
                    A, B = front(.08, .22), front(.28, .42)
                axis = (B - A).normalized()
                rear = Vector(v[v[:, 0] < lo[0] + .1].mean(0))
                sign = 1. if axis.cross(rear - A).y * d['side'] > 0 else -1.
                geo[d['key']] = dict(head=A, tail=A + axis * .45, sign=sign, axis=axis)
            else:
                length = float(hi[0] - lo[0]); travel = round(length - .08, 2)
                geo[d['key']] = dict(head=Vector(((lo + hi) / 2).tolist()), length=length, travel=travel, v=v)
        out = .08
        if fus is not None:
            need = []
            for d in DOORS:
                if d['kind'] != 'SLIDE':
                    continue
                g = geo[d['key']]; v = g['v']; lo, hi = v.min(0), v.max(0)
                grid = _fuselage_profile(fus, inv, d['side'], lo[0] - g['travel'], hi[0], lo[2], hi[2])
                need.append(cabin_clearance(v, d['side'], grid, g['travel']))
            out = float(min(max(max(need) + .015, .03), .25))
            log('PORTES ecart cabine necessaire', [round(x, 3) for x in need], '->', round(out, 3))
        travel = min(geo[d['key']]['travel'] for d in DOORS if d['kind'] == 'SLIDE')
        info.update(travel=travel, out=out, angle=COCKPIT_ANGLE,
                    hinge={d['key']: [round(x, 3) for x in geo[d['key']]['head']] for d in DOORS if d['kind'] == 'HINGE'})
        # ------------------------------------------------ os
        prev_active = vl.objects.active
        prev_mode = rig.mode
        hidden = rig.hide_get()
        rig.hide_set(False); rig.hide_viewport = False
        vl.objects.active = rig
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        EB = arm.edit_bones
        for d in DOORS:
            g = geo[d['key']]; e = EB.new(d['bone'])
            e.head = g['head']
            e.tail = g['tail'] if d['kind'] == 'HINGE' else g['head'] + Vector((0, .3, 0))
            e.roll = 0.; e.use_deform = False; e.parent = EB['Body']
        bpy.ops.object.mode_set(mode='OBJECT')
        PB = rig.pose.bones
        mech = arm.collections.get('Mecanique')
        for d in DOORS:
            pb = PB[d['bone']]; pb.rotation_mode = 'XYZ'
            if mech is not None:
                mech.assign(arm.bones[d['bone']])
        vl.update()
        # ------------------------------------------------ proprietes
        for d in DOORS:
            _prop(rig, d['prop'], 0., "Ouverture de la porte : 0 = fermée, 1 = ouverte", min=0., max=1., soft_min=0., soft_max=1., subtype='FACTOR')
        _prop(rig, 'door_cockpit_angle', COCKPIT_ANGLE, "Angle d'ouverture complète des portes cockpit (degrés)", min=0., max=110.)
        _prop(rig, 'door_cabin_travel', travel, "Course des portes cabine vers l'arrière (m)", min=0., max=2.5, subtype='DISTANCE')
        _prop(rig, 'door_cabin_out', round(out, 3), "Écart latéral des portes cabine sur leurs rails (m)", min=0., max=.4, subtype='DISTANCE')
        rig['door_cabin_travel_def'] = travel; rig['door_cabin_out_def'] = round(out, 3)
        rig['bh_doors'] = VERSION
        # ------------------------------------------------ drivers
        for d in DOORS:
            pb = PB[d['bone']]; g = geo[d['key']]
            if d['kind'] == 'HINGE':
                _drv(rig, pb, 'rotation_euler', 1, f"{g['sign']:.0f}*radians(a)*min(max(o,0),1)", o=d['prop'], a='door_cockpit_angle')
            else:
                _drv(rig, pb, 'location', 0, f"-tr*min(max((o-{POP})/{1 - POP:.2f},0),1)", o=d['prop'], tr='door_cabin_travel')
                _drv(rig, pb, 'location', 1, f"{d['side']}*w*(1-pow(1-min(max(o/{POP},0),1),2))", o=d['prop'], w='door_cabin_out')
        # ------------------------------------------------ parentage (sans bouger les portes)
        for d in DOORS:
            o = objs[d['key']]; b = arm.bones[d['bone']]
            o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = d['bone']
            o.matrix_parent_inverse = (rig.matrix_world @ b.matrix_local @ Matrix.Translation((0, b.length, 0))).inverted()
            o.matrix_basis = rest_mw[d['key']]
        for o in set(src.values()):
            me = o.data
            bpy.data.objects.remove(o)
            if me.users == 0:
                bpy.data.meshes.remove(me)
        if prev_active is not None and prev_active.name in bpy.data.objects:
            vl.objects.active = prev_active
        if hidden:
            rig.hide_set(True)
    finally:
        arm.pose_position = old_pose
        vl.update()
    log('PORTES installees', info)
    return info


def door_state(rig, d):
    """Lecture humaine de l'etat d'une porte : (texte, fraction)."""
    o = min(max(float(rig.get(d['prop'], 0.)), 0.), 1.)
    if d['kind'] == 'HINGE':
        a = rig.get('door_cockpit_angle', COCKPIT_ANGLE)
        return o, a * o, a
    tr = rig.get('door_cabin_travel', 1.85)
    return o, tr * min(max((o - POP) / (1 - POP), 0), 1), tr
