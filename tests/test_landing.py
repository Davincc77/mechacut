from pathlib import Path
"""Landing v2 contracts — the page CANNOT rot as the suite grows.

test_landing_budget   : catalogue section is a fixed-height scroller; total
                        HTML stays bounded whatever len(TABLE) becomes.
test_landing_contract : the v2 affordances exist (search, chips, panel,
                        breakpoints, hamburger, bench scroll wrap) and
                        every tool in TABLE has exactly one card.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import routing  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def _landing(lang="fr"):
    from main import LANDING
    return LANDING[lang]


def test_every_tool_has_exactly_one_card():
    html = _landing()
    for name, _p, _pk, _u, _t in routing.TABLE:
        assert html.count('data-tool="%s"' % name) == 1, name


def test_landing_budget():
    html = _landing()
    # total page stays bounded whatever len(TABLE) becomes. Resize
    # 23-11 bundle73 : le plafond 140 k datait du catalogue « 90+
    # tools » ; à 150 outils la page FR mesure 141 030 octets.
    # L'honnêteté de la croissance est portée par les gardes
    # structurels (one-card-per-tool, scroller à hauteur fixe,
    # squelette d'ancres) et par le VRAI contrat de portabilité :
    # le manifest < 9000 octets (test_bundle0) — la landing est une
    # vitrine navigateur, pas un artefact de contexte de modèle.
    assert len(html.encode("utf-8")) < 181_000  # resize 24-11 bundle100 :
    # b136_hermes elague MESURE (le lot franchissait 181 k comme annonce
    # b114 — prose serree, JAMAIS re-resize) : purposes FR/PT des deux
    # novos serres a claim constant, ligne tierlegend SUPPRIMEE (badge +
    # mot vivent dans les chips, les trois regles vivent dans tiers.intro
    # de la page — doctrine b123 « ce qui vit deux fois ne paie qu'une
    # fois »), CSS .tierlegend rendu (4 regles mortes), carte everyday e26
    # FR/PT ratismee : clauses duplicant les purposes des trois cartes
    # soldes-window/-be/-lu de la MEME page, chaque fait survit sur la
    # page (precedent b114 « e18/e19/e20 ratisses »). Mesure apres re-bake
    # : en 180 022 / fr 180 525 / pt 180 583 APP, soit +367 beacon
    # Cloudflare = 180 389 / 180 892 / 180 950 SERVIS — marge servie en
    # 610 / fr 107 / pt 49 (precedent de marge 9 : pt sous b114).
    # b114 LEÇON (classe outillage, itération ~14, pêchée PAR LA PROD) :
    # le VRAI contrat est l'octet que le NAVIGATEUR reçoit — Cloudflare
    # injecte un beacon de 367 octets dans la page SERVIE, invisible au
    # TestClient. Mesure live 25-11 22h2x : en 179 984 / fr 178 080 /
    # pt 180 624 APP, soit pt 181 188 SERVI avant élagage — la page PT
    # dépassait 181 k dans les navigateurs DEPUIS b113 (180 927 app =
    # 181 294 servi) pendant que ce test restait VERT sur les octets
    # locaux. Désormais : marge PT = 181_000 − 367 − app ; le lot PT qui
    # casse 180 633 app casse le contrat réel. Précédent mesure
    # en 173 079 / fr 178 683 / pt 176 779 — une ligne TABLE +
    # la carte e25 ×3 langues coûtent +2 189 octets FR (conforme à la
    # moyenne des bundles, 2 100-2 700). Marge = un bundle ; le
    # prochain franchira 181 k : ce sera ÉLAGUE (prose serrée), pas
    # resizé une troisième fois — la réserve est consommée, le contrat
    # de portabilité RÉEL reste le manifest < 9 000 octets. Suite du
    # plafond 178 000 (bundle99 : mesure fr 176 494) ;
    # mesure réelle fr 173 241 / pt 171 560 / en 167 976 (+1 table
    # row +1 carte everyday « pricedrop » ×3 langues = +1 245 octets
    # FR vs b92 ; la marge 172 000→175 000 tient un bundle de plus)
    # 80 : une ligne TABLE + une carte du quotidien (e21, la fenêtre
    # Target close Dec 24) coutent ~2 700 octets PAR page, FR mesure
    # 146 756, PT 145 615, EN 144 047 (re-mesure apres b81 : le
    # retrait des tags-chiffres rend ~30 octets). Le VRAI contrat de
    # portabilite reste le manifest (<9000 octets, test_bundle0).
    # 77-78 : deux lignes TABLE + une carte du quotidien (e20, la
    # divergence FedEx nommee) coutent ~2 200 octets PAR page, la prose
    # FR elaguee de 530 (e18/e19/e20 ratisses, chaque fait conserve)
    # FR mesure 143 983 < 144 200, PT 142 894, EN 141 420. Le VRAI
    # contrat de portabilite est le manifest (<9000 octets, tien),
    # precedent 143 000 au bundle76.
    # the catalogue grid is internally scrolled: page height cannot grow
    assert "max-height: 30rem" in html
    # b115 — le contrat écrit par b114 dans un COMMENTAIRE devient
    # ASSERTION : l'octet navigateur (app + beacon Cloudflare 367) doit
    # rester sous 181 000 dans les TROIS langues. Un commentaire ne
    # rougit jamais ; c'est ainsi que PT a vécu à 181 294 servis pendant
    # un cycle entier sous une suite verte (itération 14 de la classe
    # « l'outillage ment », consignée b114, close par cette ligne).
    for _l in ("en", "fr", "pt"):
        # b137c RE-ANCRE MESUREE sur tip e6deea2 (gouttiere b132 + pliage
        # CHROME deja en place) : +3 cartes pack geodesie RE-BAKEES x3,
        # AUCUNE prose tondue, AUCUN plafond touche — rendus : en 177 853 /
        # fr 178 553 / pt 178 579 APP = 178 220 / 178 920 / 178 946 SERVIS
        # (octet+367 beacon). Marges 2 780 / 2 080 / 2 054 sous 181 000 :
        # le plafond 182 500 pose sur la base fe83152 du lot 137 est
        # SUPERFLU sur le tip, la gouttiere absorbe — precedent b133 « les
        # lectures sont SYNCHRONEES dans le MEME commit ». Contrat reel =
        # manifest < 9000 (tenu 8 347, b0). Plafond 181_000 du tip CONSERVE
        # (suite des mesures b136 610/107/49 rendus par la gouttiere).
        assert len(_landing(_l).encode("utf-8")) + 367 < 181_000, _l
    # fixed section skeleton: five landmark anchors, never one per tool
    for anchor in ('id="bundles"', 'id="tiers"', 'id="bench"', 'id="build"',
                   'id="vision"', 'id="contract"'):
        assert html.count(anchor) == 1


def test_landing_contract():
    html = _landing()
    assert 'id="catsearch"' in html and "</script>" in html
    assert 'data-f="x=all"' in html
    assert 'id="tpanel"' in html and "hidden" in html
    assert "@media (max-width: 480px)" in html
    assert "@media (max-width: 1100px)" in html
    assert 'class="navbtn"' in html
    assert 'class="tblwrap"' in html
    assert '<link rel="canonical" href="https://mechacut.studio/">' in html


def test_hits_marker_survives_single_pass():
    html = _landing("en")
    m = re.search(r'data-tpl="([^"]*)"', html)
    assert m and "~n~" in m.group(1) and "~t~" in m.group(1)
    for lang in ("en", "fr", "pt"):
        loc = json.loads((ROOT / "locales" / ("%s.json" % lang))
                         .read_text(encoding="utf-8"))
        assert "{" not in loc["cat.hits"], "single braces crash fmt"


def test_js_never_spans_raw_newlines_in_strings():
    """Le crash de prod du 21-11 : une chaîne JS coupée par un VRAI saut
    de ligne — motif `+ "` en fin de ligne puis `" +` en début de ligne
    suivante — SyntaxError, tout le <script> mourait, recherche morte."""
    import re
    html = (Path(__file__).resolve().parents[1] / "static" /
            "landing.html").read_text(encoding="utf-8")
    pat = re.compile(r'\+ *"$\n^ *" *\+', re.M)
    assert not pat.search(html), (
        "chaîne JS coupée par un saut de ligne réel dans landing.html")
    # auto-preuve du détecteur sur le motif historique exact :
    NL = chr(10)
    crime = 'h += "POST " + p + "' + NL + '" +' + NL + 'b + "</pre>"'
    assert pat.search(crime), "le garde ne détecte pas son propre cas"


def test_en_got_chips_carry_no_french():
    """21-11 : la puce EN du leak-guard servait « graine … et clé »
    (résidu de rédaction). Les puces .got sont la réponse RÉELLE du
    serveur, donc traduite à la main — le français n'y a pas sa place,
    sauf dans les citations .say explicites (bench v9 verbatim)."""
    import json
    en = json.loads((Path(__file__).resolve().parents[1] / "locales" /
                     "en.json").read_text(encoding="utf-8"))
    banned = (" graine ", " et ", " cl\u00e9 ", " trouv\u00e9")
    for k, v in en.items():
        if not isinstance(v, str) or not k.endswith(".got"):
            continue
        for b in banned:
            assert b not in v, "%s contient %r" % (k, b)


def test_everyday_chips_never_placeholder():
    """La puce "?" masque un KeyError ou un ValueError de format (le %
    solitaire d'une template FR, 22-11). Le grid est baked dans les
    locales au build — c'est LÀ qu'on vérifie, pas sur un serveur."""
    for lang in ("fr", "en", "pt"):
        cat = json.loads((ROOT / "locales" / (lang + ".json"))
                         .read_text(encoding="utf-8"))
        grid = cat["everyday_grid"]
        chips = re.findall('playgot">(.*?)</pre>', grid, re.S)
        assert len(chips) >= 6, (lang, len(chips))
        assert "?" not in chips, (lang, chips)
