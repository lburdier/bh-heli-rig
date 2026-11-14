"""Test d'installation + mise à jour automatique d'un rig, dans un profil Blender isolé.
BLENDER_USER_RESOURCES=<dossier vide> blender -b --factory-startup -P test_maj.py -- <zip> <id> <prefixe_ops> [modele.zip]
1. installe le zip (comme un glisser-déposer), vérifie l'activation, les opérateurs et le dessin des préférences ;
2. fabrique une version 9.9.9 du même zip, la sert en local et déroule le chemin de mise à jour de maj.py
   (vérification -> téléchargement -> contrôle taille + SHA-256 -> installation par Blender) ;
3. vérifie que la 9.9.9 est installée, activée et rechargée ;
4. (option) installe le modèle depuis son zip et l'ajoute à la scène."""
import hashlib, http.server, importlib, os, re, sys, tempfile, threading, zipfile
import bpy

ZIP, PID, PRE = sys.argv[sys.argv.index('--') + 1:][:3]
MODEL = (sys.argv[sys.argv.index('--') + 1:] + [None])[3]
MOD = 'bl_ext.user_default.' + PID
ok = []


def chk(n, c, info=''):
    ok.append(bool(c))
    print('TEST', 'OK ' if c else 'ECHEC', n, info, flush=True)


res = bpy.ops.extensions.package_install_files(filepath=ZIP, repo='user_default', enable_on_install=True)
chk('installation du zip', 'FINISHED' in res and MOD in bpy.context.preferences.addons, MOD)
m = importlib.import_module(MOD)
maj = importlib.import_module(MOD + '.maj')
v0 = maj.current_version_str()
chk('maj configuré', maj.CFG['id'] == PID and maj.CFG['repo'].startswith('lburdier/'), (maj.CFG['repo'], v0))
ns = getattr(bpy.ops, PRE)
chk('opérateurs de mise à jour', all(hasattr(ns, o) for o in ('maj_verifier', 'maj_installer', 'maj_page')))
chk('installation de type extension', maj.install_kind()[0] == 'local', maj.install_kind())

# ------------------------------------------------ dessin des préférences et du bandeau (fausse interface)
ICONS = set(bpy.types.UILayout.bl_rna.functions['label'].parameters['icon'].enum_items.keys())
errs = []
prefs = bpy.context.preferences.addons[MOD].preferences


class L:
    def __init__(self):
        object.__setattr__(self, 'x', 0)

    def __setattr__(self, k, v):
        pass

    def _i(self, kw):
        if kw.get('icon') and kw['icon'] not in ICONS:
            errs.append('icône ' + kw['icon'])

    def label(self, **kw):
        self._i(kw)

    def operator(self, idname, **kw):
        self._i(kw)
        a, b = idname.split('.')
        if not hasattr(getattr(bpy.ops, a), b):
            errs.append('opérateur ' + idname)
        return type('P', (), {})()

    def prop(self, data, name, **kw):
        self._i(kw)
        if name not in data.bl_rna.properties:
            errs.append('propriété ' + name)

    def box(self):
        return L()

    def __getattr__(self, k):          # row, column, split, progress, template_*...
        return lambda *a, **kw: L()


class S:                               # « self » des préférences : layout factice + vraies propriétés
    layout = L()

    def __getattr__(self, k):
        return getattr(prefs, k)


S.bl_rna = prefs.bl_rna
for st in ('idle', 'checking', 'available', 'downloading', 'installed', 'uptodate', 'offline', 'error'):
    maj.state.update(status=st, latest='9.9.9', error='essai')
    maj.draw_prefs(L(), prefs)
    maj.draw_status(L(), compact=True)
    try:
        type(prefs).draw(S(), bpy.context)
    except Exception as e:
        errs.append('draw préférences : %r' % e)
maj.state.update(status='idle')
chk('dessin des préférences et du bandeau', not errs, errs[:4])

# ------------------------------------------------ version 9.9.9 servie en local
tmp = tempfile.mkdtemp()
new = os.path.join(tmp, '%s-9.9.9.zip' % PID)
with zipfile.ZipFile(ZIP) as zi, zipfile.ZipFile(new, 'w', zipfile.ZIP_DEFLATED) as zo:
    for it in zi.infolist():
        data = zi.read(it.filename)
        if it.filename == 'blender_manifest.toml':
            data = re.sub(rb'(?m)^version = "[^"]+"', b'version = "9.9.9"', data)
        zo.writestr(it, data)
blob = open(new, 'rb').read()


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=tmp, **k)

    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = 'http://127.0.0.1:%d/%s' % (srv.server_address[1], os.path.basename(new))
maj._fetch_latest = lambda name: dict(tag='v9.9.9', page='', notes='essai', asset=dict(
    name=os.path.basename(new), browser_download_url=url, size=len(blob), digest='sha256:' + hashlib.sha256(blob).hexdigest()))
maj._check_thread(maj.CFG['repo'])
chk('nouvelle version détectée', maj.state['status'] == 'available' and maj.state['latest'] == '9.9.9', maj.state['status'])
err = maj.install()
for t in threading.enumerate():
    if t.name.endswith('-maj-dl'):
        t.join(30)
chk('téléchargement vérifié (taille + SHA-256)', not err and maj.state['status'] == 'downloaded', (err, maj.state['status'], maj.state['error']))
maj._install_downloaded()
chk('installée par Blender', maj.state['status'] == 'installed', maj.state['error'])
m2 = importlib.import_module(MOD + '.maj')
chk('9.9.9 active et rechargée', MOD in bpy.context.preferences.addons and m2 is not maj and m2.current_version_str() == '9.9.9',
    (v0, m2.current_version_str()))
chk('bandeau « mis à jour » après rechargement', m2.updated_from() == (v0, '9.9.9'), m2.updated_from())

# une release dont le zip est corrompu doit être refusée
bad = os.path.join(tmp, '%s-9.9.10.zip' % PID)
open(bad, 'wb').write(blob[:-10] + b'0123456789')
m2._fetch_latest = lambda name: dict(tag='v9.9.10', page='', notes='', asset=dict(
    name=os.path.basename(bad), browser_download_url=url.replace('9.9.9', '9.9.10'), size=len(blob),
    digest='sha256:' + hashlib.sha256(blob).hexdigest()))
m2._check_thread(m2.CFG['repo'])
m2.install()
for t in threading.enumerate():
    if t.name.endswith('-maj-dl'):
        t.join(30)
chk('zip corrompu refusé', m2.state['status'] == 'error' and 'SHA-256' in m2.state['error'], m2.state['error'])
srv.shutdown()

# ------------------------------------------------ modèle (option)
if MODEL:
    mm = importlib.import_module(MOD)
    info = mm.modele.install_zip(MODEL, mm.modele.store_dir())
    chk('modèle installé depuis le zip', mm.modele.local_model() is not None, info)

print('BILAN', sum(ok), '/', len(ok), flush=True)
