"""geokit — bundle 137 (admissions 27-11, registre L56/L60/L61, recus
6b592587 / 4de2e8f2 / 3e025c90). Pack geodesie / trigonometrie.

geodesic_wgs84_inverse — Vincenty (1975) inverse, la formule publiee
nommee : Bulletin Geodesique 115:87-93. Ellipsoide WGS84, constantes
 Declarees dans chaque reponse : a = 6378137 m, f = 1/298.257223563
(b = a(1-f)). Le rapport de campagne a trace ces golds a la main et
les a recoupes contre Karney (geographiclib 2.1) a 0,1 mm pres — ici
la serie canonique A = 1 + u2/16384*(4096+...) et B = u2/1024*(256+...)
est jouee mot a mot. Le voisin sphere est NOMME : geo_distance (R =
6371008.8 m) est faux de -23,072 km sur SCL-MEL (mesure registre) —
ses reponses rendent desormais leur rayon, mais le rayon ne remplace
pas l'ellipse.

horizon_hidden_height — modele SPHERIQUE a rayon ARGUMENT (defaut
6371000 m = le R des pages auditees, dit dans applied_defaults),
refraction k ARGUMENT (defaut 0, dit), R_eff = R/(1-k). Les DEUX
definitions de chaque distance sont rendues, jamais l'une devinee a
la place de l'autre — c'est peche 2 artefacts de definition dans la
campagne (517 vs 518 km a 21 000 m ; 368 vs 369 km a 35 000 ft).
tangente sqrt(2Rh+h^2) ; arc R acos(R/(R+h)) ; drop exact
R_eff(1-cos(s/R_eff)), secante R_eff/cos-1, parabole s^2/2R_eff ;
hauteur cachee R_eff/cos((D-d_arc)/R_eff)-R_eff ; evanouissement =
somme des arcs. La regle « 8 in/mi^2 » est un claim ARITHMETIQUE du
test (267 ft a 20 mi), pas une sortie de l'outil — elle n'est PAS une
hauteur cachee, et le test le joue.

shadow_length_sun_elevation — h/tan(e), degres en entree, e <= 0
refuse PAR LE NOM (le soleil ne projette rien), e > 90 refuse,
arrondi HALF_UP a digits NOMME (defaut 2, dit). Golds de la campagne spatiale : 35,01 /
25,38 / 35,05 / 2,00 a 45 degres / 0,00 au zenith / refus a 0.

Trigonometrie : IEEE binary64 (~15 chiffres) aux frontieres
transcendantes, comme l'oracle de campagne ; entrees et constantes en
Decimal exact, quantification HALF_UP declaree. getcontext local,
jamais global (lecon b136).
"""
import hashlib
import json
import math
from decimal import Decimal, ROUND_HALF_UP, localcontext

MODEL_NAME = "geodesy-horizon-shadow-137"
MODEL_VERSION = ("137-v1 — Vincenty (1975) inverse sur WGS84 "
                 "(a=6378137, f=1/298.257223563) + modele horizon "
                 "sphere R argument, refraction R_eff=R/(1-k), "
                 "transcrit 2026-11-27 depuis les golds de campagne")

# constantes publiees WGS84, declarees dans chaque reponse
A_M = Decimal("6378137")
F_INV = Decimal("298.257223563")
F = Decimal(1) / F_INV
B_M = A_M * (Decimal(1) - F)

R_DEFAULT = Decimal("6371000")   # le R des pages auditees (dit, jamais vole)

_MODEL_DICT = {"name": MODEL_NAME, "version": MODEL_VERSION,
               "constants": {"WGS84_a_m": str(A_M), "WGS84_f": "1/298.257223563"},
               "formulas": {
                   "horizon_tangent": "sqrt(2*R_eff*h + h^2)",
                   "horizon_arc": "R_eff*acos(R_eff/(R_eff+h))",
                   "drop_exact": "R_eff*(1-cos(s/R_eff))",
                   "drop_secant": "R_eff/cos(s/R_eff)-R_eff",
                   "drop_parabolic": "s^2/(2*R_eff)",
                   "hidden_height": "R_eff/cos((D-d_arc)/R_eff)-R_eff",
                   "vanish_distance": "arc(h_obs)+arc(h_target)",
                   "shadow": "height / tan(elevation)"},
               "trig": "IEEE binary64 (~15 digits), Decimal inputs"}
MODEL_SHA256 = hashlib.sha256(json.dumps(
    _MODEL_DICT, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class GeoKitError(Exception):
    def __init__(self, msg, field="payload"):
        super().__init__(msg)
        self.msg, self.field = msg, field


def _dec(v, field):
    """Decimal STRICT : chiffres seuls, jamais 'nan'/'inf'/texte."""
    if isinstance(v, bool):
        raise GeoKitError("%s: number expected, got boolean" % field, field)
    if isinstance(v, (int, Decimal)):
        d = Decimal(str(v)) if isinstance(v, int) else v
    elif isinstance(v, float):
        d = Decimal(repr(v))
    elif isinstance(v, str):
        s = v.strip()
        try:
            d = Decimal(s)
        except Exception:
            raise GeoKitError("%s: decimal string expected, got %r"
                              % (field, v), field)
    else:
        raise GeoKitError("%s: number expected" % field, field)
    if not d.is_finite():
        raise GeoKitError("%s: finite decimal expected, got %s"
                          % (field, d), field)
    return d


def _q(d, n):
    return str(d.quantize(Decimal(1).scaleb(-n), rounding=ROUND_HALF_UP))


def _model_block(extra=None):
    m = {"name": MODEL_NAME, "version": MODEL_VERSION,
         "sha256": MODEL_SHA256, "trig": "IEEE binary64 (~15 digits)"}
    if extra:
        m.update(extra)
    return m


# ================= geodesic_wgs84_inverse (Vincenty 1975 inverse) ======

def _pt(v, what):
    if not isinstance(v, dict) or not v:
        raise GeoKitError("%s must be {lat, lon}" % what, what)
    extra = sorted(k for k in v if k not in ("lat", "lon"))
    if extra:
        raise GeoKitError("%s: unknown key(s) %s (only lat, lon)"
                          % (what, ",".join(extra)), what)
    if "lat" not in v or "lon" not in v:
        raise GeoKitError("%s: lat and lon required" % what, what)
    return _dec(v["lat"], "%s.lat" % what), _dec(v["lon"], "%s.lon" % what)


def vincenty_inverse(frm=None, to=None, digits=None):
    d = 4 if digits is None else digits
    la1, lo1 = _pt(frm, "from")
    la2, lo2 = _pt(to, "to")
    if la1.copy_abs() > Decimal(90):
        raise GeoKitError("from: latitude_range -90..90", "from")
    if la2.copy_abs() > Decimal(90):
        raise GeoKitError("to: latitude_range -90..90", "to")
    if lo1.copy_abs() > Decimal(180) or lo2.copy_abs() > Decimal(180):
        raise GeoKitError("longitude_range -180..180",
                          "from" if lo1.copy_abs() > 180 else "to")
    out = {"tool": "geodesic_wgs84_inverse",
           "ellipsoid": {"name": "WGS84", "a_m": str(A_M),
                         "f": "1/298.257223563",
                         "b_m": _q(B_M, 4)},
           "method": {"name": "Vincenty inverse",
                      "reference": ("Vincenty, T. (1975). Direct and "
                                    "inverse geodesics on an ellipsoid. "
                                    "Bulletin Geodesique 115:87-93 — "
                                    "serie A/16384, B/1024 canoniques"),
                      "version": MODEL_VERSION,
                      "sha256": MODEL_SHA256},
           "inputs": {"from": {"lat": str(la1), "lon": str(lo1)},
                      "to": {"lat": str(la2), "lon": str(lo2)}},
           "digits": {"mode": "HALF_UP", "value": d, "unit": "meters"}}
    if la1 == la2 and lo1 == lo2:
        out["distance_m"] = _q(Decimal(0), d)
        out["distance_km"] = str(Decimal(out["distance_m"]).scaleb(-3))
        out["azimuth_initial_deg"] = None
        out["azimuth_final_deg"] = None
        out["iterations"] = 0
        out["note"] = "same_point — distance 0, azimuth undefined, never guessed"
        out["model"] = _model_block()
        return out
    a, f = float(A_M), float(F)
    b = a * (1 - f)
    p1, p2 = float(la1) * math.pi / 180, float(la2) * math.pi / 180
    l1, l2 = float(lo1) * math.pi / 180, float(lo2) * math.pi / 180
    U1 = math.atan((1 - f) * math.tan(p1))
    U2 = math.atan((1 - f) * math.tan(p2))
    L = l2 - l1
    if L > math.pi:
        L -= 2 * math.pi
    elif L < -math.pi:
        L += 2 * math.pi
    lam = L
    su1, cu1 = math.sin(U1), math.cos(U1)
    su2, cu2 = math.sin(U2), math.cos(U2)
    converged = False
    iters = 0
    c2a = 0.0
    for iters in range(1, 201):
        sl, cl = math.sin(lam), math.cos(lam)
        ss = math.hypot(cu2 * sl, cu1 * su2 - su1 * cu2 * cl)
        if ss == 0.0:
            break
        cs = su1 * su2 + cu1 * cu2 * cl
        sig = math.atan2(ss, cs)
        sa = cu1 * cu2 * sl / ss
        c2a = 1 - sa * sa
        c2sm = (cs - 2 * su1 * su2 / c2a) if c2a else 0.0
        C = f / 16 * c2a * (4 + f * (4 - 3 * c2a))
        dom = lam
        lam = (L + (1 - C) * f * sa * (sig + C * ss *
               (c2sm + C * cs * (-1 + 2 * c2sm * c2sm))))
        if abs(lam - dom) < 1e-13:
            converged = True
            break
    if not converged:
        raise GeoKitError(
            "vincenty_non_convergence — near-antipodal pair: Vincenty "
            "(1975) does not converge (published limit); Karney 2013 "
            "or a small perturbation is the repair", "to")
    sl, cl = math.sin(lam), math.cos(lam)
    ss = math.hypot(cu2 * sl, cu1 * su2 - su1 * cu2 * cl)
    cs = su1 * su2 + cu1 * cu2 * cl
    sig = math.atan2(ss, cs)
    if c2a <= 1e-24:                      # ligne equatorielle : A=1,
        s_m = b * sig                      # s = b*sigma sur la sphere aux.
        out["azimuth_initial_deg"] = _q(Decimal(repr(90.0 if L >= 0
                                                     else 270.0)), d)
        out["azimuth_final_deg"] = out["azimuth_initial_deg"]
    else:
        sa2 = 1 - c2a
        c2sm = cs - 2 * su1 * su2 / c2a
        u2 = c2a * (a * a - b * b) / (b * b)
        Aa = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
        Bb = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))
        ds = Bb * ss * (c2sm + Bb / 4 * (cs * (-1 + 2 * c2sm * c2sm) -
             Bb / 6 * c2sm * (-3 + 4 * ss * ss) * (-3 + 4 * c2sm * c2sm)))
        s_m = b * Aa * (sig - ds)
        az1 = math.atan2(cu2 * sl,
                         cu1 * su2 - su1 * cu2 * cl) % (2 * math.pi)
        az2 = math.atan2(cu1 * sl,
                         -su1 * cu2 + cu1 * su2 * cl) % (2 * math.pi)
        out["azimuth_initial_deg"] = _q(Decimal(repr(az1 * 180 / math.pi)), d)
        out["azimuth_final_deg"] = _q(Decimal(repr(az2 * 180 / math.pi)), d)
    dm = _q(Decimal(repr(s_m)), d)
    out["distance_m"] = dm
    out["distance_km"] = str(Decimal(dm).scaleb(-3))
    out["iterations"] = iters
    out["model"] = _model_block({"sphere_neighbor":
                                 "geo_distance (R=6371008.8 m, sphere)"})
    return out


# ===================== horizon_hidden_height ============================

MODES = ("horizon", "drop", "hidden_height", "vanish_distance")


def _eff(R, k):
    if k < 0 or k >= 1:
        raise GeoKitError("refraction_k_range — 0 <= k < 1 (k=1 means "
                          "infinite R_eff)", "k")
    return R / (Decimal(1) - k)


def _tangent_m(h, Re):
    return math.sqrt(2 * float(Re) * float(h) + float(h) ** 2)


def _arc_m(h, Re):
    return float(Re) * math.acos(float(Re) / (float(Re) + float(h)))


def horizon_height(mode=None, observer_height_m=None, distance_m=None,
                   target_height_m=None, R_m=None, k=None, digits=None):
    applied = []
    d = 3 if digits is None else digits
    if digits is None:
        applied.append("digits")
    R = R_DEFAULT if R_m is None else _dec(R_m, "R_m")
    if R_m is None:
        applied.append("R_m")
    if R <= 0:
        raise GeoKitError("R_m must be > 0", "R_m")
    kv = Decimal(0) if k is None else _dec(k, "k")
    if k is None:
        applied.append("k")
    if mode not in MODES:
        raise GeoKitError("mode must be one of %s" % " | ".join(MODES),
                          "mode")
    Re = _eff(R, kv)
    out = {"tool": "horizon_hidden_height", "mode": mode,
           "model": _model_block({"R_m": str(R_m) if R_m is not None
                                  else str(R_DEFAULT),
                                  "k": str(kv),
                                  "R_eff_m": _q(Re, 6),
                                  "refraction": "R_eff = R / (1 - k)"}),
           "digits": {"mode": "HALF_UP", "value": d, "unit": "meters"}}
    if applied:
        out["applied_defaults"] = applied

    def _req_h():
        if observer_height_m is None:
            raise GeoKitError("observer_height_m required for this mode",
                              "observer_height_m")
        h = _dec(observer_height_m, "observer_height_m")
        if h <= 0:
            raise GeoKitError("observer_height_range — height must be > 0",
                              "observer_height_m")
        return h

    if mode == "horizon":
        h = _req_h()
        out["inputs"] = {"observer_height_m": str(h)}
        out["horizon"] = {"tangent_m": _q(Decimal(repr(_tangent_m(h, Re))), d),
                          "arc_m": _q(Decimal(repr(_arc_m(h, Re))), d)}
    elif mode == "drop":
        if distance_m is None:
            raise GeoKitError("distance_m required for this mode",
                              "distance_m")
        s = _dec(distance_m, "distance_m")
        if s <= 0:
            raise GeoKitError("distance_range — must be > 0", "distance_m")
        x = float(s) / float(Re)
        out["inputs"] = {"distance_m": str(s)}
        out["drop"] = {
            "exact_m": _q(Decimal(repr(float(Re) * (1 - math.cos(x)))), d),
            "secant_m": _q(Decimal(repr(float(Re) / math.cos(x)
                                        - float(Re))), d),
            "parabolic_m": _q(s * s / (Re * 2), d)}
    elif mode == "hidden_height":
        h = _req_h()
        if distance_m is None:
            raise GeoKitError("distance_m required for this mode",
                              "distance_m")
        D = _dec(distance_m, "distance_m")
        if D <= 0:
            raise GeoKitError("distance_range — must be > 0", "distance_m")
        da = _arc_m(h, Re)
        if float(D) <= da:
            raise GeoKitError(
                "distance_within_horizon — D <= observer arc horizon "
                "(%s m): nothing is hidden there" % _q(Decimal(repr(da)), d),
                "distance_m")
        ang = (float(D) - da) / float(Re)
        hid = float(Re) / math.cos(ang) - float(Re)
        out["inputs"] = {"observer_height_m": str(h), "distance_m": str(D)}
        out["horizon"] = {"tangent_m":
                          _q(Decimal(repr(_tangent_m(h, Re))), d),
                          "arc_m": _q(Decimal(repr(da)), d)}
        out["hidden_height_m"] = _q(Decimal(repr(hid)), d)
    else:  # vanish_distance
        h = _req_h()
        if target_height_m is None:
            raise GeoKitError("target_height_m required for this mode",
                              "target_height_m")
        ht = _dec(target_height_m, "target_height_m")
        if ht <= 0:
            raise GeoKitError("target_height_range — must be > 0",
                              "target_height_m")
        out["inputs"] = {"observer_height_m": str(h),
                         "target_height_m": str(ht)}
        out["vanish"] = {
            "arc_m": _q(Decimal(repr(_arc_m(h, Re) + _arc_m(ht, Re))), d),
            "tangent_m": _q(Decimal(repr(_tangent_m(h, Re)
                                         + _tangent_m(ht, Re))), d)}
    return out


# =================== shadow_length_sun_elevation ========================

def shadow_length(height_m=None, elevation_deg=None, digits=None):
    applied = []
    d = 2 if digits is None else digits
    if digits is None:
        applied.append("digits")
    h = _dec(height_m, "height_m") if height_m is not None else None
    if h is None:
        raise GeoKitError("height_m required", "height_m")
    if h <= 0:
        raise GeoKitError("height_range — height_m must be > 0", "height_m")
    e = _dec(elevation_deg, "elevation_deg")
    if e <= 0:
        raise GeoKitError("sun_at_or_below_horizon — elevation_deg must "
                          "be > 0 (no shadow is projected at or below 0)",
                          "elevation_deg")
    if e > 90:
        raise GeoKitError("elevation_beyond_zenith — elevation_deg "
                          "0 < e <= 90", "elevation_deg")
    x = float(e) * math.pi / 180
    val = float(h) / math.tan(x)
    out = {"tool": "shadow_length_sun_elevation",
           "inputs": {"height_m": str(h), "elevation_deg": str(e)},
           "model": _model_block({"formula": "shadow = height / tan(elevation)",
                                  "ground": "level",
                                  "angle_unit": "degree"}),
           "digits": {"mode": "HALF_UP", "value": d},
           "shadow_length_m": _q(Decimal(repr(val)), d)}
    if applied:
        out["applied_defaults"] = applied
    return out
