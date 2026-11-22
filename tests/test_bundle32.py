"""Bundle 32 — image/rightsize (pngkit). Attentes = définitions vérifiées
à la main : decode==PIL, identité 1:1, box==moyenne d'aire exacte,
refus nommés (Adam7, CRC). PIL n'est utilisé qu'en ORACLE de test."""
import base64
import io
import sys
sys.path.insert(0, ".")
import pngkit
import main
from fastapi.testclient import TestClient
from PIL import Image

client = TestClient(main.app)


def pil_png(im):
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return b.getvalue()


def gradient(w=60, h=20, mode="L"):
    im = Image.new(mode, (w, h))
    px = im.load()
    for y in range(h):
        for x in range(w):
            v = (x * 4 + y * 7) % 256
            if mode == "L":
                px[x, y] = v
            elif mode == "RGB":
                px[x, y] = (v, 255 - v, x % 256)
            else:
                px[x, y] = (v, 255 - v, x % 256, 255)
    return im


def call(**kw):
    r = client.post("/api/v1/image/rightsize", json=kw)
    return r


def test_decode_matches_pil_across_types():
    for im in (gradient(60, 20, "L"), gradient(24, 18, "RGB"),
               gradient(24, 18, "RGBA")):
        data = pil_png(im)
        d = pngkit.decode(data)
        ref = list(im.getdata())
        flat = [v for row in d["rows"] for v in row]
        want = [v for t in ref for v in (t if isinstance(t, tuple)
                                         else (t,))]
        assert flat == want, im.mode
    p = Image.new("P", (12, 6))
    p.putpalette([9, 9, 9, 200, 0, 0])
    for y in range(6):
        for x in range(12):
            p.putpixel((x, y), (x + y) % 2)
    d = pngkit.decode(pil_png(p))
    assert d["rows"][0][:6] == [9, 9, 9, 200, 0, 0]


def test_identity_and_invariants():
    im = gradient(40, 40, "RGB")
    img = pngkit.decode(pil_png(im))
    out, algo = pngkit.rightsize(img, width=40, height=40, mode="fit",
                                 resample="bilinear")
    assert out["rows"] == img["rows"] and "identity" not in algo
    plate = {"w": 40, "h": 40, "depth": 8, "channels": 3,
             "rows": [[200, 30, 90] * 40 for _ in range(40)]}
    o, _ = pngkit.rightsize(plate, width=7, height=13, mode="stretch")
    assert all(tuple(r[x * 3:x * 3 + 3]) == (200, 30, 90)
               for r in o["rows"] for x in range(7))
    d = {"w": 4, "h": 4, "depth": 8, "channels": 1,
         "rows": [[0, 100, 0, 100], [100, 0, 100, 0],
                  [0, 100, 0, 100], [100, 0, 100, 0]]}
    o, _ = pngkit.rightsize(d, width=2, height=2, mode="stretch")
    assert o["rows"] == [[50, 50], [50, 50]]


def test_box_matches_its_own_definition():
    img = pngkit.decode(pil_png(gradient()))
    o, _ = pngkit.rightsize(img, width=17, height=5, mode="stretch")
    from fractions import Fraction
    xi, yi = 8, 3
    x0, x1 = Fraction(xi * 60, 17), Fraction((xi + 1) * 60, 17)
    y0, y1 = Fraction(yi * 20, 5), Fraction((yi + 1) * 20, 5)
    im = gradient()
    acc = den = 0
    for k in range(int(y0), y1.numerator // y1.denominator + 1):
        for l in range(int(x0), x1.numerator // x1.denominator + 1):
            w = (min(y1, k + 1) - max(y0, k)) * (min(x1, l + 1)
                                                 - max(x0, l))
            if w <= 0:
                continue
            acc += im.getpixel((l, k)) * w.numerator
            den += w.denominator * w.numerator // w.numerator * int(w * 10**6)
    # redéfinition propre : moyenne exacte sur poids Fraction
    acc = Fraction(0)
    area = Fraction(0)
    for k in range(int(y0), y1.numerator // y1.denominator + 1):
        for l in range(int(x0), x1.numerator // x1.denominator + 1):
            w = (min(y1, k + 1) - max(y0, k)) * (min(x1, l + 1)
                                                 - max(x0, l))
            acc += Fraction(im.getpixel((l, k))) * w
            area += w
    hand = (2 * acc.numerator * area.denominator
            + area.numerator * acc.denominator) // (
        2 * area.numerator * acc.denominator)
    assert o["rows"][yi][xi] == hand


def test_refus_nommés():
    data = pil_png(gradient(8, 8))
    bad = bytearray(data)
    bad[28] = 1
    import struct, zlib
    bad[29:33] = struct.pack(
        ">I", zlib.crc32(bytes(bad[12:29])) & 0xFFFFFFFF)
    try:
        pngkit.decode(bytes(bad))
        raise AssertionError("Adam7 accepté !")
    except pngkit.PngError as e:
        assert "interlaced" in str(e)
    c = bytearray(data)
    c[40] ^= 0xFF
    try:
        pngkit.decode(bytes(c))
        raise AssertionError("CRC corrompu accepté !")
    except pngkit.PngError as e:
        assert "CRC" in str(e)
    r = call(data_b64="!!!pas du base64!!!", width=4)
    assert r.status_code == 400 and "base64" in r.text
    r = call(data_b64=base64.b64encode(b"BM" + b"\x00" * 40).decode(),
             width=4)
    assert r.status_code == 400 and "PNG" in r.text
    r = call(data_b64=base64.b64encode(data).decode())
    assert r.status_code == 400 and "width" in r.text


def test_endpoint_roundtrip_and_stability():
    body = {"data_b64": base64.b64encode(pil_png(gradient())).decode(),
            "width": 30, "mode": "fit", "resample": "box"}
    r1 = call(**body)
    assert r1.status_code == 200
    d = r1.json()
    assert d["source"] == {"width": 60, "height": 20, "depth": 8,
                           "channels": 1}
    assert d["result"]["width"] == 30 and d["result"]["height"] == 10
    out_bytes = base64.b64decode(d["result"]["png_b64"])
    im = Image.open(io.BytesIO(out_bytes))
    assert im.size == (30, 10)
    r2 = call(**body)
    assert r2.json() == d          # mêmes entrées, mêmes octets
