"""Modele 3D du UH-60 : telechargement (catalogue JSON + archive zip verifiee SHA-256), installation locale, import dans la scene.
Le telechargement tourne dans un fil separe ; l'interface lit l'etat via JOB et se redessine avec un timer."""
import hashlib, json, os, shutil, tempfile, threading, time, urllib.request, zipfile
import bpy

# catalogue publie avec chaque version du modele (url, taille, empreinte SHA-256)
CATALOG_URL = "https://github.com/lburdier/bh-heli-rig/releases/latest/download/modele.json"
MODEL_COLL = "UH-60 Black Hawk"
STUDIO_COLL = "UH-60 Studio"
BLEND_NAME = "UH60_BlackHawk.blend"
UA = "BlackHawkRig-Blender-addon"
SIZE_HINT = "environ 190 Mo"  # mis a jour a chaque publication du modele


def addon_prefs():
    pkg = __package__
    a = bpy.context.preferences.addons.get(pkg) if pkg else None
    return a.preferences if a else None


def catalog_url():
    p = addon_prefs()
    return (getattr(p, 'catalog_url', '') or CATALOG_URL).strip()


def store_dir(create=True):
    """Dossier du modele telecharge : choisi dans les preferences, sinon dossier utilisateur de l'extension."""
    p = addon_prefs()
    d = bpy.path.abspath(getattr(p, 'store_dir', '') or '') if p else ''
    if not d:
        try:
            d = bpy.utils.extension_path_user(__package__, path="modele", create=create)
        except Exception:
            d = os.path.join(bpy.utils.user_resource('DATAFILES', path="bh_heli_rig", create=create), "modele")
    if create:
        os.makedirs(d, exist_ok=True)
    return d


def local_model(root=None):
    """Modele installe : dict(version, dir, blend, size) ou None."""
    root = root or store_dir(create=False)
    try:
        info = json.load(open(os.path.join(root, 'installe.json'), encoding='utf8'))
    except Exception:
        return None
    blend = os.path.join(root, info.get('dir', ''), BLEND_NAME)
    if not os.path.isfile(blend):
        return None
    info['blend'] = blend; info['path'] = os.path.dirname(blend)
    return info


# ------------------------------------------------------------------ telechargement
class Job:
    def __init__(self):
        self.reset()

    def reset(self):
        self.state = 'IDLE'      # IDLE, CATALOG, DOWNLOAD, VERIFY, EXTRACT, DONE, ERROR, CANCELLED
        self.done = 0; self.total = 0; self.msg = ""; self.version = ""; self.cancel = False
        self.t0 = time.time(); self.thread = None

    @property
    def busy(self):
        return self.state in ('CATALOG', 'DOWNLOAD', 'VERIFY', 'EXTRACT')

    @property
    def factor(self):
        return self.done / self.total if self.total else 0.

    def speed(self):
        dt = time.time() - self.t0
        return self.done / dt if dt > .5 else 0.


JOB = Job()


class Cancelled(Exception):
    pass


def _open(url, timeout=30):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=timeout)


def read_catalog(url):
    with _open(url, 20) as r:
        cat = json.loads(r.read().decode('utf8'))
    for k in ('version', 'url', 'sha256', 'size'):
        if k not in cat:
            raise ValueError(f"catalogue incomplet ({k} manquant)")
    # url relative : meme dossier que le catalogue
    if '://' not in cat['url']:
        cat['url'] = url.rsplit('/', 1)[0] + '/' + cat['url']
    return cat


def _safe_extract(zf, dest):
    root = os.path.realpath(dest)
    for m in zf.infolist():
        target = os.path.realpath(os.path.join(dest, m.filename))
        if not (target == root or target.startswith(root + os.sep)):
            raise ValueError("archive refusée : chemin hors du dossier (" + m.filename + ")")
    zf.extractall(dest)


def install_zip(zpath, root, version=None):
    """Decompresse l'archive du modele dans root/UH60_BlackHawk_<version> et memorise la version installee."""
    with zipfile.ZipFile(zpath) as zf:
        names = zf.namelist()
        blend = next((n for n in names if n.endswith(BLEND_NAME)), None)
        if blend is None:
            raise ValueError("cette archive ne contient pas " + BLEND_NAME)
        if version is None:
            try:
                version = json.loads(zf.read('modele.json').decode('utf8'))['version']
            except Exception:
                version = 'local'
        name = f"UH60_BlackHawk_{version}"
        tmp = os.path.join(root, name + '.tmp')
        shutil.rmtree(tmp, ignore_errors=True)
        _safe_extract(zf, tmp)
    final = os.path.join(root, name)
    shutil.rmtree(final, ignore_errors=True)
    os.replace(tmp, final)
    sub = os.path.dirname(blend)
    info = dict(version=version, dir=os.path.join(name, sub) if sub else name, installed=time.strftime('%Y-%m-%d %H:%M'))
    json.dump(info, open(os.path.join(root, 'installe.json'), 'w', encoding='utf8'), indent=1)
    return info


def download(url, root, job=None, chunk=1 << 20):
    """Telecharge et installe le modele (bloquant). Utilisee par le fil de fond et par les tests."""
    job = job or Job()
    job.state = 'CATALOG'; job.msg = "Lecture du catalogue"
    cat = read_catalog(url)
    job.version = cat['version']; job.total = int(cat['size']); job.done = 0; job.t0 = time.time()
    job.state = 'DOWNLOAD'; job.msg = f"Téléchargement du modèle {cat['version']}"
    fd, part = tempfile.mkstemp(suffix='.zip.part', dir=root); os.close(fd)
    h = hashlib.sha256()
    try:
        with _open(cat['url'], 60) as r, open(part, 'wb') as f:
            while True:
                if job.cancel:
                    raise Cancelled()
                b = r.read(chunk)
                if not b:
                    break
                f.write(b); h.update(b); job.done += len(b)
        job.state = 'VERIFY'; job.msg = "Vérification de l'archive"
        if job.done != job.total:
            raise ValueError(f"taille inattendue ({job.done} octets au lieu de {job.total})")
        if h.hexdigest().lower() != cat['sha256'].lower():
            raise ValueError("empreinte SHA-256 différente : archive corrompue ou modifiée")
        job.state = 'EXTRACT'; job.msg = "Installation"
        info = install_zip(part, root, cat['version'])
    finally:
        if os.path.exists(part):
            os.remove(part)
    job.state = 'DONE'; job.msg = f"Modèle {cat['version']} installé"
    return info


def _worker(url, root):
    try:
        download(url, root, JOB)
    except Cancelled:
        JOB.state = 'CANCELLED'; JOB.msg = "Téléchargement annulé"
    except Exception as e:
        JOB.state = 'ERROR'; JOB.msg = "Échec : " + explain(e)


def explain(e):
    """Message d'erreur reseau lisible."""
    import urllib.error, socket
    if isinstance(e, urllib.error.HTTPError):
        if e.code == 404:
            return "modèle introuvable sur la page de publication (erreur 404). Vérifier l'adresse du catalogue dans les préférences."
        return f"le serveur a répondu {e.code} ({e.reason})"
    if isinstance(e, urllib.error.URLError):
        return f"pas de connexion au serveur ({e.reason}). Vérifier Internet ou installer depuis un fichier."
    if isinstance(e, (socket.timeout, TimeoutError)):
        return "le serveur ne répond pas (délai dépassé)"
    if isinstance(e, OSError) and getattr(e, 'errno', None) == 28:
        return "disque plein"
    return str(e)


def start_download():
    if JOB.busy:
        return False
    JOB.reset(); JOB.state = 'CATALOG'
    JOB.thread = threading.Thread(target=_worker, args=(catalog_url(), store_dir()), daemon=True)
    JOB.thread.start()
    bpy.app.timers.register(_tick, first_interval=.25)
    return True


def _redraw():
    wm = getattr(bpy.context, 'window_manager', None)
    for w in (wm.windows if wm else ()):
        for a in w.screen.areas:
            if a.type in ('VIEW_3D', 'PREFERENCES'):
                a.tag_redraw()


def _tick():
    _redraw()
    return .25 if JOB.busy else None


# ------------------------------------------------------------------ import dans la scene
def relink_images(images, folder):
    """Rattache les textures de l'archive (dossier textures/ du modele) aux images ajoutees."""
    n = 0
    tex = os.path.join(folder, 'textures')
    for img in images:
        if img.source != 'FILE' or img.packed_file is not None:
            continue
        f = os.path.join(tex, os.path.basename(bpy.path.abspath(img.filepath)))
        if os.path.isfile(f):
            img.filepath = f; n += 1
            try:
                img.reload()
            except Exception:
                pass
    return n


def import_model(context, info, studio=False, at_cursor=True):
    """Ajoute le modele (collection UH-60 Black Hawk, et le studio en option) a la scene courante. Retourne le rig."""
    blend = info['blend']
    imgs0 = set(bpy.data.images); objs0 = set(bpy.data.objects)
    want = [MODEL_COLL] + ([STUDIO_COLL] if studio else [])
    with bpy.data.libraries.load(blend, link=False) as (src, dst):
        missing = [c for c in want if c not in src.collections]
        if MODEL_COLL in missing:
            raise ValueError(f"collection « {MODEL_COLL} » absente de {BLEND_NAME}")
        dst.collections = [c for c in want if c in src.collections]
        if studio and 'BH_studio' in src.worlds:
            dst.worlds = ['BH_studio']
    sc = context.scene
    for c in dst.collections:
        if c is not None:
            sc.collection.children.link(c)
    if studio:
        w = next((w for w in getattr(dst, 'worlds', []) if w is not None), None)
        if w is not None:
            sc.world = w
        cam = next((o for o in set(bpy.data.objects) - objs0 if o.type == 'CAMERA' and o.name.startswith('CAM_hero')), None)
        if cam is not None:
            sc.camera = cam
    relink_images([i for i in bpy.data.images if i not in imgs0], info['path'])
    rig = next((o for o in set(bpy.data.objects) - objs0 if o.get('bh_rig') and o.type == 'ARMATURE'), None)
    if rig is not None:
        if at_cursor and rig.parent is None:
            rig.location = sc.cursor.location
        for o in context.view_layer.objects:
            o.select_set(False)
        if rig.name in context.view_layer.objects:
            rig.select_set(True); context.view_layer.objects.active = rig
    return rig
