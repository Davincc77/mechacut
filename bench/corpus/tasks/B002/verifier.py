"""Verifier B002 — clean-table. Contrat pinné probe 2026-11-22 (v0.84.0).

Serveur: /api/v1/recipe/clean-table {csv} -> {rows, columns, removed_rows,
fix_notes, steps, sha256}. removed_rows = int (lignes dédupliquées).
PAIN MESURÉ (pain-map P2) : à v0.84.0 le recipe NE NORMALISE PAS les valeurs
- dates conservées "2026/01/05" et "05/01/2026" (pas d'ISO),
- "1,059.69" conserve le séparateur de milliers.
Le gold (spec, calculé à la main) exige la forme normalisée -> cellules
équipées = FAIL(normalization_gap) tant que le produit ne corrige pas.
Le gold ne change JAMAIS pour suivre le produit (règle deux-golds-deux-sources).

RÉ-SONDÉ 2026-11-22 ~23h (produit corrigé, bundle 62) : art == gold,
dates_non_iso = 0, montants_milliers = 0. Le gap_reason reste en place
comme SENTINELLE À CONTRE-SENS : si le produit rechute en float ou en
slash, il redonne >0 et la sonde crie à nouveau. Le gold n'a pas bougé
d'un octet — c'est le produit qui est venu à lui (deux-golds-deux-sources).
compose() ne fait QUE de la forme (aucune mécanique), il recopie les valeurs.
gap_reason() énumère le gap pour la pain-map.

Artifact: {"input_rows", "duplicates_removed", "row_count", "rows": [...]}
"""
import json

def parse(raw):
    if isinstance(raw, str): raw = json.loads(raw)
    rows = [{"id": int(r["id"]), "name": str(r["name"]).strip(), "amount": str(r["amount"]).strip(),
             "date": str(r["date"]), "category": str(r["category"]).lower()} for r in raw["rows"]]
    rows.sort(key=lambda r: r["id"])
    return {"input_rows": raw["input_rows"], "duplicates_removed": raw["duplicates_removed"],
            "row_count": len(rows), "rows": rows}

def compose(recipe_response, input_order=None):
    rows = [{"id": int(r["id"]), "name": str(r["name"]).strip(), "amount": str(r["amount"]).strip(),
             "date": str(r["date"]), "category": str(r["category"]).lower()} for r in recipe_response["rows"]]
    rows.sort(key=lambda r: r["id"])
    removed = recipe_response.get("removed_rows", 0)
    return {"input_rows": len(rows) + removed, "duplicates_removed": removed,
            "row_count": len(rows), "rows": rows}

def gap_reason(recipe_response):
    """Gap de normalisation mesuré (v0.84.0) — à re-prober dès que le produit bouge."""
    bad_dates = [r["date"] for r in recipe_response["rows"] if "/" in str(r["date"])]
    bad_amounts = [r["amount"] for r in recipe_response["rows"] if str(r["amount"]).count(",") and "." in str(r["amount"])]
    return {"normalization_gap": bool(bad_dates or bad_amounts),
            "dates_non_iso": len(bad_dates), "montants_milliers": len(bad_amounts)}