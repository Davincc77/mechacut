# -*- coding: utf-8 -*-
"""bundle125_hermes — /api/v1/text/mojibake-scan : le scan deux couches,
sans reparer. Vient du recensement LATAM (vague 3) : 37 billets sales
sur 120, et le piege qui a fausse une passe entiere — « sera » ne DOIT
pas compter comme « sera casse ». Le dossier (door sha 23ac5fb1…,
SUSPECT-DUPLICATE arbitre OUTIL NEUF par Vince 26-11 : un outil qui
modifie le texte qu'il diagnostique efface la preuve de son propre
jugement — text_decode repare, ici on lit seulement).

AUDIT DU DOSSIER AVANT BUILD : ses 5 golds sont justes mais sous-entendus
— encoding_hits compte des FAMILLES DISTINCTES touchees (le gold 5 porte
DEUX sequences corrompues de la MEME famille cp1252 et attend 1), et le
dossier omettait des cles que le contrat rend TOUJOURS (forme fermee,
jamais de cle absente : determinisme). Precisions retravees ici,
historisees dans VERDICTS — dossier public intact.

Familles (table fermee, motivee par le corpus public brésilien) :
  latin1_accents : U+00C3 ou U+00C2 (Ã, Â) suivis d'un octet de la
    page CP1252/Latin-1 de combinaison (\u0080-\u00BF) — tÃªm, Ã©, Â«.
  cp1252_punct   : â suivi de € ou d'un des signes \u009C-\u009F/œ —
    les guillemets et tirets UTF-8 lus en CP1252 (â€œ, â€™).

Needles (contexuels, nommes — c'est la moitie de l'outil) :
  serã : la forme cassee de SERAO. Compte SEULEMENT si le mot ne
    continue pas : « serã confirmes » = 1 ; « seront » (serão) = 0
    (le a final est la suite legitime, pas une troncature).
  esta : idem pour ESTAO.

Golds traces a la main sur les textes du dossier :

1. « remarcatões tÃªm uma taxa adicional » — tÃªm = 1 token latin1.
   -> encoding_hits 1, families {latin1_accents: 1, cp1252_punct: 0},
      needle_hits {serã: 0, estã: 0}.
2. « Os voos serão confirmados em breve » — serão légitime : ã suivi
   de o, ni famille ni needle. -> 0 partout, CP1252 0.
3. « Os voos serã confirmados » — serã + espace = needle 1, aucune
   famille (ã minuscule hors motif). -> encoding_hits 0, serã 1.
4. « CONTRATAÇÃO DAS MANHÃ » — ÇÃO : Ã suivi de O (0x4F, hors page),
   MANHÃ final : Ã sans suite. Aucune famille, aucun needle (pas de
   serã/estã) -> 0 partout. C'est LE gold qui prouve que l'outil ne
   bouffe pas le portugais correct en majuscules.
5. « tarifa â€œpremiumâ€ » — deux tokens cp1252 (â€œ + â€), UNE SEULE
   famille distincte -> encoding_hits 1, cp1252_punct 2.

ROUTE : /api/v1/text/mojibake — le « -scan » est tombe dans
l'elage budget du manifeste (b125) ; la 1re passe de ce fichier
postait /mojibake-scan et recevait 404 PARCE QUE C'ETAIT VRAI — la
porte avait raison, le test s'incline (precedent : le gold s'incline
devant la donnee).

can-fail : seront ne JAMAIS compte comme serã (gold 2 rejoué en
assertion d'invariant) ; texte propre -> zero partout, pas de cle
absente ; entree vide -> 400 nommee ; non-string -> 400.
"""
import json

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def scan(text):
    r = client.post("/api/v1/text/mojibake", json={"text": text})
    assert r.status_code == 200, r.text
    return r.json()


def test_g1_latin1_family():
    d = scan("remarcações tÃªm uma taxa adicional")
    assert d["encoding_hits"] == 1
    assert d["families"]["latin1_accents"] == 1
    assert d["families"]["cp1252_punct"] == 0
    assert d["needle_hits"] == {"serã": 0, "estã": 0}


def test_g2_correct_word_never_a_needle():
    d = scan("Os voos serão confirmados em breve")
    assert d["encoding_hits"] == 0
    assert d["needle_hits"]["serã"] == 0


def test_g3_broken_word_is_the_needle():
    d = scan("Os voos serã confirmados")
    assert d["encoding_hits"] == 0
    assert d["needle_hits"]["serã"] == 1


def test_g4_uppercase_pt_is_clean():
    d = scan("CONTRATAÇÃO DAS MANHÃ")
    assert d["encoding_hits"] == 0
    assert d["needle_hits"] == {"serã": 0, "estã": 0}


def test_g5_two_tokens_one_family():
    d = scan("tarifa â€œpremiumâ€")
    assert d["encoding_hits"] == 1
    assert d["families"]["cp1252_punct"] == 2
    assert d["families"]["latin1_accents"] == 0


def test_shape_is_closed_always():
    d = scan("nothing broken here at all")
    assert set(d.keys()) >= {"encoding_hits", "families", "needle_hits",
                             "verdict", "sha256"}
    assert set(d["families"].keys()) == {"latin1_accents", "cp1252_punct"}
    assert set(d["needle_hits"].keys()) == {"serã", "estã"}
    assert d["encoding_hits"] == 0
    assert d["verdict"] == "CLEAN"


def test_can_fail_serao_never_counts():
    # si quelqu'un « repare » le needle en simple substring, ce test meurt
    for word in ("serão", "Serão", "serão,"):
        assert scan("les %s partent" % word)["needle_hits"]["serã"] == 0


def test_verdict_names_the_dirty_layer():
    d = scan("Os voos serã confirmados")
    assert d["verdict"] == "NEEDLES"
    d = scan("tarifa â€œpremiumâ€")
    assert d["verdict"] == "ENCODING"
    d = scan("tÃªm serã")
    assert d["verdict"] == "BOTH"


def test_refusals_are_named():
    r = client.post("/api/v1/text/mojibake", json={"text": ""})
    assert r.status_code == 400
    assert "text" in json.dumps(r.json())
    r = client.post("/api/v1/text/mojibake", json={"text": 12})
    assert r.status_code == 400
