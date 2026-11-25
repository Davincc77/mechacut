#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""route_radar — la fonction de recherche de douleurs COTE ROUTEUR et
ADAPTATEUR, pour la boucle de croissance. Deterministe, lecture seule,
jamais de secret echoe.

Deux lentilles :
  1. RADAR (defaut) — sonde le routeur de PROD avec un corpus de
     formulations reelles (x3 langues, variantes d'accents et de
     casse, leurres « ne doit PAS matcher ») via GET /route et, si le
     manifest les declare, POST /api/v1/router/plan + /apply.
     Classes de douleur pechees : NO_MATCH (douleur = requete morte),
     WRONG (douleur = mauvaise aiguille, pire que le silence),
     OVERMATCH (douleur = le serveur s'invente une extraction sur une
     phrase sans donnees), REGRESSION (marchait hier, casse
     aujourd'hui).
  2. CATALOG (--catalog) — le piege d'ADAPTATEUR de l'incident V23 :
     un id MODELE liste n'est pas un id invocable. Liste /v1/models
     (Nous), sonde un echantillon en un appel 1-token, signale les
     MIRAGES (liste 200, appel 404). C'est la douleur des gens qui
     cablent des annuaires a l'aveugle — la notre pareil.

Sorties : docs/RADAR/scan-<ts>.json + latest.json + diff avec le scan
precedent (nouvelles douleurs / gueris / regresses) ; resume markdown
imprimé pour coller dans DEMAND-QUEUE.md. Le script ne decide rien :
il mesure, la boucle choisit.
"""
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

APP = "https://mechacut.studio"
# Règle de cadence (bundle 72) : le scan 06:22 du 23-nov s'est
# auto-infligé un plan-http-429 — 0,3 s de sommeil = 33 req/min,
# au-dessus de NOTRE propre règle 25/min enseignée à l'instance qui
# consomme. La lentille ferme sa douleur : toute sonde de PROD attend
# APP_MIN_GAP.
APP_MIN_GAP = 2.6
UA = ("mechacut-radar/1.0 (growth-loop; contact: "
      "github.com/Davincc77/mechacut)")
NOUS = "https://inference-api.nousresearch.com/v1"
RADAR_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "docs", "RADAR")
# bundle 99 (S) — continuite du miroir --catalog entre scans impayes.
CATALOG_FILE = os.path.join(RADAR_DIR, "latest_catalog.json")

# ---------------- lentille 1 : le corpus. Chaque cas = (texte,
# attente). attente : nom de fiche/route cherche dans le top, ou
# None = « ne doit RIEN prescrire » (leurre). Les variantes
# accent/casse TESTENT l'incident consigne v0.84.0
# (accents+egalite=NO-MATCH).
CASES = [
    # chaîne, x3 langues + variantes — la zone 0/28 est le territory
    ("magasin 435 articles, 35 vendus le matin, 40 % du reste "
     "l'après-midi, combien restent", "shop"),
    ("magasin 435 articles, 35 vendus le matin, 40 % du RESTE "
     "l'après-midi, combien restent", "shop"),
    ("435 articles, 35 le matin, 40% Du Reste l'apres-midi combien "
     "restent", "shop"),
    ("shop had 435 items, 35 sold in the morning, 40% of the rest "
     "in the afternoon, how many remain", "shop"),
    ("loja tinha 435, vendeu 35 de manha, 40% do resto a tarde, "
     "quantos restam", "shop"),
    ("partage 3829 : le premier recoit 2/5, le second 1/6 du reste",
     "partage"),
    ("split 3829: first gets 2/5, second 1/6 of the rest",
     "partage"),
    ("-25 % puis -20 % sur 81,90 — prix final", "soldes2"),
    # RE-DÉCLARÉE 23-11 cycle 14h56 : la want « soldes » n'a jamais
    # désigné un outil du catalogue — l'artefact comparatif vit chez
    # money_discount ; la want dit maintenant le nom vrai.
    # RE-DÉCLARÉE 24-11 b103 : « soldes » est DÉSONNAIS un sous-mot
    # de shop_soldes_window — la ligne-prix doit nommer sa fiche.
    # « soldes2 » tranche les DEUX surfaces : sous-mot de
    # recipe_soldes2 (route) et fiche exacte du plan ; ma première
    # re-déclaration « recipe_soldes » était juste pour la route et
    # fausse au plan — douleur pêchée par mon propre garde, guérie
    # dans le corpus, pas dans le routeur.
    ("is 30% off plus another 20% the same as 50% off on 89.90",
     "discount"),
    # les deux outils du cycle — garde de leur propre douleur
    ("is retrying this timeout a fourth time rational or am i stuck",
     "retrybudget"),
    ("this strikethrough says minus 30 percent — is it legal under "
     "the omnibus rule", "discount_audit"),
    ("le prix barré annonce -30 pour cent — est-ce licite face à "
     "la règle des trente jours ?", "discount_audit"),
    ("a loja anuncia 30% sobre o preço riscado — é ilegal pela "
     "regra dos 30 dias?", "discount_audit"),
    # quotidien — le noyau qui compte
    ("mon vol est arrive avec 3 h 20 de retard le 1er nov. 2027, "
     "que me doit la table EU", "flight"),
    ("my bag is 40x18x30, flight 2027-11-02 — free under the seat",
     "baggage"),
    ("avant d'ouvrir ce CSV dans Excel, quelles colonnes perdent "
     "leurs zeros", "excel"),
    ("openpyxl read 1000000 but the human saw $1,000", "display"),
    ("tarif A 0,25 €/kWh + 0,60 par jour, B 0,27 + 0,45 — à partir "
     "de combien de kWh A gagne", "crossover"),
    # bundle 95 — l'ORTHGRAPHE ACCENTUÉE, variante que le corpus ne
    # testait JAMAIS (ses « variantes d'accents » étaient déaccentuées :
    # l'angle mort du test était le test). Sept dictées MESURÉES en
    # prod le 23-nov sous v1.16.0 (WRONG/NO_MATCH avant le pli T7).
    ("c'est quoi un prix barré légal", "discount_audit"),
    ("prix barré légal plus bas à 80", "discount_audit"),
    ("le prix barré est-il vrai", "discount_audit"),
    ("la promotion est-elle licite", "discount_audit"),
    ("recouvrement facture impayé", "aging"),
    ("preço riscado é legal", "discount_audit"),
    ("is the strikethrough was price legal under omnibus",
     "discount_audit"),
    # bundle 96 — le pilier 3 du trio boutique. Douleur : la
    # requête HUMaine « qui me rend la différence » était volée par
    # unitprice/discount-audit (les mots « prix » et « 80 » sont
    # déjà occupés) ; ces lignes ferment la découvrabilité du nouvel
    # outil ET gardent la frontière avec return-deadline.
    ("j'ai acheté 100 à la Fnac, passé à 80, qui me rembourse la "
     "différence", "pricedrop"),
    ("i paid 100 at best buy and the price dropped to 80 last week "
     "— who owes me the difference", "pricedrop"),
    ("comprei por 100 na fnac e caiu para 80, quem me devolve a "
     "diferenca", "pricedrop"),
    ("PRIX BAISSE APRES ACHAT REMBOURSEMENT DIFFÉRENCE fnac",
     "pricedrop"),
    ("can I still return the TV I bought at target, until when",
     "return_deadline"),
    # leurres : aucune extraction fermee n'est licite — le routeur
    # doit REFUSER par le nom, pas inventer.
    ("raconte-moi une blague sur les bases de donnees", None),
    ("je ne sais pas encore ce que je veux calculer, parlons-en",
     None),
    ("435 articles et puis la vie, le temps, les gens", None),
    ("raconte-moi une blague sur les soldes légaux", None),
    # bundle 97 — découvrabilité de l'agent-family NEUVE : la
    # question de SURFACE (« a-t-il changé ? ») et celle du JUGE
    # (« va-t-il rejeter ? ») ne doivent jamais se croiser ; le
    # leurre « empreintes digitales » protège le mot FR « empreinte »
    # — un leurre qui route = une fausse promesse (OVERMATCH).
    ("le listing d'outils MCP a changé depuis mon relevé épinglé",
     "mcpsurface"),
    ("did the MCP tools list change since I pinned it — fingerprints",
     "mcpsurface"),
    ("a lista de ferramentas MCP mudou desde a última leitura",
     "mcpsurface"),
    ("LISTING OUTILS MCP A CHANGÉ DÉRIVE EMPREINTE", "mcpsurface"),
    ("mon tools/list a un inputSchema vide — le client va-t-il le "
     "rejeter", "mcpaudit"),
    ("fais-moi une blague sur les empreintes digitales", None),
    # EN : « fingerprints » EST un mot du NOM ssh_fingerprint
    # (poids 4, pluriel plié) — la blague anglaise route, mesuré CE
    # cycle. Ce n'est PAS un leurre libre : douleur OVERMATCH de la
    # famille ssh, consignée à la file, non encodée ici comme « doit
    # mourir » tant que le routeur ne plie pas les formes
    # « tell/joke about » comme il plie « blague ».
    # bundle 98 — découvrabilité FR des lignes officielles neuves
    # (fnac/darty 15-jan, boulanger 31-jan fenêtre oct30→déc27,
    # dell later-of, apple direct 8-jan REÇUS) + la frontière :
    # « qui me doit la différence » reste à pricedrop, et la
    # blague FR sur les retours meurt (stop-formage b95) — un
    # leurre qui route = une promesse fausse.
    ("jusqu'où retourner le cadeau de Noël acheté à la Fnac le 20 "
     "décembre", "return_deadline"),
    ("puis-je encore retourner le téléviseur acheté chez Darty "
     "avant Noël", "return_deadline"),
    ("le PC Dell reçu le 20 décembre, jusqu'à quand puis-je le "
     "renvoyer", "return_deadline"),
    ("jusqu'au 8 janvier inclus le cadeau Apple reçu à Noël",
     "return_deadline"),
    ("can I still return the Apple gift received on December 21",
     "return_deadline"),
    ("my Fnac Christmas purchase return deadline january",
     "return_deadline"),
    ("prazo de devolução do presente de Natal comprado na Fnac em "
     "dezembro", "return_deadline"),
    ("boulanger retour prolongé 31 janvier achat 27 décembre",
     "return_deadline"),
    ("raconte-moi une blague sur les retours de Noël", None),
    # b98 — la FORME meurt, pas le poids : la blague EN qui était
    # une douleur OVERMATCH (file n°7, ssh_fingerprint, pêchée b97)
    # est encodée « doit mourir » DÈS QUE le fix existe — règle de
    # grammaire fermée « blague|joke|piada », zéro LM.
    ("tell me a joke about fingerprints", None),
    ("me faz uma piada sobre prazos de devolução", None),
    ("le meilleur prix Fnac me doit la différence après la baisse",
     "pricedrop"),
    # bundle 99 — découvrabilité des horloges LÉGALES + la frontière
    # double qu'elles ouvrent : le retour COMMERCIAL ne doit pas
    # voler l'horloge légale, et « retourner ce qui ne plaît pas »
    # (aucun défaut) ne doit PAS basculer sur la garantie — un
    # leurre qui route = une promesse fausse. La question de
    # VALEUR (« faut-il payer ») ne prescrit aucune date : None.
    # Le leurre blague × garantie teste la forme fermée b98 sur la
    # FAMILLE neuve, pas seulement sur les retours.
    ("mon cadeau est en panne le 16 janvier, la garantie légale "
     "jusqu'à quand", "legal_guarantee"),
    ("vices cachés lave-linge acheté à Noël délai pour agir",
     "legal_guarantee"),
    ("the tv I got as a gift in December broke in March, statutory "
     "rights how long", "legal_guarantee"),
    ("faulty present consumer rights act six months burden scotland",
     "legal_guarantee"),
    ("garantie de conformité 24 mois présomption occasion",
     "legal_guarantee"),
    ("presente com defeito depois do prazo da troca garantia legal",
     "legal_guarantee"),
    ("je veux retourner le cadeau de Noël qui ne me plaît pas, "
     "pas de panne", "return_deadline"),
    ("le magasin dit que la garantie du constructeur est finie, "
     "et la loi", "legal_guarantee"),
    ("faut-il payer la garantie prolongée à 40 euros pour le "
     "sèche-linge", None),
    ("tell me a joke about the legal guarantee", None),
    # b100 — keep-records-uk : la famille des horloges de RETENTION,
    # et le veto de juridiction NOMMÉE (classe b98 portée à l'outil
    # qui se nomme) : une requête qui dit « France » ou « brasileiras »
    # ne doit RIEN promettre du UK-only ; la requête honnête passe par
    # le token UK (HMRC / limited company / Reino Unido). La bordure
    # garantie-vs-papier : « garder la facture d'un objet encore
    # sous garantie » EST une question de dossier — keep_records,
    # avec la garantie en second attendu (top-2, pas top-1).
    ("can I shred this year's HMRC invoices now", "money_keep_records_uk"),
    ("when can I destroy my limited company accounting records",
     "money_keep_records_uk"),
    ("do I need to keep a VAT invoice that describes a future payment",
     "money_keep_records_uk"),
    ("puis-je jeter mes factures HMRC de 2020", "money_keep_records_uk"),
    ("quand détruire la comptabilité d'une private company UK",
     "money_keep_records_uk"),
    ("por quanto tempo guardar documentos da HMRC no Reino Unido",
     "money_keep_records_uk"),
    ("my gift is still under warranty — how long must I keep the "
     "invoice", "money_keep_records_uk"),
    ("combien de temps garder mes factures en France", None),
    ("as notas fiscais brasileiras quanto tempo guardar", None),
    ("what is HMRC", None),
    # bundle 101 — découvrabilité de la context-tax (douleur DEV,
    # douze mesures externes nov-2026) x3 langues + le verbatim du
    # fil dplouffe + deux FRONTIÈRES : « tokens in this text » reste
    # à text_count (compter n'est pas facturer), et la blague sur le
    # coût des tokens meurt — la forme fermée b98 gouverne nos mots.
    ("how many tokens does this mcp server tool list cost my agent "
     "every turn", "agent_contexttax"),
    ("combien de tokens coûte la liste d'outils de ce serveur mcp "
     "à chaque tour", "agent_contexttax"),
    ("quantos tokens a lista de ferramentas desse servidor mcp "
     "custa a cada turno", "agent_contexttax"),
    ("an eBay MCP server spends 40% of my context window on its "
     "tool list", "agent_contexttax"),
    ("mon tools/list fait 500ko combien de tokens par tour ca me "
     "coute", "agent_contexttax"),
    ("how many tokens are in this text", "text_count"),
    ("raconte-moi une blague sur le coût des tokens", None),
    # bundle 104 — le PRIX DE L'UPDATE : trois langues x want
    # agent_costdiff + le verbatim testdino + DEUX FRONTIÈRES de
    # famille payées au test : « what changed » sans vocabulaire de
    # prix reste chez mcp-surface (digest, pas facture), et le
    # single-listing « combien coûte » reste chez context-tax. La
    # blague sur le surcoût meurt par la forme b98.
    ("what did the mcp update cost my tool list in extra tokens",
     "agent_costdiff"),
    ("quel surcoût de tokens la nouvelle version du serveur mcp a "
     "ajouté à ma liste d'outils", "agent_costdiff"),
    ("quanto a nova versão do meu servidor mcp custou a mais em "
     "tokens na lista de ferramentas", "agent_costdiff"),
    ("the update of my mcp server grew the tool list by 13k tokens — "
     "what is the delta per tool", "agent_costdiff"),
    ("what changed in my mcp tool list since the reading i pinned",
     "agent_mcpsurface"),
    ("blague sur le prix de la nouvelle version de la liste "
     "d'outils", None),
    # b102 — la douleur que /shop/gift-voucher répare, x3 langues
    # (verbatim RTÉ 20-nov : « vouchers given from last Christmas »)
    # + les vetoes de juridiction NOMMÉE (b102) et la blague (b98).
    ("the gift voucher I got for last Christmas expired, shop says "
     "too late, bought in Dublin 2024", "shop_gift_voucher"),
    ("gift card expired but I heard five years is the law",
     "shop_gift_voucher"),
    ("ma carte cadeau a expiré, le magasin dit que c'est mort — "
     "j'ai acheté à Dublin", "shop_gift_voucher"),
    ("bon cadeau périmé en France, y a-t-il une durée légale ?",
     "shop_gift_voucher"),
    ("meu cartão-presente irlandês venceu, a loja diz que acabou",
     "shop_gift_voucher"),
    ("vale-presente da JD Sports expirou, comprei em Dublin",
     "shop_gift_voucher"),
    ("meu vale-presente brasileiro expirou", None),
    ("gift voucher expired in London", None),
    ("mon voucher a expiré à Londres", None),
    ("mon bon d'achat a expiré en Irlande du Nord", None),
    ("tell me a joke about expired gift vouchers", None),
    ("raconte-moi une blague sur les cartes cadeaux", None),
    # frontière jurée : le cadeau-RETOUR et le prix-payé-en-voucher
    # ne sont PAS la validité du voucher — aiguilles des frères.
    ("can I still return the Christmas gift I bought at fnac",
     "shop_return_deadline"),
    ("the price dropped after I paid, they offer a gift card "
     "refund, who owes me", "shop_pricedrop_refund"),
    # CLASSE b103 — /shop/soldes-window : la douleur « le calendrier
    # se trompe d'une semaine sur 2027 » (6 janv.->2 févr. vs « 9
    # février » pêché à midi sur lecalendrier). Aiguilles x3 langues
    # + les dérogations elles-mêmes, car c'est ELLES la valeur.
    # Leurre et frontière : la Belgique/Luxembourg/Portugal nomment
    # un AUTRE calendrier — veto b103, RIEN ne doit être prescrit.
    ("quand commencent les soldes d'hiver 2027",
     "shop_soldes_window"),
    ("les soldes d'été 2027 débutent-ils le 23 ou le 30 juin",
     "shop_soldes_window"),
    ("soldes lorraine 2027 ouvré samedi 2 ou lundi 4",
     "shop_soldes_window"),
    ("prolongation des soldes d'été 2026 canicule cinq semaines",
     "shop_soldes_window"),
    ("soldes d'hiver 2021 reportés au 20 janvier six semaines",
     "shop_soldes_window"),
    ("when do the french winter sales 2027 start january 6 or 13",
     "shop_soldes_window"),
    ("sales dates france 2027 summer start date official",
     "shop_soldes_window"),
    ("quando começam os saldos de inverno 2027 na frança",
     "shop_soldes_window"),
    ("data dos saldos de verão na frança 2027",
     "shop_soldes_window"),
    # CLASSE b105 — la Belgique a SON outil : la ligne b103
    # (« rien ne doit être prescrit ») devient une want positive,
    # la douleur fermée PAR LE LOT. Aiguilles x3 langues + la
    # clause vécue + l'attente à la borne du lendemain + le report
    # 2021. Gardes : « france » nominatif reste chez window ;
    # luxembourg/suisse/joke continuent de ne RIEN prescrire.
    ("quand commencent les soldes en belgique", "shop_soldes_be"),
    ("soldes belgique 2027 samedi 2 ou dimanche 3 janvier",
     "shop_soldes_be"),
    ("période d'attente soldes belgique 2 décembre 1er janvier",
     "shop_soldes_be"),
    ("winter sales belgium 2027 january 2 sunday clause",
     "shop_soldes_be"),
    ("belgian summer sales june 30 standstill period",
     "shop_soldes_be"),
    ("saldos na bélgica 2027 janeiro período de espera",
     "shop_soldes_be"),
    ("data dos saldos de inverno na belgica 2027",
     "shop_soldes_be"),
    ("wanneer zijn de solden 2027 in belgië", "shop_soldes_be"),
    ("report des soldes belges 4 janvier 2021 prolongés quinze février",
     "shop_soldes_be"),
    ("les soldes d'hiver 2027 en france c'est le 6 ou le 13",
     "shop_soldes_window"),
    ("quando começam os saldos em portugal", None),
    # CLASSE b110 — le leurre vendu par b108 (« les soldes d'hiver au
    # luxembourg ») devient une AIGUILLE : la table LU est construite,
    # le relai des sœurs a sa destination. Aiguilles x3 langues du lot
    # + la douleur PT pêchée par la sonde (« datas » volé par chart).
    ("les soldes d'hiver au luxembourg 2027", "shop_soldes_lu"),
    ("soldes luxembourg janvier 2027", "shop_soldes_lu"),
    ("quand commencent les soldes au luxembourg", "shop_soldes_lu"),
    ("luxembourg sale dates winter 2027", "shop_soldes_lu"),
    ("saldos luxemburgo datas 2027", "shop_soldes_lu"),
    ("reglement grand-ducal soldes 2027 luxembourg", "shop_soldes_lu"),
    ("tell me a joke about the french sales calendar", None),
    ("blague sur le calendrier des soldes belges", None),
    # frontière jurée : le MONNAIE-solde reste chez les frères. La
    # première version de cette ligne (« mon solde de carte cadeau
    # remboursement ») était une PIÈCE À PILE : pricedrop et
    # gift-voucher tie-raient à 9/9 et l'ordre TABLE décidait le
    # top1 — une phrase ambiguë n'est pas un test à want unique, la
    # douleur était dans mon corpus, pas dans le routeur. La ligne
    # nomme maintenant le domaine : expiration + Dublin = voucher.
    ("le solde restant de ma carte cadeau expirée — Dublin, remboursement",
     "shop_gift_voucher"),
    # CLASSE b106 — « quoi débrancher » : le lot DEV ferme sa douleur
    # de routeur AVANT push (aiguilles x3 langues, verbatim des fils
    # r/ClaudeCode et r/mcp du soir). Gardes testés : le COMBIEN reste
    # chez context-tax (b101), l'ÉCART chez cost-diff (b104), le
    # CHANGÉ chez mcp-surface, le rationnel-de-relance chez
    # retry-budget ; la blague de trim et l'électroménager débranché
    # ne prescrivent RIEN (forme b98 + phrase sans outil ni budget).
    ("which MCP tools should I disconnect to fit my context budget",
     "agent_tooltrim"),
    ("trop d outils MCP branchés lesquels couper pour tenir le budget",
     "agent_tooltrim"),
    ("quais ferramentas desligar para caber no orcamento",
     "agent_tooltrim"),
    ("115 tools 43000 tokens what to trim before disconnecting",
     "agent_tooltrim"),
    ("is my tool list over budget on a 60k local window",
     "agent_tooltrim"),
    ("je veux débrancher mon lave-vaisselle", None),
    ("tell me a joke about trimming hedges", None),
    # CLASSE b111 — « deux outils n'en font qu'un sans rien dire » :
    # la douleur DEV rang 1, rejouée VERBATIM des issues closes
    # (vscode#338895 « silently dropped », foundry#723 « wrong tool »,
    # gemini-cli#28970, CopilotKit#7495, openworker#746). Aiguilles x3
    # langues + garde de fratrie : le COMBIEN reste chez context-tax,
    # le QUOI COUPER chez tool-trim, le CHANGÉ chez mcp-surface, le
    # REJETÉ chez mcp-audit. Leurre en forme b98 : sans donnée de
    # noms, rien ne doit être prescrit.
    ("which tools silently disappeared after adding a second mcp "
     "server", "agent_tooloverlap"),
    ("tool names collide after truncation 64 characters",
     "agent_tooloverlap"),
    ("mcp tool prefix same first 64 characters wrong tool",
     "agent_tooloverlap"),
    ("deux serveurs meme nom d outil quel outil a disparu "
     "silencieusement vscode", "agent_tooloverlap"),
    ("collision de noms outils troncation 64 caracteres",
     "agent_tooloverlap"),
    ("quais ferramentas sumiram sem erro colisao de nomes mcp",
     "agent_tooloverlap"),
    # CLASSE b112 — « les quatre lectures d'un Net 30 » : la douleur
    # HUMAIN rang 1, rejouée des sources lues (§ 193 BGB verbatim,
    # BFDA 1971 s.1(4), DGCCRF deux méthodes, r/Contractor 1i24hj1,
    # Bluevine vs ResolvePay qui se contredisent). Aiguilles x3
    # langues + garde fratrie : aging buckete des dates CONNUES,
    # date_deemed rend la réception réputée, holidays liste des jours
    # sans terme — aucun ne rend la vraie échéance et ses lectures.
    ("facture net 30 tombe un samedi quelle est la vraie échéance",
     "invoice_payment_due"),
    ("45 jours fin de mois comment calculer la date de paiement",
     "invoice_payment_due"),
    ("rechnung netto 30 fällig am samstag zahlungsziel werktag",
     "invoice_payment_due"),
    ("invoice dated friday net 30 when is it legally due germany",
     "invoice_payment_due"),
    ("does net 30 count weekends or business days payment terms",
     "invoice_payment_due"),
    ("fatura net 30 vence no feriado qual a data real de pagamento",
     "invoice_payment_due"),
    ("combien de jours ouvrables entre le 5 et le 20 mars 2026",
     "date_calc"),  # PORTE-FAUX CONSIGNÉ : hors mes tags, cette
    # phrase est SILENCIEUSE (score sous le seuil) — elle n'a jamais
    # été à date_calc. La ligne reste au corpus comme GUERRE DE
    # L'OVERMATCH : si un jour un outil répond « combien de jours
    # entre deux dates », c'est ici qu'elle migrera. Tant que mon
    # outil ne compte pas les plages, il ne doit PAS la gagner.
    ("aging overdue unpaid receivables buckets relance client",
     "money_aging"),
    ("jours fériés 2027 Allemagne liste complète",
     "schedule_holidays"),
    ("est-ce que tu trouves que ce tableau est équilibré "
     "sans chiffres", None),  # leurre sans DONNÉES : aucune date ne
    # doit être prescrite — classe b98 ; l'ancien brouillon « ask a
    # client to pay faster » répondait chez intent_check (verbe
    # légitime ailleurs) — consigné, remplacé avant push.
    ("raconte-moi une blague sur mes outils qui se ressemblent", None),

    # CLASSE b107 — « colis reçu mardi, jusqu'à quand je me rétracte » :
    # la douleur HUMAINE verbatim (BEE SECURE LU, 24-11) ferme ses
    # aiguilles x3 langues AVANT que le lot ne se dise livré. Gardes :
    # le retour ENSEIGNE reste chez return-deadline, la garantie chez
    # legal-guarantee ; la rétractation IMMOBILIÈRE (autre loi, CCH
    # L312-12, 10 jours — pas notre section 6) et la blague ne
    # prescrivent RIEN.
    ("colis reçu mardi — jusqu'à quelle date exacte puis-je me "
     "rétracter, samedi et jours fériés comptés", "shop_withdrawal"),
    ("j'ai commandé en ligne, changement d'avis : 14 jours ou pas ?",
     "shop_withdrawal"),
    ("parcel arrived tuesday — until when can I withdraw from the "
     "online order", "shop_withdrawal"),
    ("até quando posso desistir da compra — encomenda recebida terça",
     "shop_withdrawal"),
    ("rétractation d'un achat immobilier signé chez le notaire", None),
    ("raconte-moi une blague sur la rétractation", None),
    ("piada sobre desligar ferramentas", None),
    # CLASSE b108 — « mêmes mots, autres grammaires » : LU et BE sont
    # des lois rejouées (L. 221-3 + L. 222-9 ; VI.47-53 + C. civ. I.7),
    # elles routent et DATENT. Le leurre vendu la veille
    # (« soldes d'hiver au luxembourg ») est VIVANT depuis b110 —
    # converti en aiguille plus haut ; le verbe rétractation seul ne
    # doit jamais faire vivre la FENÊTRE soldes (autres mots, autre
    # table), la frontière reste jouée par les vetos.
    ("colis reçu samedi au luxembourg, jusqu'à quand puis-je me "
     "rétracter", "shop_withdrawal"),
    ("achat en ligne belgique délai rétractation après réception",
     "shop_withdrawal"),
    ("withdrawal luxembourg parcel arrived saturday deadline",
     "shop_withdrawal"),
    ("retratação belgique prazo de desistir depois da entrega",
     "shop_withdrawal"),
    # leurre de juridiction, version b108 : l'Allemagne nommée dans
    # sa propre langue d'adjectif tue la ligne (trou « alemanh » sans
    # « allemand » corrigé ce cycle, racines au veto)
    ("rétractation colis allemagne 14 jours", None),
    # CLASSE b109 — les DEUX OVERMATCH pêchés (06h13/07h44) sont
    # FERMÉS par le veto droit-fenêtre : ils voyagent désormais en
    # L leurres — un leurre qui meurt vide est une promesse tenue.
    # brésil : question de DROIT (CDC art. 49, 7 jours, non rejoué
    # chez nous) qui routait la fenêtre enseigne US — plus rien.
    ("retour brésil 7 jours arrependimento prazo", None),
    # idem EN : « withdrawal germany ... » ne doit rien prescrire —
    # l'Allemagne est hors des deux tables américaines.
    ("withdrawal germany online order deadline", None),
    # DOULEURS DU LOT b109 — aiguilles x3 langues : « mon id est
    # listée mais meurt en appel batch / mon embedding répond 400
    # en chat » doit ROUTER agent_modelid (la porte nommée est le
    # produit). Corpus formulé depuis les issues citées dans le
    # module (openclaw #20522, litellm #37271, V23, HN 49796140).
    ("model id not found 404 batch litellm", "agent_modelid"),
    ("embedding model returns error in chat gateway", "agent_modelid"),
    ("id modelo introuvable 404 appel batch openrouter",
     "agent_modelid"),
    ("modelo listado retorna erro no chat embeddings gateway",
     "agent_modelid"),
    # leurres de la classe : un vrai json_map batch ne doit PAS
    # partir vers l'audit d'ids, et un vrai retour US nomme son
    # marché sans mot étranger.
    ("map every item of an array batch style", "json_map"),
    ("walmart return deadline january 31", "shop_return_deadline"),
    ("walmart return indiana receipt", "shop_return_deadline"),
]


def get(url, params=None, data=None, headers=None):
    # b112 FIX 429 (douleur d'outillage pêchée par le scan de clôture
    # LUI-MÊME : le balayage golden tournait en parallèle, la sonde a
    # lu des 429 comme des NO_MATCH — six fausses douleurs dont deux
    # de MES aiguilles, « NOUVELLE » sur des phrases vertes en
    # conditions calmes. Le 429 n'est pas une réponse du routeur,
    # c'est la porte de la salle d'attente : on attend, on ne
    # consigne pas. Retry poli, 4 tentatives, 6 s — un 429 persistant
    # remonte ENCORE comme status distinct, jamais comme NO_MATCH.
    if params:
        url += "?" + "&".join(
            "%s=%s" % (k, urllib.parse.quote(str(v)))
            for k, v in params.items())
    import time as _t
    last = None
    for attempt in range(4):
        req = urllib.request.Request(url, data=data, headers=headers or {})
        req.add_header("User-Agent", UA)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            try:
                body = json.loads(e.read().decode())
            except Exception:
                body = {}
            if e.code == 429 and attempt < 3:
                _t.sleep(6)
                continue
            return e.code, body
        except Exception as e:
            last = e
            if attempt < 3:
                _t.sleep(6)
                continue
            return 0, {"error": "transport:%s" % type(last).__name__}
    return 0, {"error": "retry-loop-exhausted"}  # defensif — chaque
    # iteration retourne ; la ligne est pour le lectrice statique


import urllib.parse  # noqa: E402  (après get pour lisibilité)


def probe_router(manifest):
    st, info = get(APP + "/")
    has_plan = "/api/v1/router/plan" in (info.get("endpoints") or {})
    rows = []
    for text, want in CASES:
        rec = {"text": text[:80], "want": want}
        st, body = get(APP + "/route", {"q": text, "top": "5"})
        tools = body.get("tools") or []
        names = [t.get("tool", "") for t in tools]
        top_score = tools[0].get("score", 0) if tools else 0
        top1 = names[0] if names else ""
        rec["route_top"] = top1
        rec["score"] = top_score
        # un leurre est « bien traité » si RIEN ne franchit le seuil
        # de confiance (5) : le routeur ne doit pas inventer une
        # destination. En dessous, c'est un refus doux ; au-dessus,
        # OVERMATCH. Les scores des vraies douleurs (shop/prix) sont
        # >=9 sur ce corpus.
        # Bundle 72 : le verdict s'appuie sur la LISTE RENVOYÉE, plus
        # sur un score-magasin (l'ancien « <= 5 » datait d'avant T6 :
        # sous le plancher 4 publié, un leurre à 4-5 franchissait la
        # porte comme « leurre-ok »). Un refus = liste vide (ou
        # elsewhere) ; c'est la garantie T6 elle-même, pas un seuil
        # dupliqué dans l'outillage.
        if want is None:
            rec["verdict"] = ("leurre-ok" if (not tools or
                                              body.get("elsewhere"))
                              else "OVERMATCH")
        else:
            hit = any(want.lower() in n.lower() for n in names[:3])
            # TOP1_WRONG (douleur pêchée 14h54) : le bon outil est
            # DANS la liste mais le mauvais est EN TÊTE — l'inversion
            # que la règle top-5 masquait (« -25 % puis -20 % »
            # volé top-1 par check_target via « prix final »).
            rec["verdict"] = ("TOP1_WRONG" if (
                hit and names and want.lower()
                not in names[0].lower()) else
                "ok" if hit else
                ("NO_MATCH" if not tools
                 else "WRONG"))
        rows.append(rec)
        time.sleep(APP_MIN_GAP)
    if has_plan:
        for text, want in CASES[:8]:
            st, body = get(APP + "/api/v1/router/plan",
                           data=json.dumps({"texte": text}).encode(),
                           headers={"Content-Type":
                                    "application/json"})
            presc = body.get("prescription")
            got = (presc.get("fiche") if isinstance(presc, dict)
                   else None) or body.get("fiche") or ""
            rec = {"text": text[:80], "want": want, "via": "plan",
                   "verdict": ("plan-http-%d" % st if st != 200
                               else "ok" if (want is None and
                                             not got) or (want and
                                             want.lower() in
                                             str(got).lower())
                               else "plan-WRONG")}
            rows.append(rec)
            time.sleep(APP_MIN_GAP)
    return rows


# ---------------- lentille 2 : mirages de catalogue.
def probe_catalog(sample=12):
    def key():
        p = os.path.expanduser("~/.hermes/auth.json")
        try:
            d = json.load(open(p))["providers"]["nous"]
            return d.get("agent_key") or d["access_token"]
        except Exception:
            return None
    k = key()
    if not k:
        return [{"verdict": "catalog-skipped", "text": "pas de cle"}]
    # Bundle 72 : la lecture passe par get() comme le reste — un seul
    # chemin réseau, et le test peut rejouer la sonde hors-ligne.
    st, listing = get(NOUS + "/models",
                      headers={"Authorization": "Bearer " + k})
    try:
        ids = sorted(m["id"] for m in listing["data"])
    except Exception:
        return [{"verdict": "catalog-error",
                 "text": "http-%d" % st}]
    step = max(1, len(ids) // sample)
    picked = ids[::step][:sample]
    out = []
    for mid in picked:
        # Bundle 72 — le verdict doit TYPER l'endpoint. Mesuré 06:22 :
        # google/gemini-embedding-001:batch, appelé en /chat par
        # l'ancienne sonde, renvoyait http-400 — le catalogue mélange
        # les TYPES (chat/embeddings) sans le dire dans l'id ; c'est
        # le piège V23 sous son second jour (listed ≠ invocable ICI).
        embed = "embed" in mid.lower()
        if embed:
            path, probe = "/embeddings", {"model": mid, "input": "OK"}
        else:
            path, probe = "/chat/completions", {
                "model": mid, "stream": False, "max_tokens": 2,
                "messages": [{"role": "user", "content": "OK"}]}
        st, _ = get(NOUS + path, data=json.dumps(probe).encode(),
                    headers={
                        "Authorization": "Bearer " + k,
                        "Content-Type": "application/json"})
        out.append({"text": mid, "want": "embed" if embed else None,
                    "verdict": "ok" if st == 200 else
                    ("MIRAGE" if st == 404 else "http-%d" % st)})
        time.sleep(1.0)
    return out


def main():
    argv = sys.argv[1:]
    os.makedirs(RADAR_DIR, exist_ok=True)
    rows = probe_router(None)
    # --- douleur d'OUTIL n°5/8, fix bundle 99 (S) : un scan sans
    # --catalog ecrasait latest.json SANS les lignes catalogue, donc
    # le miroir paye (1 cycle sur 4) perdait sa continuite : le
    # paiement suivant re-decouvrait ses mirages comme « NOUVELLE »
    # au lieu de les suivre. Le miroir vit desormais dans
    # latest_catalog.json, ecrit AU SEUL scan paye, et toute la
    # vue latest.json le charrie jusqu'au prochain paiement —
    # marque via=catalog-mirror, jamais compte dans les douleurs du
    # scan courant.
    mirror = []
    if os.path.exists(CATALOG_FILE):
        try:
            mirror = json.load(open(CATALOG_FILE))["rows"]
        except Exception:
            mirror = []
    if "--catalog" in argv:
        crows = probe_catalog()
        rows += crows
        mirror = []
        with open(CATALOG_FILE, "w") as fh:
            json.dump({"ts": datetime.now().isoformat(timespec="seconds"),
                       "rows": crows}, fh, ensure_ascii=False, indent=1)
    scan = {"ts": datetime.now().isoformat(timespec="seconds"),
            "n": len(rows),
            "counts": {v: sum(1 for r in rows if r["verdict"] == v)
                       for v in sorted({r["verdict"] for r in rows})},
            "rows": rows}
    latest = os.path.join(RADAR_DIR, "latest.json")
    stamp = scan["ts"].replace(":", "-").replace(" ", "_")
    with open(os.path.join(RADAR_DIR, "scan-%s.json" % stamp),
              "w") as fh:
        json.dump(scan, fh, ensure_ascii=False, indent=1)
    # latest.json = scan courant + miroir catalogue en veille ( marque
    # via=catalog-mirror ) pour que le diff du prochain scan paye voie
    # ses propres lignes comme PREV, pas comme decouvertes.
    carried = [dict(r, via="catalog-mirror") for r in mirror]
    latest_doc = {"ts": scan["ts"],
                  "n": len(rows) + len(carried),
                  "counts": scan["counts"],
                  "rows": rows + carried}
    prev = {}
    if os.path.exists(latest):
        # clé (texte, want) : le corpus contient des lignes au MEME
        # texte avec des volontés différentes — indexé sur le texte
        # seul, le last-write-wins faisait ressortir un NO_MATCH
        # ancien comme « REGRESSION » (artefact mesuré 22-11 21h57,
        # ligne PT loja).
        prev = {(r["text"], r.get("want"), r.get("via")): r["verdict"]
                for r in json.load(open(latest))["rows"]}
    with open(latest, "w") as fh:
        json.dump(latest_doc, fh, ensure_ascii=False, indent=1)
    new_pain = [r for r in rows
                if r["verdict"] not in ("ok", "leurre-ok", "plan-skip")
                and prev.get((r["text"], r.get("want"),
                              r.get("via"))) == "ok"]
    fresh = [r for r in rows
             if r["verdict"] not in ("ok", "leurre-ok", "plan-skip")
             and (r["text"], r.get("want"), r.get("via"))
             not in prev]
    healed = [k for k, v in prev.items()
              if v not in ("ok", "leurre-ok", "plan-skip")
              and any((r["text"], r.get("want"), r.get("via")) == k
                      and r["verdict"] in
                      ("ok", "leurre-ok") for r in rows)]
    print("# RADAR ROUTEUR — %s" % scan["ts"])
    print("douleurs actives : %s" % json.dumps(
        {k: v for k, v in scan["counts"].items()
         if k not in ("ok", "leurre-ok", "plan-skip")}))
    for label, items in (("REGRESSION", new_pain), ("NOUVELLE", fresh),
                         ("GUERIE", healed)):
        for it in items[:8]:
            if isinstance(it, dict):
                print("- %s : %r → %s" % (label, it["text"],
                                          it["verdict"]))
            else:
                print("- GUERIE : %r (want %r)" % (it[0][:70], it[1]))

    print("(brut : docs/RADAR/scan-%s.json — local-only)" % stamp)


if __name__ == "__main__":
    main()
