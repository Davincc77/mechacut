# -*- coding: utf-8 -*-
"""Bundle 112 — /invoice/payment-due : LA VRAIE ÉCHÉANCE + les
QUATRE LECTURES d'un « Net 30 », le report NOMMÉ par juridiction, la
couche TARGET2 où le rail ferme sans décaler la dette.

Golds tracés À LA MAIN sur l'oracle séparé g112 (scratch/
g112_oracle.py + scratch/g112_check.py, écrits AVANT paymentduekit.py —
jamais importés du module). Sens habituel : le test suit l'oracle ;
ici la machine a eu raison DEUX FOIS avant le build et l'oracle a été
corrigé DEUX FOIS, consigné dans la file : 1) le 25-déc lui-même
oublié du jeu de fermetures TARGET à la passe 1 ; 2) l'oubli
d'ASCENSION (14-mai-2026, férie MOBILE) dans le count 30-ouvres —
la main disait 12-juin, la table sourcée L3133-1 dit 17. Et le gate a
CORRIGÉ LA CITATION DE LA FILE : l'art. 1343 du code civil est la
libération au NOMINAL, pas un texte de report — la France facture est
le pays de la TABLE VIDE (1342-1343-5 lus ; anciens 1235-1244-1
abrogés ord. 2016-131 ; la loi 1925 des effets abrogée 2007). Le vide
est un VERDICT rendu, pas une absence de réponse — la clause décide.

Vecteurs :
  V1 dimanche 2026-05-31 (issue 1-mai + 30) : FR reste (31), DE ->
     1-juin par § 193, GB reste, lettre de change FR -> 1-juin.
  V2 SAMEDI 2026-06-06 : FR reste, DE -> 8 (2 jours), GB reste —
     LA divergence Saturday qui faisait l'item de la file, chiffrée.
  V3 GB worked 30 = 16-juin vs plain lundi–vendredi = 12-juin :
     +4 jours = les deux bank holidays anglais de mai (4, 25), le
     vecteur workingdayscalculator reproduit.
  V3b FR : 30 ouvrables (L. 3133-1, samedi COMPTE) = 9-juin vs 30
     ouvrés = 17-juin — HUIT jours dans le même pays sur le même
     mot ; c'est la clause « business days » du client de r/
     Contractor, rendue en nombres.
  V4 DGCCRF exemple d'ÉTAT rejoué : 45 j fin de mois, facture du
     10-mars -> 30-avr (45 puis fin de mois) contre 15-mai (fin de
     mois puis 45) : 15 jours d'écart ADMIS par l'administration.
  V5 Noël 2026 : due vendredi 25-déc. FR facture RESTE au 25 (vide
     lu) ; FR lettre de change -> SAMEDI 26 (jour OUVRABLE, samedi
     compte — l'atterrissage n'est pas un workday) ; DE -> 28 ;
     GB -> 29 (chaîne 26 samedi holiday par Schedule 1 + 28
     substitut proclamé) ; settlement : settle 28, interest dès le
     26 (directive 2011/7 art. 3, lu).
  V6 absorption : 2027-05-01 = samedi + fermeture TARGET : zéro jour
     de plus que le week-end, closing ABSORBÉE nommée ; DE -> 3.
  TABLE gate : gb hors 2026-2028 -> refus NOMMÉ « proclaimed, not
     predicted » (doctrine b110 pas-d'acte-pas-de-date, et la
     ligne FR/DE vit quand même : la divergence reste rendue).
  day-0 : les QUATRE exemples de blogs épinglés (1-mars->31-mars,
     1-avr->1-mai, 1-juil->31-juil, 1-aoû->31-aoû).
  plafond L. 441-10 : net 90 -> OVER_L441_10 ; le mode eom N'EST PAS
     flaggé (la dérogation 45-fin-de-mois dépasse 60 PAR LA LOI).
"""
import hashlib
import json

import pytest
from fastapi.testclient import TestClient

import main
import paymentduekit as k

client = TestClient(main.app)
main.RATE_LIMIT = 10**9


# ------------------------------------------------------- conventions
def test_a1_day0_pins_quatre_exemples_publies():
    # invoice-generator / upflow / bluevine / resolvepay, phrases lues
    for iss, want in (("2026-03-01", "2026-03-31"),
                      ("2026-04-01", "2026-05-01"),
                      ("2026-07-01", "2026-07-31"),
                      ("2026-08-01", "2026-08-31")):
        out = k.payment_due(iss, "net 30")
        got = [r for r in out["readings"]
               if r["reading"] == "calendar_issue"][0]
        assert got["due"] == want, (iss, got)


def test_a2_anchor_receipt_nommee():
    out = k.payment_due("2026-05-01", "net 30",
                        receipt_date="2026-05-05",
                        count_from="receipt")
    w = {r["reading"]: r for r in out["readings"]}
    assert w["calendar_receipt"]["due"] == "2026-06-04"  # jeudi
    assert out["conventions_said"]["anchor"] == "receipt"


# ----------------------------------------------------------- V1-V3
def test_b1_dimanche_reporte_par_de_pas_par_fr():
    out = k.payment_due("2026-05-01", "net 30")
    j = out["jurisdictions"]
    assert j["fr"]["legal_due"] == "2026-05-31"
    assert j["fr"]["roll_rule"] == "no_statutory_roll"
    assert j["fr"]["statutory_roll"] is False
    assert j["de"]["legal_due"] == "2026-06-01"
    assert j["de"]["roll_rule"] == "bgb_193"
    assert j["gb"]["legal_due"] == "2026-05-31"  # 31-mai n'est pas bank holiday


def test_b2_samedi_la_divergence_de_la_file():
    # l'item de la file, chiffré : les deux règles divergent SUR LE
    # SAMEDI — § 193 le reporte, la France facture ne reporte rien.
    out = k.payment_due("2026-05-07", "net 30", jurisdiction="fr")
    j = out["jurisdictions"]
    assert j["fr"]["legal_due"] == "2026-06-06"
    assert j["de"]["legal_due"] == "2026-06-08"
    assert j["de"]["shift_days"] == 2
    assert j["gb"]["legal_due"] == "2026-06-06"
    assert out["divergence_max_days"] == 2


def test_b3_gb_fenetre_bank_holidays_plus_quatre():
    out = k.payment_due("2026-05-01", "30 business days",
                        jurisdiction="gb")
    w = {r["reading"]: r["due"] for r in out["readings"]}
    assert w["worked_from_issue"] == "2026-06-16"
    assert w["plain_mon_fri"] == "2026-06-12"


def test_b4_ouvrables_vs_ouvres_huit_jours():
    # L. 3133-1 (lu, via la table holidays.py) : ouvrable = tout jour
    # sauf dimanche + férié — SAMEDI compte. Même facture, même mot,
    # deux compteurs, huit jours. C'est le client de r/Contractor.
    out = k.payment_due("2026-05-01", "net 30", jurisdiction="fr")
    w = {r["reading"]: r["due"] for r in out["readings"]}
    assert w["ouvrables_from_issue"] == "2026-06-09"
    assert w["worked_from_issue"] == "2026-06-17"  # ascension 14-mai + pentecôte 25-mai sautés
    assert int(w["worked_from_issue"][8:10]) - int(w["ouvrables_from_issue"][8:10]) == 8


# ------------------------------------------------------------- V4
def test_c1_eom_deux_methodes_de_etat():
    # exemple official economie.gouv.fr : facture du 10 mars ->
    # 30 avril OU 15 mai. L'écart est ADMIS par l'administration.
    out = k.payment_due("2026-03-10", "45 jours fin de mois")
    e = out["eom_methods"]
    assert e["days_then_end_of_month"] == "2026-04-30"
    assert e["end_of_month_then_days"] == "2026-05-15"
    assert e["gap_days"] == 15
    assert "DGCCRF" in e["law"]


def test_c2_eom_jamais_de_moyenne():
    out = k.payment_due("2026-03-10", "45 jours fin de mois")
    e = out["eom_methods"]
    # les DEUX dates voyagent, l'écart est la réponse — aucune clé
    # « moyenne/average » ne peut exister dans la sortie.
    assert "average" not in json.dumps(out) and "moyenne" not in [
        r["reading"] for r in out["readings"]]
    assert out["spread_days"] == e["gap_days"] == 15


# ------------------------------------------------------------- V5
def test_d1_noel_trois_etages_une_date():
    # due vendredi 25-déc-2026 : FR facture reste au 25 (VIDE LU) ;
    # FR lettre de change -> SAMEDI 26 (atterrissage OUVRABLE, pas
    # workday — com_l511_79 dit « premier jour ouvrable ») ; DE -> 28
    # (§ 193 : 25 férié, 26 Sonnabend+férié, 27 dimanche) ; GB -> 29
    # (25 Xmas, 26 Boxing par Schedule 1 même un samedi, 28 substitut
    # proclamé — chaîne de DEUX jours fériés + week-end).
    base = dict(invoice_date="2026-11-25", terms="net 30")
    out = k.payment_due(**base, jurisdiction="fr")
    assert out["jurisdictions"]["fr"]["legal_due"] == "2026-12-25"
    lc = k.payment_due(**base, jurisdiction="fr",
                       document="lettre_de_change")
    assert lc["jurisdictions"]["fr"]["legal_due"] == "2026-12-26"
    assert lc["jurisdictions"]["fr"]["roll_rule"] == "com_l511_79"
    assert lc["jurisdictions"]["de"]["legal_due"] == "2026-12-28"
    assert lc["jurisdictions"]["gb"]["legal_due"] == "2026-12-29"
    # settlement sur la due APPLIQUÉE FR = 25-déc, fermé :
    s = out["settlement_target2"]
    assert s["settle_on"] == "2026-12-28"
    assert s["due_day_target_closing"] == "Christmas Day"
    assert s["closing_absorbed_by_weekend"] is False
    assert s["interest_runs_from"] == "2026-12-25"


def test_d2_fermeture_absorbee_2027():
    # 1-mai-2027 = SAMEDI + fermeture TARGET. Côté FR facture (table
    # vide lue), la due RESTE au samedi : le rail ne peut rien
    # règler ce jour-là, settle -> lundi 3, et la fermeture du 1er
    # mai est ABSORBÉE par le week-end (zéro jour de plus). Côté DE,
    # § 193 a déjà roulé au 3 : le rail trouve la porte ouverte.
    out = k.payment_due("2027-04-01", "net 30", jurisdiction="fr")
    assert out["jurisdictions"]["fr"]["legal_due"] == "2027-05-01"
    assert out["jurisdictions"]["de"]["legal_due"] == "2027-05-03"
    s = out["settlement_target2"]
    assert s["settle_on"] == "2027-05-03"
    assert s["shift_days"] == 2
    assert s["closing_absorbed_by_weekend"] is True
    assert s["due_day_target_closing"] == "1 May (Labour Day)"
    outde = k.payment_due("2027-04-01", "net 30", jurisdiction="de")
    assert outde["settlement_target2"]["shift_days"] == 0  # §193 a roulé avant


def test_d3_rail_gbp_pas_de_colonne_juree():
    # doctrine b111 : le texte CHAPS n'a pas été lu — aucune colonne
    # de règlement n'est promise pour gb, c'est un refus NOMMÉ.
    out = k.payment_due("2026-06-05", "net 30", jurisdiction="gb")
    s = out["settlement_target2"]
    assert "CHAPS" in s["layer"]
    assert s["target2_open"] is None


# ------------------------------------------------------- clause & table
def test_e1_clause_prochaine_ouvre_sur_samedi():
    out = k.payment_due("2026-05-07", "net 30", jurisdiction="fr",
                        clause="next_workday")
    assert out["applied"]["legal_due"] == "2026-06-08"
    assert out["applied"]["shift_days"] == 2


def test_e2_clause_precedente_le_type_obligataire():
    # clause « preceding business day » lue dans un arrêt de la Cour
    # de cassation (émission obligataire, relue via courdecassation.
    # fr) — plusieurs jours d'écart en semaine fériée.
    out = k.payment_due("2026-05-07", "net 30", jurisdiction="fr",
                        clause="previous_workday")
    assert out["applied"]["legal_due"] == "2026-06-05"  # vendredi
    assert out["applied"]["shift_days"] == 1


def test_e3_gb_hors_table_refuse_par_nom():
    out = k.payment_due("2029-01-01", "net 30", jurisdiction="de")
    g = out["jurisdictions"]["gb"]
    assert "refused" in g and "PROCLAIMED" in g["refused"]
    assert g["expected"] == "year 2026-2028 for jurisdiction gb"
    # la ligne DE vit quand même (la divergence n'est pas otage)
    assert out["jurisdictions"]["de"]["legal_due"] == "2029-01-31"


def test_e4_count_gb_hors_table_refus_champ():
    with pytest.raises(k.DueError) as e:
        k.payment_due("2029-01-01", "30 business days",
                      jurisdiction="gb")
    assert e.value.field == "invoice_date"


def test_e5_ferie_ouvert_atterrissage_ouvrable_samedi():
    # Victoire 1945 = VENDREDI 8-mai-2026 : lettre de change ->
    # SAMEDI 9 (jour ouvrable), alors que § 193 allemand ne roule
    # PAS (8-mai n'est pas un férie du core commun des Länder) et
    # que la facture FR reste au 8. Trois dates, un vendredi.
    out = k.payment_due("2026-04-08", "net 30", jurisdiction="fr",
                        document="lettre_de_change")
    assert out["jurisdictions"]["fr"]["legal_due"] == "2026-05-09"
    assert out["jurisdictions"]["de"]["legal_due"] == "2026-05-08"
    assert out["jurisdictions"]["gb"]["legal_due"] == "2026-05-08"
    assert out["divergence_max_days"] == 1


def test_e6_document_hors_pair_refuse():
    with pytest.raises(k.DueError) as e:
        k.payment_due("2026-05-01", "net 30", document="cheque")
    assert e.value.field == "document"


# -------------------------------------------------------- plafond
def test_f1_net90_hors_la_loi_fr():
    out = k.payment_due("2026-03-01", "net 90", jurisdiction="fr")
    assert out["fr_ceiling"]["verdict"] == "OVER_L441_10"
    assert out["fr_ceiling"]["days_from_issue"] == 90


def test_f2_eom_pas_flagge_par_le_plafond():
    # la dérogation « 45 jours fin de mois » peut dépasser 60 jours
    # PAR LA LOI elle-même (jusqu'à 75) — le module ne flagge pas.
    out = k.payment_due("2026-03-10", "45 jours fin de mois",
                        jurisdiction="fr")
    assert out["fr_ceiling"]["verdict"] == "WITHIN"


def test_f3_discount_et_net_cote_a_cote():
    out = k.payment_due("2026-03-01", "2/10 net 30")
    assert out["discount_window"]["window"] == "2026-03-11"
    assert out["discount_window"]["pct"] == 2
    w = {r["reading"] for r in out["readings"]}
    assert "discount_window" in w and "calendar_issue" in w


# --------------------------------------------------------- refusals
def test_g1_terms_hors_grammaire_nomme_le_grammaire():
    with pytest.raises(k.DueError) as e:
        k.payment_due("2026-05-01", "pay me whenever")
    assert e.value.field == "terms"
    assert "net 30" in e.value.expected


def test_g2_juridiction_hors_lus_refuse_par_nom():
    with pytest.raises(k.DueError) as e:
        k.payment_due("2026-05-01", "net 30", jurisdiction="lu")
    assert e.value.field == "jurisdiction"
    assert "de | fr | gb" in e.value.expected


def test_g3_receipt_avant_encre_refuse():
    with pytest.raises(k.DueError) as e:
        k.payment_due("2026-05-01", "net 30",
                      receipt_date="2026-04-28")
    assert e.value.field == "receipt_date"


def test_g4_due_on_receipt_sans_date_refuse():
    with pytest.raises(k.DueError) as e:
        k.payment_due("2026-05-01", "due on receipt")
    assert e.value.field == "receipt_date"


def test_g5_surveillance_cloture():
    # 4 chiffres : hors grammaire (\d{1,3}) — refus grammar ;
    # 401 : dans la grammaire, hors plafond 400 — refus ceiling.
    with pytest.raises(k.DueError) as e:
        k.payment_due("2026-05-01", "net 4000")
    assert e.value.field == "terms"
    with pytest.raises(k.DueError) as e:
        k.payment_due("2026-05-01", "net 401")
    assert e.value.field == "terms" and "1-400" in e.value.expected


# ---------------------------------------------------------- API
def _api(body):
    return client.post("/api/v1/invoice/payment-due", json=body)


def test_h1_endpoint_gold_samedi():
    r = _api({"invoice_date": "2026-05-07", "terms": "net 30",
              "jurisdiction": "fr"})
    assert r.status_code == 200
    b = r.json()
    assert b["jurisdictions"]["de"]["legal_due"] == "2026-06-08"
    assert b["divergence_max_days"] == 2
    want = b.pop("sha256")
    assert main.canon(b) == want  # canon maison : les octes du corps


def test_h1b_moyenne_impossible_par_construction():
    r = _api({"invoice_date": "2026-03-10",
              "terms": "45 jours fin de mois"})
    assert r.status_code == 200
    body = json.dumps(r.json(), ensure_ascii=False)
    # « jamais la moyenne » : AUCUN mot anglais average/mean ne peut
    # apparaître — la prose FR du law-string dit « jamais une
    # moyenne » comme PLAIDOYER, pas comme clé : on teste les clés.
    assert "average" not in body and "mean" not in body
    keys = set(r.json()["eom_methods"])
    assert not any("avg" in x or "mean" in x for x in keys)


def test_h2_400_nomme_field_expected():
    r = _api({"invoice_date": "2026-05-01", "terms": "weird"})
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert e["field"] == "terms" and "net 30" in e["expected"]


def test_h3_extra_field_refuse():
    r = _api({"invoice_date": "2026-05-01", "terms": "net 30",
              "vibes": "corporate"})
    assert r.status_code == 400


def test_h4_tools_card():
    r = client.get("/tools/invoice_payment_due.json")
    assert r.status_code == 200
    b = r.json()
    assert b["tier"].startswith("free") and b["pack"] == "dates"
    assert "invoice_date" in b["schema"]["inputSchema"]["required"]


def test_h5_determinisme_octet_a_octet():
    a = _api({"invoice_date": "2026-05-01", "terms": "net 30",
              "jurisdiction": "de"})
    b = _api({"invoice_date": "2026-05-01", "terms": "net 30",
              "jurisdiction": "de"})
    assert a.content == b.content


def test_h6_batch():
    r = client.post("/api/v1/batch", json={
        "tool": "invoice_payment_due",
        "payloads": [
            {"invoice_date": "2026-05-07", "terms": "net 30",
             "jurisdiction": "fr"},
            {"invoice_date": "2026-11-25", "terms": "net 30",
             "jurisdiction": "de"},
        ]})
    assert r.status_code == 200
    b = r.json()
    assert b["failed"] == 0
    assert b["results"][1]["result"]["jurisdictions"]["de"][
        "legal_due"] == "2026-12-28"


# ------------------------------------------------- aiguilles & fratrie
def test_j1_aiguilles_payment_due_x3():
    for q in (
            "facture net 30 tombe un samedi quelle est la vraie échéance",
            "45 jours fin de mois comment calculer la date de paiement",
            "rechnung netto 30 fällig am samstag zahlungsziel werktag",
            "invoice dated friday net 30 when is it legally due germany",
            "does net 30 count weekends or business days payment terms",
            "fatura net 30 vence no feriado qual a data real de pagamento",
    ):
        hits = main.routing.route(q, top=3)
        names = [h["tool"] for h in hits]
        assert "invoice_payment_due" in names, (q, names)
        assert names[0] == "invoice_payment_due", (q, names)


def test_j2_fratrie_garde_ses_aiguilles():
    # les voisins gardent leurs phrases — le nouveau tag « business
    # days » ne vole pas date_calc, « réception » ne vole pas
    # date_deemed, « relance » reste chez aging.
    hits = main.routing.route(
        "combien de jours ouvrables entre le 5 et le 20 mars 2026",
        top=2)
    assert hits[0]["tool"] == "date_calc", hits
    hits = main.routing.route(
        "pli recommandé expédié le 3 quels jours pour réception réputée",
        top=2)
    assert hits[0]["tool"] == "date_deemed", hits
    hits = main.routing.route(
        "aging overdue unpaid receivables buckets relance client",
        top=2)
    assert hits[0]["tool"] == "money_aging", hits
    hits = main.routing.route(
        "jours fériés 2027 Allemagne liste complète", top=2)
    assert hits[0]["tool"] == "schedule_holidays", hits


def test_j3_leurre_ne_prescrit_rien():
    # phrase SANS données d'échéance : aucune date ne doit être
    # promise — la garde b98 des leurres.
    hits = main.routing.route(
        "how do I politely ask a client to pay faster", top=2)
    names = [h["tool"] for h in hits]
    assert "invoice_payment_due" not in names, names


def test_k1_locales_portent_la_carte_x3():
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    markers = {"fr": "LA VRAIE ÉCHÉANCE", "en": "four readings",
               "pt": "QUATRO leituras"}
    import json as _j
    for loc, marker in markers.items():
        data = _j.load(open(root / "locales" / ("%s.json" % loc)))
        blob = json.dumps(data, ensure_ascii=False)
        assert marker in blob or "ÉCHÉANCE" in blob, (loc, marker)


def test_k2_sayings_parite():
    import sayings
    s = sayings.SAY["/api/v1/invoice/payment-due"]
    assert set(s) == {"en", "fr", "pt"}
    for lang in s:
        assert len(s[lang]) > 40, lang
