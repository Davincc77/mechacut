"""doc/text — fixtures PDF construits à la main (octets totalement
contrôlés) + un PDF matplotlib en preuve producteur-réel (Type0 +
ToUnicode). Paywall : libre < 32 KB, 402 au-delà quand payé-configuré."""
import base64
import json
import sys
sys.path.insert(0, ".")
import pytest
import main
import payments
from fastapi.testclient import TestClient

client = TestClient(main.app)

PAY_TO = "0x0000000000000000000000000000000000000001"


def build_pdf(lines, extra_pad=b""):
    body = ("BT /F1 12 Tf "
            + " T* ".join("(%s) Tj" % l for l in lines) + " ET")
    content = body.encode("latin-1") + b"\n" + extra_pad
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /Resources << /Font "
            b"<< /F1 4 0 R >> >> /Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Length %d >>\nstream\n" % len(content) + content
            + b"\nendstream"]
    out = [b"%PDF-1.4\n"]
    for i, o in enumerate(objs, 1):
        out.append(b"%d 0 obj\n" % i + o + b"\nendobj\n")
    out.append(b"trailer << /Root 1 0 R >>\n%%EOF\n")
    return b"".join(out)


def b64(x):
    return base64.b64encode(x).decode()


def dt(**kw):
    r = client.post("/api/v1/doc/text", json=kw)
    assert r.status_code == 200, r.text
    return r.json()


def test_extract_handcrafted_invoice():
    d = dt(pdf_b64=b64(build_pdf(["Facture n\xb042",
                                  "Montant: 15 650,75 EUR"])))
    assert d["page_count"] == 1 and d["verdict"] == "ok"
    t = d["pages"][0]["text"]
    assert "Facture" in t and "15 650,75" in t and "\xb0" in t


def test_page_selector():
    d = dt(pdf_b64=b64(build_pdf(["ligne une", "ligne deux"])), page=1)
    assert d["page"] == 1 and "ligne une" in d["text"]
    r = client.post("/api/v1/doc/text",
                    json={"pdf_b64": b64(build_pdf(["x"])), "page": 3})
    assert r.status_code == 400 and "1-1" in r.text


def test_refusals_are_verdicts():
    for bad, needle in [(b"hello world", "%PDF header"),
                        (build_pdf(["a"]).replace(b"trailer",
                                                  b"/Encrypt 9 0 R trailer"
                                                  b" trailer"),
                         "encrypted")]:
        r = client.post("/api/v1/doc/text", json={"pdf_b64": b64(bad)})
        assert r.status_code == 400 and needle in r.text


def test_matplotlib_real_producer():
    pytest.importorskip("matplotlib")
    import io
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.figure import Figure
    f = Figure()
    f.add_subplot().text(0.1, 0.5, "Mechacut total 15650.75")
    buf = io.BytesIO()
    f.savefig(buf, format="pdf")
    d = dt(pdf_b64=b64(buf.getvalue()))
    assert "15650.75" in d["pages"][0]["text"]
    assert "Mechacut" in d["pages"][0]["text"]


def test_paywall_cap_over_32kb(paywall_doc):
    small = b64(build_pdf(["petite"]))
    assert client.post("/api/v1/doc/text",
                       json={"pdf_b64": small}).status_code == 200
    big = b64(build_pdf(["grande"], extra_pad=b"% pad\n" * 6000))
    r = client.post("/api/v1/doc/text", json={"pdf_b64": big})
    assert r.status_code == 402
    acc = r.json()["accepts"][0]
    assert acc["maxAmountRequired"] == "1000"


@pytest.fixture
def paywall_doc(monkeypatch):
    monkeypatch.setenv("MECHACUT_PAY_TO", PAY_TO)
    monkeypatch.setenv("MECHACUT_NETWORK", "base-sepolia")
    payments._seen.clear()
    yield
    payments._seen.clear()
