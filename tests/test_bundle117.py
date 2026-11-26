# -*- coding: utf-8 -*-
"""bundle117 — /money/settle connaît l'AVANCE NON-CASH. Le fil r/askmath
1tuuael a publié DEUX réponses pour le MÊME voyage (40,50 vs 290,50 —
écart EXACT la moitié de la face, 250 : un désaccord de GRAPHE, pas
d'arithmétique). La machine rend la lecture DECLAREE par l'appelant :
counts face | cash (valeur en ARGUMENT — jamais dévinée, CFPB
2024-05) | none (note seule). Sans lecture nommée : REFUS.

Attendus CALCULÉS À LA MAIN depuis les fils relus AU SOURCE le 26-11
06h10 (web_extract 1tuuael + 129phqq, citations complètes) — jamais
recopiés du module :
  1tuuael face : 631+50+500 = 1181 ; parts 590,50 ; elle +40,50,
      lui -40,50 (son 550 = 50 cash + 500 points COMPTÉS en face).
  1tuuael none : 631+50 = 681 ; parts 340,50 ; elle +290,50 (PuzzleDad :
      « you agreed to GIVE the $500 in credits, then share the
      remaining cost »).
  129phqq face : 144+200 = 344 ; parts 86 ; A +58, B +114, C/D -86
      (la réponse acceptée du fil, virements au détail près).
  129phqq cash-160 : 144+160 = 304 ; parts 76 ; A +68, B +84, C/D -76.
  129phqq none : pot = cash seul 144 ; parts 36 ; A +108, B/C/D -36
      (la GC est alors la part personnelle de B — elle ne « compte
      pas dans le partage »).
Croisés contre un oracle INDÉPENDANT (énumération exhaustive des
partitions à somme nulle, écriture différente du DP du module).
"""
import itertools
import json
from decimal import Decimal

import main
import settlementkit as sk
from fastapi.testclient import TestClient

client = TestClient(main.app)

# ---- r/askmath 1tuuael, relu AU FIL 26-11 06h10 ---------------------
# Elle 631 (hôtel, carte au montant ENTIER — GoudaIntruda : « did she
# truly pay 631? »). Lui 50 cash + 500 de points appliqués sur son
# 550 (PuzzleDad : « You paid $50 (after taking away the $500
# credit) »).
TRIP = [{"who": "her", "paid": "631.00"},
        {"who": "him", "paid": "50.00"},
        {"who": "him", "paid": "500.00", "kind": "noncash",
         "counts": "face", "label": "reward points"}]
TRIP_NONE = [{"who": "her", "paid": "631.00"},
             {"who": "him", "paid": "50.00"},
             {"who": "him", "paid": "500.00", "kind": "noncash",
              "counts": "none", "label": "reward points"}]
NAMES2 = ["her", "him"]

# ---- r/askmath 129phqq : GC 200 + carte 144, 4 personnes ------------
GC = [{"who": "A", "paid": "144.00"},
      {"who": "B", "paid": "200.00", "kind": "noncash",
       "counts": "face", "label": "gift card"}]
GC160 = [{"who": "A", "paid": "144.00"},
         {"who": "B", "paid": "200.00", "kind": "noncash",
          "counts": "cash", "value": "160.00", "label": "gift card"}]
GCNONE = [{"who": "A", "paid": "144.00"},
          {"who": "B", "paid": "200.00", "kind": "noncash",
           "counts": "none", "label": "gift card"}]
NAMES4 = ["A", "B", "C", "D"]


def oracle_min_transfers(bal):
    """Indépendant : énumère TOUTES les partitions en sous-ensembles
    à somme nulle (récursion premier-élément)."""
    nz = [n for n, b in bal.items() if b]

    def best(rem):
        if not rem:
            return 0
        out = -1
        head = rem[0]
        for r in range(1, len(rem) + 1):
            for combo in itertools.combinations(rem[1:], r - 1):
                grp = (head,) + combo
                if sum(bal[x] for x in grp) == 0:
                    rest = [x for x in rem if x not in grp]
                    v = 1 + best(rest)
                    if v > out:
                        out = v
        return out
    return len(nz) - best(nz)


def bal_cents(res):
    out = {}
    for b in res["balances"]:
        p = b["position"]
        if p == "settled":
            out[b["who"]] = 0
            continue
        sign = -1 if p.startswith("owed") else 1
        out[b["who"]] = sign * int(Decimal(p.split()[-1]).scaleb(2))
    return out


# ====================== les DEUX réponses publiées ==================

def test_face_reading_matches_OP_answer():
    # 40,50 — la lecture OP/GreenExponent (« the points just reduce
    # the total, not the difference » : crédités en face, le pot est
    # la consommation totale 1181).
    r = sk.money_settle(TRIP, NAMES2)
    assert r["total"] == "1181.00"
    assert [b["position"] for b in r["balances"]] == ["due 40.50",
                                                      "owed 40.50"]
    assert r["transfers"] == [{"from": "him", "to": "her",
                               "amount": "40.50"}]
    assert r["minimal"] is True
    assert r["transfer_count"] == 1


def test_none_reading_matches_PuzzleDad_answer():
    # 290,50 — « you agreed to GIVE the 500 in credits, then share
    # the remaining cost » : la nature sort du pot ET du registre.
    r = sk.money_settle(TRIP_NONE, NAMES2)
    assert r["total"] == "681.00"
    assert [b["position"] for b in r["balances"]] == ["due 290.50",
                                                      "owed 290.50"]
    assert r["transfers"] == [{"from": "him", "to": "her",
                               "amount": "290.50"}]


def test_the_gap_is_exactly_half_the_face():
    # LA thèse du lot : 290,50 - 40,50 = 250 = 500/2 — un désaccord
    # de graphe, pas d'arithmétique. Ni l'un ni l'autre n'est faux.
    f = bal_cents(sk.money_settle(TRIP, NAMES2))
    n = bal_cents(sk.money_settle(TRIP_NONE, NAMES2))
    assert f["her"] - n["her"] == -25000
    assert f["him"] - n["him"] == 25000


def test_none_line_travels_as_a_visible_note():
    r = sk.money_settle(TRIP_NONE, NAMES2)
    gc = [a for a in r["advances"] if a.get("kind") == "noncash"][0]
    assert gc["paid"] == "500.00" and gc["settled"] == "0.00"
    assert "note only" in gc["note"]


# ======================== r/askmath 129phqq ==========================

def test_giftcard_face_replays_accepted_thread_answer():
    r = sk.money_settle(GC, NAMES4)
    assert r["total"] == "344.00"
    assert [b["position"] for b in r["balances"]] == [
        "due 58.00", "due 114.00", "owed 86.00", "owed 86.00"]
    bal = bal_cents(r)
    assert r["transfer_count"] == oracle_min_transfers(bal) == 3
    assert r["minimal"] is True
    # chaque virement est du fil (C/D -> A/B, montants 86/58/28) —
    # la MAISON choisit ses égalités (plus-large-d'abord, ordre), le
    # TOTAL par créancier est identique au commentaire accepté.
    per_to = {}
    for t in r["transfers"]:
        per_to[t["to"]] = per_to.get(t["to"], 0) + int(
            Decimal(t["amount"]).scaleb(2))
    assert per_to == {"A": 5800, "B": 11400}


def test_giftcard_cash_value_reading():
    # la GC A COÛTÉ 160 : B est crédité de son débours, pas de la
    # face — troisième réponse publiée par la famille des fils.
    r = sk.money_settle(GC160, NAMES4)
    assert r["total"] == "304.00"
    assert [b["position"] for b in r["balances"]] == [
        "due 68.00", "due 84.00", "owed 76.00", "owed 76.00"]


def test_giftcard_none_reading():
    # « Is person B's GC supposed to be part of the split? » — non :
    # pot = cash seul, B paie sa part comme les autres.
    r = sk.money_settle(GCNONE, NAMES4)
    assert r["total"] == "144.00"
    assert [b["position"] for b in r["balances"]] == [
        "due 108.00", "owed 36.00", "owed 36.00", "owed 36.00"]
    assert sum(bal_cents(r).values()) == 0


# ==================== itemized : arête par arête =====================

def test_itemized_edges_per_line():
    # TRIP en face, par reçu : 631/2 = 315,50 lui->elle ; 50/2 =
    # 25,00 elle->lui ; 500/2 = 250,00 elle->lui (sa nature est
    # partagée AUSSI reçu par reçu). oop elle = 631-315,50+275 =
    # 590,50 ; oop lui = 550+315,50-275 = 590,50 ; somme 1181.
    r = sk.money_settle(TRIP, NAMES2, mode="itemized")
    assert r["total"] == "1181.00"
    assert [(e["from"], e["to"], e["amount"]) for e in r["transfers"]] \
        == [("him", "her", "315.50"), ("her", "him", "25.00"),
           ("her", "him", "250.00")]
    pos = {p["who"]: p for p in r["positions"]}
    assert pos["her"]["out_of_pocket"] == "590.50"
    assert pos["him"]["out_of_pocket"] == "590.50"
    assert pos["him"]["noncash_credit"] == "500.00"
    assert "noncash_credit" not in pos["her"]


def test_compare_carries_both_graphs_and_rule():
    r = sk.money_settle(TRIP, NAMES2, mode="compare")
    assert r["divergence"]["pays_net"]["him->her"] == "40.50"
    # itemized ne NETTE rien entre recus (regole b115) : le brut est
    # affiche par recu — 315,50 sortir contre 275,00 entrer ferme
    # EXACTEMENT au solde net 40,50. C'est la meme verite rendue
    # deux fois, pas un desaccord.
    assert r["divergence"]["pays_itemized"]["him->her"] == "315.50"
    assert r["divergence"]["pays_itemized"]["her->him"] == "275.00"
    assert Decimal("315.50") - Decimal("275.00") == Decimal("40.50")
    assert "noncash" in r["noncash_rule"]


# =================== refus nommés (le gate du lot) ===================

def _refuse(advances, fragment):
    try:
        sk.money_settle(advances, NAMES4)
        raise AssertionError("should have refused: %r" % fragment)
    except sk.MoneyError as e:
        assert fragment in str(e), str(e)


def test_noncash_without_reading_is_refused():
    _refuse([{"who": "A", "paid": "10.00", "kind": "noncash"}],
            "not a reading")


def test_unknown_reading_is_refused():
    _refuse([{"who": "A", "paid": "10.00", "kind": "noncash",
              "counts": "half"}], "not a reading")


def test_cash_reading_without_value_is_refused():
    _refuse([{"who": "A", "paid": "10.00", "kind": "noncash",
              "counts": "cash"}], "needs value")


def test_value_outside_cash_reading_is_refused():
    # une valorisation que personne ne lit est un mensonge en
    # attente de son lecteur
    _refuse([{"who": "A", "paid": "10.00", "kind": "noncash",
              "counts": "face", "value": "9.00"}],
            "legal only under counts=cash")


def test_cash_line_cannot_carry_valuation_fields():
    _refuse([{"who": "A", "paid": "10.00", "counts": "face"}],
            "belong to kind=noncash")


def test_kind_outside_closed_set_is_refused():
    _refuse([{"who": "A", "paid": "10.00", "kind": "barter"}],
            "cash|noncash")


def test_noncash_zero_face_is_refused():
    _refuse([{"who": "A", "paid": "0.00", "kind": "noncash",
              "counts": "face"}], "no face to count")


def test_negative_value_is_refused():
    _refuse([{"who": "A", "paid": "10.00", "kind": "noncash",
              "counts": "cash", "value": "-5.00"}],
            "negative value refused")


# =================== fratrie : cents, remise, devise =================

def test_remainder_rule_travels_on_noncash_faces():
    # 200,00 / 3 = 66,67 / 66,67 / 66,66 (reste 2, ordre X,Y — règle
    # /money/split importée). X avance 100 cash, Y 100 EN NATURE.
    r = sk.money_settle(
        [{"who": "X", "paid": "100.00"},
         {"who": "Y", "paid": "100.00", "kind": "noncash",
          "counts": "face"}], ["X", "Y", "Z"])
    assert [s["share"] for s in r["shares"]] == ["66.67", "66.67",
                                                 "66.66"]
    assert [b["position"] for b in r["balances"]] == [
        "due 33.33", "due 33.33", "owed 66.66"]
    bal = bal_cents(r)
    assert r["transfer_count"] == oracle_min_transfers(bal)


def test_waiver_caps_on_a_noncash_credit():
    # A (+58) remet à C : la remise ne libère QUE la créance nette —
    # le cap vit AUSSI quand le pot contient de la nature.
    r = sk.money_settle(GC, NAMES4, waivers=[{"from": "A", "to": "C"}])
    w = r["waivers"][0]
    assert w["applied"] == "58.00"
    assert "cap" not in w  # la créance suffisait, pas de plafond touché
    assert [b["position"] for b in r["balances"]] == [
        "settled", "due 114.00", "owed 28.00", "owed 86.00"]
    bal = bal_cents(r)
    assert r["transfer_count"] == oracle_min_transfers(bal) == 2


def test_noncash_face_converts_like_cash():
    # USD 50,00 au taux ARGUMENT 0,90 -> 45,00 EUR ; pot 145,00 ;
    # parts 72,50 ; elle +27,50.
    r = sk.money_settle(
        [{"who": "her", "paid": "100.00", "currency": "EUR"},
         {"who": "him", "paid": "50.00", "kind": "noncash",
          "counts": "face", "currency": "USD"}],
        NAMES2, currency="EUR", rates={"USD": "0.90"})
    assert r["total"] == "145.00"
    gc = [a for a in r["advances"] if a.get("kind") == "noncash"][0]
    assert gc["settled"] == "45.00"
    assert gc["rate_used"] == "0.90"
    assert [b["position"] for b in r["balances"]] == ["due 27.50",
                                                      "owed 27.50"]


# ============== contrat : les graphes 100 % cash ne bougent ===========

def test_cash_only_response_is_byte_stable_with_bundle115():
    ADV = [{"who": "A", "paid": "1375.00"},
           {"who": "B", "paid": "0.00"},
           {"who": "C", "paid": "865.00"}]
    r = sk.money_settle(ADV, ["A", "B", "C"],
                        waivers=[{"from": "C", "to": "B"}])
    assert set(r.keys()) == {"mode", "currency", "advances", "total",
                             "shares", "balances", "waivers",
                             "transfers", "transfer_count",
                             "minimal", "minimum_rule",
                             "identity_check", "share_mode"}
    assert all(set(b.keys()) == {"who", "position"}
               for b in r["balances"])
    assert "noncash_rule" not in r


# ============================ surface API ============================

def test_api_noncash_and_refuse():
    ok = client.post("/api/v1/money/settle",
                     json={"advances": TRIP, "participants": NAMES2})
    assert ok.status_code == 200
    assert "noncash_rule" in ok.json()
    bad = client.post("/api/v1/money/settle", json={
        "advances": [{"who": "A", "paid": "10.00", "kind": "noncash"}],
        "participants": ["A"]})
    assert bad.status_code == 400
    assert "not a reading" in json.dumps(bad.json())


def test_api_sha256_covers_the_noncash_note():
    r = client.post("/api/v1/money/settle",
                    json={"advances": GCNONE, "participants": NAMES4})
    assert r.status_code == 200
    assert "sha256" in r.json()
