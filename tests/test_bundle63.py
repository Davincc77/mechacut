"""Bundle 62 — P2 + P3 de la sonde de contrat (gold B002/B003, faits à
la main ; c'est le produit qui est venu à eux)."""
from fastapi.testclient import TestClient

import main

C = TestClient(main.app)

CSV2 = ('id,name,amount,date,category\n'
        '1,Maria Silva,2524.20,2026-01-05,billing\n'
        '2,José Almeida,"1,059.69",05/01/2026,ops\n'
        '3,Aïcha Benali,1854.82,2026/01/05,security\n')


def _ct(**kw):
    return C.post("/api/v1/recipe/clean-table", json=kw)


def test_p2_dates_iso_and_amounts_literal():
    b = _ct(csv=CSV2).json()
    rows = {str(r["id"]): r for r in b["rows"]}
    assert rows["1"]["amount"] == "2524.20"      # LITTÉRAL, pas 2524.2
    assert rows["2"]["amount"] == "1059.69"      # milliers virés
    assert rows["2"]["date"] == "2026-01-05"     # day-first, règle nommée
    assert rows["3"]["date"] == "2026-01-05"
    notes = " ".join(b["fix_notes"])
    assert "dates_iso_normalized" in notes and "dates_rule:dmy" in notes


def test_p2_mdy_override_is_explicit():
    b = _ct(csv=CSV2, dates_format="mdy").json()
    r2 = {str(r["id"]): r for r in b["rows"]}["2"]
    assert r2["date"] == "2026-05-01"          # 5 MAI sous mdy déclaré
    # note : 05 sous la position month — mdy lit month=05 day=01
    b2 = _ct(csv=CSV2, dates_format="dmy").json()
    assert _ct(csv=CSV2).json()["rows"] == b2["rows"]  # défaut = dmy


def test_p2_bad_rule_named():
    r = _ct(csv=CSV2, dates_format="auto")
    assert r.status_code == 400
    err = r.json()["errors"][0]
    assert err["field"] == "dates_format" and "CLOSED" in err["message"]


def test_p3_fr_space_thousands_not_fragmented():
    note = ("Constat : 12 450,75 € gelés puis 3 200,00 € en attente ; "
            "coût 45,90 € ; périmètre 12,5 % du flux.")
    b = C.post("/api/v1/recipe/facts", json={"text": note}).json()
    inv = b["inventory"]
    assert "12450.75" in inv["money"]
    assert "12" not in inv.get("number", [])
    assert "12.5%" in inv["percent"]
    from decimal import Decimal
    assert Decimal(b["total_money"]) == sum(Decimal(m)
                                            for m in inv["money"])


def test_p3_nbsp_is_the_same_space():
    # leçon ③ de la sonde : l'espace FR est U+00A0 — fatal en bytes.
    note = "dégât : 12\u00a0450,75 € puis 8\u00a0900,00 €."
    b = C.post("/api/v1/recipe/facts", json={"text": note}).json()
    assert "12450.75" in b["inventory"]["money"]
    assert "8900.00" in b["inventory"]["money"]
