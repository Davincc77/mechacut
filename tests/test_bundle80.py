# -*- coding: utf-8 -*-
"""Bundle 80 — /api/v1/shop/return-deadline : la table des délais de
retour de Noël 2026, croisée ≥2 sources, provenance et conflits NOMMÉS.

Golds tracés À LA MAIN avant l'impl, depuis les tableaux PUBLIÉS du
cycle (sellercentral verbatim, bestbuy.com verbatim, star-telegram/
sacbee, thinkmoney 16-nov, aol, policyreturn), jamais recopiés du
module ; chaque date glissante a son calcul rejoué contre le
calendrier stdlib par un test séparé (le module et le test partent
des MÊMES nombres publiés, pas l'un de l'autre) :

  amazon US, achat 2026-12-20      -> 2027-01-31 (Seller Central,
      date PUBLIÉE en dur), Sunday (oracle : 23-nov Monday + 69 j).
  amazon US, apple 2026-12-20      -> 2027-01-15 Friday (16 jours
      plus tôt — « a deadline shoppers could miss »).
  walmart US, 2026-10-15           -> 2027-01-31 (fenêtre Oct 1→Dec
      31, sacbee + aol concordants).
  walmart US, 2026-07-01 hors ext. -> standard 90 j depuis achat,
      Day-1 : 1-juil + 89 = 2026-09-28, Monday (tracé main : 30-31
      juil, 31 août, 28 sept ; recalendrier stdlib au test).
  target US, electronics 2026-12-26 -> REFUS nommé : la fenêtre
      d'extension Target ferme DEC 24 (7 jours avant Amazon) ; le
      standard par catégorie n'est pas dans notre ≥2.
  target US, electronics 2026-12-20 -> 2027-01-24 Sunday.
  target US, phone 2026-12-20      -> 2027-01-08 Friday (Apple/Beats/
      téléphones, ligne séparée publiée).
  bestbuy US, 2026-12-01 membre    -> 2027-01-31 (hard date).
  bestbuy US, 2026-12-04 membre    -> 60 j glissants Day-1 :
      4-déc + 59 = 2027-02-01, Monday. DEUX RÈGLES, deux jours
      adjacents — jamais de mélange.
  bestbuy US, decoration 2026-11-20 -> survit à l'extension :
      15 j Day-1 = 2026-12-04 Friday.
  bestbuy US, activatable 2026-11-20 -> 14 j = 2026-12-03 Thursday ;
      verizon 2026-11-20 -> 30 j = 2026-12-19 Saturday.
  costco US, electronics livraison 2026-12-27 -> 90 j depuis
      LIVRAISON (sacbee verbatim) = 2027-03-26 Friday ; général ->
      refus nommé (pas de fenêtre datée publiée).
  amazon UK, achat 2026-11-05, livraison 2026-11-08 : Jan 31 vs
      livraison+30 Day-1 = 2026-12-07 -> plus tard = 2027-01-31.
  amazon UK, achat 2026-12-20, livraison 2027-01-05 : livraison+30
      = 2027-02-03 > Jan 31 -> 2027-02-03 Wednesday, rule
      holiday-extension-later-of (le « whichever is later » d'un
      VRAI achat de Noël livré en janvier).
  amazon US hors fenêtre, livraison 2026-10-16 -> 30 j Day-1 =
      2026-11-14 Saturday.
  refusés par nom (single-source, règle ≥2) : next/john-lewis/argos/
  boots UK, kohls/macy's US ; pays BR/CA ; membership sur amazon ;
  année 2025 ; category inventée ; marketplace bestbuy en fenêtre
  (standard only, publié) ; protection_plan walmart sans livraison.

  days_left tracé main : 2026-11-23 -> 2027-01-31 = 69 (7 nov + 31
  déc + 31 jan) ; 0 = last-day-today ; négatif = missed.
"""
import datetime as dt

import pytest

import returndeadkit as rk
from returndeadkit import ReturnDeadError, return_deadline

WD = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
      "Saturday", "Sunday")

def _d(s):
    return dt.date.fromisoformat(s)

# ------------------------------------------------------------- golds

def test_amazon_us_extension_published_hard_date():
    out = return_deadline("amazon", "2026-12-20")
    assert out["return_by"] == "2027-01-31"
    assert out["return_by_weekday"] == "Sunday"
    assert out["rule_applied"] == "holiday-extension"
    assert out["provenance"] == ["published"]
    assert any("sellercentral" in s for s in out["sources"])
    # le conflit pattern-vs-publié est un CHAMP, jamais moyenné :
    assert any("parcelmonitor" in c for c in out["conflicts"])
    assert out["extension_applies"].startswith("auto")

def test_amazon_us_apple_line_is_16_days_earlier():
    out = return_deadline("amazon", "2026-12-20", category="ipad")
    assert out["return_by"] == "2027-01-15"
    assert out["return_by_weekday"] == "Friday"
    assert out["rule_applied"] == "holiday-exception"
    delta = (_d("2027-01-31") - _d("2027-01-15")).days
    assert delta == 16  # « 16 days earlier » publié par miamiherald

def test_walmart_in_window_and_out():
    out = return_deadline("walmart", "2026-10-15")
    assert out["return_by"] == "2027-01-31"
    assert out["rule_applied"] == "holiday-extension"
    # hors extension : standard 90 j depuis ACHAT (wreg), Day-1 :
    out2 = return_deadline("walmart", "2026-07-01")
    assert out2["return_by"] == "2026-09-28"
    assert out2["return_by_weekday"] == WD[
        _d("2026-09-28").weekday()]
    assert out2["rule_applied"] == "standard-window"

def test_walmart_marketplace_is_conditional_never_a_promise():
    out = return_deadline("walmart", "2026-12-10",
                          channel="marketplace")
    assert out["return_by"] == "2027-01-31"
    assert out["extension_applies"] == "unknown-for-seller"
    assert "opt in" in out["named_condition"].lower()

def test_target_window_closes_dec_24_the_seven_day_trap():
    # achat Dec 26 chez Target : PAS dans l'extension (la manchette
    # « until Jan 31 » des pages sœurs le cache) -> refus NOMMÉ.
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("target", "2026-12-26", category="tv")
    assert e.value.field == "purchase_date"
    assert "2026-12-24" in e.value.message  # fin de fenêtre Target,
    # en ISO — la date dure publiée est nommée telle quelle
    # Dec 20, electronics : Jan 24 (dimanche — tracé main).
    out = return_deadline("target", "2026-12-20", category="tv")
    assert out["return_by"] == "2027-01-24"
    assert out["return_by_weekday"] == "Sunday"

def test_target_phone_line_separate():
    out = return_deadline("target", "2026-12-20",
                          category="iphone")
    assert out["return_by"] == "2027-01-08"
    assert out["return_by_weekday"] == "Friday"

def test_bestbuy_member_two_rules_adjacent_days():
    a = return_deadline("bestbuy", "2026-12-03", membership=True)
    b = return_deadline("bestbuy", "2026-12-04", membership=True)
    assert a["return_by"] == "2027-01-31"
    assert a["rule_applied"] == "holiday-extension-member-hard"
    # 60 jours glissants, Day-1 publiée : 4-déc + 59 = 1-février.
    assert b["return_by"] == "2027-02-01"
    assert b["rule_applied"] == "holiday-extension-member-rolling"
    assert b["return_by_weekday"] == "Monday"
    assert "Day 1 is the date" in b["counting_convention"]

def test_bestbuy_short_windows_survive_the_extension():
    out = return_deadline("bestbuy", "2026-11-20",
                          category="decoration")
    assert out["return_by"] == "2026-12-04"      # +14 Day-1
    assert out["rule_applied"] == "short-window-exception"
    out2 = return_deadline("bestbuy", "2026-11-20",
                           category="cell phone")
    assert out2["return_by"] == "2026-12-03"     # activatable 14
    out3 = return_deadline("bestbuy", "2026-11-20",
                           category="verizon")
    assert out3["return_by"] == "2026-12-19"     # Verizon 30
    assert out3["return_by_weekday"] == "Saturday"

def test_bestbuy_marketplace_keeps_standard():
    # publié : les extended timeframes N'EXIGENT rien pour
    # Marketplace — la fenêtre standard court depuis la LIVRAISON.
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("bestbuy", "2026-12-10",
                        channel="marketplace")
    assert e.value.field == "delivery_date"
    out = return_deadline("bestbuy", "2026-12-10",
                          channel="marketplace",
                          delivery_date="2026-12-12")
    assert out["return_by"] == "2026-12-26"  # 12-déc + 14 Day-1
    assert out["rule_applied"] == "marketplace-standard-policy"

def test_costco_no_holiday_extension_90_from_delivery():
    out = return_deadline("costco", "2026-12-26",
                          category="laptop",
                          delivery_date="2026-12-27")
    assert out["return_by"] == "2027-03-26"
    assert out["return_by_weekday"] == "Friday"
    assert out["rule_applied"] == "standing-90-day-electronics"
    assert out["purchase_window"] is None
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("costco", "2026-12-26")
    assert e.value.field == "category"
    assert "without a dated window" in e.value.message.lower()

def test_amazon_uk_later_of_needs_delivery():
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("amazon", "2026-12-20", country="UK")
    assert e.value.field == "delivery_date"
    # livraison en janvier : delivery+30 = 2027-02-03 > Jan 31.
    out = return_deadline("amazon", "2026-12-20", country="UK",
                          delivery_date="2027-01-05")
    assert out["return_by"] == "2027-02-03"
    assert out["rule_applied"] == "holiday-extension-later-of"
    assert out["later_of"]["fixed"] == "2027-01-31"
    assert out["later_of"]["delivery_plus_30"] == "2027-02-03"
    # livraison début décembre : Jan 31 gagne (le fixed est plus
    # tard que delivery+30 = 2026-12-07) -> holiday-extension.
    out2 = return_deadline("amazon", "2026-11-05", country="UK",
                           delivery_date="2026-11-08")
    assert out2["return_by"] == "2027-01-31"
    assert out2["rule_applied"] == "holiday-extension"

def test_amazon_uk_vs_us_window_end_divergence():
    # Dec 28 : couvert aux US (fenêtre->Dec 31), PAS au UK (->Dec 25).
    us = return_deadline("amazon", "2026-12-28")
    uk = return_deadline("amazon", "2026-12-28", country="UK",
                         delivery_date="2027-01-02")
    assert us["rule_applied"] == "holiday-extension"
    assert uk["rule_applied"] == "standard-window"
    # 2-jan-2027 + 30 Day-1 = 31-jan… tracé main : 2 jan + 29 =
    # 31 janvier, pile la date dure — mais la règle UK hors fenêtre
    # EST le standard : le résultat est identique par hasard, et le
    # RULE NAME dit pourquoi. C'est entire la thèse.
    assert uk["return_by"] == "2027-01-31"

def test_amazon_us_out_of_window_delivery_basis():
    out = return_deadline("amazon", "2026-10-14",
                          delivery_date="2026-10-16")
    assert out["return_by"] == "2026-11-14"
    assert out["return_by_weekday"] == "Saturday"
    assert out["rule_applied"] == "standard-window"

def test_refusals_by_name():
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("next", "2026-11-20", country="UK")
    assert "ONE source" in e.value.message
    assert "5-jan-2027" in e.value.message  # le fait candidat voyage
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("kohls", "2026-11-20")
    assert ">=2" in e.value.message
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("magazine-luiza", "2026-11-20", country="BR")
    assert e.value.field == "country"
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("amazon", "2026-11-20", membership=True)
    assert e.value.field == "membership"
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("walmart", "2025-12-20")
    assert e.value.field == "purchase_date"
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("target", "2026-12-20", category="vaiselle")
    assert e.value.field == "category"

def test_days_left_and_table_version():
    out = return_deadline("amazon", "2026-12-20",
                          as_of="2026-11-23")
    assert out["days_left"] == 69       # tracé main : 7 + 31 + 31
    out2 = return_deadline("amazon", "2026-12-20",
                           as_of="2027-01-31")
    assert out2["days_left"] == 0
    out3 = return_deadline("amazon", "2026-12-20",
                           as_of="2027-02-10")
    assert out3["days_left"] == -10
    assert out["table_version"] == rk.TABLE_VERSION
    assert out["season"] == "2026-2027"

def test_month_end_31_30_feb_2027_not_leap_oracle():
    # oracle INDEPENDANT du module : le Day-1 est rejoué par
    # calendrier stdlib sur trois dates qui touchent les bords de
    # mois (31 déc, 28 fév non-bissextile 2027, 30 juin).
    cases = [("walmart", "2026-12-31", None, None,
              "2027-01-31"),
             ("costco", "2026-12-26", "2026-06-25", "electronics",
              None),  # delivery 25-juin + 90 Day-1 = 22-sept
             ("walmart", "2026-07-15", None, None, None)]
    out2 = return_deadline("costco", "2026-12-26",
                           delivery_date="2026-06-25",
                           category="tv")
    assert out2["return_by"] == (_d("2026-06-25") +
                                 dt.timedelta(days=89)).isoformat()
    assert out2["return_by"] == "2026-09-22"
    out3 = return_deadline("walmart", "2026-07-15")
    # 15-juil + 89 : juil 17 + août 31 + sept 30 + 31-41… tracé :
    assert out3["return_by"] == (_d("2026-07-15") +
                                 dt.timedelta(days=89)).isoformat()
    assert out3["return_by"] == "2026-10-12"

def test_no_clock_no_fetch():
    # doctrine : le module n'importe pas de réseau et ne lit pas
    # l'heure courante — deux tokens interdits dans le source.
    src = open("returndeadkit.py", encoding="utf-8").read()
    code = src.split('"""', 2)[2]
    for banned in ("urllib", "requests", "socket", "now(",
                   "today("):
        assert banned not in code

def test_determinism_same_bytes():
    kw = {"retailer": "bestbuy", "purchase_date": "2026-12-04",
          "membership": True, "as_of": "2026-11-23"}
    a = return_deadline(**kw)
    b = return_deadline(**kw)
    import json
    assert json.dumps(a, sort_keys=True) == json.dumps(
        b, sort_keys=True)


# ---------------------------------------------------------------- surfaces
import main  # noqa: E402
import routing as routing_mod  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

client = TestClient(main.app)

def test_wiring_present():
    names = [r[0] for r in routing_mod.TABLE]
    assert "shop_return_deadline" in names
    assert "shop_return_deadline" in main.TOOL_RUN
    docker = open("Dockerfile", encoding="utf-8").read()
    assert "returndeadkit.py" in docker

def test_route_dictations_x3_langues():
    # les phrases live (sayings) doivent tomber sur l'outil — la
    # leçon bundle71 : le live parle AVANT le push. Aucune ne porte
    # de chiffre nu : ce cycle a érigé la règle en test.
    for q in ("can I still return the Christmas gift I bought at "
              "Target, and until when?",
              "jusqu'à quelle date peut-on encore retourner un "
              "cadeau de Noël acheté chez Walmart ?",
              "qual o prazo para devolver um presente de Natal "
              "comprado na Amazon?"):
        d = client.get("/route", params={"q": q, "top": "5"}).json()
        tools = d.get("tools", [])
        assert tools and tools[0]["tool"] == \
            "shop_return_deadline", (q, tools[:2])

def test_endpoint_200_and_400_contract():
    r = client.post("/api/v1/shop/return-deadline",
                    json={"retailer": "amazon",
                          "purchase_date": "2026-12-20"})
    assert r.status_code == 200
    b = r.json()
    assert b["return_by"] == "2027-01-31"
    assert "sha256" in b
    r = client.post("/api/v1/shop/return-deadline",
                    json={"retailer": "target",
                          "purchase_date": "2026-12-26",
                          "category": "electronics"})
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert e["field"] == "purchase_date"
    assert "expected" in e
