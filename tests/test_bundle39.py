"""Bundle 39 — check/format (formatkit). Douleur HN 50404144 : « the
field is valid per JSON schema but per hidden schema only particular
strings are valid ». Chaque attendu est calculé à la main depuis la
spec citée dans le module."""
import sys
sys.path.insert(0, ".")
import formatkit
import main
import pytest
from fastapi.testclient import TestClient

client = TestClient(main.app)


def cf(payload, formats):
    return formatkit.check_format(payload, formats)


def test_hidden_schema_traps_all_caught():
    r = cf({"due": "2026-02-30",        # 30 février : passe type:string
            "v": "v1.2.3",              # leading v interdit par semver.org
            "id": "550e8400e29b41d4a716446655440000",  # uuid sans tirets
            "amount": "1 234,56"},
           {"$.due": "date-iso", "$.v": "semver",
            "$.id": "uuid", "$.amount": "decimal-string"})
    assert r["valid"] is False
    paths = {v["path"] for v in r["violations"]}
    assert paths == {"$.due", "$.v", "$.id", "$.amount"}
    why = {v["path"]: v["why"] for v in r["violations"]}
    assert "calendar" in why["$.due"]
    assert "leading v" in why["$.v"]
    assert "8-4-4-4-12" in why["$.id"]
    assert "money_columns" in why["$.amount"]   # la passerelle est dans
    #  la réparation elle-même


def test_valid_clean_and_wildcards():
    r = cf({"rows": [{"d": "2026-12-31", "c": "eur", "p": "BE"},
                     {"d": "2028-02-29", "c": "BRL", "p": "PT"}],
            "t": "23:59:60",           # seconde intercalaire : RFC 3339
            "ptr": "/a/b~1c"},
           {"$.rows[*].d": "date-iso", "$.rows[*].c": "currency-iso",
            "$.rows[*].p": "country-iso", "$.t": "time-iso",
            "$.ptr": "json-pointer"})
    assert r["valid"] is True, r["violations"]
    assert r["formats_checked"] == 8   # 2 rangs × 3 champs + t + ptr


def test_non_string_value_is_itself_the_trash():
    r = cf({"n": 1234.56}, {"$.n": "decimal-string"})
    assert not r["valid"]
    v = r["violations"][0]
    assert "validates STRINGS" in v["why"]


def test_unknown_path_and_format_refused_by_name():
    r = cf({"a": "2026-01-01"}, {"$.zz": "date-iso"})
    assert any("matches nothing" in v["why"] for v in r["violations"])
    with pytest.raises(formatkit.FormatError) as e:
        cf({}, {"$.a": "date"})
    assert "closed set" in str(e.value)
    with pytest.raises(formatkit.FormatError):
        cf({}, {})


def test_leap_year_semver_prerelease_edges():
    r = cf({"d": "2025-02-29", "s": "1.0.0-alpha+build.1"},
           {"$.d": "date-iso", "$.s": "semver"})
    assert r["valid"] is False        # 2025 n'est pas bissextile
    assert "calendar" in r["violations"][0]["why"]
    ok = cf({"s": "1.0.0-alpha.beta.11"}, {"$.s": "semver"})
    assert ok["valid"]                 # grammaire officielle autorise


def test_endpoint_stability_and_canon():
    body = {"payload": {"due": "2026-02-30"}, "formats":
            {"$.due": "date-iso"}}
    r1 = client.post("/api/v1/check/format", json=body).json()
    r2 = client.post("/api/v1/check/format", json=body).json()
    assert r1 == r2 and r1["violations"][0]["expected"] == "date-iso"
    assert r1["sha256"] == main.canon(
        {k: v for k, v in r1.items() if k != "sha256"})
