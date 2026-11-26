# Bundle 127_hermes — text_claimsweep (150.0) : le sweep d'opinion a la
# porte. Contrat = le blob ELIGIBLE-e-a-arbitre du 26-11 (door sha 77dcc80b,
# SUSPECT-DUPLICATE vs check_constraints 8 -> ARBITRE Vince OUTIL NEUF,
# liste VERROUILLEE : une regle que juge celui qu'elle juge n'est plus une
# regle). Golds G1-G3 traces a la MAIN dans docs/proposals/
# text_claimsweep.json, rejoues ici tels quels — et la table est la MEME
# que scripts/copy-audit.py (precedent claimsweep-b126 du role :
# une seule table pour le CI et pour la porte, l'import, pas la copie).
import json

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def call(text, raw=False):
    r = client.post("/api/v1/text/claimsweep", json={"text": text})
    return r if raw else r.json()


# ---- les trois golds du dossier, mot pour mot ----

def test_g1_honestly_quantifier():
    d = call("Honestly: everyone knows the bench is exact.")
    assert d["clean"] is False
    assert d["hits"] == ["honestly:", "everyone knows"]  # ordre d'apparition


def test_g2_fait_nu_propre():
    d = call("No model in this bench says it is unsure.")
    assert d == {"clean": True, "hits": []} or (
        d["clean"] is True and d["hits"] == [])


def test_g3_fr_et_canonique_minuscule():
    # la forme rendue est la forme canonique MINUSCULEE du marqueur,
    # l'apparition est insensible a la casse — G3 prouve les deux :
    # "Personne ne dit" frappe, rendu "personne ne dit" ; et
    # "honnêtement." SANS deux-points n'est PAS le marqueur
    # "honnêtement :" — la liste fermee est fermee.
    d = call("Personne ne dit jamais cela, honnêtement.")
    assert d["clean"] is False
    assert d["hits"] == ["personne ne dit"]


# ---- regles de contexte, tracees main ----

def test_g4_citation_exemptee():
    # l'exception citation du contrat : un marqueur PORTE par une voix
    # citee n'est pas l'affirmation de l'auteur. Les deux graphies de
    # guillemets basiques, rien d'autre.
    d = call('Il a dit "everyone knows" hier, et « Nobody says » avant.')
    assert d["clean"] is True
    assert d["hits"] == []


def test_g5_citation_ne_blindique_pas_le_reste():
    # hors guillemets, la porte frappe — l'exemption n'est pas un blanc-seing
    d = call('Il a dit "rien" : honnêtement, nobody says that.')
    assert d["clean"] is False
    # attention : "honestly:" (EN) attend les deux-points ; "honnêtement,"
    # avec virgule N'EST PAS le marqueur ferme — seul nobody says frappe
    assert d["hits"] == ["nobody says"]


def test_g6_dedup_et_ordre():
    d = call("Everyone knows. Everyone knows! honestly: ok.")
    assert d["hits"] == ["everyone knows", "honestly:"]


def test_g7_forme_fermee_de_reponse():
    # la reponse ne rend JAMAIS une cle hors contrat — pas de silence,
    # pas de surplus : {clean, hits, sha256}
    d = call("Rien ici ne depasse.")
    assert set(d) == {"clean", "hits", "sha256"}
    assert d["clean"] is True


def test_g8_400_sur_texte_absent():
    r = client.post("/api/v1/text/claimsweep", json={})
    assert r.status_code == 400
    assert "text" in json.dumps(r.json())


def test_g9_canfail_pas_de_regex_libre():
    # le sweep ne DEVINE pas l'opinion : une phrase integralement
    # subjective mais hors liste fermee rend clean=true. C'est la these :
    # la liste verrouille le juge, pas le LM.
    d = call("Je trouve ce banc magnifique, vraiment, absolument.")
    assert d["clean"] is True
    assert d["hits"] == []


def test_g10_batch_et_mcp_conus():
    r = client.post("/api/v1/batch", json={"tool": "text_claimsweep",
                        "payloads": [
                            {"text": "Everyone knows."},
                            {"text": "clean copy here."}]})
    assert r.status_code == 200
    b = r.json()
    assert b["results"][0]["result"]["hits"] == ["everyone knows"]
    assert b["results"][1]["result"]["clean"] is True
    names = [t["name"] for t in client.post("/mcp", json={
        "jsonrpc": "2.0", "id": 1, "method": "tools/list"}).json()["result"]["tools"]]
    assert "text_claimsweep" in names


def test_g11_table_partagee_pas_dupliquee():
    # la porte et le CI juegent avec UNE SEULE table (import, pas copie)
    import claimsweep
    import subprocess
    src = open("scripts/copy-audit.py", encoding="utf-8").read()
    assert "from claimsweep import" in src or "claimsweep.MARKERS" in src
    assert "personne ne dit" in [m.lower() for m in claimsweep.MARKERS]
