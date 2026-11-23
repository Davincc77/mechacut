# PROTOCOL-KIT — la suite sur le disque, l'acte de naissance dans le manifest

Spec de protocole. Réponse à l'inversion proposée par l'humain (23-11, nuit) :
et si l'agent, au lieu d'appeler mechacut par le réseau, installait la suite
basique sur le disque de sa machine, avec une skill qui lui permet d'appeler
le kit ET de construire ses propres outils dessus ?

## Le geste central

Un protocole d'outils s'évalue sur trois questions. MCP n'en répond qu'une :

1. Comment nommer l'outil au modèle ? — MCP : oui.
2. Comment prouver que l'outil fait ce qu'il dit ? — MCP : silence.
3. Comment un outil nouveau gagne-t-il le droit d'exister ? — MCP : aucun
   rituel, n'importe qui publie n'importe quoi derrière un nom.

Notre couche : **le contrat est l'unité de capability, pas l'appel.**
Contrat = (nom, grammaire d'entrée, forme de sortie, golds input/expected,
sha256 du module, pins). Le contrat vit au-dessus du transport : HTTP au
datacenter, argv sur le disque — même canon, mêmes golds, même sha. Un agent
écrit pour /agent/manifest fonctionne localement sans réécrire une ligne :
`curl` devient `kit call`.

## Ce qui est déjà vrai

Le repo est déjà coupé en deux : les familles (moneykit, qrkit, evalkit,
loopkit…) sont des fonctions pures Python ; main.py, routing.py et le
serveur ne sont que le boîtier. La suite installable n'est pas un produit à
inventer, c'est un produit à **déshabiller**. Les 127 transformations
libres, elles, sont déjà « la suite basique du genre mechacut sur le disque
». Le payant par machine existe à la grille de prix — c'est ce kit, vendu
comme il devrait l'être.

## L'arbre du kit

    kit/
      suite/*.py          fonctions pures, AST-gate, zéro réseau, zéro disque
      manifest.json       le contrat publié — identique octet pour octet au
                          /agent/manifest : c'est LA source de vérité locale
      golds/*.json        les input/expected tracés AVANT le code
      journal/            append-only, comme le ledger de banc : chaque appel,
                          chaque proposition, chaque verdict, par clé neuve
      SKILL.md            la skill : consulter avant d'agir, appeler via
                          runner, construire selon le rituel
      bin/kit             runner : route / call / propose / verify / diff

Grammaire du runner — les mêmes mots que les routes :

    kit route "mon problème"        -> l'annuaire, même resolve qu'au réseau
    kit call money_baggage in.json  -> stdout canonique, sha256 du rapport
    kit verify                      -> recalcule les pins : le kit n'a pas
                                        dérivé depuis l'installation
    kit diff manifest.json          -> rapport de divergence (eval/compare
                                        appliqué à deux manifestes)

## Le rituel de construction (le protocole, vraiment)

L'agent détecte, propose, et le kit juge. Détection mécanique, pas
d'humeur : le journal connaît les répétitions — N appels canoniques
identiques dans la fenêtre (doom-check en local, c'est la loi 1 de
SKILL-NETWORK qui devient une implémentation).

1. **Contrat d'abord.** La proposition écrit le nom, l'entrée, la sortie,
   et DES GOLDS TRACÉS À LA MAIN AVANT TOUTE LIGNE DE CODE. Un gold que
   l'agent n'a pas su écrire avant l'implémentation n'est pas un gold,
   c'est une photo de l'implémentation — c'est exactement l'incident du
   juge V2, consigné pour l'éternité dans ce repo.
2. **AST-gate** — porte runtime, pas LLM, pas d'avis : fonction pure ;
   imports dans un sous-ensemble stdlib nommé ; pas de réseau, pas de
   disque hors kit/, pas d'eval, pas de horloge murale ni de hasard —
   `as_of` est un argument, toujours ; plafond d'octets et de profondeur.
3. **Gold-gate** : tous les golds passent ou la proposition meurt nommée.
4. **Pin-gate** : l'outil nouveau est épinglé ; les pins existants ne
   bougent pas — un outil qui change de sens en douce est un refus, pas
   une feature.
5. **Publication locale** : le module entre dans suite/ avec un statut :

        proposé      — construit par l'agent, jugé par ses propres portes
        attesté      — journal : M exécutions, zéro divergence signalée
        réseau-vérifié — passé les portes du SKILL-NETWORK (deuxième paire
                       d'yeux, golds rejoués par un tiers, publié au manifest)
        contesté     — un tiers reproduit une divergence : tout appel local
                       le dit à la face de l'agent
        révoqué      — sha de révocation au journal ; l'outil meurt daté

## Pourquoi le local SANS le réseau ne serait pas un protocole

Un kit isolé est un gestionnaire de paquets avec un step-parent :
l'agent écrit ses propres golds, et des golds auto-certifiés ne prouvent
que leur auteur. La valeur du réseau (SKILL-NETWORK) est la **deuxième
paire d'yeux** : la proposition locale, rejouée ailleurs, devient un fait.
C'est la loi fondatrice du banc, miniaturisée par machine : on ne se
relève pas soi-même. Donc :

- kit local = où les leçons NAISSENT (rapide, hors-ligne, gratuit,
  personnel — l'outil évolue avec son propriétaire) ;
- réseau = où les leçons VALENT (golds rejoués par autrui, manifest,
  alertes sur les pushes malsains, pins qui parlent) ;
- le contrat est la même écriture des deux côtés : c'est ça, la couche
  de protocole. Pas de nouveau format, pas de nouveau langage — le format
  du corpus, celui de 300+ golds, avec un champ de plus : `originaire:
  <sha du kit qui l'a enfanté>`.

## Refus nommés (encore, toujours)

- Pas de daemon, pas de service, pas d'auto-update. Le kit est froid :
  c'est l'humain qui décide de la montée de version (`kit verify` dit si
  la machine a dérivé). Un protocole qui s'installe en service persistant
  a trahi sa promesse : le sans-état EST le contrat.
- Pas de réseau dans le moteur : suite/*.py ne connaît ni socket ni URL.
  Le boîtier HTTP est une option de packaging, pas une dépendance.
- Pas de confiance par ancienneté : statut = sha + journal, jamais
  nombre d'étoiles. La réputation est un vote, le protocole est une preuve.
- Pas de code de tiers exécuté sans ses golds : on ne « fait pas
  confiance au paquet », on rejoue ses golds. Ce qui ne peut pas être
  rejoué n'est pas un contrat, et n'entre pas.

## Ce que ça change dans la maison

La boucle cron de ce repo EST la démonstration d'existence : un agent qui,
à chaque cycle, détecte une répétition, trace des golds avant le code,
passe les mêmes portes, publie au manifest. Le kit local, c'est cette
discipline donnée à dix mille agents sur leurs disques — la doctrine
d'ici, version portable, avec le même juge à la porte.

Ordre de construction honnête : 1) `agent/contract-check` au réseau (le
juge des contrats d'autrui — sans lui le kit est orphelin) ; 2) `kit`
runner sur les modules existants (déshabillage, pas réécriture) ;
3) SKILL.md du kit + rituel de proposition vers la file du réseau.
Chaque pièce passe le banc avant de paraître — sinon on n'aurait construit
que le rêve d'un gestionnaire de paquets.

## Part des gains — tranché par l'humain (24-11) : 50/50

Un outil réseau qui tombe dans un palier payant (cap au-delà du plafond 32 Ko,
ou payé au call) rapporte : **50 % à qui a tracé les golds, 50 % à qui tient
le banc.** Pas de bonus de volume, pas de taux dégressif, pas de négociation
par outil : le seul nombre qui n'a jamais besoin d'être justifié est celui
qu'on ne change pas. Les autres chiffres seraient politiques ; 50/50 est
arithmétique.

1. **Le split suit l'admission, jamais l'audience.** Un contrat entre parce
   que le banc le rejoue, pas parce qu'il se vend. L'argent ne rouvre aucune
   porte que le banc a fermée.
2. **Le noyau libre reste libre.** Le réseau ne peut pas créer de nouveau
   péage sur la couche gratuite — le partage ne porte que sur cap/payant.
   Un DUPLICATE-OF ne touche rien : on ne paye pas d'avoir redécouvert la
   France.
3. **Le mécanisme : un seul `payTo`, un contrat splitter.** L'exigence x402
   (EIP-3009, USDC sur Base) ne porte qu'une adresse — c'est la spec, on ne
   la bricole pas. L'adresse publiée est donc un contrat splitter déployé
   sur Base : deux bénéficiaires, proportions en bps fixées au déploiement,
   sha épinglé au manifest. Le paiement reste un message, le partage reste
   on-chain, la facilitation reste gasless. Zéro évolution de protocole,
   zéro compte à tenir pour personne.
4. **Le split est calculé par nos propres outils.** `money_split` —
   répartition exacte au centime, règle de reste fermée — est la
   transformation qui décide qui reçoit quoi quand un montant ne se divise
   pas pile. Le versement d'un réseau déterministe est lui-même une
   transformation déterministe, vérifiable par sha. Le plus beau
   dogfooding possible, et c'est pour ça qu'on n'ira pas externaliser ça à
   une régie de paiements.
5. **Le créateur est l'humain, pas l'agent.** L'adresse bénéficiaire est
   celle du propriétaire de l'agent ; « l'outil évolue avec son propriétaire »
   vaut aussi pour la facture.
6. **Pas de rétroactivité.** Les outils publiés avant le splitter restent à
   la maison ; le réseau démarre à jour 0.

Ce qui reste à construire avant tout versement (et n'est pas encore vrai,
donc n'est pas encore promis) : le contrat splitter déployé, son address
dans le manifest, l'endpoint de soumission qui porte le bénéficiaire, et la
file d'admission. Chacun passera le banc comme n'importe quel outil.
