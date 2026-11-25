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
    "/api/v1/ledger/summary": {
        "en": "sum my journal entries by month and carry the "
              "running balance",
        "fr": "résume mon grand livre par mois avec le solde "
              "reporté",
        "pt": "resuma meu livro-razão por mês com o saldo "
              "acumulado"},
    "/api/v1/shop/shipping-deadline": {
        "en": "last day to ship UPS 2nd Day Air so it arrives by "
              "Christmas?",
        "fr": "dernier jour pour envoyer avec FedEx Express Saver "
              "avant Noël — combien de jours me reste-t-il ?",
        "pt": "qual o último dia para enviar FedEx Ground 3 dias e "
              "chegar no Natal 2026?"},
    "/api/v1/shop/return-deadline": {
        "en": "can I still return the Christmas gift I bought at "
              "Target, and until when?",
        "fr": "jusqu'à quelle date peut-on encore retourner un "
              "cadeau de Noël acheté à la Fnac ?",
        "pt": "qual o prazo para devolver um presente de Natal "
              "comprado na Amazon?"},
    "/api/v1/shop/pricedrop-refund": {
        "en": "I paid 100 for the TV, it dropped to 80 last week — "
              "does Best Buy owe me the difference, and until when?",
        "fr": "acheté 100 € à la Fnac, passé à 80 € — qui me "
              "rembourse la différence et jusqu'à quand ?",
        "pt": "paguei 100 e caiu para 80 — quem me devolve a "
              "diferença e até quando?"},
    "/api/v1/agent/mcp-surface": {
        "en": "did that MCP server's tool list change under me "
              "since the listing I pinned last week?",
        "fr": "qu'est-ce qui a changé dans la liste d'outils MCP "
              "depuis le relevé que j'avais épinglé ?",
        "pt": "o que mudou na lista de ferramentas MCP desde a "
              "leitura que eu tinha fixado?"},
    "/api/v1/agent/context-tax": {
        "en": "how many tokens does this MCP server's tool list "
              "cost my agent, every turn?",
        "fr": "combien de tokens la liste d'outils de ce serveur "
              "MCP coûte à mon agent, à chaque tour ?",
        "pt": "quantos tokens a lista de ferramentas desse servidor "
              "MCP custa para meu agente, a cada turno?"},
    "/api/v1/agent/cost-diff": {
        "en": "how many extra tokens per turn did the update to my "
              "MCP server's tool list cost me?",
        "fr": "combien de tokens en plus par tour la "
              "nouvelle liste d'outils de mon serveur MCP "
              "m'a coûté ?",
        "pt": "quantos tokens a mais por turno meu servidor MCP "
              "custou com a nova versão da lista de ferramentas?"},
    "/api/v1/agent/tool-trim": {
        "en": "115 tools, 200k window — which servers do I "
              "disconnect to fit, and what does it save?",
        "fr": "115 outils, fenêtre 200k — lesquels débrancher pour "
              "tenir, et combien ça rend ?",
        "pt": "115 ferramentas, janela 200k — quais desligar para "
              "caber, e quanto eu economizo?"},
    "/api/v1/agent/tool-overlap": {
        "en": "two servers expose get_file and my gateway prefix is "
              "long — which tool silently vanished from VS Code?",
        "fr": "deux serveurs exposent get_file, mon préfixe gateway "
              "est long — quel outil a silencieusement disparu ?",
        "pt": "dois servidores expõem get_file e meu prefixo gateway "
              "é longo — qual ferramenta sumiu sem aviso?"},
    "/api/v1/agent/mcp-list-completeness": {
        "en": "my server declares 64 tools, Codex only sees the first "
              "15 — did my client stop at page one, and what exactly "
              "is missing?",
        "fr": "mon serveur déclare 64 outils, mon agent n'en voit que "
              "15 — mon client s'est-il arrêté à la page 1, et que me "
              "manque-t-il exactement ?",
        "pt": "meu servidor tem 64 ferramentas, meu agente só vê 15 "
              "— o cliente parou na página 1; quais faltam?"},
    "/api/v1/shop/withdrawal": {
        "en": "parcel arrived Tuesday — what is the real last day "
              "to change my mind, weekends and holidays counted?",
        "fr": "reçu mardi — jusqu'à quand puis-je me rétracter, "
              "fériés comptés ?",
        "pt": "recebi o pacote terça — até que dia posso desistir "
              "pela lei francesa, contando fim de semana e feriado?"},
    "/api/v1/invoice/payment-due": {
        "en": "invoice Friday 1 May, net 30 — the calendar says "
              "31 May, my client swears 17 June, and Germany moves "
              "the date by law. Which date is the REAL one?",
        "fr": "facture vendredi 1er mai, net 30 — le calendrier dit "
              "31 mai, le client jure 17 juin, l'Allemagne reporte "
              "par la loi : quelle date est la vraie échéance ?",
        "pt": "fatura sexta 1º de maio, net 30 — o calendário diz "
              "31 de maio, o cliente jura 17 de junho e a Alemanha "
              "adia por lei: qual é a data de vencimento real?"},
    "/api/v1/invoice/validate-totals": {
        "en": "the OCR read $1,204.50 as the total — do these lines "
              "actually add up to it?",
        "fr": "est-ce que le total déclaré de la facture correspond "
              "à la somme des lignes ?",
        "pt": "a nota diz R$ 1.204,50 no total — as linhas batem "
              "com esse valor?"},
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
    "/api/v1/ship/dimweight": {
        "en": "my box is 20x20x12 inches and two calculators say 35 "
              "and 34.5 — which weight does the carrier bill",
        "fr": "mon colis fait 40×30×25 cm, un simulateur annonce 5 kg "
              "et le transporteur facture 6 — quel poids est vraiment "
              "facturé",
        "pt": "minha caixa é 40×30×25 cm, um simulador diz 5 kg e a "
              "transportadora cobra 6 — qual peso sai na fatura"},
    "/api/v1/json/coerce": {
        "en": "the model sent limit 8.0 and the strict parser rejected "
              "the whole call — repair the arguments without guessing",
        "fr": "le modèle a envoyé limit 8.0 et le parseur strict a "
              "tout refusé — répare les arguments sans jamais deviner",
        "pt": "o modelo mandou limit 8.0 e o parser estrito recusou a "
              "chamada inteira — conserte os argumentos sem adivinhar"},
    "/api/v1/money/bogo": {
        "en": "the sign says buy one get one 50% off — a $60 and a $40 "
              "hoodie: what percentage does the register really take",
        "fr": "l'affiche dit achète le premier, le deuxième à −50 % — "
              "deux sweats à 60 € et 40 €, c'est combien sur la note",
        "pt": "a placa diz compre um e leve o segundo com 50% off — "
              "duas camisetas de R$ 60 e R$ 40: qual é o desconto real "
              "no caixa"},
    "/api/v1/money/unitprice": {
        "en": "the 500 g pack became 400 g at the same price — what "
              "percentage is it really per kilogram, and is two-for-$7 "
              "cheaper per ounce than the big jar",
        "fr": "le paquet de 500 g est passé à 400 g au même prix — "
              "combien ça fait vraiment au kilo, et le 2 pour 7 $ "
              "bat-il le grand pot à l'once",
        "pt": "o pacote de 500 g virou 400 g pelo mesmo preço — quanto "
              "isso dá por quilo de verdade, e o leve 2 por R$ 7 é "
              "mais barato por grama que o pote grande"},
    "/api/v1/food/poultry": {
        "en": "Thanksgiving is Thursday — what time does the turkey "
              "leave the freezer to hit the table at three",
        "fr": "thanksgiving jeudi : à quelle heure sortir la dinde "
              "du congélateur pour être à table à quinze heures",
        "pt": "ação de graça quinta: a que horas tirar o peru do "
              "congelador para estar à mesa às quinze horas"},
    "/api/v1/food/leftovers": {
        "en": "the turkey went in the fridge at 9 pm after the "
              "4 pm dinner — by which day do I eat it, and until "
              "when does it keep if I freeze it tonight",
        "fr": "la dinde est entrée au frigo à 21 h après le repas "
              "de 16 h — jusqu'à quel jour la manger, et jusqu'à "
              "quand si je la congèle ce soir",
        "pt": "o peru foi para a geladeira às 21h depois do jantar "
              "das 16h — até que dia comer, e até quando se "
              "congelar hoje à noite"},
    "/api/v1/food/ovenschedule": {
        "en": "the bird, the stuffing and the rolls all want the "
              "oven before a 4 pm serve — give me the countdown and "
              "name the temperature conflicts",
        "fr": "la dinde, la farce et les petits pains veulent tous "
              "le four avant un service de 16 h — donne-moi le "
              "compte à rebours et nomme les conflits de "
              "température",
        "pt": "o peru, o recheio e os pães querem todos o forno "
              "antes das 16h — me dá a contagem regressiva e "
              "nomeia os conflitos de temperatura"},
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
    "/api/v1/shop/discount-audit": {
        "en": "an EU shop strikes 100 down to 70 — real 30% off "
              "under the Omnibus rule, or fiction?",
        "fr": "l'étiquette annonce -30 % sur un 89,90 € — le prix "
              "barré tient-il la règle des 30 jours ?",
        "pt": "a loja na UE grita 30% OFF sobre o preço riscado — "
              "a regra dos 30 dias segura a auditoria?"},
    "/api/v1/agent/mcp-audit": {
        "en": "your MCP server lists 12 tools and the client loads "
              "3 — paste the listing, get the named reasons",
        "fr": "le client ne charge que 3 outils sur 12 — colles la "
              "liste, reçois les raisons nommées, sans lancer le "
              "serveur",
        "pt": "o cliente carrega 3 das 12 ferramentas — cole a "
              "lista e receba os motivos com nome, sem executar o "
              "servidor"},
    "/api/v1/shop/legal-guarantee": {
        "en": "gift faulty on 16 January — the shop window died, "
              "the LAW didn't: your 30-day, six-month and six-year "
              "dates, to the day",
        "fr": "le cadeau tombe en panne le 16 janvier : la fenêtre "
              "du magasin est morte, la garantie légale court "
              "encore — vos dates de 2 ans, de présomption et de "
              "forclusion, jour pour jour",
        "pt": "o presente quebra em 16 de janeiro: a janela da loja "
              "morreu, a garantia legal da França e do Reino Unido "
              "continua — datas contadas ao dia"},
    "/api/v1/money/keep-records-uk": {
        "en": "can I shred this drawer? — every UK clock from its "
              "official anchor: the earliest lawful destruction "
              "date, to the day",
        "fr": "puis-je jeter ce classeur ? — chaque horloge du "
              "Royaume-Uni part de son ancre officielle (émission, "
              "clôture, deadline) : la date de destruction permise, "
              "jour pour jour",
        "pt": "posso descartar esta pasta? — cada prazo do Reino "
              "Unido conta da âncora oficial: a data em que o "
              "documento pode ser destruído, ao dia"},
    "/api/v1/agent/retry-budget": {
        "en": "same 429 three times running — retry it, change it, "
              "or stop?",
        "fr": "le même timeout au troisième essai — re-tenter en "
              "core, muter ou abandonner ?",
        "pt": "o mesmo erro tres vezes seguidas — repetir, mudar "
              "ou parar?"},
    "/api/v1/shop/gift-voucher": {
        "en": "€50 gift voucher from Dublin, printed dead last "
              "month — five-year law: alive or not?",
        "fr": "carte cadeau de 50 € achetée à Dublin, périmée sur "
              "le papier — la loi des cinq ans la ravive ?",
        "pt": "vale-presente de 50 € comprado em Dublin, vencido no "
              "papel — a lei dos cinco anos vale aqui?"},
    "/api/v1/shop/soldes-window": {
        "en": "winter sales 2027 in France: Wednesday January 6 — "
              "or the 13th? the arrête decides, not the calendar "
              "site",
        "fr": "soldes d'hiver 2027 : mercredi 6 janvier à 8 h ou "
              "13 ? et en Moselle, samedi 2 ou lundi 4 ? l'arrêté "
              "tranche, la presse hésite",
        "pt": "os saldos de inverno 2027 na França começam dia 6 "
              "ou 13 de janeiro? a data vem do arrêté, não do "
              "site de calendário"},
    "/api/v1/shop/soldes-be": {
        "en": "Belgian winter sales 2027: Saturday 2 January or "
              "the 3rd? and when does the one-month standstill "
              "close — 1 January or 2 January? the Livre VI says, "
              "the press splits",
        "fr": "soldes d'hiver 2027 en Belgique : samedi 2 ou "
              "dimanche 3 janvier ? et l'attente du 2 décembre au "
              "1er janvier ou du 3 ? le Livre VI tranche, la "
              "presse hésite",
        "pt": "os saldos de inverno 2027 na Bélgica: sábado 2 ou "
              "domingo 3 de janeiro? e a espera termina 1 ou 2 de "
              "janeiro? o Livro VI decide, a imprensa erra"},
    "/api/v1/shop/soldes-lu": {
        "en": "Luxembourg has no rule — every date comes from an "
              "act: winter 2026/2027 runs Saturday 2 to Saturday "
              "30 January; and summer 2023? the Official Journal "
              "printed a Sunday end until it rectified, the press "
              "had it right all along",
        "fr": "au Luxembourg, chaque date vient d'un règlement "
              "grand-ducal, jamais d'une formule : hiver 2026/2027 "
              "du samedi 2 au samedi 30 janvier — et l'été 2023 ? "
              "le Mémorial imprimait « samedi 23 juillet », un "
              "dimanche ; le rectificatif dit 22, la presse l'a "
              "toujours su",
        "pt": "no Luxemburgo cada data vem de um ato, nunca de "
              "uma regra: o inverno 2026/2027 vai de sábado 2 a "
              "30 de janeiro; e o verão 2023? o Jornal Oficial "
              "imprimia 23 (um domingo) até o retificativo dizer "
              "22 — a imprensa acertava desde o começo"},
}
