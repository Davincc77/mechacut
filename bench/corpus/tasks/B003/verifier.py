"""Verifier B003 — faits d'une note d'incident. Contrat pinné probe 2026-11-22 (v0.84.0).

PAINS MESURÉS à v0.84.0, voie équipée NON fonctionnelle (pain-map P3) :
1. MISROUTE: /intent/card (utterance) -> money_baggage (bagages !) ;
   /router/plan (texte) -> fiche "partage-reste" cible "second_share"
   (le problème de chaîne, pas l'extraction facts). Deux aiguillages faux.
2. FRAGMENTS: /api/v1/recipe/facts extrait "450,75", "900,00", "000,00" des
   montants FR à espace-milliers ("12 450,75" -> "12" + "450,75") et ne sort
   ni money[] ni total.
Le gold (money DESC + percents + dates uniques + url + email + total) reste le
contrat spec. compose() = artefact serveur brut marqué _gap; l'égalité
canonique au gold est FAUSSE -> cellule FAIL(misroute|fragments) jusqu'à
correction produit; le jour où c'est fixé, la sonde repasse au vert.

Cadenas/synonymes (banc parallèle, à intégrer pain-map P1) : une réponse
correcte arrivant avec le mot de l'énoncé doit passer — sinon on facture des
refus absurdes. Enseigner les synonymes au serveur (~½ journée, sans risque).
"""
import json, re
from decimal import Decimal

def _money(s):
    t = re.sub(r"[^0-9.,-]", "", str(s)).replace(" ", "")
    if "," in t and "." in t:
        t = t.replace(",", "") if t.rfind(",") < t.rfind(".") else t.replace(".", "").replace(",", ".")
    elif "," in t:
        t = t.replace(",", ".")
    return f"{Decimal(t):.2f}"

def parse(raw):
    if isinstance(raw, str): raw = json.loads(raw)
    return {"money": sorted([_money(m) for m in raw["money"]], key=Decimal, reverse=True),
            "percents": sorted([str(Decimal(p.rstrip("%").replace(",", "."))) + "%" for p in raw["percents"]], key=Decimal),
            "dates": sorted(raw["dates"]), "url": str(raw["url"]), "email": str(raw["email"]),
            "total": _money(raw["total"])}

def compose(tool_output, input_order=None):
    """RÉ-SONDÉE 2026-11-22 ~23h (bundle 62) : l'extraction FR marche —
    money groupée « 12 450,75 € » -> 12450.75, percents canonisés,
    total exact. compose projette l'output serveur sur la FORME du
    gold (mêmes clés, mêmes tri) — l'égalité canonique DOIT tenir ; si
    le produit rechute en fragments, sha != gold et la sonde hurle.
    Le MISROUTE (intent/plan) reste ouvert — douleur d'une autre
    juridiction (instance routeur), sentinel inchangé côté plan."""
    from decimal import Decimal
    inv = (tool_output or {}).get("inventory", {})
    def _pdec(p):
        return Decimal(str(p).rstrip("%").replace(",", "."))
    return {"money": sorted(inv.get("money", []), key=Decimal,
                            reverse=True),
            "percents": sorted(inv.get("percent", []), key=_pdec),
            "dates": sorted(inv.get("date", [])),
            "url": (inv.get("url") or [None])[0],
            "email": (inv.get("email") or [None])[0],
            "total": _money(tool_output.get("total_money"))}