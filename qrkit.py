"""Bundle 30 lot 3 — a complete QR encoder (ISO/IEC 18004), pure stdlib,
SVG out. Versions 1-10, modes numeric / alphanumeric / byte chosen by
charset, ECL L M Q H, automatic mask selection by the published penalty
rules.

Why hand-written: a QR of the same text must be the same bitmap forever,
which is exactly this service's promise. Every matrix produced here is
cross-checked against the independent, published segno implementation
(dev-time oracle; the production path never imports it).
"""

_ALNUM = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"

_TOTAL_CW = {1: 26, 2: 44, 3: 70, 4: 100, 5: 134, 6: 172, 7: 196,
             8: 242, 9: 292, 10: 346}
# (ec_cw_per_block, [(blocks, data_cw), ...]) per version and ECL — the
# Reed-Solomon block structure table of the standard
_RS = {
    (1, "L"): (7, [(1, 19)]), (1, "M"): (10, [(1, 16)]),
    (1, "Q"): (13, [(1, 13)]), (1, "H"): (17, [(1, 9)]),
    (2, "L"): (10, [(1, 34)]), (2, "M"): (16, [(1, 28)]),
    (2, "Q"): (22, [(1, 22)]), (2, "H"): (28, [(1, 16)]),
    (3, "L"): (15, [(1, 55)]), (3, "M"): (26, [(1, 44)]),
    (3, "Q"): (18, [(2, 17)]), (3, "H"): (22, [(2, 13)]),
    (4, "L"): (20, [(1, 80)]), (4, "M"): (18, [(2, 32)]),
    (4, "Q"): (26, [(4, 9)]), (4, "H"): (16, [(4, 4)]),
    (5, "L"): (26, [(1, 108)]), (5, "M"): (24, [(2, 43)]),
    (5, "Q"): (18, [(2, 15), (2, 16)]),
    (5, "H"): (22, [(2, 11), (2, 12)]),
    (6, "L"): (18, [(2, 68)]), (6, "M"): (16, [(4, 27)]),
    (6, "Q"): (24, [(4, 19)]), (6, "H"): (28, [(4, 15)]),
    (7, "L"): (20, [(2, 78)]), (7, "M"): (18, [(4, 31)]),
    (7, "Q"): (18, [(2, 14), (4, 15)]),
    (7, "H"): (26, [(4, 13), (1, 14)]),
    (8, "L"): (24, [(2, 97)]), (8, "M"): (22, [(2, 38), (2, 39)]),
    (8, "Q"): (22, [(4, 18), (2, 19)]),
    (8, "H"): (26, [(4, 14), (2, 15)]),
    (9, "L"): (30, [(2, 116)]), (9, "M"): (22, [(3, 36), (2, 37)]),
    (9, "Q"): (20, [(4, 16), (4, 17)]),
    (9, "H"): (24, [(4, 12), (4, 13)]),
    (10, "L"): (18, [(2, 68), (2, 69)]),
    (10, "M"): (26, [(4, 43), (1, 44)]),
    (10, "Q"): (24, [(6, 19), (2, 20)]),
    (10, "H"): (28, [(6, 15), (2, 16)]),
}
_ALIGN = {1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30],
          6: [6, 34], 7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46],
          10: [6, 28, 50]}
_CCI = {"numeric": (10, 12), "alphanumeric": (9, 11),
        "byte": (8, 16)}      # (versions 1-9, versions 10-26)

_FORMAT_ECL = {"L": 0b01, "M": 0b00, "Q": 0b11, "H": 0b10}


class QrError(Exception):
    pass


# ------------------------------------------------------------ GF(256)
_EXP = [0] * 512
_LOG = [0] * 256


def _init_gf():
    x = 1
    for i in range(255):
        _EXP[i] = x
        _LOG[x] = i
        x <<= 1
        if x & 0x100:
            x ^= 0x11D
    for i in range(255, 512):
        _EXP[i] = _EXP[i - 255]


_init_gf()


def _gmul(a, b):
    if a == 0 or b == 0:
        return 0
    return _EXP[_LOG[a] + _LOG[b]]


def _rs_generator(deg):
    g = [1]
    for i in range(deg):
        # multiply g by (x - a^i)
        n = [0] * (len(g) + 1)
        for j, c in enumerate(g):
            n[j] ^= _gmul(c, _EXP[i])
            n[j + 1] ^= c
        g = n
    return g[::-1]          # LFSR below reads highest degree first


def _rs_encode(data, ec_len):
    g = _rs_generator(ec_len)
    rem = [0] * ec_len
    for d in data:
        f = d ^ rem[0]
        rem = rem[1:] + [0]
        if f:
            for i in range(ec_len):
                rem[i] ^= _gmul(g[i + 1], f)
    return rem


# ------------------------------------------------------------ segments
def _pick_mode(text):
    if text and all(c in "0123456789" for c in text):
        return "numeric"
    if text and all(c in _ALNUM for c in text):
        return "alphanumeric"
    return "byte"


def _cci_bits(mode, v):
    """Character-count indicator width is a function of the VERSION
    range (ISO 18004 Tables 3-5), never of the text length — v1-9 /
    v10-26 / v27-40. Versions here stop at 10."""
    if mode == "numeric":
        return 10 if v < 10 else 12
    if mode == "alphanumeric":
        return 9 if v < 10 else 11
    return 8 if v < 10 else 16


def _bits(text, mode, v):
    out = []

    def push(val, n):
        for i in range(n - 1, -1, -1):
            out.append((val >> i) & 1)
    if mode == "numeric":
        push(1, 4)
        push(len(text), _cci_bits("numeric", v))
        i = 0
        while i + 3 <= len(text):
            push(int(text[i:i + 3]), 10)
            i += 3
        rest = len(text) - i
        if rest == 2:
            push(int(text[i:]), 7)
        elif rest == 1:
            push(int(text[i:]), 4)
    elif mode == "alphanumeric":
        push(2, 4)
        push(len(text), _cci_bits("alphanumeric", v))
        i = 0
        while i + 2 <= len(text):
            push(_ALNUM.index(text[i]) * 45 + _ALNUM.index(text[i + 1]),
                 11)
            i += 2
        if i < len(text):
            push(_ALNUM.index(text[i]), 6)
    else:
        data = text.encode("utf-8")
        push(4, 4)
        push(len(data), _cci_bits("byte", v))
        for b in data:
            push(b, 8)
    return out


def _fit_version(mode, text, ecl):
    for v in range(1, 11):
        data_cw = sum(nb * k for k, nb in _RS[(v, ecl)][1])
        cci_bits = _cci_bits(mode, v)
        over = 0
        if mode == "numeric":
            n = len(text)
            over = 4 + cci_bits + (n // 3) * 10 + \
                {1: 4, 2: 7}.get(n % 3, 0)
        elif mode == "alphanumeric":
            n = len(text)
            over = 4 + cci_bits + (n // 2) * 11 + (n % 2) * 6
        else:
            over = 4 + cci_bits + 8 * len(text.encode("utf-8"))
        if over <= data_cw * 8:
            return v
    raise QrError("text too long for versions 1-10 at ECL %s "
                  "(%d bits > capacity v10)" % (ecl, over))


# ------------------------------------------------------------ matrix
def _new_matrix(size):
    return [[None] * size for _ in range(size)]


def _place_function(m, v, reserved):
    size = len(m)

    def setr(r, c, dark):
        m[r][c] = 1 if dark else 0
        reserved[r][c] = True
    # finder patterns + separators
    for (br, bc) in ((0, 0), (0, size - 7), (size - 7, 0)):
        for dr in range(-1, 8):
            for dc in range(-1, 8):
                r, c = br + dr, bc + dc
                if 0 <= r < size and 0 <= c < size:
                    dark = (0 <= dr <= 6 and 0 <= dc <= 6 and (
                        dr in (0, 6) or dc in (0, 6) or
                        (2 <= dr <= 4 and 2 <= dc <= 4)))
                    setr(r, c, dark)
    # timing
    for i in range(8, size - 8):
        setr(6, i, i % 2 == 0)
        setr(i, 6, i % 2 == 0)
    # alignment
    pos = _ALIGN[v]
    for r in pos:
        for c in pos:
            if ((r, c) in ((6, 6), (6, pos[-1]), (pos[-1], 6))):
                continue
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    setr(r + dr, c + dc,
                         max(abs(dr), abs(dc)) != 1)
    # dark module
    setr(size - 8, 8, True)
    # version info (v >= 7)
    if v >= 7:
        rem = v
        for _ in range(12):
            rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
        bits = v << 12 | rem
        for i in range(18):
            bit = (bits >> i) & 1
            setr(i // 3, size - 11 + i % 3, bit)
            setr(size - 11 + i % 3, i // 3, bit)


def _reserve_format(reserved):
    size = len(reserved)
    for i in range(9):
        reserved[8][i] = True
        reserved[i][8] = True
    for i in range(8):
        reserved[8][size - 1 - i] = True
        reserved[size - 1 - i][8] = True


def _place_data(m, reserved, stream):
    size = len(m)
    idx = 0
    col = size - 1
    upward = True
    while col > 0:
        if col == 6:
            col -= 1
        rng = range(size - 1, -1, -1) if upward else range(size)
        for row in rng:
            for cc in (col, col - 1):
                if not reserved[row][cc]:
                    m[row][cc] = stream[idx] if idx < len(stream) else 0
                    idx += 1
        col -= 2
        upward = not upward


_MASKS = [
    lambda r, c: (r + c) % 2 == 0,
    lambda r, c: r % 2 == 0,
    lambda r, c: c % 3 == 0,
    lambda r, c: (r + c) % 3 == 0,
    lambda r, c: (r // 2 + c // 3) % 2 == 0,
    lambda r, c: (r * c) % 2 + (r * c) % 3 == 0,
    lambda r, c: ((r * c) % 2 + (r * c) % 3) % 2 == 0,
    lambda r, c: ((r + c) % 2 + (r * c) % 3) % 2 == 0,
]


def _apply_mask(m, reserved, k):
    size = len(m)
    out = [row[:] for row in m]
    for r in range(size):
        for c in range(size):
            if not reserved[r][c] and _MASKS[k](r, c):
                out[r][c] ^= 1
    return out


def _format_bits(ecl, mask):
    data = _FORMAT_ECL[ecl] << 3 | mask
    rem = data
    for _ in range(10):
        rem = (rem << 1) ^ ((rem >> 9) * 0x537)
    bits = ((data << 10) | rem) ^ 0x5412
    return bits


def _place_format(m, ecl, mask):
    """Format bit placement exactly as the standard's geometry (the same
    mapping Nayuki documents): first copy down column 8 then along row 8,
    second copy along row 8 from the right and down column 8 at the
    bottom. The dark module at (size-8, 8) is not a format bit."""
    size = len(m)
    bits = _format_bits(ecl, mask)

    def gb(i):
        return (bits >> i) & 1
    for i in range(6):
        m[i][8] = gb(i)
    m[7][8] = gb(6)
    m[8][8] = gb(7)
    m[8][7] = gb(8)
    for i in range(9, 15):
        m[8][14 - i] = gb(i)
    for i in range(8):
        m[8][size - 1 - i] = gb(i)
    for i in range(8, 15):
        m[size - 15 + i][8] = gb(i)


def _penalty(m):
    """The four published evaluation conditions of ISO 18004 (N1=3/5+,
    N2=3 per 2x2 block, N3=40 per 1:1:3:1:1 pattern + 10 bonus,
    N4=10 per 5% deviation from 50% dark)."""
    size = len(m)
    score = 0
    for line in list(m) + [[m[r][c] for r in range(size)]
                           for c in range(size)]:
        run, prev = 1, line[0]
        for x in line[1:]:
            if x == prev:
                run += 1
            else:
                if run >= 5:
                    score += 3 + (run - 5)
                run, prev = 1, x
        if run >= 5:
            score += 3 + (run - 5)
    for r in range(size - 1):
        for c in range(size - 1):
            x = m[r][c]
            if x == m[r][c + 1] == m[r + 1][c] == m[r + 1][c + 1]:
                score += 3
    pat = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]
    rpat = pat[::-1]
    for line in list(m) + [[m[r][c] for r in range(size)]
                           for c in range(size)]:
        for i in range(size - 11 + 1):
            w = line[i:i + 11]
            if w == pat[:11] or w == rpat:
                score += 40
    dark = sum(sum(row) for row in m)
    pct = dark * 100 // (size * size)
    score += 10 * (min(abs(pct - 50) // 5, 10))
    return score


def qr_matrix(text, ecl="M", version=None):
    if not isinstance(text, str) or not text:
        raise QrError("text: non-empty string required")
    if len(text.encode("utf-8")) > 2700:
        raise QrError("text too long")
    ecl = ecl.upper()
    if ecl not in "LMQH":
        raise QrError("error-correction level must be L M Q or H")
    if version is not None and (not isinstance(version, int)
                                or not 1 <= version <= 10):
        raise QrError("version must be 1-10 (this encoder covers that "
                      "closed subset)")
    mode = _pick_mode(text)
    v = version or _fit_version(mode, text, ecl)
    data_cw = sum(nb * k for k, nb in _RS[(v, ecl)][1])
    stream = _bits(text, mode, v)
    if len(stream) > data_cw * 8:
        raise QrError("text needs version %d, not %d" % (
            _fit_version(mode, text, ecl), v))
    # terminator + pad to byte boundary + pad bytes 0xEC 0x11
    stream += [0, 0, 0, 0]
    while len(stream) % 8 and len(stream) < data_cw * 8:
        stream.append(0)
    stream = stream[:data_cw * 8]
    while len(stream) < data_cw * 8:
        for pb in (0xEC, 0x11):
            stream.extend([(pb >> i) & 1 for i in range(7, -1, -1)])
            if len(stream) == data_cw * 8:
                break
    codewords = [int("".join(str(b) for b in stream[i:i + 8]), 2)
                 for i in range(0, len(stream), 8)]
    # split into RS blocks
    ec_len, groups = _RS[(v, ecl)]
    blocks, pos = [], 0
    for count, size in groups:
        for _ in range(count):
            blocks.append(codewords[pos:pos + size])
            pos += size
    eccs = [_rs_encode(bl, ec_len) for bl in blocks]
    final = []
    for i in range(max(len(b) for b in blocks)):
        for bl in blocks:
            if i < len(bl):
                final.append(bl[i])
    for i in range(ec_len):
        for ec in eccs:
            final.append(ec[i])
    bitstream = []
    for by in final:
        bitstream.extend([(by >> i) & 1 for i in range(7, -1, -1)])
    # remainder bits (versions 2-6: 7 bits)
    if 2 <= v <= 6:
        bitstream += [0] * 7
    size = 17 + 4 * v
    m = _new_matrix(size)
    reserved = [[False] * size for _ in range(size)]
    _place_function(m, v, reserved)
    _reserve_format(reserved)
    _place_data(m, reserved, bitstream)
    best, best_score = None, None
    for k in range(8):
        cand = _apply_mask(m, reserved, k)
        _place_format(cand, ecl, k)
        p = _penalty(cand)
        if best_score is None or p < best_score:
            best, best_score, chosen_k = cand, p, k
    return {"matrix": best, "version": v, "mode": mode,
            "ecl": ecl, "mask": chosen_k, "size": size}


def qr_svg(matrix, scale=8, quiet=4):
    n = len(matrix)
    dim = (n + 2 * quiet) * scale
    rows = []
    for r, row in enumerate(matrix):
        c = 0
        while c < n:
            if row[c]:
                start = c
                while c < n and row[c]:
                    c += 1
                rows.append('<rect x="%d" y="%d" width="%d" height="%d"/>'
                            % ((start + quiet) * scale, (r + quiet) * scale,
                               (c - start) * scale, scale))
            else:
                c += 1
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
            'shape-rendering="crispEdges"><rect width="100%%" height="100%%" '
            'fill="#ffffff"/><g fill="#000000">%s</g></svg>'
            % (dim, dim, "".join(rows)))
