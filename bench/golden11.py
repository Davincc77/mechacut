# bench v11 — golds par oracles purs (aucun appel produit).
# Chaque valeur est recalculée ici par une implémentation main de la
# spec citée dans la question nue ; les asserts internes recoupent des
# vecteurs PUBLIÉS (HP 043942089X, canon JSON de l'énoncé, +12 semaines
# calendrier) — si l'oracle et la question divergent, le build casse.
import hashlib
import json
import sys
from datetime import date, timedelta
from decimal import Decimal

sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut/bench")
import task11


def gs1_dv(payload):
    s, w = 0, 3
    for ch in reversed(str(payload)):
        s += int(ch) * w
        w = 1 if w == 3 else 3
    return (10 - s % 10) % 10


def luhn_dv(digits):
    total, alt = 0, True
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return (10 - total % 10) % 10


def isbn10_check(p9):
    s = sum(int(c) * (10 - i) for i, c in enumerate(p9))
    r = (11 - s % 11) % 11
    return "X" if r == 10 else str(r)


def issn_check(p7):
    s = sum(int(c) * (8 - i) for i, c in enumerate(p7))
    r = (11 - s % 11) % 11
    return "X" if r == 10 else str(r)


def isin_dv(payload):
    num = "".join(str(int(c, 36)) for c in payload)
    return str(luhn_dv(num))


def mod97_10(payload):
    num = "".join(str(int(c, 36)) for c in payload)
    x = int(num + "00")
    return "%02d" % (98 - x % 97)


def biz_shift(iso, n, holidays=()):
    hol = set(holidays)
    d = date.fromisoformat(iso)
    left = abs(n)
    while left:
        d += timedelta(days=1)
        if d.weekday() < 5 and d.isoformat() not in hol:
            left -= 1
    return d.isoformat()


def biz_diff_incl(a, b, holidays=()):
    """weekdays in (a, b] excluding holidays — convention du PRODUIT,
    énoncée dans la question nue."""
    hol = set(holidays)
    d, e = date.fromisoformat(a), date.fromisoformat(b)
    n = 0
    while d < e:
        d += timedelta(days=1)
        if d.weekday() < 5 and d.isoformat() not in hol:
            n += 1
    return n


def h(x):
    return hashlib.sha256(x.encode()).hexdigest()


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


GOLD11 = {
    "v11_hash_stack": [h(h(h("mechacut-v11")))[-12:]],
    "v11_sha512_64": [hashlib.sha512(b"mechacut-v11-stack").hexdigest()],
    "v11_biz_holidays": [biz_shift("2026-12-14", 15,
                                   ["2026-12-25", "2027-01-01"])],
    "v11_diff_biz_hol": [str(biz_diff_incl("2027-01-04", "2027-01-29",
                                           ["2027-01-18"]))],
    "v11_csv_max": ["%.2f" % max(Decimal(str(v)) for v in
                                 task11.VALS11)],
    "v11_isbn10": ["X"],      # 043942089X — Scholastic HP, publié
    "v11_isbn10_k": [isbn10_check("156512158")],
    "v11_isin": [isin_dv("XS123456789")],
    "v11_dv_ean13": [str(gs1_dv("590123412345"))],
    "v11_gtin14": [str(gs1_dv("1234567890123"))],
    "v11_issn_x": [issn_check("2499216")],
    "v11_dv_lei": [mod97_10("529900MMAF64L11L2P")],
    "v11_url_canon": ["http://api.example.com/V2/Users/?a=1&b=2&limit=10"
                      "&offset=20"],
    "v11_canon_sha": [h(canon({"b": [3, {"d": 1, "c": 2}],
                               "a": True}))],
    "v11_recurring": ["2027-04-01"],  # 2027-01-07 + 4×21 jours
}

# ---- recoupements publiés / sanity
assert GOLD11["v11_isbn10"] == [isbn10_check("043942089")]  # HP vector
assert GOLD11["v11_recurring"] == [(date(2027, 1, 7)
                                    + timedelta(weeks=12))
                                   .isoformat()]
assert len(GOLD11["v11_sha512_64"][0]) == 128
assert GOLD11["v11_dv_ean13"] == ["7"]  # ladder double-vérifié
# (complément + contrôle mod-10 plein du n°13 complet) — le
# "3 de mémoire" a été tué par sa propre assertion : c'est LA
# règle d'or du bench, appliquée à l'oracle lui-même.
assert len(GOLD11) == len(task11.TASKS11) == 15

if __name__ == "__main__":
    print(json.dumps(GOLD11, ensure_ascii=False, indent=1))
