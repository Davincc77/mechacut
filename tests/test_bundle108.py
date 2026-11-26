# -*- coding: utf-8 -*-
"""Bundle 108 — /shop/withdrawal entre au LUXEMBOURG et à la BELGIQUE :
mêmes mots, AUTRES grammaires. Le gate (25-11, 04h50-05h20) a paye
cinq sources primaires ET corrige deux citations de la file : la
retractation LU est L. 221-3 + L. 222-9 (pas le 1251-19, numero
abroge en 2014) ; la belge est VI.47-VI.53 (pas VI.25, l'article des
SOLDES, deja joue par la soeur soldes-be).

Golds traces À LA MAIN sur l'oracle separe g108 (scratch/
oracle_g108.py — calendrier LU/BE RECOPIES des tableaux officiels
ITM/SPF Emploi, ecrit AVANT le module, jamais importe de lui).
Sens habituel : le test suit l'oracle ; si la machine contredit, on
verifie DEUX FOIS qui a raison.

Les vecteurs croises (un jour de reception, trois pays) — verifie
calendrier 2025-2028 :
  v1 recu mardi 2026-11-24 : CONVERGENCE honnete, les trois rendent
     mardi 2026-12-08 (le verbatim BEE SECURE ne divise pas).
  v2 recu samedi 2026-11-28 : brut 2026-12-12 SAMEDI — FR avance au
     lundi 14, BE avance au lundi 14 (I.7 par. 3 exclut le samedi),
     LU RESTE samedi 12 (ouvrable = lundi-samedi, glossaire guichet).
  v3 recu mardi 2026-06-09 : brut 2026-06-23 — fete NATIONALE LU
     (pas FR ni BE) : LU rend 2026-06-24, FR/BE gardent 2026-06-23.
  v4 recu mercredi 2026-10-28 : brut 2026-11-11 — armistice FR/BE,
     ABSENT de la liste LU : FR/BE rendent 2026-11-12, LU garde
     2026-11-11. La divergence marche dans les DEUX sens.
  v5 recu vendredi 2025-12-12 : brut 2025-12-26 VENDREDI —
     Saint-Etienne (2e jour de Noel) n'existe qu'en LU : LU rend
     2025-12-27 (samedi — ouvrable LU, la chaine s'arrete la),
     FR/BE gardent 2025-12-26.
  v6 recu mardi 2028-04-25 : brut 2028-05-09 — Journee de l'Europe
     (loi du 25 avril 2019, LU seul pays UE) : LU rend 2028-05-10,
     FR/BE gardent 2028-05-09.
  v8 notifie mardi 2026-07-07 (delai 2026-07-08) : +14 = 2026-07-21
     — fete nationale BE seulement : BE reporte ses SECONDES horloges
     au 2026-07-22 (I.7 par. 4 vise toute prestation), FR/LU rendent
     2026-07-21 brut (divergence NOMMEE, pas moyennee).
  v8b notifie samedi 2026-06-27 : +14 = 2026-07-11 SAMEDI — FR/LU
     rendent le samedi BRUT (seconde horloge), BE reporte au lundi 13.
  v9 info tardive samedi 2027-05-29 : redemarrage +14 = 2027-06-12
     SAMEDI — FR/BE au lundi 14, LU reste au samedi 12.
  v10 recu 2028-02-15, info manquante : brut 2028-02-29 (mardi,
     bissextile), +12 MOIS CLAMPE 2029-02-28 — la convention des
     soeurs, trois fois.
  v11 service conclu vendredi 2026-04-17 : brut 2026-05-01 ferie
     PARTOUT — FR/BE poussent samedi+dimanche jusqu'au LUNDI 4, LU
     s'arrete au SAMEDI 2 (ouvrable). Trois departements, trois
     pays, trois reponses.
"""
import json

from fastapi.testclient import TestClient

import main

main.RATE_LIMIT = 10 ** 9
client = TestClient(main.app)


def post(body):
    return client.post("/api/v1/shop/withdrawal", json=body)


# --------------------------------------------------- la convergence
# verbatim : le meme colis ne DIVISE pas ce jour-la, et le module le
# dit — il ne fabrique pas une divergence quand le texte n'en donne
# aucune.


def test_v1_three_countries_one_date():
    for c in ("fr", "lu", "be"):
        r = post({"start_date": "2026-11-24", "country": c})
        assert r.status_code == 200
        b = r.json()
        assert b["deadline"] == "2026-12-08", c
        assert b["deadline_weekday"] == "Tuesday", c
        assert b["extension_applied"] is False, c
        assert b["country"] == c.upper()


# ------------------------------------------- la divergence du samedi
# LE produit entier tient dans ce test : meme echeance brute, le LU
# garde le samedi, le FR et le BE l'avancent.


def test_v2_saturday_lu_survives_fr_be_advance():
    got = {}
    for c in ("fr", "lu", "be"):
        b = post({"start_date": "2026-11-28", "country": c,
                  "as_of": "2026-12-10"}).json()
        got[c] = b
        assert b["deadline_initial"] == "2026-12-12"
        assert b["deadline_initial_weekday"] == "Saturday"
    assert got["fr"]["deadline"] == "2026-12-14"
    assert got["be"]["deadline"] == "2026-12-14"
    assert got["lu"]["deadline"] == "2026-12-12"      # reste un samedi
    assert [x["reason"] for x in got["fr"]["extension_chain"]] == \
        ["Saturday", "Sunday"]
    assert [x["reason"] for x in got["be"]["extension_chain"]] == \
        ["Saturday", "Sunday"]
    assert got["lu"]["extension_chain"] == []
    assert got["lu"]["extension_applied"] is False
    # as_of VENDREDI 2026-12-10 : LU ouvre 2 jours, FR et BE 4 —
    # memes mots, pas la meme date limite.
    assert got["lu"]["days_left"] == 2
    assert got["fr"]["days_left"] == 4
    assert got["be"]["days_left"] == 4


def test_v2_lu_final_day_is_a_saturday():
    b = post({"start_date": "2026-11-28", "country": "lu",
              "as_of": "2026-12-12"}).json()
    assert b["verdict"] == "FINAL_DAY"
    assert b["days_left"] == 0
    assert b["deadline_weekday"] == "Saturday"


# ----------------------------------------- fete nationale LU (23 juin)


def test_v3_lu_national_day_moves_lu_only():
    for c, want in (("fr", "2026-06-23"), ("be", "2026-06-23"),
                    ("lu", "2026-06-24")):
        b = post({"start_date": "2026-06-09", "country": c}).json()
        assert b["deadline"] == want, c
    lu = post({"start_date": "2026-06-09", "country": "lu"}).json()
    assert "Grand-Duc" in lu["extension_chain"][0]["reason"]
    assert "COTRAV L. 232-6" in lu["extension_chain"][0]["reason"]


# ------------------------------------------ armistice absent du LU


def test_v4_armistice_fr_be_not_lu():
    for c, want in (("fr", "2026-11-12"), ("be", "2026-11-12"),
                    ("lu", "2026-11-11")):
        b = post({"start_date": "2026-10-28", "country": c}).json()
        assert b["deadline"] == want, c


# -------------------------------------- Saint-Etienne, 2e jour LU


def test_v5_st_stephane_lu_only():
    for c, want in (("fr", "2025-12-26"), ("be", "2025-12-26"),
                    ("lu", "2025-12-27")):
        b = post({"start_date": "2025-12-12", "country": c}).json()
        assert b["deadline"] == want, c
    lu = post({"start_date": "2025-12-12", "country": "lu"}).json()
    assert lu["deadline_weekday"] == "Saturday"   # la chaine s'arrete
    assert lu["extension_chain"][0]["reason"].startswith("holiday:")


# ------------------------------------ Journee de l'Europe, 9 mai LU


def test_v6_europe_day_lu_2028():
    for c, want in (("fr", "2028-05-09"), ("be", "2028-05-09"),
                    ("lu", "2028-05-10")):
        b = post({"start_date": "2028-04-25", "country": c}).json()
        assert b["deadline"] == want, c
    lu = post({"start_date": "2028-04-25", "country": "lu"}).json()
    assert "25 avril 2019" in lu["extension_chain"][0]["reason"]


def test_v7_ascension_moves_everywhere():
    for c in ("fr", "lu", "be"):
        b = post({"start_date": "2026-05-11", "country": c}).json()
        assert b["deadline"] == "2026-05-26", c   # Ascension 14 mai


# --------------------------------------------- secondes horloges


def test_v8_be_second_clock_advances_fr_lu_raw():
    for c, want in (("fr", "2026-07-21"), ("lu", "2026-07-21"),
                    ("be", "2026-07-22")):
        b = post({"start_date": "2026-06-24", "country": c,
                  "notified": "2026-07-07"}).json()
        assert b["return_by"] == want, c
        assert b["refund_by"] == want, c


def test_v8b_be_second_clock_saturday():
    for c, want in (("fr", "2026-07-11"), ("lu", "2026-07-11"),
                    ("be", "2026-07-13")):
        b = post({"start_date": "2026-06-20", "country": c,
                  "notified": "2026-06-27"}).json()
        assert b["return_by"] == want, c


# ------------------------------------------------- info tardive


def test_v9_restart_saturday_three_grammars():
    for c, want in (("fr", "2027-06-14"), ("be", "2027-06-14"),
                    ("lu", "2027-06-12")):
        b = post({"start_date": "2026-12-15", "country": c,
                  "info_date": "2027-05-29"}).json()
        assert b["restarted_deadline"] == want, c
        assert b["final_deadline"] == want, c
        src = {"fr": "L221-20 al. 2", "lu": "L. 222-9 (4)",
               "be": "VI.48 al. 2"}[c]
        assert b["final_deadline_source"].startswith(src), c


def test_v10_leap_clamp_three_countries():
    for c in ("fr", "lu", "be"):
        b = post({"start_date": "2028-02-15", "country": c,
                  "info_missing": True}).json()
        assert b["deadline_initial"] == "2028-02-29", c
        assert b["extended_12m"] == "2029-02-28", c
        assert b["final_deadline"] == "2029-02-28", c


def test_v11_may_first_three_answers():
    for c, want in (("fr", "2026-05-04"), ("be", "2026-05-04"),
                    ("lu", "2026-05-02")):
        b = post({"start_date": "2026-04-17", "country": c,
                  "kind": "services"}).json()
        assert b["deadline"] == want, c


# -------------------------------------------------- exceptions


def test_lu_thirteen_classes_lettered():
    b = post({"start_date": "2026-11-24", "country": "lu",
              "product_class": "made_to_order"}).json()
    assert b["exception"]["article"] == "L. 222-9 (7) c)"
    assert b["verdict"] == "NOT_WITHDRAWABLE"


def test_be_fourteenth_class_exists_only_in_belgium():
    b = post({"start_date": "2026-11-24", "country": "be",
              "product_class": "betting_lottery"}).json()
    assert b["exception"]["article"] == "VI.53 14°"
    assert "paris" in b["exception"]["clause"]
    assert b["verdict"] == "NOT_WITHDRAWABLE"
    for c in ("fr", "lu"):
        r = post({"start_date": "2026-11-24", "country": c,
                  "product_class": "betting_lottery"})
        assert r.status_code == 400, c
        e = r.json()["errors"][0]
        assert e["field"] == "product_class"
        assert "betting_lottery" not in e["expected"]


# --------------------------------------------------- refus nommes


def test_in_store_refused_in_all_three_carries_own_statute():
    for c, needle in (("fr", "démarchage"), ("lu", "BEE SECURE"),
                      ("be", "VI.67")):
        r = post({"start_date": "2026-11-24", "country": c,
                  "kind": "in_store"})
        assert r.status_code == 400, c
        assert needle in r.json()["errors"][0]["message"]


def test_uk_and_br_refused_by_name_carrying_facts():
    r = post({"start_date": "2026-11-24", "country": "uk"})
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert e["expected"] == "fr | be | lu"
    assert "CCA 2015" in e["message"]
    r = post({"start_date": "2026-11-24", "country": "br"})
    assert r.status_code == 400
    assert "CDC art. 49" in r.json()["errors"][0]["message"]
    assert "SEVEN" in r.json()["errors"][0]["message"]


def test_lu_clock_text_is_replayed_not_recalled():
    b = post({"start_date": "2026-11-28", "country": "lu"}).json()
    # le texte porte l'article ET la source de la definition —
    # jamais une date inventee, jamais une prose de memoire
    assert "L. 221-3" in b["clock"]["text"]
    assert "SAMEDI EST OUVRABLE" in b["clock"]["text"]
    assert "glossaire" in b["clock"]["text"]
    b = post({"start_date": "2026-11-28", "country": "be"}).json()
    assert "I.7" in b["clock"]["text"]
    assert "lendemain" in b["clock"]["text"]


# ---------------------------------------------- la table des feries


def test_holidays_lu_2026_is_the_itm_table():
    r = client.post("/api/v1/schedule/holidays",
                    json={"country": "lu", "year": 2026})
    assert r.status_code == 200
    b = r.json()
    assert b["count"] == 11
    dates = [x["date"] for x in b["holidays"]]
    assert dates == ["2026-01-01", "2026-04-06", "2026-05-01",
                     "2026-05-09", "2026-05-14", "2026-05-25",
                     "2026-06-23", "2026-08-15", "2026-11-01",
                     "2026-12-25", "2026-12-26"]   # ITM, recopie


def test_holidays_be_2026_is_the_spf_list():
    b = client.post("/api/v1/schedule/holidays",
                    json={"country": "be", "year": 2026}).json()
    assert b["count"] == 10
    dates = [x["date"] for x in b["holidays"]]
    assert dates == ["2026-01-01", "2026-04-06", "2026-05-01",
                     "2026-05-14", "2026-05-25", "2026-07-21",
                     "2026-08-15", "2026-11-01", "2026-11-11",
                     "2026-12-25"]   # liste SPF Emploi, recopiee
    assert "2026-12-26" not in dates  # Saint-Etienne n'est pas belge


def test_is_holiday_verdicts_cross_country():
    # le meme jour : ferie en LU, pas en FR ni BE — et l'inverse
    r = client.post("/api/v1/schedule/holidays",
                    json={"country": "lu", "on": "2026-06-23"})
    assert r.json()["is_holiday"] is True
    for c in ("fr", "be"):
        r = client.post("/api/v1/schedule/holidays",
                        json={"country": c, "on": "2026-06-23"})
        assert r.json()["is_holiday"] is False, c
    r = client.post("/api/v1/schedule/holidays",
                    json={"country": "be", "on": "2026-11-11"})
    assert r.json()["is_holiday"] is True
    r = client.post("/api/v1/schedule/holidays",
                    json={"country": "lu", "on": "2026-11-11"})
    assert r.json()["is_holiday"] is False
    r = client.post("/api/v1/schedule/holidays",
                    json={"country": "be", "on": "2026-12-26"})
    assert r.json()["is_holiday"] is False   # ni BE ni FR


def test_holidays_closed_set_names_the_new_states():
    r = client.post("/api/v1/schedule/holidays",
                    json={"country": "nl", "year": 2026})
    assert r.status_code == 400
    assert "FR BE LU BR PT DE US" in r.json()["errors"][0]["message"]


# ------------------------------------------------------ le routeur


def test_router_lu_be_named_route_the_tool():
    for q in ("rétractation colis luxembourg jusqu'à quand",
              "j'ai reçu un colis en Belgique, jusqu'où changer "
              "d'avis",
              "withdrawal belgium parcel received saturday"):
        tools = client.get("/route?q=" + q).json()["tools"]
        assert tools and tools[0]["tool"] == "shop_withdrawal", q


def test_router_fr_needles_untouched_and_guards_hold():
    # b107 : les trois langues du verbatim gardent leur top1
    for q in ("colis reçu mardi — jusqu'à quelle date exacte puis-je "
              "me rétracter, samedi et jours fériés comptés ?",
              "parcel arrived tuesday — until when can I withdraw "
              "from the online order",
              "até quando posso desistir da compra — encomenda "
              "recebida terça"):
        tools = client.get("/route?q=" + q).json()["tools"]
        assert tools[0]["tool"] == "shop_withdrawal", q
    # b105 : « soldes belgique » reste CHEZ LA SOEUR soldes-be
    for q in ("soldes belgique 2027 quand commencent",
              "quand commencent les soldes en belgique"):
        tools = client.get("/route?q=" + q).json()["tools"]
        assert tools[0]["tool"] == "shop_soldes_be", q
    # veto : un pays SANS table tue toujours
    for q in ("can I still withdraw, bought it in England",
              "rétractation suisse délai",
              "rétractation d'un achat immobilier signé chez le "
              "notaire",
              "raconte-moi une blague sur la rétractation"):
        tools = client.get("/route?q=" + q).json()["tools"]
        assert not tools or all(
            t["tool"] != "shop_withdrawal" for t in tools), q


# ------------------------------------------------------- pins & or

def test_ten_new_pins_are_replayable():
    g = json.loads(open("golden.json", encoding="utf-8").read())
    if "pins" in g:
        g = g["pins"]
    for name in (
            "shop_withdrawal_lu_saturday_pin",
            "shop_withdrawal_be_saturday_pin",
            "shop_withdrawal_lu_national_day_pin",
            "shop_withdrawal_be_armistice_pin",
            "shop_withdrawal_lu_ststephane_pin",
            "shop_withdrawal_lu_europe2028_pin",
            "shop_withdrawal_be_second_clock_pin",
            "shop_withdrawal_be_betting_pin",
            "schedule_holidays_lu_2026_pin",
            "schedule_holidays_be_2026_pin"):
        assert name in g, name
    # le pin REMPLACÉ (b107 refus BE -> b108 calcul BE) a change de
    # contrat PAR CONCEPTION, gate paye ; il n'est pas efface.
    assert g["shop_withdrawal_be_refuse_pin"].startswith("200:")
    # 331 pins vivants + 10 neufs, adds-only : RIEN perdu.
    # b109 relève ce total global : 341 + 3 dialectes neufs (adds-
    # only, la pin V23 remplacee PAR CONCEPTION comme celle de b108).
    # b110 relève à 355 : +11 pins soldes-lu (adds-only, zero retiree ;
    # la pin shop_soldesbe_luxembourg_refuse REMPLACEE par contrat
    # change — le pointeur « en file » devient « vivent sous », gate
    # paye 25-11, consigne dans le message du commit).
    # b111 relève à 364 : +9 agent_tooloverlap (adds-only, zero retirée,
    # vecteurs publics — le contrat des sœurs n'a pas bougé d'un octet).
    # b112 relève à 374 : +10 invoice_payment_due (adds-only, vecteurs
    # de l'oracle g112 — les dates viennent des actes lus, pas du vent).
    # b114 relève à 392 : +9 json_bigint (adds-only, vecteurs publics
    # Unity/claude/llm4s/ragflow/x402) ; b113 relève à 383 : +9 agent_mcplist (adds-only, vecteurs
    # PUBLICS — #6935, codex, claude-web, vercel).
    # b115 relève à 400 : +8 money_settle (adds-only, vecteurs du
    # fil r/askmath) ; b114 relève à 392 : +9 json_bigint
    # b116 relève à 410 : +10 agent_resultcliff (adds-only, la
    # b117 relève à 415 : +5 money_settle noncash (adds-only)
    # b118 relève à 418 : +3 agent_resultcliff onyx (adds-only, le
    # vecteur #16312 843719−2032226 rejoué, le refus nommé, la
    # frontière marge 0)
    # matrice #97622 rejouée, les portes codex/bionic/rakazo/vscode,
    # la notice hermes calculée à la main, le mode all-rows).
    assert len(g) == 418


def test_fr_response_byte_contract():
    # la reponse FR n'a PAS bouge d'un octet : ni champ neuf, ni
    # chaine retouchee (le contrat golden des 8 pins FR)
    b = post({"start_date": "2026-11-24", "as_of": "2026-11-25"}).json()
    assert "grammar_note" not in b
    assert b["final_deadline_source"] == "L221-18 + L221-19"
    assert b["clock"]["article"] == "L221-19"
    assert len(b["conditions"]) == 7
