"""pngkit — PNG decode / resize / encode in pure stdlib, deterministic.

Contract, stated honestly:
  * Decodes non-interlaced PNG: grey/RGB/palette/grey+alpha/RGBA, bit
    depths 1/2/4/8/16 (low depths expand to 8-bit, palette to RGB(A);
    16-bit stays 16-bit). Interlaced Adam7 is refused by name — it is a
    different spec chapter, not a fallback.
  * Resampling is pure INTEGER arithmetic (Fraction areas, 1/65536
    fixed-point taps, round-half-up on exact integer means). No float
    ever touches a sample: same input bytes + same request = same
    output bytes on any platform, forever.
  * Geometry: fit (inside box, aspect kept), cover (fills box, aspect
    kept, may exceed the requested side), stretch (exactly W×H, aspect
    may change). Scale factors are Fractions — no float rounding.
  * box is the exact area average for downscale; on enlargement it
    degrades to bilinear and the algorithm field says so.
  * Encoding: filter-0 scanlines, zlib level 9 — stable per runtime;
    named in `algorithm`.
JPEG/WebP are out of contract on purpose: a lossy re-encode replays
bit-exactly only on the exact codec build that made it, and this machine
does not sign up for codec archaeology.
"""
import struct
import zlib
from fractions import Fraction

PNG_SIG = b"\x89PNG\r\n\x1a\n"
MAX_PIXELS = 5_000_000           # decoded input guard (bombs)
MAX_OUT_SIDE = 4096              # output guard
FP = 65536                       # 1/65536 fixed-point unit


class PngError(Exception):
    pass


# ── decode ────────────────────────────────────────────────────────────

def _chunks(data):
    if data[:8] != PNG_SIG:
        raise PngError("not a PNG (signature)")
    pos, out = 8, []
    while pos + 8 <= len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8])
        if pos + 12 + ln > len(data):
            raise PngError("truncated chunk %r" % typ)
        payload = data[pos + 8:pos + 8 + ln]
        crc = struct.unpack(">I", data[pos + 8 + ln:pos + 12 + ln])[0]
        if zlib.crc32(typ + payload) & 0xFFFFFFFF != crc:
            raise PngError("CRC mismatch in %r — file is corrupt" % typ)
        out.append((typ.decode("latin-1"), payload))
        pos += 12 + ln
    return out


def _unfilter(f, line, prev, bpp, rowlen):
    if f == 0:
        return
    if f == 1:
        for i in range(bpp, rowlen):
            line[i] = (line[i] + line[i - bpp]) & 0xFF
    elif f == 2:
        for i in range(rowlen):
            line[i] = (line[i] + prev[i]) & 0xFF
    elif f == 3:
        for i in range(rowlen):
            a = line[i - bpp] if i >= bpp else 0
            line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
    elif f == 4:
        for i in range(rowlen):
            a = line[i - bpp] if i >= bpp else 0
            c = prev[i - bpp] if i >= bpp else 0
            b = prev[i]
            p = a + b - c
            pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
            pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
            line[i] = (line[i] + pr) & 0xFF
    else:
        raise PngError("unknown scanline filter %d" % f)


def decode(data):
    chunks = _chunks(data)
    ihdr = next((p for t, p in chunks if t == "IHDR"), None)
    if ihdr is None:
        raise PngError("missing IHDR")
    w, h, depth, ctype, comp, filt, inter = struct.unpack(
        ">IIBBBBB", ihdr[:13])
    if comp or filt:
        raise PngError("unsupported compression/filter method")
    if inter:
        raise PngError("interlaced (Adam7) PNG refused — supply a "
                       "non-interlaced file")
    if w * h > MAX_PIXELS:
        raise PngError("image too large (%d×%d, cap %d Mpx)"
                       % (w, h, MAX_PIXELS // 1_000_000))
    chan = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ctype)
    if chan is None:
        raise PngError("colour type %d unsupported" % ctype)
    if depth not in (1, 2, 4, 8, 16):
        raise PngError("bit depth %d unsupported" % depth)
    idat = b"".join(p for t, p in chunks if t == "IDAT")
    raw_per_row = (w * chan * depth + 7) // 8
    # bomb guard is structural: IHDR pixel cap above + the exact size
    # equality below — a lying IDAT either misses the size or was
    # already capped by MAX_PIXELS (≤ ~20 MB raw).
    try:
        raw = zlib.decompress(idat)
    except zlib.error:
        raise PngError("IDAT inflate failed — corrupt stream")
    if len(raw) != h * (raw_per_row + 1):
        raise PngError("IDAT size %d, expected %d"
                       % (len(raw), h * (raw_per_row + 1)))
    bpp = max(1, chan * depth // 8)
    prev = bytearray(raw_per_row)
    byte_rows = []
    for y in range(h):
        base = y * (raw_per_row + 1)
        f = raw[base]
        line = bytearray(raw[base + 1:base + 1 + raw_per_row])
        _unfilter(f, line, prev, bpp, raw_per_row)
        byte_rows.append(line)
        prev = line
    if depth == 16:
        rows = [[(r[i] << 8 | r[i + 1]) for i in range(0, len(r), 2)]
                for r in byte_rows]
        out_depth = 16
    elif depth == 8:
        rows = [list(r) for r in byte_rows]
        out_depth = 8
    else:
        mask = (1 << depth) - 1
        # low-bit GREY scales to 0..255 ; palette samples are INDICES
        # (PIL happily writes 1-bit palettes) — scale 1 there.
        scale = 255 // mask if ctype in (0, 4) else 1
        per = 8 // depth
        rows = []
        for r in byte_rows:
            row = []
            for x in range(w * chan):
                sh = 8 - depth * (x % per + 1)
                row.append((r[x // per] >> sh & mask) * scale)
            rows.append(row)
        out_depth = 8
    if ctype == 3:
        pal = next((p for t, p in chunks if t == "PLTE"), b"")
        trns = next((p for t, p in chunks if t == "tRNS"), b"")
        if not pal:
            raise PngError("palette PNG without PLTE")
        nc = 4 if any(t == "tRNS" for t, _ in chunks) else 3
        new = []
        for row in rows:
            flat = []
            for idx in row:
                if idx * 3 + 2 >= len(pal):
                    raise PngError("palette index %d out of range" % idx)
                flat.extend(pal[idx * 3:idx * 3 + 3])
                if nc == 4:
                    flat.append(trns[idx] if idx < len(trns) else 255)
            new.append(flat)
        rows, chan = new, nc
    return {"w": w, "h": h, "depth": out_depth, "channels": chan,
            "rows": rows}


# ── encode ────────────────────────────────────────────────────────────

def encode(img):
    depth, chan = img["depth"], img["channels"]
    ctype = {1: 0, 2: 4, 3: 2, 4: 6}[chan]
    buf = bytearray()
    for row in img["rows"]:
        buf.append(0)
        if depth == 16:
            buf.extend(struct.pack(">%dH" % len(row), *row))
        else:
            buf.extend(bytes(row))
    out = bytearray(PNG_SIG)

    def chunk(typ, payload):
        out.extend(struct.pack(">I", len(payload)))
        out.extend(typ)
        out.extend(payload)
        out.extend(struct.pack(
            ">I", zlib.crc32(typ + payload) & 0xFFFFFFFF))

    chunk(b"IHDR", struct.pack(">IIBBBBB", img["w"], img["h"], depth,
                               ctype, 0, 0, 0))
    chunk(b"IDAT", zlib.compress(bytes(buf), 9))
    chunk(b"IEND", b"")
    return bytes(out)


# ── resize (integer only) ─────────────────────────────────────────────

def _bands(n_in, n_out):
    """Per output index: ([(src_idx, weight)], den) — exact area
    coverage; weight/den is the source-pixel fraction that lands in
    this output pixel. All integers."""
    bands = []
    for i in range(n_out):
        lo, hi = Fraction(i * n_in, n_out), Fraction((i + 1) * n_in, n_out)
        den = hi.denominator
        segs = []
        k = int(lo)
        while k < hi:
            ov = min(hi, k + 1) - max(lo, k)
            if ov > 0:
                segs.append((k, ov.numerator * (den // ov.denominator)))
            k += 1
        cov = sum(ov for _, ov in segs)
        bands.append((segs, cov))
    return bands


def box(img, width, height):
    chan = img["channels"]
    maxs = 65535 if img["depth"] == 16 else 255
    src = img["rows"]
    xb = _bands(img["w"], width)
    yb = _bands(img["h"], height)
    rows = []
    for yseg, yden in yb:
        acc = [0] * (width * chan)
        wsum = [0] * (width * chan)
        for (yk, wy) in yseg:
            srow = src[yk]
            for xi, (xseg, xden) in enumerate(xb):
                for (xk, wx) in xseg:
                    w = wy * wx
                    base = xi * chan
                    for c in range(chan):
                        acc[base + c] += srow[xk * chan + c] * w
        for xi, (xseg, xcov) in enumerate(xb):
            den = xcov * yden          # coverage in input-pixel units
            for c in range(chan):
                wsum[xi * chan + c] = den
        row = []
        for a, d in zip(acc, wsum):
            row.append(min((2 * a + d) // (2 * d) if d else 0, maxs))
        rows.append(row)
    return {"w": width, "h": height, "depth": img["depth"],
            "channels": chan, "rows": rows}


def _coords(n_in, n_out):
    """Source coordinate in 1/65536 under the pixel-centres convention:
    src = (i + 0.5) * n_in / n_out - 0.5 — integer and exact: a 1:1
    map is the identity, no blur at equal size."""
    return [max(0, ((2 * i + 1) * n_in - n_out) * FP // (2 * n_out))
            for i in range(n_out)]


def nearest(img, width, height):
    # nearest taps under the same centres convention, pure integers
    xs = [(2 * i + 1) * img["w"] // (2 * width) for i in range(width)]
    ys = [(2 * j + 1) * img["h"] // (2 * height) for j in range(height)]
    chan = img["channels"]
    src = img["rows"]
    rows = []
    for cy in ys:
        srow = src[min(cy, img["h"] - 1)]
        out = []
        for cx in xs:
            xk = min(cx, img["w"] - 1)
            out.extend(srow[xk * chan:xk * chan + chan])
        rows.append(out)
    return {"w": width, "h": height, "depth": img["depth"],
            "channels": chan, "rows": rows}


def bilinear(img, width, height):
    xs, ys = _coords(img["w"], width), _coords(img["h"], height)
    chan = img["channels"]
    maxs = 65535 if img["depth"] == 16 else 255
    src = img["rows"]
    rows = []
    for cy in ys:
        y0 = min(cy >> 16, img["h"] - 1)
        y1 = min(y0 + 1, img["h"] - 1)
        fy = cy - (y0 << 16)
        r0, r1 = src[y0], src[y1]
        out = []
        for cx in xs:
            x0 = min(cx >> 16, img["w"] - 1)
            x1 = min(x0 + 1, img["w"] - 1)
            fx = cx - (x0 << 16)
            for c in range(chan):
                top = (r0[x0 * chan + c] * (FP - fx)
                       + r0[x1 * chan + c] * fx)
                bot = (r1[x0 * chan + c] * (FP - fx)
                       + r1[x1 * chan + c] * fx)
                v = (top * (FP - fy) + bot * fy + (FP * FP >> 1)) >> 32
                out.append(min(v, maxs))
        rows.append(out)
    return {"w": width, "h": height, "depth": img["depth"],
            "channels": chan, "rows": rows}


RESAMPLE = {"box": box, "bilinear": bilinear, "nearest": nearest}


def _target(w0, h0, width, height, mode):
    fw = Fraction(width, w0) if width else None
    fh = Fraction(height, h0) if height else None
    if mode == "stretch":
        if not (width and height):
            raise PngError("stretch needs both width and height")
        return width, height
    if fw and fh:
        sf = min(fw, fh) if mode == "fit" else max(fw, fh)
    else:
        sf = fw or fh
    tw = (w0 * sf + Fraction(1, 2)).__floor__()
    th = (h0 * sf + Fraction(1, 2)).__floor__()
    return max(1, min(tw, MAX_OUT_SIDE)), max(1, min(th, MAX_OUT_SIDE))


def rightsize(img, width=None, height=None, mode="fit", resample="box"):
    if resample not in RESAMPLE:
        raise PngError("resample must be box|bilinear|nearest")
    if mode not in ("fit", "cover", "stretch"):
        raise PngError("mode must be fit|cover|stretch")
    if not width and not height:
        raise PngError("give width and/or height")
    w0, h0 = img["w"], img["h"]
    tw, th = _target(w0, h0, width, height, mode)
    algo_extra = ""
    fn = RESAMPLE[resample]
    if resample == "box" and (tw > w0 or th > h0):
        fn = bilinear
        algo_extra = " (box→bilinear on enlargement)"
    out = fn(img, tw, th)
    algo = "%s %dx%d→%dx%d, integer weights, half-up%s" % (
        resample if not algo_extra else "box-as-bilinear",
        w0, h0, tw, th, algo_extra)
    return out, algo
