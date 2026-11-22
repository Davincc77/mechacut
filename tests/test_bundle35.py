"""Bundle 35 — xml/to_json (xmlkit). Oracle = xmltodict, test-only.
La seule divergence (whitespace-only → null) est NOTRE règle publiée,
normalisée explicitement dans le comparateur, jamais gommée."""
import sys
sys.path.insert(0, ".")
import json
import main
import xmlkit
import digitkit
import pytest
from fastapi.testclient import TestClient

client = TestClient(main.app)


def oracle_norm(x):
    """règle 4/5 de nos réponses : whitespace-only text → null."""
    if isinstance(x, dict):
        return {k: oracle_norm(v) for k, v in x.items()}
    if isinstance(x, list):
        return [oracle_norm(v) for v in x]
    if isinstance(x, str) and x.strip() == "":
        return None
    return x


def test_identity_with_xmltodict_oracle():
    xmltodict = pytest.importorskip("xmltodict")
    docs = [
        '<note><to>Tove</to><body>Hi</body></note>',
        '<catalog><book id="bk101"><price>44.95</price>'
        '</book></catalog>',
        '<catalog><book id="a"><t>1</t></book>'
        '<book id="b"><t>2</t></book></catalog>',
        '<root a="1"><!-- c --><?pi x?><empty/><ws>   </ws>'
        '<mix>text <b>bold</b></mix></root>',
        '<soap:Envelope '
        'xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
        '<soap:Body><ns:x xmlns:ns="urn:n">v</ns:x></soap:Body>'
        '</soap:Envelope>',
        '<p>ligne1\n  ligne2</p>',
    ]
    for d in docs:
        mine = xmlkit.to_json(d)["json"]
        ref = json.loads(json.dumps(
            xmltodict.parse(d, strip_whitespace=False)))
        assert oracle_norm(mine) == oracle_norm(ref), d[:40]


def test_one_item_bug_and_force_array():
    one = '<catalog><book id="a"><t>1</t></book></catalog>'
    plain = xmlkit.to_json(one)["json"]
    assert isinstance(plain["catalog"]["book"], dict)   # la vérité du doc
    forced = xmlkit.to_json(
        one, force_array=["catalog/book"])["json"]
    assert forced["catalog"]["book"] == [{"@id": "a", "t": "1"}]
    two = '<c><b>1</b><b>2</b></c>'
    assert xmlkit.to_json(two)["json"]["c"]["b"] == ["1", "2"]
    rules = xmlkit.to_json(
        one, force_array=["catalog/book"])["rules_applied"]
    assert any("force_array=['catalog/book']" in r for r in rules)


def test_coerce_keeps_identifiers_as_strings():
    out = xmlkit.to_json(
        '<r><n>00713</n><m>42</m><b>true</b><f>1.5</f>'
        '<z>+7</z><w>1 000</w></r>', coerce=True)["json"]["r"]
    assert out == {"n": "00713", "m": 42, "b": True, "f": 1.5,
                   "z": "+7", "w": "1 000"}
    plain = xmlkit.to_json('<r><m>42</m></r>')["json"]["r"]
    assert plain == {"m": "42"}          # défaut : chaînes, déclaré


def test_refus_par_leur_nom():
    with pytest.raises(xmlkit.XmlError) as ei:
        xmlkit.to_json('<!DOCTYPE x [<!ENTITY e "x">]><x/>')
    assert "DTD" in str(ei.value)
    with pytest.raises(xmlkit.XmlError) as ei:
        xmlkit.to_json('<a><b></a>')
    assert "malformed" in str(ei.value)
    with pytest.raises(xmlkit.XmlError) as ei:
        xmlkit.to_json('')
    assert "malformed" in str(ei.value)   # expat: no element found
    with pytest.raises(xmlkit.XmlError) as ei:
        xmlkit.to_json('<a>x</a>', force_array=[42])
    assert "slash paths" in str(ei.value)


def test_discarded_are_counted_not_silent():
    r = xmlkit.to_json('<a><!-- c1 --><!-- c2 --><?pi x?><b/></a>')
    assert r["discarded"] == {"comments": 2,
                              "processing_instructions": 1}
    assert r["json"] == {"a": {"b": None}}


def test_endpoint_and_canon():
    body = {"xml": "<feed><entry><t>un</t></entry></feed>",
            "force_array": ["feed/entry"]}
    r1 = client.post("/api/v1/xml/to_json", json=body)
    assert r1.status_code == 200
    d = r1.json()
    assert d["json"] == {"feed": {"entry": [{"t": "un"}]}}
    assert len(d["rules_applied"]) == 10
    assert d["sha256"] == main.canon(
        {k: v for k, v in d.items() if k != "sha256"})
    r2 = client.post("/api/v1/xml/to_json",
                     json={"xml": "<!DOCTYPE a><a/>"})
    assert r2.status_code == 400 and "DTD" in r2.text


def test_iban_pointer_instead_of_silence():
    d = digitkit.checkdigit(mode="check",
                            value="FR7630006000011234567890189")
    assert d["pointer"].startswith("this looks like an IBAN")
    assert d["valid_candidates"] == []
    # un vrai ISBN ne reçoit PAS le pointeur (aucune régression)
    i = digitkit.checkdigit(mode="check", value="9780306406157")
    assert "pointer" not in i and i["valid_candidates"]
