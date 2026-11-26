# -*- coding: utf-8 -*-
"""bundle124_hermes — /api/v1/pdf/provenance : la provenance lue dans les
octets du PDF. Ne vient pas de la theorie : du forensic SENAT (template
aux octets identiques sur 15 mois, CreationDate D:20261014160317, Producer
iOS Quartz) et du case study LATAM — les dates d'un PDF racontent s'il a
ete regenere, dans quel outil, dans quel ordre.

AUDIT DU DOSSIER AVANT BUILD (grave dans VERDICTS, pas efface) :
le dossier ELIGIBLE (door sha 961167b7c1979716, 26-11) portait UN SEUL
gold, et ce gold etait FAUX de semantique : « created_before_modified:
true » rendu alors que « modified: null » — on ne peut pas etre AVANT une
date absente. Comparaison a vide n'est pas un fait. Le build corrige la
semantique : le champ vaut null quand une des deux dates manque, et
l'outil ne rend JAMAIS true par defaut.

Attendus CALCULES A LA MAIN (octets relus) — jamais recopies du module :

G1 (le gold du dossier, corrige) : un seul /Producer, /CreationDate
   D:20180517120000Z, AUCUN /ModDate
   -> producer "ProvenanceKit 1.0", created "2018-05-17T12:00:00Z",
      modified null, created_before_modified NULL (pas true : rien a
      comparer). Z reste Z : l'offset des octets voyage, jamais rebase.

G2 (deux dates, ordre normal) : Creation D:20180517120000Z,
   Mod D:20190101000000Z -> created < modified -> TRUE.

G3 (mod before created — le signal de regeneration) : Creation
   D:20200101000000Z, Mod D:20190101000000Z -> FALSE. Un document
   « modifie avant sa creation » ment quelque part : l'outil le NOMME,
   ne l'excuse pas.

G4 (offset nominal) : Creation D:20200101090000+01'00'
   -> "2020-01-01T09:00:00+01:00" — les apostrophes de la spec PDF
   deviennent les deux-points ISO, le signe voyage.

G5 (mise a jour incrementale — la loi du Senat) : DEUX /Producer dans
   les octets ("First" puis "Second") : le DERNIER gagne (l'objet Info
   le plus recent ecrase, comme un re-export iOS Quartz qui ajoute sa
   generation en fin de fichier), et le nombre d'occurrences est DIT :
   producer "Second", producer_count 2 — la preuve que deux generations
   coexistent ne disparait pas.

G6 (aucun Info) : %PDF-1.4 nu sans dates -> les quatre champs null,
   producer_count 0. Absence nommee, jamais 0 par devinette.

Rejets NOMMES : pas %PDF en tete -> 400 (champ pdf_b64, « is not a
PDF ») ; base64 invalide -> 400. Dates mal formees -> le champ part
null et « created_before_modified » null — une date illisible n'est
pas une date inventee.

Renommage des champs : le dossier nommait created_before_modified —
nom CONSERVE (l'histoire du dossier reste lisible), valeur corrigee.
"""
import base64
import hashlib  # noqa: F401 — les golds sont des bytes, pas des hashes

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _pdf(inner):
    return base64.b64encode(b"%PDF-1.4\n" + inner + b"\n%%EOF\n").decode()


def call(inner_or_b64, raw=False):
    body = inner_or_b64 if raw else _pdf(inner_or_b64)
    return client.post("/api/v1/pdf/provenance", json={"pdf_b64": body})


def info(producer=None, created=None, mod=None, twice=False):
    parts = ["<<"]
    if producer:
        parts.append("/Producer (%s)" % producer)
    if twice:
        parts.append("/Producer (%s)" % producer)
    if created:
        parts.append("/CreationDate (%s)" % created)
    if mod:
        parts.append("/ModDate (%s)" % mod)
    parts.append(">>")
    return " ".join(parts).encode()


def body_with(info_obj):
    return (b"1 0 obj<</Type/Catalog>>endobj "
            b"2 0 obj" + info_obj + b"endobj")


def test_g1_dossier_gold_corrected():
    r = call(body_with(info(producer="ProvenanceKit 1.0",
                            created="D:20180517120000Z")))
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["producer"] == "ProvenanceKit 1.0"
    assert d["created"] == "2018-05-17T12:00:00Z"
    assert d["modified"] is None
    # LA correction : une date absente ne se compare pas.
    assert d["created_before_modified"] is None
    assert d["producer_count"] == 1


def test_g2_normal_order():
    d = call(body_with(info(created="D:20180517120000Z",
                            mod="D:20190101000000Z"))).json()
    assert d["created"] == "2018-05-17T12:00:00Z"
    assert d["modified"] == "2019-01-01T00:00:00Z"
    assert d["created_before_modified"] is True


def test_g3_mod_before_created():
    d = call(body_with(info(created="D:20200101000000Z",
                            mod="D:20190101000000Z"))).json()
    assert d["created_before_modified"] is False


def test_g4_named_offset():
    d = call(body_with(info(created="D:20200101090000+01'00'"))).json()
    assert d["created"] == "2020-01-01T09:00:00+01:00"


def test_g5_incremental_last_wins():
    d = call(body_with(info(producer="Second", twice=True,
                            created="D:20180517120000Z"))).json()
    # Deux generations dans les octets : la derniere parle, le compte reste.
    # body avec twice met le DEUXIEME producteur — attention: la fonction
    # info() ecrit producer deux fois avec la MEME valeur; on teste ici le
    # comptage. L'ecrasement par valeur differente est G5b.
    assert d["producer_count"] == 2


def test_g5b_incremental_overwrite():
    inner = (b"1 0 obj<</Type/Catalog>>endobj "
             b"2 0 obj<</Producer (First)>>endobj "
             b"3 0 obj<</Producer (Second)>>endobj")
    d = call(inner).json()
    assert d["producer"] == "Second"
    assert d["producer_count"] == 2


def test_g6_bare_pdf_all_null():
    d = call(b"1 0 obj<</Type/Catalog>>endobj").json()
    assert d["producer"] is None
    assert d["created"] is None
    assert d["modified"] is None
    assert d["created_before_modified"] is None
    assert d["producer_count"] == 0


def test_unreadable_date_is_named_null():
    # une date illegible n'est PAS une date inventee
    d = call(body_with(info(created="D:not-a-date"))).json()
    assert d["created"] is None
    assert d["created_before_modified"] is None


def test_can_fail_g1_is_not_true():
    # si quelqu'un « repare » le champ en true par defaut, ce test meurt
    d = call(body_with(info(created="D:20180517120000Z"))).json()
    assert d["created_before_modified"] is not True


def test_refusals_are_named():
    r = call(base64.b64encode(b"NOTA PDF AT ALL").decode(), raw=True)
    assert r.status_code == 400
    assert "pdf" in r.text.lower()
    r = client.post("/api/v1/pdf/provenance", json={"pdf_b64": "!!!bad"})
    assert r.status_code == 400
