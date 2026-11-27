"""celestekit — bundle 145 (admissions 27-11, registre L65/L66/L67, payload
sha ed7e5fc9 / 423b030c / 813dcb95, campagne releveur celeste Wow!/SETI).
Trois outils, trois grammaires publiques CLOSES, chaque gold porte sa
REFERENCE publiee nommee.

astro_precess_equatorial — precession d'epoch EQUATORIALE au 1er ordre,
transcrite mot a mot du rapport d'anniversaire de J. D. Ehman
(https://www.bigear.org/Wow30th/wow30th.htm) : Delta_RA_an = m +
n_ra*sin(RA)*tan(Dec) (secondes de temps), Delta_Dec_an = n*cos(RA)
(secondes d'arc), m = 3.07234 + 0.00186*T, n = 20.0468 - 0.0085*T, T en
siecles tropiques depuis 1900 — constantes IAU 1976 (Lieske et al. 1977 /
Explanatory Supplement). Nutation et aberration EXPLICITEMENT negliees,
comme la source : l'outil dit son modele, il ne certifie pas le ciel.
Golds : les corrections PUBLIEES du rapport recalculees au meme chiffre
(19h22m25s -> 185.615 s / 352.621", 19h25m17s -> 185.463 s / 364.325",
J2000 arrondi a la seconde = 19h25m31s publie) ; les entrees de precision
du rapport de campagne (19h22m24.64s) rendent 185.616 s -> 19h25m30.256s.
Le pole refuse PAR LE NOM (tan(Dec) diverge), 24h refuse par le nom (la
page ferme l'intervalle avant 24h), au-dela de 2 siecles refuse par le
nom : 1er ordre = aune annoncee, pas fait cache.

units_freq_wavelength — lambda = c/f avec c = 299792458 m/s EXACT (SI,
17e CGPM 1983). Ce n'est PAS une conversion units_convert : les familles
de units_convert sont fermees et MHz y est refuse PAR LE NOM ; ici la
paire fermee est la sienne — Hz kHz MHz GHz THz (noms de l'article 1 du
Reglement des radiocommunications ITU) croise nm um µm mm cm m km,
dans les DEUX sens. Golds : la raie HI 1420.405751768 MHz ->
21.106114054160 cm reproduite AU DERNIER CHIFFRE publie (valeur
Wikipedia « Hydrogen line » 21.106114054160(30) cm) ; le round-trip
ramene la frequence repos au milli-Hertz publie.

bigear_snr_decode — l'echelle d'impression du Big Ear, table FERMEE
publiee (5 etapes, Ehman, page citee) : espace = 0-1, chiffres 1-9 = 1-9,
lettres A-Z = 10-35 (entier TRONQUE du SNR). 6EQUJ5 se decompose en
intervalles [n, n+1) ; la suite 6.5 14.5 26.5 30.5 19.5 5.5 +- 0.5 est
celle du rapport, pas une devinette. L'outil expose les DIVERGENCES de
pic publiees (30.5 Ehman / 30.1 Mendez arXiv 2508.10657 / « entre 30 et
31 » Wikipedia / 30 sigma Kraus) et l'ABSENCE de source du « bruit 10 »
(nulle part publie ; le bruit est normalise a 1 sigma par construction —
les seuls 10 publies : canal 10 kHz, integration 10 s). Le 72 s est dit
comme le rapport le dit : 6 rangees x 12 s, et la HPBW 37 s N'EST PAS la
duree. Refus nommes : '0' absent du code publie (zero = blanc),
minuscules hors alphabet, caracteres inconnus.

Arithmetique : entrees et constantes en Decimal exact, trigonometrie IEEE
binary64 aux frontieres transcendantes (comme geokit, lecon 137),
quantification HALF_UP declaree, getcontext LOCAL (lecon b136).
"""
import hashlib
import json
import math
from decimal import Decimal, ROUND_HALF_UP, localcontext

# ---------------------------------------------------------------- model
PRECESS_NAME = "iau1976-first-order-epoch-precession-145"
PRECESS_VERSION = ("145-v1 — termes seculaires du 1er ordre transcrits "
                   "mot a mot du rapport Big Ear 30e anniversaire "
                   "(Ehman, bigear.org/Wow30th) : m = 3.07234 + 0.00186*T "
                   "(s RA/an), n = 20.0468 - 0.0085*T (\"/an), T en "
                   "siecles tropiques depuis 1900, systeme IAU 1976 "
                   "(Lieske 1977) ; nutation et aberration negliees "
                   "COMME LA SOURCE")
PRECESS_REF = ("IAU 1976 precession constants (Lieske et al. 1977; "
               "Explanatory Supplement) under the first-order secular "
               "form, printed in J. D. Ehman, 'The Wow! Signal', Big Ear "
               "30th anniversary report, "
               "https://www.bigear.org/Wow30th/wow30th.htm")
FREQ_NAME = "freq-wavelength-si-exact-145"
FREQ_VERSION = ("145-v1 — lambda = c/f, c = 299792458 m/s EXACT (SI 17e "
                "CGPM 1983), familles fermees Hz kHz MHz GHz THz (noms "
                "ITU Reglement des radiocommunications art. 1) x "
                "nm um µm mm cm m km")
FREQ_REF = ("c exact by SI definition (17th CGPM 1983); frequency "
            "prefix names per ITU Radio Regulations, Art. 1; HI-line "
            "published wavelength 21.106114054160(30) cm, "
            "https://en.wikipedia.org/wiki/Hydrogen_line")
BIGEAR_NAME = "bigear-printout-scale-145"
BIGEAR_VERSION = ("145-v1 — echelle d'impression N50CH publiee en 5 "
                  "etapes (Ehman) : espace = 0-1, '1'-'9' = 1-9, "
                  "'A'-'Z' = 10-35, entier tronque du SNR")
BIGEAR_REF = ("J. D. Ehman, 'The Wow! Signal', Big Ear 30th anniversary "
              "report, the published 5-step intensity coding, "
              "https://www.bigear.org/Wow30th/wow30th.htm")


def _model(name, version, ref, extra=None):
    m = {"name": name, "version": version, "reference": ref}
    if extra:
        m.update(extra)
    m["sha256"] = hashlib.sha256(json.dumps(
        m, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return m


class CelesteKitError(Exception):
    def __init__(self, msg, field="payload"):
        super().__init__(msg)
        self.msg, self.field = msg, field


def _dec(v, field):
    """Decimal STRICT : chiffres seuls, jamais 'nan'/'inf'/texte."""
    if isinstance(v, bool):
        raise CelesteKitError("%s: number expected, got boolean" % field,
                              field)
    if isinstance(v, (int, Decimal)):
        d = Decimal(str(v)) if isinstance(v, int) else v
    elif isinstance(v, float):
        d = Decimal(repr(v))
    elif isinstance(v, str):
        s = v.strip()
        try:
            d = Decimal(s)
        except Exception:
            raise CelesteKitError("%s: decimal string expected, got %r"
                                  % (field, v), field)
    else:
        raise CelesteKitError("%s: number expected" % field, field)
    if not d.is_finite():
        raise CelesteKitError("%s: finite decimal expected, got %s"
                              % (field, d), field)
    return d


def _q(d, n):
    return str(d.quantize(Decimal(1).scaleb(-n), rounding=ROUND_HALF_UP))


def _pad_s(d_str):
    """'7.379' -> '07.379' — deux chiffres au champ secondes, publie."""
    ip, _, fp = d_str.partition(".")
    out = "%02d.%s" % (int(ip), fp) if fp else "%02d" % int(ip)
    return out


# ============================ astro_precess_equatorial ================

EPOCH_LO = Decimal("1500")
EPOCH_HI = Decimal("2500")
SPAN_LIMIT = Decimal("200")


def _parse_ra(v):
    """RA -> (heures_Decimal, secondes_Decimal exactes). Formes fermees."""
    if v is None:
        raise CelesteKitError("ra required", "ra")
    if isinstance(v, str):
        s = v.strip().lower().replace("h", ":").replace("m", ":") \
            .replace("s", ":")
        if s.endswith(":"):
            s = s[:-1]
        if ":" in s:
            fields = s.split(":")
            if not 1 <= len(fields) <= 3 or any(f == "" for f in fields):
                raise CelesteKitError("ra_format — expected H, H:M or "
                                      "H:M:S (19:22:25.64 or "
                                      "19h22m24.64s), got %r" % v, "ra")
            parts = []
            for i, f in enumerate(fields):
                x = _dec(f, "ra")
                if x < 0:
                    raise CelesteKitError("ra_sign — right ascension "
                                          "hours are never negative",
                                          "ra")
                if i > 0 and x >= 60:
                    raise CelesteKitError(
                        "sexagesimal_field_range — minutes and seconds "
                        "are 0..59.x, got %s" % f, "ra")
                parts.append(x)
            while len(parts) < 3:
                parts.append(Decimal(0))
            secs = parts[0] * 3600 + parts[1] * 60 + parts[2]
        else:
            h = _dec(s, "ra")
            if h < 0:
                raise CelesteKitError("ra_sign — right ascension hours "
                                      "are never negative", "ra")
            secs = h * 3600
    else:
        secs = _dec(v, "ra") * 3600
    if secs >= Decimal(24) * 3600:
        raise CelesteKitError(
            "ra_hours_range — 0h <= RA < 24h: the printed range is "
            "'00h00m00s up to but not including 24h00m00s' (Ehman Big "
            "Ear 30th report)", "ra")
    return secs / Decimal(3600), secs


def _parse_dec(v):
    """Dec -> secondes d'arc exactes (signees)."""
    if v is None:
        raise CelesteKitError("dec required", "dec")
    if isinstance(v, str):
        s = v.strip()
        sign = Decimal(1)
        if s.startswith("-"):
            sign, s = Decimal(-1), s[1:]
        elif s.startswith("+"):
            s = s[1:]
        if ":" in s:
            fields = s.split(":")
            if not 1 <= len(fields) <= 3 or any(f == "" for f in fields):
                raise CelesteKitError("dec_format — expected D or D:M "
                                      "or D:M:S (-27:03), got %r" % v,
                                      "dec")
            parts = []
            for i, f in enumerate(fields):
                if f[:1] in ("-", "+"):
                    raise CelesteKitError(
                        "dec_field_sign — the sign is taken ONCE on "
                        "the degrees; per-field signs (-27:+3) are "
                        "refused, never resolved by guessing", "dec")
                x = _dec(f, "dec")
                if i > 0 and x >= 60:
                    raise CelesteKitError("sexagesimal_field_range — "
                                          "minutes and seconds are "
                                          "0..59.x, got %s" % f, "dec")
                parts.append(x)
            while len(parts) < 3:
                parts.append(Decimal(0))
            mag = parts[0] * 3600 + parts[1] * 60 + parts[2]
        else:
            mag = _dec(s, "dec") * 3600
    else:
        dd = _dec(v, "dec")
        sign = Decimal(-1) if dd < 0 else Decimal(1)
        mag = abs(dd) * 3600
    if mag > Decimal(90) * 3600:
        raise CelesteKitError("dec_range — declination -90..+90", "dec")
    return sign * mag


def precess_equatorial(ra=None, dec=None, from_epoch=None, to_epoch=None,
                       digits=None):
    applied = []
    if digits is None:
        d = 3
        applied.append("digits")
    else:
        d = digits
    ra_hours, ra_secs = _parse_ra(ra)
    dec_secs = _parse_dec(dec)
    if from_epoch is None or to_epoch is None:
        raise CelesteKitError("from_epoch and to_epoch are required "
                              "(1950 / 2000 for B1950 -> J2000), never "
                              "assumed",
                              "to_epoch" if from_epoch is not None
                              else "from_epoch")
    e_from = _dec(from_epoch, "from_epoch")
    e_to = _dec(to_epoch, "to_epoch")
    for name, e in (("from_epoch", e_from), ("to_epoch", e_to)):
        if e < EPOCH_LO or e > EPOCH_HI:
            raise CelesteKitError("epoch_range — epochs 1500..2500 for "
                                  "this first-order secular model "
                                  "(%s = %s)" % (name, e), name)
    span = e_to - e_from
    if abs(span) > SPAN_LIMIT:
        raise CelesteKitError(
            "span_beyond_first_order — |to-from| <= 200 years: beyond "
            "that the 1st-order secular terms (nutation and aberration "
            "neglected, as the source report itself warns) are the "
            "wrong tool and the answer would be a fabricated number",
            "to_epoch")
    t_mid = ((e_from + e_to) / 2 - Decimal(1900)) / Decimal(100)
    m = Decimal("3.07234") + Decimal("0.00186") * t_mid
    n = Decimal("20.0468") - Decimal("0.0085") * t_mid
    n_ra = n / Decimal(15)
    if abs(dec_secs) == Decimal(90) * 3600:
        raise CelesteKitError(
            "dec_polar_singularity — the published formula carries "
            "tan(Dec), infinite at the poles: right ascension is "
            "undefined there and the tool refuses instead of guessing "
            "a coordinate", "dec")
    ra_deg_f = float(ra_hours) * 15.0
    dec_f = float(dec_secs) / 3600.0
    sinra = math.sin(math.radians(ra_deg_f))
    tan_d = math.tan(math.radians(dec_f))
    cosra = math.cos(math.radians(ra_deg_f))
    rate_ra = float(m) + float(n_ra) * sinra * tan_d
    rate_dec = float(n) * cosra
    dra_s = rate_ra * float(span)
    ddec_s = rate_dec * float(span)
    total_ra = (ra_secs + Decimal(repr(dra_s))).quantize(
        Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP) \
        % (Decimal(24) * 3600)
    rh = int(total_ra // 3600)
    rm = int((total_ra % 3600) // 60)
    rs = total_ra % 60
    total_dec = (dec_secs + Decimal(repr(ddec_s))).quantize(
        Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    if abs(total_dec) > Decimal(90) * 3600:
        raise CelesteKitError(
            "dec_polar_crossing — the corrected declination leaves "
            "-90..+90: the first-order secular form breaks down past "
            "the pole and the tool refuses to fold a coordinate it "
            "cannot state", "dec")
    dsign = "-" if total_dec < 0 else ""
    mag = abs(total_dec)
    dd = int(mag // 3600)
    dm = int((mag % 3600) // 60)
    ds = mag % 60
    out = {"tool": "astro_precess_equatorial",
           "inputs": {"ra_hours": _q(ra_hours, 9),
                      "dec_deg": _q(dec_secs / Decimal(3600), 9),
                      "from_epoch": str(e_from), "to_epoch": str(e_to)},
           "rates": {"T_mid_centuries": _q(t_mid, 6),
                     "m_s_per_year": _q(m, 6),
                     "n_arcsec_per_year": _q(n, 6),
                     "n_ra_s_per_year": _q(n_ra, 7)},
           "delta": {"ra_s_of_time_per_year": _q(Decimal(repr(rate_ra)),
                                                 6),
                     "dec_arcsec_per_year": _q(Decimal(repr(rate_dec)),
                                               6),
                     "ra_s_of_time": _q(Decimal(repr(dra_s)), d),
                     "dec_arcsec": _q(Decimal(repr(ddec_s)), d)},
           "span_years": _q(span, 4),
           "output_epoch": str(e_to),
           "output": {"ra_dms": "%02d:%02d:%s" % (rh, rm,
                                                  _pad_s(str(rs))),
                      "dec_dms": "%s%02d:%02d:%s" % (dsign, dd, dm,
                                                     _pad_s(str(ds))),
                      "ra_hours": _q(total_ra / Decimal(3600), 9),
                      "dec_deg": _q(total_dec / Decimal(3600), 9)}}
    if span == 0:
        out["note"] = ("same_epoch_identity — span 0: the output is the "
                       "input by arithmetic, an identity, not a fix")
    out["model"] = _model(
        PRECESS_NAME, PRECESS_VERSION, PRECESS_REF,
        {"formulas": {"delta_ra_per_year":
                      "m + (n/15)*sin(RA)*tan(Dec) [s RA]",
                      "delta_dec_per_year": "n*cos(RA) [arcsec]",
                      "m": "3.07234 + 0.00186*T",
                      "n": "20.0468 - 0.0085*T"},
         "neglected": "nutation, aberration, 2nd-order precession — "
                      "named by the source, not hidden here",
         "trig": "IEEE binary64 (~15 digits), Decimal inputs"})
    out["digits"] = {"mode": "HALF_UP", "value": d,
                     "continuous_fields_dp": 9}
    if applied:
        out["applied_defaults"] = applied
    return out


# ============================ units_freq_wavelength ===================

FREQ_UNITS = {"Hz": 0, "kHz": 3, "MHz": 6, "GHz": 9, "THz": 12}
LEN_UNITS = {"km": 3, "m": 0, "cm": -2, "mm": -3, "um": -6, "µm": -6,
             "nm": -9}
FREQ_ORDER = ("Hz", "kHz", "MHz", "GHz", "THz")
LEN_ORDER = ("km", "m", "cm", "mm", "um", "nm")
C_M_S = Decimal(299792458)
SPANNING = 30              # |adjusted exponent| cap on m and Hz sides


def freq_wavelength(value=None, unit=None, out=None, digits=None):
    applied = []
    if digits is None:
        d = 12
        applied.append("digits")
    else:
        d = digits
    if value is None:
        raise CelesteKitError("value required", "value")
    if unit is None:
        raise CelesteKitError(
            "unit required — one of Hz kHz MHz GHz THz | km m cm mm "
            "um µm nm (exact case); units_convert refuses MHz by name "
            "— that closed-family gap is why this tool exists", "unit")
    if not isinstance(unit, str):
        raise CelesteKitError("unit must be a name from the closed "
                              "table", "unit")
    if unit in FREQ_UNITS:
        family, exp = "frequency", FREQ_UNITS[unit]
    elif unit in LEN_UNITS:
        family, exp = "wavelength", LEN_UNITS[unit]
    else:
        raise CelesteKitError(
            "unit_unknown — %r is not in the closed pair: Hz kHz MHz "
            "GHz THz | km m cm mm um µm nm — case-sensitive (SI units "
            "are: 'Mhz' and 'MHZ' are not 'MHz') and this table is "
            "lambda = c/f, not units_convert" % unit, "unit")
    v = _dec(value, "value")
    if v <= 0:
        raise CelesteKitError(
            ("frequency_range — f must be > 0: zero frequency is DC "
             "and its wavelength is infinite, never a printed number"
             if family == "frequency" else
             "wavelength_range — lambda must be > 0 (no negative "
             "wavelength)"), "value")
    if out is None:
        out = "m" if family == "frequency" else "Hz"
        applied.append("out")
    if not isinstance(out, str):
        raise CelesteKitError("out must be a unit name", "out")
    want = "wavelength" if family == "frequency" else "frequency"
    table = LEN_UNITS if want == "wavelength" else FREQ_UNITS
    if out in FREQ_UNITS if family == "frequency" else out in LEN_UNITS:
        raise CelesteKitError(
            "out_unit_same_family — out %r is a %s unit, the input "
            "family; the answer crosses the pair lambda = c/f "
            "(same-family scaling is units_convert's job)"
            % (out, family), "out")
    if out not in table:
        raise CelesteKitError("out_unit_unknown — out must be one of "
                              "%s" % " ".join(LEN_ORDER
                                              if want == "wavelength"
                                              else FREQ_ORDER), "out")
    with localcontext() as ctx:
        ctx.prec = 60
        if family == "frequency":
            base_hz = v * Decimal(10) ** exp
            base_m = C_M_S / base_hz
        else:
            base_m = v * Decimal(10) ** exp
            base_hz = C_M_S / base_m
        for name, x in (("base", base_m), ("base", base_hz)):
            if abs(x.adjusted()) > SPANNING:
                raise CelesteKitError(
                    "value_out_of_range — beyond about 1e-30..1e30 in "
                    "the pair (m or Hz) the printed table loses digits "
                    "it cannot honour", "value")
        result = (base_m * Decimal(10) ** (-table[out])
                  if want == "wavelength"
                  else base_hz / Decimal(10) ** table[out])
        if result.quantize(Decimal(1).scaleb(-d),
                           rounding=ROUND_HALF_UP) == 0:
            raise CelesteKitError(
                "result_below_digits — the answer is smaller than the "
                "smallest number %d digits can print: raising digits "
                "(or switching out) is the repair, a silent zero is "
                "not an answer" % d, "digits")
        other = {}
        if want == "wavelength":
            for u in LEN_ORDER:
                other[u] = _q(base_m * Decimal(10) ** (-LEN_UNITS[u]), d)
        else:
            for u in FREQ_ORDER:
                other[u] = _q(base_hz / Decimal(10) ** FREQ_UNITS[u], d)
    out_dict = {"tool": "units_freq_wavelength",
                "input": {"value": str(v), "unit": unit,
                          "family": family},
                "constants": {"c_m_per_s": str(C_M_S),
                              "exactness": "c is exact by SI "
                                           "definition (17th CGPM "
                                           "1983) — the pair is "
                                           "arithmetic, not a measured "
                                           "ratio"},
                "result": {"unit": out, "family": want,
                           "value": _q(result, d)},
                "other_units": other,
                "pair": "lambda = c / f — both directions, closed "
                        "tables",
                "model": _model(
                    FREQ_NAME, FREQ_VERSION, FREQ_REF,
                    {"division": "Decimal, local precision 60, "
                                 "HALF_UP at the digits named"}),
                "digits": {"mode": "HALF_UP", "value": d}}
    if applied:
        out_dict["applied_defaults"] = applied
    return out_dict


# ============================ bigear_snr_decode =======================

BIGEAR_MAX_LEN = 200


def _code_interval(ch):
    if ch == " ":
        return "space", 0
    if "1" <= ch <= "9":
        return ch, int(ch)
    if "A" <= ch <= "Z":
        return ch, 10 + (ord(ch) - ord("A"))
    if ch == "0":
        raise CelesteKitError(
            "zero_code_absent — '0' is not a Big Ear code: the "
            "published coding prints an integer value of zero as a "
            "BLANK, digits start at 1 (Ehman, 30th report, step 5)",
            "string")
    if "a" <= ch <= "z":
        raise CelesteKitError(
            "lowercase_code — the published alphabet is UPPER CASE "
            "letters A through Z; a transcript with 'u' is refused, "
            "never folded by guessing", "string")
    raise CelesteKitError("unknown_code — %r is not in the published "
                          "scale (space, 1-9, A-Z)" % ch, "string")


def bigear_decode(string=None):
    if string is None:
        raise CelesteKitError("string required — the printed sequence, "
                              "e.g. 6EQUJ5", "string")
    if not isinstance(string, str):
        raise CelesteKitError("string must be the printout text",
                              "string")
    if string == "":
        raise CelesteKitError("empty_printout — nothing to decode: the "
                              "scale codes one character per 12-second "
                              "row", "string")
    if len(string) > BIGEAR_MAX_LEN:
        raise CelesteKitError("printout_too_long — %d characters, cap "
                              "%d (a printout row window)"
                              % (len(string), BIGEAR_MAX_LEN), "string")
    digits = []
    for i, ch in enumerate(string):
        code, lo = _code_interval(ch)
        digits.append({"index": i, "char": code,
                       "snr_truncated": lo,
                       "interval": {"lo": str(lo), "hi": str(lo + 1),
                                    "closed_form": "[%d,%d)"
                                                   % (lo, lo + 1)},
                       "best_estimate": _q(Decimal(lo) + Decimal("0.5"),
                                           1)})
    peak_lo = max(e["snr_truncated"] for e in digits)
    peak_chars = [{"index": e["index"], "char": e["char"]}
                  for e in digits if e["snr_truncated"] == peak_lo]
    rows = len(string)
    out = {"tool": "bigear_snr_decode",
           "input": {"string": string, "rows": rows},
           "scale": {"mapping": "space = [0,1) | '1'-'9' = 1..9 | "
                                "'A'-'Z' = 10..35 (integer truncation "
                                "of SNR)",
                     "code_formula": "letter code = ord(ch) - "
                                     "ord('A') + 10"},
           "digits": digits,
           "best_estimate_sequence": " ".join(
               e["best_estimate"] for e in digits),
           "peak": {"chars": peak_chars,
                    "interval": "[%d,%d)" % (peak_lo, peak_lo + 1),
                    "best_estimate": _q(Decimal(peak_lo) +
                                        Decimal("0.5"), 1),
                    "truncation_bar": "+/- 0.5 (the fraction is "
                                      "discarded by the printout — "
                                      "Ehman's own estimate rule)",
                    "system_noise_note": "the system noise itself adds "
                                         "1.0 at the 1-sigma level "
                                         "(2.0 at 95.44%) — the "
                                         "printed bars are truncation, "
                                         "not radiometry"},
           "cadence": {"seconds_per_row": "12",
                       "integration_s": "10",
                       "processing_s": "~2",
                       "duration_nominal_s": str(rows * 12),
                       "first_to_last_s": str((rows - 1) * 12),
                       "note": "the published 72 s for 6EQUJ5 = 6 rows "
                               "x 12 s (Ehman); the 37 s HPBW on the "
                               "same page is NOT the duration"},
           "published_variants": {
               "peak_snr": [
                   {"value": "30.5 +/- 0.5",
                    "who": "Ehman, Big Ear 30th report — '30.5 +/- 0.5 "
                           "times stronger than the background noise'",
                    "source": "https://www.bigear.org/Wow30th/"
                              "wow30th.htm"},
                   {"value": "30.1 +/- 0.4",
                    "who": "Mendez 2025 recalibration",
                    "source": "https://arxiv.org/abs/2508.10657"},
                   {"value": "between 30 and 31",
                    "who": "Wikipedia, Wow! signal",
                    "source": "https://en.wikipedia.org/wiki/"
                              "Wow%21_signal"},
                   {"value": "30 sigma",
                    "who": "Kraus",
                    "source": "https://technosearch.seti.org/wp-"
                              "content/uploads/2018/09/WOW%20official."
                              "pdf"}],
               "ambient_noise_10": "ABSENT — no published source for "
                                   "a 'background noise of 10': the "
                                   "metric is normalized to 1 sigma by "
                                   "construction (the baseline is "
                                   "subtracted); the nearest published "
                                   "'10's are the 10 kHz channel width "
                                   "and the 10 s integration",
               "rule": "every variant above is CITED with its own "
                       "source; the tool renders the interval the "
                       "printout itself encodes and never averages a "
                       "disagreement into one number"},
           "not_a_message": "the sequence is an intensity coding, not "
                            "an encoded message (published reading of "
                            "the same page)"}
    out["scale"].update(_model(BIGEAR_NAME, BIGEAR_VERSION, BIGEAR_REF))
    return out
