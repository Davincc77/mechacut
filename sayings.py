"""Human sentences for the site's Try-it panel.

One line per task, PER LANGUAGE, in the money the reader's country
bills in: dollars for EN, euros for FR, reais for pt-BR. Keys are route
paths (stable contract); missing paths fall back to the tool's purpose
line. These are instructions, not slogans — phrased the way a person
actually talks to their agent.
"""

SAY = {
    "/api/v1/fiche/shop-reste": {
        "en": "shop had 435, sold 35 morning, 40% of the REST "
              "afternoon, how many remain?",
        "fr": "le magasin a 435 articles, 35 vendus le matin, 40 % du "
              "RESTE l'après-midi — combien restent ?",
        "pt": "a loja tinha 435, vendeu 35 de manha, 40% DO RESTO a "
              "tarde — quantos restam?"},
    "/api/v1/fiche/partage-reste": {
        "en": "split 3829: first gets 2/5, second 1/6 OF THE REST",
        "fr": "partage 3 829 € : le premier a 2/5, le second 1/6 DU "
              "RESTE",
        "pt": "divida 3829: o primeiro pega 2/5, o segundo 1/6 DO "
              "RESTO"},
    "/api/v1/fiche/soldes2": {
        "en": "-25% then -20% on 81.90 — final price, exact",
        "fr": "-25 % puis -20 % sur 81,90 € — prix final exact",
        "pt": "-25% e depois -20% em 81,90 — preço final exato"},
    "/api/v1/chart": {
        "en": "bar chart of these sales figures",
        "fr": "fais-moi un histogramme de ces ventes",
        "pt": "faça um gráfico de barras dessas vendas"},
    "/api/v1/reshape": {
        "en": "flatten this API response into a simple table",
        "fr": "aplatis cette réponse JSON en tableau simple",
        "pt": "aplatize essa resposta da API numa tabela simples"},
    "/api/v1/validate": {
        "en": "does this JSON match this schema?",
        "fr": "ce JSON respecte-t-il ce schéma ?",
        "pt": "este JSON obedece a este schema?"},
    "/api/v1/csv/fix": {
        "en": "repair this broken CSV",
        "fr": "répare ce CSV cassé",
        "pt": "conserta este CSV quebrado"},
    "/api/v1/csv/types": {
        "en": "what type is each column?",
        "fr": "devine les types de chaque colonne",
        "pt": "qual o tipo de cada coluna?"},
    "/api/v1/csv/join": {
        "en": "join these two tables on id",
        "fr": "joins ces deux tables sur id",
        "pt": "junte essas duas tabelas por id"},
    "/api/v1/table/pivot": {
        "en": "pivot this table by month",
        "fr": "pivot ce tableau par mois",
        "pt": "pivot desta tabela por mês"},
    "/api/v1/json/patch": {
        "en": "change just this one field",
        "fr": "change juste ce champ sans renvoyer tout",
        "pt": "mude só este campo sem reenviar tudo"},
    "/api/v1/text/diff": {
        "en": "what changed between these two versions?",
        "fr": "qu'est-ce qui a changé entre ces deux versions ?",
        "pt": "o que mudou entre essas duas versões?"},
    "/api/v1/text/patch": {
        "en": "apply this patch to the text",
        "fr": "applique ce patch au texte",
        "pt": "aplique este patch no texto"},
    "/api/v1/text/apply-diff": {
        "en": "apply this unified diff",
        "fr": "applique ce diff unifié",
        "pt": "aplique este diff unificado"},
    "/api/v1/format/convert": {
        "en": "convert this YAML to JSON",
        "fr": "convertis ce YAML en JSON",
        "pt": "converta este YAML para JSON"},
    "/api/v1/num/round": {
        "en": "round 1234.5678 to 2 decimals",
        "fr": "arrondis 1234.5678 à 2 décimales",
        "pt": "arredonde 1234.5678 para 2 casas"},
    "/api/v1/math/calc": {
        "en": "compute 7834 times 9217 and round 1000 over 17 to four "
              "places — exactly",
        "fr": "calcule 7834 fois 9217 et arrondis 1000 sur 17 à 4 "
              "décimales — exactement",
        "pt": "calcule 7834 vezes 9217 e arredonda 1000 por 17 a "
              "quatro casas — exato"},
    "/api/v1/money/discount": {
        "en": "is 30% off plus another 20% the same as 50% off on a $89.90 "
              "jacket?",
        "fr": "-30 % puis -20 %, ça fait -50 % sur un manteau à 89,90 € ?",
        "pt": "30 % mais 20 % de desconto é o mesmo que 50 % numa jaqueta "
              "de R$ 89,90?"},
    "/api/v1/table/sql_dump": {
        "en": "turn this CSV into INSERT statements with the right "
              "column types for postgres",
        "fr": "converts ce CSV en INSERT avec les bons types de colonnes "
              "pour postgres",
        "pt": "converta este CSV em INSERT com os tipos certos para "
              "mysql"},
    "/api/v1/table/scale": {
        "en": "third of this recipe — 3/4 cup sugar, 5 eggs, 2 tsp salt, "
              "6 to 2 servings",
        "fr": "un tiers de cette recette — 250 g de sucre, 5 œufs, "
              "2 c. à café de sel, pour 6 au lieu de 2",
        "pt": "um terço desta receita — 2 xícaras de açúcar, 5 ovos, "
              "2 colheres de chá de sal, de 6 para 2 porções"},
    "/api/v1/date/recurrence": {
        "en": "book club every other Tuesday at 7 — give me the next "
              "four dates, not a guess",
        "fr": "le club de lecture tous les quinze jours mardi 19 h — "
              "les quatre prochaines dates, pas à l'œil",
        "pt": "clube do livro a cada duas terças às 19h — as próximas "
              "quatro datas, não no chute"},
    "/api/v1/units/shoe_size": {
        "en": "the chart says EU 42.5 but adidas prints 42 2/3 — what "
              "is my foot, in millimetres, with the drift stated",
        "fr": "le tableau dit EU 42,5 mais adidas imprime 42⅔ — ma "
              "pointure en millimètres, la dérive dite, pas un numéro "
              "au pif",
        "pt": "a tabela diz EU 42,5 mas a adidas imprime 42⅔ — meu pé "
              "em milímetros, com a deriva declarada, não no chute"},
    "/api/v1/date/tz_ambiguity": {
        "en": "my cron says 01:30 the night clocks fall back — which "
              "UTC instants is that, both of them, named",
        "fr": "mon cron tourne à 01h30 la nuit où l'on recule d'une "
              "heure — quels instants UTC, les deux, nommés",
        "pt": "meu cron roda às 01:30 na noite em que os relógios "
              "atrasam — quais instantes UTC, os dois, nomeados"},
    "/api/v1/money/flight_comp": {
        "en": "my flight arrived 3 h 20 late on 2027-11-01 — what does "
              "the NEW EU table say I'm owed, € or £, deadline included",
        "fr": "mon vol est arrivé avec 3 h 20 de retard le 1er nov. "
              "2027 — ce que la NOUVELLE table UE me doit, en euros, "
              "forclusion comprise",
        "pt": "meu voo chegou 3h20 atrasado em 1º de nov. de 2027 — o "
              "que a NOVA tabela europeia me deve, em euros, com o prazo "
              "de nove meses"},
    "/api/v1/date/week": {
        "en": "my report prints 2027-W53 but that week does not exist — "
              "give me the real ISO year, the bounds, and Excel beside it",
        "fr": "mon rapport imprime 2027-W53 mais cette semaine "
              "n'existe pas — l'année ISO réelle, les bornes, et la "
              "semaine Excel à côté",
        "pt": "meu relatório imprime 2027-W53 mas essa semana não "
              "existe — o ano ISO real, os limites e a semana do Excel "
              "ao lado"},
    "/api/v1/money/baggage": {
        "en": "my bag is 40×18×30 and my flight is 2027-11-02 — does "
              "it fit under the seat for free, and what does my "
              "airline's gauge say",
        "fr": "mon sac fait 40×18×30, vol le 2 nov. 2027 — passe-t-il "
              "gratuitement sous le siège, et que dit le gabarit de "
              "ma compagnie",
        "pt": "minha bagagem é 40×18×30, voo 2/11/2027 — passa de "
              "graça sob o assento, e o que diz o gabarito da minha "
              "companhia"},
    "/api/v1/csv/excel_damage": {
        "en": "before I open this CSV in Excel — which columns will "
              "silently lose their zeros, IDs and dates",
        "fr": "avant d'ouvrir ce CSV dans Excel — quelles colonnes "
              "perdront en silence leurs zéros, identifiants et dates",
        "pt": "antes de abrir este CSV no Excel — quais colunas "
              "perderão em silêncio os zeros, IDs e datas"},
    "/api/v1/money/crossover": {
        "en": "plan A is 24.5p a kWh plus 60p a day, plan B 26.32p "
              "plus 54.83p — above how many kWh does A actually win?",
        "fr": "tarif A 0,25 €/kWh + 60 centes d'abonnement par jour, "
              "B 0,27 € + 45 — à partir de combien de kWh A gagne "
              "vraiment",
        "pt": "plano A R$ 0,30 por kWh mais R$ 12 por mês, plano B "
              "R$ 0,26 mais R$ 22 — a partir de quantos kWh o B "
              "passa a ganhar"},
    "/api/v1/csv/excel_display": {
        "en": "openpyxl read 1000000 from the budget cell but the "
              "human saw $1,000 — render what Excel displays",
        "fr": "openpyxl lit 1 000 000 dans la cellule du budget mais "
              "l'humain voit 1 000 $ — rends ce qu'Excel affiche",
        "pt": "o openpyxl lê 1000000 na célula do orçamento mas o "
              "chefe vê US$ 1.000 — mostre o que o Excel exibe"},
    "/api/v1/date/tz_anchor": {
        "en": "my cron says 9:00 Paris and the box is UTC — how "
              "late does it actually fire",
        "fr": "le job est écrit à 9 h heure de Paris, le serveur "
              "est en UTC — il part vraiment à quelle heure",
        "pt": "meu agendador é UTC mas escrevi 09:00 no horário de "
              "São Paulo — com quantos minutos de atraso dispara"},
    "/api/v1/money/points": {
        "en": "60,000 points for a $438 flight minus $5.60 taxes — "
              "what is a point really worth",
        "fr": "29 000 points pour un vol à 438 € moins 5,60 € de "
              "taxes, ça vaut combien de centimes le point "
              "exactement",
        "pt": "29 000 pontos por um voo de R$ 438 menos R$ 5,60 de "
              "taxas — quantos centavos vale cada ponto"},
    "/api/v1/net/sri": {
        "en": "hash this exact local file into an integrity attribute "
              "I can paste — and audit the one that keeps failing",
        "fr": "transforme ce fichier local en attribut integrity prêt "
              "à coller — et audite celui qui bloque en prod",
        "pt": "gere o atributo integrity deste arquivo local pronto "
              "para colar — e audite o que quebra em produção"},
    "/api/v1/check/target": {
        "en": "my answer says 49.14 and calls it 'final price' — did "
              "it hit the question's target or a leftover?",
        "fr": "ma réponse dit 49,14 et l'appelle « prix final » — "
              "est-ce la cible de la question ou un reste ?",
        "pt": "minha resposta diz 49,14 e chama de 'preço final' — "
              "acertou o alvo da pergunta ou um resto?"},
    "/api/v1/check/format": {
        "en": "check every date and uuid field in this payload against "
              "its real format, not just 'string'",
        "fr": "vérifie chaque champ date et uuid du payload contre son "
              "vrai format, pas juste « string »",
        "pt": "confira cada campo de data e uuid contra o formato real, "
              "não só 'string'"},
    "/api/v1/csv/money_columns": {
        "en": "do these invoice amounts use US or European decimals — "
              "read them without guessing",
        "fr": "ces montants sont-ils en décimales US ou européennes — "
              "lis-les sans deviner",
        "pt": "esses valores usam decimal US ou europeu — leia sem "
              "adivinhar"},
    "/api/v1/date/relative": {
        "en": "when is 'next Monday morning', counted from today?",
        "fr": "c'est quoi « lundi prochain » en date exacte ?",
        "pt": "quando é « segunda que vem », em data exata?"},
    "/api/v1/text/url_canonical": {
        "en": "is this link the same page as that one, once you strip "
              "the tracking junk?",
        "fr": "c'est la même page que ce lien, une fois les traqueurs "
              "retirés ?",
        "pt": "esse link é a mesma página daquele, tirando o rastreamento?"},
    "/api/v1/xml/to_json": {
        "en": "turn this RSS feed into JSON, items always an array",
        "fr": "convertis ce flux RSS en JSON, avec items toujours en "
              "tableau",
        "pt": "converte esse feed RSS em JSON, items sempre como "
              "array"},
    "/api/v1/web/cert": {
        "en": "when does this site's TLS certificate expire?",
        "fr": "quand expire le certificat TLS de ce site ?",
        "pt": "quando vence o certificado TLS deste site?"},
    "/api/v1/id/checkdigit": {
        "en": "is this ISBN a real check digit or a bad copy-paste?",
        "fr": "ce code-barres a-t-il le bon chiffre de contrôle ?",
        "pt": "este ISBN tem o dígito verificador certo?"},
    "/api/v1/image/rightsize": {
        "en": "shrink this screenshot to 480 wide, keep the ratio",
        "fr": "réduis cette capture à 480 de large, en gardant les proportions",
        "pt": "diminui esse print para 480 de largura, mantendo a proporção"},
    "/api/v1/money/rates": {
        "en": "what's a dollar worth today? and on 6 November?",
        "fr": "un euro vaut combien de réais aujourd'hui ? et au 6 novembre ?",
        "pt": "quanto está o dólar hoje? e no dia 6 de novembro?"},
    "/api/v1/money/prorate": {
        "en": "prorate $1,200 over 47 days",
        "fr": "prorate 1 200 € sur 47 jours",
        "pt": "prorrateie R$ 1.200 por 47 dias"},
    "/api/v1/money/amortize": {
        "en": "schedule a $15,000 loan at 4.5% over 24 months",
        "fr": "tableau d'un prêt de 15 000 € à 4,5 % sur 24 mois",
        "pt": "tabela de um financiamento de R$ 15.000 a 4,5% em 24 meses"},
    "/api/v1/money/interest": {
        "en": "$1,000 at 10% for 5 years, compounded monthly?",
        "fr": "1 000 € à 10 % pendant 5 ans, capitalisés mensuellement ?",
        "pt": "R$ 1.000 a 10% por 5 anos, capitalizado ao mês?"},
    "/api/v1/date/calc": {
        "en": "how many business days until December 31?",
        "fr": "combien de jours ouvrés jusqu'au 31 décembre ?",
        "pt": "quantos dias úteis até 31 de dezembro?"},
    "/api/v1/hash/sha256": {
        "en": "hash this payload with sha256",
        "fr": "hashe ce payload en sha256",
        "pt": "dê um sha256 neste payload"},
    "/api/v1/hash/hmac": {
        "en": "sign this message HMAC-SHA256 with this key",
        "fr": "signe ce message en HMAC-SHA256 avec cette clé",
        "pt": "assine esta mensagem HMAC-SHA256 com esta chave"},
    "/api/v1/id/ulid": {
        "en": "give me a deterministic idempotency key",
        "fr": "donne-moi un idempotency-key déterministe",
        "pt": "gere uma chave de idempotência determinística"},
    "/api/v1/secret/scan": {
        "en": "any secrets in this log before I paste it?",
        "fr": "y a-t-il des secrets dans ce log avant que je le colle ?",
        "pt": "tem segredos neste log antes de eu colar?"},
    "/api/v1/text/redact": {
        "en": "mask the secrets in this text",
        "fr": "masque les secrets de ce texte",
        "pt": "mascare os segredos deste texto"},
    "/api/v1/validate/iban": {
        "en": "is this IBAN valid?",
        "fr": "cet IBAN est-il valide ?",
        "pt": "este IBAN é válido?"},
    "/api/v1/validate/taxid": {
        "en": "is my client's VAT number FR40303265045 valid?",
        "fr": "la TVA FR40303265045 de mon client passe-t-elle le contrôle ?",
        "pt": "o CNPJ 11.222.333/0001-81 do meu cliente é válido?"},
    "/api/v1/caip/parse": {
        "en": "which chain is 0x…@eip155:8453?",
        "fr": "c'est quelle chaîne ce 0x…@eip155:8453 ?",
        "pt": "de qual rede é este 0x…@eip155:8453?"},
    "/api/v1/crypto/address": {
        "en": "is this bitcoin address well-formed?",
        "fr": "cette adresse bitcoin est-elle bien formée ?",
        "pt": "este endereço bitcoin é bem formado?"},
    "/api/v1/qr/generate": {
        "en": "make a QR code for this link",
        "fr": "génère un QR pour ce lien",
        "pt": "gere um QR code para este link"},
    "/api/v1/zip/verify": {
        "en": "is this archive healthy without unpacking it?",
        "fr": "cette archive est-elle saine sans l'extraire ?",
        "pt": "este arquivo está íntegro sem extrair?"},
    "/api/v1/ssh/fingerprint": {
        "en": "what's this ssh key's fingerprint?",
        "fr": "quelle est l'empreinte de cette clé ssh ?",
        "pt": "qual a impressão digital desta chave ssh?"},
    "/api/v1/schedule/overlap": {
        "en": "does 9–11 clash with my meetings?",
        "fr": "est-ce que 9h-11h chevauche mes réunions ?",
        "pt": "das 9h às 11h choca com minhas reuniões?"},
    "/api/v1/schedule/holidays": {
        "en": "which days are US federal holidays in 2027?",
        "fr": "quels sont les jours fériés en France en 2027 ?",
        "pt": "quais são os feriados nacionais do Brasil em 2027?"},
    "/api/v1/cron/validate": {
        "en": "what does '0 9 * * 1-5' actually mean?",
        "fr": "à quoi correspond '0 9 * * 1-5' ?",
        "pt": "o que significa '0 9 * * 1-5'?"},
    "/api/v1/ics/validate": {
        "en": "is this calendar file valid?",
        "fr": "ce fichier calendrier est-il valide ?",
        "pt": "este arquivo de calendário é válido?"},
    "/api/v1/ics/generate": {
        "en": "make an .ics for this event",
        "fr": "fais-moi un .ics pour cet événement",
        "pt": "gere um .ics para este evento"},
    "/api/v1/ics/parse": {
        "en": "read this .ics file",
        "fr": "lis ce fichier .ics",
        "pt": "leia este arquivo .ics"},
    "/api/v1/doc/text": {
        "en": "extract the text from this PDF invoice",
        "fr": "extrais le texte de cette facture PDF",
        "pt": "extraia o texto desta nota fiscal em PDF"},
    "/api/v1/web/cache": {
        "en": "what does this Cache-Control header do?",
        "fr": "que veut dire cet en-tête Cache-Control ?",
        "pt": "o que este Cache-Control faz?"},
    "/api/v1/gzip/roundtrip": {
        "en": "gzip these logs, byte-for-byte reproducible",
        "fr": "compresse ces logs en gzip",
        "pt": "comprima estes logs em gzip"},
    "/api/v1/recipe/facts": {
        "en": "pull every amount, date and email from this report",
        "fr": "relève montants, dates et emails de ce texte",
        "pt": "extraia valores, datas e e-mails deste texto"},
    "/api/v1/intent/card": {
        "en": "I don't know which tool to call",
        "fr": "je ne sais pas quel outil appeler",
        "pt": "não sei qual ferramenta chamar"},
    "/api/v1/batch": {
        "en": "run these calls in one round trip",
        "fr": "exécute ces appels en une fois",
        "pt": "execute estas chamadas de uma vez"},
    "/api/v1/integrity/verify": {
        "en": "is that other API really deterministic?",
        "fr": "cette autre API est-elle vraiment déterministe ?",
        "pt": "aquela API é mesmo determinística?"},
    "/api/v1/number/spell": {
        "en": "write 4213 in words",
        "fr": "écris 4213 en toutes lettres",
        "pt": "escreva 4213 por extenso"},
    "/api/v1/md/render": {
        "en": "turn this markdown into html",
        "fr": "converts ce markdown en html",
        "pt": "converta este markdown em html"},
    "/api/v1/html/text": {
        "en": "strip this web page down to its text",
        "fr": "garde juste le texte de cette page html",
        "pt": "fique só com o texto desta página"},
    "/api/v1/extract/facts": {
        "en": "extract the numbers from this sentence",
        "fr": "extrais les faits chiffrés de cette phrase",
        "pt": "extraia os números desta frase"},
    "/api/v1/text/chunk": {
        "en": "split this document into 800-token chunks",
        "fr": "découpe ce document en chunks de 800 tokens",
        "pt": "divida este documento em blocos de 800 tokens"},
    "/api/v1/check/agreement": {
        "en": "do these two answers actually agree?",
        "fr": "ces deux réponses sont-elles identiques ?",
        "pt": "essas duas respostas coincidem?"},
    "/api/v1/check/redlines": {
        "en": "does this draft cross any of my forbidden words?",
        "fr": "ce brouillon franchit-il mes interdits ?",
        "pt": "este rascunho cruza alguma das minhas linhas vermelhas?"},
    "/api/v1/deal/vat": {
        "en": "what's the VAT on $200 at 8.25%?",
        "fr": "quelle TVA sur 200 € HT à 20 % ?",
        "pt": "qual o imposto sobre R$ 200 a 17%?"},
}
