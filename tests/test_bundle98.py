# -*- coding: utf-8 -*-
"""Bundle 98 — extension FRANCE + Apple direct de /shop/return-deadline.

Golds tracés À LA MAIN depuis les clauses PUBLIÉES rejouées le
24-nov-2026 (officiels verbatim), jamais recopiés du module. Ancres
de calendrier : 2026-01-01 jeudi (b80 dit 23-nov Monday — cohérent),
2027-01-01 vendredi (b80 dit 31-jan Sunday — cohérent).

  fnac, achat 2026-12-20           -> 2027-01-15, vendredi (« Les
      retours sont prolongés jusqu'au 15 janvier 2027 — tout achat
      effectué à la Fnac entre le 1er novembre et le 31 décembre
      2026 », fnac.com verbatim ; 15-jan = 8-jan + 7 = vendredi).
  fnac, achat 2026-10-15 hors ext.  -> standard « 15 jours à partir
      de la date d'achat OU de réception » (double base publiée) :
      sans livraison = depuis achat : 15-oct + 14 (Day-1) =
      2026-10-29, jeudi (302e jour -> 301%7=0 -> jeudi).
      livraison 2026-10-20 = depuis réception : 20-oct + 14 =
      2026-11-03, mardi (307-1=306, 306%7=5 -> jeudi+5 = mardi).
  darty marketplace                -> REFUS nommé : le verbatim
      exclut « produits achetés sur la marketplace ».
  fnac/darty category electronics  -> CONDITIONNÉ : l'exclusion
      publiée « gros électroménager et TV » est un sous-ensemble
      de notre mot fermé electronics — le verbatim voyage.
  boulanger 2026-10-30 et 12-27    -> 2027-01-31 dimanche (fenêtre
      officielle OCT 30→DÉC 27, PAS déc 31) ; 10-29 et 12-28 hors
      fenêtre -> refus nommé (standard non daté en ≥2) ; le module
      panier du MÊME site publie « 27 décembre 2027 » — coquille
      officielle CONFLIT NOMMÉ, la note légale dit 2026.
  dell, achat 2026-12-10, livr.
      2026-12-20                   -> max(15-jan, 20-déc+29=18-jan)
      = 2027-01-18 LUNDI (la clause « ou 30 jours à compter de la
      date de livraison, la date la plus tardive des deux
      prévalant » bat la date dure — grammaire later-of FR) ;
      livraison 2026-11-10 : +29 = 9-déc < 15-jan -> date dure.
  amazon.fr, achat 2026-12-20,
      livraison 2027-01-05         -> 5-jan+29 = 2027-02-03,
      MERCREDI (même mécanique qu'Amazon UK, clause FR).
  amazon.fr, achat 2026-12-26 hors fenêtre (25-déc) livraison
      2027-01-02                   -> standard 30 j depuis réception
      = 2-jan + 29 = 2027-01-31, DIMANCHE — même date que
      l'extension par coincidence, AUTRE RÈGLE nommée.
  apple direct US, REÇU 2026-12-21 (achat 2026-12-20)
                                   -> 2027-01-08 VENDREDI ; la
      fenêtre se joue sur la LIVRAISON (« received between
      November 6, 2026 and December 25, 2026 » — verbatim, base
      nouvelle dans la table) ; reçu 2026-12-27 après Noël ->
      standard 14 jours = 27-déc+13 = 2027-01-09 SAMEDI ; sans
      livraison -> refus nommé.
  apple FR reçu 2026-12-11         -> 2027-01-08 vendredi (page
      FR verbatim : « jusqu'au 8 janvier 2027 inclus… reçus entre
      le 6 novembre 2026 et le 25 décembre 2026 »).
  apple UK                         -> REFUS nommé : le tableau
      multi-pays macrumors dit UK dans le lot 8-jan, mais la page
      UK n'a PAS été rejouée ce cycle — pas de prêt.
  cdiscount                        -> REFUS nommé portant le fait
      candidat (8-jan presse concordante, fenêtre d'achat connue
      seulement d'un agrégateur de coupons) : « une date sans sa
      fenêtre n'est pas une deadline ».

  days_left tracé main : 2026-11-24 -> 2027-01-15 = 52 (6 reste de
  nov + 31 déc + 15 jan).
"""
import datetime as dt

import pytest

import returndeadkit as rk
from returndeadkit import ReturnDeadError, return_deadline


def _d(s):
    return dt.date.fromisoformat(s)


# ---------------------------------------------------------------- fnac

def test_fnac_extension_hard_date_friday():
    out = return_deadline("fnac", "2026-12-20", country="FR")
    assert out["return_by"] == "2027-01-15"
    assert out["return_by_weekday"] == "Friday"
    assert out["rule_applied"] == "holiday-extension"
    assert out["provenance"] == ["published"]
    assert out["purchase_window"] == ["2026-11-01", "2026-12-31"]
    assert any("15 janvier 2027" in s for s in out["sources"])


def test_fnac_window_edge_dec31_in_and_season_gate():
    out = return_deadline("fnac", "2026-12-31", country="FR")
    assert out["return_by"] == "2027-01-15"
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("fnac", "2027-01-01", country="FR")
    assert e.value.field == "purchase_date"  # saison 2026 seule


def test_fnac_out_of_window_dual_basis_purchase():
    out = return_deadline("fnac", "2026-10-15", country="FR")
    assert out["return_by"] == "2026-10-29"
    assert out["return_by_weekday"] == "Thursday"
    assert out["rule_applied"] == "standard-window"
    assert "date d'achat" in out["basis_note"]


def test_fnac_out_of_window_dual_basis_delivery():
    out = return_deadline("fnac", "2026-10-15", country="FR",
                          delivery_date="2026-10-20")
    assert out["return_by"] == "2026-11-03"
    assert out["return_by_weekday"] == "Tuesday"
    assert "réception" in out["basis_note"]


def test_fnac_electronics_is_conditional_gem_tv():
    out = return_deadline("fnac", "2026-12-20", country="FR",
                          category="tv")
    assert out["return_by"] == "2027-01-15"
    assert "gros électroménager" in out["named_condition"]
    assert "TV" in out["named_condition"]


def test_fnac_general_has_no_fake_caveat():
    out = return_deadline("fnac", "2026-12-20", country="FR",
                          category="toy")
    assert out["category"] == "general"
    assert out["return_by"] == "2027-01-15"
    assert "named_condition" not in out
    out2 = return_deadline("fnac", "2026-12-20", country="FR",
                           category="laptop")
    # laptop -> electronics (alias publié b80) : la caveat est
    # DUE — la machine a raison, ce test a d'abord eu tort.
    assert "named_condition" in out2


# ---------------------------------------------------------------- darty

def test_darty_marketplace_refused_verbatim():
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("darty", "2026-12-20", country="FR",
                        channel="marketplace")
    assert e.value.field == "channel"
    # verbatim darty.com écrit « Marketplace » avec la majuscule
    # de la marque — la machine transporte le verbatim, le test a
    # d'abord eu tort (check deux fois qui a raison : fait ici).
    assert "Marketplace" in e.value.message


def test_darty_volumineux_43_inch_definition_travels():
    out = return_deadline("darty", "2026-12-20", country="FR",
                          category="electronics")
    assert out["return_by"] == "2027-01-15"
    assert "43" in out["named_condition"]  # TV > 43'' (109 cm)


# ---------------------------------------------------------------- boulanger

def test_boulanger_official_window_is_oct30_dec27():
    out = return_deadline("boulanger", "2026-10-30", country="FR")
    assert out["purchase_window"] == ["2026-10-30", "2026-12-27"]
    assert out["return_by"] == "2027-01-31"
    assert out["return_by_weekday"] == "Sunday"
    out2 = return_deadline("boulanger", "2026-12-27", country="FR")
    assert out2["return_by"] == "2027-01-31"


def test_boulanger_outside_window_refuses_standard():
    for day in ("2026-10-29", "2026-12-28"):
        with pytest.raises(ReturnDeadError) as e:
            return_deadline("boulanger", day, country="FR")
        assert e.value.field == "purchase_date"
        assert "≥2" in e.value.message or ">=2" in e.value.message


def test_boulanger_official_typo_is_named_conflict():
    out = return_deadline("boulanger", "2026-11-10", country="FR")
    assert any("27 décembre 2027" in c for c in out["conflicts"])


# ---------------------------------------------------------------- dell

def test_dell_later_of_beats_hard_date():
    out = return_deadline("dell", "2026-12-10", country="FR",
                          delivery_date="2026-12-20")
    assert out["return_by"] == "2027-01-18"
    assert out["return_by_weekday"] == "Monday"
    assert out["rule_applied"] == "holiday-extension-later-of"
    assert out["later_of"] == {"fixed": "2027-01-15",
                               "delivery_plus_30": "2027-01-18"}


def test_dell_hard_date_wins_when_delivery_early():
    out = return_deadline("dell", "2026-11-05", country="FR",
                          delivery_date="2026-11-10")
    assert out["return_by"] == "2027-01-15"
    assert out["rule_applied"] == "holiday-extension"


def test_dell_needs_delivery_for_later_of():
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("dell", "2026-12-10", country="FR")
    assert e.value.field == "delivery_date"
    assert "tardive" in e.value.message


def test_dell_outside_window_refused_and_eligibility_named():
    # la fenêtre Dell ferme le 29 DÉCEMBRE (verbatim) : un achat du
    # 28 est DEDANS — le premier tracé main de ce test disait faux,
    # la machine (et la page officielle) ont raison.
    out_in = return_deadline("dell", "2026-12-28", country="FR",
                             delivery_date="2027-01-02")
    assert out_in["return_by"] == "2027-01-31"  # 2-jan+29 > 15-jan
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("dell", "2026-12-31", country="FR",
                        delivery_date="2027-01-02")
    assert e.value.field == "purchase_date"
    out = return_deadline("dell", "2026-12-10", country="FR",
                          delivery_date="2026-12-20")
    assert "accessoires pour PC" in out["named_condition"]


# ---------------------------------------------------------------- amazon FR

def test_amazon_fr_later_of_february():
    out = return_deadline("amazon", "2026-12-20", country="FR",
                          delivery_date="2027-01-05")
    assert out["return_by"] == "2027-02-03"
    assert out["return_by_weekday"] == "Wednesday"
    assert out["rule_applied"] == "holiday-extension-later-of"


def test_amazon_fr_window_closes_dec25_standard_hits_jan31_by_other_rule():
    out = return_deadline("amazon", "2026-12-26", country="FR",
                          delivery_date="2027-01-02")
    assert out["return_by"] == "2027-01-31"
    assert out["return_by_weekday"] == "Sunday"
    assert out["rule_applied"] == "standard-window"  # PAS l'extension


def test_amazon_fr_widget_regime_is_named_condition():
    out = return_deadline("amazon", "2026-12-20", country="FR",
                          delivery_date="2026-12-21")
    assert out["return_by"] == "2027-01-31"
    assert "15 janvier 2027" in out["named_condition"]
    assert "widget" in out["named_condition"]
    assert out["extension_applies"].startswith("auto")


# ---------------------------------------------------------------- apple direct

def test_apple_us_received_basis_extension():
    out = return_deadline("apple", "2026-12-20",
                          delivery_date="2026-12-21")
    assert out["return_by"] == "2027-01-08"
    assert out["return_by_weekday"] == "Friday"
    assert out["rule_applied"] == "holiday-extension"
    assert "received" in out["eligibility_basis"] or "REÇUS" in \
        out["eligibility_basis"]


def test_apple_us_after_dec25_falls_to_standard_14():
    out = return_deadline("apple", "2026-12-20",
                          delivery_date="2026-12-27")
    assert out["return_by"] == "2027-01-09"
    assert out["return_by_weekday"] == "Saturday"
    assert out["rule_applied"] == "standard-window"


def test_apple_us_requires_delivery_date():
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("apple", "2026-12-20")
    assert e.value.field == "delivery_date"


def test_apple_fr_jan8_inclus_with_financing_exclusion():
    out = return_deadline("apple", "2026-12-10", country="FR",
                          delivery_date="2026-12-11")
    assert out["return_by"] == "2027-01-08"
    assert out["return_by_weekday"] == "Friday"
    assert any("financement" in c for c in out["conditions"])


def test_apple_uk_named_not_replayed():
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("apple", "2026-12-20", country="UK",
                        delivery_date="2026-12-21")
    assert e.value.field == "retailer"
    assert "January 8" in e.value.message


# ---------------------------------------------------------------- refusés nommés

def test_cdiscount_refused_date_without_window_is_not_a_deadline():
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("cdiscount", "2026-12-20", country="FR")
    assert e.value.field == "retailer"
    assert "8 janvier 2027" in e.value.message


def test_unknown_fr_retailer_expected_names_fr_table():
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("carrefour", "2026-12-20", country="FR")
    assert "fnac" in e.value.expected
    assert "darty" in e.value.expected
    assert "boulanger" in e.value.expected


def test_br_still_refused_but_fr_accepted():
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("amazon", "2026-12-20", country="BR")
    assert "FR" in e.value.expected


def test_membership_refused_on_fr_row():
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("fnac", "2026-12-20", country="FR",
                        membership=True)
    assert e.value.field == "membership"


def test_unknown_category_on_fr_row_still_closed_grammar():
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("fnac", "2026-12-20", country="FR",
                        category="skis")
    assert e.value.field == "category"


# ---------------------------------------------------------------- contrats partagés

def test_days_left_fnac_handtraced():
    out = return_deadline("fnac", "2026-12-20", country="FR",
                          as_of="2026-11-24")
    assert out["days_left"] == 52


def test_table_version_travels_stamped():
    out = return_deadline("fnac", "2026-12-20", country="FR")
    assert out["table_version"] == rk.TABLE_VERSION
    assert rk.TABLE_VERSION == "2026-11-24"


def test_us_rows_untouched_by_fr_extension():
    # régression frontière : la ligne US n'a pas gagné de champ FR
    out = return_deadline("amazon", "2026-12-20")
    assert out["return_by"] == "2027-01-31"
    assert "named_condition" not in out
    assert "eligibility_basis" not in out
    assert "basis_note" not in out


def test_uk_later_of_bytes_untouched():
    out = return_deadline("amazon", "2026-12-20", country="UK",
                          delivery_date="2027-01-05")
    assert out["later_of"] == {"fixed": "2027-01-31",
                               "delivery_plus_30": "2027-02-03"}
    with pytest.raises(ReturnDeadError) as e:
        return_deadline("amazon", "2026-12-20", country="UK")
    assert "Amazon UK: 'until 31 January 2027 OR within 30 days" \
        " of delivery, whichever is later'" in e.value.message


# ---------------------------------------------------------------- forme blague
# Douleur pêchée par le leurre que CE lot a lui-même ajouté au
# corpus radar : depuis l'extension FR, « blague sur les retours de
# Noël » pesait assez pour router. Le lot qui touche le routeur
# ferme sa propre douleur : forme fermée nommée, zéro LM, trois
# langues — et la file n°7 (EN fingerprints, pêchée b97) meurt par
# la même règle.

def test_joke_form_dies_three_languages():
    import routing
    assert routing.route("raconte-moi une blague sur les retours "
                         "de Noël") == []
    assert routing.route("tell me a joke about fingerprints") == []
    assert routing.route("me faz uma piada sobre prazos de "
                         "devolução") == []


def test_joke_form_does_not_gild_real_queries():
    import routing
    hits = routing.route("date limite de retour fnac noël")
    assert hits and hits[0]["tool"] == "shop_return_deadline"
    # aucun mot réel n'est devenu aveugle :
    assert routing.route("retour dell 15 janvier") != []
