"""Bundle 36 — text/url_canonical (urlkit). Vecteurs = exemples publiés
de la RFC 3986 (§5.2.4 / §6.2.2) recalculés à la main dans ce fichier,
jamais copiés de urlkit."""
import sys
sys.path.insert(0, ".")
import main
import urlkit
import pytest
from fastapi.testclient import TestClient

client = TestClient(main.app)


def test_rfc_published_equivalences():
    # §6.2.2 exemple publié : HTTP://EXAMPLE.COM:80/b vs /b
    assert urlkit.canonicalize(
        "HTTP://EXAMPLE.COM:80/b")["canonical"] == "http://example.com/b"
    # §5.2.4 exemples publiés de remove_dot_segments (base http://a/b/c/)
    assert urlkit.canonicalize(
        "http://a/b/c/./../../g")["canonical"] == "http://a/g"
    assert urlkit.canonicalize(
        "http://a/b/c/./../../g")["already_canonical"] is False
    # §6.2.2.2 : %7E → ~ (unreserved) ; %26 reste (structurel)
    r = urlkit.canonicalize("http://x.com/%7Ea?q=%261")
    assert r["canonical"] == "http://x.com/~a?q=%261"
    # host en majuscules + IPv6 intact (cas de host seulement)
    r6 = urlkit.canonicalize("http://[2001:DB8::1]/P")
    assert r6["canonical"] == "http://[2001:db8::1]/P"
    # le CHEMIN garde sa casse (pas de règle dans la RFC pour ça)
    assert urlkit.canonicalize(
        "http://x.com/Page")["canonical"] == "http://x.com/Page"


def test_www_stays_baby():
    # "www." N'EST PAS un préfixe canonique (confusion fréquente des
    # convertisseurs — ici c'est écrit, donc testé)
    r = urlkit.canonicalize("http://www.example.com/")
    assert r["canonical"] == "http://www.example.com/"


def test_idn_punycode_published_vector():
    # vector publié RFC 3490 : bücher.example → xn--bcher-kva.example
    r = urlkit.canonicalize("http://bücher.example/x")
    assert r["canonical"] == "http://xn--bcher-kva.example/x"
    assert "punycode" in " ".join(r["actions"])


def test_tracking_named_removals_and_opt_outs():
    u = ("https://shop.example/p?utm_source=nl&gclid=X&keep=1"
         "&fbclid=Y")
    r = urlkit.canonicalize(u)
    assert r["canonical"] == "https://shop.example/p?keep=1"
    removed = [a for a in r["actions"] if "tracking param" in a]
    assert len(removed) == 3   # utm_source, gclid, fbclid — tous nommés
    off = urlkit.canonicalize(u, strip_tracking=False)
    assert "gclid=X" in off["canonical"]
    # ordre préservé par défaut = la donnée de l'appelant
    o = urlkit.canonicalize("http://x/?b=2&a=1")
    assert "b=2&a=1" in o["canonical"]
    s = urlkit.canonicalize("http://x/?b=2&a=1", sort_params=True)
    assert s["canonical"] == "http://x/?a=1&b=2"


def test_refus_nommés():
    with pytest.raises(urlkit.UrlError) as e:
        urlkit.canonicalize("/just/a/path")     # pas de scheme
    assert "scheme required" in str(e.value)
    with pytest.raises(urlkit.UrlError):
        urlkit.canonicalize("")


def test_endpoint_and_pin_stability():
    body = {"url": "HTTP://www.Example.COM:80/a/../b/%7Euser"
                   "?utm_source=n&id=42#%61"}
    r1 = client.post("/api/v1/text/url_canonical", json=body).json()
    assert r1["canonical"] == \
        "http://www.example.com/b/~user?id=42#a"
    r2 = client.post("/api/v1/text/url_canonical", json=body).json()
    assert r1 == r2 and r1["sha256"]
