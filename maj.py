# SPDX-License-Identifier: GPL-3.0-or-later
"""Mises à jour automatiques depuis les releases GitHub de l'extension.

* Au démarrage de Blender (au plus une fois toutes les 12 h), un fil de fond demande à l'API GitHub
  la dernière release du dépôt.
* Si elle est plus récente que la version installée, son zip d'extension (<id>-X.Y.Z.zip) est téléchargé,
  vérifié (taille + SHA-256 fourni par GitHub) puis installé par l'installateur d'extensions de Blender :
  tout seul (réglage par défaut, jamais pendant un pilotage ou un téléchargement) ou d'un clic.
* Respecte « Autoriser l'accès en ligne » de Blender ; n'envoie qu'une requête GET anonyme.
Publier une version = créer une release GitHub vX.Y.Z avec le zip de l'extension en pièce jointe
(script outils/publier.py du dépôt).

Fichier commun aux rigs véhicules (Black Hawk, Jeep Commander, Ducati Monster) : la seule partie propre
à chaque add-on est l'appel à configure() dans __init__.py.
"""
import hashlib
import json
import os
import tempfile
import threading
import time
import urllib.error
import urllib.request

import bpy

CFG = {"id": "", "repo": "", "name": "", "prefix": "", "busy": None}
_PERIOD = 12 * 3600

state = {"status": "idle", "latest": "", "asset": None, "page": "", "notes": "", "error": "", "checked": 0.0,
         "auto": False, "download": ""}
_lock = threading.Lock()


def configure(pkg_id, repo, name, prefix, busy=None):
    """pkg_id = id du manifeste, repo = 'proprietaire/depot', prefix = préfixe des opérateurs (bh, jc...),
    busy() -> texte non vide quand il ne faut pas recharger l'add-on (pilotage, téléchargement...)."""
    CFG.update(id=pkg_id, repo=repo, name=name, prefix=prefix, busy=busy)


# ------------------------------------------------------------------------------------ outils
def _vtuple(text):
    out = []
    for part in str(text).lstrip("vV").split("."):
        num = ""
        for ch in part:
            if not ch.isdigit():
                break
            num += ch
        out.append(int(num or 0))
    while len(out) < 3:
        out.append(0)
    return tuple(out[:3])


_VERSION = None


def current_version():
    global _VERSION
    if _VERSION is None:
        try:
            import tomllib
            with open(os.path.join(os.path.dirname(__file__), "blender_manifest.toml"), "rb") as f:
                _VERSION = _vtuple(tomllib.load(f)["version"])
        except Exception:
            _VERSION = (0, 0, 0)
    return _VERSION


def current_version_str():
    return ".".join(str(x) for x in current_version())


def _prefs():
    try:
        return bpy.context.preferences.addons[__package__].preferences
    except Exception:
        return None


def repo_url():
    return "https://github.com/" + CFG["repo"]


def online_allowed():
    return bool(getattr(bpy.app, "online_access", True))


def install_kind():
    """('local' | 'remote' | 'legacy', module du dépôt d'extensions)."""
    parts = (__package__ or "").split(".")
    if len(parts) < 3 or parts[0] != "bl_ext":
        return "legacy", None
    module = parts[1]
    for r in bpy.context.preferences.extensions.repos:
        if r.module == module:
            return ("remote" if r.use_remote_url else "local"), module
    return "legacy", None


def _busy():
    fn = CFG.get("busy")
    try:
        return (fn() or "") if fn else ""
    except Exception:
        return ""


def _stamp_path():
    try:
        d = bpy.utils.extension_path_user(__package__, path="", create=True)
    except Exception:
        d = tempfile.gettempdir()
    return os.path.join(d, "maj_verification.json")


def _last_check():
    try:
        with open(_stamp_path(), encoding="utf8") as f:
            return float(json.load(f).get("t", 0.0))
    except Exception:
        return 0.0


def _save_check(t):
    try:
        with open(_stamp_path(), "w", encoding="utf8") as f:
            json.dump({"t": t, "latest": state.get("latest", "")}, f)
    except Exception:
        pass


def tag_redraw():
    try:
        for w in bpy.context.window_manager.windows:
            for a in w.screen.areas:
                if a.type in {'VIEW_3D', 'PREFERENCES'}:
                    a.tag_redraw()
    except Exception:
        pass


def _ensure_poll():
    if not bpy.app.timers.is_registered(_poll):
        bpy.app.timers.register(_poll, first_interval=0.5, persistent=True)


# ------------------------------------------------------------------------------------ vérification
def _fetch_latest(name):
    url = "https://api.github.com/repos/%s/releases/latest" % name
    req = urllib.request.Request(url, headers={"User-Agent": CFG["id"] + "-blender-updater",
                                               "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        rel = json.loads(resp.read(4 * 1024 * 1024).decode("utf-8"))
    pre = CFG["id"].lower() + "-"
    assets = [a for a in rel.get("assets", []) if a.get("name", "").lower().startswith(pre)
              and a.get("name", "").lower().endswith(".zip")]
    return dict(tag=rel.get("tag_name", ""), page=rel.get("html_url", ""), notes=(rel.get("body") or "")[:2000],
                asset=assets[0] if assets else None)


def _check_thread(name):
    try:
        rel = _fetch_latest(name)
        newer = _vtuple(rel["tag"]) > current_version() and current_version() != (0, 0, 0)
        with _lock:
            state.update(checked=time.time(), latest=rel["tag"].lstrip("vV"), page=rel["page"], notes=rel["notes"],
                         asset=rel["asset"], error="")
            if newer and rel["asset"] is None:
                state.update(status="error", error="la release %s n'a pas de zip d'extension" % rel["tag"])
            else:
                state["status"] = "available" if newer else "uptodate"
    except urllib.error.HTTPError as exc:
        with _lock:
            state.update(status="error", checked=time.time(),
                         error=("aucune version publiée" if exc.code == 404 else "GitHub : erreur HTTP %d" % exc.code))
    except Exception as exc:  # noqa: BLE001 (hors ligne, DNS, délai...)
        with _lock:
            state.update(status="error", error="pas de connexion à GitHub (%s)" % str(exc)[:120], checked=time.time())


def check(auto_install=False):
    """Lance une vérification en fond. Renvoie un message d'erreur pour l'interface, ou ''."""
    if state["status"] in ("checking", "downloading", "installing"):
        return ""
    if not online_allowed():
        state.update(status="offline")
        return "L'accès en ligne est désactivé dans les préférences de Blender (Système > Réseau)"
    state.update(status="checking", auto=auto_install, error="")
    threading.Thread(target=_check_thread, args=(CFG["repo"],), daemon=True, name=CFG["id"] + "-maj").start()
    _ensure_poll()
    return ""


def _poll():
    st = state["status"]
    if st in ("checking", "downloading"):
        return 0.5
    if st in ("available", "uptodate"):
        _save_check(state["checked"])
    tag_redraw()
    if st == "available" and state["auto"]:
        if _busy():
            return 5.0                                   # attendre la fin du pilotage / du téléchargement
        state["auto"] = False
        install()
        return 0.5 if state["status"] == "downloading" else None
    if st == "downloaded":
        if _busy():
            return 5.0
        _install_downloaded()
    return None


# ------------------------------------------------------------------------------------ installation
def _download_thread(asset, version):
    try:
        req = urllib.request.Request(asset["browser_download_url"], headers={"User-Agent": CFG["id"] + "-blender-updater"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read(256 * 1024 * 1024)
        size = asset.get("size")
        if size and int(size) != len(data):
            raise ValueError("taille inattendue")
        digest = str(asset.get("digest") or "")
        if digest.startswith("sha256:") and hashlib.sha256(data).hexdigest() != digest[7:]:
            raise ValueError("empreinte SHA-256 différente")
        folder = tempfile.mkdtemp(prefix=CFG["id"] + "_maj_")
        path = os.path.join(folder, "%s-%s.zip" % (CFG["id"], version))
        with open(path, "wb") as fh:
            fh.write(data)
        with _lock:
            state.update(status="downloaded", download=path)
    except Exception as exc:  # noqa: BLE001
        with _lock:
            state.update(status="error", error="téléchargement : %s" % str(exc)[:140])


def install():
    """Installe la dernière release. Renvoie un message d'erreur pour l'interface, ou ''."""
    why = _busy()
    if why:
        return why
    asset = state.get("asset")
    if not asset or state["status"] not in ("available", "error"):
        return "Aucune mise à jour disponible"
    kind, _module = install_kind()
    if kind == "legacy":
        import webbrowser
        webbrowser.open(state.get("page") or repo_url())
        return "Add-on installé à l'ancienne : télécharge la nouvelle version sur la page qui vient de s'ouvrir"
    state["status"] = "downloading"
    threading.Thread(target=_download_thread, args=(asset, state.get("latest", "")), daemon=True,
                     name=CFG["id"] + "-maj-dl").start()
    _ensure_poll()
    return ""


def _call_op(op, **kw):
    wm = bpy.context.window_manager
    win = wm.windows[0] if wm and len(wm.windows) else None
    if win is not None:
        with bpy.context.temp_override(window=win):
            return op(**kw)
    return op(**kw)


def _env_key():
    return "MAJ_%s_DEPUIS" % CFG["id"].upper()


def _install_downloaded():
    # lancé par un timer, hors de tout opérateur de l'add-on : Blender recharge l'add-on pendant l'appel
    path = state.get("download")
    _kind, module = install_kind()
    state["status"] = "installing"
    try:
        os.environ[_env_key()] = "%s>%s" % (current_version_str(), state.get("latest", ""))
        res = _call_op(bpy.ops.extensions.package_install_files, filepath=path, repo=module,
                       enable_on_install=True, overwrite=True)
        if "FINISHED" not in res:
            raise RuntimeError("Blender a refusé le paquet (%s)" % ", ".join(sorted(res)))
        state["status"] = "installed"
    except Exception as exc:  # noqa: BLE001
        os.environ.pop(_env_key(), None)
        state.update(status="error", error=str(exc)[:160])
    tag_redraw()


def updated_from():
    """('1.2.2', '1.3.0') juste après une mise à jour automatique dans cette session de Blender."""
    val = os.environ.get(_env_key(), "")
    return tuple(val.split(">", 1)) if ">" in val else None


# ------------------------------------------------------------------------------------ interface
def draw_status(layout, compact=False):
    """État de la mise à jour. compact=True (panneau de la vue 3D) : rien quand tout est à jour."""
    st = state["status"]
    up = updated_from()
    pre = CFG["prefix"]
    if up and st not in ("available", "downloading", "downloaded", "installing"):
        layout.label(text="Mis à jour : %s → %s" % up, icon='CHECKMARK')
        if compact:
            return
    if st == "checking":
        layout.label(text="Recherche d'une mise à jour…", icon='SORTTIME')
    elif st == "available":
        box = layout.box() if compact else layout
        box.label(text="Nouvelle version %s disponible" % state["latest"], icon='INFO')
        row = box.row(align=True)
        row.operator(pre + ".maj_installer", icon='IMPORT')
        row.operator(pre + ".maj_page", text="", icon='URL')
        why = _busy()
        if why:
            box.label(text=why, icon='PAUSE')
    elif st in ("downloading", "downloaded", "installing"):
        layout.label(text="Installation de la version %s…" % state["latest"], icon='SORTTIME')
    elif st == "installed":
        layout.label(text="Version %s installée" % state["latest"], icon='CHECKMARK')
    elif compact:
        return
    elif st == "uptodate":
        layout.label(text="À jour (dernière version : %s)" % state["latest"], icon='CHECKMARK')
    elif st == "offline":
        layout.label(text="Accès en ligne désactivé dans Blender", icon='ERROR')
    elif st == "error":
        col = layout.column(align=True)
        col.alert = True
        col.label(text="Mise à jour : " + state["error"], icon='ERROR')


def draw_prefs(layout, prefs):
    """Boîte « Mises à jour » des préférences de l'add-on."""
    box = layout.box()
    row = box.row(align=True)
    row.label(text="%s %s" % (CFG["name"], current_version_str()), icon='PACKAGE')
    row.operator(CFG["prefix"] + ".maj_verifier", icon='FILE_REFRESH')
    row.operator(CFG["prefix"] + ".maj_page", text="", icon='URL')
    draw_status(box)
    box.prop(prefs, "maj_verifier")
    sub = box.column()
    sub.active = prefs.maj_verifier
    sub.prop(prefs, "maj_auto")
    if install_kind()[0] == "legacy":
        c = box.column(align=True)
        c.alert = True
        c.label(text="Installé comme ancien add-on : la mise à jour ouvrira la page de téléchargement.", icon='INFO')


def make_operators():
    pre = CFG["prefix"]

    class MAJ_OT_verifier(bpy.types.Operator):
        bl_idname = pre + ".maj_verifier"
        bl_label = "Rechercher une mise à jour"
        bl_description = "Demande à GitHub si une nouvelle version de l'add-on est publiée"

        def execute(self, context):
            err = check(auto_install=False)
            if err:
                self.report({'WARNING'}, err)
                return {'CANCELLED'}
            return {'FINISHED'}

    class MAJ_OT_installer(bpy.types.Operator):
        bl_idname = pre + ".maj_installer"
        bl_label = "Installer la mise à jour"
        bl_description = "Télécharge et installe la nouvelle version (l'add-on se recharge, la scène est conservée)"

        def execute(self, context):
            err = install()
            if err:
                self.report({'WARNING'}, err)
                return {'CANCELLED'}
            return {'FINISHED'}

    class MAJ_OT_page(bpy.types.Operator):
        bl_idname = pre + ".maj_page"
        bl_label = "Page GitHub"
        bl_description = "Ouvre la page des versions de l'add-on sur GitHub"

        def execute(self, context):
            bpy.ops.wm.url_open(url=state.get("page") or repo_url() + "/releases")
            return {'FINISHED'}

    for c in (MAJ_OT_verifier, MAJ_OT_installer, MAJ_OT_page):
        c.__name__ = "%s_OT_maj_%s" % (pre.upper(), c.__name__.rsplit("_", 1)[1])
    return (MAJ_OT_verifier, MAJ_OT_installer, MAJ_OT_page)


# ------------------------------------------------------------------------------------ démarrage
def _startup():
    p = _prefs()
    if p is None or not getattr(p, "maj_verifier", True) or not online_allowed():
        return None
    if time.time() - _last_check() < _PERIOD:
        return None
    check(auto_install=getattr(p, "maj_auto", True))
    return None


_OPS = ()


def register():
    global _OPS
    _OPS = make_operators()
    for c in _OPS:
        bpy.utils.register_class(c)
    if bpy.app.background or os.environ.get("RIGS_SANS_MAJ"):
        return
    # persistent : sinon le chargement du .blend passé en ligne de commande supprime le timer
    bpy.app.timers.register(_startup, first_interval=6.0, persistent=True)


def unregister():
    for fn in (_startup, _poll):
        if bpy.app.timers.is_registered(fn):
            bpy.app.timers.unregister(fn)
    for c in reversed(_OPS):
        try:
            bpy.utils.unregister_class(c)
        except Exception:
            pass
