# bench v10 — ORACLES INDÉPENDANTS + PROBE d'alignement.
# Les golds sont calculés ICI (implémentations main des specs publiées :
# GS1 mod-10, ISO 7064 MOD 97-10, calendrier/zoneinfo stdlib, hashlib,
# Decimal) — JAMAIS en appelant mechacut. --probe compare ensuite au
# produit LIVE : tout désaccord est une QUESTION AU PRODUIT, jamais un
# gold retouchée en silence.
import base64
import calendar
import hashlib
import json
import re
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

sys.path.insert(0, "/Users/vincenzocirilli/Downloads/mechacut/bench")

TWO = Decimal("0.01")


def gs1_dv(payload):
    s, w = 0, 3
    for ch in reversed(str(payload)):
        s += int(ch) * w
        w = 1 if w == 3 else 3
    return (10 - s % 10) % 10


def isbn_repair(v):
    out = []
    for pos in range(len(v)):
        for d in "0123456789":
            if d == v[pos]:
                continue
            cand = v[:pos] + d + v[pos + 1:]
            if cand[:3] in ("978", "979") and \
                    gs1_dv(cand[:12]) == int(cand[12]):
                out.append("%d:%s" % (pos, d))
    return sorted(out, key=lambda x: (int(x.split(":")[0]), x))


def mod97_10_check(payload18):
    """ISO 7064 MOD 97-10 comme publié par GLEIF (ISO 17442 §3) :
    lettres A=10..Z=35, on ajoute '00', check = 98 − (nombre mod 97),
    deux chiffres. Recoupé par le vecteur public BMW/DO55→55."""
    num = "".join(str(int(c, 36)) for c in payload18)
    x = int(num + "00")
    return "%02d" % (98 - x % 97)


def q2(d):
    return str(Decimal(d).quantize(TWO, rounding=ROUND_HALF_UP))


def biz_shift(iso, n):
    d = date.fromisoformat(iso)
    left = abs(n)
    step = 1 if n >= 0 else -1
    while left:
        d += timedelta(days=step)
        if d.weekday() < 5:
            left -= 1
    return d.isoformat()


def canon_url(u):
    m = re.match(r"(?P<s>[^:]+)://(?P<host>[^/]*)(?P<rest>.*)", u)
    scheme = m.group("s").lower()
    host = m.group("host").lower().split(":")[0]
    rest = m.group("rest").split("#", 1)[0]
    if "?" in rest:
        path, qs = rest.split("?", 1)
        pairs = [kv.split("=", 1) for kv in qs.split("&") if kv]
        pairs = [p for p in pairs if not p[0].startswith("utm_")]
        pairs.sort(key=lambda p: (p[0], p[1] if len(p) > 1 else ""))
        q = "&".join("=".join(p) for p in pairs)
        rest = path + ("?" + q if q else "")
    return scheme + "://" + host + rest


def build_gold():
    return {
        "dv_ean13": [str(gs1_dv("400638133393"))],
        "dv_gtin14": [str(gs1_dv("0978030640615"))],
        "dv_isbn13": [str(gs1_dv("978030640615"))],
        "repair_isbn": [",".join(isbn_repair("9780306406158"))],
        "lei_check": [mod97_10_check("529900T8BM49AURSDO")],
        "sha256_a": [hashlib.sha256(
            "mechacut:v10:9780306406157".encode()).hexdigest()],
        "sha256_b": [hashlib.sha256("v10-Δ-€-日本".encode()).hexdigest()],
        "b64_sha512": [base64.b64encode(
            hashlib.new("sha512", b"mechacut-v10").digest()).decode()],
        "disc_double": [q2(Decimal("89.90") * Decimal("0.7")
                           * Decimal("0.8")),
                        q2((Decimal(1) - Decimal("0.7")
                            * Decimal("0.8")) * 100)],
        "disc_order": [q2(Decimal("83.40") * Decimal("0.7") - 5),
                       q2(abs((Decimal("83.40") - 5) * Decimal("0.7")
                              - (Decimal("83.40") * Decimal("0.7") - 5)))],
        "disc_b2p1": [q2(Decimal("19.99") * 2),
                      q2((Decimal(1) - Decimal(2) / Decimal(3)) * 100)],
        "biz_shift": [biz_shift("2026-11-23", 10)],
        "feb_end": ["2027-02-%02d" % calendar.monthrange(2027, 2)[1]],
        "next_monday_sunday": [date.fromisocalendar(2026, 48, 1)
                               .isoformat()],
        "dst_gap": [(datetime(2027, 3, 28, 1, 30,
                  tzinfo=ZoneInfo("Europe/Luxembourg"))
                     + timedelta(hours=2)).strftime("%H:%M")],
        "url_canon": [canon_url("HTTPS://Shop.Example.COM/Deals/?b=2"
                                "&a=1&utm_source=x&b=1#top")],
        "csv_eu_meaning": ["1234"],
        "xml_force": ['{"a":{"b":{"c":[{"@x":"1"}]}}}'],
    }


GOLD = build_gold()

# SANITÉS publiées (l'oracle doit reproduire les vecteurs connus)
assert GOLD["dv_gtin14"] == ["7"], GOLD["dv_gtin14"]  # vecteur
                                        # test 34
assert GOLD["lei_check"] == ["55"], GOLD["lei_check"]  # GLEIF
assert GOLD["dv_ean13"] == ["1"], GOLD["dv_ean13"]      # exemple GS1
assert GOLD["dv_isbn13"] == ["7"], GOLD["dv_isbn13"]    # ISBN canonique
assert GOLD["biz_shift"] == ["2026-12-07"], GOLD["biz_shift"]
assert GOLD["feb_end"] == ["2027-02-28"]
assert GOLD["next_monday_sunday"] == ["2026-11-23"]
assert GOLD["dst_gap"] == ["03:30"]
assert GOLD["disc_double"] == ["50.34", "44.00"]
assert GOLD["disc_order"] == ["53.38", "1.50"]
assert GOLD["disc_b2p1"] == ["39.98", "33.33"]
assert "12:7" in GOLD["repair_isbn"][0]                 # la vraie correction

if __name__ == "__main__":
    print(json.dumps(GOLD, ensure_ascii=False, indent=1))
    if "--probe" in sys.argv:
        import httpx
        import task10
        import run10  # réutilise extracteurs + binding
        bad = 0
        for t in task10.TASKS:
            r = run10.server_answer(t)
            ok = run10.match(GOLD[t["id"]], r, t["cmp"])
            print("%-20s %s gold=%s server=%s"
                  % (t["id"], "OK " if ok else "DÉSACCORD",
                     GOLD[t["id"]], r))
            bad += 0 if ok else 1
        print("probe:", len(task10.TASKS) - bad, "/", len(task10.TASKS),
              "alignés")
        sys.exit(1 if bad else 0)
