# -*- coding: utf-8 -*-
"""Bundle 54 — l'annuaire de douleurs (S1) : contrat de la DATA +
verrou de cible + R1 machine (la fiche rend l'or sans aucun LM).

Doctrine : une entrée d'annuaire sans preuve sur disque est une
opinion — le test la tue. Le verrou T4 (answer[cible], pas trace[-1])
est né d'un incident de gate réel (bench/run22.py, 22-11) : il est
testé pour ne pas rouiller.
"""
import re

from fastapi.testclient import TestClient

import annuaire
import main

client = TestClient(main.app)


# --------------------------------------------------------- contrat DATA
def test_annuaire_charge_et_prouve():
    d = annuaire.load()
    assert d["version"]
    assert len(d["entrees"]) >= 3
    ids = {e["id"] for e in d["entrees"]}
    assert {"chaine-shop-reste", "chaine-partage-reste",
            "chaine-soldes2"} <= ids


def test_entree_sans_preuve_sur_disque_est_refusée(tmp_path):
    import json
    import pytest
    d = annuaire.load()
    d["entrees"][0]["preuve"] = ["bench/NEXISTE-PAS.md"]
    p = tmp_path / "a.json"
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    import pytest
    with pytest.raises(AssertionError):
        annuaire.load(str(p))


def test_verrou_cible_t4_impossible_de_se_tromper(tmp_path):
    # une cible qui ne correspond pas à la fiche crève le chargeur
    import json
    import pytest
    d = annuaire.load()
    d["entrees"][0]["prescription"]["cible"] = "leftover"  # le piège vécu
    fp = tmp_path / "a.json"
    fp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(AssertionError):
        annuaire.load(str(fp))


# ------------------------------------------------------------ trouver()
def test_trouver_nomme_la_bonne_fiche():
    d = annuaire.load()
    e, s = annuaire.trouver(
        "Un magasin a 10 articles, 2 vendus le matin puis 40% du "
        "RESTE l'après-midi, combien reste-t-il ?", d)
    assert e and e["prescription"]["fiche"] == "shop-reste"
    e2, _ = annuaire.trouver(
        "On partage 100 € : la première reçoit 1/4, la seconde 1/3 "
        "DU RESTE.", d)
    assert e2 and e2["prescription"]["fiche"] == "partage-reste"
    e3, _ = annuaire.trouver(
        "Un article à 80 € subit deux réductions successives de 20% "
        "et 30%.", d)
    assert e3 and e3["prescription"]["fiche"] == "soldes2"


def test_trouver_ne_devine_pas():
    d = annuaire.load()
    e, s = annuaire.trouver("Quelle est la capitale du Pérou ?", d)
    assert e is None and s == 0


def test_trouver_plie_les_accents():
    """Incident live 22-11 : « recoit » sans accent faisait perdre
    l'entrée partage au profit de mots-clés génériques."""
    d = annuaire.load()
    e, _ = annuaire.trouver(
        "On partage 800 euros : la premiere recoit 1/4, la seconde "
        "1/3 DU RESTE.", d)
    assert e and e["prescription"]["fiche"] == "partage-reste"


def test_trouver_egalite_pas_de_match():
    """Deux entrées au même score = le texte est réellement ambigu :
    aucun départage à l'ordre des lignes, pas de match (R3)."""
    d = annuaire.load()
    e, s = annuaire.trouver("Le magasin partage la marchandise.", d)
    assert e is None and s == 1


# ------------------------------------------- S2/S3 : plan + apply (R1/R3)
# V16_SHOP/V16_SOLDES : textes verbatim des gabarits v16 (bench/
# gen16.py), golds publiés FINDINGS-V16/F5. V16_PARTAGE : INSTANCE
# NOUVELLE du gabarit partage (mêmes motifs, fractions différentes) —
# gold écrit à la main ici : 3829×(1−2/5)=2297,4 ; ÷4 = 574,35 exact.
# (Premier jet du test : 382.90, le gold de #2 — le serveur a pêché
# mon erreur en rendant 574.35 : le verrou tient dans les deux sens.)
V16_SHOP = ("Un magasin a 435 articles. 35 sont vendus le matin, et 40 % "
            "du RESTE l'après-midi. Combien restent-ils ?")
V16_PARTAGE = ("On partage 3829 € : la première personne reçoit 2/5, la "
               "seconde 1/4 du RESTE. Combien reçoit la seconde ?")
V16_SOLDES = ("Un article à 81.90 € est soldé 20 %, puis le prix soldé "
              "est à nouveau réduit de 30 %. Quel est le prix final, "
              "en euros ?")


def _apply(texte):
    r = client.post("/api/v1/router/apply", json={"texte": texte})
    assert r.status_code == 200, r.text
    return r.json()


def test_r1_apply_machine_sans_lm():
    a = _apply(V16_SHOP)
    assert a["applied"] is True and a["cible"] == "remaining"
    assert a["reponse"] == "240"
    b = _apply(V16_PARTAGE)
    assert b["applied"] is True and b["reponse"] == "574.35"
    c = _apply(V16_SOLDES)
    assert c["applied"] is True
    # 81.90 × 0,8 × 0,7 = 45.864 exact = 45 108/125 (la fiche soldes2
    # rend la fraction exacte + l'approximation, jamais un float nu)
    assert c["reponse"] == "45 108/125 (≈ 45.86)"
    assert c["cible"] == "final"


def test_apply_deterministe_memes_octets():
    r1 = client.post("/api/v1/router/apply", json={"texte": V16_SHOP})
    r2 = client.post("/api/v1/router/apply", json={"texte": V16_SHOP})
    assert r1.content == r2.content


def test_r3_apply_ne_devine_jamais():
    # ambigu : deux « sont vendus » distincts → refus nommé, pas de nombre
    a = _apply("Un magasin a 435 articles. 35 sont vendus le matin, "
               "60 sont vendus le soir, et 40 % du RESTE l'après-midi.")
    assert a["applied"] is False and a["match"] is True
    assert any(x["slot"] == "sold_morning" for x in a["ambigus"])
    assert "reponse" not in a
    # hors cadre : pas de prescription inventée
    b = _apply("Quelle est la capitale du Pérou ?")
    assert b["applied"] is False and b["match"] is False
    assert "reponse" not in b
    # incomplet : prescription + prompt à remplir
    c = _apply("Un magasin a 100 articles, 40 % du RESTE l'après-midi.")
    assert c["applied"] is False and "sold_morning" in c["creneaux_manquants"]
    assert "Tu ne CALCULES RIEN" in c["prompt_lm"]


def test_plan_prescrit_avec_preuves():
    r = client.post("/api/v1/router/plan", json={"texte": V16_PARTAGE})
    b = r.json()
    assert b["match"] is True
    assert b["prescription"]["fiche"] == "partage-reste"
    assert len(b["regles_transport"]) == 4
    assert all(p.endswith(".md") for p in b["preuve"])
    r2 = client.post("/api/v1/router/plan",
                     json={"texte": "Quelle est la capitale du Pérou ?"})
    assert r2.json()["match"] is False


def test_parity_prod_image_sans_bench(tmp_path):
    """Incident 0.84.0 : le Docker n'embarque pas bench/ — un load
    strict au runtime plantait la prod sur les preuves (500). Garde :
    preuves absentes = le strict crève (commit), le runtime sert."""
    import json
    import pytest
    d = annuaire.load()
    for e in d["entrees"]:
        e["preuve"] = ["bench/PAS-DANS-L-IMAGE.md"]
    for r in d["regles_transport"]:
        r["preuve"] = "bench/PAS-DANS-L-IMAGE.md"
    fp = tmp_path / "ghost.json"
    fp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(AssertionError):
        annuaire.load(str(fp))            # le garde de commit veille
    g = annuaire.load(str(fp), strict=False)   # le runtime sert
    assert len(g["entrees"]) == 3


# ------------------------------------------------- R1 : la fiche rend l'or
def _reste(total, matin, pct):
    r = client.post("/api/v1/fiche/shop-reste", json={"slots": {
        "total": str(total), "sold_morning": str(matin),
        "pct_afternoon": "%d%%" % pct}})
    assert r.status_code == 200, r.text
    return r.json()


def test_shop_reste_cible_and_pas_trace():
    b = _reste(435, 35, 40)
    assert b["target"] == "remaining"
    assert b["answer"]["remaining"] == "240"
    # T4 : la dernière valeur de trace EST la cible ici, mais on
    # n'utilise JAMAIS trace[-1] pour répondre — answer[target] seul.
    assert "answer" in b and "trace" in b


def test_soldes2_leurre_some():
    r = client.post("/api/v1/fiche/soldes2", json={"slots": {
        "price": "100", "pct1": "20%", "pct2": "30%"}})
    b = r.json()
    assert b["answer"]["final"] == "56"        # pas 50%
    assert b["answer"]["naive_sum_pct"] == "50"
    assert b["target"] == "final"


def test_annuaire_creneau_coherents_avec_fiche():
    # chaque créneau prescrit doit être réellement accepté (sinon la
    # prescription est un mensonge) — on rejoue chaque fiche à l'or.
    checks = {
        "shop-reste": ({"total": "100", "sold_morning": "20",
                        "pct_afternoon": "50%"}, "remaining"),
        "partage-reste": ({"total": "100", "first_part": "1/4",
                           "second_of_rest": "1/3"}, "second_share"),
        "soldes2": ({"price": "100", "pct1": "10%", "pct2": "10%"},
                    "final"),
    }
    d = annuaire.load()
    for e in d["entrees"]:
        fiche = e["prescription"]["fiche"]
        slots, cible = checks[fiche]
        assert set(slots) == set(e["prescription"]["creneaux"]), fiche
        assert e["prescription"]["cible"] == cible
        r = client.post("/api/v1/fiche/" + fiche, json={"slots": slots})
        assert r.status_code == 200, (fiche, r.text)
        assert cible in r.json()["answer"]
