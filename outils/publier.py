"""Publie une version de l'extension sur GitHub (release publique) : les utilisateurs la reçoivent
automatiquement (maj.py vérifie les releases au démarrage de Blender et installe la nouvelle version).

    python outils/publier.py                       # version du manifeste, modèle inchangé
    python outils/publier.py --modele X.zip        # publie aussi un nouveau modèle 3D (zip + modele.json)
    python outils/publier.py --notes notes.md      # texte de la release (sinon : dernier message de commit)
    python outils/publier.py --essai               # construit et vérifie seulement, ne publie rien

Étapes : vérifie que le dépôt est propre et poussé -> construit <id>-<version>.zip avec Blender
(blender --command extension build) -> le valide -> prépare modele.json (catalogue du modèle 3D lu par
l'add-on à releases/latest/download/modele.json) -> tag vX.Y.Z -> gh release create avec les fichiers.
Sans --modele, modele.json est repris de la release précédente avec une adresse absolue vers le zip
du modèle déjà publié : le modèle n'est pas renvoyé à chaque version.
Prérequis : git, gh (connecté), Blender 4.2+ (variable BLENDER, sinon le plus récent de Program Files)."""
import argparse
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(*cmd, capture=False, check=True):
    print('>', ' '.join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=capture, encoding='utf8')
    if check and r.returncode:
        sys.exit(f"échec ({r.returncode}) : {' '.join(cmd)}\n{(r.stderr or '') if capture else ''}")
    return (r.stdout or '').strip() if capture else r.returncode


def blender():
    exe = os.environ.get('BLENDER')
    if exe and os.path.isfile(exe):
        return exe
    found = sorted(glob.glob(r'C:\Program Files\Blender Foundation\Blender *\blender.exe'),
                   key=lambda p: [int(x) for x in os.path.basename(os.path.dirname(p)).split()[-1].split('.')])
    if not found and shutil.which('blender'):
        return shutil.which('blender')
    if not found:
        sys.exit("Blender introuvable : définir la variable BLENDER")
    return found[-1]


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modele', help="zip du modèle 3D à publier avec cette version")
    ap.add_argument('--notes', help="fichier Markdown du texte de la release")
    ap.add_argument('--essai', action='store_true', help="construire et vérifier sans publier")
    a = ap.parse_args()

    with open(os.path.join(ROOT, 'blender_manifest.toml'), 'rb') as f:
        man = tomllib.load(f)
    pid, ver, name = man['id'], man['version'], man['name']
    repo = man['website'].rstrip('/').split('github.com/')[1]
    tag = 'v' + ver
    print(f"== {name} {ver} -> {repo}", flush=True)

    if not a.essai:
        if run('git', 'status', '--porcelain', capture=True):
            sys.exit("des fichiers ne sont pas commités : commit d'abord (git status)")
        run('git', 'fetch', '--tags', '--quiet', 'origin')
        if run('git', 'rev-parse', '-q', '--verify', 'refs/tags/' + tag, capture=True, check=False):
            sys.exit(f"le tag {tag} existe déjà : augmenter « version » dans blender_manifest.toml")
        if run('git', 'rev-list', '--count', '@{u}..HEAD', capture=True, check=False) not in ('0', ''):
            run('git', 'push', 'origin', 'HEAD')

    out = tempfile.mkdtemp(prefix=pid + '_release_')
    exe = blender()
    run(exe, '--factory-startup', '--command', 'extension', 'build', '--source-dir', ROOT, '--output-dir', out)
    zp = os.path.join(out, f'{pid}-{ver}.zip')
    if not os.path.isfile(zp):
        sys.exit("zip de l'extension non créé")
    run(exe, '--factory-startup', '--command', 'extension', 'validate', zp)
    files = [zp]

    # catalogue du modèle 3D
    cat_path = os.path.join(out, 'modele.json')
    if a.modele:
        mz = os.path.abspath(a.modele)
        local = os.path.join(os.path.dirname(mz), 'modele.json')
        cat = json.load(open(local, encoding='utf8')) if os.path.isfile(local) else {}
        cat.update(url=os.path.basename(mz), size=os.path.getsize(mz), sha256=sha256(mz))
        if 'version' not in cat:
            sys.exit("modele.json (à côté du zip du modèle) doit donner la version du modèle")
        files.append(mz)
    else:
        prev = tempfile.mkdtemp()
        if run('gh', 'release', 'download', '-R', repo, '--pattern', 'modele.json', '--dir', prev, check=False):
            sys.exit("pas de modele.json dans la dernière release : publier avec --modele <zip du modèle>")
        cat = json.load(open(os.path.join(prev, 'modele.json'), encoding='utf8'))
        if '://' not in cat['url']:
            prev_tag = run('gh', 'release', 'view', '-R', repo, '--json', 'tagName', '--jq', '.tagName', capture=True)
            cat['url'] = f"https://github.com/{repo}/releases/download/{prev_tag}/{cat['url']}"
    with open(cat_path, 'w', encoding='utf8') as f:
        json.dump(cat, f, indent=1, ensure_ascii=False)
    files.append(cat_path)
    print('catalogue du modèle :', json.dumps(cat, ensure_ascii=False), flush=True)

    if a.notes:
        notes = open(a.notes, encoding='utf8').read()
    else:
        notes = run('git', 'log', '-1', '--format=%B', capture=True)
    notes += (f"\n\n---\n**Installation** : télécharge `{pid}-{ver}.zip` ci-dessous et glisse-le dans Blender "
              f"(ou *Édition › Préférences › Extensions › Installer depuis le disque*). "
              f"Les versions suivantes s'installent ensuite toutes seules au démarrage de Blender.")
    if a.essai:
        print('ESSAI : rien publié. Fichiers :', files)
        return
    run('git', 'tag', '-a', tag, '-m', f'{name} {ver}')
    run('git', 'push', 'origin', tag)
    nf = os.path.join(out, 'notes.md')
    open(nf, 'w', encoding='utf8').write(notes)
    run('gh', 'release', 'create', tag, '-R', repo, '--title', f'{name} {ver}', '--notes-file', nf, '--latest', *files)
    print(f"PUBLIÉ https://github.com/{repo}/releases/tag/{tag}")


if __name__ == '__main__':
    main()
