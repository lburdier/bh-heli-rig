bl_info = {
    "name": "Black Hawk Rig",
    "author": "Lucas Burdier",
    "version": (1, 3, 1),
    "blender": (4, 2, 0),
    "location": "Vue 3D > Barre latérale (N) > Black Hawk",
    "description": "Pilote le rig du UH-60 : boucle, rotors, pales, vol stationnaire, portes et LEDs",
    "doc_url": "",
    "category": "Animation",
}

import json, math, os, sys, textwrap

# Mise a jour sans redemarrer Blender : les sous-modules de l'ancienne version (aide, modele, portes)
# restent dans sys.modules et seraient reutilises tels quels -> textes/fonctions perimes (ex. 'tab_PORTES').
# On les retire pour que « from . import » charge ceux de la version installee.
for _m in [m for m in sys.modules if m.startswith(__name__ + '.')]:
    del sys.modules[_m]
    globals().pop(_m.rsplit('.', 1)[1], None)   # sinon « from . import » reprend l'attribut perime en cas de reload

import bpy
import bpy.utils.previews
from bpy.app.handlers import persistent
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty, StringProperty
from bpy.types import AddonPreferences
from bpy_extras import anim_utils

from . import aide, maj, modele, portes

maj.configure('bh_heli_rig', 'lburdier/bh-heli-rig', 'Black Hawk Rig', 'bh',
              busy=lambda: "Téléchargement du modèle en cours" if modele.JOB.busy else "")
from .aide import HELP, LED_LABEL

HERE = os.path.dirname(__file__)
DOC_PATH = os.path.join(HERE, 'doc', 'index.html')
LED_MODE_NAMES = ("Fixe", "Clignotant", "Double flash", "Gyrophare")
# valeurs d'origine (bouton Reinitialiser)
DEFAULTS = {
    'ANIM': dict(rpm=258., tail_ratio=4.6, rotor_dir=1, tail_dir=1, loop_start=1, loop_frames=240, ramp_frames=240),
    'PALES': dict(droop_rest=.62, droop_flight=.24, coning=3.2, collective=6., blade_wobble=.35),
    'VOL': dict(hover_height=1.6, hover_z=.11, hover_xy=.07, hover_tilt=1.1, hover_yaw=.8),
    'LEDS': dict(leds_on=1., leds_blink=1.),
    'PORTES': dict(door_cockpit_l=0., door_cockpit_r=0., door_cabin_l=0., door_cabin_r=0., door_cockpit_angle=portes.COCKPIT_ANGLE),
}
LED_POWER = {'Nav_Babord': (14., 25.), 'Nav_Tribord': (14., 25.), 'Feu_Queue': (14., 60.), 'Gyro_Ventre': (14., 120.),
             'Gyro_Toit': (14., 120.), 'Cockpit_Gauche': (3., 3.), 'Cockpit_Centre': (3., 3.), 'Cockpit_Droit': (3., 3.)}
# limites et unites affichees des proprietes du rig (infos-bulles en francais)
META = {
    'rpm': dict(min=0., max=600., soft_max=400., step=100, precision=1),
    'tail_ratio': dict(min=.5, max=10., step=10, precision=2),
    'rotor_dir': dict(min=-1, max=1), 'tail_dir': dict(min=-1, max=1),
    'loop_start': dict(min=0, max=100000), 'loop_frames': dict(min=24, max=100000, soft_max=1200),
    'ramp_frames': dict(min=24, max=100000, soft_max=1200),
    'spool': dict(min=0., max=1., step=1, precision=3),
    'droop_rest': dict(min=0., max=1.5, step=1, precision=3, subtype='DISTANCE'),
    'droop_flight': dict(min=-.5, max=1.5, step=1, precision=3, subtype='DISTANCE'),
    'coning': dict(min=0., max=10., step=10, precision=2), 'collective': dict(min=-5., max=16., step=10, precision=2),
    'blade_wobble': dict(min=0., max=3., step=5, precision=2),
    'hover_on': dict(min=0., max=1., step=1, precision=3),
    'hover_height': dict(min=0., max=50., soft_max=20., step=10, precision=2, subtype='DISTANCE'),
    'hover_z': dict(min=0., max=2., step=1, precision=3, subtype='DISTANCE'),
    'hover_xy': dict(min=0., max=2., step=1, precision=3, subtype='DISTANCE'),
    'hover_tilt': dict(min=0., max=15., step=10, precision=2), 'hover_yaw': dict(min=0., max=15., step=10, precision=2),
    'leds_on': dict(min=0., max=1., step=1, precision=2), 'leds_blink': dict(min=0., max=1., step=1, precision=2),
    'rotor_turns': {}, 'tail_turns': {}, 'loop_phase': {}, 'anim_mode': None, 'led_names': None, 'bh_rig': {},
    'door_cockpit_l': dict(min=0., max=1., step=5, precision=2, subtype='FACTOR'), 'door_cockpit_r': dict(min=0., max=1., step=5, precision=2, subtype='FACTOR'),
    'door_cabin_l': dict(min=0., max=1., step=5, precision=2, subtype='FACTOR'), 'door_cabin_r': dict(min=0., max=1., step=5, precision=2, subtype='FACTOR'),
    'door_cockpit_angle': dict(min=0., max=110., step=100, precision=0),
    'door_cabin_travel': dict(min=0., max=2.5, step=1, precision=3, subtype='DISTANCE'),
    'door_cabin_out': dict(min=0., max=.4, step=1, precision=3, subtype='DISTANCE'),
    'door_cabin_travel_def': None, 'door_cabin_out_def': None, 'bh_doors': None, 'bh_model': None,
}
LED_META = {
    'color': ('led_color', dict(min=0., max=1., subtype='COLOR')),
    'glow': ('led_glow', dict(min=0., max=200., soft_max=50., step=10, precision=1)),
    'watts': ('led_watts', dict(min=0., max=5000., soft_max=500., step=100, precision=0)),
    'mode': ('led_mode', dict(min=0, max=3)),
    'cycles': ('led_cycles', dict(min=1, max=200)),
    'phase': ('led_phase', dict(min=0., max=1., step=1, precision=3)),
    't': ('led_t', {}), 'level': ('led_level', {}),
    'color_def': ('led_def', None), 'mode_def': ('led_def', None), 'cycles_def': ('led_def', None), 'phase_def': ('led_def', None),
}
PCOLL = None
# regime reel du UH-60 : 100 % Nr = 258 tr/min ; rotor de queue ~1 190 tr/min (rapport ~4,6)
NR_RPM = 258.
TAIL_REAL_RPM = 1190.
SOUND = 340.3  # vitesse du son au niveau de la mer (m/s)


# ------------------------------------------------------------------ outils
def find_rig(context):
    o = getattr(context, 'active_object', None)
    if o is not None and o.get('bh_rig'):
        return o
    if o is not None and o.parent is not None and o.parent.get('bh_rig'):
        return o.parent
    scene = getattr(context, 'scene', None)
    for o in (scene.objects if scene else ()):
        if o.get('bh_rig'):
            return o
    return None


def channelbag(rig):
    ad = rig.animation_data
    if ad is None or ad.action is None or ad.action_slot is None:
        return None
    return anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)


def is_animated(rig, name):
    cb = channelbag(rig)
    return cb is not None and cb.fcurves.find(f'["{name}"]') is not None


def set_curve(rig, name, points, extrapolate=False):
    """Remplace la courbe de la propriete par des cles lineaires."""
    path = f'["{name}"]'
    cb = channelbag(rig)
    if cb is not None:
        fc = cb.fcurves.find(path)
        if fc is not None:
            cb.fcurves.remove(fc)
    for frame, value in points:
        rig[name] = float(value)
        rig.keyframe_insert(data_path=path, frame=frame)
    fc = channelbag(rig).fcurves.find(path)
    for k in fc.keyframe_points:
        k.interpolation = 'LINEAR'
    fc.extrapolation = 'LINEAR' if extrapolate else 'CONSTANT'
    fc.update()
    rig.update_tag()


def clear_curve(rig, name, value):
    cb = channelbag(rig)
    if cb is not None:
        fc = cb.fcurves.find(f'["{name}"]')
        if fc is not None:
            cb.fcurves.remove(fc)
    rig[name] = float(value)
    rig.update_tag()


def loop_turns(rig, scene):
    """Tours entiers par boucle : la derniere image raccorde exactement avec la premiere."""
    seconds = rig['loop_frames'] / (scene.render.fps / scene.render.fps_base)
    main = max(1, round(rig['rpm'] / 60 * seconds)) if rig['rpm'] > 0 else 0
    tail = round(main * rig['tail_ratio'])
    return main, tail, seconds


def apply_loop(rig, scene):
    """Boucle continue : rotors a regime constant, plage d'images calee sur la boucle."""
    s, n = int(rig['loop_start']), int(rig['loop_frames'])
    main, tail, _ = loop_turns(rig, scene)
    set_curve(rig, 'rotor_turns', [(s, 0), (s + n, main)], True)
    set_curve(rig, 'tail_turns', [(s, 0), (s + n, tail)], True)
    clear_curve(rig, 'spool', 1)
    clear_curve(rig, 'hover_on', 1)
    scene.frame_start, scene.frame_end = s, s + n - 1


def smooth(x):
    x = min(max(x, 0), 1)
    return x * x * (3 - 2 * x)


def apply_ramp(rig, scene, frames, down=False):
    """Demarrage ou arret : integre le regime image par image pour que les pales accelerent sans a-coup."""
    s = int(rig['loop_start'])
    fps = scene.render.fps / scene.render.fps_base
    main = tail = 0.0
    pts_m, pts_t, pts_s, pts_h = [], [], [], []
    step = 2
    for i in range(0, frames + step, step):
        f = min(i, frames)
        k = smooth(f / frames)
        if down:
            k = 1 - k
        pts_m.append((s + f, main)); pts_t.append((s + f, tail)); pts_s.append((s + f, k))
        pts_h.append((s + f, smooth((k - .75) / .25)))
        main += rig['rpm'] * k / 60 / fps * step
        tail += rig['rpm'] * rig['tail_ratio'] * k / 60 / fps * step
    set_curve(rig, 'rotor_turns', pts_m, not down)
    set_curve(rig, 'tail_turns', pts_t, not down)
    set_curve(rig, 'spool', pts_s)
    set_curve(rig, 'hover_on', pts_h)
    scene.frame_start, scene.frame_end = s, s + frames


def apply_parked(rig, scene):
    for n in ('rotor_turns', 'tail_turns'):
        clear_curve(rig, n, 0)
    clear_curve(rig, 'spool', 0)
    clear_curve(rig, 'hover_on', 0)


def blade_radius(rig):
    """Rayon du rotor (bout de la derniere section de pale), 8,17 m sur ce modele."""
    b = rig.data.bones.get('DEF_Pale1_8') if rig.type == 'ARMATURE' else None
    if b is None:
        return 8.17
    t = b.tail_local
    return math.hypot(t.x, t.y)


def turns_at(rig, frame, name='rotor_turns'):
    cb = channelbag(rig)
    fc = cb.fcurves.find(f'["{name}"]') if cb else None
    return fc.evaluate(frame) if fc else float(rig.get(name, 0.))


def rotor_info(rig, scene, frame=None):
    """Grandeurs du regime : consigne, regime de la boucle, regime instantane, bout de pale, aspect a l'ecran."""
    fps = scene.render.fps / scene.render.fps_base
    f = scene.frame_current if frame is None else frame
    main, tail, sec = loop_turns(rig, scene)
    loop_rpm = main * 60 / sec if sec > 0 else 0.
    mode = rig.get('anim_mode', 'LOOP')
    target = loop_rpm if mode == 'LOOP' else (0. if mode == 'PARKED' else rig['rpm'])
    tail_rpm = (tail * 60 / sec if sec > 0 else 0.) if mode == 'LOOP' else target * rig['tail_ratio']
    # regime instantane : derivee des tours animes autour de l'image courante
    now = abs(turns_at(rig, f + .5) - turns_at(rig, f - .5)) * fps * 60
    now_tail = abs(turns_at(rig, f + .5, 'tail_turns') - turns_at(rig, f - .5, 'tail_turns')) * fps * 60
    R = blade_radius(rig)
    deg = target / 60 * 360 / fps
    a = deg % 90  # 4 pales identiques : l'image du rotor se repete tous les 90 degres
    if target == 0:
        look = "rotor immobile"
    elif a < 3 or a > 87:
        look = "semble immobile (effet stroboscopique)"
    elif a > 45:
        look = f"semble reculer de {90 - a:.1f}° par image"
    else:
        look = f"semble avancer de {a:.1f}° par image"
    tip = 2 * math.pi * R * target / 60
    return dict(target=target, loop_rpm=loop_rpm, pct=100 * target / NR_RPM, rps=target / 60, deg=deg, tail=tail_rpm,
                tip=tip, mach=tip / SOUND, radius=R, look=look, now=now, now_pct=100 * now / NR_RPM, now_tail=now_tail,
                fps=fps, mode=mode)


def ramp_frames(rig):
    return int(rig.get('ramp_frames', 240))


def refresh(rig, scene):
    """Recale l'animation du mode courant apres un changement de reglage."""
    mode = rig.get('anim_mode', 'LOOP')
    if mode == 'LOOP':
        apply_loop(rig, scene)
    elif mode in ('STARTUP', 'SHUTDOWN'):
        apply_ramp(rig, scene, ramp_frames(rig), mode == 'SHUTDOWN')


def led_ids(rig):
    return json.loads(rig['led_names'])


def touch(rig):
    rig.update_tag()
    bpy.context.view_layer.update()


def apply_meta(rig):
    """Infos-bulles francaises, limites et unites des proprietes du rig (aussi visibles dans Proprietes > Objet)."""
    def upd(name, key, kw):
        if name not in rig.keys():
            return
        try:
            ui = rig.id_properties_ui(name)
            ui.update(description=aide.tooltip(key), **(kw or {}))
        except Exception as e:  # propriete d'un type sans donnees d'interface
            print('BH meta', name, e)
    for name, kw in META.items():
        upd(name, name, kw)
    for i, _ in enumerate(led_ids(rig), 1):
        for suffix, (key, kw) in LED_META.items():
            upd(f'led_{i:02d}_{suffix}', key, kw)


def apply_meta_all():
    for sc in bpy.data.scenes:
        for o in sc.objects:
            if o.get('bh_rig'):
                apply_meta(o)


# ------------------------------------------------------------------ icones et illustrations
def ICON(name):
    k = 'ico_' + name
    return PCOLL[k].icon_id if PCOLL and k in PCOLL else 0


def IMG(name):
    k = 'img_' + name
    return PCOLL[k].icon_id if PCOLL and k in PCOLL else 0


def icon_kw(spec):
    if not spec:
        return {}
    if spec.startswith('@'):
        return dict(icon_value=ICON(spec[1:]))
    return dict(icon=spec)


def load_previews():
    global PCOLL
    PCOLL = bpy.utils.previews.new()
    for sub, pre in (('icons', 'ico_'), ('images', 'img_')):
        d = os.path.join(HERE, sub)
        for f in sorted(os.listdir(d)) if os.path.isdir(d) else ():
            if f.endswith('.png'):
                PCOLL.load(pre + f[:-4], os.path.join(d, f), 'IMAGE')


# ------------------------------------------------------------------ reglages relies au rig : chaque changement recale l'animation
def _get(name, default):
    return lambda self: self.get(name, default)


def _set(name, cast):
    def f(self, value):
        self[name] = cast(value)
        if self.get('bh_rig'):
            refresh(self, bpy.context.scene)
    return f


def _dir_get(name):
    return lambda self: 0 if self.get(name, 1) >= 0 else 1


def _dir_set(name):
    def f(self, value):
        self[name] = 1 if value == 0 else -1
        self.update_tag()
    return f


DIR_ITEMS = (('NORMAL', "Normal", "Sens d'origine (rotor principal : anti-horaire vu de dessus, comme le vrai UH-60)", 'LOOP_FORWARDS', 0),
             ('INV', "Inversé", "Sens inverse", 'LOOP_BACK', 1))


def register_props():
    O = bpy.types.Object
    O.bh_rpm = FloatProperty(name="Régime", min=0, soft_max=400, precision=1, get=_get('rpm', 258.), set=_set('rpm', float),
                             description=aide.tooltip('rpm'))
    O.bh_nr = FloatProperty(name="Régime nominal (Nr)", min=0, max=130, soft_max=110, precision=1, subtype='PERCENTAGE',
                            get=lambda self: 100 * self.get('rpm', NR_RPM) / NR_RPM,
                            set=lambda self, v: _set('rpm', float)(self, v * NR_RPM / 100),
                            description=aide.tooltip('nr'))
    O.bh_ratio = FloatProperty(name="Rapport queue", min=.5, soft_max=8, precision=2, get=_get('tail_ratio', 4.6), set=_set('tail_ratio', float),
                               description=aide.tooltip('tail_ratio'))
    O.bh_frames = IntProperty(name="Durée de la boucle", min=24, soft_max=1200, get=_get('loop_frames', 240), set=_set('loop_frames', int),
                              description=aide.tooltip('loop_frames'))
    O.bh_start = IntProperty(name="Image de départ", min=0, soft_max=1000, get=_get('loop_start', 1), set=_set('loop_start', int),
                             description=aide.tooltip('loop_start'))
    O.bh_ramp = IntProperty(name="Durée de la rampe", min=24, soft_max=1200, get=_get('ramp_frames', 240), set=_set('ramp_frames', int),
                            description=aide.tooltip('ramp_frames'))
    O.bh_rotor_dir = EnumProperty(name="Sens principal", items=DIR_ITEMS, get=_dir_get('rotor_dir'), set=_dir_set('rotor_dir'),
                                  description=aide.tooltip('rotor_dir'))
    O.bh_tail_dir = EnumProperty(name="Sens queue", items=DIR_ITEMS, get=_dir_get('tail_dir'), set=_dir_set('tail_dir'),
                                 description=aide.tooltip('tail_dir'))


PROP_NAMES = ('bh_nr', 'bh_rpm', 'bh_ratio', 'bh_frames', 'bh_start', 'bh_ramp', 'bh_rotor_dir', 'bh_tail_dir')


def unregister_props():
    for n in PROP_NAMES:
        if hasattr(bpy.types.Object, n):
            delattr(bpy.types.Object, n)


# ------------------------------------------------------------------ etat de l'interface (onglet, illustrations)
_TAB_ITEMS = []
TABS = ('ANIM', 'PALES', 'VOL', 'PORTES', 'LEDS', 'AIDE')
_LED_ITEMS = []


def tab_items(self, context):
    return _TAB_ITEMS


def led_mode_items(self, context):
    return _LED_ITEMS


def build_items():
    _TAB_ITEMS.clear()
    for n, k in enumerate(TABS):
        h = HELP['tab_' + k]
        _TAB_ITEMS.append((k, h['t'], h['court'], ICON(h['ico'][1:]), n))
    _LED_ITEMS.clear()
    for m in range(4):
        h = HELP[f'led_mode_{m}']
        _LED_ITEMS.append((str(m), h['t'], h['court'], ICON(f'led_mode_{m}'), m))


DOOR_WHICH = (('ALL', "Toutes les portes", "Les quatre portes", 'SELECT_EXTEND', 0),
              ('COCKPIT', "Portes cockpit", "Pilote et copilote (charnières)", 'MOD_SOLIDIFY', 1),
              ('CABIN', "Portes cabine", "Les deux portes coulissantes", 'ARROW_LEFTRIGHT', 2),
              ('LEFT', "Côté gauche", "Cockpit et cabine, côté gauche", 'TRIA_LEFT', 3),
              ('RIGHT', "Côté droit", "Cockpit et cabine, côté droit", 'TRIA_RIGHT', 4))


def doors_for(which):
    return [d for d in portes.DOORS if which == 'ALL' or (which == 'COCKPIT' and d['kind'] == 'HINGE')
            or (which == 'CABIN' and d['kind'] == 'SLIDE') or (which == 'LEFT' and d['side'] > 0) or (which == 'RIGHT' and d['side'] < 0)]


class BH_UI(bpy.types.PropertyGroup):
    tab: EnumProperty(name="Onglet", items=tab_items, description="Section du panneau Black Hawk")
    show_images: BoolProperty(name="Illustrations", default=True, description=aide.tooltip('show_images'))
    show_hud: BoolProperty(name="Régime dans la vue 3D", default=True, description=aide.tooltip('hud'))
    img_scale: IntProperty(name="Taille", default=7, min=4, max=16, description=aide.tooltip('img_scale'))
    door_which: EnumProperty(name="Portes", items=DOOR_WHICH, default='ALL', description=aide.tooltip('door_which'))
    door_frames: IntProperty(name="Durée", default=48, min=1, soft_max=240, description=aide.tooltip('door_frames'))
    model_studio: BoolProperty(name="Avec studio et caméras", default=False, description=aide.tooltip('model_studio'))


# ------------------------------------------------------------------ operateurs
class BH_OT_Anim(bpy.types.Operator):
    bl_idname = "bh.anim_mode"
    bl_label = "Mode d'animation"
    bl_options = {'REGISTER', 'UNDO'}
    mode: EnumProperty(items=(('LOOP', "Boucle", aide.tooltip('mode_LOOP')),
                              ('STARTUP', "Démarrage", aide.tooltip('mode_STARTUP')),
                              ('SHUTDOWN', "Arrêt", aide.tooltip('mode_SHUTDOWN')),
                              ('PARKED', "Parking", aide.tooltip('mode_PARKED'))))
    frames: IntProperty(name="Durée de la rampe", default=0, min=0, soft_max=1200,
                        description="Durée du démarrage ou de l'arrêt (0 = valeur du rig)")

    @classmethod
    def description(cls, context, props):
        return aide.full_text('mode_' + props.mode)

    def execute(self, context):
        rig = find_rig(context)
        if rig is None:
            self.report({'ERROR'}, "Aucun rig Black Hawk dans la scène")
            return {'CANCELLED'}
        rig['anim_mode'] = self.mode
        if self.frames > 0:
            rig['ramp_frames'] = int(self.frames)
        if self.mode == 'LOOP':
            apply_loop(rig, context.scene)
        elif self.mode == 'PARKED':
            apply_parked(rig, context.scene)
        else:
            apply_ramp(rig, context.scene, ramp_frames(rig), self.mode == 'SHUTDOWN')
        context.scene.frame_set(context.scene.frame_start)
        apply_meta(rig)
        touch(rig)
        return {'FINISHED'}


class BH_OT_RealRpm(bpy.types.Operator):
    bl_idname = "bh.real_rpm"
    bl_label = "Régime réel UH-60"
    bl_description = aide.tooltip('rpm_real')
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        rig = find_rig(context)
        rig['tail_ratio'] = round(TAIL_REAL_RPM / NR_RPM, 2)
        rig.bh_rpm = NR_RPM  # recale aussi la boucle ou la rampe
        self.report({'INFO'}, f"Rotor principal {NR_RPM:.0f} tr/min (100 % Nr), queue {NR_RPM * rig['tail_ratio']:.0f} tr/min")
        return {'FINISHED'}


class BH_OT_LedMode(bpy.types.Operator):
    bl_idname = "bh.led_mode"
    bl_label = "Mode de la LED"
    bl_description = aide.tooltip('led_mode')
    bl_property = "mode"
    bl_options = {'REGISTER', 'UNDO'}
    led: IntProperty()
    mode: EnumProperty(items=led_mode_items)

    def execute(self, context):
        rig = find_rig(context)
        rig[f'led_{self.led:02d}_mode'] = int(self.mode)
        touch(rig)
        return {'FINISHED'}


class BH_OT_LedPreset(bpy.types.Operator):
    bl_idname = "bh.led_preset"
    bl_label = "Prérégler les LEDs"
    bl_options = {'REGISTER', 'UNDO'}
    preset: EnumProperty(items=(('AVIATION', "Aviation", aide.tooltip('preset_AVIATION')),
                                ('RED', "Tout rouge", aide.tooltip('preset_RED')),
                                ('WHITE', "Tout blanc", aide.tooltip('preset_WHITE')),
                                ('SYNC', "Clignotement commun", aide.tooltip('preset_SYNC'))))

    @classmethod
    def description(cls, context, props):
        return aide.full_text('preset_' + props.preset)

    def execute(self, context):
        rig = find_rig(context)
        for i, name in enumerate(led_ids(rig), 1):
            p = f'led_{i:02d}_'
            if self.preset == 'AVIATION':
                rig[p + 'color'] = list(rig[p + 'color_def']); rig[p + 'mode'] = rig[p + 'mode_def']
                rig[p + 'cycles'] = rig[p + 'cycles_def']; rig[p + 'phase'] = rig[p + 'phase_def']
            elif self.preset == 'RED':
                rig[p + 'color'] = [1., .03, .01]
            elif self.preset == 'WHITE':
                rig[p + 'color'] = [1., 1., 1.]
            else:
                rig[p + 'mode'] = 1; rig[p + 'phase'] = 0.; rig[p + 'cycles'] = 10
        touch(rig)
        return {'FINISHED'}


class BH_OT_Help(bpy.types.Operator):
    bl_idname = "bh.help"
    bl_label = "Aide Black Hawk"
    bl_options = {'INTERNAL'}
    topic: StringProperty(options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, props):
        return aide.full_text(props.topic) + "\n\nClic : illustration et explication complète"

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=420)

    def draw(self, context):
        h = HELP.get(self.topic, {}); lay = self.layout
        row = lay.row(); row.scale_y = 1.2
        row.label(text=h.get('t', "Aide"), **icon_kw(h.get('ico')))
        if h.get('img') and IMG(h['img']):
            lay.template_icon(icon_value=IMG(h['img']), scale=20)
        col = lay.column(align=True)
        wrap(col, aide.full_text(self.topic), 64)
        lay.separator()
        lay.operator("bh.open_doc", **icon_kw(HELP['open_doc']['ico']))

    def execute(self, context):
        return {'FINISHED'}


class BH_OT_OpenDoc(bpy.types.Operator):
    bl_idname = "bh.open_doc"
    bl_label = "Ouvrir la documentation"
    bl_description = aide.tooltip('open_doc')

    def execute(self, context):
        if not os.path.isfile(DOC_PATH):
            self.report({'ERROR'}, "Documentation introuvable : " + DOC_PATH)
            return {'CANCELLED'}
        bpy.ops.wm.url_open(url='file:///' + DOC_PATH.replace('\\', '/'))
        return {'FINISHED'}


def _object_mode(context):
    if context.mode != 'OBJECT' and context.active_object is not None:
        bpy.ops.object.mode_set(mode='OBJECT')


class BH_OT_SelectBone(bpy.types.Operator):
    bl_idname = "bh.select_bone"
    bl_label = "Sélectionner le contrôle"
    bl_options = {'REGISTER', 'UNDO'}
    bone: StringProperty()

    @classmethod
    def description(cls, context, props):
        return aide.tooltip('bone_' + props.bone) + ". Clic : sélectionne l'os en mode Pose"

    def execute(self, context):
        rig = find_rig(context)
        if rig is None or props_missing(rig.pose.bones, self.bone):
            return {'CANCELLED'}
        _object_mode(context)
        for o in context.selected_objects:
            o.select_set(False)
        rig.hide_set(False); rig.select_set(True); context.view_layer.objects.active = rig
        bpy.ops.object.mode_set(mode='POSE')
        b = rig.data.bones[self.bone]
        for c in b.collections:
            c.is_visible = True
        for pb in rig.pose.bones:
            _bone_select(rig, pb, False)
        _bone_select(rig, rig.pose.bones[self.bone], True)
        rig.data.bones.active = b
        return {'FINISHED'}


def props_missing(coll, name):
    return coll.get(name) is None


def _bone_select(rig, pb, state):
    if hasattr(pb, 'select'):
        pb.select = state
    else:
        rig.data.bones[pb.name].select = state


class BH_OT_SelectLed(bpy.types.Operator):
    bl_idname = "bh.select_led"
    bl_label = "Sélectionner la LED"
    bl_description = aide.tooltip('led_select')
    bl_options = {'REGISTER', 'UNDO'}
    led: IntProperty()

    def execute(self, context):
        o = next((o for o in context.scene.objects if o.type == 'LIGHT' and o.name.startswith(f'LED_{self.led:02d}_')), None)
        if o is None:
            self.report({'WARNING'}, "Lumière de la LED introuvable")
            return {'CANCELLED'}
        _object_mode(context)
        for x in context.selected_objects:
            x.select_set(False)
        o.hide_set(False); o.select_set(True); context.view_layer.objects.active = o
        return {'FINISHED'}


class BH_OT_DiscFlat(bpy.types.Operator):
    bl_idname = "bh.disc_flat"
    bl_label = "Remettre à plat"
    bl_description = "Remet le disque rotor à plat (rotations de CTRL_Disque à 0)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pb = find_rig(context).pose.bones.get('CTRL_Disque')
        if pb:
            pb.rotation_euler = (0, 0, 0)
        return {'FINISHED'}


class BH_OT_Reset(bpy.types.Operator):
    bl_idname = "bh.reset"
    bl_label = "Réinitialiser"
    bl_options = {'REGISTER', 'UNDO'}
    section: EnumProperty(items=(('ANIM', "Animation", ""), ('PALES', "Pales", ""), ('VOL', "Vol", ""), ('PORTES', "Portes", ""),
                                 ('LEDS', "LEDs", ""), ('ALL', "Tout", "")))

    @classmethod
    def description(cls, context, props):
        if props.section == 'ALL':
            return "Remet tous les réglages du rig à leurs valeurs d'origine et relance la boucle"
        if props.section == 'PORTES':
            return "Ferme les quatre portes, efface leur animation et remet angle, course et écart à leurs valeurs d'origine"
        return aide.tooltip('reset')

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        rig = find_rig(context); sc = context.scene
        secs = ('ANIM', 'PALES', 'VOL', 'PORTES', 'LEDS') if self.section == 'ALL' else (self.section,)
        for s in secs:
            if s == 'PORTES' and not portes.has_doors(rig):
                continue
            for k, v in DEFAULTS[s].items():
                rig[k] = v
        if 'PORTES' in secs and portes.has_doors(rig):
            clear_doors_anim(rig)
            for k in ('door_cabin_travel', 'door_cabin_out'):
                rig[k] = rig.get(k + '_def', rig[k])
        if 'PALES' in secs:
            pb = rig.pose.bones.get('CTRL_Disque')
            if pb:
                pb.rotation_euler = (0, 0, 0)
        if 'LEDS' in secs:
            bpy.ops.bh.led_preset(preset='AVIATION')
            for i, name in enumerate(led_ids(rig), 1):
                g, w = LED_POWER.get(name, (14., 25.))
                rig[f'led_{i:02d}_glow'] = g; rig[f'led_{i:02d}_watts'] = w
        if self.section == 'ALL':
            rig['anim_mode'] = 'LOOP'
        refresh(rig, sc)
        apply_meta(rig)
        touch(rig)
        return {'FINISHED'}


def _need_doors(op, rig):
    if rig is None:
        op.report({'ERROR'}, "Aucun rig Black Hawk dans la scène"); return False
    if not portes.has_doors(rig):
        op.report({'ERROR'}, "Ce rig n'a pas de portes animables : onglet Portes › Ajouter les portes"); return False
    return True


def _key_door(rig, prop, frame):
    rig.keyframe_insert(data_path=f'["{prop}"]', frame=frame)


class BH_OT_DoorsSet(bpy.types.Operator):
    bl_idname = "bh.doors_set"
    bl_label = "Ouvrir / fermer les portes"
    bl_options = {'REGISTER', 'UNDO'}
    value: FloatProperty(name="Ouverture", min=0., max=1., default=1.)
    which: EnumProperty(name="Portes", items=DOOR_WHICH, default='ALL')

    @classmethod
    def description(cls, context, props):
        return aide.tooltip('doors_open' if props.value > .5 else 'doors_close')

    def execute(self, context):
        rig = find_rig(context)
        if not _need_doors(self, rig):
            return {'CANCELLED'}
        f = context.scene.frame_current
        for d in doors_for(self.which):
            rig[d['prop']] = self.value
            if is_animated(rig, d['prop']):
                _key_door(rig, d['prop'], f)
        touch(rig)
        return {'FINISHED'}


class BH_OT_DoorsAnim(bpy.types.Operator):
    bl_idname = "bh.doors_anim"
    bl_label = "Animer les portes"
    bl_options = {'REGISTER', 'UNDO'}
    open: BoolProperty(name="Ouvrir", default=True)
    which: EnumProperty(name="Portes", items=DOOR_WHICH, default='ALL')
    frames: IntProperty(name="Durée", default=48, min=1, soft_max=240, description=aide.tooltip('door_frames'))

    @classmethod
    def description(cls, context, props):
        return aide.full_text('door_anim' if props.open else 'door_anim_close')

    def execute(self, context):
        rig = find_rig(context)
        if not _need_doors(self, rig):
            return {'CANCELLED'}
        sc = context.scene; f0 = sc.frame_current; f1 = f0 + self.frames
        target = 1. if self.open else 0.
        for d in doors_for(self.which):
            p = d['prop']
            _key_door(rig, p, f0)            # etat actuel au depart
            rig[p] = target
            _key_door(rig, p, f1)
            fc = channelbag(rig).fcurves.find(f'["{p}"]')
            for k in fc.keyframe_points:
                if abs(k.co.x - f0) < .01 or abs(k.co.x - f1) < .01:
                    k.interpolation = 'BEZIER'; k.handle_left_type = k.handle_right_type = 'AUTO_CLAMPED'
            fc.update()
        sc.frame_set(f0)
        msg = f"Portes : {'ouverture' if self.open else 'fermeture'} de l'image {f0} à {f1}"
        if f1 > sc.frame_end:
            msg += f" (attention : la scène s'arrête à l'image {sc.frame_end})"
        self.report({'INFO'}, msg)
        return {'FINISHED'}


class BH_OT_DoorsKey(bpy.types.Operator):
    bl_idname = "bh.doors_key"
    bl_label = "Clé sur les portes"
    bl_description = aide.tooltip('door_key')
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        rig = find_rig(context)
        if not _need_doors(self, rig):
            return {'CANCELLED'}
        for p in portes.DOOR_PROPS:
            _key_door(rig, p, context.scene.frame_current)
        return {'FINISHED'}


def clear_doors_anim(rig):
    cb = channelbag(rig)
    for p in portes.DOOR_PROPS:
        fc = cb.fcurves.find(f'["{p}"]') if cb else None
        if fc is not None:
            cb.fcurves.remove(fc)


class BH_OT_DoorsClear(bpy.types.Operator):
    bl_idname = "bh.doors_clear"
    bl_label = "Effacer l'animation des portes"
    bl_description = aide.tooltip('door_clear')
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        rig = find_rig(context)
        if not _need_doors(self, rig):
            return {'CANCELLED'}
        vals = {p: float(rig[p]) for p in portes.DOOR_PROPS}
        clear_doors_anim(rig)
        for p, v in vals.items():
            rig[p] = v
        touch(rig)
        return {'FINISHED'}


class BH_OT_DoorsInstall(bpy.types.Operator):
    bl_idname = "bh.doors_install"
    bl_label = "Ajouter les portes à ce rig"
    bl_description = aide.full_text('doors_install')
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        rig = find_rig(context)
        ok, why = portes.can_install(rig)
        if not ok:
            self.report({'ERROR'}, why); return {'CANCELLED'}
        try:
            info = portes.install(rig, context, log=lambda *a: None)
        except Exception as e:
            self.report({'ERROR'}, f"Installation des portes impossible : {e}"); return {'CANCELLED'}
        apply_meta(rig); touch(rig)
        context.window_manager.bh_ui.tab = 'PORTES'
        self.report({'INFO'}, f"Portes installées : course cabine {fr(info['travel'], 2)} m, écart {fr(info['out'] * 100, 1)} cm")
        return {'FINISHED'}


class BH_OT_ModelDownload(bpy.types.Operator):
    bl_idname = "bh.model_download"
    bl_label = "Télécharger le modèle"
    bl_description = aide.tooltip('model_download')

    def execute(self, context):
        if not getattr(bpy.app, 'online_access', True):
            self.report({'ERROR'}, aide.tooltip('online')); return {'CANCELLED'}
        if not modele.start_download():
            self.report({'WARNING'}, "Un téléchargement est déjà en cours"); return {'CANCELLED'}
        self.report({'INFO'}, "Téléchargement du modèle UH-60 lancé")
        return {'FINISHED'}


class BH_OT_ModelCancel(bpy.types.Operator):
    bl_idname = "bh.model_cancel"
    bl_label = "Annuler le téléchargement"
    bl_description = aide.tooltip('model_cancel')

    def execute(self, context):
        modele.JOB.cancel = True
        return {'FINISHED'}


class BH_OT_ModelImport(bpy.types.Operator):
    bl_idname = "bh.model_import"
    bl_label = "Ajouter le UH-60 à la scène"
    bl_description = aide.full_text('model_import')
    bl_options = {'REGISTER', 'UNDO'}
    studio: BoolProperty(name="Avec studio et caméras", default=False, description=aide.tooltip('model_studio'))

    def execute(self, context):
        info = modele.local_model()
        if info is None:
            self.report({'ERROR'}, "Modèle non installé : le télécharger d'abord"); return {'CANCELLED'}
        _object_mode(context)
        try:
            rig = modele.import_model(context, info, studio=self.studio)
        except Exception as e:
            self.report({'ERROR'}, f"Import impossible : {e}"); return {'CANCELLED'}
        if rig is None:
            self.report({'ERROR'}, "Le fichier du modèle ne contient pas de rig Black Hawk"); return {'CANCELLED'}
        refresh(rig, context.scene); apply_meta(rig); touch(rig)
        context.scene.frame_set(context.scene.frame_start)
        self.report({'INFO'}, f"UH-60 {info.get('version', '')} ajouté : {rig.name}")
        return {'FINISHED'}


class BH_OT_ModelFile(bpy.types.Operator):
    bl_idname = "bh.model_file"
    bl_label = "Installer le modèle depuis un fichier"
    bl_description = aide.tooltip('model_file')
    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.zip", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        try:
            info = modele.install_zip(bpy.path.abspath(self.filepath), modele.store_dir())
        except Exception as e:
            self.report({'ERROR'}, f"Archive refusée : {e}"); return {'CANCELLED'}
        self.report({'INFO'}, f"Modèle {info['version']} installé")
        return {'FINISHED'}


class BH_OT_ModelFolder(bpy.types.Operator):
    bl_idname = "bh.model_folder"
    bl_label = "Ouvrir le dossier du modèle"
    bl_description = aide.tooltip('model_folder')

    def execute(self, context):
        bpy.ops.wm.path_open(filepath=modele.store_dir())
        return {'FINISHED'}


class BH_Prefs(AddonPreferences):
    bl_idname = __package__
    catalog_url: StringProperty(name="Catalogue du modèle", default="",
                                description="Adresse du fichier modele.json (vide = page de publication officielle du plugin)")
    store_dir: StringProperty(name="Dossier du modèle", default="", subtype='DIR_PATH',
                              description="Où installer le modèle téléchargé (vide = dossier utilisateur de l'extension)")

    maj_verifier: BoolProperty(name="Rechercher les mises à jour au démarrage", default=True,
                               description="Demande à GitHub, au plus toutes les 12 h, si une nouvelle version est publiée")
    maj_auto: BoolProperty(name="Installer automatiquement", default=True,
                           description="Installe toute seule la nouvelle version (jamais pendant un pilotage ou un téléchargement). "
                                       "Désactivé : un bouton apparaît dans le panneau")

    def draw(self, context):
        lay = self.layout
        maj.draw_prefs(lay, self)
        draw_model(lay.box(), context, context.window_manager.bh_ui)
        col = lay.column()
        col.prop(self, 'store_dir'); col.prop(self, 'catalog_url')
        c = col.column(align=True); c.active = False
        c.label(text="Catalogue par défaut : " + modele.CATALOG_URL)


# ------------------------------------------------------------------ dessin
def wrap(layout, text, width):
    for para in text.split('\n'):
        for ln in textwrap.wrap(para, max(18, width)) or ['']:
            layout.label(text=ln)


def text_width(context, pad=40):
    region = getattr(context, 'region', None)
    w = region.width if region is not None else 300
    prefs = getattr(context, "preferences", None)
    scale = (prefs.system.ui_scale if prefs else 0) or 1.
    return int((w - pad) / (6.2 * scale))


def help_btn(layout, key):
    layout.operator("bh.help", text="", icon='QUESTION', emboss=False).topic = key


def prop_row(col, owner, path, key, text=None, slider=False, index=-1, expand=False):
    """[icone] [champ] [?] : survol du champ = info-bulle, clic sur ? = illustration."""
    h = HELP[key]
    row = col.row(align=True)
    row.label(text="", **icon_kw(h.get('ico')))
    row.prop(owner, path, text=h['t'] if text is None else text, slider=slider, index=index, expand=expand)
    help_btn(row, key)
    return row


def section(layout, ui, idname, key, closed=False):
    """Sous-section repliable avec titre, icone, bouton d'aide et illustration."""
    h = HELP[key]
    header, body = layout.panel('bh_' + idname, default_closed=closed)
    header.label(text=h['t'], **icon_kw(h.get('ico')))
    help_btn(header, key)
    if body is not None and ui.show_images and h.get('img') and IMG(h['img']):
        body.template_icon(icon_value=IMG(h['img']), scale=ui.img_scale)
    return body


def reset_row(lay, section_id):
    lay.separator()
    row = lay.row(); row.alignment = 'RIGHT'
    row.operator("bh.reset", text="Réinitialiser l'onglet", icon='LOOP_BACK').section = section_id


def anim_note(col, rig, name):
    if is_animated(rig, name):
        r = col.row(); r.scale_y = .8
        r.label(text="Animé par le mode (suit la timeline)", icon='DECORATE_ANIMATE')


def draw_anim(lay, context, rig, ui):
    sc = context.scene; mode = rig.get('anim_mode', 'LOOP')
    b = section(lay, ui, 'mode', 'sec_mode')
    if b:
        grid = b.grid_flow(row_major=True, columns=2, even_columns=True, align=True)
        for m in ('LOOP', 'STARTUP', 'SHUTDOWN', 'PARKED'):
            h = HELP['mode_' + m]
            op = grid.operator("bh.anim_mode", text=h['t'], depress=mode == m, **icon_kw(h['ico']))
            op.mode = m
        col = b.column(align=True); col.active = mode in ('STARTUP', 'SHUTDOWN')
        prop_row(col, rig, 'bh_ramp', 'ramp_frames')
    b = section(lay, ui, 'loop', 'sec_loop')
    if b:
        col = b.column(align=True)
        prop_row(col, rig, 'bh_start', 'loop_start')
        prop_row(col, rig, 'bh_frames', 'loop_frames')
        main, tail, sec = loop_turns(rig, sc)
        box = b.box(); c = box.column(align=True); c.scale_y = .85
        if sec > 0:
            c.label(text=f"{fr(sec)} s · {main} tours entiers", icon='INFO')
            c.label(text=f"Queue : {tail} tours", icon='BLANK1')
            c.label(text=f"Régime obtenu : {fr(main * 60 / sec)} tr/min", icon='BLANK1')
        c.label(text=f"Images {sc.frame_start} à {sc.frame_end}", icon='BLANK1')
    b = section(lay, ui, 'rotors', 'sec_rotors')
    if b:
        col = b.column(align=True)
        r = col.row(align=True); r.scale_y = 1.3
        real = abs(rig['rpm'] - NR_RPM) < .05 and abs(rig['tail_ratio'] - TAIL_REAL_RPM / NR_RPM) < .02
        r.operator("bh.real_rpm", text="Régime réel UH-60 (258 tr/min)", icon='CHECKMARK' if real else 'FORCE_VORTEX', depress=real)
        help_btn(r, 'rpm_real')
        col = b.column(align=True)
        prop_row(col, rig, 'bh_rpm', 'rpm', text="Régime (tr/min)")
        prop_row(col, rig, 'bh_nr', 'nr', text="Régime Nr")
        prop_row(col, rig, 'bh_ratio', 'tail_ratio')
        draw_rotor_info(b, context, rig)
        for p, k in (('bh_rotor_dir', 'rotor_dir'), ('bh_tail_dir', 'tail_dir')):
            r = b.row(align=True)
            r.label(text=HELP[k]['t'], icon=HELP[k]['ico'])
            r.prop(rig, p, expand=True)
            help_btn(r, k)
    reset_row(lay, 'ANIM')


def fr(x, nd=1):
    """Nombre a la francaise : virgule decimale, espace pour les milliers."""
    t = f"{x:,.{nd}f}".replace(',', ' ').replace('.', ',')
    return t


def draw_rotor_info(lay, context, rig):
    """Bloc de lecture : a quoi correspond le regime choisi."""
    i = rotor_info(rig, context.scene)
    box = lay.box(); c = box.column(align=True); c.scale_y = .85
    r = c.row(); r.label(text="Ce que donne ce régime", icon='INFO'); help_btn(r, 'rotor_info')
    c.label(text=f"Principal : {fr(i['target'])} tr/min", icon_value=ICON('rotor'))
    c.label(text=f"= {fr(i['pct'], 0)} % Nr (réel : 258)", icon='BLANK1')
    c.label(text=f"{fr(i['rps'], 2)} tours/s · {fr(i['deg'])}°/image", icon='BLANK1')
    c.label(text=f"Queue : {fr(i['tail'], 0)} tr/min", icon='BLANK1')
    c.label(text=f"Bout de pale : {fr(i['tip'], 0)} m/s", icon='BLANK1')
    c.label(text=f"soit Mach {fr(i['mach'], 2)}", icon='BLANK1')
    if i['mode'] == 'LOOP' and abs(i['loop_rpm'] - rig['rpm']) > .05:
        c.label(text=f"arrondi boucle (demandé {fr(rig['rpm'])})", icon='BLANK1')
    w = c.column(align=True); w.active = False
    look = i['look'].replace('.', ',').replace(' (effet stroboscopique)', '')
    w.label(text="À l'écran : " + look, icon='HIDE_OFF')
    c.separator()
    c.label(text=f"Image {context.scene.frame_current} : {fr(i['now'], 0)} tr/min", icon='TIME')
    c.label(text=f"= {fr(i['now_pct'], 0)} % Nr", icon='BLANK1')
    lay.prop(context.window_manager.bh_ui, 'show_hud', icon='OVERLAY')


def draw_pales(lay, context, rig, ui):
    b = section(lay, ui, 'spool', 'sec_spool')
    if b:
        prop_row(b.column(), rig, '["spool"]', 'spool', slider=True)
        anim_note(b, rig, 'spool')
    b = section(lay, ui, 'flex', 'sec_flex')
    if b:
        col = b.column(align=True)
        prop_row(col, rig, '["droop_rest"]', 'droop_rest')
        prop_row(col, rig, '["droop_flight"]', 'droop_flight')
    b = section(lay, ui, 'angles', 'sec_angles')
    if b:
        col = b.column(align=True)
        for k in ('coning', 'collective', 'blade_wobble'):
            prop_row(col, rig, f'["{k}"]', k, text=HELP[k]['t'] + " (°)")
    b = section(lay, ui, 'disc', 'sec_disc', closed=True)
    if b:
        pb = rig.pose.bones.get('CTRL_Disque')
        if pb is None:
            b.label(text="Os CTRL_Disque introuvable", icon='ERROR')
        else:
            col = b.column(align=True)
            prop_row(col, pb, 'rotation_euler', 'disc_x', index=0)
            prop_row(col, pb, 'rotation_euler', 'disc_z', index=2)
            r = b.row(align=True)
            r.operator("bh.disc_flat", icon='LOOP_BACK')
            r.operator("bh.select_bone", text="Sélectionner l'os", icon='BONE_DATA').bone = 'CTRL_Disque'
    reset_row(lay, 'PALES')


def draw_vol(lay, context, rig, ui):
    b = section(lay, ui, 'hover', 'sec_hover')
    if b:
        col = b.column(align=True)
        prop_row(col, rig, '["hover_on"]', 'hover_on', slider=True)
        prop_row(col, rig, '["hover_height"]', 'hover_height')
        anim_note(b, rig, 'hover_on')
    b = section(lay, ui, 'moves', 'sec_moves')
    if b:
        col = b.column(align=True)
        prop_row(col, rig, '["hover_z"]', 'hover_z')
        prop_row(col, rig, '["hover_xy"]', 'hover_xy')
        col = b.column(align=True)
        prop_row(col, rig, '["hover_tilt"]', 'hover_tilt', text="Roulis / tangage (°)")
        prop_row(col, rig, '["hover_yaw"]', 'hover_yaw', text="Lacet (°)")
    b = section(lay, ui, 'trajet', 'sec_trajet', closed=True)
    if b:
        wrap(b.column(align=True), HELP['sec_trajet']['long'], text_width(context))
        r = b.row(align=True)
        r.operator("bh.select_bone", text="CTRL_Main", icon='OBJECT_ORIGIN').bone = 'CTRL_Main'
        r.operator("bh.select_bone", text="root", icon='PIVOT_CURSOR').bone = 'root'
    reset_row(lay, 'VOL')


def draw_leds(lay, context, rig, ui):
    b = section(lay, ui, 'leds_gen', 'sec_leds_gen')
    if b:
        col = b.column(align=True)
        prop_row(col, rig, '["leds_on"]', 'leds_on', slider=True)
        prop_row(col, rig, '["leds_blink"]', 'leds_blink', slider=True)
        b.label(text="Préréglages :")
        grid = b.grid_flow(row_major=True, columns=2, even_columns=True, align=True)
        for p in ('AVIATION', 'RED', 'WHITE', 'SYNC'):
            h = HELP['preset_' + p]
            grid.operator("bh.led_preset", text=h['t'], **icon_kw(h['ico'])).preset = p
    b = section(lay, ui, 'leds_list', 'sec_leds_list')
    if b:
        for i, name in enumerate(led_ids(rig), 1):
            p = f'led_{i:02d}_'; mode = int(rig.get(p + 'mode', 0))
            header, body = b.panel(f'bh_led_{i}', default_closed=i != 1)
            row = header.row(align=True)
            row.label(text=f"{i}. {LED_LABEL.get(name, name.replace('_', ' '))}", icon_value=ICON(f'led_mode_{mode}'))
            sw = row.row(); sw.ui_units_x = 2.2; sw.prop(rig, f'["{p}color"]', text="")
            if body is None:
                continue
            if ui.show_images:
                body.template_icon(icon_value=IMG(f'led_mode_{mode}'), scale=max(4, ui.img_scale - 3))
            col = body.column(align=True)
            prop_row(col, rig, f'["{p}color"]', 'led_color')
            r = col.row(align=True)
            r.label(text="", icon_value=ICON(f'led_mode_{mode}'))
            op = r.operator_menu_enum("bh.led_mode", "mode", text=LED_MODE_NAMES[mode]); op.led = i
            help_btn(r, 'led_mode')
            col = body.column(align=True)
            prop_row(col, rig, f'["{p}cycles"]', 'led_cycles')
            prop_row(col, rig, f'["{p}phase"]', 'led_phase', slider=True)
            col = body.column(align=True)
            prop_row(col, rig, f'["{p}glow"]', 'led_glow')
            prop_row(col, rig, f'["{p}watts"]', 'led_watts', text="Lumière (W)")
            body.operator("bh.select_led", text="Sélectionner la lumière", icon='RESTRICT_SELECT_OFF').led = i
    reset_row(lay, 'LEDS')


def draw_door_row(col, rig, d):
    o, now, full = portes.door_state(rig, d)
    prop_row(col, rig, '["%s"]' % d['prop'], d['prop'], slider=True)
    r = col.row(); r.active = False; r.scale_y = .75
    if d['kind'] == 'HINGE':
        r.label(text=f"{fr(now, 0)}° sur {fr(full, 0)}°" + ("  · animée" if is_animated(rig, d['prop']) else ""), icon='BLANK1')
    else:
        r.label(text=(f"{fr(now, 2)} m sur {fr(full, 2)} m" if o > portes.POP else ("sortie du cadre" if o > 0 else "fermée"))
                + ("  · animée" if is_animated(rig, d['prop']) else ""), icon='BLANK1')


def draw_portes(lay, context, rig, ui):
    if not portes.has_doors(rig):
        box = lay.box(); c = box.column(align=True)
        c.label(text="Ce rig n'a pas encore de portes animables", icon='INFO')
        wrap(c, "Rig fait avec la version 1.0 ou 1.1 : les portes forment un seul objet par type. "
                "Un clic les sépare et crée charnières et glissières, sans les déplacer.", text_width(context))
        ok, why = portes.can_install(rig)
        r = box.row(); r.scale_y = 1.5; r.enabled = ok
        r.operator("bh.doors_install", icon_value=ICON('door'))
        if not ok:
            box.label(text=why, icon='ERROR')
        c = lay.column(align=True); c.active = False
        wrap(c, "Ou ajoute le modèle 1.2 complet : onglet Aide › Modèle UH-60.", text_width(context))
        return
    b = section(lay, ui, 'doors_all', 'sec_doors_all')
    if b:
        r = b.row(align=True)
        r.prop(ui, 'door_which', text="")
        help_btn(r, 'door_which')
        r = b.row(align=True); r.scale_y = 1.3
        op = r.operator("bh.doors_set", text="Ouvrir", icon_value=ICON('door_open')); op.value = 1.; op.which = ui.door_which
        op = r.operator("bh.doors_set", text="Fermer", icon_value=ICON('door')); op.value = 0.; op.which = ui.door_which
        col = b.column(align=True)
        prop_row(col, ui, 'door_frames', 'door_frames', text=f"Durée ({fr(ui.door_frames / (context.scene.render.fps / context.scene.render.fps_base), 1)} s)")
        r = col.row(align=True)
        r.label(text="", icon_value=ICON('door_anim'))
        op = r.operator("bh.doors_anim", text="Ouverture"); op.open = True; op.which = ui.door_which; op.frames = ui.door_frames
        op = r.operator("bh.doors_anim", text="Fermeture"); op.open = False; op.which = ui.door_which; op.frames = ui.door_frames
        help_btn(r, 'door_anim')
        r = b.row(align=True)
        r.operator("bh.doors_key", text="Clé", icon='DECORATE_KEYFRAME')
        r.operator("bh.doors_clear", text="Effacer", icon='X')
    b = section(lay, ui, 'doors_cockpit', 'sec_doors_cockpit')
    if b:
        col = b.column(align=True)
        for d in portes.DOORS:
            if d['kind'] == 'HINGE':
                draw_door_row(col, rig, d)
        prop_row(b.column(align=True), rig, '["door_cockpit_angle"]', 'door_cockpit_angle', text="Angle d'ouverture (°)")
    b = section(lay, ui, 'doors_cabin', 'sec_doors_cabin')
    if b:
        col = b.column(align=True)
        for d in portes.DOORS:
            if d['kind'] == 'SLIDE':
                draw_door_row(col, rig, d)
        col = b.column(align=True)
        prop_row(col, rig, '["door_cabin_travel"]', 'door_cabin_travel')
        prop_row(col, rig, '["door_cabin_out"]', 'door_cabin_out')
    reset_row(lay, 'PORTES')


def draw_model(lay, context, ui):
    """Etat du modele telecharge : telechargement, progression, ajout a la scene."""
    job = modele.JOB; info = modele.local_model()
    r = lay.row(); r.label(text=HELP['sec_model']['t'], icon_value=ICON('download')); help_btn(r, 'sec_model')
    if job.busy:
        c = lay.column(align=True)
        txt = job.msg
        if job.state == 'DOWNLOAD' and job.total:
            sp = job.speed()
            txt = f"{fr(job.done / 1048576, 0)} / {fr(job.total / 1048576, 0)} Mo" + (f" · {fr(sp / 1048576, 1)} Mo/s" if sp else "")
        if hasattr(c, 'progress'):
            c.progress(factor=job.factor, type='BAR', text=txt)
        else:
            c.label(text=f"{txt} ({job.factor * 100:.0f} %)", icon='SORTTIME')
        c.operator("bh.model_cancel", icon='CANCEL')
        return
    if job.state in ('ERROR', 'CANCELLED'):
        c = lay.column(align=True); c.alert = job.state == 'ERROR'
        wrap(c, job.msg, text_width(context))
    if info is not None:
        lay.label(text=f"Modèle {info.get('version', '?')} installé", icon='CHECKMARK')
        r = lay.row(); r.scale_y = 1.5
        r.operator("bh.model_import", icon='IMPORT').studio = ui.model_studio
        lay.prop(ui, 'model_studio', icon='OUTLINER_OB_CAMERA')
        r = lay.row(align=True)
        r.operator("bh.model_download", text="Mettre à jour", icon='FILE_REFRESH')
        r.operator("bh.model_folder", text="Dossier", icon='FILEBROWSER')
        return
    c = lay.column(align=True)
    wrap(c, f"Le plugin a besoin du modèle 3D du UH-60 ({modele.SIZE_HINT}). Il se télécharge une seule fois.", text_width(context))
    if not getattr(bpy.app, 'online_access', True):
        c = lay.column(align=True); c.alert = True
        wrap(c, aide.tooltip('online'), text_width(context))
    r = lay.row(); r.scale_y = 1.5
    r.operator("bh.model_download", icon_value=ICON('download'))
    lay.operator("bh.model_file", icon='FILE_FOLDER')


def rig_health(rig, scene):
    n = bad = 0
    ids = [rig] + [m.node_tree for m in bpy.data.materials if m.node_tree and m.name.startswith('LED_')]
    ids += [o.data for o in scene.objects if o.type == 'LIGHT' and o.name.startswith('LED_')]
    for idb in ids:
        ad = getattr(idb, 'animation_data', None)
        for f in (ad.drivers if ad else ()):
            n += 1; bad += (not f.driver.is_valid) or f.mute
    return n, bad


def draw_aide(lay, context, rig, ui):
    b = section(lay, ui, 'start', 'sec_start')
    if b:
        col = b.column(align=True)
        wrap(col, HELP['sec_start']['long'], text_width(context))
    b = section(lay, ui, 'ctrl', 'sec_ctrl')
    if b:
        col = b.column(align=True)
        for bone in ('root', 'CTRL_Main', 'CTRL_Disque', 'CTRL_Rotor', 'CTRL_Queue'):
            h = HELP['bone_' + bone]
            r = col.row(align=True)
            r.operator("bh.select_bone", text=bone, **icon_kw(h['ico'])).bone = bone
            help_btn(r, 'bone_' + bone)
    b = section(lay, ui, 'model', 'sec_model', closed=True)
    if b:
        draw_model(b, context, ui)
    b = section(lay, ui, 'opts', 'show_images')
    if b:
        r = b.row(align=True)
        r.prop(ui, 'show_images', icon='IMAGE_DATA')
        s = r.row(align=True); s.active = ui.show_images; s.prop(ui, 'img_scale')
    b = section(lay, ui, 'doc', 'open_doc')
    if b:
        r = b.row(); r.scale_y = 1.5
        r.operator("bh.open_doc", text="Ouvrir la documentation", icon_value=ICON('doc'))
        n, bad = rig_health(rig, context.scene)
        b.label(text=f"État du rig : {n} drivers, {'tous valides' if bad == 0 else str(bad) + ' en défaut'}",
                icon='CHECKMARK' if bad == 0 else 'ERROR')
        # extension (Blender 4.2+) : bl_info n'existe plus une fois le module chargé -> version lue dans le manifeste
        v = next((l.split('=')[1].strip().strip('"') for l in open(os.path.join(os.path.dirname(__file__), 'blender_manifest.toml'),
                  encoding='utf8') if l.startswith('version')), '?')
        b.label(text=f"Black Hawk Rig {v} · rig : {rig.name}", icon='BLANK1')
        b.label(text=("Portes animables installées" if portes.has_doors(rig) else "Portes : non installées (onglet Portes)"),
                icon='CHECKMARK' if portes.has_doors(rig) else 'INFO')
        r = b.row(); r.alert = True
        r.operator("bh.reset", text="Tout réinitialiser", icon='LOOP_BACK').section = 'ALL'


DRAW = {'ANIM': draw_anim, 'PALES': draw_pales, 'VOL': draw_vol, 'PORTES': draw_portes, 'LEDS': draw_leds, 'AIDE': draw_aide}


class BH_PT_Rig(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Black Hawk"
    bl_label = "Black Hawk Rig"
    bl_order = 0

    def draw_header(self, context):
        self.layout.label(text="", icon_value=ICON('heli'))

    def draw(self, context):
        lay = self.layout; rig = find_rig(context); ui = context.window_manager.bh_ui
        maj.draw_status(lay, compact=True)
        if rig is None:
            box = lay.box()
            box.label(text="Aucun UH-60 dans la scène", icon='INFO')
            draw_model(box, context, ui)
            lay.operator("bh.open_doc", icon_value=ICON('doc'))
            return
        # onglets en icones (lisibles meme dans une barre etroite), titre et resume en dessous
        row = lay.row(align=True); row.scale_y = 1.6
        row.prop(ui, 'tab', expand=True, icon_only=True)
        h = HELP['tab_' + ui.tab]
        r = lay.row(align=True)
        r.label(text=h['t'], **icon_kw(h['ico']))
        r.prop(ui, 'show_images', text="", icon='IMAGE_DATA')
        help_btn(r, 'sec_start')
        c = lay.column(align=True); c.active = False; c.scale_y = .8
        wrap(c, h['court'], text_width(context))
        DRAW[ui.tab](lay, context, rig, ui)


# ------------------------------------------------------------------ enregistrement
_HUD = None


def draw_hud():
    """Texte en bas a gauche de la vue 3D : regime instantane des rotors."""
    try:
        ctx = bpy.context
        if not ctx.window_manager.bh_ui.show_hud:
            return
        rig = find_rig(ctx)
        if rig is None:
            return
        import blf
        i = rotor_info(rig, ctx.scene)
        s = ctx.preferences.system.ui_scale or 1.
        lines = [(f"UH-60  rotor {fr(i['now'], 0)} tr/min  ({fr(i['now_pct'], 0)} % Nr)", (1., .72, .2, 1.)),
                 (f"queue {fr(i['now_tail'], 0)} tr/min  ·  bout de pale {fr(2 * math.pi * i['radius'] * i['now'] / 60, 0)} m/s", (.85, .87, .9, 1.))]
        fid = 0; y = 62 * s
        blf.enable(fid, blf.SHADOW); blf.shadow(fid, 3, 0, 0, 0, .8)
        for txt, col in lines:
            blf.size(fid, 13 * s); blf.color(fid, *col)
            blf.position(fid, 20 * s, y, 0); blf.draw(fid, txt); y -= 18 * s
        blf.disable(fid, blf.SHADOW)
    except Exception:
        pass


@persistent
def _on_load(_):
    apply_meta_all()


def _first_meta():
    try:
        apply_meta_all()
    except Exception as e:
        print('BH meta', e)
    return None


CLASSES = (BH_UI, BH_OT_Anim, BH_OT_RealRpm, BH_OT_LedMode, BH_OT_LedPreset, BH_OT_Help, BH_OT_OpenDoc, BH_OT_SelectBone, BH_OT_SelectLed,
           BH_OT_DiscFlat, BH_OT_Reset, BH_OT_DoorsSet, BH_OT_DoorsAnim, BH_OT_DoorsKey, BH_OT_DoorsClear, BH_OT_DoorsInstall,
           BH_OT_ModelDownload, BH_OT_ModelCancel, BH_OT_ModelImport, BH_OT_ModelFile, BH_OT_ModelFolder, BH_Prefs, BH_PT_Rig)


def register():
    load_previews()
    build_items()
    register_props()
    for c in CLASSES:
        bpy.utils.register_class(c)
    bpy.types.WindowManager.bh_ui = PointerProperty(type=BH_UI)
    if _on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_on_load)
    bpy.app.timers.register(_first_meta, first_interval=.2)
    global _HUD
    _HUD = bpy.types.SpaceView3D.draw_handler_add(draw_hud, (), 'WINDOW', 'POST_PIXEL')
    maj.register()


def unregister():
    global PCOLL, _HUD
    modele.JOB.cancel = True
    maj.unregister()
    if _HUD is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_HUD, 'WINDOW'); _HUD = None
    if _on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load)
    del bpy.types.WindowManager.bh_ui
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
    unregister_props()
    if PCOLL is not None:
        bpy.utils.previews.remove(PCOLL); PCOLL = None


if __name__ == "__main__":
    register()
