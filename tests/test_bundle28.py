"""Bundle 28 — OPS/FORMES. Lot 1: hash/hmac.
Attendues = vecteurs publiés RFC 4231 (extraits du texte officiel, section 4),
jamais recalculés par le produit lui-même."""
import sys
sys.path.insert(0, ".")
import main
from fastapi.testclient import TestClient

client = TestClient(main.app)

# RFC 4231 section 4.2 (TC1) et 4.3 (TC2)
TC1_KEY = "0b" * 20
TC1_DATA = "Hi There"
TC1_SHA256 = ("b0344c61d8db38535ca8afceaf0bf12b"
              "881dc200c9833da726e9376c2e32cff7")
TC1_SHA512 = ("87aa7cdea5ef619d4ff0b4241a1d6cb0"
              "2379f4e2ce4ec2787ad0b30545e17cde"
              "daa833b7d6b8a702038b274eaea3f4e4"
              "be9d914eeb61f1702e696c203a126854")
TC2_KEY = "Jefe"
TC2_DATA = "what do ya want for nothing?"
TC2_SHA256 = ("5bdcc146bf60754e6a042426089575c7"
              "5a003f089d2739839dec58b964ec3843")


def hmac(**kw):
    r = client.post("/api/v1/hash/hmac", json=kw)
    assert r.status_code == 200, r.text
    return r.json()


def test_rfc4231_tc1_sha256():
    d = hmac(message=TC1_DATA, key=TC1_KEY, key_kind="hex",
             algo="sha256")
    assert d["hex"] == TC1_SHA256


def test_rfc4231_tc1_sha512():
    d = hmac(message=TC1_DATA, key=TC1_KEY, key_kind="hex",
             algo="sha512")
    assert d["hex"] == TC1_SHA512


def test_rfc4231_tc2_text_key():
    d = hmac(message=TC2_DATA, key=TC2_KEY, algo="sha256")
    assert d["hex"] == TC2_SHA256


def test_verify_match_and_mismatch():
    good = hmac(message="payload", key="s3cret", algo="sha256")
    v = hmac(message="payload", key="s3cret", signature=good["hex"])
    assert v["match"] is True
    v2 = hmac(message="payload", key="s3cret",
              signature="0x" + "ab" * 32)
    assert v2["match"] is False


def test_unknown_algo_free_400():
    r = client.post("/api/v1/hash/hmac",
                    json={"message": "x", "key": "k", "algo": "blake3"})
    assert r.status_code == 400
    assert r.json()["errors"][0]["field"] == "algo"
    assert "sha256" in r.json()["errors"][0]["message"]


def test_deterministic_sha():
    a = hmac(message="x", key="k")
    b = hmac(message="x", key="k")
    assert a["sha256"] == b["sha256"]


def ulid(**kw):
    r = client.post("/api/v1/id/ulid", json=kw)
    assert r.status_code == 200, r.text
    return r.json()


def pkg(**kw):
    r = client.post("/api/v1/pkg/name", json=kw)
    assert r.status_code == 200, r.text
    return r.json()


def test_ulid_all_zeros_hand_computed():
    # ts=0 -> 10 premiers caractères '0'; entropy 10 octets nuls -> '0'*16
    d = ulid(mode="make", timestamp_ms=0, entropy="00" * 10)
    assert d["ulid"] == "0" * 26


def test_ulid_max_entropy_is_all_Z():
    # 80 bits à 1 -> chaque digit base32 = 31 = 'Z'
    d = ulid(mode="make", timestamp_ms=0, entropy="ff" * 10)
    assert d["ulid"] == "0" * 10 + "Z" * 16
    p = ulid(mode="parse", ulid=d["ulid"])
    assert p["timestamp_ms"] == 0
    assert p["entropy_hex"] == "ff" * 10


def test_ulid_ts_one():
    d = ulid(mode="make", timestamp_ms=1, entropy="00" * 10)
    assert d["ulid"] == "0000000001" + "0" * 16


def test_ulid_seed_is_deterministic_idempotency():
    a = ulid(mode="make", timestamp_ms=1234567890123, seed="order-42")
    b = ulid(mode="make", timestamp_ms=1234567890123, seed="order-42")
    assert a["ulid"] == b["ulid"]
    # re-derivation INDÉPENDANTE de l'entropie (cross-impl, pas le produit)
    import hashlib
    C = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    eb = hashlib.sha256(b"mechacut-ulid:order-42").digest()[:10]
    n = int.from_bytes(eb, "big")
    tail = ""
    for _ in range(16):
        tail = C[n & 31] + tail
        n >>= 5
    assert a["ulid"][10:] == tail


def test_ulid_no_hidden_clock():
    r = client.post("/api/v1/id/ulid", json={"mode": "make",
                                             "seed": "x"})
    assert r.status_code == 400  # timestamp_ms exigé, jamais now()


def test_pkg_npm_verdicts():
    assert pkg(name="my-valid_pkg.2")["valid"] is True
    d = pkg(name="My-Awesome")
    assert d["valid"] is False and any("lowercase" in e for e in d["errors"])
    assert d["normalized"] == "my-awesome"
    assert pkg(name=".hidden")["valid"] is False


def test_pkg_pypi_pep503():
    d = pkg(name="Django_REST--framework", kind="pypi")
    assert d["valid"] is True
    assert d["normalized"] == "django-rest-framework"


def test_pkg_docker_grammar():
    assert pkg(name="library/nginx:1.25.3-alpine", kind="docker")["valid"]
    assert pkg(name="Nginx", kind="docker")["valid"] is False
    d = pkg(name="nginx:.badtag", kind="docker")
    assert d["valid"] is False
    assert any("tag" in e for e in d["errors"])
    dg = pkg(name="img@sha256:" + "ab" * 32, kind="docker")
    assert dg["valid"] is True


def jm(items, ops):
    r = client.post("/api/v1/json/map", json={"items": items, "ops": ops})
    assert r.status_code == 200, r.text
    return r.json()


def test_json_map_string_ops_compose_in_order():
    d = jm(["  MiXeD Case  ", "FOO BAR"], [{"op": "strip"},
                                           {"op": "lower"}])
    assert d["mapped"] == ["mixed case", "foo bar"]


def test_json_map_round_is_bankers_half_even():
    # expectations CALCULÉES À LA MAIN sur les décimales :
    # 1.005 -> tie -> pair -> 1.00 ; 2.675 -> tie -> 2.68 (8 pair)
    d = jm([1.005, 2.675], [{"op": "round", "places": 2}])
    assert d["mapped"] == [1.0, 2.68]


def test_json_map_case_families():
    assert jm(["hello world_two"], [{"op": "camel"}])["mapped"] \
        == ["helloWorldTwo"]
    assert jm(["HTTPSProxy v2"], [{"op": "kebab"}])["mapped"] \
        == ["http-s-proxy-v2".replace("-s-", "s-")]  # "https-proxy-v2"


def test_json_map_rejects_open_ops():
    r = client.post("/api/v1/json/map",
                    json={"items": [1], "ops": [{"op": "eval"}]})
    assert r.status_code == 400
    assert "lower" in r.json()["errors"][0]["message"]  # closed alphabet


def fx(amount, rate, to, **kw):
    r = client.post("/api/v1/num/fx",
                    json={"amount": amount, "rate": rate, "to": to, **kw})
    assert r.status_code == 200, r.text
    return r.json()


def test_fx_exact_brl():
    d = fx("100.00", "5.0825", "BRL")
    assert d["result"] == "508.25" and d["minor_units"] == 50825


def test_fx_jpy_zero_decimals_banker():
    # 1000 x 0.0065 = 6.5 -> half_even -> 6 (pair), PAS 7
    d = fx("1000", "0.0065", "JPY")
    assert d["result"] == "6" and d["decimals"] == 0


def test_fx_unknown_currency_names_the_table():
    r = client.post("/api/v1/num/fx",
                    json={"amount": "1", "rate": "1", "to": "XTS9"})
    assert r.status_code == 400
    assert "closed table" in r.json()["errors"][0]["message"]


def test_usage_is_ephemeral_shape():
    d = client.get("/usage.json").json()
    assert d["stored"] is False
    assert {"settled_calls", "failed_settles", "cache_hits_saved",
            "by_route"} <= set(d)


def test_semver_sort_official_precedence_chain():
    # chaîne d'exemple PUBLIÉE sur semver.org (règle 11), dans l'ordre
    chain = ["1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-alpha.beta",
             "1.0.0-beta", "1.0.0-beta.2", "1.0.0-beta.11",
             "1.0.0-rc.1", "1.0.0"]
    r = client.post("/api/v1/semver/sort", json={"versions":
                  list(reversed(chain))})
    assert r.status_code == 200
    assert r.json()["sorted"] == chain
    assert r.json()["highest"] == "1.0.0"


def test_semver_numeric_not_lexicographic():
    r = client.post("/api/v1/semver/sort",
                    json={"versions": ["2.0.0", "10.0.0", "1.0.0"]})
    assert r.json()["sorted"] == ["1.0.0", "2.0.0", "10.0.0"]


def test_semver_parse_parts():
    r = client.post("/api/v1/semver/parse",
                    json={"version": "1.2.3-alpha.1+build.7"})
    d = r.json()
    assert (d["major"], d["minor"], d["patch"]) == (1, 2, 3)
    assert d["prerelease"] == ["alpha", "1"]
    assert d["build"] == ["build", "7"]
    assert d["is_stable"] is False


def test_semver_rejects_leading_zero_and_v_prefix():
    for bad in ("01.2.3", "v1.2.3", "1.2", "1.2.3-01"):
        r = client.post("/api/v1/semver/parse", json={"version": bad})
        assert r.status_code == 400, bad


def test_sanitize_windows_reserved():
    d = client.post("/api/v1/text/sanitize",
                    json={"name": "CON.txt"}).json()
    assert d["safe"] == "_CON.txt" and d["changed"] is True
    assert any("reserved" in w for w in d["warnings"])


def test_sanitize_charset_and_trailing():
    d = client.post("/api/v1/text/sanitize",
                    json={"name": 'a/b:c?.txt  '}).json()
    assert d["safe"] == "a_b_c_.txt"
    # trailing dot+space: warning de strip AVANT charset
    w = " ".join(d["warnings"])
    assert "stripped" in w or "forbidden" in w


def test_sanitize_utf8_budget():
    d = client.post("/api/v1/text/sanitize",
                    json={"name": "é" * 130, "max_bytes": 255}).json()
    assert d["bytes"] <= 255
    assert d["safe"].startswith("é") and len(d["safe"]) == 127  # 254/2


def fi(blob_bytes):
    import base64 as b64
    r = client.post("/api/v1/file/identify",
                    json={"blob": b64.b64encode(blob_bytes).decode()})
    assert r.status_code == 200, r.text
    return r.json()


def test_file_identify_png_signature():
    d = fi(b"\x89PNG\r\n\x1a\n" + b"\x00" * 20)
    assert d["detected"] == "image/png"
    assert d["signature_hex"] == "89504e470d0a1a0a"   # la signature publiée


def test_file_identify_longest_wins_and_zip_family():
    assert fi(b"PK\x03\x04rest")[
        "detected"] == "application/zip"
    # un gzip commence par 1f 8b — pas un PNG tronqué
    assert fi(b"\x1f\x8b\x08\x00junk")["detected"] == "application/gzip"


def test_file_identify_control_soup_is_unknown_not_text():
    d = fi(bytes(range(10, 30, 2)))
    assert d["detected"] is None and "first_bytes_hex" in d


def test_file_identify_plain_text_gate():
    assert fi(b"just words, plainly").get("detected") == "text/text"


def test_punycode_munich_published_example():
    # xn--mnchen-3ya.de = l'exemple IDN publié le plus cité
    d = client.post("/api/v1/text/punycode",
                    json={"domain": "münchen.de"}).json()
    assert d["ascii_form"] == "xn--mnchen-3ya.de"
    assert d["is_idn"] is True
    back = client.post("/api/v1/text/punycode",
                       json={"domain": d["ascii_form"]}).json()
    assert back["unicode_form"] == "münchen.de"


def test_punycode_plain_ascii_not_idn():
    d = client.post("/api/v1/text/punycode",
                    json={"domain": "example.com"}).json()
    assert d["is_idn"] is False and d["ascii_form"] == "example.com"


def test_net_cidr_hand_computed_range():
    d = client.post("/api/v1/net/cidr",
                    json={"cidr": "192.168.1.0/24"}).json()
    assert d["usable_hosts"] == 254
    assert d["network"] == "192.168.1.0"
    assert d["broadcast"] == "192.168.1.255"


def test_net_cidr_rfc3021_point_to_point():
    d = client.post("/api/v1/net/cidr", json={"cidr": "10.0.0.0/31"}).json()
    assert d["usable_hosts"] == 2      # pas -2 sur /31 et /32


def test_net_cidr_contains_ip_and_subnet():
    d = client.post("/api/v1/net/cidr", json={
        "cidr": "10.0.0.0/8", "contains": "10.255.255.255"}).json()
    assert d["contains"]["inside"] is True
    d2 = client.post("/api/v1/net/cidr", json={
        "cidr": "10.0.0.0/8", "contains": "11.0.0.0/16"}).json()
    assert d2["contains"]["inside"] is False


def test_net_cidr_split_hand_verified():
    # /8 split_into=2 -> quatre /10 aux offsets 0, 64, 128, 192
    d = client.post("/api/v1/net/cidr", json={
        "cidr": "10.0.0.0/8", "split_into": 2}).json()
    assert d["subnets"] == ["10.0.0.0/10", "10.64.0.0/10",
                            "10.128.0.0/10", "10.192.0.0/10"]


def test_net_ip_scopes():
    import base64 as b64
    d = client.post("/api/v1/net/ip", json={"value": "::1"}).json()
    assert d["is_loopback"] is True and d["version"] == 6
    d2 = client.post("/api/v1/net/ip",
                     json={"value": "169.254.0.1"}).json()
    assert d2["is_link_local"] is True
    d3 = client.post("/api/v1/net/ip", json={"value": "8.8.8.8"}).json()
    assert d3["is_private"] is False
    assert d3["reverse_dns_name"] == "8.8.8.8.in-addr.arpa"


def test_net_ip_rejects_cidr_and_garbage():
    for bad in ("10.0.0.0/8", "not-an-ip", "999.1.1.1"):
        r = client.post("/api/v1/net/ip", json={"value": bad})
        assert r.status_code == 400, bad


def test_file_encoding_bom_table():
    import base64 as b64
    d = client.post("/api/v1/file/encoding", json={
        "blob": b64.b64encode(b"\xff\xfed\x00n\x00").decode()}).json()
    assert d["encoding"] == "utf-16-le" and d["bom"] == "fffe"
    clean = client.post("/api/v1/file/encoding", json={
        "blob": b64.b64encode("café".encode("utf-8")).decode()}).json()
    assert clean["encoding"] == "utf-8" and clean["declared"] is False
    bad = client.post("/api/v1/file/encoding", json={
        "blob": b64.b64encode("café".encode("cp1252")).decode()}).json()
    assert bad["verdict"] == "undetermined"
    assert bad["first_bad_hex"] == "e9"    # é en latin-1: 0xe9


def gd(**kw):
    r = client.post("/api/v1/geo/distance", json=kw)
    assert r.status_code == 200, r.text
    return r.json()


def test_geo_paris_london_published():
    # 343.5-344 km: la valeur grande-cercle usuellement publiée
    d = gd(a={"lat": 48.8566, "lon": 2.3522},
           b={"lat": 51.5074, "lon": -0.1278})
    assert 343.0 < d["km"] < 344.0


def test_geo_route_is_ordered_sum():
    d = gd(route=[{"lat": 0, "lon": 0}, {"lat": 0, "lon": 1},
                  {"lat": 0, "lon": 2}])
    assert d["legs_m"] == [d["legs_m"][0], d["legs_m"][0]]
    assert abs(d["legs_m"][0] - 111195.1) < 0.5   # 1° équateur, IUGG R
    d2 = gd(route=[{"lat": 0, "lon": 2}, {"lat": 0, "lon": 0}])
    assert d2["total_m"] == d["total_m"]          # somme symétrique


def test_geo_out_of_range_400():
    r = client.post("/api/v1/geo/distance", json={
        "a": {"lat": 95, "lon": 0}, "b": {"lat": 0, "lon": 0}})
    assert r.status_code == 400


def test_geohash_published_spec_example():
    d = client.post("/api/v1/geo/geohash",
                    json={"lat": 42.6, "lon": -5.6,
                          "precision": 5}).json()
    assert d["geohash"] == "ezs42"               # l'exemple du spec
    back = client.post("/api/v1/geo/geohash",
                       json={"geohash": "ezs42"}).json()
    assert abs(back["lat"] - 42.6) < 0.01
    assert back["box"]["lat"][0] < back["lat"] < back["box"]["lat"][1]


def test_geohash_alphabet_rejects_il():
    r = client.post("/api/v1/geo/geohash", json={"geohash": "lo"})
    assert r.status_code == 400
    assert "no a i l o" in r.json()["errors"][0]["message"]


def test_country_fr_published_row():
    d = client.post("/api/v1/validate/country",
                    json={"code": "fr"}).json()
    assert d["alpha_3"] == "FRA" and d["numeric"] == "250"
    assert d["currency"] == "EUR" and d["currency_decimal_places"] == 2
    assert d["calling_code"] == "+33"


def test_country_jpy_zero_decimals():
    d = client.post("/api/v1/validate/country",
                    json={"code": "JP"}).json()
    assert d["currency_decimal_places"] == 0


def test_country_edge_is_honest_not_fake_invalid():
    d = client.post("/api/v1/validate/country",
                    json={"code": "TV"}).json()      # Tuvalu hors subset
    assert d["in_subset"] is False
    assert "NOT a claim of invalidity" in d["verdict"]


def test_country_bad_shape_400():
    r = client.post("/api/v1/validate/country", json={"code": "FRA"})
    assert r.status_code == 400


def test_postal_canonicals_hand_verified():
    assert client.post("/api/v1/validate/postal", json={
        "code": "01310100", "country": "BR"}).json()["canonical"] \
        == "01310-100"
    assert client.post("/api/v1/validate/postal", json={
        "code": "10001", "country": "US"}).json()["valid"] is True
    assert client.post("/api/v1/validate/postal", json={
        "code": "1234ab", "country": "NL"}).json()["canonical"] \
        == "1234 AB"
    bad = client.post("/api/v1/validate/postal", json={
        "code": "1234", "country": "FR"}).json()
    assert bad["valid"] is False and bad["expected"] == r"\d{5}"


def test_postal_unshipped_country_says_so():
    r = client.post("/api/v1/validate/postal",
                    json={"code": "1", "country": "TV"})
    assert r.status_code == 400
    assert "no postal grammar shipped" in r.json()["errors"][0]["message"]
