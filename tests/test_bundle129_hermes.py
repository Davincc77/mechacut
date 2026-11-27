# Bundle 129_hermes — pdf_provenance conforme a ISO 32000-1 (v1.52.0).
# Douleur mesuree par Probe (vague 2, banques de PDF) : 33/55 réponses
# fausses ou vides. Les cinq racines, chacune avec son piège tracé main :
#   1. le scan global dernier-gagnant ramassait les /Producer des diction-
#      naires Info EMBEDDES (§14.3.3 : l'Info du document est celui que le
#      trailer nomme) — deux verdicts arXiv inverses a eux seuls ;
#   2. les chaines HEX <...> n'etaient pas lues (13 producteurs ratés) ;
#   3. UTF-16BE a BOM rendu en latin-1 = dechets (14 producteurs faux) ;
#   4. une date sans offset rendue null — la grammaire PDF rend l'offset
#      OPTIONNEL ; l'aveu honnete est « naive », pas null ; et « OHH »
#      seul (+01) est légal aussi ;
#   5. created_before_modified rendait True quand created == modified
#      (Scout, 2/3 ANJ) — « <= » ne s'appelle pas « before » ;
#   plus Probe#3 : le recu sha256 etait identique pour des inputs
#   differents (hash de la SORTIE seule) — le sha de l'ENTREE est rendu.
#
# Doctrine conservee, pas amendue : le COMPTE global des occurrences
# (producer_count) reste la preuve des generations coexistantes (rangee
# 16 du dossier MiCA) ; seul le VALEUR rendue change de source.
# L'encrypted ne rend plus jamais le ciphertext comme producteur.
import base64
import hashlib

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _prov(pdf_bytes):
    r = client.post("/api/v1/pdf/provenance",
                    json={"pdf_b64": base64.b64encode(pdf_bytes).decode()})
    return r.status_code, r.json()


def _wrap(info_body, trailer_extra=b"", extra_body=b"", decoy_stream=b""):
    """Minimal real PDF: object 1 = catalog, object 2 = the /Info dict,
    page tree kept deliberately absent (this tool never reads pages)."""
    objs = [
        b"1 0 obj << /Type /Catalog >> endobj\n",
        b"2 0 obj << " + info_body + b" >> endobj\n",
    ]
    if decoy_stream:
        objs.append(b"3 0 obj << /Length %d >> stream\n" % len(decoy_stream)
                    + decoy_stream + b"\nendstream endobj\n")
    body = b"%PDF-1.4\n" + b"".join(objs) + extra_body
    xref_off = len(body)
    n = len(objs)
    xref = b"xref\n0 %d\n" % (n + 1)
    xref += b"0000000000 65535 f \n"
    for i in range(n):
        # offsets are decorative here — the tool resolves /Info by object
        # NUMBER from the trailer, then finds "N G obj"; xref parsing is
        # out of scope and SAID so.
        xref += b"0000000000 00000 n \n"
    trailer = (b"trailer << /Size %d /Info 2 0 R%s >>\n"
               % (n + 1, trailer_extra))
    return body + xref + trailer + b"startxref\n%d\n%%%%EOF\n" % xref_off


# ---------- 1. le trailer nomme l'Info ; les decoys embeches ne gagnent
# ---------- plus, mais leur preuve reste comptee

def test_p4_decoy_embedde_ne_dict_plus_la_valeur():
    decoy = (b"<< /Producer b\"EVIL 9\" /CreationDate (D:19990101000000Z)"
             b" >> put /Producer (EVIL 9) /CreationDate (D:19990101000000Z)")
    pdf = _wrap(b"/Producer (Acrobat (W) 5.0) /CreationDate "
               b"(D:20010101000000+01'00')", decoy_stream=decoy)
    s, d = _prov(pdf)
    assert s == 200
    assert d["producer"] == "Acrobat (W) 5.0"      # celui du trailer
    assert d["producer_count"] == 2                # la preuve survit
    assert d["info_resolution"] == "trailer"


# ---------- 2. chaines HEX ----------

def test_p3_hex_producteur_decode():
    hexprod = b"<FEFF0041007000610074006300680065>"   # UTF-16BE "Apatche"
    pdf = _wrap(b"/Producer " + hexprod + b" /CreationDate "
                b"(D:20150605040302Z)")
    s, d = _prov(pdf)
    # or du trace a main : la TABLE (octets hex) avait raison, mon oeil
    #avait ecrit « Apche ». Le gold se recale sur la table, jamais l'inverse.
    assert s == 200 and d["producer"] == "Apatche"


def test_p3b_hex_producteur_latin():
    pdf = _wrap(b"/Producer <47535420392E32> /CreationDate "
                b"(D:20150605040302Z)")   # "GST 9.2" en hex simple
    s, d = _prov(pdf)
    assert d["producer"] == "GST 9.2"


# ---------- 3. UTF-16BE a BOM en chaine litterale ----------

def test_p2_utf16be_bom_decode():
    # \376\377 BOM puis "Qt" en UTF-16BE litteral
    val = b"(\\376\\377\\000Q\\000t)"
    pdf = _wrap(b"/Producer " + val + b" /CreationDate (D:20100101000000Z)")
    s, d = _prov(pdf)
    assert d["producer"] == "Qt"


# ---------- 4. dates : offset optionnel = NAIVE dit ; OHH seul = légal ----

def test_p7_naive_est_dit_pas_null():
    pdf = _wrap(b"/Producer (Z) /CreationDate (D:20020319110136)")
    s, d = _prov(pdf)
    assert d["created"] == "2002-03-19T11:01:36"
    assert "created" in d["dates_naive"]


def test_p8_offset_heures_seules_accepte():
    # « +01 » sans minutes : la grammaire PDF l'autorise ; null etait
    # notre cecite, pas l'absence de l'information.
    pdf = _wrap(b"/Producer (Zenodo) /CreationDate (D:20020319110136+01)")
    s, d = _prov(pdf)
    assert d["created"] == "2002-03-19T11:01:36+01:00"


# ---------- 5. Scout : equal n'est PAS before ----------

def test_p6_created_equal_modified_rend_false_et_le_dit():
    pdf = _wrap(b"/Producer (ANJ) /CreationDate (D:20240101120000Z) "
                b"/ModDate (D:20240101120000Z)")
    s, d = _prov(pdf)
    assert d["created_before_modified"] is False
    assert d["date_order"] == "equal"


def test_p6b_mixed_naive_vs_zoned_ne_devine_pas():
    pdf = _wrap(b"/Producer (M) /CreationDate (D:20240101120000) "
                b"/ModDate (D:20240101130000Z)")
    s, d = _prov(pdf)
    assert d["created_before_modified"] is None
    assert d["date_order"] == "unknown_mixed_naive_zoned"


# ---------- Probe#3 : le recu est lie a l'input ----------

def test_p9_source_sha_differente_pour_octets_differents():
    pdf1 = _wrap(b"/Producer (SAME) /CreationDate (D:20010101000000Z)",
                 extra_body=b"% v1\n")
    pdf2 = _wrap(b"/Producer (SAME) /CreationDate (D:20010101000000Z)",
                 extra_body=b"% v2 other bytes\n")
    s, d1 = _prov(pdf1)
    s, d2 = _prov(pdf2)
    assert d1["source_sha256"] == hashlib.sha256(pdf1).hexdigest()
    assert d1["source_sha256"] != d2["source_sha256"]


# ---------- can-fail : le fallback nomme quand le trailer ne dit rien ----

def test_p10_fallback_nomme_sans_trailer_info():
    pdf = _wrap(b"/Producer (Orphan) /CreationDate (D:20010101000000Z)")
    pdf = pdf.replace(b"/Info 2 0 R", b"")   # trailer muet
    s, d = _prov(pdf)
    assert d["producer"] == "Orphan"          # l'ancien scan, mais
    assert d["info_resolution"] == "fallback_global_scan"  # c'est DIT


# ---------- encrypted : jamais de ciphertext rendu comme producteur ------

def test_p11_encrypted_ne_rit_pas_garbage():
    body = _wrap(b"/Producer (\\293\\001\\255\\377\\201) /CreationDate "
                 b"(D:20010101000000Z)", trailer_extra=b" /Encrypt 4 0 R")
    body += b"4 0 obj << /Filter /Standard /V 2 >> endobj\n"
    s, d = _prov(body)
    assert d["encrypted"] is True
    assert d["producer"] is None
    assert d["producer_unreadable_encrypted"] is True
