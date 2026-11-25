# -*- coding: utf-8 -*-
"""Bundle 107 — /shop/withdrawal : la rétractation légale française en
DATES, pas en prose. Section 6 (L221-18 à L221-28) rejouée VERBATIM
legifrance (snapshot web.archive 2025-03-09, concordance live 25-11),
fiches service-public F10485/F11094 rejouées.

Golds tracés À LA MAIN sur l'oracle séparé g107 (scratch/
oracle_g107.py — datetime + calendrier FR RECOPié à la main des lignes
L3133-1, écrit AVANT withdrawalkit.py, jamais importé du module).
Sens habituel : le test suit l'oracle ; si la machine contredit, on
vérifie DEUX FOIS qui a raison.

Tracés principaux (jours vérifiés à la main sur le calendrier 2026-29) :
  v1 reçu 2026-11-24 (mardi) -> day1 25, échéance brute 2026-12-08
     mardi, aucune avancée, deadline 2026-12-08.
  v2 reçu 2026-11-21 (samedi) -> brut 2026-12-05 SAMEDI -> 26 dim ->
     2026-12-07 lundi, chain [Saturday, Sunday].
  v3 reçu 2026-04-24 (vendredi) -> brut 2026-05-08 VENDREDI =
     Victoire 1945 (L3133-1 4°) -> 09 sam, 10 dim -> 2026-05-11
     lundi ; la chain cite la LOI de chaque férié.
  v4 services conclu 2026-11-17 -> deadline 2026-12-01 ; notifié
     2026-12-01 -> return_by = refund_by = 2026-12-15 (mardi) —
     secondes horloges SANS avancée : divergence NOMMÉE.
  v5 info manquante, reçu 2026-01-15 -> deadline 2026-01-29, +12 m
     -> 2027-01-29, final = extended_12m (L221-20 al. 1).
  v6 info tardive 2026-05-30 (samedi) -> brut 2026-06-13 SAMEDI ->
     2026-06-15 lundi ; final = restarted (L221-20 al. 2).
  v11 reçu 2028-02-15 -> brut 2028-02-29 (BISSEXTILE, mardi) ->
     +12 m CLAMPÉ 2029-02-28 — la convention des sœurs.
  v13 reçu 2026-12-11 -> brut 2026-12-25 = Noël (L3133-1 11°) ->
     26 sam -> 27 dim -> 2026-12-28 lundi, chain de TROIS jours.
  as_of 2026-12-01/08/09 sur v1 -> OPEN 7, FINAL_DAY 0, EXPIRED -1.
"""
import hashlib
import json
from datetime import date

import pytest
from fastapi.testclient import TestClient

import main
import withdrawalkit as k

main.RATE_LIMIT = 10 ** 9
client = TestClient(main.app)


def post(body):
    return client.post("/api/v1/shop/withdrawal", json=body)


# ---------------------------------------------------- les horloges


def test_v1_goods_plain():
    r = post({"start_date": "2026-11-24"})
    assert r.status_code == 200
    b = r.json()
    assert b["day1"] == "2026-11-25"
    assert b["deadline_initial"] == "2026-12-08"
    assert b["deadline_initial_weekday"] == "Tuesday"
    assert b["deadline"] == "2026-12-08"
    assert b["extension_applied"] is False
    assert b["extension_chain"] == []
    assert b["start_weekday"] == "Tuesday"


def test_v2_saturday_expiry_advances():
    b = post({"start_date": "2026-11-21"}).json()
    assert b["deadline_initial"] == "2026-12-05"
    assert [c["reason"] for c in b["extension_chain"]] == [
        "Saturday", "Sunday"]
    assert b["deadline"] == "2026-12-07"
    assert b["deadline_weekday"] == "Monday"
    assert b["extension_applied"] is True


def test_v3_holiday_chain_names_the_law():
    b = post({"start_date": "2026-04-24"}).json()
    assert b["deadline_initial"] == "2026-05-08"
    chain = b["extension_chain"]
    assert chain[0]["reason"].startswith("holiday: Victoire 1945")
    assert "L3133-1 4°" in chain[0]["reason"]
    assert [c["reason"].split(" (")[0] for c in chain] == [
        "holiday: Victoire 1945", "Saturday", "Sunday"]
    assert b["deadline"] == "2026-05-11"


def test_v4_services_notified_second_clocks():
    b = post({"start_date": "2026-11-17", "kind": "services",
              "notified": "2026-12-01"}).json()
    assert b["deadline"] == "2026-12-01"
    assert b["start_rule"]["article"] == "L221-18 1°"
    # 14 JOURS CALENDAIRES sans avancée : 2026-12-15 tombe un MARDI
    # (l'absence d'avancée est un choix tracé, pas un accident)
    assert b["return_by"] == "2026-12-15"
    assert b["refund_by"] == "2026-12-15"
    assert any("WITHOUT weekend extension" in c for c in b["conditions"])
    assert b["final_deadline"] == "2026-12-01"


def test_v5_info_missing_twelve_months():
    b = post({"start_date": "2026-01-15", "info_missing": True}).json()
    assert b["deadline"] == "2026-01-29"
    assert b["extended_12m"] == "2027-01-29"
    assert b["final_deadline"] == "2027-01-29"
    assert "L221-20 al. 1" in b["final_deadline_source"]


def test_v6_late_info_restarts_fourteen_days():
    b = post({"start_date": "2026-01-15", "info_date": "2026-05-30"}).json()
    assert b["info_missing"] is True          # info_date l'implique
    assert b["restarted_deadline"] == "2026-06-15"   # 13 sam -> 15 lun
    assert [c["reason"] for c in b["restarted_extension"]] == [
        "Saturday", "Sunday"]
    assert b["final_deadline"] == "2026-06-15"
    assert "L221-20 al. 2" in b["final_deadline_source"]
    assert b["extended_12m"] == "2027-01-29"  # le plafond voyage aussi


def test_v6b_info_after_the_prolongation():
    b = post({"start_date": "2026-01-15", "info_missing": True,
              "info_date": "2027-06-01"}).json()
    assert b["restarted_deadline"] is None
    assert b["final_deadline"] == "2027-01-29"
    assert "AFTER the twelve-month" in b["final_deadline_source"]


def test_v8_off_premises_starts_at_conclusion():
    b = post({"start_date": "2026-11-18", "kind": "off_premises"}).json()
    assert b["deadline"] == "2026-12-02"
    assert "hors établissement" in b["start_rule"]["text"]
    assert b["start_rule"]["article"] == "L221-18 2° (alinéa 2)"


def test_v9_subscriptions_first_good():
    b = post({"start_date": "2026-09-03", "kind": "subscriptions"}).json()
    assert b["deadline"] == "2026-09-17"
    assert "premier bien" in b["start_rule"]["text"]


def test_v11_leap_february_clamps():
    b = post({"start_date": "2028-02-15", "info_missing": True}).json()
    assert b["deadline_initial"] == "2028-02-29"   # 2028 bissextile
    assert b["deadline"] == "2028-02-29"           # mardi, aucun férié
    assert b["extended_12m"] == "2029-02-28"       # CLAMP fin de mois
    # concordance avec la sœur : même convention que dates.py
    from datetime import datetime
    from dates import _add_calendar
    assert _add_calendar(datetime(2028, 2, 29),
                         months=12).isoformat()[:10] == "2029-02-28"


def test_v13_christmas_three_day_chain():
    b = post({"start_date": "2026-12-11"}).json()
    assert b["deadline_initial"] == "2026-12-25"
    assert [c["reason"].split(" (")[0] for c in b["extension_chain"]] == [
        "holiday: Noël", "Saturday", "Sunday"]
    assert "L3133-1 11°" in b["extension_chain"][0]["reason"]
    assert b["deadline"] == "2026-12-28"


# ---------------------------------------------------- verdicts


@pytest.mark.parametrize("asof,verdict,left", [
    ("2026-12-01", "OPEN", 7),
    ("2026-12-08", "FINAL_DAY", 0),
    ("2026-12-09", "EXPIRED", -1),
])
def test_as_of_verdicts(asof, verdict, left):
    b = post({"start_date": "2026-11-24", "as_of": asof}).json()
    assert b["verdict"] == verdict
    assert b["days_left"] == left


def test_no_as_of_never_reads_the_clock():
    b = post({"start_date": "2026-11-24"}).json()
    assert b["as_of"] is None and b["days_left"] is None
    assert b["verdict"].startswith("UNDATED")


def test_final_day_is_still_open():
    # L221-19 2° : « à l'expiration de la DERNIÈRE HEURE du dernier
    # jour » — le jour même n'est pas périmé, c'est FINAL_DAY
    b = post({"start_date": "2026-11-21", "as_of": "2026-12-07"}).json()
    assert b["verdict"] == "FINAL_DAY" and b["days_left"] == 0


# ---------------------------------------------------- exceptions


def test_exception_made_to_order_verbatim():
    b = post({"start_date": "2026-11-24", "as_of": "2026-11-30",
              "product_class": "made_to_order"}).json()
    e = b["exception"]
    assert e["article"] == "L221-28 3°"
    assert "confectionnés selon les spécifications" in e["clause"]
    assert b["verdict"] == "NOT_WITHDRAWABLE"
    assert b["days_left"] is None
    # les dates voyagent QUAND MÊME : exclure n'est pas effacer
    assert b["deadline"] == "2026-12-08"


def test_exception_press_keeps_its_sauf():
    b = post({"start_date": "2026-11-24",
              "product_class": "press_daily"}).json()
    assert "sauf pour les contrats d'abonnement" in \
        b["exception"]["clause"]
    assert "ABONNEMENT" in b["exception"]["note"]


def test_exception_table_is_closed_at_thirteen():
    assert len(k.EXCEPTIONS) == 13
    nums = sorted(v[0] for v in k.EXCEPTIONS.values())
    assert nums == list(range(1, 14))   # L221-28 : 1° à 13°, complet


def test_unknown_class_refused_by_name():
    r = post({"start_date": "2026-11-24", "product_class": "voiture"})
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert e["field"] == "product_class"
    assert "alcohol_delayed" in e["expected"]   # les 13 sont listés


# ---------------------------------------------------- refus


def test_refuse_other_country_named():
    r = post({"start_date": "2026-11-24", "country": "be"})
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert e["field"] == "country" and e["expected"] == "fr"
    assert "1182" not in e["message"]           # pas de prose de mémoire
    assert "CDC art. 49" in e["message"]        # le BR est NOMMÉ


def test_refuse_in_store_carries_the_statute():
    r = post({"start_date": "2026-11-24", "kind": "in_store"})
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert "à distance, à la suite d'un démarchage " \
           "téléphonique ou hors établissement" in e["message"]
    assert "return-deadline" in e["message"]    # la frontière rendue


def test_refuse_unknown_kind():
    r = post({"start_date": "2026-11-24", "kind": "location"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "kind"


def test_refuse_inverted_notified():
    r = post({"start_date": "2026-11-24", "notified": "2026-11-01"})
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert e["field"] == "notified"
    assert "inverted" in e["message"]


def test_notified_inside_the_prolongation_is_legal():
    # L221-20 : le droit court 12 mois de plus — notifier DANS cette
    # fenêtre est légal, le refuser serait inventer une clôture
    b = post({"start_date": "2026-01-15", "info_missing": True,
              "notified": "2026-06-01"})
    assert b.status_code == 200
    j = b.json()
    assert j["return_by"] == "2026-06-15" and j["refund_by"] == "2026-06-15"


def test_notified_after_final_deadline_refused():
    r = post({"start_date": "2026-11-24", "notified": "2026-12-09"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "notified"


def test_refuse_bad_and_out_of_range_dates():
    for body in ({"start_date": "2026-02-30"},
                 {"start_date": "2026-11-24", "as_of": "2100-01-01"},
                 {"start_date": "mardi"}):
        r = post(body)
        assert r.status_code == 400, body


def test_extra_field_is_refused():
    r = post({"start_date": "2026-11-24", "refund_wanted": True})
    assert r.status_code == 400


# ---------------------------------------------------- contrat


def test_clock_travels_verbatim_with_its_anchor():
    b = post({"start_date": "2026-11-24"}).json()
    t = b["clock"]["text"]
    assert "règlement n° 1182/71/CEE" in t
    assert "n'est pas compté" in t
    assert "dernière heure du dernier jour" in t
    assert "premier jour ouvrable suivant" in t
    assert "1182/71" in b["clock"]["anchor"]


def test_provenance_names_the_replay():
    b = post({"start_date": "2026-11-24"}).json()
    p = b["provenance"]
    assert "LEGISCTA000032221365" in p["code"]
    assert "2025-03-09" in p["rejoue"] and "25-Nov-2026" in p["rejoue"]
    assert "F10485" in p["official_fiches"] and "F11094" in \
        p["official_fiches"]
    assert "L3133-1" in p["sister_table"]


def test_sha256_is_the_canon_of_the_body():
    b = post({"start_date": "2026-11-24"}).json()
    claimed = b.pop("sha256")
    blob = json.dumps(b, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode()
    assert hashlib.sha256(blob).hexdigest() == claimed


def test_determinism_same_bytes_forever():
    a = post({"start_date": "2026-12-11"}).json()["sha256"]
    b = post({"start_date": "2026-12-11"}).json()["sha256"]
    assert a == b


# ---------------------------------------------------- routeur


def test_needles_top1_x3_langues():
    for q in ("i received my online order last tuesday — until when "
              "can i change my mind",
              "colis reçu le 20 novembre, jusqu'à quand puis-je me "
              "rétracter",
              "comprei pela internet na frança, até quando vai meu "
              "prazo de retratação",
              "rétractation 14 jours achat à distance date limite",
              "14 day withdrawal deadline holiday advance received"):
        r = client.get("/route", params={"q": q}).json()
        assert r["tools"], q
        assert r["tools"][0]["tool"] == "shop_withdrawal", q


def test_foreign_jurisdictions_die_before_promising():
    for q in ("me arrependi da compra no brasil 7 dias prazo",
              "14 day cooling off period in belgium online order",
              "withdrawal right luxembourg distance selling"):
        names = [t["tool"] for t in
                 client.get("/route", params={"q": q}).json()["tools"]]
        assert "shop_withdrawal" not in names, q


def test_sisters_gardent_leurs_aiguilles():
    for q, want in (
            ("jusqu'à quelle date peut-on encore retourner un cadeau "
             "de Noël acheté à la Fnac", "shop_return_deadline"),
            ("la garantie légale sur un produit défectueux court "
             "jusqu'à quand", "shop_legal_guarantee"),
            ("quand commencent les soldes en belgique",
             "shop_soldes_be")):
        r = client.get("/route", params={"q": q}).json()
        assert r["tools"][0]["tool"] == want, q


def test_bouilloire_meurt_vide():
    names = [t["tool"] for t in client.get(
        "/route", params={"q": "jusqu'à quand je peux retourner ma "
                               "bouilloire au magasin"}).json()["tools"]]
    assert "shop_withdrawal" not in names


# ---------------------------------------------------- vitrine


def test_manifest_carries_the_row():
    body = client.get("/agent/manifest").text
    assert "/api/v1/shop/withdrawal" in body


def test_tool_card_exists():
    r = client.get("/tools/shop_withdrawal.json")
    assert r.status_code == 200
    b = r.json()
    assert b["tier"] == "free"
    for lang in ("en", "fr", "pt"):
        assert b["try"]["say"][lang]
