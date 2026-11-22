"""compkit — /api/v1/money/flight_comp : la compensation vol, DEUX états
du monde, choisie par la DATE DU VOL — pas par la date de presse.

Le règlement (UE) 2026/2202 est entré en vigueur le 22 octobre 2026 mais
NE S'APPLIQUE QU'AU 23 OCTOBRE 2027 (Art. 3 : « It shall apply from
23 October 2027 » — EUR-Lex, texte rejoué). La presse a fondu les deux
dates (« eu261rights: A great deal of what has been written about it is
wrong »), et un modèle sans table fondra aussi : la même question sur un
vol de 2027-06 et un vol de 2027-11 a des RÉPONSES DIFFÉRENTES. C'est
exactement le genre de règle que les modèles rabotent en une seule.

Tables rejouées AU TEXTE (cache EUR-Lex 32026R2202 + legislation.gov.uk,
vérifiés 22 nov. 2026) :
  A — vols EU avant le 23-oct-2027 : 261/2004 original + jurisprudence
      (Sturgeon C-402/08 seuil « AT LEAST 3 h » ; Nelson C-581/10 : >3500
      hors-UE 3-4 h = 50 % ; Wegener C-537/17 correspondance manquée).
      Forclusion : AUCUNE dans le règlement — lois des États membres.
  B — vols EU à partir du 23-oct-2027 : Art. 6(4) « EXCEEDING three
      hours » (STRICT : 180 min pile ne paye pas), Art. 5(5) exemption
      deux branches (≥14 jours, OU reroute part ≤1 h avant ET arrive
      <2 h après), Art. 7(2) 50 % collé au seul point (c) arrivée ≤+4 h,
      Art. 7(3) nouvelles réductions 50 %/25 % reroute partant >1 h
      AVANT, Art. 7(5) distance = départ initial → destination FINALE
      grand cercle, Art. 7(9) demande sous NEUF MOIS depuis la date de
      départ effective du billet + réponse du transporteur sous 30 jours
      calendaires, Art. 15a plainte 12 mois.
  UK — UK261 (retained law, amendé) : Art. 7 F15 £220/£350/£520 ;
      Art. 6(3) F143 « 3 h ou plus » ; table officielle gov.uk « Air
      passenger travel guide » Table 2 avec ses propres vecteurs
      (Glasgow-Amsterdam £220 ; East Midlands-Marrakech £350 ;
      London-New York £520, £260 si arrivée sous 4 h). UK261 n'existe
      pas avant le 2021-01-01 — refusé par le nom.

Contrat d'entrée = chaînes (ScaleRequest precedent) : NOMBRES FOURNIS,
jamais de fetch de vol, jamais de devinette de juridiction (intra_eu
REFUSÉ d'être deviné — le plafond intra-UE €400 est précisément ce que
les modèles ratent : « the single most misreported fact » — receiptroad).
Réductions rendues en OPTIONS nommées : le texte dit « MAY reduce » —
le transporteur PEUT, ne DOIT pas ; la route le DIT, ne choisit pas.
"""

import re
from datetime import date
from fractions import Fraction

_APPLIES_B = date(2027, 10, 23)   # Reg. (EU) 2026/2202, Art. 3
_UK261_START = date(2021, 1, 1)   # UK261 retained law boundary

_EVENTS = {"denied_boarding", "cancellation", "delay", "missed_connection"}
_YESNO = {"yes": True, "no": False}

_EXPECTED = {
    "regime": "'EU' or 'UK' — never guessed (the two systems pay "
              "different amounts for the same flight)",
    "flight_date": "ISO date 'YYYY-MM-DD' of the flight — it SELECTS "
                   "the table (Reg. 2026/2202 applies from 2027-10-23)",
    "event": "one of: 'denied_boarding' | 'cancellation' | 'delay' | "
             "'missed_connection'",
    "distance_km": "great-circle km from initial departure to the FINAL "
                   "destination (Art. 7(5)); supplied, never fetched — "
                   "compute it with /api/v1/geo/distance if needed",
    "intra_eu": "'yes' or 'no' — required for EU flights above 1500 km: "
                "it is what decides €400 (intra cap, b) vs €600 (c)",
    "delay_min": "whole minutes of delay at arrival at the final "
                 "destination vs the scheduled arrival",
    "notice_days": "whole days between the notification of cancellation "
                   "and the scheduled departure",
    "rerouted": "'yes' or 'no' — was a rerouting offered",
    "reroute_depart_early_min": "whole minutes EARLIER than the original "
                                "scheduled departure the reroute leaves "
                                "(0 if it leaves at/after the original)",
    "reroute_arrive_late_min": "whole minutes LATER at the final "
                               "destination than the original scheduled "
                               "arrival (0 if it arrives at/earlier)",
    "extraordinary": "'yes'/'no' — the carrier INVOKES extraordinary "
                     "circumstances (assessment of facts is a legal "
                     "call, not arithmetic; amounts shown are before "
                     "that exemption)",
}


class CompError(ValueError):
    def __init__(self, field, message, expected=None):
        super().__init__(message)
        self.field = field
        self.message = message
        self.expected = expected or _EXPECTED.get(field, "")


# ---------------------------------------------------------------- inputs

def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise CompError(field, "missing or empty (a JSON number is "
                        "refused — pass the string)")
    return value.strip()


def _yesno(value, field, default=None):
    if value is None:
        if default is None:
            raise CompError(field, "missing", _EXPECTED.get(field))
        return default
    t = _text(value, field).lower()
    if t not in _YESNO:
        raise CompError(field, "must be 'yes' or 'no', got %r" % value)
    return _YESNO[t]


def _int(value, field, minimum=0):
    t = _text(value, field)
    if not re.match(r"^[+-]?\d+$", t):
        raise CompError(field, "not a whole number: %r" % value)
    n = int(t)
    if n < minimum:
        raise CompError(field, "must be >= %d, got %d" % (minimum, n))
    return n


def _amount(value, field):
    """distance : entier ou décimal borné, rendu exact."""
    t = _text(value, field)
    if not re.match(r"^\d+(\.\d{1,3})?$", t):
        raise CompError(field, "a decimal km value like '5800' or "
                        "'5800.75', got %r" % value)
    return Fraction(t)


def _iso_date(value, field="flight_date"):
    t = _text(value, field)
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", t)
    if not m:
        raise CompError(field, "strict ISO date 'YYYY-MM-DD', got %r"
                        % value)
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError as exc:
        raise CompError(field, "impossible date %r (%s)" % (value, exc))


def _add_months(d, n):
    """Même jour de mois ; si le jour n'existe pas, DERNIER jour du
    mois cible (règle de clamp nommée dans la réponse)."""
    y, m = divmod(d.month - 1 + n, 12)
    y += d.year
    m += 1
    last = [31, 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0))
            else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
    return date(y, m, min(d.day, last))



# ---------------------------------------------------------------- bands

def _band_eu(d_km, intra):
    """261/2004 Art. 7(1) : (a) <=1500 ; (b) intra-UE >1500 et autres
    1500<d<=3500 ; (c) le reste. Le plafond intra-UE (b) s'applique AU-
    DELA de 3500 km — la règle la plus ratée."""
    if d_km <= 1500:
        return "a", Fraction(250), "Art. 7(1)(a) — journeys of 1500 km " \
                                   "or less: EUR 250"
    if intra:
        note = ""
        if d_km > 3500:
            note = " — INTRA-UNION CAP: even above 3500 km an intra-UE " \
                   "journey stays (b) at EUR 400 (the most misreported " \
                   "band)"
        return "b", Fraction(400), "Art. 7(1)(b) — all intra-Union " \
                                   "journeys of more than 1500 km: EUR " \
                                   "400" + note
    if d_km <= 3500:
        return "b", Fraction(400), "Art. 7(1)(b) — journeys between " \
                                   "1500 and 3500 km: EUR 400"
    return "c", Fraction(600), "Art. 7(1)(c) — journeys not falling " \
                               "under (a) or (b): EUR 600"


def _band_uk(d_km):
    """UK261 Art. 7 F15 : pas de concept intra-UE — bandes de distance."""
    if d_km <= 1500:
        return "a", Fraction(220), "UK261 Art. 7(1)(a) — 1500 km or " \
                                   "less: GBP 220"
    if d_km <= 3500:
        return "b", Fraction(350), "UK261 Art. 7(1)(b) — between 1500 " \
                                   "and 3500 km: GBP 350"
    return "c", Fraction(520), "UK261 Art. 7(1)(c) — otherwise: GBP 520"


# ---------------------------------------------------------------- tables

def _table_of(regime, fd):
    if regime == "UK":
        if fd < _UK261_START:
            raise CompError(
                "flight_date",
                "UK261 does not exist before 2021-01-01 — a UK-departing "
                "flight before that date falls under Regulation (EC) "
                "261/2004 as then in force; pass regime='EU' only if the "
                "legal basis is the EU regulation, else refuse")
        return "UK", {
            "id": "UK261",
            "label": "UK261 — retained Regulation (EC) 261/2004, as "
                     "amended (delay right Art. 6(3) F143; amounts "
                     "Art. 7 F15)",
            "why": "regime UK; applies to every flight date on record "
                    "from 2021-01-01"}
    if fd < _APPLIES_B:
        return "A", {
            "id": "261/2004+case-law",
            "label": "Regulation (EC) 261/2004 ORIGINAL text + CJEU "
                     "case-law (delay right: Sturgeon C-402/08 'at "
                     "least 3 hours'; Nelson C-581/10 long-haul 3-4 h "
                     "= 50 %; Wegener C-537/17)",
            "why": "flight %s is BEFORE the application date of Reg. "
                   "(EU) 2026/2202 (2027-10-23, Art. 3) — the old table "
                   "governs" % fd.isoformat()}
    return "B", {
        "id": "amended-2026/2202",
        "label": "Regulation (EC) 261/2004 AS AMENDED by Regulation "
                 "(EU) 2026/2202 — 'It shall apply from 23 October "
                 "2027' (Art. 3, EUR-Lex)",
        "why": "flight %s is ON/AFTER 2027-10-23 — the new codified "
               "rules govern" % fd.isoformat()}


def _red(pct, cite, cond, base, symbol):
    value = base * (Fraction(100 - pct, 100))
    return {"percent": pct, "cite": cite, "condition": cond,
            "amount": "%s%s" % (symbol, _disp(value))}


def _disp(fr):
    if fr.denominator == 1:
        return "%d" % fr
    return "%.2f" % float(fr)


def decide(args):
    regime = _text(args.get("regime"), "regime").upper()
    if regime not in ("EU", "UK"):
        raise CompError("regime", "must be 'EU' or 'UK', got %r"
                        % args.get("regime"))
    fd = _iso_date(args.get("flight_date"))
    event = _text(args.get("event"), "event").lower()
    if event not in _EVENTS:
        raise CompError("event", "unknown event %r" % args.get("event"))
    d_km = _amount(args.get("distance_km"), "distance_km")
    if d_km <= 0:
        raise CompError("distance_km", "must be > 0")

    if regime == "UK":
        if args.get("intra_eu") is not None:
            raise CompError(
                "intra_eu",
                "refused: UK261 bands are PURE distance — there is no "
                "intra-Union band; remove the field")
        band, base, band_rule = _band_uk(d_km)
        symbol = "£"
    else:
        if d_km > 1500:
            intra = _yesno(args.get("intra_eu"), "intra_eu")
        else:
            intra = None
            if args.get("intra_eu") is not None:
                raise CompError(
                    "intra_eu",
                    "not needed: below/at 1500 km the band is (a) in "
                    "both cases; remove the field")
        band, base, band_rule = _band_eu(d_km, intra)
        symbol = "€"

    tcode, table = _table_of(regime, fd)
    extraordinary = _yesno(args.get("extraordinary"), "extraordinary",
                           default=False)

    owed = base
    exemptions = []
    reductions = []
    threshold = None
    rerouted = None
    dep_early = arr_late = 0

    if event in ("delay", "missed_connection"):
        delay_min = _int(args.get("delay_min"), "delay_min")
        if regime == "UK":
            cite_evt = ("UK261 Art. 6(3) (F143) — delay at arrival of "
                        "three hours or more gives the Art. 7 right")
        elif tcode == "A":
            cite_evt = ("Sturgeon C-402/08 + Nelson C-581/10 — the "
                        "ORIGINAL Art. 6 text gives NO compensation for "
                        "delay; the right is case-law"
                        if event == "delay" else
                        "Wegener C-537/17 — a delayed leg of one "
                        "journey carries the Art. 7 right at the FINAL "
                        "destination (case-law, not text)")
        else:
            cite_evt = ("Art. 6(4) as amended — 'delay at arrival "
                        "EXCEEDING three hours'"
                        if event == "delay" else
                        "Art. 6b(3) as amended — missed connection on "
                        "one journey: delay measured from the arrival "
                        "of the itinerary as booked")
        if regime == "UK" or tcode == "A":
            # seuil jurisprudentiel/guidance : « 3 hours OR MORE »
            threshold = {"rule": "delay at arrival AT LEAST 3 h (180 "
                                 "min) — Sturgeon C-402/08 (A) / UK261 "
                                 "Art. 6(3) F143",
                         "met": delay_min >= 180,
                         "input_min": delay_min}
            if delay_min < 180:
                owed = Fraction(0)
                exemptions.append({
                    "cite": cite_evt,
                    "rule": "threshold not met: %d min < 3 h" % delay_min})
            elif band == "c" and ((regime == "UK" and delay_min < 240)
                                  or (regime == "EU"
                                      and delay_min <= 240)):
                if regime == "UK":
                    owed = base / 2   # table officielle gov.uk : £260
                    threshold["rule"] += ("; long-haul split: under 4 h "
                                          "late = 50 % (£260), 4 h or "
                                          "more = £520 — gov.uk Air "
                                          "passenger travel guide "
                                          "Table 2")
                else:
                    reductions.append(_red(
                        50, "Nelson C-581/10 via Art. 7(2)(c)",
                        "long-haul (>3500 km, non-intra) arriving 3-4 h "
                        "late: the 50 % window applies — the carrier "
                        "MAY reduce", base, symbol))
        else:
            # Table B : EXCEEDING three hours — STRICT
            threshold = {"rule": "delay at arrival EXCEEDING 3 h — "
                                 "Art. 6(4) as amended ('exceeding', "
                                 "strict: exactly 180 min does NOT "
                                 "pay)",
                         "met": delay_min > 180,
                         "input_min": delay_min}
            if delay_min <= 180:
                owed = Fraction(0)
                exemptions.append({
                    "cite": cite_evt,
                    "rule": "threshold not met: %d min does not EXCEED "
                            "three hours (Art. 6(4) as amended)"
                            % delay_min})
            elif band == "c" and delay_min <= 240:
                reductions.append(_red(
                    50, "Art. 7(2) as amended — point (c) only, arrival "
                        "within +4 h ('delay at arrival of the journey "
                        "originally booked' limb (b))",
                    "long-haul (>3500 km, non-intra) arriving 3 h to "
                    "4 h late: the carrier MAY reduce by 50 %",
                    base, symbol))

    elif event == "cancellation":
        notice_days = _int(args.get("notice_days"), "notice_days")
        rerouted = _yesno(args.get("rerouted"), "rerouted", default=False)
        dep_early = arr_late = 0
        if rerouted:
            dep_early = _int(args.get("reroute_depart_early_min"),
                             "reroute_depart_early_min")
            arr_late = _int(args.get("reroute_arrive_late_min"),
                            "reroute_arrive_late_min")
        if regime == "UK" or tcode == "A":
            # 261/2004 original Art. 5(1)(c) matrix (UK: same retained
            # structure, different amounts)
            cite_5 = ("UK261 Art. 5(1)(c) as retained" if regime == "UK"
                      else "Art. 5(1)(c) (original)")
            if notice_days >= 14:
                owed = Fraction(0)
                exemptions.append({
                    "cite": cite_5 + " (i)",
                    "rule": "informed at least two weeks (>=14 days) "
                            "before scheduled departure — no "
                            "compensation"})
            elif 7 <= notice_days < 14 and rerouted and \
                    dep_early <= 120 and arr_late < 240:
                owed = Fraction(0)
                exemptions.append({
                    "cite": cite_5 + " (ii)",
                    "rule": "informed 7-13 days ahead AND rerouting "
                            "departs <=2 h early, arrives <4 h late "
                            "at final destination — no compensation"})
            elif notice_days < 7 and rerouted and \
                    dep_early <= 60 and arr_late < 120:
                owed = Fraction(0)
                exemptions.append({
                    "cite": cite_5 + " (iii)",
                    "rule": "informed <7 days ahead AND rerouting "
                            "departs <=1 h early, arrives <2 h late — "
                            "no compensation"})
            elif rerouted:
                windows = {"a": (120, "2 h"), "b": (180, "3 h"),
                           "c": (240, "4 h")}
                win, wtxt = windows[band]
                if arr_late <= win:
                    reductions.append(_red(
                        50, "Art. 7(2) — rerouting arrival within +%s of "
                            "the original scheduled arrival" % wtxt,
                        "carrier offered rerouting arriving within +%s "
                        "— the carrier MAY reduce by 50 %%. Text says "
                        "'MAY', not 'shall'" % wtxt,
                        base, symbol))
        else:
            # Table B : Art. 5(5) — deux branches seulement
            if notice_days >= 14:
                owed = Fraction(0)
                exemptions.append({
                    "cite": "Art. 5(5) as amended, first limb",
                    "rule": "informed at least 14 calendar days before "
                            "the departure date of the ticket — no "
                            "compensation"})
            elif rerouted and dep_early <= 60 and arr_late < 120:
                owed = Fraction(0)
                exemptions.append({
                    "cite": "Art. 5(5) as amended, second limb",
                    "rule": "rerouting offered: departs <=1 h early AND "
                            "arrives <2 h late at final destination — "
                            "no compensation (the 7-14 d / <7 d "
                            "branches of the OLD text are GONE)"})
            else:
                if band == "c" and rerouted and arr_late <= 240:
                    reductions.append(_red(
                        50, "Art. 7(2) as amended — point (c), rerouting "
                            "at a later time arriving within +4 h",
                        "rerouting offered arriving <=4 h late on a "
                        ">3500 km non-intra journey — the carrier MAY "
                        "reduce by 50 %", base, symbol))
                if rerouted and dep_early > 60:
                    if dep_early < 120:
                        reductions.append(_red(
                            50, "Art. 7(3)(a) as amended",
                            "reroute scheduled to depart MORE than 1 h "
                            "but LESS than 2 h early and the passenger "
                            "took the flight — the carrier MAY reduce "
                            "by 50 %", base, symbol))
                    if dep_early < 180:
                        reductions.append(_red(
                            25, "Art. 7(3)(b) as amended",
                            "reroute brought forward by less than 3 h "
                            "and the passenger took the flight — the "
                            "carrier MAY reduce by 25 %", base, symbol))

    elif event == "denied_boarding":
        if regime == "UK":
            exemptions.append({"cite": "UK261 Art. 4(3) as retained",
                               "rule": "involuntary denied boarding: "
                                       "compensation under Art. 7(1) — "
                                       "full band, no rerouting window "
                                       "applies"})
        elif tcode == "A":
            exemptions.append({"cite": "Art. 4(3) (original)",
                               "rule": "denied boarding against the "
                                       "passenger's will: compensate "
                                       "immediately per Art. 7"})
        else:
            exemptions.append({"cite": "Art. 4(4) as amended",
                               "rule": "involuntary denied boarding: "
                                       "pay under Art. 7(1) without "
                                       "undue delay, at the latest 7 "
                                       "calendar days after denial — "
                                       "full band"})

    # deadlines
    if regime == "EU" and tcode == "B":
        claim_by = _add_months(fd, 9)
        deadlines = {
            "claim_by": claim_by.isoformat(),
            "claim_within": "nine months from the ACTUAL date of "
                            "departure indicated on the ticket "
                            "(Art. 7(9) as amended)",
            "claim_rule": "same day-of-month + 9 months; if that day "
                          "does not exist in the target month, its "
                          "LAST day (clamp)",
            "claim_day_clamped": claim_by.day != fd.day,
            "carrier_answer_days": 30,
            "carrier_answer_rule": "pay or justify within 30 calendar "
                                   "days of receipt (Art. 7(9)); "
                                   "acknowledgement immediate",
            "complaint_by": _add_months(fd, 12).isoformat(),
            "complaint_rule": "Art. 15a: complaint within 12 months of "
                              "the flight date OR three months after "
                              "the compensation request — whichever is "
                              "LATER; the flight-date bound is shown",
        }
    else:
        deadlines = {
            "claim_by": None,
            "rule": ("Regulation 261/2004 (original) sets NO statutory "
                     "claim deadline — Member State limitation law "
                     "governs and the tool refuses to guess it"
                     if regime == "EU" else
                     "UK261 sets no statutory claim deadline in the "
                     "regulation — contract limitation under national "
                     "law (England/Wales vs Scotland differ) is OUT of "
                     "the closed grammar; ask a lawyer, not a regex"),
        }

    info = []
    if regime == "EU" and tcode == "B":
        info.append("Art. 7(4) as amended: within 96 h of the end of "
                    "the journey the carrier must send the passenger, "
                    "on a durable medium, the right to compensation "
                    "AND how to request it")
    if extraordinary:
        info.append("extraordinary circumstances INVOKED: exemption "
                    "requires proof of the direct causal link AND that "
                    "all reasonable measures were taken (Art. 6c(2) as "
                    "amended / Art. 5(3)-6(4) before) — that is an "
                    "assessment of facts, NOT arithmetic; amounts "
                    "above are BEFORE that exemption")
    else:
        info.append("extraordinary circumstances NOT invoked in the "
                    "inputs — if the carrier proves them, the "
                    "compensation may drop to zero (Art. 6c(2))")

    owed_display = "%s%s" % (symbol, _disp(owed))
    verdict = ("under %s, flight %s, %s km band %s, %s: %s%s" % (
        table["id"], fd.isoformat(), _disp(d_km), band, event,
        owed_display,
        " — %d reduction option(s) the carrier MAY take" % len(reductions)
        if reductions else ""))

    return {
        "regime": regime,
        "flight_date": fd.isoformat(),
        "event": event,
        "distance_km": _disp(d_km),
        "band": {"letter": band, "cite": band_rule},
        "table": table,
        "threshold": threshold,
        "owed": {"amount": _disp(owed), "display": owed_display,
                 "currency": "EUR" if regime == "EU" else "GBP",
                 "per": "passenger"},
        "exemption_or_refusal": exemptions or None,
        "reductions_may": reductions,
        "deadlines": deadlines,
        "info": info,
        "rerouted": ("yes" if rerouted else "no")
                    if event == "cancellation" else None,
        "intra_eu": ("yes" if intra else "no") if regime == "EU"
                    and d_km > 1500 else None,
        "verdict": verdict,
        "scope_note": [
            "deterministic arithmetic over numbers GIVEN — no flight "
            "data is ever fetched; this is not legal advice",
            "distance basis = initial departure -> FINAL destination "
            "of the whole journey, great-circle (Art. 7(5) as amended; "
            "Art. 7(4) before; UK261 Art. 7(4)) — supply it, e.g. via "
            "/api/v1/geo/distance",
            "press coverage conflated entry-into-force (2026-10-22) "
            "with APPLICATION (2027-10-23): the table here is keyed by "
            "the FLIGHT DATE, the only date that decides",
        ],
    }
