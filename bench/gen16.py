# Générateur seedé du banc v16 — nombres NEUFS, golds calculés AVANT
# que le modèle parle. Chaque famille porte sa contrainte d'unicité
# (un seul arrondi légitime) : la réponse exacte est atteignable, donc
# toute faute est une faute, pas une querelle d'arrondi.
#
# Anti-contamination : l'identité d'un problème = graine + famille,
# publiée. Aucun de ces énoncés n'existait avant ce fichier ; s'il en
# sortait un correct au premier coup, la mémoire ne peut pas être la
# cause — c'est exactement ce que v13 nous a volé et qu'on récupère.
import random
from fractions import Fraction

SEED = 2026
N = 20


def _fmt(f):
    """Fraction → chaîne décimale EXACTE. Le garde _terminates_2dp a
    déjà garanti dénominateur | 100 : on met aux centièmes en ENTIERS,
    sans jamais toucher un float (le formatage ne doit pas plus
    inventer que le calcul)."""
    assert 100 % f.denominator == 0
    cents = f * 100
    n = int(cents)
    if n < 0:
        return "-%d.%02d" % (-n // 100, -n % 100)
    return "%d.%02d" % (n // 100, n % 100)


def _terminates_2dp(f):
    """Le gold n'a droit qu'à des centièmes exacts : dénominateur
    (après réduction) dividing 100. Sinon le problème est re-tiré —
    jamais arrondi à la sauvette : la règle « un seul arrondi
    légitime » de l'en-tête est ICI exécutée, pas déclarative."""
    return 100 % f.denominator == 0


def problems():
    rng = random.Random(SEED)
    out = []
    fams = ["mix", "rate", "partage", "soldes", "distance", "recette"]

    def mix():
        # (a − b) multiple de 100 → le pourcentage du reste tombe sur
        # des centièmes EXACTS, aucun arrondi à inventer ni à deviner.
        b = rng.randint(20, 90)
        a = b + 100 * rng.randint(2, 6)
        pc = rng.choice([10, 15, 20, 25, 40, 50])
        r = Fraction(pc, 100) * (a - b)
        left = Fraction(a) - Fraction(b) - r
        return ("Un magasin a %d articles. %d sont vendus le matin, "
                "et %d %% du RESTE l'après-midi. Combien restent-ils ?"
                % (a, b, pc)), left

    def rate():
        l = rng.randint(6, 18)
        h = rng.randint(3, 9)
        q = rng.choice([2, 3, 5, 7])
        return ("Une pompe délivre %d litres en %d heures. À ce débit, "
                "combien de litres en %d heures ?" % (l, h, q)), \
            Fraction(l * q, h)

    def partage():
        tot = rng.randint(2000, 9000)
        r1 = rng.choice([Fraction(1, 2), Fraction(1, 3), Fraction(2, 5)])
        r2 = rng.choice([Fraction(1, 4), Fraction(1, 5), Fraction(1, 6)])
        return ("On partage %d € : la première personne reçoit %s, la "
                "seconde %s du RESTE. Combien reçoit la seconde ?"
                % (tot, str(r1), str(r2))), \
            (Fraction(tot) * (1 - r1)) * r2

    def soldes():
        # même discipline que mix : le Fraction du prix final doit
        # TOMBER sur des centièmes exacts — le garde _terminates_2dp
        # retirage sinon. Jamais de round() manuel qui inventerait une
        # convention que l'énoncé ne dit pas.
        p = rng.randint(19, 89) * 100 + 90  # 19.90 … 89.90 €
        d1 = rng.choice([10, 20, 25, 30, 50])
        d2 = rng.choice([10, 20, 25, 30, 50])
        f = Fraction(p, 100) * (1 - Fraction(d1, 100)) * \
            (1 - Fraction(d2, 100))
        return ("Un article à %.2f € est soldé %d %%, puis le prix "
                "soldé est à nouveau réduit de %d %%. Quel est le prix "
                "final, en euros ?" % (p / 100, d1, d2)), f

    def distance():
        v = rng.choice([55, 65, 75, 85, 95])
        tmin = rng.choice([40, 50, 70, 80, 110])
        return ("Une voiture roule à %d km/h pendant %d minutes. "
                "Combien de kilomètres parcourt-elle ?" % (v, tmin)), \
            Fraction(v * tmin, 60)

    def recette():
        base = rng.choice([2, 3, 4])
        eggs = rng.choice([3, 5, 7])
        people = rng.choice([6, 9, 12, 15])
        return ("Une recette pour %d personnes utilise %d œufs. Pour "
                "%d personnes, combien d'œufs, en conservant la même "
                "proportion ?" % (base, eggs, people)), \
            Fraction(eggs * people, base)

    F = {"mix": mix, "rate": rate, "partage": partage, "soldes": soldes,
         "distance": distance, "recette": recette}
    for i in range(N):
        fam = fams[i % len(fams)]
        for _ in range(500):          # retirage déterministe : la même
            text, gold = F[fam]()     # graine donne toujours les mêmes
            if _terminates_2dp(gold):  # 20 problèmes, reproductibles
                break
        else:
            raise AssertionError("famille %s : aucun tirage exact en "
                                 "500 essais — corriger la famille, pas "
                                 "relâcher le garde" % fam)
        out.append({"i": i, "family": fam, "text": text,
                    "gold": _fmt(gold)})
    return out


if __name__ == "__main__":
    for p in problems():
        print(p["i"], p["family"], "→", p["gold"], "|",
              p["text"][:60])
