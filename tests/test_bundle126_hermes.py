# Bundle 126_hermes — VAGUE INTEGRITE PORTE (26-11, go Vince)
# Bugs mesurés et confirmés au rejeu prod par l'equipe Grok (synthese
# 22:55) + un trouve par Hermes en rejouant :
#  B3  math_calc > 30 chiffres -> HTTP 500 nu (devait etre un 400 nomme)
#  B3b un payload toxique tuait TOUT le /batch (500 global) — isolation
#  B7  sort_multi en batch sans by -> 500 (le direct rendait un 400 honnete)
#  B5/B8 num_fx / recipe_invoice avalaient les cles inconnues en silence
#  (+ defaut TVA nomme ; + l'URL de reparation inventee /tools/<champ>)
# Ces tests sont ROUGES avant les correctifs — oracles traces a la MAIN.
import json

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _post(path, body):
    return client.post(path, json=body)


def test_batch_survit_a_un_item_toxique():
    # l'item sain doit SURVIVRE ; le toxique meurt nomme, pas la demande.
    r = _post("/api/v1/batch", {"tool": "math_calc", "payloads": [
        {"expr": "1 + 1"}, {"expr": "9" * 31 + " + 1"}, {"expr": "2 * 3"}]})
    assert r.status_code == 200
    b = r.json()
    assert b["succeeded"] == 2 and b["failed"] == 1
    assert b["results"][0]["ok"] is True
    assert b["results"][1]["ok"] is False
    # l'item toxique meurt NOMME (invalid_input avec la borne 30 citee,
    # ou tool_error en dernier rempart) — jamais 500, jamais le lot.
    err = json.dumps(b["results"][1]["error"])
    assert "invalid_input" in err or "tool_error" in err
    assert "30" in err
    assert b["results"][2]["ok"] is True


def test_math_calc_trente_et_un_chiffres_quarante_cent_nomme():
    # direct : plus JAMAIS de 500 ; un 400 qui nomme champ, borne, ecart.
    r = _post("/api/v1/math/calc", {"expr": "9" * 31 + " + 1"})
    assert r.status_code == 400
    e = r.json()["errors"][0]
    assert e["field"] == "expr"
    assert "30" in e["message"]
    assert "expected" in e


def test_batch_sort_multi_sans_by_item_meurt_pas_le_lot():
    r = _post("/api/v1/batch", {"tool": "sort_multi",
                                "payloads": [{"rows": [{"a": 2}, {"a": 1}]}]})
    assert r.status_code == 200
    b = r.json()
    assert b["failed"] == 1 and b["succeeded"] == 0
    assert b["results"][0]["ok"] is False


def test_num_fx_refuse_les_cles_inconnues_par_leur_nom():
    # direction/pair/legs n'existent PAS au contrat (amount, rate, to,
    # precision) — les avaler en silence est la porte derobee de B5.
    r = _post("/api/v1/num/fx", {"amount": "1000", "rate": "0.9216",
                                 "to": "USD", "direction": "USD vers EUR"})
    assert r.status_code == 400
    assert "direction" in json.dumps(r.json())


def test_recipe_invoice_refuse_pays_inconnu_et_nome_son_defaut():
    bad = _post("/api/v1/recipe/invoice", {"line_items": [
        {"desc": "x", "qty": 1, "unit_price": "100.00"}], "country": "FR"})
    assert bad.status_code == 400
    assert "country" in json.dumps(bad.json())
    ok = _post("/api/v1/recipe/invoice", {"line_items": [
        {"desc": "x", "qty": 1, "unit_price": "100.00"}]})
    assert ok.status_code == 200
    b = ok.json()
    assert b["vat_percent"] == "0"
    # le defaut est DIT — pas un silence
    assert "vat_percent" in " ".join(b.get("applied_defaults", []))


def test_reparation_url_reelle_pas_interpolee():
    # le 400 de recipe_invoice pointait vers /tools/line_items[0] — une URL
    # inventee par interpolation du champ. Elle doit pointer l'outil reel.
    r = _post("/api/v1/recipe/invoice", {"line_items": [{"z": 1}]})
    assert r.status_code == 400
    blob = json.dumps(r.json())
    assert "/tools/recipe_invoice.json" in blob
    assert "/tools/line_items" not in blob


def test_canonique_inchange_batch_valide():
    # garde : l'isolation ne casse pas la voie rapide — batch propre = meme
    # reponse sha stable qu'avant la vague (1+1 = 2).
    r = _post("/api/v1/batch", {"tool": "math_calc",
                                "payloads": [{"expr": "1 + 1"}]})
    assert r.status_code == 200
    assert r.json()["results"][0]["result"]["value"] == "2"
