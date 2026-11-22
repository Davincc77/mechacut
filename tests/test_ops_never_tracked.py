"""ADN gate — runtime, pas promesse : les docs d’opérations interne
(négociations, brouillons, méthode de travail) ne doivent JAMAIS
exister dans le dépôt public — le repo porte le produit et la preuve,
rien d’autre.

Sémantique : TOUT chemin exclu personnellement dans .git/info/exclude
(local, jamais poussable) est interdit à l’index git. La boucle exige
pytest vert avant chaque commit : un futur add -f d’un chemin ops
rouge la suite ici, sur cette machine, avant que ça parte sur GitHub.
Sur un clone tiers le fichier n’existe pas → le test se tait, et le
monde ne voit même pas la liste de ce qu’on protège."""
import fnmatch
import os
import subprocess

EXCLUDE = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                        os.pardir, ".git",
                                        "info", "exclude"))


def test_ops_never_tracked():
    if not os.path.exists(EXCLUDE):
        return
    banned = [l.strip() for l in open(EXCLUDE, encoding="utf-8")
              if l.startswith("/")]
    tracked = subprocess.run(["git", "ls-files"], capture_output=True,
                             text=True).stdout.split()
    for path in tracked:
        for b in banned:
            pat = b.lstrip("/")
            hit = (path == pat.rstrip("/")
                   or path.startswith(pat.rstrip("/") + "/")
                   or fnmatch.fnmatch(path, pat))
            assert not hit, ("chemin protégé dans le dépôt suivi : "
                             + path)
