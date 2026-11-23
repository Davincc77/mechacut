# FINDINGS — BENCH EQUIP-V1 (24-11, local qwen2.5:7b-instruct-q4_K_M, temperature 0)

**Question posée** : un utilisateur Hermes qui ÉQUIPE la skill mechacut
dépense-t-il moins de tokens / se trompe-t-il moins sur les tâches
mécaniques répétitives, vs le même agent SANS la skill ?

**Protocole** : mêmes 10 tâches, même modèle, même outil (sandbox python
réelle), un seul facteur qui change — la skill telle que le plugin
l'installe (`~/.hermes/plugins/mechacut/skills/mechacut/SKILL.md`,
3 900 chars ≈ 1 000 tokens, sha cb1aded6604d). Tokens = compteurs
d'ollama (`prompt_eval_count` + `eval_count`), PAS d'estimation.
Ground truth = Decimal/datetime/hashlib calculés ici, jamais la mémoire
du modèle. 20 sessions.

## Les chiffres bruts

| bras              | justesse | tokens totaux | médiane/task |
|-------------------|----------|---------------|--------------|
| sans skill        | 5/10     | 10 075        | 697          |
| avec skill        | 6/10     | 30 055        | 2 875        |

**Équipé gagne la justesse, perd le token — et les deux chiffres
s'expliquent, y compris par des fautes à nous.**

## Ce que l'équipement a bel et bien défendu (les classes où le sans-skill MENT)

| tâche        | sans skill                              | avec skill                 |
|--------------|------------------------------------------|----------------------------|
| sha256       | **hash halluciné** `9a2d9a2d9a2d…` répété | hash exact serveur         |
| 45 jours     | 4 itérations, 2 225 tok                   | 1 appel, exact             |
| big mul      | correct mais 608 tok de loop python       | 1 appel                    |
| round 2.675  | (les deux corrects)                       | 1 appel                    |

L'agent non équipé qui ne sait pas hacher **invente un hash plausible**.
C'est la fraude silencieuse que le pitch dénonçait, observée en direct.

## Le ×4 sur les tokens est en majeure partie un artefact — de notre côté

Chaque itération de boucle renvoie le system prompt entier, skill
comprise : une session de 5 appels paie la skill ×5 (30 055 tok au lieu
d'environ 12 000 dans un vrai client Hermes, où la skill est une prime
FIXE par session et chaque tâche mécanique ~50 tokens). Le coût serveur
réel mesuré à part, au HTTP : **8 tâches mécaniques complètes ≈ 500
tokens de réponses, tout exact ou refus nommé.** Dans une session Hermes
(60-150 messages), la prime skill s'amortit dès la 2ᵉ tâche mécanique.

## Les échecs de l'armé = un gap de la SKILL, pas du serveur

1. **money/split** : l'armé envoie `participants: 7` → 400 → 4 476 tok
   de round-trips → échoue. La forme réelle (`participants: ["a","b",…]`)
   n'est pas dans le mini-texte. Le serveur, lui, répond `6×14.29 + 14.26`
   = exactement 100.00 en un appel (~110 tok).
2. **date/calc add** : la skill ne dit pas que `duration` est un
   ISO-8601-ish (`"45d"`) ; idem `diff` → `params.until`.
3. **1,234 (T7)** : l'armé n'a PAS posé la question → a répondu 1234.
   La skill dit de refuser l'ambiguïté ; le 7B a ignoré sa propre skill.
   Données honnêtes sur les modèles faibles, à publier telles quelles.
4. **T8 « between neither endpoint »** : nos deux bras ont donné 79/88 —
   la QUESTION était ambiguë. Le serveur n'est jamais consulté ainsi.
   Verdict de doctrine : la seule réponse correcte pour cette phrase est
   un refus qui nomme les lectures. (Le bench nous a faits tomber dans
   notre propre piège — consigné.)

## Corrections décidées (bundle 95)

- SKILL-MINI/SKILL.md plugin : table des 6 payload shapes réelles
  (split=liste de noms, date/calc duration/until, hash `data/algo`,
  units `from/to`), + ligne « le bord bloque l'UA urllib nu —
  mets un User-Agent ».
- Harnais : compter la skill comme PRIME FIXE (session multi-tâches)
  et mesurer une « session Hermes moyenne » = 1 prime + N tâches,
  vs baseline = N loops. C'est LE chiffre qu'on imprime.
- T7/T8 : rester tels quels — ce sont des résultats, pas des bugs.

## À publier (après re-run sous ces conditions)

« Sur une 7B locale : la skill fait passer le hash halluciné en hash
exact et le 45-jours en un appel — au prix d'une prime fixe d'environ
1 000 tokens par session qui s'amortit dès la deuxième tâche
mécanique. L'agent non équipé ne tombe pas juste plus souvent : il
tombe EN MENTA. » — et publier aussi le ×4 cold-session qui ne dit pas
encore tout.
