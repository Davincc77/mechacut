"""Bundle 29 lot 2 — TEMPS. National holiday calendars, closed sets.

Every rule cites its published legal basis; nothing here is folklore:
  FR — Code du travail L3133-1 (Légifrance), 11 fêtes légales
  BE — jours fériés légaux : 10, liste officielle SPF Emploi
       (emploi.belgique.be, relu 25-11-2026), cadre loi du 5
       décembre 1918 ; dimanches mobiles = Pâques occidentale
       (table recopiée ITM, commune FR/BE/LU)
  LU — 11 jours fériés légaux : COTRAV art. L. 232-6 + loi du
       25 avril 2019 (Journée de l'Europe) — listes ITM D9a2 et
       guichet.lu, relues 25-11-2026
  BR — Lei nº 662/1949 (redação Lei 10.607/2002) + Lei 6.802/1980
       (12 de outubro); Sexta-Feira Santa = feriado religioso de
       descanso remunerado (Lei 605/1949, via Lei 9.093/1995).
       Carnaval e Corpus Christi são PONTOS FACULTATIVOS (portaria
       anual) — jamais listados aqui como feriados nacionais.
  PT — Código do Trabalho art. 234º nº 1 (Lei 8/2016, Diário da
       República): 13 feriados obrigatórios.
  DE — common core observed by all Länder; individual Länder add more
       (verdict says so — we do not guess the Land calendar).
  US — 5 U.S.C. 6103: eleven federal holidays, Monday-uniform dates
       since 1971, MLK from 1986, Juneteenth from 2021, and the
       published weekend-observance shift (Sat -> Fri, Sun -> Mon).

Easter: the Gregorian computus published by Meeus / the Explanatory
Supplement, cross-checked against the U.S. Census Bureau table 2000-
2099 in the tests. No network, no wall clock: year is an argument.
"""
from datetime import date, timedelta


class HolidayError(Exception):
    pass


def easter(year):
    """Anonymous Gregorian computus (Meeus), the published algorithm."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _nth_weekday(year, month, weekday, n):
    """weekday: Monday=0 (python). n 1..5 or -1 = last."""
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    if n > 0:
        d = first + timedelta(days=offset + 7 * (n - 1))
        if d.month != month:
            raise HolidayError("no such nth weekday")
        return d
    # last
    nxt = date(year + (month == 12), (month % 12) + 1, 1)
    d = nxt - timedelta(days=1)
    d -= timedelta(days=(d.weekday() - weekday) % 7)
    return d


_FIXED = {
    "FR": [((1, 1), "Jour de l'An", "L3133-1 1°"),
           ((5, 1), "Fête du travail", "L3133-1 3°"),
           ((5, 8), "Victoire 1945", "L3133-1 4°"),
           ((7, 14), "Fête nationale", "L3133-1 7°"),
           ((8, 15), "Assomption", "L3133-1 8°"),
           ((11, 1), "Toussaint", "L3133-1 9°"),
           ((11, 11), "Armistice 1918", "L3133-1 10°"),
           ((12, 25), "Noël", "L3133-1 11°")],
    "LU": [((1, 1), "Nouvel An", "COTRAV L. 232-6"),
           ((5, 1), "Fête du travail", "COTRAV L. 232-6"),
           ((5, 9), "Journée de l'Europe", "loi du 25 avril 2019 (COTRAV L. 232-6)"),
           ((6, 23), "Jour de la célébration publique de l'anniversaire du Grand-Duc", "COTRAV L. 232-6"),
           ((8, 15), "Assomption", "COTRAV L. 232-6"),
           ((11, 1), "Toussaint", "COTRAV L. 232-6"),
           ((12, 25), "Premier jour de Noël", "COTRAV L. 232-6"),
           ((12, 26), "Deuxième jour de Noël (Saint-Étienne)", "COTRAV L. 232-6")],
    "BE": [((1, 1), "Nieuwjaar / 1er janvier", "liste SPF Emploi (loi du 5 déc. 1918, cadre)"),
           ((5, 1), "Dag van de Arbeid / Fête du travail", "liste SPF Emploi (loi du 5 déc. 1918, cadre)"),
           ((7, 21), "Nationale feestdag / Fête nationale", "liste SPF Emploi (loi du 5 déc. 1918, cadre)"),
           ((8, 15), "Onze-Lieve-Vrouw-Hemelvaart / Assomption", "liste SPF Emploi (loi du 5 déc. 1918, cadre)"),
           ((11, 1), "Allerheiligen / Toussaint", "liste SPF Emploi (loi du 5 déc. 1918, cadre)"),
           ((11, 11), "Wapenstilstand / Armistice 1918", "liste SPF Emploi (loi du 5 déc. 1918, cadre)"),
           ((12, 25), "Eerste kerstdag / Noël", "liste SPF Emploi (loi du 5 déc. 1918, cadre)")],
    "BR": [((1, 1), "Confraternização Universal", "Lei 662/1949 art 1º"),
           ((4, 21), "Tiradentes", "Lei 662/1949 art 1º"),
           ((5, 1), "Dia do Trabalhador", "Lei 662/1949 art 1º"),
           ((9, 7), "Independência", "Lei 662/1949 art 1º"),
           ((10, 12), "Nossa Senhora Aparecida", "Lei 6.802/1980"),
           ((11, 2), "Finados", "Lei 10.607/2002"),
           ((11, 15), "Proclamação da República", "Lei 662/1949 art 1º"),
           ((12, 25), "Natal", "Lei 662/1949 art 1º")],
    "PT": [((1, 1), "Dia de Ano Novo", "CT 234º/1"),
           ((4, 25), "Dia da Liberdade", "CT 234º/1"),
           ((5, 1), "Dia do Trabalhador", "CT 234º/1"),
           ((6, 10), "Dia de Portugal", "CT 234º/1"),
           ((8, 15), "Assunção de Maria", "CT 234º/1"),
           ((10, 5), "Implantação da República", "CT 234º/1"),
           ((11, 1), "Todos-os-Santos", "CT 234º/1"),
           ((12, 1), "Restauração da Independência", "CT 234º/1"),
           ((12, 8), "Imaculada Conceição", "CT 234º/1"),
           ((12, 25), "Natal", "CT 234º/1")],
    "DE": [((1, 1), "Neujahr", "common to all Länder"),
           ((5, 1), "Tag der Arbeit", "common to all Länder"),
           ((10, 3), "Tag der Deutschen Einheit", "Einigungsvertrag"),
           ((12, 25), "1. Weihnachtstag", "common to all Länder"),
           ((12, 26), "2. Weihnachtstag", "common to all Länder")],
}
_MOVING = {
    "FR": [(1, "Lundi de Pâques", "L3133-1 2°"),
           (39, "Ascension", "L3133-1 5°"),
           (50, "Lundi de Pentecôte", "L3133-1 6°")],
    "LU": [(1, "Lundi de Pâques", "COTRAV L. 232-6"),
           (39, "Ascension", "COTRAV L. 232-6"),
           (50, "Lundi de Pentecôte", "COTRAV L. 232-6")],
    "BE": [(1, "Paasmaandag / Lundi de Pâques", "liste SPF Emploi (loi du 5 déc. 1918, cadre)"),
           (39, "Hemelvaart / Ascension", "liste SPF Emploi (loi du 5 déc. 1918, cadre)"),
           (50, "Pinkstermaandag / Lundi de Pentecôte", "liste SPF Emploi (loi du 5 déc. 1918, cadre)")],
    "BR": [(-2, "Sexta-Feira Santa",
            "Lei 605/1949 (feriado religioso; Lei 9.093/1995)")],
    "PT": [(-2, "Sexta-feira Santa (Paixão do Senhor)", "CT 234º/1"),
           (0, "Páscoa", "CT 234º/1"),
           (60, "Corpo de Deus", "CT 234º/1")],
    "DE": [(-2, "Karfreitag", "common to all Länder"),
           (1, "Ostermontag", "common to all Länder"),
           (39, "Christi Himmelfahrt", "common to all Länder"),
           (50, "Pfingstmontag", "common to all Länder")],
}
_NOTES = {
    "BR": "Carnaval and Corpus Christi are pontos facultativos "
          "(annual federal portaria), NOT national holidays — state "
          "and municipal calendars add their own days.",
    "DE": "Individual Länder add holidays (Heilige Drei Könige, "
          "Fronleichnam, Assumption in Saar, Reformationstag, "
          "Allerheiligen, Augsburger Friedensfest, Buß- und Bettag "
          "in Sachsen) — this endpoint returns the all-Länder core "
          "only and says so.",
    "PT": "Autonomous regions (Açores/Madeira) add holidays.",
    "FR": "Alsace-Moselle adds Good Friday and December 26.",
    "LU": "11 legal holidays (COTRAV L. 232-6 + loi du 25 avril 2019). "
          "Saturday IS a business day (jour ouvrable) per the official "
          "glossaire guichet.lu and ITM D9a3 — only Sundays and legal "
          "holidays are not. Employers may substitute local/professional "
          "days keeping 11 — the legal list is what returns.",
    "BE": "10 federal legal holidays (liste SPF Emploi; regional/"
          "community days — 28 September FWB, 11 July Flanders, 1 July "
          "BC — are NOT federal and do not enter). Substitution days "
          "per joint committee (e.g. Saint-Éloi 1 December, CP 104) "
          "are not folded in. For deadlines the new Civil Code art. "
          "I.7 §3 (loi du 28 avril 2022) excludes Saturdays from "
          "jours ouvrables.",
}
# US built by its own rules (date arithmetic + observance shift)
_US_LAW = [
    ("New Year's Day", (1, 1), None, 1900),
    ("Birthday of Martin Luther King, Jr.", None, ("jan", 3, 0), 1986),
    ("Washington's Birthday", None, ("feb", 3, 0), 1971),
    ("Memorial Day", None, ("memorial",), 1971),
    ("Juneteenth National Independence Day", (6, 19), None, 2021),
    ("Independence Day", (7, 4), None, 1900),
    ("Labor Day", None, ("sep", 1, 0), 1913),
    ("Columbus Day", None, ("oct", 2, 0), 1971),
    ("Veterans Day", (11, 11), None, 1938),
    ("Thanksgiving Day", None, ("nov", 4, 3), 1941),
    ("Christmas Day", (12, 25), None, 1900),
]


def _us_holidays(year):
    out = []
    for name, md, rule, since in _US_LAW:
        if year < since:
            continue
        if md:
            d = date(year, md[0], md[1])
        elif rule[0] == "memorial":
            d = _nth_weekday(year, 5, 0, -1)
        else:
            month = {"jan": 1, "feb": 2, "sep": 9, "oct": 10,
                     "nov": 11}[rule[0]]
            d = _nth_weekday(year, month, rule[2], rule[1])
        entry = {"date": d.isoformat(), "name": name,
                 "law": "5 U.S.C. 6103 (since %d)" % since}
        wd = d.weekday()
        if wd == 5:
            entry["observed"] = (d - timedelta(days=1)).isoformat()
            entry["shift"] = "Saturday holiday observed Friday before"
        elif wd == 6:
            entry["observed"] = (d + timedelta(days=1)).isoformat()
            entry["shift"] = "Sunday holiday observed Monday following"
        out.append(entry)
    return out


def holidays(country, year):
    c = (country or "").upper()
    if not isinstance(year, int) or not 1900 <= year <= 2099:
        raise HolidayError("year must be an integer 1900-2099 "
                           "(the anchored computus range)")
    if c == "US":
        return {"country": c, "year": year,
                "scope": "federal holidays (5 U.S.C. 6103)",
                "easter": easter(year).isoformat(),
                "holidays": _us_holidays(year),
                "count": len(_us_holidays(year))}
    if c not in _FIXED:
        raise HolidayError("country %r outside the closed set (FR BE "
                           "LU BR PT DE US); this calendar is law, not "
                           "vibes — other countries ship when sourced"
                           % country)
    e = easter(year)
    days = [{"date": date(year, m, dd).isoformat(), "name": n,
             "law": law} for (m, dd), n, law in _FIXED[c]]
    for off, n, law in _MOVING.get(c, []):
        days.append({"date": (e + timedelta(days=off)).isoformat(),
                     "name": n, "law": law})
    days.sort(key=lambda x: x["date"])
    return {"country": c, "year": year, "scope": "national legal core",
            "easter": e.isoformat(), "holidays": days,
            "count": len(days),
            "note": _NOTES.get(c, "")}


def is_holiday(country, day):
    d = day if isinstance(day, date) else date.fromisoformat(str(day))
    h = holidays(country, d.year)
    for x in h["holidays"]:
        if x["date"] == d.isoformat():
            return {**h, "query": d.isoformat(), "is_holiday": True,
                    "matched": x}
    # US: a holiday FALLING on the weekend is observed elsewhere —
    # the query date matching the law's calendar day is what counts here
    return {**h, "query": d.isoformat(), "is_holiday": False}
