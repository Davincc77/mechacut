"""mayakit — bundle 133 (admission 27-11, registre L64, reçu b3026c7c).

Compte long mésoaméricain -> jour civil, par la corrélation NOMMÉE.
La douleur mesurée (COMPIL_RAPPORTS_VAGUE2, section clic 133, §4.2) :
date_parse refuse « 13.0.0.0.0 », date_calc ne sait pas remonter
1 872 000 jours (durations négatives refusées) et text_count compte
cinq mots — un outil qui ne peut PAS nommer la corrélation ne peut pas
auditer les claims 2012 qui divergent justement sur elle.

Table fermée des corrélations, version + sha dans chaque réponse
(doctrine 27-11) : les deux constantes consignées de la matière, GMT
584283 (Goodman–Martinez–Thompson) et GMT+2 584285 (Thompson, dite
« Lounsbury »), lues sur la table de corrélation publiée (page
Mesoamerican Long Count calendar, récupérée 27-11). Les autres
constantes publiées de la même table (Stock, Goodman 584280, Böhm,
Kreichgauer…) sont d'autres contrats : refus par le nom, jamais une
extrapolation.

Grammaire close, publique : cinq positions baktun.katun.tun.uinal.kin ;
valeurs de position 144000 / 7200 / 360 / 20 / 1 ; le compte n'est PAS
du base-20 pur — la deuxième position à droite (uinal) roule à 18
(18 uinal = 1 tun, règle publiée). Écart CONSIGNÉ sur la matière : la
synthèse écrivait « uinal range 0..19 » tout en citant sa gold
12.19.19.17.19 (uinal 17) ; la règle publiée fait foi, uinal est borné
à 17, refus NOMMÉ au-delà — le report n'est jamais silencieux.

Le jour civil se lit dans le pont JDN de juliankit (bundle 135) : la
corrélation 584283 y est déjà gold (JDN 584283 = grégorien -3113-08-11
= julien -3113-09-06), rejouée ici par l'autre porte, fenêtre civile
close -9999..9999 identique, hors portée = refus nommé.
"""
import hashlib
import json
import re
from typing import NoReturn

import juliankit

PLACES = ("baktun", "katun", "tun", "uinal", "kin")
PLACE_VALUES = (144000, 7200, 360, 20, 1)
# ranges fermés par position, dits par la règle publiée (base modifiée :
# seul le uinal roule à 18)
PLACE_MAX = {"kin": 19, "uinal": 17, "tun": 19, "katun": 19}

CORRELATIONS = {
    "gmt-584283": {"days": 584283,
                   "label": "Goodman-Martinez-Thompson (GMT)"},
    "gmt-584285": {"days": 584285,
                   "label": "GMT+2 - Thompson (Lounsbury)"},
}

_WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
             "Saturday", "Sunday")

TABLE_NAME = "maya-long-count-correlations"
TABLE_VERSION = (
    "v1 (2026-11-27) — the two correlations of the named table on the "
    "published Mesoamerican Long Count calendar page: GMT 584283 and "
    "Thompson/Lounsbury GMT+2 584285; place values 144000/7200/360/20/1 "
    "with the published base-18 uinal carry; civil faces replayed on "
    "the juliankit JDN bridge (bundle 135, where JDN 584283 is already "
    "gold)")
TABLE_RULE = ("JDN = correlation_days + 144000*baktun + 7200*katun "
              "+ 360*tun + 20*uinal + 1*kin; digits: kin 0..19, "
              "uinal 0..17 (18 uinal = 1 tun), tun 0..19, katun 0..19, "
              "baktun open up to the closed -9999..9999 civil window")
TABLE_SHA256 = hashlib.sha256(json.dumps(
    {"name": TABLE_NAME, "version": TABLE_VERSION, "rule": TABLE_RULE,
     "correlations": {k: v["days"] for k, v in CORRELATIONS.items()}},
    sort_keys=True, separators=(",", ":")).encode()).hexdigest()

_LC_RE = re.compile(r"^(\d{1,6})\.(\d{1,6})\.(\d{1,6})\.(\d{1,6})"
                    r"\.(\d{1,6})$")


class MayaKitError(Exception):
    def __init__(self, msg, field):
        super().__init__(msg)
        self.msg, self.field = msg, field


def _grammar_refusal(given) -> NoReturn:
    raise MayaKitError(
        "long_count %r is not five dot-separated non-negative places "
        "baktun.katun.tun.uinal.kin (e.g. 13.0.0.0.0). The campaign "
        "measured this string dying in date_parse as unparsable and "
        "counting in text_count as five words — this is the Long Count "
        "contract; the places roll 20/18/20/20 (18 uinal = 1 tun, "
        "never a silent carry)" % given, "long_count")


def _parse_long_count(lc):
    if isinstance(lc, bool) or not isinstance(lc, str):
        raise MayaKitError(
            "long_count %r is %s, not a string — the count is written "
            "baktun.katun.tun.uinal.kin with its dots; a JSON number "
            "collapses 13.0.0.0.0 to a float and loses the places"
            % (lc, type(lc).__name__), "long_count")
    t = lc.strip()
    m = _LC_RE.match(t)
    if not m:
        _grammar_refusal(lc)
    digs = [int(g) for g in m.groups()]
    for place, value in zip(PLACES, digs):
        cap = PLACE_MAX.get(place)
        if cap is not None and value > cap:
            if place == "kin":
                why = ("20 kin = 1 uinal: %d belongs one place left, "
                       "written 0.0.0.%d.0, never carried silently"
                       % (value, value // 20))
            elif place == "uinal":
                why = ("18 uinal = 1 tun (the published base-18 "
                       "carry): %d is written in the tun place, "
                       "never carried silently" % value)
            else:
                why = "20 %s = the next place left — %d is out of " \
                      "range 0..19" % (place, value)
            raise MayaKitError(
                "%s digit %d exceeds %d: %s (closed place ranges, "
                "said by the table)" % (place, value, cap, why),
                "long_count")
    return digs, t


def long_count_to_day(long_count=None, correlation=None):
    if correlation is None:
        raise MayaKitError(
            "correlation: gmt-584283 or gmt-584285 — REQUIRED, never "
            "guessed. The 2012 claims disagree exactly because of this "
            "number (13.0.0.0.0: 21 Dec Friday under 584283, 23 Dec "
            "Sunday under 584285) — a tool that cannot name it cannot "
            "audit them", "correlation")
    if correlation not in CORRELATIONS:
        hint = ""
        if re.fullmatch(r"-?\d{4,7}", correlation):
            hint = (" — the bare number is refused so the choice is "
                    "typed, never guessed: name the correlation, not "
                    "just its days")
        raise MayaKitError(
            "correlation=%r is not in the closed set {gmt-584283, "
            "gmt-584285} of this contract%s. The other correlations on "
            "the published table (Stock, Goodman 584280, Modified "
            "Thompson 1, Pogo, +2CR, Bohm, Kreichgauer) are separate "
            "contracts, not modelled and not synonyms" % (
                correlation, hint), "correlation")
    if long_count is None:
        raise MayaKitError(
            "long_count: the five dot-separated places as written "
            "(13.0.0.0.0) — REQUIRED beside the correlation",
            "long_count")

    digs, given = _parse_long_count(long_count)
    days = sum(d * v for d, v in zip(digs, PLACE_VALUES))
    corr = CORRELATIONS[correlation]
    jdn = corr["days"] + days
    jy, jm, jd = juliankit.julian_from_jdn(jdn)
    gy, gm, gd = juliankit.gregorian_from_jdn(jdn)
    if not (juliankit.Y_MIN <= gy <= juliankit.Y_MAX
            and juliankit.Y_MIN <= jy <= juliankit.Y_MAX):
        raise MayaKitError(
            "long_count %r under %s lands on Gregorian year %d "
            "(Julian %d), outside the closed civil window "
            "-9999..9999 the JDN bridge declares: refused by range, "
            "never truncated" % (given, correlation, gy, jy),
            "long_count")

    return {
        "long_count": given,
        "places": [{"place": p, "digit": d, "value_days": v}
                   for p, d, v in zip(PLACES, digs, PLACE_VALUES)],
        "days": days,
        "correlation": {"name": correlation, "days": corr["days"],
                        "label": corr["label"]},
        "jdn": jdn,
        "jdn_identity": "JDN = %d + %d = %d" % (corr["days"], days, jdn),
        "gregorian": juliankit._fmt(gy, gm, gd),
        "julian": juliankit._fmt(jy, jm, jd),
        "weekday": {"name": _WEEKDAYS[jdn % 7], "iso": jdn % 7 + 1},
        "scale": juliankit.SCALE,
        "bridge": "civil days come from the juliankit JDN bridge "
                  "(bundle 135) — one implementation, one window, the "
                  "584283 epoch gold replayed on both doors",
        "correlation_table": {"name": TABLE_NAME, "version": TABLE_VERSION,
                              "rule": TABLE_RULE,
                              "sha256": TABLE_SHA256},
        "flags": [],
        "applied_defaults": [],
    }
