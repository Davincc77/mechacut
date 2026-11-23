# -*- coding: utf-8 -*-
"""Bundle 94 — CORS chirurgicale : le navigateur devient un client légitime.

La question d'un auditeur concepteur (« CORS is wide open — the mockup can
be genuinely functional ») mérite une réponse MESURÉE, pas un avis :
l'état mesuré avant ce bundle était : moovicut = `access-control-allow-origin:
*` ; mechacut = AUCUN en-tête, OPTIONS → 405. Un mockup navigateur sur
mechacut lisait donc RIEN (fetch bloqué côté client).

Décision (c'est l'appel de l'usine, pas l'arbitrage du repo voisin) :
ouvrir les portes GRATUITES — la promesse produit est « un agent, c'est
du texte collé » ; un agent dans un onglet est un agent. Les portes
PAYANTES restent opaques au cross-origin : x402 est un contrat signé par
un humain, pas une facture à cloner par une page. Ouverture bornée :
content-type/accept uniquement, GET/POST/OPTIONS, max-age dit.

Golds tracés main :
  K1 OPTIONS préflight sur une route gratuite -> 204, allow-origin *,
     allow-methods exactes, allow-headers exactes, max-age 86400.
  K2 POST gratuit cross-origin -> 200 + ACAO * présent.
  K3 OPTIONS préflight sur route PAYANTE (/api/v1/chart) -> PAS d'
     allow-origin dans la réponse (pas de 405 non plus : le verbe est
     répondu, la porte est fermée à la lecture cross-origin).
  K4 route gratuite sans en-tête Origin -> en-tête CORS ABSENT : le
     curl des agents ne voit rien changer (comportement historique).
  K5 OPTIONS sur route inexistante -> 405 (le 204 n'est pas un 404
     maquillé : on ne fait pas semblant d'exister).
"""
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)

FREE = "/api/v1/date/parse"
PAID = "/api/v1/chart"
ORIGIN = {"Origin": "https://exemple.com"}


def test_k1_preflight_free_is_204_with_named_bounds():
    r = client.options(FREE, headers={**ORIGIN,
                   "Access-Control-Request-Method": "POST",
                   "Access-Control-Request-Headers": "content-type"})
    assert r.status_code == 204
    assert r.headers["access-control-allow-origin"] == "*"
    assert "POST" in r.headers["access-control-allow-methods"]
    assert r.headers["access-control-allow-headers"] == "content-type, accept"
    assert r.headers["access-control-max-age"] == "86400"


def test_k2_free_post_cross_origin_carries_the_header():
    r = client.post(FREE, json={"text": "2026-12-25"}, headers=ORIGIN)
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "*"


def test_k3_paid_route_never_opens():
    r = client.options(PAID, headers={**ORIGIN,
                   "Access-Control-Request-Method": "POST"})
    assert r.status_code == 204
    assert "access-control-allow-origin" not in r.headers


def test_k4_same_origin_curls_see_nothing_new():
    r = client.post(FREE, json={"text": "2026-12-25"})
    assert r.status_code == 200
    assert "access-control-allow-origin" not in r.headers


def test_k5_preflight_is_not_a_masked_404():
    r = client.options("/api/v1/does/not/exist", headers=ORIGIN)
    assert r.status_code == 405


def test_k6_open_pages_serve_cors_too():
    # /route et /agent/manifest sont gratuits : le mockup doit pouvoir
    # lire l'annuaire aussi, sinon la démo ne peut pas « consulter avant
    # d'agir » — la loi des trois premières lignes.
    r = client.get("/route?q=sha256", headers=ORIGIN)
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "*"
    r = client.get("/agent/manifest", headers=ORIGIN)
    assert r.headers.get("access-control-allow-origin") == "*"
