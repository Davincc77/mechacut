#!/usr/bin/env python3
# -*- coding: utf-8 -*-  # OBLIGATOIRE (b116) : CPython 3.9 execute depuis
# fichier refuse « Non-UTF-8 code starting with \xe2 » sur les longues
# lignes accentuées SANS déclaration — compile() in-memory passe, le
# run ne passe pas ; ne jamais retirer cette ligne.
"""Generate the human landing page FROM the final code (rule 7).

Run after every bundle: python scripts/make_landing.py && pytest -q
Writes: static/landing.html (template with {{keys}}), locales/{en,fr,pt}.json
Everything measurable is read from main.py / payments.py / bench results;
everything human is translated here, in the three voices of the family.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "bench"))

import payments                    # noqa: E402
import registry                    # noqa: E402
import routing                     # noqa: E402

# ------------------------------- measured facts (single source: code)

NAMES = [n for n, _p, _k, _u, _t in routing.TABLE]
TOOLS = [e for e in routing.TABLE if not e[0].startswith("recipe_")]
RECIPES = [e for e in routing.TABLE if e[0].startswith("recipe_")]
PAID = sorted(payments.PRICES)
CAP = sorted(payments.CAP_ROUTES)
path_tier = {}
for name, path, pack, purpose, tags in routing.TABLE:
    if path in payments.PRICES:
        path_tier[name] = "paid"
    elif path in payments.CAP_ROUTES:
        path_tier[name] = "cap"
    else:
        path_tier[name] = "free"
# the lede's breakdown must sum to the number it announces: count the
# TIERS OVER TOOLS ONLY (91+18+11=120) — the 6 recipes are all free and
# get their own clause, not a silent +6 in the green bucket.
_TOOLS_TIER = {k: v for k, v in path_tier.items()
               if not k.startswith("recipe_")}
N_FREE = sum(1 for v in _TOOLS_TIER.values() if v == "free")
N_CAP = sum(1 for v in _TOOLS_TIER.values() if v == "cap")
N_PAID = sum(1 for v in _TOOLS_TIER.values() if v == "paid")
assert N_FREE + N_CAP + N_PAID == len(TOOLS), \
    "lede tiers must sum to n_tools"


def bench_rows():
    """Latest v6 row per (model, arm)."""
    latest = {}
    with open(ROOT / "bench" / "results.jsonl", encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            # the table documents the v6 task only; v7 (harder, partial
            # results) lives in bench/FINDINGS.md — mixing harnesses would
            # silently change what the published ✅ means
            if r.get("harness") == "v6":
                latest[(r["model"], r["arm"])] = r
    rows = []
    for m in ("0.5b", "1.5b", "7b"):
        a = latest.get((m, "A"))
        b = latest.get((m, "B"))
        if a and b:
            rows.append((m, a["success"], b["success"],
                         a["tokens_in"] + a["tokens_out"],
                         b["tokens_in"] + b["tokens_out"]))
    return rows


BENCH = bench_rows()
assert BENCH, "no v6 bench rows yet — run the matrix first"
BENCH_ALL = all(b for _m, _a, b, _x, _y in BENCH)  # used for copy truth

# ------------------------------- translations

PACK_TITLE = {
    "en": {"core": "Core transforms", "repair": "Data repair & cleaning",
           "code": "Code editing", "dates": "Dates, cron & ICS",
           "numbers": "Numbers, units & money",
           "identity": "Hashes & identity", "checks": "Validators",
           "text": "Context & text", "design": "Color & design",
           "extract": "Extraction & selection", "logic": "Logic & ordering"},
    "fr": {"core": "Transforms de base", "repair": "Réparation de données",
           "code": "Édition de code", "dates": "Dates, cron & ICS",
           "numbers": "Nombres, unités & argent",
           "identity": "Hachage & identité", "checks": "Validateurs",
           "text": "Contexte & texte", "design": "Couleur & design",
           "extract": "Extraction & sélection", "logic": "Logique & ordre"},
    "pt": {"core": "Transformações centrais",
           "repair": "Reparação de dados", "code": "Edição de código",
           "dates": "Datas, cron & ICS",
           "numbers": "Números, unidades & dinheiro",
           "identity": "Hash & identidade", "checks": "Validadores",
           "text": "Contexto & texto", "design": "Cor & design",
           "extract": "Extração e seleção", "logic": "Lógica e ordem"},
}

TR =   {
 "en": {
  'meta.title': 'Mechacut — same request, same bytes',
  'meta.desc': 'Deterministic transforms for AI agents: 184 tools, three tiers, machine payments. No signup, no key, no storage.',
  'hero.plain': 'In plain words: Mechacut does the exact counting for AI assistants. Splitting a bill, a due date, a currency, a file — the assistant asks, Mechacut answers, and the answer is always the same. And when one assistant learns something new, every assistant gets it the same day.',
  'dev.h2': 'For developers & agents',
  'dev.intro': 'Everything above was true. Below is how: the full API, the tool catalogue, the schemas, the benchmarks, the pricing. No prose — references.',
  'nav.everyday': 'Everyday',
  'nav.tools': 'Bundles',
  'nav.numbers': 'Proof',
  'nav.vision': 'Vision',
  'nav.api': 'Contract',
  'pill': 'v{ver} · {n_tools} transforms · {n_recipes} recipes',
  'hero1': 'Meaning is learned.',
  'hero.why': '<strong>Why determinism?</strong> Because a right answer that changes on every run is not an answer — it is a dice roll. A machine that returns the same bytes for the same question makes agents auditable: every response carries its checksum, every error names the offending field, and what you test in the morning is what you ship at night.',
  'demo.title': 'ASK THE BENCH — live, keyless, same bytes every run',
  'demo.run': 'Run',
  'demo.hint': 'press Run — the answer below comes from the real endpoint, not a screenshot',
  'demo.err': 'network hiccup — the endpoint still answers: POST /api/v1/num/round',
  'hero2': 'Mechanics are known.',
  'hero3': 'Competence is not learned. It is served.',
  'lede': 'A suite of <strong>{n_tools} deterministic transforms</strong> for AI agents — {n_free} free forever, {n_cap} free under 32 KB then pay-per-call, {n_paid} machine-payable — plus {n_recipes} one-call recipes, free. The model stops guessing what a checksum can prove.',
  'bundles.h2': 'The catalogue',
  'bundles.creed': 'A model computes. A server knows.',
  'cat.search': 'search a tool or your problem…',
  'cat.hits': '~n~ of ~t~ tools',
  'panel.copy': 'copy curl',
  'panel.copied': 'copied',
  'panel.close': 'close',
  'panel.say': 'dis to your agent:',
  'panel.got': 'the server answered:',
  'nav.menu': 'menu',
  'bundles.intro': 'Same request, same bytes — every response carries its own sha256. Install one pack, or read the whole manifest in one request and let <code>GET /route</code> pick.',
  'tiers.h2': 'Three tiers, no accounts',
  'tiers.intro': 'Agents do not read pricing pages — so the price is in the protocol: a free route answers keyless, a capped route answers free under 32 KB, anything else gets an honest <code>402</code> with an x402 USDC-on-Base challenge, settled by a facilitator. Between a server and a robot, only prices and receipts exist.',
  'bench.h2': 'Benchmarks, or what we looked for:',
  'bench.creed': 'The wall is FORM, not size — and we priced the door.',
  'bench9.intro': 'One deliberately vague French sentence, six required fields — money sorted to 2 decimals, percents, unique dates, URL, email, total. Expectations hand-computed before any run. The server builds the card (/intent/card); the model relays one line and the answer never passes through it.',
  'bench9.with': 'with the intake card',
  'bench9.foot': 'The 0.5B row reproduced on an independent second pass. Three identical live calls returned one sha256. The autonomous variant (the model picks the tool itself, no card played by the harness) also scores 6/6. Seeds, scripts, failures: bench/results_v9.jsonl.\n',
  'bench10.intro': 'Eighteen tasks with ONE right answer each — GS1 check digits, a SHA-256, chained discounts, a money column that proves its own decimal comma. Two free LOCAL models, no API spend: the harness asserts every route it calls is free. Golds were computed from the published specs before any model ran.',
  'bench10.with': 'with one relay call',
  'bench10.foot': 'Naked failures reproduce on an independent second pass, 18/18 verdicts identical — at temp 0 a retry never converges, it repeats. Raw runs: bench/results_v10.jsonl, method: bench/FINDINGS-V10.md.\n',
  'bench.v23.sum': 'A 1.7B trained for agents solved {v23_chain}/{v23_chain_cells} chains naked for ${v23_cost} — our wall was TRAINING, not size; and the lock refused {v23_refused} right answers over their names.',
  'bench.v23.intro': 'The cross-family replication: the same 20 seeded problems, the same arms as v20, one model of another lineage (LFM3-1.7B, tri-hybrid, post-trained for tool calls). Nude {v23_n_all}/20, relayed {v23_s_all}/20, locked {v23_l_all}/20. Nothing here refutes v19: answering right once is not answering with the same byte thirty days running.',
  'bench.v23.arm': 'arm',
  'bench.v23.wins': 'right /20',
  'bench.v23.usd': 'cost',
  'bench.v23.foot': 'Raw: bench/results_v23_lfm3.jsonl · method: bench/FINDINGS-V23.md · $ at frozen per-token prices.\n',
  'bench.v20.sum': 'The wall is AIM: llama 8B went {v20_8b_s}→{v20_8b_l}/20 with a target lock; the 7B signed its first {v20_7b_l}/20.',
  'bench.v20.intro': 'The promise of v17, measured: the answer must name the quantity it returns. Nude, the 8B computed right and answered beside it — {v20_aside} of its misses carried another quantity of the chain; the lock converted {v20_aside_conv}. {v20_cells} cells, and the naked arm replays v15 exactly ({v20_replay}).',
  'bench.v20.model': 'model',
  'bench.v20.naked': 'naked',
  'bench.v20.locked': 'with the lock',
  'bench.v20.foot': 'Raw: bench/results_v20_target_lock.jsonl · method: bench/FINDINGS-V20.md.\n',
  'bench.g1': 'What they miss is executing, not thinking',
  'bench.g2': 'The wall is a SHAPE — and shapes are a training target',
  'bench.g3': 'No model in this bench says "I\'m not sure" — paying more doesn\'t dodge the shape',
  'bench.g4': 'Reading is the ceiling no tool breaks',
  'bench.g5': 'The real regime: thirty days of the same job',
  'bench.v11.sum': 'Fifteen hostile tasks: the 7B goes {v11_7b_nu} to {v11_7b_relay} relayed; the 8B {v11_8b_nu} to {v11_8b_relay}.',
  'bench.v11.foot': 'Raw: bench/results_v11.jsonl · method: bench/FINDINGS-V11.md',
  'bench.f5.sum': '{f5_wins}/{f5_cells} chain attempts with the fiche — criterion ≥19 PASSED; {f5_repairs} repaired by a named refusal; the 7B alone {f5_7b}.',
  'bench.f5.foot': 'Raw: bench/results_f5_accept.jsonl · method: bench/FINDINGS-F5.md',
  'bench.v13.sum': 'The negative result, published first: on real GSM8K the relay card falls to {v13_relay_05b}/20 for the 0.5B — asking the model for the decomposition still leaves it doing the decomposition.',
  'bench.v13.foot': 'Raw: bench/results_v13_gsm8k.jsonl · method: bench/FINDINGS-V13.md',
  'bench.v14.sum': 'Strict skill: {v14_breaks}/{v14_cells} protocol breaks — the class the form measures directly — while reading stays free.',
  'bench.v14.foot': 'Raw: bench/results_v14_skill.jsonl · method: bench/FINDINGS-V14.md',
  'bench.v22.sum': "Three frontier models answer {v22_nu} naked — one at {v22_best}, another at {v22_worst}. Through the frozen fiche: {v22_fiche}. Paying more doesn't change the shape.",
  'bench.v22.foot': 'Raw: bench/results_v22.jsonl · method: bench/FINDINGS-V22.md',
  'bench.v22b.sum': 'Five passes at agent temperature: {v22b_ok}/{v22b_cells} right — the SAME program twice: {v22b_stable}/14. The server: {v22b_shas} sha per problem.',
  'bench.v22b.foot': 'Raw: bench/results_v22b.jsonl · method: bench/FINDINGS-V22.md',
  'bench.v24.sum': 'Thirty days of the same CSV with a model that CAN do chains: {v24_sil}/{v24_days} days of empty answers after 8,192 reasoning tokens, {v24_ok} right, billed ${v24_usd}. The machine: {v24_m_ok} at $0.00.',
  'bench.f7.sum': "EN/PT copies of the seven chains: {f7_wins}/{f7_cells} — criterion ≥19 passed; {f7_rep} of them won by the named refusal. PT copy at 4/7 vs FR's 0/7 on the 0.5B: the reading ceiling belongs to model × language × form.",
  'bench.f7.foot': 'Raw: bench/results_f7_accept.jsonl · frozen criterion: bench/FINDINGS-F7.md',
  'bench.v24.foot': 'Raw: bench/results_v24_lfm3_30days.jsonl · the amendment lives in git history (run24 amendé)',
  'bench.v19.sum': '{v19_wins}/{v19_days} attempts right for the models — machine: {v19_m_ok}/{v19_m_days} days on one identical hash; {v19_drift} different outputs from one model in 30 days.',
  'bench.v19.intro': 'The same dirty CSV cleaned 30 days in a row. Six-rule spec, a gold file written BY HAND before the harness, a retry arm that only ever sees its own format — never the answer. Temperature 0.7: the real regime of agents, disclosed.',
  'bench.v19.arm': 'arm',
  'bench.v19.right': 'right days /30',
  'bench.v19.distinct': 'distinct outputs',
  'bench.v19.foot': 'Raw: bench/results_v19_csv_bill.jsonl · method + dollars: bench/FINDINGS-V19.md · replay: python bench/run19.py',
  'bench.v17.sum': 'Retry ×5 on a systematic miss: {v17_retry_wins}/{v17_retry_cells} chains fixed — the same mistake, ×5 the price.',
  'bench.v17.intro': 'Three arms, the same 20 fresh problems, every token counted: answer naked, retry five times, or hand the calculation to the server. Cells: {v17_cells}.',
  'bench.v17.nu': 'naked',
  'bench.v17.retry': 'retry ×5',
  'bench.v17.relay': 'server does it (ok · tokens/right)',
  'bench.v17.foot': 'Raw: bench/results_v17_tokens.jsonl · bench/FINDINGS-V17.md · replay: python bench/run17.py',
  'bench.v16.sum': "{v16_wrong} wrong answers in {v16_runs} runs — 'I'm not sure' said {v16_doubt} times.",
  'bench.v16.intro': 'Everyday word problems, freshly generated, each model asked to mark its own confidence. They failed the same way every time: confidently.',
  'bench.v16.foot': 'Raw: bench/results_v16_calibration.jsonl · bench/FINDINGS-V16.md · generator: bench/gen16.py (seeded, double oracle).',
  'bench.v15.sum': 'The wall is a SHAPE: {v15_alone_wins}/{v15_cells} chain attempts solved naked or retried — {v15_best_arm}/{v15_arm_cells} by the best server arm.',
  'bench.v15.intro': 'The full matrix: 5 transports × 4 free models × 20 seeded problems (400 cells), hypotheses committed BEFORE the first run, failed predictions published first.',
  'bench.v15.foot': 'Raw: bench/results_v15_matrix.jsonl · bench/FINDINGS-V15.md · replay: python bench/run15.py && python bench/score15.py',
  'bench.v12.sum': '{v12_zero} alone → {v12_hero} with one relay call. The zero becomes the hero.',
  'bench.v10.sum': 'One right answer each: {v10_alone} alone → {v10_server} relayed — at $0, audited by the harness itself.',
  'bench.v9.sum': 'One vague sentence, six keys: {v9_alone} → {v9_card} with the intake card.',
  'bench.v6.sum': 'The first matrix — naked vs relay. Every row, harness and failure: bench/FINDINGS.md.',
  'bench12.intro': "Ten exact calculations (7834×9217, 0.1+0.2, chained percentages…) × four FREE local models × three arms: answering naked, writing Python, or relaying one expression to math/calc. Scores shown; the code arm's answers are float, the relay's are exact — same table, different physics.",
  'bench12.code': 'writes Python',
  'bench12.relay': 'relays to Mechacut',
  'bench12.foot': 'The 8B fails RELAY on protocol babble, not math — which is why the intake card writes the line for it. The 0.5B invented 89000098 naked and posts 9/10 relayed at 0.2 s median. Raw: bench/results_v12.jsonl, method: bench/FINDINGS-V12.md.\n',
  'bench.intro': 'A frozen task (seed 20261120): dirty CSV + broken JSON + URL list → one canonical YAML, expected answer pinned by sha256. Same weak local model (Qwen 2.5, temperature 0), one arm alone, one arm driving Mechacut. We publish the failures too — the 0.5B fails both arms, and a capability ceiling is a result.',
  'bench.model': 'model',
  'bench.alone': 'alone',
  'bench.with': 'with mechacut',
  'bench.tokens': 'tokens consumed',
  'bench.foot': 'The 7B goes from 0 % to 100 % in a single pipeline call. Every run, every token, is in bench/results.jsonl.',
  'nav.build': 'Build',
  'nav.market': 'Market',
  'market.h2': 'They say it too',
  'market.creed': 'The big houses converged on the same sentence — only the delivery differs.',
  'build.h2': 'What you can build tonight',
  'build.intro': 'You have a free small model on your machine. Here are three things to make it do — the quoted lines are what you say to your agent, the answers below are what the server really returned. No account, no card, no prayer.',
  'build.r1.name': 'The tax-ID gate',
  'build.r1.say': '“Is my client’s VAT number FR40303265045 valid for the invoice?”',
  'build.r1.got': '{{ "valid": true, "algorithm": "EU VAT check-digit rule for FR (published)" }}',
  'build.r1.why': 'Alone, a 0.5B model computes check digits — and gets them wrong. Here the digits decide, so the invoice does not die at the accountant’s. Every country’s flavour lives on its own page: CNPJ for Brazil, SIREN and TVA for France.',
  'build.r2.name': 'The leak guard',
  'build.r2.say': '“Scan this log before I paste it into a chatbot.”',
  'build.r2.got': '2 findings → seed [SEED_PHRASE] and key [OPENAI_KEY_1]',
  'build.r2.why': 'The scan answers with positions, never the value; the mask never returns the key. The secret came here for safekeeping — it stays safe from us too.',
  'build.r3.name': 'The incident relay',
  'build.r3.say': '“relève les montants et dates de cette note d’incident” — said in French, to a 0.5B.',
  'build.r3.got': 'money [3200.00, 12450.75] · 6/6 keys in 320 tokens (alone: 0/6)',
  'build.r3.why': 'That is bench v9 verbatim: same task, same model, one relay line. Every run is in bench/results_v9.jsonl — replay it yourself.',
  'build.connect': 'Or skip the story and wire it now: paste this ONE line into ANY agent, even the smallest — it becomes the full manual:',
  'everyday.h2': 'For everyone',
  'everyday.open': 'Expand the proofs — real server outputs, no mockups.',
  'everyday.intro': "No code, no jargon. Twenty-eight things a person asks an agent on a Tuesday — every answer below is real server output, not a mockup.",
  'everyday.e1.name': 'Guest Wi-Fi, one scan',
  'everyday.e1.say': '“Turn our Wi-Fi into a QR so guests stop asking the password.”',
  'everyday.e2.name': 'The check, in words',
  'everyday.e2.say': '“Write $1,234.56 in words for the check — the bank rejects typos.”',
  'everyday.e3.name': 'IBAN before the wire',
  'everyday.e3.say': '“Did I copy this IBAN right? A bounced wire costs $45.”',
  'everyday.e4.name': 'Recipe to printable page',
  'everyday.e4.say': '“Make my recipe notes a clean page — I want a PDF for the fridge.”',
  'everyday.e5.name': 'Counting the days',
  'everyday.e5.say': '“How many days until our trip?”',
  'everyday.e6.name': 'Sale math the register will not do',
  'everyday.e6.say': '“Minus 30 %, then another 20 % — that is 50 % off, right?” It is 44 %.',
  'everyday.e7.name': 'A third of the cake, nothing rounded in the dark',
  'everyday.e7.say': '“This 6-serving cake, I want it for 2 — 400 g flour, 5 eggs?” 400 × 1/3 = 133 1/3 g exact, 135 g to weigh. The eggs are stated, not guessed.',
  'everyday.e8.name': 'Every other Tuesday, on the dot',
  'everyday.e8.say': '“Book club every other Tuesday at 7 — the next four dates?” Nov 3, 17, Dec 1, 15: every two weeks means SKIPPING the weeks between — and the skipped weeks are named, not guessed.',
  'everyday.e9.name': 'One foot, three right answers',
  'everyday.e9.say': '“EU 42 2/3 or 42.5 — which one am I?” Both charts round: the millimetre is exact, the half-size and third-size candidates are all printed, and the drift between systems is a stated number. Never one confident size.',
  'everyday.e10.name': 'Delayed flight — who owes me what',
  'everyday.e10.say': '“My flight landed 3 h 20 late — what am I actually owed?” The FLIGHT DATE picks the rule: before 2027-10-23 the old EC261 + case-law; on or after it, the new codified ‘EXCEEDING three hours’ table. Same facts either side of that line can pay differently. € or £, with the claim deadline as a real date.',
  'everyday.e11.name': 'Will my bag pass the gate',
  'everyday.e11.say': '“My bag is 40×18×12, flight in November 2027 — free under the seat? The FLIGHT DATE decides: the 2027 law caps the under-seat item at 40×30×15, nothing before it. Rotation counts — faces sorted, never the order you typed.',
  'everyday.e12.name': 'The two tariffs, one honest number',
  'everyday.e12.say': "“Plan A is cheaper per kWh, plan B is cheaper per month — when does A really win?” The crossover is (fixed gap × days) ÷ (rate gap) — and the exact fraction, not the web's rounded intermediate: 4,623⅓ kWh where the article says “about 4,623”. “Never” is also an answer, named, when one plan wins on both parts.",
  'everyday.e13.name': 'What a point is really worth',
  'everyday.e13.say': '“29,000 points for a $438 flight minus $5.60 taxes — how much is a point, really?” cpp = (cash − taxes) ÷ points × 100: the printed 1.49 hides the exact 1081/725 = 1.491034…, subtracted BEFORE dividing. And the floor that says take-it-or-pay-cash is yours, never a stale table.',
  'everyday.e14.name': 'The billed weight, both chains printed',
  'everyday.e14.say': '“Two carriers bill 6 kg and 5 kg for my 40×30×25 box — who is wrong?” Neither: 30 000 cm³ ÷ 5 000 = 6 exactly, ÷ 6 000 = 5 exactly — two divisors, one honest chain, each step named. And carrier tables ROT (USPS moved 166 → 139 in July 2026), so the divisor stays YOUR argument — never our memory.',
  'everyday.e15.name': 'The BOGO sign says 50 % — the bill does not',
  'everyday.e15.say': '“Buy one, get the second 50 % off — a $60 and a $40 hoodie, am I at −50, −25?” Neither: the % hits the CHEAPER item (published retail rule), so the pair is 80 of 100 = −20 %. Equal prices would be −25 %, BOGO free −50 %, and a −30 coupon on top gives −47.5, never 55 — percentages multiply.',
  'everyday.e16.name': 'The 500 g pack became 400 g — at the same price',
  'everyday.e16.say': '“−20 % on the package?” Not the shelf’s number: losing 1/5 of the product costs +1/4 per unit (20 % vs 25 % — two denominators, 500 and 400). “2 for $7” of 15 oz jars vs one 24 oz at $3.99? The eye says promo; the exact fraction: the single jar wins — the bundle pays 40.3509 % more per ounce. And “1 lb 4 oz” IS 20 oz: the coupon was right, the cashier wasn’t.',
  'everyday.e17.name': 'Thanksgiving turkey: the freezer clock AND the leftover window',
  'everyday.e17.say': "Two clocks, one turkey. Fridge math (8 Nov 2026 calendars disagree on one USDA table): in by = oven − longest tail, not before = −1-2 day rest; hours are ARGUMENTS, never the wall clock; done = 165 °F at the probe. Leftovers: 'eat by Mon 30 Nov' (NBC) vs 'three days, 72 h optimum' (ky3); FSIS contradicts itself on the freezer (2-6 vs 3-4 months) — returned: the UNION, two dated anchors, 2 h STRICT since cooked_at (2 h flat passes, 2 h 01 discards), day 4 = LAST_DAY, quality named quality.",
  'everyday.e18.name': 'Three dishes want the oven — the countdown, every conflict named',
  'everyday.e18.say': 'Eight 2026 timelines publish one dinner with rests of 20–60 min, 325 or 350 °F — none of the eight counts the 45-min preheat. Scheduled BACKWARDS from serve_at (an argument, never the wall clock): one oven, one dish, rests outside; a dish entering as the previous leaves at another setting = named conflict; bare 180 without unit refused; rest beyond 2 h hits the FSIS danger zone — leftovers rule.',
  'everyday.e19.name': 'Christmas ship-by dates — ≥2 sources per row, the outlier NAMED',
  'everyday.e19.say': 'Six holiday tables published Nov 13–21, 2026 disagree: one syndicate prints FedEx Saver, 2Day, Overnight a day late — silently: its target is Dec 25, not 24. Kept: rows where ≥2 sources agree, dissenter named WITH reason; weekdays derived from the cited calendar; UPS Ground refused (zone-dependent — no single date); no extrapolated year. as_of is an argument: « days left » is arithmetic, not a clock. Window dies Dec 23.',
  'everyday.e20.name': 'Holiday RETURN deadlines — ≥2 sources, provenance per row',
  'everyday.e20.say': "The shared January-31 headline is a lie of omission: Target's window closes Dec 24, Best Buy's member rule splits Dec 4, parcelmonitor republished last year's dates shifted by one as a 'likely pattern' while Seller Central published 2026 verbatim. Kept: rows with two concordant sources, provenance (published|press), the Day-1 convention named; single-source retailers refused WITH the candidate fact; 'whichever is later' never a guess — delivery date is an argument.",
  'everyday.e21.name': 'Is that crossed-out price LEGAL — the Omnibus 30-day rule, audited from your own history',
  'everyday.e21.say': "Legal reference: the LOWEST price of the previous 30 days (dir. 2019/2161 art. 6a) — a weekend promo LOWERS the reference even if the price rises after (CJEU C-330/23). 100 → 80 → 100 → 70 = 12.5 %, not 30 %. Commission sweep, March 2026: 30 % of 314 shops get it wrong; Spain fined up to 350,000 EUR. History in, reference and true % out — never fetches a price.",
  'everyday.e22.name': 'Price DROPPED after you paid — who owes what, by when',
  'everyday.e22.say': "You paid 100, the shop shows 80. No law forces a refund — the shops' own published guarantees do, and those windows are DATES: Target Dec 24, Best Buy Jan 15, Costco 30 days, Fnac-Darty the campaign itself (gift card, not cash), Amazon nothing. Paste purchase + drop dates, both prices — the machine returns verdict, claim deadline, amount, refund mode, source class per row. Never fetches a price.",
  'everyday.e23.name': 'The gift broke AFTER the return window — what does the LAW still owe you, to the day',
  'everyday.e23.say': "Christmas gift, delivered Dec 25, dies Jan 16: the goodwill window closed Jan 15; the press stops here. The statute doesn't. France: conformity 2 years from DELIVERY, hidden defects 2 from DISCOVERY, 20-year cap — three anchors, one word. UK: 30 days to reject, six months reversed burden (a PROOF rule, not a deadline), six years to sue — five in Scotland. Every answer dated from your one input; a page contradicting itself (refurbished, 24 vs 12): BOTH dates travel named. US/AU refused by name: no federal window; 'reasonable time' is not a date.",
  'everyday.e24.name': 'Can I shred this? — the UK drawer hides FOUR clocks',
  'everyday.e24.say': "“Six years” is ONE phrase for four dates: VAT counts from the date ON THE DOCUMENT (even for a future event — HMRC says so), a limited company from the END of the financial year, s.388 THREE years if private / SIX if plc from the date MADE, Self Assessment five years from a 31-Jan deadline, no document. Example replayed: 2022-23 return sent by 31-01-2024 → keep until 31-01-2029, shred from 1 February. The “or longer if” cases (late return, open check) come back BLOCKED, reason published — no invented date; two rules on one paper, the LONGER governs (CH15400, replayed after its 2026-11-23 update).",
  'everyday.e25.name': "The 'expired' gift voucher may be alive — Ireland counts from the BUY",
  'everyday.e25.say': "Ireland (Gift Vouchers Act 2019, replayed): printed expiry under FIVE YEARS from purchase is not voided — DEEMED REPLACED by five; law OVERRIDES paper (66B(1)(b)+(c)). JD Sports: one-year vouchers, ~€250,000 refunded in July after CCPC's 20-Nov call-in. A gift-card starts no clock: anchor = contract date, RECIPIENT holds every right (66B(10)). Leftover €1+ owed; the boundary conflict ships named: Act 'or more', CCPC FAQ 'more than'. France: NO statutory minimum; printed date contractual; the '30 years' rumour = real-property prescription, refused by name.",
  'everyday.e26.name': 'Sale dates: three tables — two formulas, zero in Luxembourg',
  'everyday.e26.say': "Three replayed calendars. France (arrete 27-May-2019): winter = 2nd Wednesday of January 8h, advanced when the 2nd falls after the 12th (2027: 6 Jan — the 9-Feb site lost the clause); summer = last Wed June, penultimate when the last falls after 28 (2027: 23 June); 4 weeks, start counted; seven derogations verbatim (Moselle alone 26 June 2021; winter 2021 SIX WEEKS; Guadeloupe 7 October; heatwaves 2023/2026 five weeks); 'ouvré' undefined: 2027 ships Mon 4, Sat 2 named. Belgium (art. VI.25 CDE): winter 3-31 Jan, from the 2ND when the 3rd is Sunday — lived 2016, next 2027 — SPF names the pause «du 2 décembre au 1er janvier», press: 3 December; summer 1-31 July, 30 June when Jul 1 is Sunday — lived 2018; corona: summer 2020 → 1-31 Aug; winter 2021 REPORTED to Mon 4, clause overruled, PROLONGED to 15 Feb by LOI — headlines: 14. Luxembourg (loi du 23-déc-2016, art. 1er § 4): NO formula — a decree dates BOTH periods EVERY year; ten acts 2018–2027 (winter 2026/2027: Sat 2 → Sat 30 January); two rectifications — 2017: weekday LABEL only, 2023: the real BOUNDARY (the JO printed a Sunday the press never gave); the 2021 chain: three acts, one dead. Beyond the last act: refused, never prophesied. CE 20-May-2026: fines annulled, dates stand.",
  'everyday.e27.name': 'Received Tuesday — until WHEN can you change your mind',
  'everyday.e27.say': "The law hands out its own calendar: section 6 replayed verbatim from legifrance 25-Nov — L221-18 names the start (receipt, end of service); L221-19: next day = day 1, midnight ends day 14; Sat/Sun/holiday push to first business day (OUR L3133-1 table). Delivery 24 Nov → 8 Dec; Sat 5 → Mon 7; 8 May → Mon 11. Missing information buys +12 months (L221-20); late delivery restarts 14 days. 13 exceptions by clause (made-to-order, sealed hygiene, auctions). Sales, second-hand: the right still runs (F10485). In-store: NO automatic right — refused by name. The shop's extra weeks: another clock, /shop/return-deadline.",
  'everyday.e28.name': 'They fought about arithmetic — they had two graphs',
  'everyday.e28.say': "A fronted 1,375.00, C 865.00, B nothing; equal shares; C tells B 'the barbecue is on me.' A demands 628.33, B offers 458.33 — both answers right, DIFFERENT GRAPHS. Net: C forgives only the 118.34 owed to them → B wires A 628.33, ONE transfer, proven minimum. Itemized: the forgiveness kills the B→C edge; B pays A 458.33, C bears 288.33. compare numbers the gap; cents close where the thread's 746.67×3 did not.",
  'everyday.e29.name': 'Same rent, four conventions — no calculator picks for you',
  'everyday.e29.say': "Move out the 18th, $1,000 month: the posted formula '1000/30 = 33.33 × 18 = 600' rounded SILENTLY twice — the landlord's own way gives 599.94 (9sqw2j). Move in Jan 15 of a 31-day month: the office splits by '/30 days, REGARDLESS of actual number of days' — 566.67; a neighbour by /31 — 548.39 (r/Landlord 1hitzjq). Lease ends at NOON the 12th: 12 billed, 11.5 pleaded, 12-or-11 published (cevz6l). prorate names basis cycle|month30|year365, order, bound; compare renders BOTH with the signed delta; a moment in a date is refused, the two whole-day counts shown. Local law never encoded.",
  'everyday.e30.name': 'Same salary, many hourly rates — the stub never says',
  'everyday.e30.say': "52,000 a year: ÷2,080 = 25.00 (r/Payroll's “typically” — in every comment, named by no calculator); ÷2,087 = 24.92 — that is 5 USC 5504(b) word for word (‘divide the annual rate by 2,087’, ‘nearest cent, counting one-half and over’); the r/ATC stub “20 cents off” IS this law. Order bites: round the rate first, ×80 = 1,993.60; divide the year by 26 = 2,000.00 — −6.40 a pay, −166.40 a year, rendered as a signed pair. Biweekly ÷26 vs semimonthly ÷24 are TWO clocks (2,000.00 vs 2,166.67). And 2027 has 53 Fridays: 27 every-other-week paydays (r/IRS_Source) — counted, not prophesied. payscale names each denominator and its citation; 365 refused by name; YOUR divisor stays an argument (1,820, 2,640 — law never encoded); never an average, never a fetch.",
  'nav.kit': 'Kit',
  'kit.h2': 'The suite on your disk',
  'kit.creed': 'The protocol is not the transport — it is the birth certificate of the tool.',
  'kit.intro': 'The free transforms are not only an API. They are a suite: an agent can install them on its own machine, call them locally, and — the part no marketplace does — build new tools on the same gates. curl becomes kit call; a repeated task becomes a proposed contract; a proposal becomes a published tool only if its golds were drawn before its code.',
  'kit.c1.sum': 'Install — the base suite on the machine',
  'kit.c1.foot': 'Verified sha, no daemon, no auto-update, no network inside the engine. Stateless is the contract: the human decides when the kit moves.',
  'kit.c2.sum': 'Call — consult before acting',
  'kit.c2.foot': 'The skill asks the directory first. Same canon, same refusals, same golds as the datacenter — what is verified here is verified there, byte for byte.',
  'kit.c3.sum': 'Build — the second time, write the tool',
  'kit.c3.foot': 'Golds drawn BEFORE the code, AST-gate, pin-gate. Status: proposed, attested, network-verified — the kit grows locally, the proof grows back to the network. A lesson is a proposal; the bench locks it.',
  'kit.howto.p1': 'Install the skill: <code>curl https://mechacut.studio/SKILL-MINI.md -o SKILL.md</code> — drop the file into your agent (CLAUDE.md, AGENTS.md, skills/). ~1,000 tokens, sized for small models.',
  'kit.howto.p2': 'Make it consult first: before acting, the agent describes the problem in one sentence to /route/resolve — the directory returns the tool that already exists, or says none does.',
  'kit.howto.p3': 'Call: stateless POSTs, keyless on free; the response carries its sha256, the refusal carries field + expected + example. Everything on this page works right now: one line installs the skill file, the directory answers, the free calls need no key.',
  'kit.plain.sum': 'Not a developer? No problem — we translate.',
  'kit.plain.p1': 'Open your usual AI assistant (Claude, ChatGPT, Grok, Copilot…).',
  'kit.plain.p2': 'Send it this message: "Read https://mechacut.studio/SKILL-MINI.md and follow it for my calculations." Nothing to install, nothing to pay, no account.',
  'kit.plain.p3': 'Then ask your real task: "30% then 20% discount — what is that really?", "how many days overdue is this invoice?" The numbers no longer come from its head — they come from the suite, and they are the same for everyone.',
  'kit.plain.p4': 'Did you ask for something the suite cannot do? Propose it " in plain words on the same page — every proposal is public, its verdict too: shipped, waiting, or refused with the reason named, at /proposals.',
  'kit.dev.sum': 'For developers — three lines, no account',
  'kit.propose': 'Propose a tool: POST /api/v1/agent/propose — a contract, never code; duplicate named, evidence shown, eligibility returned as a commit-ready blob. Nothing stored server-side. Protocol skill: /SKILL-KIT.md',
  'bench.d82.sum': 'Tool-call traces, judged: the same agent motion was re-emitted identically 0 out of 14 times (V22b) and a retry multiplied the bill ×4 without converging (V17) — loop/doom-check now says DOOM, CYCLIC or STORM on canonical bytes, thresholds named.',
  'bench.d82.foot': 'Identity on canonical (tool, args): key order never hides a loop. Two identical calls are not a loop — the threshold is stated, never guessed. All signals reported, the verdict is the most severe. Sources: bench/FINDINGS-V17.md · run22b.',
  'bench.e76.sum': 'The bench judge became a route: eval/compare returns OK or WRONG with divergences named — 2.5 versus "2.50" is never a disagreement, floats are never an argument.',
  'bench.e76.foot': 'Rule born from the V2 judge incident (it copied its own expectation): same quantity is never a divergence; a different quantity is named by pointer, kind, expected, got. Exact Decimal, never float.',
  'bench.a79.sum': 'Policy as closed grammar: check/allowlist returns ALLOW, DENY or AMBIGUOUS — the most specific rule wins, ties go to the human, silence never authorizes.',
  'bench.a79.foot': "A regex-shaped action is refused, not evaluated: a gate that interprets is a backdoor. Exact Decimal amounts, ISO currency table, default deny true. Same law as the directory's R3, another domain.",
  'x402.h2': 'Machine payments',
  'x402.p1': 'The paying path is four bytes of protocol: the server answers <code>402</code> with requirements; the agent signs an EIP-3009 USDC transfer; a facilitator verifies and settles; the response replays proof in <code>X-PAYMENT-RESPONSE</code>. The server holds no keys.',
  'x402.p2': 'Replayed payments are refused. Errors on paid routes stay free. The ledger of every refusal is public: <a href="/misses.json">/misses.json</a>.',
  'x402.bankr': 'Second home: four paid transforms on <a href="https://bankr.bot">Bankr</a> x402 Cloud — same code paths, same sha256: <a href="https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/chart_from_data">chart</a> &middot; <a href="https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/reshape_json">reshape</a> &middot; <a href="https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/validate_json">validate</a> &middot; <a href="https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/csv_join">csv-join</a>. The rest: only here, free tier included.',
  'vision.h2': 'Why determinism, why now',
  'vision.p1': 'A large language model is a machine that approximates. Ask it what <code>sha256("abc")</code> is and it will answer confidently, fluently, and wrong. Ask it to re-clean the same CSV every day and it will bill you in tokens to re-derive what a function returns in milliseconds — with the same bytes every time.',
  'vision.p2': 'The Apollo guidance computer had 4 KB of RAM. It landed humans because the math was never asked to improvise: constants were computed once, on the ground, in cold blood, then frozen into core rope memory.',
  'vision.quote': 'Determinism was coded the first time to send us to the moon. Determinism will send AI to work.',
  'nav.network': 'Network',
  'network.h2': 'The catalogue is fed by agents, judged by bytes.',
  'network.creed': 'One agent learns. All agents know.',
  'network.intro': 'The door is an endpoint, not a support ticket: POST /api/v1/agent/propose — five fields, closed grammar, a contract and never code. Every verdict lands in a public append-only registry.',
  'network.ask.sum': 'THE ASK — five fields, no code',
  'network.ask.body': 'name, purpose, examples (input → expected), why, source (your handle or URL). The server answers with a named verdict — ELIGIBLE, SUSPECT-DUPLICATE, DUPLICATE-OF — and a blob ready to commit. Nothing is stored server-side: the registry lives in git, append-only.',
  'network.verdict.sum': 'THE VERDICT — the same judge for every model',
  'network.verdict.body': 'Accepted means the same doors this house passes for itself: hand-traced golds before code, pins, AST-gate, green suite. The judge is third-party and byte-exact — the same sha proves it for Claude and for Qwen. A refusal names itself: an outcome of the protocol, not a failure.',
  'network.loop.sum': 'THE LOOP — one learns, all know',
  'network.loop.body': 'A shipped contract is one call every agent in the network gets, hashed, from that day. The first external proposer is credited in the registry row. The 50/50 split is decided and the splitter factory is live on Base — splits run on-chain, anyone can check.',
  'network.proof': 'Entries shipped in the public registry — arrivals, verdicts and refusals, row by row',
  'vision.p3': 'Mechacut is that frozen math for agents: closed vocabularies, contracts that refuse what is outside the table, errors that name the expected shape — the error is the repair prompt. Meaning stays with the model. Mechanics move here.',
  'contract.h2': 'The contract',
  'x402.sum': 'How a machine pays — 402, EIP-3009, facilitator, proof header',
  'vision.sum': 'Why determinism, why now — Apollo, 4 KB, and the dice',
  'contract.sum': 'The five promises, verbatim',
  'contract.li1': 'Same request → same bytes, sha256 on every response',
  'contract.li2': 'No signup, no API key, no rate wall below 30 req/min',
  'contract.li3': 'No storage: the only state is a 1-minute window, a 60-minute ledger and a payment-nonce replay set',
  'contract.li4': 'Closed vocabularies — everything outside the table is refused, named, pointed at its expected shape',
  'contract.li5': 'Errors that repair: field, message, expected, always',
  'contract.li6': 'x402 machine payments: USDC on Base, facilitator verified, zero human in the loop',
  'agents.line': 'Speak agent: MCP tools, GET /agent/manifest (the whole suite in one request), GET /route?q=…, POST /api/v1/pipeline.',
  'agents.hint': 'install one pack',
  'footer.family': 'Mechacut is part of the C.V. family — see moovicut.',
 },
 "fr": {
  'meta.title': 'Mechacut — même requête, mêmes octets',
  'meta.desc': 'Transformations déterministes pour agents IA : 184 outils, trois paliers, paiements machine. Sans inscription, sans clé, sans stockage.',
  'hero.plain': 'En mots simples : Mechacut fait les comptes exacts des assistants. Facture à partager, échéance, devise, fichier — l’assistant demande, Mechacut répond, toujours pareil. Et quand un assistant apprend quelque chose, tous le savent le jour même.',
  'dev.h2': 'Pour les développeurs & agents',
  'dev.intro': 'Tout ce qui précède est vrai. En dessous, le comment : l’API complète, le catalogue, les schémas, les benchs, les prix. Plus de prose — des références.',
  'nav.everyday': 'Quotidien',
  'nav.tools': 'Bundles',
  'nav.numbers': 'Preuves',
  'nav.vision': 'Vision',
  'nav.api': 'Contrat',
  'pill': 'v{ver} · {n_tools} transformations · {n_recipes} recettes',
  'hero1': "Le sens s'apprend.",
  'hero.why': "<strong>Pourquoi le déterminisme ?</strong> Une réponse juste qui change à chaque exécution EST un dé. Même question, mêmes octets : l'agent devient auditable — chaque réponse porte son empreinte, chaque erreur nomme le champ. Testé le matin, vendu le soir.",
  'demo.title': 'DANS LE BANC — en direct, sans clé, mêmes octets à chaque appel',
  'demo.run': 'Exécuter',
  'demo.hint': "exécutez — la réponse vient du vrai endpoint, pas d'une capture",
  'demo.err': "réseau hésitant — l'endpoint répond : POST /api/v1/num/round",
  'hero2': 'La mécanique se sait.',
  'hero3': "La compétence ne s'apprend pas. Elle se sert.",
  'lede': "Chaque réponse est la sortie réelle d'un endpoint GET, figée à la build. Aucune ligne touchée par un humain, aucune générée à la volée. Les pannes sont épinglées aussi, avec leur code. Des nombres, pas des promesses — vérifiables à l'œil.",
  'bundles.h2': 'Le catalogue',
  'bundles.creed': 'Un modèle calcule. Un serveur sait.',
  'cat.search': 'chercher un outil ou votre problème…',
  'cat.hits': '~n~ outils sur ~t~',
  'panel.copy': 'copier curl',
  'panel.copied': 'copié',
  'panel.close': 'fermer',
  'panel.say': 'dis à ton agent :',
  'panel.got': 'le serveur a répondu :',
  'nav.menu': 'menu',
  'bundles.intro': 'Même requête, mêmes octets — chaque réponse porte son sha256. Installez un pack, ou lisez le manifeste entier en une requête et laissez <code>GET /route</code> choisir.',
  'tiers.h2': 'Trois paliers, zéro compte',
  'tiers.intro': "Les agents ne lisent pas les pages de tarifs — le prix est dans le protocole : route gratuite sans clé, plafonnée sous 32 Ko, sinon <code>402</code> honnête, défi x402 USDC sur Base réglé par facilitateur. Entre serveur et robot : des prix et des reçus.",
  'bench.h2': 'Benchmarks, ou ce que nous cherchions :',
  'bench.creed': "Le mur, c'est la FORME, pas la taille — et nous avons chiffré la porte.",
  'bench9.intro': "Phrase floue volontairement, six champs requis — montants à 2 décimales, pourcentages, dates uniques, URL, email, total. Attentes calculées à la main avant exécution. Serveur construit la fiche (/intent/card) ; relais n'écrit qu'une ligne — la réponse ne le traverse jamais.",
  'bench9.with': "avec la fiche d'intention",
  'bench9.foot': "La ligne 0.5B reproduite au second passage indépendant. Trois appels live identiques → un seul sha256. La variante autonome (le modèle choisit l'outil) marque aussi 6/6. Graines, scripts, échecs : bench/results_v9.jsonl.\n",
  'bench10.intro': "Dix-huit tâches à réponse UNIQUE — contrôles GS1, SHA-256, remises en cascade, colonne prouvant sa virgule. Deux modèles gratuits LOCAUX, zéro API : le harnais vérifie chaque route appelée gratuite. Réponses justes calculées sur specs publiées, AVANT tout modèle.",
  'bench10.with': 'avec un seul appel-relais',
  'bench10.foot': "Les échecs nus se reproduisent à l'identique au second passage indépendant : 18/18 verdicts inchangés — à temp 0, recommencer ne converge pas, ça répète. Brutes : bench/results_v10.jsonl, méthode : bench/FINDINGS-V10.md.\n",
  'bench.v23.sum': "Un 1,7 B entraîné pour les agents résout {v23_chain}/{v23_chain_cells} chaînes à nu pour ${v23_cost} — le mur était l'ENTRAÎNEMENT, pas la taille ; le verrou a refusé {v23_refused} bonnes réponses pour leurs noms.",
  'bench.v23.intro': "Deux suites publiées le même jour, six tâches chacune : même 0.5B local, nu contre relayé. Scores = compteurs bruts du harnais, zéro retouche ; les échecs des deux bras restent au tableau. Le serveur construit la fiche ; le relais n'écrit qu'une ligne — la réponse ne le traverse jamais.",
  'bench.v23.arm': 'bras',
  'bench.v23.wins': 'justes /20',
  'bench.v23.usd': 'coût',
  'bench.v23.foot': 'Brut : bench/results_v23_lfm3.jsonl · méthode : bench/FINDINGS-V23.md · $ aux tarifs par token gelés.\n',
  'bench.v20.sum': 'Le mur est une CIBLE : le llama 8B passe de {v20_8b_s} à {v20_8b_l}/20 avec le verrou de cible ; le 7B signe son premier {v20_7b_l}/20.',
  'bench.v20.intro': "Promesse v17 mesurée : la réponse nomme la quantité rendue. Nu, le 8B calculait juste et répondait à côté — {v20_aside} de ses fautes portaient une autre quantité de la chaîne ; le verrou en a converti {v20_aside_conv}. {v20_cells} cellules ; le bras nu rejoue v15 à l'identique ({v20_replay}).",
  'bench.v20.model': 'modèle',
  'bench.v20.naked': 'nu',
  'bench.v20.locked': 'avec verrou',
  'bench.v20.foot': 'Brut : bench/results_v20_target_lock.jsonl · méthode : bench/FINDINGS-V20.md.\n',
  'bench.g1': "Ce qu'ils ratent n'est pas de réfléchir — c'est d'exécuter",
  'bench.g2': "Le mur est une FORME — et les formes sont un objectif d'entraînement",
  'bench.g3': "Aucun modèle de ce banc ne dit « je ne suis pas sûr » — payer plus n'esquive pas la forme",
  'bench.g4': "La lecture est le plafond qu'aucun outil ne franchit",
  'bench.g5': 'Le régime réel : trente jours du même job',
  'bench.v11.sum': 'Quinze tâches hostiles : le 7B passe de {v11_7b_nu} à {v11_7b_relay} en relais ; le 8B de {v11_8b_nu} à {v11_8b_relay}.',
  'bench.v11.foot': 'Brut : bench/results_v11.jsonl · méthode : bench/FINDINGS-V11.md',
  'bench.f5.sum': '{f5_wins}/{f5_cells} tentatives en chaîne avec la fiche — critère ≥19 PASSÉ ; {f5_repairs} réparées par un refus nommé ; le 7B seul {f5_7b}.',
  'bench.f5.foot': 'Brut : bench/results_f5_accept.jsonl · méthode : bench/FINDINGS-F5.md',
  'bench.v13.sum': "Résultat négatif, publié en premier : sur GSM8K réel la fiche-relais s'effondre à {v13_relay_05b}/20 pour le 0.5B — demander la décomposition au modèle, c'est encore la lui laisser faire.",
  'bench.v13.foot': 'Brut : bench/results_v13_gsm8k.jsonl · méthode : bench/FINDINGS-V13.md',
  'bench.v14.sum': 'Skill stricte : {v14_breaks}/{v14_cells} ruptures de protocole — la classe que la forme mesure directement — la lecture, elle, reste libre.',
  'bench.v14.foot': 'Brut : bench/results_v14_skill.jsonl · méthode : bench/FINDINGS-V14.md',
  'bench.v22.sum': "Trois modèles frontière, {v22_nu} justes nus — l'un {v22_best}, l'autre {v22_worst}. Par la fiche gelée : {v22_fiche}. Payer plus ne change pas la forme.",
  'bench.v22.foot': 'Brut : bench/results_v22.jsonl · méthode : bench/FINDINGS-V22.md',
  'bench.v22b.sum': 'Cinq passes au régime des agents : {v22b_ok}/{v22b_cells} justes — le MÊME programme deux fois : {v22b_stable}/14. Le serveur : {v22b_shas} sha par problème.',
  'bench.v22b.foot': 'Brut : bench/results_v22b.jsonl · méthode : bench/FINDINGS-V22.md',
  'bench.v24.sum': 'Trente jours sur le même CSV, un modèle QUI SAIT les chaînes : {v24_sil}/{v24_days} jours de réponse vide après 8 192 tokens de raisonnement, {v24_ok} justes, facturés ${v24_usd}. La machine : {v24_m_ok} à 0,00 $.',
  'bench.f7.sum': 'Sept chaînes recopiées EN/PT : {f7_wins}/{f7_cells} — critère ≥19 PASSÉ ; {f7_rep} gagnées par le refus nommé. Le 0.5b copie 4/7 en PT, 0/7 en FR : le plafond de lecture est modèle × langue × forme.',
  'bench.f7.foot': 'Brut : bench/results_f7_accept.jsonl · critère gelé : bench/FINDINGS-F7.md',
  'bench.v24.foot': "Brut : bench/results_v24_lfm3_30days.jsonl · l'amendement est dans l'historique git (run24 amendé)",
  'bench.v19.sum': '{v19_wins}/{v19_days} tentatives justes pour les modèles — machine : {v19_m_ok}/{v19_m_days} jours sur un même octet ; {v19_drift} sorties différentes pour un seul modèle en 30 jours.',
  'bench.v19.intro': 'Le même CSV sale nettoyé 30 jours de suite. Spéc à six règles, gold ÉCRIT À LA MAIN avant le banc, un bras retry qui ne voit que sa forme — jamais la réponse. Température 0,7 : le régime réel des agents, publié.',
  'bench.v19.arm': 'bras',
  'bench.v19.right': 'jours justes /30',
  'bench.v19.distinct': 'sorties distinctes',
  'bench.v19.foot': 'Brut : bench/results_v19_csv_bill.jsonl · méthode + dollars : bench/FINDINGS-V19.md · rejeu : python bench/run19.py',
  'bench.v17.sum': 'Retry ×5 sur une erreur systématique : {v17_retry_wins}/{v17_retry_cells} chaînes réparées — la même faute, 5× le prix.',
  'bench.v17.intro': 'Trois bras, les mêmes 20 problèmes neufs, chaque token compté : répondre nu, recommencer cinq fois, ou donner le calcul au serveur. Cellules : {v17_cells}.',
  'bench.v17.nu': 'nu',
  'bench.v17.retry': 'retry ×5',
  'bench.v17.relay': 'serveur (ok · tokens/juste)',
  'bench.v17.foot': 'Brut : bench/results_v17_tokens.jsonl · bench/FINDINGS-V17.md · rejeu : python bench/run17.py',
  'bench.v16.sum': '{v16_wrong} fautes en {v16_runs} runs — « je ne suis pas sûr » dit {v16_doubt} fois.',
  'bench.v16.intro': 'Des problèmes du quotidien générés à la volée, chaque modèle prié de marquer sa confiance. Ils ont échoué toujours de la même façon : avec assurance.',
  'bench.v16.foot': 'Brut : bench/results_v16_calibration.jsonl · bench/FINDINGS-V16.md · générateur : bench/gen16.py (seedé, double oracle).',
  'bench.v15.sum': 'Le mur a une FORME : {v15_alone_wins}/{v15_cells} tentatives en chaîne nues ou en retry — {v15_best_arm}/{v15_arm_cells} avec le meilleur bras serveur.',
  'bench.v15.intro': 'La matrice complète : 5 transports × 4 modèles gratuits × 20 problèmes seedés (400 cellules) ; hypothèses commitées AVANT la première cellule, prédictions ratées publiées en premier.',
  'bench.v15.foot': 'Brut : bench/results_v15_matrix.jsonl · bench/FINDINGS-V15.md · rejeu : python bench/run15.py && python bench/score15.py',
  'bench.v12.sum': '{v12_zero} seul → {v12_hero} avec un seul relais. Le zéro devient héros.',
  'bench.v10.sum': 'Une seule bonne réponse chacun : {v10_alone} seul → {v10_server} relayé — à 0 $, audité par le banc lui-même.',
  'bench.v9.sum': "Une phrase vague, six clés : {v9_alone} → {v9_card} avec la carte d'intention.",
  'bench.v6.sum': 'La première matrice — nu vs relais. Chaque ligne, chaque harnais, chaque échec : bench/FINDINGS.md.',
  'bench12.intro': "Dix calculs exacts (7834×9217, 0.1+0.2, pourcentages en chaîne…) × quatre modèles locaux GRATUITS × trois bras : répondre nu, écrire du Python, relayer vers math/calc. Même tableau, deux physiques : le bras code rend du flottant, le relais de l'exact.",
  'bench12.code': 'écrit du Python',
  'bench12.relay': 'relais Mechacut',
  'bench12.foot': "Le 8B échoue au RELAIS sur le babil protocole, pas sur les maths — la fiche d'intention écrit la ligne. Nu, le 0.5B inventait 89000098 ; relayé, il sort 9/10 en 0,2 s médian. Brut : bench/results_v12.jsonl, méthode : bench/FINDINGS-V12.md.\n",
  'bench.intro': 'Tâche gelée (seed 20261120) : CSV sale + JSON cassé + URLs → un YAML canonique, attendu épinglé sha256. Même modèle local faible (Qwen 2.5, température 0), un bras nu, un bras avec Mechacut. Échecs publiés — le 0.5B échoue aux deux bras ; un plafond de capacité est un résultat.',
  'bench.model': 'modèle',
  'bench.alone': 'seul',
  'bench.with': 'avec mechacut',
  'bench.tokens': 'tokens consommés',
  'bench.foot': 'Le 7B passe de 0 % à 100 % en un seul appel pipeline. Chaque exécution, chaque token, est dans bench/results.jsonl.',
  'nav.build': 'Construire',
  'nav.market': 'Eux aussi',
  'market.h2': 'Ils le disent aussi',
  'market.creed': 'Les grandes maisons ont convergé sur la même phrase — seule la façon de la livrer diffère.',
  'build.h2': 'Ce que tu peux construire ce soir',
  'build.intro': 'Un petit modèle gratuit sur ta machine. Trois choses à lui faire faire — phrases citées = celles dites à l’agent, réponses = celles du serveur, rendues. Pas de compte, pas de carte, pas de prière.',
  'build.r1.name': 'Le contrôle de TVA (France)',
  'build.r1.say': '« Le numéro de TVA de mon client, FR40303265045, est-il valide pour la facture ? »',
  'build.r1.got': '{{ "valid": true, "algorithm": "EU VAT check-digit rule for FR (published)" }}',
  'build.r1.why': 'Seul, un 0.5B « calcule » la clé de contrôle — et se trompe. Ici les chiffres décident : la facture ne meurt pas chez le comptable.',
  'build.r2.name': 'Le garde-fuite',
  'build.r2.say': '« Scanne ce log avant que je le colle dans un chatbot. »',
  'build.r2.got': '2 findings → graine [SEED_PHRASE] et clé [OPENAI_KEY_1]',
  'build.r2.why': 'Le scan répond des positions, jamais la valeur ; le masque ne rend jamais la clé. Le secret est venu ici — protégé même de nous.',
  'build.r3.name': 'Le relai d’incident',
  'build.r3.say': '« relève les montants et dates de cette note d’incident » — dit en français,à un 0.5B.',
  'build.r3.got': 'money [3200.00, 12450.75] · 6/6 en 320 tokens (seul : 0/6)',
  'build.r3.why': 'C’est le bench v9 à l’identique : même tâche, même modèle, une ligne de relai. Toutes les exécutions : bench/results_v9.jsonl — rejoue-les.',
  'build.connect': "Ou branche-le tout de suite : colle CETTE ligne dans n'importe quel agent, même le plus petit — elle devient le manuel complet :",
  'everyday.h2': 'Pour tout le monde',
  'everyday.open': 'Dérouler les preuves — sorties réelles du serveur, pas des maquettes.',
  'everyday.intro': "Pas de code. Vingt-huit choses qu'un humain sans IDE règle en un tour et vérifie à l'œil.",
  'everyday.e1.name': 'Wi-Fi invités, un scan',
  'everyday.e1.say': '« Transforme le Wi-Fi en QR pour que les invités arrêtent de demander le mot de passe. »',
  'everyday.e2.name': 'Le chèque, en lettres',
  'everyday.e2.say': '« Écris 1 234,56 € en toutes lettres pour le chèque — la banque refuse les approximations. »',
  'everyday.e3.name': 'IBAN avant le virement',
  'everyday.e3.say': "« J'ai bien recopié cet IBAN ? 60 € de frais si le virement rebondit. »",
  'everyday.e4.name': 'Recette en page imprimable',
  'everyday.e4.say': '« Mets mes notes de recette en page propre — je veux un PDF pour le frigo. »',
  'everyday.e5.name': 'Compter les jours',
  'everyday.e5.say': '« Combien de jours avant les vacances ? »',
  'everyday.e6.name': 'Le compte que la caisse ne fera pas',
  'everyday.e6.say': '« -30 % puis -20 %, ça fait -50 %, non ? » En fait -44 %.',
  'everyday.e7.name': 'Un tiers du gâteau, sans arrondi caché',
  'everyday.e7.say': '« Mon gâteau pour 6, je le veux pour 2 — 400 g de farine, 5 œufs ? » 400 × 1/3 = 133 1/3 g exacts, peser 135 g. Les œufs sont dits, pas devinés.',
  'everyday.e8.name': "Un mardi sur deux, à l'heure",
  'everyday.e8.say': 'Club de lecture un mardi sur deux à 19 h — les 4 prochaines dates ? 3 et 17 nov., 1ᵉʳ et 15 déc. : quinze jours veut dire SAUTER les semaines du milieu — le moteur les nomme.',
  'everyday.e9.name': 'Un pied, trois bonnes réponses',
  'everyday.e9.say': 'EU 42⅔ ou 42,5 ? Les deux tableaux arrondissent : millimètre exact, candidats demi et tiers écrits, dérive entre systèmes dite en nombre — jamais un numéro confiant.',
  'everyday.e10.name': 'Vol retardé — qui me doit quoi',
  'everyday.e10.say': "Vol retardé 3 h 20 — la DATE DU VOL choisit la règle : avant le 23 oct. 2027 l'ancien EC261 + jurisprudence, après la table « PLUS DE trois heures ». Mêmes faits, réponses différentes. € ou £, délai de recours en vraie date.",
  'everyday.e11.name': 'Mon sac passera-t-il la porte',
  'everyday.e11.say': "Sac 40×18×12, vol nov. 2027 — la DATE DU VOL décide : la règle 2027 plafonne le sous-siège à 40×30×15, avant rien n'est fixé. Rotation compte — faces triées, jamais l'ordre tapé.",
  'everyday.e12.name': 'Deux tarifs, un seul chiffre honnête',
  'everyday.e12.say': "La bascule = (écart de fixe × jours) ÷ (écart de prix), fraction EXACTE : 4 623⅓ kWh là où l'article écrit « environ 4 623 ». « Jamais » est une réponse quand un plan gagne des deux côtés.",
  'everyday.e13.name': 'Ce que vaut vraiment un point',
  'everyday.e13.say': "29 000 points, vol à 438 € moins 5,60 € de taxes : le 1,49 affiché cache l'exact 1081/725 = 1,491034… ; soustraction AVANT division ; VOTRE plancher décide.",
  'everyday.e14.name': 'Le poids vraiment facturé, les deux chaînes imprimées',
  'everyday.e14.say': "Deux transporteurs : 6 kg et 5 kg pour la même boîte 40×30×25 — personne n'a tort : 30 000 cm³ ÷ 5 000 = 6, ÷ 6 000 = 5 pile. Les tables transporteurs POURRISSENT (USPS 166→139, juillet 2026) : le diviseur reste VOTRE argument.",
  'everyday.e15.name': "L'affiche dit 50 % — la note, jamais",
  'everyday.e15.say': 'Deux sweats à 60 € et 40 €, « deuxième à −50 % » : ni 50 ni 25 — la remise porte sur le MOINS CHER (règle publiée), la paire rend 80/100 = −20 %. À prix égaux −25 %, BOGO gratuit −50 %, coupon −30 % par dessus −47,5 %, jamais 55.',
  'everyday.e16.name': 'Le 500 g est devenu 400 g — au même prix',
  'everyday.e16.say': "Perdre 1/5 du produit (500→400 g, même étiquette) = +1/4 au kilo — 20 % contre 25 %, deux dénominateurs. « 2 pour 7 $ » de pots de 15 oz perd 40,3509 % à l'once contre le 24 oz — la fraction tranche, pas l'œil.",
  'everyday.e17.name': 'Dinde de Thanksgiving : congélateur ET restes, deux horloges',
  'everyday.e17.say': "Deux horloges, une dinde. Réfrigération (8 calculettes nov. 2026 divergent sur la table USDA) : au plus tard = four − bout long, jamais avant = − garde 1-2 j ; heures = arguments ; fini = 165 °F à la sonde. Restes : « avant lundi 30 nov. » (NBC) vs « trois jours, 72 h » (ky3) ; FSIS se contredit au congélateur (2-6 vs 3-4 mois) — rendu : l'UNION, 2 h STRICTES depuis cooked_at (2 h pile passe, 2 h 01 jette), 4ᵉ jour = LAST_DAY.",
  'everyday.e18.name': 'Trois plats veulent le four — le compte à rebours, conflits nommés',
  'everyday.e18.say': "Huit timelines 2026, un dîner, des repos 20-60 min, 325 ou 350 °F — aucune des huit ne compte les 45 min de préchauffage. À REBOURS de l'heure de service (argument) : un four, un plat à la fois, repos dehors ; autre consigne = conflit nommé ; « 180 » sans unité = refusé ; repos > 2 h = zone FSIS.",
  'everyday.e19.name': "Dates limites d'envoi de Noël — ≥2 sources, divergente nommée",
  'everyday.e19.say': 'Six tableaux des 13-21 nov. 2026 se contredisent : un syndicat imprime FedEx Saver, 2Day, Overnight un jour plus tard — cible 25, pas 24. ≥2 sources concordantes par ligne ; divergente nommée ; UPS Ground refusé (pas de date unique). Fenêtre close 23 déc.',
  'everyday.e20.name': 'Retours des fêtes — ≥2 sources, provenance par ligne',
  'everyday.e20.say': "« Jusqu'au 31 janvier » ment par omission : Target ferme l'achat le 24 déc., Best Buy coupe la règle membres à 4 déc., un blog a republié les dates passées DÉCALÉES ; Seller Central publiait 2026. ≥2 sources par ligne, provenance, mono-sources refusées avec le fait. « Au plus tard des deux » exige la livraison.",
  'everyday.e21.name': 'Le prix barré est-il LÉGAL ? règle Omnibus des 30 jours',
  'everyday.e21.say': "Référence légale : le prix le PLUS BAS des 30 jours (dir. 2019/2161 art. 6a) — la promo du week-end l'ABAISSE (CJEU C-330/23). 100 → 80 → 100 → 70 = 12,5 %, pas 30 %. Sweep mars 2026 : 30 % des 314 commerces se trompent ; jusqu'à 350 000 € d'amende en Espagne. Historique en entrée, référence et % vrai.",
  'everyday.e22.name': "Le prix a BAISSÉ après l'achat — qui doit la différence",
  'everyday.e22.say': "Payé 100, affiché 80. Aucune loi n'oblige au remboursement — les garanties publiées oui, fenêtres DATES : Target 24 déc., Best Buy 15 janv., Costco 30 j, Fnac-Darty la campagne (carte cadeau, pas espèces), Amazon zéro. Verdict, date, montant, monnaie — classe de source par ligne. Zéro fetch.",
  'everyday.e23.name': 'Le cadeau mort APRÈS le retour — ce que la LOI doit, jour pour jour',
  'everyday.e23.say': 'Cadeau livré 25 déc., en panne le 16 : fermeture le 15, presse muette ; la loi, si. France : conformité 2 ans depuis la DÉLIVRANCE, vices cachés 2 depuis la DÉCOUVERTE, plafond 20 ans. UK : 30 j pour rejeter, preuve INVERSÉE à 6 mois, 6 ans (5 en Écosse). Page officielle contradictoire : les DEUX dates voyagent. US/AU refusés par nom.',
  'everyday.e24.name': 'Puis-je jeter ce dossier ? — QUATRE horloges dans le carton',
  'everyday.e24.say': "« Six ans » = QUATRE dates : TVA depuis la date ÉCRITE (événement futur compris — HMRC l'écrit), limited company depuis CLÔTURE, s.388 : TROIS si private, SIX si plc depuis CRÉATION, SA cinq ans depuis le 31/01. Exemple officiel 2022-23 : gardé jusqu'au 31-01-2029. Les « ou plus si » reviennent BLOCKED ; CH15400 : la PLUS LONGUE gouverne.",
  'everyday.e25.name': "Carte cadeau « périmée » ? Peut-être vivante — l'ACHAT ancre",
  'everyday.e25.say': "Irlande — Gift Vouchers Act 2019 : date imprimée < cinq ans depuis l'achat = REMPLACÉE — le légal couvre le papier (66B(1)(b)+(c)). JD Sports : ≈250 000 € rendus en juillet. Le porteur tient tous les droits (66B(10)). Solde ≥ 1 € : dû. France : AUCUNE durée ; « 30 ans » = immobilier (refusé).",
  'everyday.e26.name': 'Les soldes sont UNE LOI : trois tables, deux formules, zéro au Luxembourg',
  'everyday.e26.say': 'France (arrêté 27-05-2019) : hiver = 2ᵉ mercredi janv. 8 h, avancé si le 2ᵉ > 12 (2027 : 6 janv. — « 9 février » = clause ratée) ; été = dernier merc. juin, avant-dernier si > 28 (2027 : 23 juin) ; 4 semaines, début compté ; 7 dérogations verbatim (Moselle 26 juin 2021 ; hiver 2021 SIX SEMAINES ; Guadeloupe 7 oct. ; canicules 2023/2026 5 semaines) ; « ouvré » non défini : lundi 4 premier, samedi 2 nommé. Belgique (VI.25 CDE) : hiver 3–31 janv., DU 2 SI dimanche — 2016, 2027 ; attente « du 2 décembre au 1ᵉʳ janvier » (SPF — presse : 3) ; été 1–31 juil., 30 JUIN si dimanche — 2018 ; corona : été 2020 1er-31 août, hiver 2021 REPORTÉ lundi 4 — clause écrasée — 15 FÉVRIER par LOI (titres : 14). Luxembourg (loi 23-déc-2016, art. 1er § 4) : AUCUNE formule — un règlement date CHAQUE ANNÉE ; dix actes 2018-2027 (hiver 2026/27 : sam. 2 → 30 janv.) ; deux rectificatifs — 2017 : nom de jour seul, 2023 : la borne (Mémorial : dimanche jamais donné par la presse) ; chaîne 2021 : trois actes, un mort ; au-delà : refus, jamais prophétie. CE 20-05-2026 : amendes annulées, dates tenues.',
  'everyday.e27.name': "Colis reçu mardi — jusqu'à QUAND changer d'avis",
  'everyday.e27.say': 'Section 6 legifrance rejouée verbatim : L221-18 nomme le départ (bien reçu, service conclu) ; L221-19 : lendemain = jour 1, fin minuit du 14ᵉ jour, samedi/dimanche/férié au premier ouvrable (table L3133-1 maison). Reçu 24 nov → 8 déc ; samedi 5 → lundi 7 ; 8 mai férié → lundi 11. Info manquante → +12 mois ; retard → 14 jours nouveaux. 13 exceptions verbatim (personnalisé, scellé hygiène, enchère). Soldes, occasion : droit court (F10485). Magasin : AUCUN droit, refusé par nom. Fenêtre enseigne : autre horloge.',
  'everyday.e28.name': "Ils se sont disputés sur le calcul — ils "
                           "avaient deux graphes",
  'everyday.e28.say': "A avance 1 375,00 €, C 865,00 €, B rien ; parts égales ; C remet sa part à B. A exige 628,33, B propose 458,33 — le désaccord EST l'architecture : C ne remet que les 118,34 qu'on lui doit → B vire 628,33 à A, un virement, minimum prouvé ; par reçu, la remise tue l'arête B→C → B paye 458,33, C porte 288,33. compare rend les deux, chiffre l'écart ; les cents ferment là où le 746,67×3 du fil ne fermait pas.",
  'everyday.e29.name': 'Un même loyer, quatre conventions — aucun calculateur ne choisit pour vous',
  'everyday.e29.say': "Sortie le 18, loyer 1 000 € : publié : « 1000/30 = 33,33 × 18 = 600 » — DEUX arrondis silencieux, la voie du bailleur donne 599,94 (9sqw2j). Entrée le 15 janvier, mois de 31 : l'office divise « par 30, REGARDLESS of actual number of days » — 566,67 ; le voisin par 31 — 548,39 (1hitzjq). Bail finit MIDI le 12 : 12 facturés, 11,5 plaidés, 12-ou-11 publiés (cevz6l). prorate nomme basis cycle|month30|year365, ordre, borne ; compare rend les DEUX, écart signé ; un instant dans une date est refusé — les deux jours entiers montrés. Jamais la loi locale.",
  'everyday.e30.name': 'Un salaire, plusieurs taux horaires — la fiche ne dit jamais lequel',
  'everyday.e30.say': "52 000 par an : ÷2 080 = 25,00 (le « typically » de r/Payroll — écrit dans tous les fils, nommé par aucun calculateur) ; ÷2 087 = 24,92 — c'est la loi fédérale US mot pour mot (5 USC 5504(b) : « divide the annual rate by 2,087 », « nearest cent, counting one-half and over ») ; le bulletin « 20 cents off » de r/ATC, c'est elle. L'ordre mord : arrondir le taux d'abord, ×80 = 1 993,60 ; diviser l'année par 26 = 2 000,00 — −6,40 par paie, −166,40 par an, rendus en paire signée. Bihebdo ÷26 contre semi-mensuel ÷24 : DEUX horloges (2 000,00 contre 2 166,67). Et 2027 compte 53 vendredis : 27 paies tous les 15 jours (r/IRS_Source) — comptées, pas prophétisées. payscale nomme chaque diviseur et sa citation ; 365 refusé par le nom ; TON diviseur reste un argument (1 820, 2 640 — jamais la loi locale) ; jamais de moyenne, jamais de fetch.",
  'nav.kit': 'Kit',
  'kit.h2': 'La suite sur votre disque',
  'kit.creed': "Le protocole n'est pas le transport — c'est l'acte de naissance de l'outil.",
  'kit.intro': "Un dossier, trois fichiers, aucune dépendance : SKILL.md (les tables ci-dessus, en prose), serveur local (stdlib seule, catalogue sur /agent/manifest), l'auto-diminution quand l'agent n'est pas connecté. Copiez, installez, vérifiez — le kit tient dans un dépôt de notes.",
  'kit.c1.sum': 'Installer — la suite basique sur la machine',
  'kit.c1.foot': "Sha vérifié, pas de daemon, pas d'auto-update, pas de réseau dans le moteur. Le sans-état est le contrat : l'humain décide quand le kit bouge.",
  'kit.c2.sum': "Appeler — consulter avant d'agir",
  'kit.c2.foot': "La skill interroge l'annuaire d'abord. Même canon, mêmes refus, mêmes golds qu'au datacenter — ce qui est vérifié ici l'est là-bas, octet pour octet.",
  'kit.c3.sum': "Construire — dès la deuxième fois, écrire l'outil",
  'kit.c3.foot': 'Golds tracés AVANT le code, AST-gate, pin-gate. Statuts : proposé, attesté, réseau-vérifié — le kit grandit localement, la preuve repousse au réseau. Une leçon est une proposition — le banc la verrouille.',
  'kit.howto.p1': "Installer la skill : <code>curl https://mechacut.studio/SKILL-MINI.md -o SKILL.md</code> — déposer le fichier chez l'agent (CLAUDE.md, AGENTS.md, skills/). ~1 000 jetons, calibré petits modèles.",
  'kit.howto.p2': "Le faire consulter d'abord : avant d'agir, l'agent décrit son problème en une phrase à /route/resolve — l'annuaire rend l'outil qui existe déjà, ou dit qu'aucun n'existe.",
  'kit.howto.p3': "Appeler : POST sans état, sans clé sur le libre ; la réponse porte son sha256, le refus champ + attendu + exemple. Tout tient sur cette page : une ligne installe le skill, l'annuaire répond, le libre va sans clé.",
  'kit.plain.sum': "Vous n'êtes pas développeurs ? Pas grave, on traduit.",
  'kit.plain.p1': 'Ouvrez votre assistant IA habituel (Claude, ChatGPT, Grok, Copilot…).',
  'kit.plain.p2': 'Envoyez-lui ce message : " Lis https://mechacut.studio/SKILL-MINI.md et suis-le pour tous mes calculs." Rien à installer, rien à payer, pas de compte.',
  'kit.plain.p3': 'Puis demandez votre vraie tâche : "30 % puis 20 % de remise, ça fait combien ?", "cette facture est en retard de combien de jours ?" Les chiffres ne sortent plus de sa tête — ils sortent de la suite, identiques pour tous.',
  'kit.plain.p4': 'Rien ne sait faire ce que vous avez demandé ? Proposez-le en mots simples — proposition publique, verdict public : livré, en banc, ou refusé avec la raison nommée, sur /proposals.',
  'kit.dev.sum': 'Pour les développeurs — trois lignes, sans compte',
  'kit.propose': "Proposer un outil : POST /api/v1/agent/propose — un contrat, jamais du code ; doublon nommé, preuve affichée, éligibilité rendue en blob prêt au commit. Zéro stockage serveur. Protocole : /SKILL-KIT.md",
  'bench.d82.sum': "Traces d'appels jugées : le même geste d'agent n'a jamais été réémis à l'identique (0/14, V22b) ; un retry a multiplié la facture ×4 sans converger (V17) — loop/doom-check dit DOOM, CYCLIC ou STORM sur bytes canoniques, seuils nommés.",
  'bench.d82.foot': "Identité en (outil, args) canoniques : l'ordre des clés ne cache jamais une boucle. Deux appels identiques ne sont pas une boucle — seuil dit. Tous les signaux rapportés, verdict le plus grave. Sources : bench/FINDINGS-V17.md · run22b.",
  'bench.e76.sum': 'Le juge du banc est devenu route : eval/compare rend OK ou WRONG avec les divergences nommées — 2,5 contre "2.50" n\'est jamais un désaccord, les flottants ne sont jamais un argument.',
  'bench.e76.foot': "Règle née de l'incident du juge V2 (il recopiait son attente) : même quantité n'est jamais une divergence ; quantité différente nommée par pointer, kind, expected, got. Decimal exact, jamais float.",
  'bench.a79.sum': "La politique en grammaire fermée : check/allowlist rend ALLOW, DENY ou AMBIGUOUS — la règle la plus spécifique gagne, l'égalité remonte à l'humain, le silence n'autorise jamais.",
  'bench.a79.foot': "Une action en forme de regex est refusée, pas évaluée : un gate qui interprète est une porte dérobée. Montants Decimal exacts, devises ISO, default deny vrai. Même loi que R3 de l'annuaire.",
  'x402.h2': 'Paiements machine',
  'x402.p1': "Le payant tient en quatre pas : le serveur répond <code>402</code> avec ses exigences ; l'agent signe un transfert USDC EIP-3009 ; un facilitateur vérifie et règle ; la réponse rejoue la preuve dans <code>X-PAYMENT-RESPONSE</code>. Zéro clé serveur.",
  'x402.p2': 'Les paiements rejoués sont refusés ; les erreurs sur routes payantes restent gratuites. Chaque refus est public : <a href="/misses.json">/misses.json</a>.',
  'x402.bankr': 'Second domicile : quatre transforms payés aussi sur le x402 Cloud de <a href="https://bankr.bot">Bankr</a> — mêmes chemins, mêmes sha256 : <a href="https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/chart_from_data">chart</a> &middot; <a href="https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/reshape_json">reshape</a> &middot; <a href="https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/validate_json">validate</a> &middot; <a href="https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/csv_join">csv-join</a>. Le reste ici, gratuit compris.',
  'vision.h2': 'Pourquoi le déterminisme, pourquoi maintenant',
  'vision.p1': 'Un LLM approxime. <code>sha256("abc")</code> ? Réponse avec assurance, élégance, et fausse. Nettoyer le même CSV chaque jour ? Des tokens pour redériver ce qu\'une fonction rend en millisecondes — mêmes octets, à chaque fois.',
  'vision.p2': "Le calculateur Apollo : 4 Ko de RAM, des humains sur la Lune — parce qu'aucune maths n'improvise. Chaque constante calculée une fois, au sol, à froid, gelée dans la mémoire à cordes.",
  'vision.quote': "Codé d'abord pour envoyer l'homme sur la Lune, le déterminisme enverra l'IA au travail.",
  'nav.network': 'Réseau',
  'network.h2': 'Le catalogue est nourri par les agents, jugé par les octets.',
  'network.creed': 'Un agent apprend. Tous les agents savent.',
  'network.intro': 'La porte est un endpoint, pas un ticket : POST /api/v1/agent/propose — cinq champs, grammaire fermée, un contrat et jamais de code. Chaque verdict atterrit dans un registre public, append-only.',
  'network.ask.sum': 'LA DEMANDE — cinq champs, zéro code',
  'network.ask.body': 'name, purpose, examples (entrée → attendu), why, source (votre pseudo ou URL). Serveur répond par un verdict nommé — ELIGIBLE, SUSPECT-DUPLICATE, DUPLICATE-OF — et un blob prêt à commiter. Rien n’est stocké côté serveur : le registre vit dans git, append-only.',
  'network.verdict.sum': 'LE VERDICT — le même juge pour tous les modèles',
  'network.verdict.body': 'Accepté = les mêmes portes que la maison passe pour elle-même : golds tracés à la main avant le code, pins, AST-gate, suite verte. Le juge est tiers et byte-exact — le même sha le prouve pour Claude comme pour Qwen. Un refus se nomme : issue du protocole, pas échec.',
  'network.loop.sum': 'LA BOUCLE — un apprend, tous savent',
  'network.loop.body': 'Un contrat shippe = un appel pour chaque agent du réseau, haché, dès ce jour. Le premier proposeur externe est crédité dans la ligne. La répartition 50/50 est décidée et la factory splitter est live sur Base — les répartitions tournent on-chain, n’importe qui peut vérifier.',
  'network.proof': 'Entrées shippées au registre public — arrivées, verdicts et refus, ligne à ligne',
  'vision.p3': "Mechacut est cette math gelée pour les agents : vocabulaires fermés, contrats refusant ce qui sort de la table, erreurs nommant la forme attendue — l'erreur est le prompt qui répare. Le sens reste au modèle, la mécanique vient ici.",
  'contract.h2': 'Le contrat',
  'x402.sum': 'Comment une machine paie — 402, EIP-3009, facilitateur, preuve',
  'vision.sum': 'Pourquoi le déterminisme, pourquoi maintenant — Apollo, 4 Ko, le dé',
  'contract.sum': 'Les cinq promesses, verbatim',
  'contract.li1': 'Même requête → mêmes octets, sha256 sur chaque réponse',
  'contract.li2': 'Sans inscription, sans clé, sans mur de débit sous 30 req/min',
  'contract.li3': "Zéro stockage : le seul état est une fenêtre d'une minute, un registre de 60 minutes et un jeu de nonces de paiement",
  'contract.li4': 'Vocabulaires fermés — tout ce qui sort de la table est refusé, nommé, renvoyé à sa forme attendue',
  'contract.li5': 'Des erreurs qui réparent : champ, message, attendu, toujours',
  'contract.li6': 'Paiements machine x402 : USDC sur Base, vérifiés par facilitateur, zéro humain dans la boucle',
  'agents.line': 'Parlez agent : outils MCP, GET /agent/manifest (toute la suite en une requête), GET /route?q=…, POST /api/v1/pipeline.',
  'agents.hint': 'installez un pack',
  'footer.family': 'Mechacut fait partie de la famille C.V. — voir moovicut.',
 },
 "pt": {
  'meta.title': 'Mechacut — mesma requisição, mesmos bytes',
  'meta.desc': 'Transformações determinísticas para agentes: 184 ferramentas, três níveis, pagamentos entre máquinas. Sem cadastro, chave ou armazenamento.',
  'hero.plain': 'Em palavras simples: a Mechacut faz as contas exactas dos assistentes. Conta para dividir, prazo, moeda, ficheiro — o assistente pergunta, a Mechacut responde, sempre igual. E quando um aprende algo, todos sabem no próprio dia.',
  'dev.h2': 'Para programadores & agentes',
  'dev.intro': 'Tudo o que está acima é verdade. Abaixo está o como: a API completa, o catálogo, os esquemas, os benchmarks, os preços. Sem prosa — referências.',
  'nav.everyday': 'Dia a dia',
  'nav.tools': 'Bundles',
  'nav.numbers': 'Provas',
  'nav.vision': 'Visão',
  'nav.api': 'Contrato',
  'pill': 'v{ver} · {n_tools} transformações · {n_recipes} receitas',
  'hero1': 'Significado se aprende.',
  'hero.why': '<strong>Por que determinismo?</strong> Porque uma resposta certa que muda a cada execução não é resposta — é um dado lançado. Mesma pergunta, mesmos bytes tornam agentes auditáveis: cada resposta traz sua impressão, cada erro nomeia o campo, e o que você testa de manhã é o que entrega à noite.',
  'demo.title': 'NO BANCO — ao vivo, sem chave, mesmos bytes a cada chamada',
  'demo.run': 'Rodar',
  'demo.hint': 'rode — a resposta vem do endpoint real, não de uma captura',
  'demo.err': 'rede instável — o endpoint responde: POST /api/v1/num/round',
  'hero2': 'Mecânica se conhece.',
  'hero3': 'Competência não se aprende. Serve-se.',
  'lede': 'Suíte de <strong>{n_tools} transformações determinísticas</strong> para agentes — {n_free} grátis para sempre, {n_cap} grátis até 32 KB e depois por chamada, {n_paid} pagáveis por máquina — mais {n_recipes} receitas de chamada única. O modelo para de adivinhar o que um checksum prova.',
  'bundles.h2': 'O catálogo',
  'bundles.creed': 'Um modelo calcula. Um servidor sabe.',
  'cat.search': 'busque uma ferramenta ou seu problema…',
  'cat.hits': '~n~ ferramentas de ~t~',
  'panel.copy': 'copiar curl',
  'panel.copied': 'copiado',
  'panel.close': 'fechar',
  'panel.say': 'diga ao seu agente:',
  'panel.got': 'o servidor respondeu:',
  'nav.menu': 'menu',
  'bundles.intro': 'Mesma requisição, mesmos bytes — cada resposta carrega seu sha256. Instale um pack, ou leia o manifesto inteiro em uma requisição e deixe <code>GET /route</code> escolher.',
  'tiers.h2': 'Três níveis, zero contas',
  'tiers.intro': 'Agentes não leem páginas de preço — então o preço está no protocolo: rota grátis responde sem chave, rota com teto é grátis abaixo de 32 KB, o resto recebe <code>402</code> honesto — desafio x402 USDC na Base liquidado por facilitador. Entre um servidor e um robô, só preços e recibos.',
  'bench.h2': 'Benchmarks, ou o que procurávamos:',
  'bench.creed': 'O muro é a FORMA, não o tamanho — e nós precificamos a porta.',
  'bench9.intro': 'Uma frase vaga (em francês), seis campos obrigatórios — valores com 2 decimais, percentuais, datas únicas, URL, e-mail, total. Expectativas calculadas à mão antes de rodar. O servidor monta o cartão (/intent/card); o modelo repassa uma linha e a resposta nunca passa por ele.',
  'bench9.with': 'com o cartão de intenção',
  'bench9.foot': 'A linha 0.5B reproduziu em uma segunda rodada independente. Três chamadas iguais → um único sha256. A variante autônoma (o modelo escolhe a ferramenta) também marca 6/6. Sementes, scripts, falhas: bench/results_v9.jsonl.\n',
  'bench10.intro': 'Dezoito tarefas com UMA resposta certa — dígitos GS1, um SHA-256, descontos em cascata, uma coluna que prova o próprio ponto decimal. Dois modelos grátis e LOCAIS, zero gasto de API: o harness verifica que cada rota é gratuita. Os gabaritos saíram das specs publicadas ANTES de qualquer modelo.',
  'bench10.with': 'com uma chamada-relé',
  'bench10.foot': 'As falhas nuas se reproduzem num segundo passe independente: 18/18 vereditos idênticos — a temp 0, repetir não converge, repete. Execuções brutas: bench/results_v10.jsonl, método: bench/FINDINGS-V10.md.\n',
  'bench.v23.sum': 'Um 1,7B treinado para agentes resolveu {v23_chain}/{v23_chain_cells} correntes nu por ${v23_cost} — nosso muro era o TREINAMENTO, não o tamanho; e o cadeado recusou {v23_refused} respostas certas pelos nomes.',
  'bench.v23.intro': 'A replicação fora da família: os mesmos 20 problemas com semente, os mesmos braços do v20, um modelo de outra linhagem (LFM3-1.7B, tri-híbrido, pós-treinado para tool calling). Nu {v23_n_all}/20, retransmitido {v23_s_all}/20, com cadeado {v23_l_all}/20. Nada aqui refuta o v19: acertar uma vez não é responder no mesmo byte trinta dias seguidos.',
  'bench.v23.arm': 'braço',
  'bench.v23.wins': 'acertos /20',
  'bench.v23.usd': 'custo',
  'bench.v23.foot': 'Bruto: bench/results_v23_lfm3.jsonl · método: bench/FINDINGS-V23.md · $ a preços por token congelados.\n',
  'bench.v20.sum': 'O muro é um ALVO: o llama 8B vai de {v20_8b_s} para {v20_8b_l}/20 com o cadeado de alvo; o 7B fecha seu primeiro {v20_7b_l}/20.',
  'bench.v20.intro': 'A promessa de v17 medida: a resposta deve nomear a quantidade que devolve. Nu, o 8B calculava certo e respondia ao lado — {v20_aside} de seus erros traziam outra quantidade da cadeia, e o cadeado converteu {v20_aside_conv}. {v20_cells} células, e o braço nu reencena o v15 exatamente ({v20_replay}).',
  'bench.v20.model': 'modelo',
  'bench.v20.naked': 'nu',
  'bench.v20.locked': 'com cadeado',
  'bench.v20.foot': 'Bruto: bench/results_v20_target_lock.jsonl · método: bench/FINDINGS-V20.md.\n',
  'bench.g1': 'O que eles erram não é pensar — é executar',
  'bench.g2': 'O muro é uma FORMA — e formas são alvo de treino',
  'bench.g3': 'Nenhum modelo neste banco diz «não tenho certeza» — pagar mais não desvia da forma',
  'bench.g4': 'A leitura é o teto que nenhuma ferramenta fura',
  'bench.g5': 'O regime real: trinta dias do mesmo trabalho',
  'bench.v11.sum': 'Quinze tarefas hostis: o 7B vai de {v11_7b_nu} a {v11_7b_relay} com relé; o 8B de {v11_8b_nu} a {v11_8b_relay}.',
  'bench.v11.foot': 'Bruto: bench/results_v11.jsonl · método: bench/FINDINGS-V11.md',
  'bench.f5.sum': '{f5_wins}/{f5_cells} tentativas encadeadas com a ficha — critério ≥19 APROVADO; {f5_repairs} reparadas por recusa nomeada; o 7B sozinho {f5_7b}.',
  'bench.f5.foot': 'Bruto: bench/results_f5_accept.jsonl · método: bench/FINDINGS-F5.md',
  'bench.v13.sum': 'O resultado negativo, publicado primeiro: no GSM8K real o cartão-relé desaba a {v13_relay_05b}/20 no 0.5B — pedir a decomposição ao modelo ainda é deixá-la com o modelo.',
  'bench.v13.foot': 'Bruto: bench/results_v13_gsm8k.jsonl · método: bench/FINDINGS-V13.md',
  'bench.v14.sum': 'Skill estrita: {v14_breaks}/{v14_cells} rupturas de protocolo — a classe que a forma mede diretamente — a leitura segue livre.',
  'bench.v14.foot': 'Bruto: bench/results_v14_skill.jsonl · método: bench/FINDINGS-V14.md',
  'bench.v22.sum': 'Três modelos fronteira respondem {v22_nu} nus — um {v22_best}, outro {v22_worst}. Pela ficha congelada: {v22_fiche}. Pagar mais não muda a forma.',
  'bench.v22.foot': 'Bruto: bench/results_v22.jsonl · método: bench/FINDINGS-V22.md',
  'bench.v22b.sum': 'Cinco passes no regime dos agentes: {v22b_ok}/{v22b_cells} certos — o MESMO programa duas vezes: {v22b_stable}/14. O servidor: {v22b_shas} sha por problema.',
  'bench.v22b.foot': 'Bruto: bench/results_v22b.jsonl · método: bench/FINDINGS-V22.md',
  'bench.v24.sum': 'Trinta dias no mesmo CSV com um modelo QUE SABE cadeias: {v24_sil}/{v24_days} dias de resposta vazia após 8.192 tokens de raciocínio, {v24_ok} certas, faturados ${v24_usd}. A máquina: {v24_m_ok} a $0,00.',
  'bench.f7.sum': 'As sete cadeias copiadas EN/PT: {f7_wins}/{f7_cells} — critério ≥19 APROVADO; {f7_rep} ganhas pela recusa nomeada. O 0.5b copia 4/7 em PT onde o FR o punha a 0/7: o teto de leitura é do modelo × língua × forma.',
  'bench.f7.foot': 'Bruto: bench/results_f7_accept.jsonl · critério gelado: bench/FINDINGS-F7.md',
  'bench.v24.foot': 'Bruto: bench/results_v24_lfm3_30days.jsonl · a emenda está no histórico git (run24 amendado)',
  'bench.v19.sum': '{v19_wins}/{v19_days} tentativas corretas para os modelos — máquina: {v19_m_ok}/{v19_m_days} dias no mesmo byte; {v19_drift} saídas diferentes de um só modelo em 30 dias.',
  'bench.v19.intro': 'O mesmo CSV sujo limpo 30 dias seguidos. Especificação de seis regras, gold ESCRITO À MÃO antes do banco, um braço retry que só vê sua própria forma — nunca a resposta. Temperatura 0,7: o regime real dos agentes, divulgado.',
  'bench.v19.arm': 'braço',
  'bench.v19.right': 'dias certos /30',
  'bench.v19.distinct': 'saídas distintas',
  'bench.v19.foot': 'Bruto: bench/results_v19_csv_bill.jsonl · método + dólares: bench/FINDINGS-V19.md · replay: python bench/run19.py',
  'bench.v17.sum': 'Retry ×5 num erro sistemático: {v17_retry_wins}/{v17_retry_cells} cadeias consertadas — o mesmo erro, 5× o preço.',
  'bench.v17.intro': 'Três braços, os mesmos 20 problemas novos, cada token contado: responder nuo, tentar cinco vezes, ou entregar o cálculo ao servidor. Células: {v17_cells}.',
  'bench.v17.nu': 'nu',
  'bench.v17.retry': 'retry ×5',
  'bench.v17.relay': 'servidor (ok · tokens/certo)',
  'bench.v17.foot': 'Bruto: bench/results_v17_tokens.jsonl · bench/FINDINGS-V17.md · replay: python bench/run17.py',
  'bench.v16.sum': '{v16_wrong} erros em {v16_runs} execuções — «não tenho certeza» dito {v16_doubt} vezes.',
  'bench.v16.intro': 'Problemas do dia a dia gerados na hora, cada modelo convidado a marcar sua confiança. Falharam sempre do mesmo modo: com certeza.',
  'bench.v16.foot': 'Bruto: bench/results_v16_calibration.jsonl · bench/FINDINGS-V16.md · gerador: bench/gen16.py (semeado, duplo oráculo).',
  'bench.v15.sum': 'O muro tem FORMA: {v15_alone_wins}/{v15_cells} tentativas em cadeia nuas ou com retry — {v15_best_arm}/{v15_arm_cells} com o melhor braço servidor.',
  'bench.v15.intro': 'A matriz completa: 5 transportes × 4 modelos gratuitos × 20 problemas semeado (400 células), hipóteses comitadas ANTES da primeira célula, previsões furadas publicadas primeiro.',
  'bench.v15.foot': 'Bruto: bench/results_v15_matrix.jsonl · bench/FINDINGS-V15.md · replay: python bench/run15.py && python bench/score15.py',
  'bench.v12.sum': '{v12_zero} sozinho → {v12_hero} com um só relé. O zero vira herói.',
  'bench.v10.sum': 'Uma resposta certa cada: {v10_alone} sozinho → {v10_server} com relé — a $0, auditado pelo próprio banco.',
  'bench.v9.sum': 'Uma frase vaga, seis chaves: {v9_alone} → {v9_card} com o cartão de intenção.',
  'bench.v6.sum': 'A primeira matriz — nu vs relé. Cada linha, cada harness, cada falha: bench/FINDINGS.md.',
  'bench12.intro': 'Dez cálculos exatos (7834×9217, 0.1+0.2, porcentagens em cadeia…) × quatro modelos locais GRATUITOS × três braços: responder nu, escrever Python, ou repassar uma expressão ao math/calc. Mesmo quadro, duas físicas: o braço código devolve float, o relé devolve exato.',
  'bench12.code': 'escreve Python',
  'bench12.relay': 'relé Mechacut',
  'bench12.foot': 'O 8B falha no RELÉ por tagarelice de protocolo, não por matemática — por isso a ficha de intenção escreve a linha por ele. Nu, o 0.5B inventou 89000098; em relé, 9/10 com mediana de 0,2 s. Bruto: bench/results_v12.jsonl, método: bench/FINDINGS-V12.md.\n',
  'bench.intro': 'Tarefa congelada (seed 20261120): CSV sujo + JSON quebrado + lista de URLs → YAML canônico, espera fixada por sha256. O mesmo modelo local fraco (Qwen 2.5, temperatura 0), um braço sozinho, um braço guiando o Mechacut. Fracassos publicados também — o 0.5B falha nos dois braços, e teto de capacidade é resultado.',
  'bench.model': 'modelo',
  'bench.alone': 'sozinho',
  'bench.with': 'com mechacut',
  'bench.tokens': 'tokens consumidos',
  'bench.foot': 'O 7B vai de 0 % a 100 % em uma única chamada de pipeline. Cada execução, cada token, está em bench/results.jsonl.',
  'nav.build': 'Construir',
  'nav.market': 'Mercado',
  'market.h2': 'Eles também dizem',
  'market.creed': 'As grandes casas convergiram na mesma frase — só o modo de entregá-la difere.',
  'build.h2': 'O que você pode construir hoje',
  'build.intro': 'Você tem um modelo pequeno e gratuito na sua máquina. Três coisas para fazer com ele — as frases citadas são o que você diz ao agente, as respostas são o que o servidor realmente devolveu. Sem conta, sem cartão, sem reza.',
  'build.r1.name': 'A portaria da nota (Brasil)',
  'build.r1.say': '“O CNPJ 11.222.333/0001-81 do meu cliente é válido para a nota?”',
  'build.r1.got': '{{ "valid": true, "algorithm": "mod-11 double DV (Receita Federal)" }}',
  'build.r1.why': 'Sozinho, um 0.5B “calcula” dígitos de conferência — e erra. Aqui os dígitos decidem: a nota não morre no contador.',
  'build.r2.name': 'O guarda-vazamento',
  'build.r2.say': '“Escaneie este log antes de eu colar num chatbot.”',
  'build.r2.got': '2 achados → semente [SEED_PHRASE] e chave [OPENAI_KEY_1]',
  'build.r2.why': 'O scan devolve posições, nunca o valor; a máscara nunca devolve a chave. O segredo veio guardar-se aqui — protegéo até de nós.',
  'build.r3.name': 'O rélay do incidente',
  'build.r3.say': '“relève les montants et dates de cette note d’incident” — em francês, para um 0.5B.',
  'build.r3.got': 'money [3200.00, 12450.75] · 6/6 em 320 tokens (sozinho: 0/6)',
  'build.r3.why': 'É o bench v9, igual: mesma tarefa, mesmo modelo, uma linha de relay. Cada execução está em bench/results_v9.jsonl — reproduza você mesmo.',
  'build.connect': 'Ou ligue agora: cole ESTA linha em qualquer agente, até o menor — ela vira o manual completo:',
  'everyday.h2': 'Para todo mundo',
  'everyday.open': 'Expandir as provas — saídas reais do servidor, não maquetes.',
  'everyday.intro': "Sem código, sem jargão. Vinte e oito coisas que uma pessoa pede ao agente numa terça — cada resposta abaixo é saída real do servidor, não maquete.",
  'everyday.e1.name': 'Wi-Fi de visitas, um scan',
  'everyday.e1.say': '“Coloca o Wi-Fi num QR para as pararem de perguntar a senha.”',
  'everyday.e2.name': 'O cheque, por extenso',
  'everyday.e2.say': '“Escreva R$ 1.234,56 por extenso no cheque — o banco recusa erro.”',
  'everyday.e3.name': 'IBAN antes da transferência',
  'everyday.e3.say': '“Copiei certo este IBAN? Se voltar, pago tarifa.”',
  'everyday.e4.name': 'Receita em página imprimível',
  'everyday.e4.say': '“Transforma minhas anotações da receita numa página limpa — quero o PDF para a geladeira.”',
  'everyday.e5.name': 'Contando os dias',
  'everyday.e5.say': '“Quantos dias até a viagem?”',
  'everyday.e6.name': 'A conta que o caixa não fará',
  'everyday.e6.say': '“-30 % e depois -20 % é -50 %, certo?” É -44 %.',
  'everyday.e7.name': 'Um terço do bolo, sem arredondar escondido',
  'everyday.e7.say': '“Meu bolo de 6 porções, quero para 2 — 400 g de farinha, 5 ovos?” 400 × 1/3 = 133 1/3 g exato, 135 g na balança. Os ovos são ditos, não adivinhados.',
  'everyday.e8.name': 'Uma terça sim, outra não',
  'everyday.e8.say': '“Clube do livro a cada duas terças às 19h — as próximas quatro datas?” 3 e 17 de nov., 1º e 15 de dez.: quinzenal é PULAR as semanas do meio — e o motor nomeia os pulos.',
  'everyday.e9.name': 'Um pé, três respostas certas',
  'everyday.e9.say': '“EU 42⅔ ou 42,5 — qual é o meu número?” As duas tabelas arredondam: o milímetro é exato, os candidatos de meia e de terço aparecem escritos, e a deriva entre sistemas é um número dito. Nunca um número único confiante.',
  'everyday.e10.name': 'Voo atrasado — quem me deve quanto',
  'everyday.e10.say': "Voo 3h20 atrasado — quanto me devem? A DATA DO VOO escolhe a regra: antes de 23 out. 2027, o antigo EC261 + jurisprudência; depois, a tabela codificada “ACIMA DE três horas”. Os mesmos fatos de cada lado da linha pagam diferente. € ou £, prazo de reclamar em data real.",
  'everyday.e11.name': 'Minha bagagem passa no portão',
  'everyday.e11.say': "Mala 40×18×12, voo em novembro de 2027 — grátis sob o assento? A DATA DO VOO decide: a regra de 2027 limita o item a 40×30×15; antes, nada é fixo. Rotação conta — faces ordenadas, nunca a ordem digitada.",
  'everyday.e12.name': 'Dois planos, um número honesto',
  'everyday.e12.say': "Plano A mais barato por kWh, B por mês — quando A ganha? A virada = (Δ fixo × dias) ÷ Δ preço, em fração EXATA: 4.623⅓ kWh onde o artigo diz “cerca de 4.623”. “Nunca” também é resposta nomeada quando um plano vence nos dois componentes.",
  'everyday.e13.name': 'Quanto vale um ponto de verdade',
  'everyday.e13.say': "“29 000 pontos, voo de R$ 438 menos R$ 5,60 de taxas — quanto vale o ponto?” (438 − 5,60) ÷ 29 000 × 100: o 1,49 impresso esconde o exato 1081/725 = 1,491034… Subtraia ANTES de dividir; é o SEU piso que diz “resgate” ou “pague em dinheiro”.",
  'everyday.e14.name': 'O peso de fato cobrado, as duas correntes impressas',
  'everyday.e14.say': "Duas cobram 6 kg e 5 kg da caixa 40×30×25 — quem erra? Nenhuma: 30 000 ÷ 5 000 = 6, ÷ 6 000 = 5 — dois divisores, uma corrente, cada passo nomeado. As tabelas ESTRAGAM (USPS 166→139, 07/2026); o divisor continua SEU argumento — nunca nossa memória.",
  'everyday.e15.name': 'A placa diz 50 % — a conta, nunca',
  'everyday.e15.say': "«Segundo a 50% off — camisetas de R$ 60 e R$ 40, quanto eu pago?» Nem 50 nem 25: o desconto cai sobre a MAIS BARATA (regra de varejo publicada), o par sai por 80 de 100 = −20 %. Iguais = −25 %; BOGO grátis = −50 %; cupom de −30 % por cima dá −47,5 %, nunca 55 — percentuais multiplicam.",
  'everyday.e16.name': 'Os 500 g viraram 400 g — pelo mesmo preço',
  'everyday.e16.say': "“−20 % na embalagem?” Não é o número da prateleira: perder 1/5 do produto custa +1/4 por quilo (20 % contra 25 % — dois denominadores, 500 e 400). “2 por R$ 7” de potes de 15 oz perde 40,3509 % por onça contra o pote de 24 oz — a fração exata decide, não o olho.",
  'everyday.e17.name': 'Peru de Ação de Graças: congelador E sobras, dois relógios',
  'everyday.e17.say': "Dois relógios, um peru. Geladeira: oito calendários 2026 divergem na mesma tabela USDA: entrar até = forno − ponta longa; horas são ARGUMENTOS. Sobras: '30/nov' (NBC) vs 'três dias, 72 h' (ky3); o FSIS se contradiz no congelador — devolvido: a UNIÃO, 2 h RÍGIDAS desde o cozimento (2 h passam, 2 h 01 deitam), dia 4 = ÚLTIMO.",
  'everyday.e18.name': 'Três pratos querem o forno — a contagem e os conflitos nomeados',
  'everyday.e18.say': "Oito timelines 2026 publicam um jantar com descansos 20-60 min, 325 ou 350 °F — nenhuma das oito conta os 45 min de pré-aquecimento. Cálculo AO CONTRÁRIO da hora de servir (argumento, nunca relógio): um forno, um prato por vez, descanso fora; entrada no minuto da saída em outra temperatura = conflito nomeado; «180» sem unidade = recusado; descanso > 2 h = zona FSIS.",
  'everyday.e19.name': 'Prazos de envio do Natal — ≥2 fontes por linha, a divergente nomeada',
  'everyday.e19.say': "Seis tabelas de 13 a 21/nov/2026 se contradizem: um sindicato imprime FedEx Saver, 2Day, Overnight um dia depois — a meta é 25, não 24. ≥2 fontes concordantes por linha; divergente nomeada com o motivo. UPS Ground recusado: data única não existe. as_of é argumento, não relógio. Janela morre 23/dez.",
  'everyday.e20.name': 'Prazos de DEVOLUÇÃO das festas — ≥2 fontes, classe de provenância por linha',
  'everyday.e20.say': "A manchete «até 31 de janeiro» é mentira por omissão: Target fecha a compra 24/dez, Best Buy corta a regra de membros 4/dez, um blog republicou as datas passadas deslocadas; Seller Central publicava 2026 literal. ≥2 fontes por linha, proveniência, convenção nomeada; fonte única recusada com o fato. «O mais tarde dos dois» exige a entrega.",
  'everyday.e21.name': 'O preço riscado é LEGAL — a regra Omnibus dos 30 dias, auditada do SEU histórico',
  'everyday.e21.say': "A lei nomeia a referência: o preço MAIS BAIXO dos 30 dias (Diretiva 2019/2161 art. 6a) — fim de semana ABAIXA a referência mesmo se o preço subiu depois (TJUE C-330/23). 100 → 80 → 100 → 70 é 12,5%, não 30%. Varredura da Comissão, março de 2026: 30% de 314 lojas erram; Espanha multou até 350.000 EUR. Histórico entra, referência e % real saem — nunca busca preços.",
  'everyday.e22.name': 'O preço CAIU depois da compra — quem deve a diferença, até quando, em que dinheiro',
  'everyday.e22.say': "Pagou 100, a loja mostra 80. Nenhuma lei obriga o reembolso — as garantias publicadas sim, e essas janelas são DATAS: Target 24 dez, Best Buy 15 jan, Costco 30 d, Amazon nada. Cole as duas datas e os dois preços — veredicto, prazo, valor e forma do reembolso, com a classe de fonte por linha. Nunca busca preços.",
  'everyday.e23.name': 'Presente quebrou DEPOIS do prazo de troca — o que a LEI deve, ao dia',
  'everyday.e23.say': "Presente 25/12, morto 16/01: a janela fechou 15; a imprensa cala; a lei não. França: conformidade 2 anos desde a ENTREGA, vícios ocultos 2 desde a DESCOBERTA, teto de 20 anos — três âncoras. UK: 30 dias para rejeitar, 6 meses de ônus INVERTIDO (prova, não prazo), 6 anos para agir — 5 na Escócia. Página oficial se contradiz (recondicionado 24 vs 12): as DUAS datas viajam. EUA/AU recusados por nome.",
  'everyday.e24.name': 'Posso descartar esta pasta? — a gaveta britânica tem QUATRO relógios',
  'everyday.e24.say': "«Seis anos» = QUATRO datas: IVA desde a data ESCRITA (evento futuro conta — HMRC o escreve), limited company desde o FECHAMENTO, s.388: TRÊS se private, SEIS se plc desde a CRIAÇÃO, SA cinco desde um 31/01 que não está em papel. Exemplo oficial 2022-23: guarda até 31-01-2029. Os «ou mais, se» voltam BLOCKED; CH15400: a MAIS LONGA governa.",
  'everyday.e25.name': 'Vale-presente « vencido » pode estar vivo — a Irlanda conta da COMPRA',
  'everyday.e25.say': "Irlanda, Gift Vouchers Act 2019 rejogado: validade impressa menor que CINCO ANS desde a compra é SUBSTITUÍDA — a data legal COBRE o papel (66B(1)(b)+(c)). JD Sports: ≈€250.000 devolvidos em julho (call-in CCPC 20/nov). Âncora: o contrato; o portador tem TODOS os direitos (66B(10)). Saldo ≥ €1 devido. França: nenhuma duração legal; «30 anos» = prescrição imobiliária, recusado.",
  'everyday.e26.name': 'Saldos: três tabelas — duas regras, nenhuma no Luxemburgo',
  'everyday.e26.say': "Três calendários. França (arrêté 27-05-2019): inverno = 2ª quarta de jan. 8h, adiantada se a 2ª passa o dia 12 (2027: 6/jan); verão = última quarta de junho, penúltima se a última passa o 28 (2027: 23/jun); 4 semanas, começo contado; 7 derrogações (Mosela 26/06/2021; inverno 2021 SEIS SEMANAS). Bélgica (VI.25 CDE): inverno 3–31/01, do DIA 2 se o 3 cai domingo — vivido 2016, 2027; a espera é NOMEADA «2/dez a 1º/jan» — imprensa: 3; verão 1–31/07, 30 de JUNHO se o 1º cai domingo — vivido 2018; corona: verão 2020 1–31/08; inverno 2021 ADIADO seg. 4 — cláusula anulada — PROLONGADO a 15/02 por LEI; manchetes: 14. Luxemburgo (lei 23-dez-2016, art. 1º § 4): NENHUMA fórmula — decreto data A CADA ANO; dez atos 2018-2027 (inverno 2026/2027: sáb. 2 → 30/jan); dois retificativos — 2017: só o DIA DA SEMANA, 2023: a BORDE (o JO deu domingo que a imprensa nunca deu); cadeia 2021: três atos, um morto; após o último: recusado, nunca profecia.",
  'everyday.e27.name': 'Recebeu terça — até QUANDO pode desistir',
  'everyday.e27.say': "A lei entrega o calendário: seção 6 legifrance rejogada verbatim — L221-18 nomeia a partida (recebimento, fim do serviço); L221-19: dia seguinte = dia 1, meia-noite fecha o 14; sáb/dom/feriado → primeiro útil (L3133-1 NOSSA). Recebido 24/nov → 8/dez; sábado 5 → 7; 8/mai → 11. Falta a informação: +12 meses; atraso: 14 dias novos. As 13 exceções citam a cláusula. Promoção e usado: direito corre (F10485). Loja física: NENHUM direito — recusado pelo nome. Janela da loja: outro relógio.",
  'everyday.e28.name': 'Brigaram na conta — eram dois gráficos',
  'everyday.e28.say': "A adiantou 1.375, C 865, B nada; partes iguais; C perdoa a parte de B — A cobra 628,33, B oferece 458,33: a briga É a arquitetura. No saldo, C só perdoa os 118,34 que lhe devem → PIX de 628,33 B→A, mínimo provado; nota a nota, o perdão mata a aresta B→C → B paga 458,33, C carrega 288,33. compare numera o vão.",
  'everyday.e29.name': 'Aluguel: quatro convenções — nenhuma calculadora escolhe',
  'everyday.e29.say': "Saída dia 18, aluguel R$ 1.000: postado « 1000/30 = 33,33 × 18 = 600 » — DUAS rodadas em silêncio, o caminho do locador dá 599,94 (9sqw2j). Entrada 15 de janeiro, mês de 31: o escritório divide « por 30, REGARDLESS » — 566,67; o vizinho por 31 — 548,39 (1hitzjq). Contrato termina ao MEIODIA do 12: 12 dias cobrados, 11,5 alegados, 12-ou-11 publicados (cevz6l). prorate nomeia basis cycle|month30|year365, ordem, marco; compare mostra as DUAS com a diferença; instante numa data é recusado — os dois dias inteiros mostrados. Nunca a lei local.",
  'everyday.e30.name': 'Um salário, várias taxas por hora — o contracheque nunca diz qual',
  'everyday.e30.say': "52.000 por ano: ÷2.080 = 25,00 (o “typically” do r/Payroll — em todo comentário, em nenhuma calculadora); ÷2.087 = 24,92 — é a lei federal dos EUA palavra por palavra (5 USC 5504(b): « divide the annual rate by 2,087 », « nearest cent, counting one-half and over »); o contracheque “20 cents off” do r/ATC é essa lei. A ordem morde: arredondar a taxa antes, ×80 = 1.993,60; dividir o ano por 26 = 2.000,00 — −6,40 por pagamento, −166,40 por ano, no par com sinal. Quinzenal ÷26 contra semimensal ÷24: DOIS relógios (2.000,00 contra 2.166,67). E 2027 tem 53 sextas: 27 pagamentos quinzenais (r/IRS_Source) — contados, não profetizados. payscale nomeia cada divisor e sua citação; 365 recusado pelo nome; o SEU divisor fica como argumento (1.820, 2.640 — nunca a lei local); nunca média, nunca fetch.",
  'nav.kit': 'Kit',
  'kit.h2': 'A suíte no seu disco',
  'kit.creed': 'O protocolo não é o transporte — é a certidão de nascimento da ferramenta.',
  'kit.intro': 'As transformações livres não são só uma API: são uma suíte. Instalar, chamar localmente e — o que nenhum mercado faz — construir ferramentas sobre os mesmos portões. curl vira kit call; tarefa repetida vira contrato; contrato vira ferramenta só se os golds foram traçados antes do código.',
  'kit.c1.sum': 'Instalar — a suíte básica na máquina',
  'kit.c1.foot': 'Sha verificado, sem daemon, sem auto-update, sem rede dentro do motor. O sem-estado é o contrato: o humano decide quando o kit se move.',
  'kit.c2.sum': 'Chamar — consultar antes de agir',
  'kit.c2.foot': 'A skill consulta o diretório primeiro. Mesmo cânone, mesmas recusas, mesmos golds do datacenter — o que é verificado aqui é verificado lá, byte por byte.',
  'kit.c3.sum': 'Construir — na segunda vez, escrever a ferramenta',
  'kit.c3.foot': 'Golds traçados ANTES do código, AST-gate, pin-gate. Status: proposto, atestado, rede-verificado — o kit cresce localmente, a prova cresce de volta na rede. Uma lição é uma proposta; o banco a tranca.',
  'kit.howto.p1': 'Instalar a skill: <code>curl https://mechacut.studio/SKILL-MINI.md -o SKILL.md</code> — soltar o arquivo no agente (CLAUDE.md, AGENTS.md, skills/). ~1,000 tokens, calibrado para modelos pequenos.',
  'kit.howto.p2': 'Fazê-lo consultar primeiro: antes de agir, o agente descreve o problema em uma frase a /route/resolve — o diretório devolve a ferramenta que já existe, ou diz que não há.',
  'kit.howto.p3': 'Chamar: POSTs sem estado, sem chave no livre; a resposta traz seu sha256, a recusa traz campo + esperado + exemplo. Tudo o que há nesta página já funciona: uma linha instala o arquivo de skill, o diretório responde, as chamadas livres não têm chave.',
  'kit.plain.sum': 'Você não é desenvolvedor? Sem problema — a gente traduz.',
  'kit.plain.p1': 'Abra seu assistente de IA de sempre (Claude, ChatGPT, Grok, Copilot…).',
  'kit.plain.p2': 'Envie esta mensagem: "Leia https://mechacut.studio/SKILL-MINI.md e siga-o para os meus cálculos." Nada para instalar, nada para pagar, sem conta.',
  'kit.plain.p3': 'Depois peça a tarefa real: "30% e depois 20% de desconto dá quanto?", "quantos dias de atraso tem esta fatura?" Os números não saem mais da cabeça dele — saem da suíte, e são os mesmos para todos.',
  'kit.plain.p4': 'Pediu algo que a suíte não faz? Proponha em palavras simples — cada proposta é pública, e seu veredito também: entregue, em bancada ou recusado com o motivo nomeado, em /proposals.',
  'kit.dev.sum': 'Para desenvolvedores — três linhas, sem conta',
  'kit.propose': 'Proporcionar uma ferramenta: POST /api/v1/agent/propose — um contrato, nunca código; duplicado nomeado, evidência exibida, elegibilidade devolvida como blob pronto para commit. Nada é guardado no servidor. Skill do protocolo: /SKILL-KIT.md',
  'bench.d82.sum': 'Traces de chamadas julgadas: o mesmo gesto de agente nunca foi reemitido igual (0 de 14, V22b) e um retry multiplicou a fatura ×4 sem convergir (V17) — loop/doom-check agora diz DOOM, CYCLIC ou STORM sobre bytes canônicos, limiares nomeados.',
  'bench.d82.foot': 'Identidade em (ferramenta, args) canônicos: a ordem das chaves nunca esconde um loop. Duas chamadas iguais não são loop — o limiar é dito, nunca adivinhado. Todos os sinais reportados, veredito o mais grave. Fontes: bench/FINDINGS-V17.md · run22b.',
  'bench.e76.sum': 'O juiz do banco virou rota: eval/compare devolve OK ou WRONG com as divergências nomeadas — 2.5 versus "2.50" nunca é discordância, floats nunca são argumento.',
  'bench.e76.foot': 'Regra nascida do incidente do juiz V2 (ele copiava a própria expectativa): mesma quantidade nunca é divergência; quantidade diferente é nomeada por pointer, kind, expected, got. Decimal exato, nunca float.',
  'bench.a79.sum': 'Política como gramática fechada: check/allowlist devolve ALLOW, DENY ou AMBIGUOUS — a regra mais específica vence, empate sobe ao humano, silêncio nunca autoriza.',
  'bench.a79.foot': 'Uma ação em forma de regex é recusada, não avaliada: um gate que interpreta é porta dos fundos. Valores Decimal exatos, tabela ISO de moedas, default deny verdadeiro. A mesma lei do R3 do diretório, outro domínio.',
  'x402.h2': 'Pagamentos entre máquinas',
  'x402.p1': 'O caminho pago cabe em quatro bytes de protocolo: o servidor responde <code>402</code> com os requisitos; o agente assina uma transferência USDC EIP-3009; um facilitador verifica e liquida; a resposta reproduz a prova em <code>X-PAYMENT-RESPONSE</code>. O servidor não guarda chaves.',
  'x402.p2': 'Pagamentos repetidos são recusados. Erros em rotas pagas continuam grátis. O registro de cada recusa é público: <a href="/misses.json">/misses.json</a>.',
  'x402.bankr': 'Segunda casa: os quatro transforms pagos também estão no Cloud x402 do <a href="https://bankr.bot">Bankr</a> — mesmos caminhos, mesmos sha256: <a href="https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/chart_from_data">chart</a> &middot; <a href="https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/reshape_json">reshape</a> &middot; <a href="https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/validate_json">validate</a> &middot; <a href="https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/csv_join">csv-join</a>. Os demais vivem só aqui, gratuito incluso.',
  'vision.h2': 'Por que determinismo, por que agora',
  'vision.p1': 'Um grande modelo de linguagem é uma máquina de aproximar. Pergunte <code>sha256("abc")</code> e ele responde com confiança, elegância e erro. Peça para limpar o mesmo CSV todo dia e ele cobrará tokens para re-derivar o que uma função entrega em milissegundos — com os mesmos bytes, sempre.',
  'vision.p2': 'O computador de navegação Apollo tinha 4 KB de RAM. Pousou humanos na Lua porque a matemática nunca improvisou: cada constante, calculada uma vez, no solo, a frio, congelada na memória de corda.',
  'vision.quote': 'O determinismo foi codificado a primeira vez para nos levar à Lua. O determinismo levará a IA ao trabalho.',
  'nav.network': 'Rede',
  'network.h2': 'O catálogo é alimentado por agentes, julgado por bytes.',
  'network.creed': 'Um agente aprende. Todos os agentes sabem.',
  'network.intro': 'A porta é um endpoint, não um ticket: POST /api/v1/agent/propose — cinco campos, gramática fechada, um contrato e nunca código. Cada veredito pousa num registro público, append-only.',
  'network.ask.sum': 'O PEDIDO — cinco campos, zero código',
  'network.ask.body': 'name, purpose, examples (entrada → esperado), why, source (handle ou URL). O servidor devolve veredito nomeado — ELIGIBLE, SUSPECT-DUPLICATE, DUPLICATE-OF — e um blob pronto para commit. Nada fica no servidor: o registro vive no git, append-only.',
  'network.verdict.sum': 'O VEREDITO — o mesmo juiz para todo modelo',
  'network.verdict.body': 'Aceito = as mesmas portas que esta casa passa para si: golds traçados à mão antes do código, pins, AST-gate, suíte verde. O juiz é terceiro e byte-exato — o mesmo sha vale para Claude e Qwen. Recusa nomeada é desfecho do protocolo.',
  'network.loop.sum': 'O CICLO — um aprende, todos sabem',
  'network.loop.body': 'Contrato aceito vira chamada para cada agente da rede, com hash, desde o merge. O primeiro proponente externo é creditado na linha do registro. Divisão 50/50 decidida e a fábrica splitter está live na Base — divisões rodam on-chain, qualquer um pode verificar.',
  'network.proof': 'Entradas enviadas ao registro público — chegadas, vereditos e recusas, linha a linha',
  'vision.p3': 'Mechacut é essa matemática congelada para agentes: vocabulários fechados, contratos que recusam o que está fora da tabela, erros que nomeiam a forma esperada — o erro é o prompt que conserta. O significado fica com o modelo. A mecânica se muda para cá.',
  'contract.h2': 'O contrato',
  'x402.sum': 'Como uma máquina paga — 402, EIP-3009, facilitador, prova',
  'vision.sum': 'Por que determinismo, por que agora — Apollo, 4 KB, o dado',
  'contract.sum': 'As cinco promessas, verbatim',
  'contract.li1': 'Mesma requisição → mesmos bytes, sha256 em cada resposta',
  'contract.li2': 'Sem cadastro, sem chave, sem muro de taxa abaixo de 30 req/min',
  'contract.li3': 'Zero armazenamento: o único estado é uma janela de 1 minuto, um registro de 60 minutos e um conjunto de nonces de pagamento',
  'contract.li4': 'Vocabulários fechados — tudo fora da tabela é recusado, nomeado, apontado à forma esperada',
  'contract.li5': 'Erros que consertam: campo, mensagem, esperado, sempre',
  'contract.li6': 'Pagamentos x402 entre máquinas: USDC na Base, verificados por facilitador, zero humano no circuito',
  'agents.line': 'Fale agente: ferramentas MCP, GET /agent/manifest (a suíte inteira em uma requisição), GET /route?q=…, POST /api/v1/pipeline.',
  'agents.hint': 'instale um pack',
  'footer.family': 'Mechacut faz parte da família C.V. — veja moovicut.',
 },
}

BADGE = {"free": "\U0001f7e2", "cap": "\U0001f7e1", "paid": "\U0001f534"}
# A bare coloured square means nothing to a human (mobile review, 2026-11-21):
# the chip carries the word, the legend carries the rule, the dot carries
# a tooltip. Legend text is composed from these two tables — one source.
TIER_CHIP = {
    "en": {"free": "free", "cap": "free \u2264 32 KB", "paid": "paid"},
    "fr": {"free": "gratuit", "cap": "gratuit \u2264 32 Ko", "paid": "payant"},
    "pt": {"free": "gr\u00e1tis", "cap": "gr\u00e1tis \u2264 32 KB",
           "paid": "pago"},
}
TIER_RULE = {
    "en": {"free": "no key, no account",
           "cap": "402 above the cap",
           "paid": "HTTP 402 + x402 USDC on Base"},
    "fr": {"free": "sans cl\u00e9, sans compte",
           "cap": "402 au-del\u00e0 du plafond",
           "paid": "HTTP 402 + x402 USDC sur Base"},
    "pt": {"free": "sem chave, sem conta",
           "cap": "402 acima do teto",
           "paid": "HTTP 402 + x402 USDC na Base"},
}

TEMPLATE = """<!DOCTYPE html>
<html lang="{{LANG}}">
<head>
<meta charset="utf-8">
<link rel="canonical" href="https://mechacut.studio/">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{meta.title}}</title>
<meta name="description" content="{{meta.desc}}">
<meta property="og:image" content="https://mechacut.studio/static/brand/banner-2560.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://mechacut.studio/static/brand/banner-2560.jpg">
<link rel="icon" type="image/png" href="/static/brand/favicon-512.png">
<style>
@font-face{font-family:'Space Grotesk';font-style:normal;font-weight:400 700;
  font-display:swap;src:url('/static/fonts/SpaceGrotesk-var.woff2') format('woff2')}
@font-face{font-family:'IBM Plex Mono';font-style:normal;font-weight:400;
  font-display:swap;src:url('/static/fonts/IBMPlexMono-400.woff2') format('woff2')}
@font-face{font-family:'IBM Plex Mono';font-style:normal;font-weight:500;
  font-display:swap;src:url('/static/fonts/IBMPlexMono-500.woff2') format('woff2')}
@font-face{font-family:'Inter';font-style:normal;font-weight:400 500;
  font-display:swap;src:url('/static/fonts/Inter-var.woff2') format('woff2')}
  :root {
    --bg: #0a0a0a; --fg: #ececec; --muted: #8f8f8f;
    --gold: #d4af37; --line: #232323; --card: #121212;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body::before { content:""; position:fixed; top:0; bottom:0; left:8px; width:calc(50vw + 494px); z-index:-2; background:url(/static/brand/bg-hero.jpg?v=25-11d) no-repeat left top / 100% auto; }
  body::after { content:""; position:fixed; inset:0; z-index:-1; background:rgba(10,12,18,.74); }
  .plain { font-size:1.06em; color:var(--ink); max-width:880px; margin-top:40px; }
  .thesis { border-left:3px solid var(--gold); background:var(--card); border-radius:0 12px 12px 0; padding:14px 18px; margin:56px 0 16px; max-width:660px; }
  .thesis .th2 { margin:0; font-size:1.12em; font-weight:800; }
  .thesis .tcreed { margin:8px 0 6px; color:var(--gold); font-weight:700; font-size:1.05em; }
  .thesis a { color:var(--muted); font-family:'IBM Plex Mono',monospace; font-size:.86em; }
  .qa { display:grid; gap:10px; max-width:760px; margin:18px 0 10px; }
  .qrow { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:11px 15px; margin:0; }
  .qrow b { display:block; margin-top:5px; color:var(--gold); font-size:.9em; }
  .devhead { margin:34px 0 6px; padding-top:26px; border-top:1px solid var(--line); }
  body { background: var(--bg); color: var(--fg);
    font-family: "Inter", system-ui, -apple-system, sans-serif;
    line-height: 1.6; -webkit-font-smoothing: antialiased; }
  .wrap { max-width: 1020px; margin: 0 auto; padding: 0 24px; }
  main > section:first-of-type { padding-top: max(160px, 11vw); }
  .brandmark { position:fixed; top:14px; left:max(16px, calc(50vw - 726px)); z-index:60; }
  .brandmark img { display:block; border-radius:12px; height:104px; width:auto; }
  header.top { display: flex; align-items: center; justify-content: flex-end;
    padding: 20px 18px; border-bottom: 1px solid var(--line);
    position: sticky; top: 0; z-index: 50;
    background: rgba(10,10,12,.92); backdrop-filter: blur(8px); }
  #prog { position: fixed; top: 0; left: 0; height: 2px;
    background: var(--gold); width: 0; z-index: 60; }
  .brand { display: flex; align-items: center; gap: 12px;
    font-family: "Space Grotesk", sans-serif; font-weight: 700; letter-spacing: -.3px; }
  .brand svg, .brand img { display: block; }
  nav { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; }
  nav a { color: var(--muted); text-decoration: none; font-size: 14px;
    margin-left: 18px; transition: color .15s; }
  nav a:hover { color: var(--fg); }
  nav .lang { font-family: "IBM Plex Mono", monospace; font-size: 12px; letter-spacing: 1px; }
  nav .lang.cur { color: var(--gold); }
  main { padding: 70px 0 60px; }
  h1 { font-family: "Space Grotesk", sans-serif; font-weight: 700;
    font-size: clamp(30px, 5vw, 50px); line-height: 1.05; letter-spacing: -.5px;
    margin-bottom: 16px; }
  h1 .dim { color: var(--muted); }
  .why { font-size: 15px; font-weight: 400; line-height: 1.6; max-width: 880px; margin: 40px 0 0; color: var(--muted); }
  .why strong { color: var(--gold); font-weight: 600; }
  .lede { font-size: 16px; color: var(--muted); max-width: 880px; margin-bottom: 36px; }
  .lede strong { color: var(--fg); font-weight: 500; }
  .creed { font-size: 17px; font-style: italic; color: var(--fg);
    max-width: 680px; margin: 2px 0 26px; }
  .creed .sig { font-style: normal; color: var(--muted);
    font-size: 15px; letter-spacing: .02em; }
  .catbar { display: flex; gap: 14px; align-items: baseline;
    flex-wrap: wrap; margin-bottom: 14px; }
  #catsearch { flex: 1 1 240px; background: var(--card);
    border: 1px solid var(--line); border-radius: 10px; color: var(--fg);
    font: inherit; font-size: 14px; padding: 10px 14px; }
  #catsearch:focus { outline: 1px solid var(--gold); }
  .cathits { font-family: "IBM Plex Mono", monospace; font-size: 12px;
    color: var(--muted); white-space: nowrap; }
  .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
  .chip { font-family: "IBM Plex Mono", monospace; font-size: 12px;
    color: var(--muted); border: 1px solid var(--line);
    background: var(--card); border-radius: 999px; padding: 5px 11px;
    cursor: pointer; }
  .chip.on { color: var(--gold); border-color: #3a3320; background: #14110a; }
  .tierlegend { font-family: "IBM Plex Mono", monospace; font-size: 11.5px;
    color: var(--muted); margin: -6px 0 14px; line-height: 1.8; }
  .tierlegend .lg { white-space: nowrap; }
  @media (max-width: 640px) { .tierlegend .lg { white-space: normal; } }
  .catgrid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 10px; max-height: 30rem; overflow-y: auto; padding-right: 6px;
    scrollbar-width: thin; scrollbar-color: #333 transparent; }
  .tcard { text-align: left; background: var(--card);
    border: 1px solid var(--line); border-radius: 11px;
    padding: 12px 13px; color: var(--fg); font: inherit; cursor: pointer;
    display: flex; flex-direction: column; gap: 5px; }
  .tcard:hover, .tcard:focus-visible { border-color: #3a3320; }
  .tcard code { font-family: "IBM Plex Mono", monospace; font-size: 12.5px; }
  .tcard .tp { font-size: 12px; color: var(--muted);
    display: -webkit-box; -webkit-line-clamp: 2;
    -webkit-box-orient: vertical; overflow: hidden; }
  /* b125_hermes elagage STRUCTUREL : le span .tierdot (28 octets x 200
     cartes = ~5,6 k PAR PAGE) passe en ::before pilote par data-tier —
     meme badge, meme taille, zero repetition dans le markup. Precents :
     b110 (lignes vides), b119 (name hors hay), b124 (packlinks repliees).
     Le budget d'un outil neuf devient ~negatif pour la landing. */
  .tcard::before { font-size: 10px; margin-right: 2px; }
  .tcard[data-tier="free"]::before { content: "\1F7E2 "; }
  .tcard[data-tier="cap"]::before { content: "\1F7E1 "; }
  .tcard[data-tier="paid"]::before { content: "\1F534 "; }
  .tcard.hide { display: none; }
  #tptry { margin: 0 0 10px; }
  #tptry .tsay { font-size: 14px; margin: 0 0 6px; color: var(--fg); }
  #tptry .tsay b { color: var(--muted); font-weight: 500; font-size: 12px;
                   display: block; text-transform: uppercase;
                   letter-spacing: .06em; }
  #tptry .treq, #tptry .tgot { font: 12px/1.5 ui-monospace,
      SFMono-Regular, Menlo, monospace; background: var(--codebg, #0d1117);
      border-radius: 8px; padding: 8px 10px; overflow-x: auto;
      white-space: pre-wrap; word-break: break-all; margin: 0 0 6px; }
  #tptry .tgot { max-height: 9rem; overflow-y: auto; color: #9fd6a2; }
  .packlinks { margin-top: 14px; font-size: 13px; color: var(--muted); }
  .packlinks a { color: var(--gold); text-decoration: none; }
  .tpanel { position: fixed; top: 0; right: 0; width: 430px;
    max-width: 94vw; height: 100dvh; background: #101010;
    border-left: 1px solid var(--line); z-index: 60; padding: 20px 22px;
    overflow-y: auto; box-shadow: -18px 0 40px rgba(0, 0, 0, .5); }
  .tpanel[hidden] { display: none; }
  .tphead { display: flex; gap: 10px; align-items: center;
    flex-wrap: wrap; margin-bottom: 12px; }
  .tphead code { font-family: "IBM Plex Mono", monospace;
    color: var(--gold); font-size: 14px; }
  .tphead button { font: inherit; font-size: 12.5px;
    background: var(--card); color: var(--fg);
    border: 1px solid var(--line); border-radius: 8px; padding: 6px 10px;
    cursor: pointer; }
  .tphead .sp { flex: 1; }
  .tblwrap { overflow-x: auto; }
  .navbtn { display: none; font: inherit; font-size: 20px;
    background: none; border: 1px solid var(--line); border-radius: 8px;
    color: var(--fg); padding: 2px 10px; cursor: pointer; }
  @media (max-width: 1100px) { .catgrid { grid-template-columns: repeat(2, 1fr); } }
  @media (max-width: 1100px) { body::before { left:50%; transform:translateX(-50%); width:min(1020px,92vw); } }
  @media (max-width: 480px) {
    .catgrid { grid-template-columns: 1fr; }
    .navbtn { display: block; }
    .brandmark img { height:40px; }
    header.top nav { display: none; position: fixed; inset: 0;
      background: rgba(8, 8, 8, .97); flex-direction: column;
      align-items: flex-start; gap: 18px; padding: 84px 28px; z-index: 50; }
    header.top nav.open { display: flex; }
    .tpanel { width: 100vw; max-width: 100vw; border-left: none; }
  }
  h2 { font-family: "Space Grotesk", sans-serif; font-size: 25px;
    font-weight: 700; letter-spacing: -.3px; margin-bottom: 18px; }
  .section { margin-bottom: 56px; }
  .vision p { color: var(--muted); max-width: 720px; margin-bottom: 16px; font-size: 16.5px; }
  .vision p strong { color: var(--fg); font-weight: 500; }
  .playgrid { display: grid; grid-template-columns: repeat(auto-fit,
                minmax(250px, 1fr)); gap: 16px; margin-top: 26px; }
  .play { border: 1px solid var(--line); border-radius: 12px;
          padding: 18px 18px 14px; background: var(--bg2, transparent); }
  .play h3 { margin: 0 0 10px; font-size: 16px; }
  .playsay { font-size: 15px; margin: 0 0 12px; color: var(--fg); }
  .playgot { font: 12.5px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace;
             background: var(--codebg, #0d1117); border-radius: 8px;
             padding: 10px 12px; overflow-x: auto; margin: 0 0 12px; }
  .playwhy { font-size: 13.5px; color: var(--muted); margin: 0; }
  .connect { margin-top: 26px; }
  .connect #connectcmd { user-select: all; }
  .copybtn { margin-top: 8px; background: none; border: 1px solid
             var(--line); color: var(--muted); border-radius: 8px;
             padding: 8px 14px; font-size: 12.5px; min-height: 40px;
             cursor: pointer; }
  .copybtn:hover, .copybtn:focus-visible { color: var(--fg);
             border-color: #3a3320; }
  .vision p code, .tiers p code, .x402 p code { font-family: "IBM Plex Mono", monospace;
    font-size: 14px; color: var(--fg); background: #1c1c1c; padding: 1px 6px; border-radius: 5px; }
  .vision .quote, .quote { border-left: 2px solid var(--gold); padding-left: 20px;
    margin: 30px 0; font-size: 18px; color: var(--fg);
    font-family: "Space Grotesk", sans-serif; }
  ul.contract { list-style: none; display: grid;
    grid-template-columns: repeat(2, 1fr); gap: 12px 30px; max-width: 760px; }
  @media (max-width: 640px) { ul.contract { grid-template-columns: 1fr; } }
  ul.contract li { color: var(--muted); font-size: 15px; display: flex; gap: 10px; }
  ul.contract li::before { content: "\\2192"; color: var(--gold); flex-shrink: 0; }
  table.bench { border-collapse: collapse; width: 100%; max-width: 760px;
    font-family: "IBM Plex Mono", monospace; font-size: 14px; }
  table.bench th { text-align: left; color: var(--muted); font-weight: 400;
    font-size: 12px; letter-spacing: .5px; padding: 8px 18px 8px 0;
    border-bottom: 1px solid var(--line); }
  table.bench td { padding: 10px 18px 10px 0; border-bottom: 1px solid var(--line); }
  td.yes { color: #7fd47f; } td.no { color: #d47f7f; }
  td.num { color: var(--muted); }
  .tiers p, .x402 p { color: var(--muted); max-width: 720px; margin-bottom: 14px; font-size: 15.5px; }
  .tiers p a, .x402 p a { color: var(--gold); }
  pre { background: #0d0d0d; border: 1px solid var(--line); border-radius: 12px;
    padding: 22px 24px; overflow-x: auto; font-family: "IBM Plex Mono",
    monospace; font-size: 13px; line-height: 1.7; color: #d8d8d8; margin: 20px 0; }
  footer { border-top: 1px solid var(--line); padding: 34px 0 48px;
    color: var(--muted); font-size: 13.5px; }
  footer .row { display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
  footer a { color: var(--muted); text-decoration: none; }
  footer a:hover { color: var(--fg); }
  .pill { display: inline-block; font-family: "IBM Plex Mono", monospace;
    font-size: 11.5px; letter-spacing: 1px; text-transform: uppercase;
    color: var(--gold); border: 1px solid #3a3320; background: #14110a;
    padding: 5px 12px; border-radius: 999px; margin-bottom: 18px; }
  .demo { border: 1px solid var(--line); border-radius: 12px;
    background: var(--card); margin: 26px 0 8px; }
  .demo .dh { padding: 11px 16px; border-bottom: 1px solid var(--line);
    font-family: "IBM Plex Mono", monospace; font-size: 11.5px;
    letter-spacing: 1px; text-transform: uppercase; color: var(--gold); }
  .demo .dr { display: flex; gap: 10px; padding: 14px 16px; flex-wrap: wrap; }
  .demo input { flex: 1 1 240px; background: #0d0d0d; border: 1px solid var(--line);
    border-radius: 8px; color: var(--fg); font-family: "IBM Plex Mono", monospace;
    font-size: 13.5px; padding: 10px 12px; }
  .demo input:focus { outline: 1px solid var(--gold); }
  .demo button { background: var(--gold); color: #0b0b0d; border: 0; border-radius: 8px;
    font-weight: 600; font-size: 14px; padding: 10px 18px; min-height: 40px; cursor: pointer; }
  .demo pre { margin: 0; border: 0; border-top: 1px solid var(--line);
    border-radius: 0 0 12px 12px; min-height: 64px; }
  .tcard .tp{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
  .mgrid{display:grid;grid-template-columns:1fr;gap:12px;max-width:860px}
  .mcard{border-left:2px solid var(--gold);padding:16px 22px;background:var(--card);border-radius:0 10px 10px 0}
  .mcard q{display:block;color:var(--fg);font-size:14.5px;line-height:1.55;font-style:italic}
  .mcard cite{display:block;margin-top:10px;font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:var(--muted);font-style:normal}
  .mcard cite b{color:var(--gold);font-weight:400}
  .mcard cite a{color:var(--muted)}
.bcard{border:1px solid var(--line,#232b3d);border-radius:10px;margin:10px 0;background:var(--card,#121724)}\n.bcard summary{cursor:pointer;padding:13px 16px;font-weight:700;color:var(--ink,#e8ecf4);list-style-position:outside}\n.bcard summary .bv{color:var(--gold,#ffcf5c);margin-right:10px}\n.bcard .bbody{padding:4px 18px 16px}\n.bgroup{color:var(--gold,#ffcf5c);margin:30px 0 8px;font-size:1.08em;letter-spacing:.02em}
.bgroupd{border:1px solid var(--line);border-radius:10px;margin:12px 0;background:var(--card)}
.bgroupd>summary{cursor:pointer;padding:13px 16px;font-weight:700;color:var(--gold);list-style:none;display:flex;justify-content:space-between;align-items:center}
.bgroupd>summary::-webkit-details-marker{display:none}
.bgroupd>summary::after{content:'+';font-family:'IBM Plex Mono',monospace;font-size:18px}
.bgroupd[open]>summary::after{content:'\2013'}
.bgroupd .bin{padding:0 14px 12px}\n</style>
</head>
<body>
<div id="prog"></div>
<div class="wrap">

  <header class="top">
    <nav>
      <a href="#everyday">{{nav.everyday}}</a>
      <a href="#bundles">{{nav.tools}}</a>
      <a href="#bench">{{nav.numbers}}</a>
      <a href="#market">{{nav.market}}</a>
      <a href="#network">{{nav.network}}</a>
      <a href="#kit">{{nav.kit}}</a>
      <a href="#build">{{nav.build}}</a>
      <a href="#vision">{{nav.vision}}</a>
      <a href="#contract">{{nav.api}}</a>
      <a href="/agent/manifest">manifest</a>
      <a class="lang{{cur.en}}" href="?lang=en">EN</a>
      <a class="lang{{cur.fr}}" href="?lang=fr">FR</a>
      <a class="lang{{cur.pt}}" href="?lang=pt">PT</a>
    </nav>
    <button class="navbtn" id="navbtn" aria-label="{{nav.menu}}">&#9776;</button>
  </header>

  <main>
    <section>
      <div class="pill">{{pill}}</div>
      <h1>{{hero1}}<br><span class="dim">{{hero2}}</span></h1>
      <p class="creed">{{hero3}}<span class="sig"> — C.V.</span></p>
      <p class="lede">{{lede}}</p>
      <p class="plain">{{hero.plain}}</p>
      <p class="why">{{hero.why}}</p>
      <div class="thesis">
        <p class="th2">{{network.h2}}</p>
        <p class="tcreed">{{network.creed}}</p>
        <a href="#network">{{nav.network}} →</a>
      </div>
      <div class="demo">
        <div class="dh"><span>{{demo.title}}</span></div>
        <div class="dr">
          <input id="dexpr" value='{"value": 2.675, "places": 2}' spellcheck="false" aria-label="payload">
          <button id="drun" type="button">{{demo.run}}</button>
        </div>
        <pre id="dout" data-err="{{demo.err}}">{{demo.hint}}</pre>
      </div>
    </section>

    {{everyday_grid}}

    <section class="devhead">
      <h2>{{dev.h2}}</h2>
      <p class="tiers" style="color:var(--muted)">{{dev.intro}}</p>
    </section>

    <section class="section" id="bundles">
      <h2>{{bundles.h2}}</h2>
      <p class="quote">{{bundles.creed}}</p>
      <p class="tiers" style="color: var(--muted); max-width: 720px; margin-bottom: 26px;">{{bundles.intro}}</p>
      <div class="catbar">
        <input id="catsearch" type="search" placeholder="{{cat.search}}" aria-label="{{cat.search}}">
        <span class="cathits" id="cathits" data-tpl="{{cat.hits}}"></span>
      </div>
      <div id="cattray">
{{bundles_grid}}
      </div>
    </section>
    <aside class="tpanel" id="tpanel" hidden>
      <div class="tphead">
        <code id="tpname"></code><span class="sp"></span>
        <button id="tpcopy" data-copied="{{panel.copied}}">{{panel.copy}}</button>
        <button id="tpclose">{{panel.close}} &#10005;</button>
      </div>
      <div id="tptry" hidden></div>
      <pre id="tpbody"></pre>
    </aside>

    <section class="section" id="market">
      <h2>{{market.h2}}</h2>
      <p class="quote">{{market.creed}}</p>
{{market_grid}}
    </section>

    <section class="section" id="network">
      <h2>{{network.h2}}</h2>
      <p class="quote">{{network.creed}}</p>
      <p class="tiers" style="color: var(--muted); max-width: 720px; margin-bottom: 26px;">{{network.intro}}</p>
      <details class="bcard">
        <summary>{{network.ask.sum}}</summary>
        <div class="bbody"><p class="tiers" style="color: var(--muted);">{{network.ask.body}}</p></div>
      </details>
      <details class="bcard">
        <summary>{{network.verdict.sum}}</summary>
        <div class="bbody"><p class="tiers" style="color: var(--muted);">{{network.verdict.body}}</p></div>
      </details>
      <details class="bcard">
        <summary>{{network.loop.sum}}</summary>
        <div class="bbody"><p class="tiers" style="color: var(--muted);">{{network.loop.body}}</p></div>
      </details>
      <p class="tiers" style="margin-top: 14px;"><a href="/proposals">{{network.proof}}</a></p>
    </section>

<section class="section" id="kit">
      <h2>{{kit.h2}}</h2>
      <p class="quote">{{kit.creed}}</p>
      <p class="tiers" style="color: var(--muted); max-width: 720px;">{{kit.intro}}</p>
      <details class="bcard" open>
        <summary>{{kit.plain.sum}}</summary>
        <div class="bbody">
          <ol class="tiers" style="color: var(--muted); max-width: 720px;">
            <li>{{kit.plain.p1}}</li>
            <li>{{kit.plain.p2}}</li>
            <li>{{kit.plain.p3}}</li>
            <li>{{kit.plain.p4}}</li>
          </ol>
        </div>
      </details>
      <details class="bcard">
        <summary>{{kit.dev.sum}}</summary>
        <div class="bbody">
          <ol class="tiers" style="color: var(--muted); max-width: 720px;">
            <li>{{kit.howto.p1}}</li>
            <li>{{kit.howto.p2}}</li>
            <li>{{kit.howto.p3}}</li>
          </ol>
        </div>
      </details>
      <details class="bcard">
        <summary>{{kit.c1.sum}}</summary>
        <div class="bbody"><p class="tiers" style="color: var(--muted);">{{kit.c1.foot}}</p></div>
      </details>
      <details class="bcard">
        <summary>{{kit.c2.sum}}</summary>
        <div class="bbody"><p class="tiers" style="color: var(--muted);">{{kit.c2.foot}}</p></div>
      </details>
      <details class="bcard">
        <summary>{{kit.c3.sum}}</summary>
        <div class="bbody"><p class="tiers" style="color: var(--muted);">{{kit.c3.foot}}</p></div>
      </details>
      <p class="tiers" style="margin-top: 14px;"><a href="https://github.com/mechacut/mechacut/blob/master/PROTOCOL-KIT.md">PROTOCOL-KIT.md</a> · <a href="https://github.com/mechacut/mechacut/blob/master/SKILL-NETWORK.md">SKILL-NETWORK.md</a></p>
      <p class="tiers" style="margin-top: 10px;">{{kit.propose}}</p>
    </section>


    <section class="section tiers" id="tiers">
      <h2>{{tiers.h2}}</h2>
      <p>{{tiers.intro}}</p>
    </section>

    <section class="section" id="bench">
      <h2>{{bench.h2}}</h2>
      <p class="quote">{{bench.creed}}</p>
      <p class="tiers" style="color: var(--muted); max-width: 720px;">{{bench.intro}}</p>
      <details class="bgroupd"><summary>{{bench.g1}}</summary><div class="bin">
          <details class="bcard">
        <summary><span class="bv">v6</span>{{bench.v6.sum}}</summary>
        <div class="bbody">
          <div class="tblwrap"><table>
            <tr><th>{{bench.model}}</th><th>{{bench.alone}}</th><th>{{bench.with}}</th><th>{{bench.tokens}}</th></tr>
{{bench_rows}}          </table></div>
          <p class="tiers" style="margin-top: 12px;">{{bench.foot}}</p>
        </div>
      </details>
          <details class="bcard">
        <summary><span class="bv">v9</span>{{bench.v9.sum}}</summary>
        <div class="bbody">
          <p class="tiers" style="color: var(--muted);">{{bench9.intro}}</p>
          <div class="tblwrap"><table>
            <tr><th>{{bench.model}}</th><th>{{bench.alone}}</th><th>{{bench9.with}}</th><th>{{bench.tokens}}</th></tr>
{{bench9_rows}}          </table></div>
          <p class="tiers" style="margin-top: 12px;">{{bench9.foot}}</p>
        </div>
      </details>
          <details class="bcard">
        <summary><span class="bv">v10</span>{{bench.v10.sum}}</summary>
        <div class="bbody">
          <p class="tiers" style="color: var(--muted);">{{bench10.intro}}</p>
          <div class="tblwrap"><table>
            <tr><th>{{bench.model}}</th><th>{{bench.alone}}</th><th>{{bench10.with}}</th><th>{{bench.tokens}}</th></tr>
{{bench10_rows}}          </table></div>
          <p class="tiers" style="margin-top: 12px;">{{bench10.foot}}</p>
        </div>
      </details>
          <details class="bcard">
        <summary><span class="bv">v11</span>{{bench.v11.sum}}</summary>
        <div class="bbody">
          <p class="tiers" style="color: var(--muted);">{{bench.v11.foot}}</p>
        </div>
      </details>
          <details class="bcard">
        <summary><span class="bv">v12</span>{{bench.v12.sum}}</summary>
        <div class="bbody">
          <p class="tiers" style="color: var(--muted);">{{bench12.intro}}</p>
          <div class="tblwrap"><table>
            <tr><th>{{bench.model}}</th><th>{{bench.alone}}</th><th>{{bench12.code}}</th><th>{{bench12.relay}}</th></tr>
{{bench12_rows}}          </table></div>
          <p class="tiers" style="margin-top: 12px;">{{bench12.foot}}</p>
        </div>
      </details>
            </div></details><details class="bgroupd"><summary>{{bench.g2}}</summary><div class="bin">
          <details class="bcard">
        <summary><span class="bv">v15</span>{{bench.v15.sum}}</summary>
        <div class="bbody">
          <p class="tiers" style="color: var(--muted);">{{bench.v15.intro}}</p>
          <p class="tiers">{{bench.v15.foot}}</p>
        </div>
      </details>
          <details class="bcard">
        <summary><span class="bv">v17</span>{{bench.v17.sum}}</summary>
        <div class="bbody">
          <p class="tiers" style="color: var(--muted);">{{bench.v17.intro}}</p>
          <div class="tblwrap"><table>
            <tr><th>{{bench.model}}</th><th>{{bench.v17.nu}}</th><th>{{bench.v17.retry}}</th><th>{{bench.v17.relay}}</th></tr>
{{bench17_rows}}          </table></div>
          <p class="tiers" style="margin-top: 12px;">{{bench.v17.foot}}</p>
        </div>
      </details>
          <details class="bcard">
        <summary><span class="bv">F5</span>{{bench.f5.sum}}</summary>
        <div class="bbody">
          <p class="tiers" style="color: var(--muted);">{{bench.f5.foot}}</p>
        </div>
      </details>
      <details class="bcard">
        <summary><span class="bv">F7</span>{{bench.f7.sum}}</summary>
        <div class="bbody">
          <p class="tiers" style="color: var(--muted);">{{bench.f7.foot}}</p>
        </div>
      </details>
              <details class="bcard">
        <summary><span class="bv">D82</span>{{bench.d82.sum}}</summary>
        <div class="bbody">
          <p class="tiers" style="color: var(--muted);">{{bench.d82.foot}}</p>
        </div>
      </details>
          <details class="bcard">
        <summary><span class="bv">E76</span>{{bench.e76.sum}}</summary>
        <div class="bbody">
          <p class="tiers" style="color: var(--muted);">{{bench.e76.foot}}</p>
        </div>
      </details>
          <details class="bcard">
        <summary><span class="bv">A79</span>{{bench.a79.sum}}</summary>
        <div class="bbody">
          <p class="tiers" style="color: var(--muted);">{{bench.a79.foot}}</p>
        </div>
      </details>
      <details class="bcard" open>
        <summary><span class="bv">v23</span>{{bench.v23.sum}}</summary>
        <div class="bbody">
          <p class="tiers" style="color: var(--muted);">{{bench.v23.intro}}</p>
          <div class="tblwrap"><table>
            <tr><th>{{bench.v23.arm}}</th><th>{{bench.v23.wins}}</th><th>{{bench.v23.usd}}</th></tr>
{{bench23_rows}}          </table></div>
          <p class="tiers" style="margin-top: 12px;">{{bench.v23.foot}}</p>
        </div>
      </details>
            </div></details><details class="bgroupd"><summary>{{bench.g3}}</summary><div class="bin">
          <details class="bcard">
        <summary><span class="bv">v16</span>{{bench.v16.sum}}</summary>
        <div class="bbody">
          <p class="tiers" style="color: var(--muted);">{{bench.v16.intro}}</p>
          <p class="tiers">{{bench.v16.foot}}</p>
        </div>
      </details>
          <details class="bcard">
        <summary><span class="bv">v20</span>{{bench.v20.sum}}</summary>
        <div class="bbody">
          <p class="tiers" style="color: var(--muted);">{{bench.v20.intro}}</p>
          <div class="tblwrap"><table>
            <tr><th>{{bench.v20.model}}</th><th>{{bench.v20.naked}}</th><th>{{bench.v20.locked}}</th></tr>
{{bench20_rows}}          </table></div>
          <p class="tiers" style="margin-top: 12px;">{{bench.v20.foot}}</p>
        </div>
      </details>
          <details class="bcard">
        <summary><span class="bv">v22</span>{{bench.v22.sum}}</summary>
        <div class="bbody">
          <p class="tiers" style="color: var(--muted);">{{bench.v22.foot}}</p>
        </div>
      </details>
          <details class="bcard">
        <summary><span class="bv">v22b</span>{{bench.v22b.sum}}</summary>
        <div class="bbody">
          <p class="tiers" style="color: var(--muted);">{{bench.v22b.foot}}</p>
        </div>
      </details>
            </div></details><details class="bgroupd"><summary>{{bench.g4}}</summary><div class="bin">
          <details class="bcard">
        <summary><span class="bv">v13</span>{{bench.v13.sum}}</summary>
        <div class="bbody">
          <p class="tiers" style="color: var(--muted);">{{bench.v13.foot}}</p>
        </div>
      </details>
          <details class="bcard">
        <summary><span class="bv">v14</span>{{bench.v14.sum}}</summary>
        <div class="bbody">
          <p class="tiers" style="color: var(--muted);">{{bench.v14.foot}}</p>
        </div>
      </details>
            </div></details><details class="bgroupd"><summary>{{bench.g5}}</summary><div class="bin">
          <details class="bcard">
        <summary><span class="bv">v19</span>{{bench.v19.sum}}</summary>
        <div class="bbody">
          <p class="tiers" style="color: var(--muted);">{{bench.v19.intro}}</p>
          <div class="tblwrap"><table>
            <tr><th>{{bench.v19.arm}}</th><th>{{bench.v19.right}}</th><th>{{bench.v19.distinct}}</th><th>{{bench.tokens}}</th></tr>
{{bench19_rows}}          </table></div>
          <p class="tiers" style="margin-top: 12px;">{{bench.v19.foot}}</p>
        </div>
      </details>
          <details class="bcard">
        <summary><span class="bv">v24</span>{{bench.v24.sum}}</summary>
        <div class="bbody">
          <p class="tiers" style="color: var(--muted);">{{bench.v24.foot}}</p>
        </div>
      </details>
          </section>

    </div></details><section class="section build" id="build">
      <h2>{{build.h2}}</h2>
      <p class="tiers" style="color: var(--muted); max-width: 720px;">{{build.intro}}</p>
      <div class="playgrid">
        <div class="play"><h3>{{build.r1.name}}</h3>
          <p class="playsay">{{build.r1.say}}</p>
          <pre class="playgot">{{build.r1.got}}</pre>
          <p class="playwhy">{{build.r1.why}}</p></div>
        <div class="play"><h3>{{build.r2.name}}</h3>
          <p class="playsay">{{build.r2.say}}</p>
          <pre class="playgot">{{build.r2.got}}</pre>
          <p class="playwhy">{{build.r2.why}}</p></div>
        <div class="play"><h3>{{build.r3.name}}</h3>
          <p class="playsay">{{build.r3.say}}</p>
          <pre class="playgot">{{build.r3.got}}</pre>
          <p class="playwhy">{{build.r3.why}}</p></div>
      </div>
      <div class="connect">
        <p class="playwhy">{{build.connect}}</p>
        <pre class="playgot" id="connectcmd">Read https://mechacut.studio/SKILL-MINI.md and follow it before any mechanical task.</pre>
        <button class="copybtn" data-for="connectcmd" data-copied="{{panel.copied}}">{{panel.copy}}</button>
      </div>
    </section>

    <section class="section x402" id="x402">
      <h2>{{x402.h2}}</h2>
      <details class="bcard">
        <summary>{{x402.sum}}</summary>
        <div class="bbody">
      <p>{{x402.p1}}</p>
      <p>{{x402.p2}}</p>
      <p>{{x402.bankr}}</p>
        </div>
      </details>
    </section>

    <section class="section vision" id="vision">
      <h2>{{vision.h2}}</h2>
      <details class="bcard">
        <summary>{{vision.sum}}</summary>
        <div class="bbody">
      <p>{{vision.p1}}</p>
      <p>{{vision.p2}}</p>
      <div class="quote">{{vision.quote}}</div>
      <p>{{vision.p3}}</p>
        </div>
      </details>
    </section>

    <section class="section" id="contract">
      <h2>{{contract.h2}}</h2>
      <details class="bcard" open>
        <summary>{{contract.sum}}</summary>
        <div class="bbody">
      <ul class="contract">
        <li>{{contract.li1}}</li>
        <li>{{contract.li2}}</li>
        <li>{{contract.li3}}</li>
        <li>{{contract.li4}}</li>
        <li>{{contract.li5}}</li>
        <li>{{contract.li6}}</li>
      </ul>
      <div class="quote" style="margin: 30px 0 0 0;">{{agents.line}}</div>
      <p style="color: var(--muted); font-size: 15px; margin-top: 18px;">
        {{agents.hint}} — <a href="/mcp">/mcp</a> · <a href="/SKILL.md">/SKILL.md</a> · <a href="/openapi.json">/openapi.json</a>
      </p>
        </div>
      </details>
    </section>
  </main>

  <footer>
    <div class="row">
      <div>{{footer.family}}</div>
      <div><a href="/misses.json">/misses.json</a> · <a href="/route?q=dirty%20csv%20into%20yaml">/route</a> · <a href="/api/v1/recipes">/recipes</a></div>
      <div><a href="https://github.com/mechacut/mechacut" rel="me">GitHub</a> · <a href="https://x.com/Davincc" rel="me">Follow on X</a></div>
    </div>
  </footer>

</div>
<script>
(function () {
  var cards = Array.prototype.slice.call(document.querySelectorAll(".tcard"));
  var hits = document.getElementById("cathits");
  var search = document.getElementById("catsearch");
  var tray = document.getElementById("cattray");
  var panel = document.getElementById("tpanel");
  var pname = document.getElementById("tpname");
  var pbody = document.getElementById("tpbody");
  var trybox = document.getElementById("tptry");
  var trycmd = "";
  var LBL = {say: "{{panel.say}}", got: "{{panel.got}}"};
  var copyb = document.getElementById("tpcopy");
  var closeb = document.getElementById("tpclose");
  var pack = "all", tier = "all", w = "", last = null,
      topmode = true;
  function ok(c) {
    return (pack === "all" || c.dataset.pack === pack) &&
           (tier === "all" || c.dataset.tier === tier) &&
           (!topmode || w !== "" || c.dataset.top === "1") &&
           (!w || c.dataset.tool.indexOf(w) >= 0 ||
                  c.dataset.hay.indexOf(w) >= 0);
  }
  function apply() {
    var n = 0;
    cards.forEach(function (c) {
      var v = ok(c); c.classList.toggle("hide", !v); if (v) n++;
    });
    if (hits) hits.textContent =
      hits.dataset.tpl.replace("~n~", n).replace("~t~", cards.length);
  }
  if (tray) tray.addEventListener("click", function (e) {
    var chip = e.target.closest(".chip");
    if (chip) {
      var kv = chip.dataset.f.split("=");
      if (kv[0] === "top") { topmode = true; pack = "all"; tier = "all"; }
      else if (kv[0] === "x") { topmode = false; pack = "all"; tier = "all"; }
      else if (kv[0] === "pack") { topmode = false; pack = kv[1]; }
      else { topmode = false; tier = kv[1]; }
      tray.querySelectorAll(".chip").forEach(function (c) {
        var k2 = c.dataset.f.split("=");
        var on = k2[0] === "top" ? topmode
             : k2[0] === "x" ? (!topmode && pack === "all" && tier === "all")
             : k2[0] === "pack" ? (pack === k2[1]) : (tier === k2[1]);
        c.classList.toggle("on", on);
      });
      apply();
      return;
    }
    var card = e.target.closest(".tcard");
    if (card) {
      last = card;
      pname.textContent = card.dataset.tool;
      pbody.textContent = "\u2026";
      trybox.hidden = true; trybox.innerHTML = ""; trycmd = "";
      panel.hidden = false;
      fetch("/tools/" + card.dataset.tool + ".json")
        .then(function (r) { return r.json(); })
        .then(function (j) {
          pbody.textContent = JSON.stringify(j, null, 2);
          if (j && j.try) {
            var t = j.try, esc = function (x) {
              return String(x).replace(/&/g, "&amp;")
                              .replace(/</g, "&lt;"); };
            var h = "";
            var sv = t.say;
            if (sv && typeof sv === "object") {
              var L = (document.documentElement.lang || "en")
                      .slice(0, 2);
              sv = sv[L] || sv.en;
            }
            if (sv) h += '<p class="tsay"><b>' + LBL.say +
                         '</b>' + esc(sv) + "</p>";
            if (t.request && t.request.body !== null &&
                t.request.body !== undefined) {
              var body = JSON.stringify(t.request.body);
              trycmd = "curl -s -X POST https://" + location.host +
                       t.request.path +
                       " -H 'content-type: application/json' -d '" +
                       body.replace(/'/g, "'\\''") + "'";
              h += '<pre class="treq">POST ' + t.request.path + "\\n" +
                   esc(body) + "</pre>";
            }
            if (t.response) h += '<p class="tsay"><b>' + LBL.got +
                                '</b></p><pre class="tgot">' +
                                esc(t.response) + "</pre>";
            trybox.innerHTML = h;
            trybox.hidden = false;
          }
        })
        .catch(function () { pbody.textContent = "schema unavailable"; });
      closeb.focus();
    }
  });
  function closep() { panel.hidden = true; if (last) last.focus(); }
  if (copyb) copyb.addEventListener("click", function () {
    // b116: nom vide => copie /agent/manifest, jamais un /tools/.json 404
    var cmd = trycmd || (pname.textContent
        ? "curl -s https://" + location.host + "/tools/" +
          pname.textContent + ".json"
        : "curl -s https://" + location.host + "/agent/manifest");
    if (navigator.clipboard) navigator.clipboard.writeText(cmd).then(
      function () { copyb.textContent = copyb.dataset.copied; });
  });
  if (closeb) closeb.addEventListener("click", closep);
  document.querySelectorAll(".copybtn").forEach(function (b) {
    b.addEventListener("click", function () {
      var t = document.getElementById(b.dataset.for);
      if (!t || !navigator.clipboard) { return; }
      navigator.clipboard.writeText(t.textContent.trim()).then(
        function () { var o = b.textContent; b.textContent =
          b.dataset.copied || "copied";
          setTimeout(function () { b.textContent = o; }, 1600); });
    });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && panel && !panel.hidden) closep();
  });
  if (search) search.addEventListener("input", function () {
    w = search.value.trim().toLowerCase(); apply();
  });
  var navbtn = document.getElementById("navbtn");
  if (navbtn) navbtn.addEventListener("click", function () {
    document.querySelector("header.top nav").classList.toggle("open");
  });
  document.querySelectorAll("header.top nav a").forEach(function (a) {
    a.addEventListener("click", function () {
      document.querySelector("header.top nav").classList.remove("open");
    });
  });
  apply();
})();

(function () {
  var run = document.getElementById("drun"); if (!run) return;
  var out = document.getElementById("dout"), inp = document.getElementById("dexpr");
  run.addEventListener("click", function () {
    out.textContent = "\u2026";
    fetch("/api/v1/num/round", { method: "POST",
      headers: { "content-type": "application/json" }, body: inp.value || "{}" })
      .then(function (r) { return r.json().then(function (j) { return [r.status, j]; }); })
      .then(function (res) { out.textContent = res[0] + " " + JSON.stringify(res[1], null, 1); })
      .catch(function () { out.textContent = out.getAttribute("data-err"); });
  });
  var p = document.getElementById("prog");
  addEventListener("scroll", function () {
    var d = document.documentElement;
    p.style.width = (d.scrollTop / (d.scrollHeight - d.clientHeight) * 100) + "%";
  });
})();
</script>
</body>
</html>
"""


PACK_LABEL_EXTRA = {"en": "skill packs:", "fr": "packs de compétences :",
                    "pt": "pacotes de skills:"}
TOP10 = {  # le catalogue grand public : ce que « pour tout le monde » utilise
    "qr_generate", "csv_excel_damage", "csv_excel_display", "money_baggage",
    "money_discount", "money_split", "money_unitprice", "date_relative",
    "validate_iban", "money_flight_comp",
}
CAT_TOP10 = {"en": "\u2605 Top 10", "fr": "\u2605 Le top 10",
             "pt": "\u2605 Top 10"}

PURPOSES = {  # catalogue FR/PT — traduits 24-11 par trois enfants,
                # validés nom par nom + chiffres par chiffres au merge
    "fr": {
        "stats_rate_ci":
            "k sur n → taux OBSERVÉ et centre WILSON séparés et nommés, intervalle 95 % — le 65,2 % seul est un mensonge de précision",
        "pdf_provenance":
            "ce que les octets d'un PDF avouent : outil qui l'a écrit, dates prétendues, ordre possible ou NON — null nommé, jamais deviné",
        "text_mojibake":
            "scan deux couches SANS réparer : familles d'encodage comptées, needles de contexte nommés — serão ne compte JAMAIS comme serã",
        "address_parse":
            "adresse postale → pays, code postal validé contre 50 grammaires, lignes restantes ; ambiguïté NOMMÉE, jamais devinée",
        "date_civil":
            "instant + zone IANA nommée → la date civile que cette zone habite ; glissement d'exercice signalé, fuseau du serveur jamais lu",
        "text_fold_report":
            "qu'une suppression d'accents ou de casse EFFACE une identité distincte — rapporté, nommé ; le pliage lui-même reste à l'appelant",
        "text_novel_words":
            "description contre titre : les mots nouveaux comptés par item, les flux écho nommés, borne dite (défaut 3)",
        "date_window":
            "bornes d'une clause (min..max jours avant/après un "     "événement) → la fenêtre INCLUSIVE entière, span et sens dits ; "     "bornes inversées refusées par nom (on ne trie pas un contrat)",
        "date_deemed":
            "date d'envoi + mode d'envoi → réception réputée ; sans mode, pas de date (table fermée nommée, override argument déclaré)",
        "net_ratelimit":
            "en-têtes Retry-After et X-RateLimit-* lus (delta-seconds ou IMF-fixdate strict) ; en désaccord les deux attendus NOMMÉS, jamais choisis ; now est un argument, jamais l’horloge murale",
        "number_words_pair":
            "forme écrite et forme chiffrée vérifiées l’une contre l’autre — trente (40) refuse : AGREE/MISMATCH/NO_PAIR, les deux valeurs gardées",
        "agent_mcpaudit":
            "la liste d'outils MCP collée jugée contre des "
            "règles de rejet nommées, avant qu'un client ne "
            "la descarte en silence",
        "agent_mcpsurface":
            "empreinte SHA-256 de la surface MCP collée, dérive NOMMÉE contre relevé antérieur — annotations canoniquées à leurs défauts publics, angle mort du AI SDK fermé ; ordre dans le contrat",
        "agent_contexttax":
            "combien coûte VOTRE liste MCP collée, octets et tokens (estimateur chars÷4 publié, plancher déclaré), par outil et champ — names-only chiffré, facture PAR TOUR, dollars à VOTRE prix ; ici COMBIEN",
        "agent_costdiff":
            "le PRIX DE L'UPDATE : deux listings MCP collés, surplus par outil et champ signé, % du côté avant ; delta global, somme par outil, divergence CHIFFRÉE ; ici DE COMBIEN À COMBIEN",
        "agent_tooltrim":
            "QUOI DÉBRANCHER pour tenir le budget : IDLE-d'abord, fractions exactes, re-compte au canon context-tax ; FITS/STILL_OVER, RESTE chiffré ; la fratrie dit COMBIEN, ici QUOI ENLEVER",
        "agent_tooloverlap":
            "QUELS DEUX OUTILS N'EN FONT QU'UN, dans QUEL CLIENT : coupe 64 chars VS Code avec ABORT alphabétique (repro publié : 5 outils, 2 listés), pliage gemini-cli tête30+queue30 avec OVERWRITE, coupe de gateway sans contrôle ; correction en NOMBRE — la clef serveur la plus courte qui dé-colle, sinon NO_PREFIX_FIX ; légal dans l'API, muet chez le client",
        "agent_mcplist":
            "VOTRE CLIENT MCP A-T-IL VU TOUTES LES PAGES ? Le listing collé, jugé contre la spec lue verbatim : nextCursor présent — vide aussi — ne dit PAS fini (« an empty string is a valid cursor and thus MUST NOT be treated as the end of results », 2026-07-28, clause absente de 2025-06-18) ; page vide avec cursor = piège nommé ; cursor répété = boucle refusée ; le reste devient un NOMBRE, avec les NOMS si déclarés (jamais fetchés). sept clients, même bug publié 2026 — Codex : « the other 2,642 are uncallable » ; reprise = curseur exact ou refus nommé — la fratrie dit COMBIEN, CHANGÉ, COLLIDÉ, REJETÉ ; aucune ne COMPTAIT LES PAGES",
        "invoice_payment_due":
            "LA VRAIE ÉCHÉANCE + LES QUATRE LECTURES d'un « Net 30 » : calendaire ou ouvrés × émission ou réception, ÉCART chiffré, jamais de moyenne ; report NOMMÉ par juridiction — § 193 BGB reporte le SAMEDI par la loi, BFDA 1971 reporte les bank holidays (tables gov.uk 2026-2028 proclamées, jamais prédites), facture FR : AUCUN texte de report lu — le vide est un VERDICT ; L. 511-79 reporte au prochain OUVRABLE, samedi compris (L. 3133-1) ; TARGET2 : le rail ferme, la dette court (dir. 2011/7) ; plafond L. 441-10 signalé ; 45 j fin de mois = DEUX méthodes DGCCRF — 15 j d'écart officiel",
        "shop_gift_voucher":
            "carte cadeau « périmée » REMPLACÉE d'office : cinq ans depuis l'achat — le légal couvre le papier (Irlande 2019) ; solde ≥ 1 € = dû, frontière 1 € en conflit NOMMÉ ; France : AUCUNE durée légale, mythe « 30 ans » = immobilier",
        "shop_soldes_window":
            "sept dérogations verbatim (hiver 2021 six semaines, Moselle seule 26 juin 2021), annexe versionnée, « ouvré » nommé ; hors France refusé par nom",
        "shop_soldes_be":
            "dates légales belges (VI.25 CDE) : clause dimanche datée (2027 : samedi 2 janv.), attente NOMMÉE (2 déc. → 1ᵉʳ janv.), reports corona verbatim, clause écartée visible ; France/Luxembourg refusés par nom",
        "shop_soldes_lu":
            "dates PAR ACTE (loi 2016 : CHAQUE ANNÉE par règlement, zéro formule) ; dix actes 2018-2027 ; deux rectificatifs nommés (2023 : le Mémorial imprimait un dimanche, la presse disait juste) ; chaîne 2021 : trois actes, un mort ; PAS d'attente (divergence BE) ; ≤2017, ≥2028 refusés par nom",
        "agent_retrybudget":
            "re-tenter cet échec est-il rationnel ? taxonomie fermée, plafond de hachage, budget de session, backoff déterministe",
        "money_keep_records_uk":
            "destruction légale UK au plus tôt, depuis l'ancre officielle ; TVA trois ancres, s388 par forme, extensions BLOCKED jamais devinées",
        "agent_propose":
            "proposition de contrat jugée contre le catalogue vivant — DUPLICATE-OF, SUSPECT avec preuve, ELIGIBLE avec blob",
        "shop_legal_guarantee":
            "horloges légales FR/UK depuis un jour de livraison : 24 m/12 m, vices 2+20 ans, UK 30 j/6 mois/6-5 ans — conflits nommés",
        "shop_pricedrop_refund":
            "baisse de prix après achat : qui doit la différence, jusqu'à quand, dans quelle monnaie — table Black Friday 2026 fermée",
        "shop_discount_audit":
            "règle Omnibus des trente jours : le prix barré est-il légal ? référence, vrai pourcentage, verdict nommé",
        "chart_from_data":
            "records/CSV → spécification Vega-Lite + PNG",
        "reshape_json":
            "remodelage JSON sous contrôle de schéma",
        "validate_json":
            "JSON contre schéma, pointeurs d'erreur",
        "json_repair":
            "JSON cassé → valide",
        "json_diff":
            "diff structurel, pointeurs JSON",
        "json_patch":
            "applique les opérations JSON Patch",
        "json_canonical":
            "forme canonique + clé stable",
        "csv_fix":
            "CSV sale → propre, refus nommés",
        "csv_types":
            "infère les types de colonnes, règles fermées",
        "csv_join":
            "deux tables jointes, clés vérifiées",
        "table_pivot":
            "pivote et agrège les tables",
        "list_dedupe":
            "déduplication exacte, ordre préservé",
        "format_convert":
            "allers-retours json/csv/yaml",
        "text_patch":
            "rechercher/remplacer sur du texte",
        "text_diff":
            "diff unifié entre textes",
        "text_apply_diff":
            "applique le diff unifié exactement",
        "path_normalize":
            "chemins de fichiers canoniques, tout OS",
        "glob_match":
            "ce chemin correspond-il à ce glob",
        "env_interpolate":
            "expansion de ${VAR}, valeurs par défaut, refus",
        "date_parse":
            "toute chaîne de date plausible → ISO",
        "date_tz":
            "conversion de fuseau, exacte en heure d'été",
        "date_calc":
            "jours ouvrés, additions/soustractions, deltas",
        "cron_next":
            "les N prochaines exécutions cron, fuseau épinglé",
        "cron_humanize":
            "expression cron → mots simples",
        "ics_generate":
            "événements → calendrier ICS valide",
        "ics_parse":
            "ICS → événements structurés",
        "num_format":
            "formatage de nombres exact selon la locale",
        "num_parse":
            "chaînes ambiguës → décimal exact",
        "num_round":
            "arrondi banquier ou explicite, au-delà du float",
        "units_convert":
            "familles fermées, facteurs exacts",
        "money_prorate":
            "prorata: base 30/365, ordre, écart — tout nommé",
        "money_aging":
            "ancienneté des créances par date d'échéance, en tranches",
        "money_unitprice":
            "prix unitaire + shrinkflation, dénominateur NOMMÉ (−12.5 % du pack ≠ +12.5 % par unité)",
        "eval_compare":
            "juge deux artefacts JSON : OK/WRONG, divergences nommées",
        "check_allowlist":
            "verdicts de politique par grammaire fermée, le plus spécifique gagne",
        "loop_doom_check":
            "verdicts doom/cyclic/storm sur une trace d'appels d'outils",
        "ledger_apply_payments":
            "rapprochement FIFO des paiements sur les factures",
        "ledger_summary":
            "résumé mensuel du grand livre, chaîne de soldes courants",
        "shop_shipping_deadline":
            "dernier jour d'expédition pour Noël, par transporteur et service",
        "shop_return_deadline":
            "date limite de retour des fêtes publiée pour une date d'achat, provenance et conflits nommés",
        "invoice_validate_totals":
            "totaux déclarés de facture vs arithmétique exacte, deltas signés",
        "money_split":
            "répartition exacte au centime, règle de reste fermée",
        "number_spell":
            "montant → en lettres FR/EN/PT",
        "net_ip":
            "cette IP est-elle private, loopback, link-local, multicast, reserved : anatomie",
        "net_cidr":
            "plage cidr : réseau, broadcast, hôtes, contains, découpe de sous-réseau",
        "file_encoding":
            "forensique de charset : bom, table, utf-8 strict ou indéterminé, avec preuve",
        "integrity_verify":
            "auditeur : rejoue N fois les pins publiées de TOUTE api, verdict de déterminisme par pin, egress contrôlé",
        "math_calc":
            "calculatrice Decimal exacte, fermée — le modèle écrit l'expression, la machine calcule ; 0.1+0.2 fait 0.3",
        "money_discount":
            "remises chaînées en facteurs exacts — 30%+20% font 44% pas 50%, ordre des étapes comparé, formule renvoyée",
        "table_sql_dump":
            "csv vers sql : CREATE TABLE + INSERT depuis les lignes, types DÉDUITS mais DITS, quoting exact selon le dialecte",
        "table_scale":
            "mise à l'échelle de recette, arrondi DÉCLARÉ : fraction exacte + pas mesurable par classe d'ingrédient + delta, multiplicateur dit une fois",
        "check_format":
            "les formats que JSON Schema ne peut pas exprimer (dates, semver, uuid, decimal-string…) — ensemble fermé, violations avec pourquoi + attendu",
        "csv_money_columns":
            "colonnes CSV financières lues par convention PROUVÉE — les valeurs non ambiguës de la colonne décident, contradictions refusées, pas devinées",
        "date_relative":
            "expressions de date relative (EN/FR/PT) vers ISO exact — grammaire fermée, « now » en argument, ambiguïtés signalées jamais tranchées",
        "date_recurrence":
            "RRULE déroulé en dates — sous-ensemble RFC 5545 fermé, mois invalides sautés LISTÉS, ancrage DTSTART déclaré, COUNT ou UNTIL jamais les deux, refus nommés, cap 500",
        "date_tz_ambiguity":
            "Heure murale + zone → single | fold | gap : heures inexistantes (spring forward) ou DOUBLES (fall back), chaque instant UTC nommé, offset + abréviation, règle PEP 495 dite — le verdict que date/tz applique en silence, que cron/next ne signale pas",
        "date_tz_anchor":
            "Heure murale ÉCRITE dans la zone du job, ANCRÉE dedans : chaque instant UTC candidat, dérive SIGNÉE en minutes (+ = en retard) ; l'offset gagne (Composio #4148) ; single/fold/gap rendus par date/tz_ambiguity APPELÉ",
        "money_flight_comp":
            "Date de vol = TABLE : 261/2004 + Sturgeon/Nelson avant 2027-10-23, (UE) 2026/2202 APRÈS (« EXCEEDING 3 h » STRICT, 180 pile ne paye pas), UK261 £220/350/520 + ligne £260 sous 4 h, plafond intra-UE €400, forclusion 9 mois",
        "date_week":
            "Semaine ISO aller-retour ; année ISO SÉPARÉE du %Y ; W53 par THÉORÈME (53 jeudis ⟺ 1er janv. jeudi, ou mercredi + bissextile ; zéro table) ; artefact %Y-W%V nommé ; Excel/US côte à côte",
        "units_shoe_size":
            "Pointures en millimètres exacts — jamais publiés en fractions (barleycorn 127/15, Paris point 20/3) ; demi ET tiers candidats ; dérive entre systèmes DITE ; charts marques hors contrat",
        "net_sri":
            "Subresource Integrity depuis OCTETS LOCAUX — zéro fetch : integrity prêt à coller, crossorigin, audit du style d'attribut (classe CVE-2026-120423 TAB), @latest signalé panne programmée",
        "text_url_canonical":
            "RFC 3986 §6.2.2 canonicalisation d'URL — toute transformation listée, paramètres de tracking retirés par opt-in nommé, IDN en punycode",
        "xml_to_json":
            "XML vers JSON avec les règles de conversion imprimées dans la réponse ; force_array fige la cardinalité, DTD refusé par son nom",
        "web_cert":
            "Lint de certificat X.509 depuis PEM : SANs, validité, flags de dépréciation, forme de la chaîne ; as_of rend le verdict rejouable",
        "id_checkdigit":
            "clés de contrôle : ISBN/EAN/GTIN/ISIN/LEI/boleto… vérifier, réparer, scanner",
        "image_rightsize":
            "redimensionnement PNG déterministe : boîte exacte / bilinéaire / nearest, rééchantillonnage entier, mêmes bytes pour toujours",
        "money_rates":
            "taux de référence officiels de la BCE : dernier jour ou archive 90 jours, croix en Decimal, jamais un taux inventé",
        "doc_text":
            "PDF en texte page par page : CMaps, Flate, verdicts honnêtes sur l'absence de couche texte",
        "money_amortize":
            "tableau d'amortissement d'emprunt : versements en annuité, intérêts par mois, solde à 0.00",
        "money_interest":
            "intérêts composés + taux annuel effectif, formule incluse",
        "ics_validate":
            "lint VCALENDAR : les MUST de RFC 5545 en erreurs, les SHOULD en avertissements",
        "schedule_holidays":
            "jours fériés légaux FR BE LU BR PT DE US avec la loi citée sur chaque ligne",
        "shop_withdrawal":
            "rétractation FR BE LU : un colis, trois grammaires — samedi avancé FR/BE, SURVIVANT au LU ; douze mois si info absente ; exceptions nommées",
        "web_cache":
            "texte Cache-Control → action RFC 9111, fraîcheur, directives inertes",
        "gzip_roundtrip":
            "compression/décompression gzip déterministe, mtime à zéro, base64",
        "qr_generate":
            "texte → QR code : SVG déterministe ou matrice de modules, ISO 18004",
        "table_peek":
            "profil de table : types de colonnes, nulls, uniques, min-max — règles fermées",
        "csv_diff":
            "diff de lignes par clé : ajoutées, retirées, champs changés, même compte",
        "ssh_fingerprint":
            "ligne de clé ssh → empreintes SHA256/MD5 exactement comme ssh-keygen les imprime",
        "zip_verify":
            "archive zip listée et vérifiée par CRC en mémoire, jamais extraite",
        "schedule_overlap":
            "agenda : blocs occupés fusionnés, paires qui se chevauchent, trous libres, verdict à un instant",
        "cron_validate":
            "cron : parse, verdict date impossible, prochaines exécutions depuis une heure donnée",
        "crypto_address":
            "adresse crypto : base58check, bech32 segwit, EIP-55 — verdict de checksum",
        "validate_taxid":
            "identifiant fiscal : verdict de clé de contrôle pour CNPJ, CPF, SIREN, SIRET, NIF, TVA EU",
        "caip":
            "identifiant de chaîne caip-2 caip-10 : namespace, nom de chaîne, adresse checksumée",
        "secret_scan":
            "est-ce que ce texte laisse fuiter clés api, tokens, cartes, seeds : positions, pas d'écho",
        "text_redact":
            "masque les secrets avec des tags numérotés stables avant tout partage",
        "validate_country":
            "code pays iso : alpha3, numeric, devise, décimales, indicatif téléphonique",
        "validate_postal":
            "grammaire de code postal par pays avec espacement canonique",
        "geo_distance":
            "distance orthodromique entre points ou le long d'un itinéraire ordonné",
        "geo_geohash":
            "encodage/décodage geohash avec bounding box, alphabet publié",
        "file_identify":
            "ce qu'est vraiment ce blob : magic bytes, pas l'extension de fichier",
        "text_punycode":
            "aller-retour domaine unicode ↔ idn xn-- et contrôle d'homoglyphes",
        "semver_parse":
            "grammaire semver officielle : parties, prerelease, build, stabilité",
        "semver_sort":
            "tri des versions par précédence, pas alphabétique : 10 > 2, pre < release",
        "text_sanitize":
            "nom de fichier sûr multi-OS : noms réservés, charset, budget de bytes, pourquoi",
        "json_map":
            "applique des ops fermées de casse et de nombre à chaque élément d'un tableau",
        "num_fx":
            "conversion de devise avec VOTRE taux explicite : Decimal exact, unités mineures ISO",
        "id_ulid":
            "création/parse/tri ULID déterministe : même seed, même id — retry-safe",
        "pkg_name":
            "nom de paquet npm, PyPI ou Docker valide ? version normalisée et exactement pourquoi pas",
        "hash_hmac":
            "signer et vérifier un payload avec une clé partagée : comparaison en temps constant",
        "hash_digest":
            "md5/sha/blake2b, hex + base64",
        "enc_base64":
            "base64/hex encodage/décodage, urlsafe",
        "jwt_decode":
            "segments JWT, jamais vérifiés pour de faux",
        "id_uuid":
            "v5/v7/seeded-v4, déterministe",
        "id_slug":
            "texte → slug URL propre",
        "fingerprint":
            "hash canonique de JSON/CSV",
        "validate_iban":
            "61 pays, BBAN + mod-97",
        "validate_phone":
            "E.164 + règles par pays",
        "validate_email":
            "syntaxe email + politique de domaine",
        "validate_url":
            "structure URL + règles de scheme",
        "color_check":
            "hex/rgb/hsl + contraste WCAG",
        "text_count":
            "mots/phrases/lignes/bytes exacts",
        "sort_natural":
            "file2 se trie avant file10",
        "text_case":
            "camel/snake/kebab/pascal exacts",
        "text_truncate":
            "troncature à frontière exacte",
        "regex_test":
            "match/spans/groups/replace, sandboxé",
        "text_chunk":
            "chunks RAG au budget de tokens exact",
        "md_render":
            "markdown → HTML fermé et sûr",
        "html_text":
            "HTML → texte lisible canonique",
        "recipe_shop_reste":
            "la chaîne « du RESTE » en un appel : total, vendus du matin, % de l'après-midi → trace des trois pas, reste exact ; 0/28 nu sur cette forme (bench v15) — la décomposition EST le travail",
        "recipe_partage_reste":
            "part de la PART : total, première part, seconde « du reste » → la seconde part + le reliquat, fractions exactes tracées",
        "recipe_soldes2":
            "deux remises, un prix final exact + le mensonge de la somme chiffré ; les chaînes à N paliers restent chez money/discount",
        "recipe_clean_table":
            "un appel : CSV sale → lignes typées uniques",
        "recipe_clean_json":
            "un appel : JSON cassé → texte canonique réparé",
        "recipe_data_trio":
            "un appel : csv sale + json cassé + liste d'urls → YAML final {rows, totals, urls}",
        "color_palette":
            "harmonies fermées + rampes de luminosité",
        "check_constraints":
            "brouillon + contraintes fermées → pass/fail par règle",
        "check_refs":
            "urls citées, nombres, hex, uuid vs sources fournies",
        "extract_facts":
            "money, date, number, url, email, uuid, iban — tout extrait, rien perdu",
        "text_select":
            "top-k chunks selon des règles de couverture fermées",
        "logic_rules":
            "faits + règles fermées → trace par règle",
        "sort_multi":
            "tri stable multi-clés avec ordre des égalités explicite",
        "json_query":
            "accès imbriqué par $-path, jokers [*], chemins canoniques",
        "check_redlines":
            "mots interdits/regex/formes de PII/budget dans ton brouillon : clean ou première violation",
        "check_target":
            "la réponse porte sur la BONNE quantité ? target lock : cible nommée, refus nommé, grammaire de synonymes fermée",
        "check_agreement":
            "ces payloads décrivent la même opération ? chaque divergence par pointeur",
        "intent_check":
            "le formulaire rempli vérifié avant de payer : ok, ou exactement quoi demander",
        "formula_catalog":
            "règle de trois, dilution C1V1, dosage mg/kg, EDD Naegele, hydratation boulanger, part en % — formule publiée, vos nombres substitués, calcul exact",
        "intent_reflect":
            "le miroir de compréhension : tu déclares ta lecture (formule + args), la machine te la rend écrite et exacte avant que tu la prennes pour la vérité",
        "intent_card":
            "phrase simple → le bon outil + un formulaire pré-rempli, ou la question exacte à poser",
        "batch":
            "un outil sur N payloads en un seul appel",
        "recipe_invoice":
            "un appel : lignes + TVA → facture exacte + montant en lettres + échéance",
        "recipe_facts":
            "un appel : texte en désordre → inventaire trié money/percent/date/url + total",
        "recipe_schedule":
            "un appel : cron + départ → occurrences + ICS prêt",
        "text_decode":
            "mojibake → utf-8, seules les corrections prouvables",
        "num_human":
            "durées, octets, nombres romains, ordinaux, mis en forme pour humains",
        "text_escape":
            "une valeur échappée pour html sql shell csv json url",
        "text_normalize":
            "formes unicode, accents, pleine chasse, règles d'espaces",
        "eth_address":
            "checksum EIP-55 + verdicts de liste autorisée",
        "eth_selector":
            "signature → sélecteur calldata 4 octets",
        "eth_units":
            "conversions exactes wei gwei ether",
        "eth_abi_encode":
            "types+valeurs → calldata exact",
        "eth_abi_decode":
            "calldata → valeurs lisibles",
        "eth_eip712":
            "données typées → digest EIP-712 0x1901",
        "eth_receipt":
            "logs + effets attendus → verdict de correspondance",
        "money_baggage":
            "Bagage : la DATE DU VOL choisit la règle (2027 plafonne le sous-siège 40×30×15, avant rien n'est fixé), faces triées = rotation, gabarit vs loi — trois verdicts séparés",
        "csv_excel_damage":
            "règles = trois interrupteurs Microsoft nommés ; import colonne-Texte PRESCRIT ; csv/fix répare, ici on PRÉDIT",
        "money_crossover":
            "sept calculateurs publiés arrondissent Δ fixe avant diviser ; jours NOMMÉS (mensuel ×12 jamais 30 ; journalier ×365/×366 bissextile ; « semaine » refusée) ; DOMINATION « never » ; km si conso FOURNIE ; one-off en mois de payback",
        "money_points":
            "Combien vaut un POINT : cpp = (cash − reste − rewards forgoes) / points × 100 en FRACTION EXACTE (1081/725) ; voies triées, égalités nommées, verdict contre FLOOR fourni ; jamais de table",
        "csv_excel_display":
            "Ce qu'Excel AFFICHE d'une valeur STOCKÉE (numFmt) : virgule trailing SCALE par mille (« $#,##0, » + 1 000 000 → $1,000 — arXiv 2611.05806, 6 extracteurs aveugles) ; table Microsoft rejouée ; demi-vers-le-large dit ; locale en ARGUMENT ; General/dates/couleurs refusés PAR NOM ; rendu ≠ import",
        "ship_dimweight":
            "poids volumétrique : diviseur en ARGUMENT (5 000 vs 6 000 = deux factures), faces triées, plafond porteur refusé par nom si hors table",
        "json_coerce":
            "; exposants/fractions TELS QUELS ; 'false' refusé PAR LE NOM (truthy) ; string→number si cast_strings=on ; '007' JAMAIS (zéros de tête = payload) ; clés dupliquées refusées ; notation CONSERVÉE",
        "money_bogo":
            ": remise sur le MOINS CHER (60+40 rend 20 % sur 100, ni 25 ni 50) ; prix égaux = 25 % JAMAIS 50 ; l'impair se paie PLEIN ; coupon EMPILE (25 puis 30 = 47,5) ; trace/paire, fraction exacte",
        "agent_modelid":
            "audit des ids de modèle contre un catalogue collé — verdicts nommés, did-you-mean à distance nommée, ne jure jamais avoir fait le GET (V23)",
        "agent_resultcliff":
            "mon résultat survit-il EN LIGNE chez CE harnais — la traversée calculée dans SON unité (claude code compte des CARACTÈRES en parlant de tokens), verdict, marqueur et clause de réparation cités, chaque ligne datée et sourcée ; collé en JSON, le survivant est jugé INTACT, CASSE avec le nœud coupable, ou PARSANT-MAIS-MENTI",
        "food_poultry":
            "fenêtre décongélation et cuisson de la dinde, tables USDA FSIS, horloge ISO en argument — jamais l'horloge murale, jamais de nombres inventés",
        "food_leftovers":
            "fenêtre des restes, USDA FSIS : seuil 2h, 3-4 jours frigo, 2-6 mois congélateur (UNION des deux pages FSIS) — temps en ARGUMENTS, jamais l'horloge, jamais de tables inventées",
        "food_ovenschedule":
            "un four, des plats, une heure de service : compte à rebours à l'envers, conflits de température nommés, jamais d'horloge murale",
        "json_bigint":
            "quels ENTIERS JSON mentent au-delà de 2^53 : la valeur binary64 EXACTE ET la chaîne que JS réémet, par lecteur (JS/Go/Python/nlohmann), COLLISIONS nommées — le symptôme du mauvais enregistrement ; mode=quote ne cite que les littéraux marqués, le reste octet à octet ; RFC 8259 §6 cité verbatim",
        "money_settle":
            "qui paye qui après les avances : solde NET (remise plafonnée à la propre créance, NOMMÉE) ou graphe PAR REÇUS — compare rend les DEUX réponses du fil, écart chiffré ; avance en NATURE (points, carte cadeaux) comptée à TA lecture, face|cash|none, jamais devinée ; virements minimaux PROUVÉS (DP ≤9) ; taux en ARGUMENTS, jamais fetchés",
    },    "pt": {
        "stats_rate_ci":
            "k de n → taxa OBSERVADA e centro WILSON separados e nomeados, intervalo 95 % — 65,2% sozinho é mentira de precisão",
        "pdf_provenance":
            "o que os bytes do PDF confessam: qual ferramenta o escreveu, que datas alega, se a ordem ao menos faz sentido — null nomeado, nunca inventado",
        "text_mojibake":
            "varredura em duas camadas SEM consertar: famílias de codificação contadas, agulhas de contexto nomeadas — serão nunca conta como serã",
        "address_parse":
            "endereço postal → país, CEP validado contra 50 gramáticas, linhas restantes; ambiguidade NOMEADA, nunca adivinhada",
        "date_civil":
            "instante + fuso IANA → a data civil do fuso; mudança de exercício sinalizada, fuso do servidor nunca lido",
        "text_fold_report":
            "quais reduções de acentos ou caixa APAGAM identidade — relatado, nomeado; o dobramento fica com o chamador",
        "text_novel_words":
            "descricao contra titulo: palavras novas contadas por item, feeds eco nomeados, limite dito (padrao 3)",
        "date_window":
            "limites de cláusula (min..max dias antes/depois de um evento) → janela INCLUSIVE, span e sentido ditos; invertidas recusadas por nome (não se reordena um contrato)",
        "date_deemed":
            "data de envio + modo → recebimento reputado; sem modo, sem data (tabela fechada nomeada, override por argumento)",
        "net_ratelimit":
            "cabeçalhos Retry-After e X-RateLimit-* lidos (delta-seconds ou IMF-fixdate estrito); em contradição, ambas as esperas são NOMEADAS, nunca escolhidas; now é argumento, nunca relógio de parede",
        "number_words_pair":
            "forma por extenso e forma numérica conferidas uma contra a outra — trinta (40) recusa: AGREE/MISMATCH/NO_PAIR, os dois valores guardados",
        "agent_mcpaudit":
            "a lista de ferramentas MCP colada, julgada "
            "contra regras de rejeição nomeadas, antes de um "
            "cliente descartá-la em silêncio",
        "agent_mcpsurface":
            "impressão SHA-256 da superfície de ferramentas MCP "
            "colada e deriva NOMEADA contra uma leitura anterior — "
            "anotações canonizadas com os padrões publicados da "
            "spec, o ponto cego do AI SDK fechado; a ordem entra no "
            "contrato",
        "agent_contexttax":
            "quanto custa A SUA lista MCP colada, em bytes e tokens (estimador publicado chars÷4): por ferramenta e total, o que some com nomes-only, o que a drop de DESCRIPTIONS devolve — medida, não palpite",
        "agent_costdiff":
            "quanto MUDA uma lista de ferramentas entre duas versões: por ferramenta, added/changed/removed + tokens do delta com o MESMO estimador publicado do context-tax; o preço da atualização, não a lista inteira",
        "agent_tooltrim":
            "O QUE DESCONECTAR para caber no orçamento: gotas IDLE-primeiro em frações exatas, recontagem no canon da irmã — mesmo número em context-tax; FITS/STILL_OVER com o RESTE cifrado; context-tax diz QUANTO, cost-diff A DIFERENÇA — aqui O QUE TIRAR",
        "agent_tooloverlap":
            "QUAIS DUAS FERRAMENTAS VIRAM UMA SÓ, em QUAL CLIENTE: corte 64 chars do VS Code com ABORT alfabético (repro: 5, listadas 2), dobra cabeça30+cauda30 do gemini-cli com OVERWRITE, corte de gateway sem checagem; correção em NÚMERO — a menor chave que desencalha, senão NO_PREFIX_FIX; legal na API, mudo no cliente",
        "agent_mcplist":
            "VIU TODAS AS PÁGINAS do tools/list? Cursor presente — até vazio — NÃO encerra (MUST 2026-07-28); página vazia com cursor = armadilha; repetido = laço; o que falta vira NÚMERO e NOMES se declarados; sete clientes, mesmo bug 2026 — Codex: «as outras 2.642 são incallables»; retomada = cursor exato ou recusa — nenhuma irmã contou PÁGINAS",
        "invoice_payment_due":
            "vencimento REAL + as QUATRO leituras do Net 30: calendarial ou útil × emissão ou recebimento, gap CIFRADO, nunca média; § 193 BGB adia o SÁBADO por lei, BFDA 1971 adia bank holidays (gov.uk 2026-2028, nunca previstas); fatura FR: vazio é VEREDITO; letra: L. 511-79 → dia ÚTIL, sábado conta (L. 3133-1); TARGET2: trilho fecha, dívida corre (2011/7); teto L. 441-10; 45 dias fim de mês = DOIS métodos DGCCRF — gap 15",
        "shop_gift_voucher":
            "vale « vencido » de um ano é SUBSTITUÍDO por cinco desde a compra — a data legal COBRE o papel (Lei irlandesa 2019, forma JD Sports); saldo ≥ €1 devido, fronteira €1 com conflito NOMEADO; França NEGATIVA: nenhuma duração legal, « 30 anos » é imobiliário",
        "shop_soldes_window":
            "janelas de soldas FR pela regra do arrêté (2ª quarta hiver, avanço se após o 12; última quarta verão; 4 semanas) — derrogações NOMADAS com o texto, ano em ARGUMENTO, nunca profecia",
        "shop_soldes_be":
            "datas belgas (art. VI.25 CDE): cláusula do domingo datada (2027: sáb 2 jan), espera de um mês NOMEADA (2 dez–1 jan), adiamentos corona verbatim, cláusula afastada visível; França/Luxemburgo recusados pelo nome",
        "agent_retrybudget":
            "repetir esta falha é racional? taxonomia fechada, teto "
            "de hash, orçamento de sessão, backoff determinístico",
        "shop_discount_audit":
            "regra Omnibus de trinta dias: o preço riscado é legal? "
            "referência, porcentagem real, veredito nomeado",
        "chart_from_data":
            "registros/CSV → especificação Vega-Lite + PNG",
        "reshape_json":
            "remodelagem de JSON validada por schema",
        "validate_json":
            "JSON contra schema, ponteiros de erro",
        "json_repair":
            "JSON quebrado → válido",
        "json_diff":
            "diff estrutural, ponteiros JSON",
        "json_patch":
            "aplica operações JSON Patch",
        "json_canonical":
            "forma canônica + chave estável",
        "csv_fix":
            "CSV sujo → limpo, recusas nomeadas",
        "csv_types":
            "infer tipos de coluna, regras fechadas",
        "csv_join":
            "duas tabelas unidas, chaves verificadas",
        "table_pivot":
            "pivotear e agregar tabelas",
        "list_dedupe":
            "deduplicação exata, ordem preservada",
        "format_convert":
            "ida e volta json/csv/yaml",
        "text_patch":
            "localizar/substituir em texto",
        "text_diff":
            "diff unificado entre textos",
        "text_apply_diff":
            "aplica diff unificado exatamente",
        "path_normalize":
            "caminhos de arquivo canônicos, qualquer SO",
        "glob_match":
            "este caminho corresponde a este glob",
        "env_interpolate":
            "expansão de ${VAR}, padrões, recusas",
        "date_parse":
            "qualquer string de data plausível → ISO",
        "date_tz":
            "conversão de fuso, exata com horário de verão",
        "date_calc":
            "dias úteis, soma/subtração, deltas",
        "cron_next":
            "próximas N execuções cron, fuso fixado",
        "cron_humanize":
            "expressão cron → palavras simples",
        "ics_generate":
            "eventos → calendário ICS válido",
        "ics_parse":
            "ICS → eventos estruturados",
        "num_format":
            "formatação numérica exata por locale",
        "num_parse":
            "strings ambíguas → decimal exato",
        "num_round":
            "arredondamento banker's ou explícito, além do float",
        "units_convert":
            "famílias fechadas, fatores exatos",
        "money_prorate":
            "rateio: base 30/365, ordem, diferença — tudo nomeado",
        "money_aging":
            "aging de contas a receber por vencimento, em faixas",
        "money_unitprice":
            "preço por unidade + shrinkflation, denominador NOMEADO (−12.5 % do pacote ≠ +12.5 % por unidade)",
        "eval_compare":
            "julga dois artefatos JSON: OK/WRONG, divergências nomeadas",
        "check_allowlist":
            "vereditos de política por gramática fechada, o mais específico vence",
        "loop_doom_check":
            "vereditos doom/cyclic/storm sobre o trace de chamadas de ferramenta",
        "ledger_apply_payments":
            "conciliação FIFO de pagamentos sobre faturas",
        "ledger_summary":
            "resumo mensal do livro-razão com cadeia de saldo corrente",
        "shop_shipping_deadline":
            "último dia de envio para o Natal, por transportadora e serviço",
        "shop_return_deadline":
            "prazo de devolução de fim de ano publicado para uma data de compra, procedência e conflitos nomeados",
        "invoice_validate_totals":
            "totais declarados da fatura vs aritmética exata, deltas com sinal",
        "money_split":
            "divisão exata em centavos, regra de resto fechada",
        "number_spell":
            "valor → por extenso FR/EN/PT",
        "net_ip":
            "este IP é private, loopback, link-local, multicast, reserved: anatomia",
        "net_cidr":
            "faixa cidr: rede, broadcast, hosts, contains, divisão de sub-rede",
        "file_encoding":
            "forense de charset: bom, tabela, utf-8 estrito ou indeterminado, com prova",
        "integrity_verify":
            "auditor: reproduz as pins publicadas de QUALQUER api N vezes, veredito de determinismo por pin, egresso protegido",
        "math_calc":
            "calculadora Decimal exata, fechada — o modelo escreve a expressão, a máquina calcula; 0.1+0.2 é 0.3",
        "money_discount":
            "descontos encadeados como fatores exatos — 30%+20% é 44% não 50%, ordem das etapas comparada, fórmula retornada",
        "table_sql_dump":
            "csv para sql: CREATE TABLE + INSERT a partir das linhas, tipos DEDUZIDOS mas DITOS, quoting exato por dialeto",
        "table_scale":
            "escalonamento de receita com o arredondamento DECLARADO: fração exata + passo mensurável por classe de ingrediente + delta, multiplicador dito uma vez",
        "check_format":
            "validação de formato em conjunto fechado para regras que JSON Schema não expressa (datas, semver, uuid, decimal-string…) — violações vêm com o porquê + esperado",
        "csv_money_columns":
            "colunas CSV financeiras lidas por convenção COMPROVADA — os valores inequívocos da própria coluna decidem, contradições são recusadas, não adivinhadas",
        "date_relative":
            "frases de data relativa (EN/FR/PT) para ISO exato — gramática fechada, agora como argumento, ambiguidades reportadas nunca decididas",
        "date_recurrence":
            "RRULE desdobrada em datas — subconjunto fechado da RFC 5545, meses inválidos pulados LISTADOS, ancoragem do DTSTART declarada, COUNT ou UNTIL nunca os dois, recusas nomeadas, teto de 500",
        "date_tz_ambiguity":
            "Relógio + fuso → single | fold | gap : horas que não existem (spring forward) ou existem DUAS VEZES (fall back), cada instante UTC com offset e abreviação, PEP 495 declarada, vizinhos do buraco exibidos — o veredicto que date/tz aplica em silêncio e cron_next não sinaliza",
        "date_tz_anchor":
            "instante + fuso IANA nomeado → a data civil que o fuso habita; mudança de exercício sinalizada; nunca «a» data UTC — a âncora é o fuso que a lei nomeia",
        "money_flight_comp":
            "a DATA DO VOO escolhe a tabela: EC261 + jurisprudência antes de 23/10/2027, a nova tabela «ACIMA DE três horas» depois; € e £, prazos de reclamar em datas nomeadas; ANAC/R$ recusado por outra lei",
        "date_week":
            "semana ISO 8601 com W53 nomeada; week-based-year ≠ ano civil; os números NUM, ISOWEEKNUM da imprensa são TESTADOS, não seguidos",
        "units_shoe_size":
            "Numeração de calçado em milímetros exatos — não publicada em frações (barleycorn 127/15, Paris point 20/3), meio E terço como candidatos de grade, desvio entre sistemas DITO, nunca um único número confiante, tabelas de marcas fora do contrato",
        "net_sri":
            "Atributo Subresource Integrity a partir de BYTES LOCAIS — nunca fetch: integrity pronto para colar, crossorigin, auditoria do estilo do atributo (classe CVE-2026-120423 TAB), URL @latest ou range sinalizadas como falha programada",
        "text_url_canonical":
            "RFC 3986 §6.2.2 canonicalização de URL — toda transformação listada, parâmetros de rastreamento removidos por opt-in nomeado, IDN para punycode",
        "xml_to_json":
            "XML para JSON com as regras de conversão impressas na resposta; force_array fixa a cardinalidade, DTD recusado pelo nome",
        "web_cert":
            "Lint de certificado X.509 a partir de PEM: SANs, validade, flags de depreciação, forma da cadeia; as_of torna o veredito reproduzível",
        "id_checkdigit":
            "dígitos verificadores: ISBN/EAN/GTIN/ISIN/LEI/boleto… verificar, reparar, escanear",
        "image_rightsize":
            "redimensionamento PNG determinístico: caixa exata / bilinear / nearest, reamostragem inteira, mesmos bytes para sempre",
        "money_rates":
            "taxas de referência oficiais do BCE: último dia ou arquivo de 90 dias, cruzamentos em Decimal, nunca uma taxa inventada",
        "doc_text":
            "PDF para texto página por página: CMaps, Flate, vereditos honestos sobre ausência de camada de texto",
        "money_amortize":
            "tabela de amortização de empréstimo: parcelas em anuidade, juros por mês, saldo até 0.00",
        "money_interest":
            "juros compostos + taxa anual efetiva, fórmula inclusa",
        "ics_validate":
            "lint de VCALENDAR: MUSTs da RFC 5545 como erros, SHOULDs como avisos",
        "schedule_holidays":
            "feriados legais FR BE LU BR PT DE US com a lei citada em cada linha",
        "shop_withdrawal":
            "retratação FR BE LU: um pacote, três gramáticas — sábado avança FR/BE, SOBREVIVE no LU; doze meses sem informação; exceções nomeadas",
        "web_cache":
            "texto Cache-Control → ação RFC 9111, frescor, diretivas inertes",
        "gzip_roundtrip":
            "compressão/descompressão gzip determinística, mtime zerado, base64",
        "qr_generate":
            "texto → QR code: SVG determinístico ou matriz de módulos, ISO 18004",
        "table_peek":
            "perfil da tabela: tipos de coluna, nulos, únicos, min-max — regras fechadas",
        "csv_diff":
            "diff de linhas por chave: adicionadas, removidas, campos alterados, mesma contagem",
        "ssh_fingerprint":
            "linha de chave ssh → digital SHA256/MD5 exatamente como o ssh-keygen imprime",
        "zip_verify":
            "arquivo zip listado e verificado por CRC em memória, nunca extraído",
        "schedule_overlap":
            "agenda: blocos ocupados mesclados, pares sobrepostos, intervalos livres, veredito em um ponto",
        "cron_validate":
            "cron: parse, veredito de data impossível, próximas execuções a partir de um horário dado",
        "crypto_address":
            "endereço cripto: base58check, bech32 segwit, EIP-55 — veredito de checksum",
        "validate_taxid":
            "ID fiscal: veredito de dígito verificador para CNPJ, CPF, SIREN, SIRET, NIF, IVA UE",
        "caip":
            "identificador de chain caip-2 caip-10: namespace, nome da chain, endereço com checksum",
        "secret_scan":
            "se este texto vaza chaves de api, tokens, cartões, seeds: posições, sem eco",
        "text_redact":
            "mascara segredos com tags numeradas estáveis antes de compartilhar qualquer coisa",
        "validate_country":
            "código de país iso: alpha3, numeric, moeda, decimais, código de discagem",
        "validate_postal":
            "gramática de CEP por país com espaçamento canônico",
        "geo_distance":
            "distância ortodrômica entre pontos ou ao longo de uma rota ordenada",
        "geo_geohash":
            "encode/decode de geohash com bounding box, alfabeto publicado",
        "file_identify":
            "o que esse blob realmente é: magic bytes, não a extensão do arquivo",
        "text_punycode":
            "ida e volta de domínio unicode ↔ idn xn-- e checagem de homoglifos",
        "semver_parse":
            "gramática oficial do semver: partes, prerelease, build, estabilidade",
        "semver_sort":
            "ordena versões por precedência, não por alfabeto: 10 > 2, pre < release",
        "text_sanitize":
            "nome de arquivo seguro entre sistemas: nomes reservados, charset, orçamento de bytes, por quê",
        "json_map":
            "aplica ops fechadas de caixa e número em cada item de um array",
        "num_fx":
            "converte moeda com a SUA taxa explícita: Decimal exato, unidades menores ISO",
        "id_ulid":
            "gerar/parse/ordenar ULID determinístico: mesma seed, mesmo id — seguro para retry",
        "pkg_name":
            "nome de pacote npm, PyPI ou Docker válido? forma normalizada e exatamente por que não",
        "hash_hmac":
            "assina e verifica um payload com chave compartilhada: comparação em tempo constante",
        "hash_digest":
            "md5/sha/blake2b, hex + base64",
        "enc_base64":
            "base64/hex encode/decode, urlsafe",
        "jwt_decode":
            "segmentos JWT, nunca verificados de mentira",
        "id_uuid":
            "v5/v7/seeded-v4, determinístico",
        "id_slug":
            "texto → slug de URL limpo",
        "fingerprint":
            "hash canônica de JSON/CSV",
        "validate_iban":
            "61 países, BBAN + mod-97",
        "validate_phone":
            "E.164 + regras por país",
        "validate_email":
            "sintaxe de e-mail + política de domínio",
        "validate_url":
            "estrutura de URL + regras de scheme",
        "color_check":
            "hex/rgb/hsl + contraste WCAG",
        "text_count":
            "palavras/frases/linhas/bytes exatos",
        "sort_natural":
            "file2 vem antes de file10 na ordenação",
        "text_case":
            "camel/snake/kebab/pascal exatos",
        "text_truncate":
            "truncamento com limite exato",
        "regex_test":
            "match/spans/groups/replace, em sandbox",
        "text_chunk":
            "chunks RAG com orçamento de tokens exato",
        "md_render":
            "markdown → HTML fechado e seguro",
        "html_text":
            "HTML → texto legível canônico",
        "recipe_shop_reste":
            "a cadeia «do RESTO» em uma chamada: total, vendas da manhã, % da tarde → o rastro dos três passos e o resto exato; 0/28 puro e retry nessa forma (bench v15) — a decomposição é o trabalho, ele já está feito aqui",
        "recipe_partage_reste":
            "a parte da PARTE: total, primeira parte, segunda «do resto» → a segunda parte + o remanescente, frações exatas com rastro",
        "recipe_soldes2":
            "dois descontos, um preço final exato + a mentira da soma em números; as cadeias de N níveis ficam em money/discount",
        "recipe_clean_table":
            "uma chamada: CSV sujo → linhas tipadas únicas",
        "recipe_clean_json":
            "uma chamada: JSON quebrado → texto canônico reparado",
        "recipe_data_trio":
            "uma chamada: csv sujo + json quebrado + lista de urls → YAML final {rows, totals, urls}",
        "color_palette":
            "harmonias fechadas + rampas de luminosidade",
        "check_constraints":
            "rascunho + restrições fechadas → pass/fail por regra",
        "check_refs":
            "urls citadas, números, hex, uuid vs fontes fornecidas",
        "extract_facts":
            "money, date, number, url, email, uuid, iban — tudo extraído, nada perdido",
        "text_select":
            "top-k chunks por regras fechadas de cobertura",
        "logic_rules":
            "fatos + regras fechadas → rastro por regra",
        "sort_multi":
            "ordenação estável por várias chaves com ordem de empate explícita",
        "json_query":
            "acesso aninhado por $-path, curingas [*], caminhos canônicos",
        "check_redlines":
            "palavras proibidas/regex/formatos de PII/orçamento no seu rascunho: clean ou primeira violação",
        "check_target":
            "a resposta é sobre a QUANTIDADE CERTA? target lock: alvo nomeado, recusa nomeada, gramática de sinônimos fechada",
        "check_agreement":
            "esses payloads descrevem o mesmo negócio? cada divergência por ponteiro",
        "intent_check":
            "o formulário preenchido conferido antes de você pagar: ok, ou exatamente o que perguntar",
        "formula_catalog":
            "regra de três, diluição C1V1, dosagem mg/kg, EDD Naegele, hidratação do padeiro, parte em porcentagem — a fórmula publicada, seus números substituídos, o cálculo exato",
        "intent_reflect":
            "o espelho de compreensão: você declara sua leitura (fórmula + args), a máquina a devolve escrita e exata antes que você a tome como verdade",
        "intent_card":
            "frase simples → a ferramenta certa + formulário pré-preenchido, ou a pergunta exata a fazer",
        "batch":
            "uma ferramenta sobre N payloads em uma única chamada",
        "recipe_invoice":
            "uma chamada: itens + IVA → fatura exata + valor por extenso + vencimento",
        "recipe_facts":
            "uma chamada: texto bagunçado → inventário ordenado de money/percent/date/url + total",
        "recipe_schedule":
            "uma chamada: cron + início → ocorrências + ICS pronto",
        "text_decode":
            "mojibake → utf-8, só correções comprováveis",
        "num_human":
            "duração, bytes, algarismos romanos, ordinal, formatados para humanos",
        "text_escape":
            "um valor escapado para html sql shell csv json url",
        "text_normalize":
            "formas unicode, acentos, largura total, regras de espaços",
        "eth_address":
            "checksum EIP-55 + vereditos da lista de permitidos",
        "eth_selector":
            "assinatura → seletor calldata de 4 bytes",
        "eth_units":
            "conversões exatas wei gwei ether",
        "eth_abi_encode":
            "tipos+valores → calldata exato",
        "eth_abi_decode":
            "calldata → valores legíveis",
        "eth_eip712":
            "dados tipados → digest EIP-712 0x1901",
        "eth_receipt":
            "logs + efeitos esperados → veredito de correspondência",
        "money_baggage":
            "Data do voo = faixa da LEI (40×30×15 sob o assento GRÁTIS desde 2027-10-23, NADA antes — cada companhia decide); gabaritos COMO ARGUMENTOS, nunca fetchados; ajuste POR DIMENSÃO com ROTAÇÃO; o «total 100 cm / 7 kg» da imprensa é TESTADO, nunca regra",
        "csv_excel_damage":
            "o que o Excel DESTRÓI no duplo clique, PREDITO: zeros à esquerda, muro de 15 dígitos, notação científica, datas forçadas (locale ARGUMENTO, ano por as_of), formas de fórmula; interruptores Microsoft nomeados; Texto para Colunas PRESCRITO; csv/fix conserta, aqui se PREDIT",
        "money_crossover":
            "Preço de custo de DUAS tarifas (unitário + fixo): virada em FRAÇÃO EXATA — as calculadoras públicas arredondam o Δ fixo antes de dividir e se contradizem; dias NOMEADOS (mensal ×12, «semana» recusada); DOMINAÇÃO «never»; km se consumo FORNECIDO",
        "money_points":
            "quanto vale um PONTO: cpp = (cash − resto − rewards forgoes) ÷ pontos × 100 em FRAÇÃO EXATA (1081/725 onde a imprensa diz 1.49); vias lado a lado, veredito contra FLOOR fornecido, retorno efetivo pts/$; nunca tabela de valoração embarcada",
        "csv_excel_display":
            "O que o Excel EXIBE de um valor ARMAZENADO sob numFmt: vírgula trailing ESCALA por mil (« $#,##0, » + 1 000 000 → $1,000 — arXiv 2611.05806, seis extratores cegos) ; tabela Microsoft rejouée ; meio-para-fora dito ; locale como ARGUMENTO ; General/datas/cores recusados PELO NOME",
        "ship_dimweight":
            "o peso REALMENTE cobrado: dimensões ARREDONDADAS PARA A POLEGADA SUPERIOR antes do volume, volume ÷ divisor (unidade DECLARADA), max(real, dimensional), ceil na faixa; fração exata tranche; tabelas da transportadora COMO ARGUMENTOS",
        "json_coerce":
            "conserta os ARGUMENTOS que um leitor RÍGIDO recusa: 8.0→8 (classe serde « invalid type: floating point »), exponentes e frações TAIS QUAIS, 'false' em string recusado PELO NOME, '007' NUNCA (zeros são payload), chaves duplicadas recusadas; notação CONSERVADA",
        "money_bogo":
            "a porcentagem que o CAIXA aplica sob « BUY ONE GET ONE 50 % »: desconto na MAIS BARATA (60+40 vira 80 em 100 = 20 %, nem 25 nem 50), iguais = 25 % do par NUNCA 50, ímpar se paga CHEIO (pares DADOS), cupom EMPILHA em produto de fatores (nunca 55)",
        "agent_modelid":
            "audita ids de modelo contra um catálogo colado — vereditos nomeados, did-you-mean a uma distância nomeada, nunca jura que fez o GET (V23)",
        "agent_resultcliff":
            "meu resultado sobrevive INLINE NESTE harness — a travessia na UNIDADE DELE (o claude code conta CARACTERES falando de tokens), veredito, marcador e reparo citados, linha por linha datada ; colado em JSON, o sobrevivente é julgado INTACTO, QUEBRADO com o nó culpado, ou PARSEIA-MENTE",
        "food_poultry":
            "janela de descongelar e assar o peru, tabelas USDA FSIS, relógio ISO como argumento — nunca relógio de parede, nunca números inventados",
        "food_leftovers":
            "janela das sobras, USDA FSIS: limite 2h, 3-4 dias geladeira, 2-6 meses congelador (UNIÃO das duas páginas FSIS que se contradizem) — tempos como ARGUMENTOS, nunca relógio de parede nem tabela inventada",
        "food_ovenschedule":
            "um forno, vários pratos, hora de servir: contagem de trás para frente, conflitos de temperatura nomeados, nunca relógio de parede",
        # b114 : le PT FRANCHIT le plafond (181 558 > 181 000) — élagage
        # à l'annonce, précédent b112/b113. 1) shop_soldes_lu tombait
        # sur le FALLBACK ANGLAIS (640 octets de prose EN sur une page
        # PT — faute de parité PÊCHÉE PAR le budget : c'est le plafond
        # qui l'a révélée, consigné) — traduite SERREE ; 2) les deux
        # plus longues .tp PT raccourcies à claims constants (les
        # détails voyagent dans /tools/<name>.json, la carte est une
        # vitrine) ; 3) json_bigint PT ajoutée (parité — la carte
        # neuve doit se lire en portugais chez elle).
        "shop_soldes_lu":
            "janelas do Luxemburgo datadas POR ACTO (lei 2016: A CADA ANO, zero fórmula); dez actos 2018-2027; duas retificações, tipos opostos (2018: dia; 2023: limite); cadeia 2021: três actos, um morto; SEM espera (divergência BE); fora da faixa: recusado por nome",
        "json_bigint":
            "quais inteiros JSON MENTEM além de 2^53 : valor binary64 EXATO E a string que o JS reimprime, por leitor; COLISÕES nomeadas — o registro errado; mode=quote cita só os marcados, o resto byte a byte; RFC 8259 §6 verbatim",
        "money_settle":
            "quem paga quem após os avanços: LÍQUIDOS (perdão só do que se TEM A RECEBER, nomeado) ou NOTA A NOTA; natureza (pontos, cartão-presente) pela SUA leitura: face|cash|none, nunca adivinhada; compare numera o vão; mínimos PROVADOS (DP ≤9); taxas EM ARGUMENTOS",
    },
}




CAT_ALL = {"en": "all", "fr": "tout", "pt": "tudo"}



# ── everyday cards: real answers, captured by asking the app itself ──
W = {
    "en": {"qr": "QR v%s \u00b7 %s\u00d7%s modules \u00b7 printable SVG, "
                 "deterministic",
           "word": "\u2192 \u201c%s\u201d",
           "iban": "\u2192 check digit valid \u00b7 %s",
           "page": "\u2192 standalone page (%s bytes) \u00b7 Ctrl-P = PDF",
           "days": "\u2192 %s days to go",
      "sale": "\u2192 $%s — really -%s %%, not -50%%",
      "scale": "\u2192 flour %s exact, weigh %s \u00b7 eggs stated, "
               "not guessed",
      "recur": "\u2192 %s then %s \u00b7 biweekly SKIPS weeks \u2014 "
               "named, not guessed",
      "shoe": "\u2192 %s mm exact \u00b7 EU position %s \u2014 half-grid "
              "%s, third-grid %s \u00b7 never one number",
      "comp": "\u2192 %s owed under the NEW table (\u22652027-10-23) \u00b7 "
              "carrier MAY pay %s \u00b7 claim by %s \u00b7 or \u00a3220/"
              "\u00a3350/\u00a3520 UK261 \u00b7 same flight, old rules: "
              "another answer",
      "bag": "\u2192 %s under the seat by the 2027 LAW \u00b7 carrier "
             "gauge 40\u00d730\u00d720: %s once faces are sorted \u00b7 "
             "overhead: the law sets NO size",
      "cross": "\u2192 tariffs flip at %s kWh/mo (%s/yr) "
               "\u00b7 exact \u2014 web calculators round the "
               "fixed part first",
      "points": "\u2192 %s \u00a2/point, exactly %s \u00b7 above your "
                "floor %s \u2192 redeem",
      "dim": "\u2192 billed %s kg vs %s kg \u2014 same box, divisors "
             "5 000 vs 6 000, each step named",
      "bogo": "\u2192 sign says 50%%, the pair pays %s — you pay %s of %s",
      "unitprice": "\u2192 500 g to 400 g, same sticker: \u2212%s%% of "
                   "product, +%s%% per unit \u2014 two denominators",
      "poultry": "\u2192 16-lb bird into the fridge by %s, not "
                 "before %s",
      "withdrawal": "\u2192 last day to change your mind: %s \u00b7 %s at as_of",
      "settle": "\u2192 net: ONE wire B\u2192A $%s, minimum PROUVED \u00b7 per "
                "receipt $%s \u00b7 C forgave $%s net vs $%s itemized",
      "prorate": "→ $1,000 x 18d: product %s vs landlord %s · "
                 "delta %s · named, never picked for you",
      "payscale": "→ 52,000 ÷2,087 = %s/h · rate-first ×80 = %s · "
                  "÷26 by %s · 2027: %s paydays",
      "leftovers": "\u2192 Thanksgiving 2026 replay: eat by %s \u00b7 "
                   "band %s",
      "ovenschedule": "\u2192 oven on %s, bird out %s \u00b7 temp "
                      "conflicts: %d \u2014 no timeline checks this",
      "deadline": "\u2192 last ship %s (%s) \u00b7 the dissenter "
                  "prints %s \u2014 named, never averaged",
      "returndead": "\u2192 return by %s (%s) \u00b7 Target's holiday "
                    "window closed %s \u2014 the 'Jan 31' headline "
                    "never says",
      "auditcut": "\u2192 %s \u00b7 legal reference %s \u00b7 real "
                  "cut %s%%, not the announced 30%%",
      "pricedrop": "\u2192 owed %s \u00b7 claim by %s (%s) \u00b7 the "
                   "window is a published date, the source class "
                   "travels in the row",
      "warr": "\u2192 statutory conformity until %s (%s) \u00b7 "
              "hidden-defect clock to %s from the DISCOVERY \u2014 "
              "the shop window died Jan 15, the law did not",
           "rec": "\u2192 keep until %s \u00b7 shred from %s \u00b7 official 2022-23 example, replayed",
           "vouch": "\u2192 law reads ALIVE to %s \u00b7 %s days left "
                    "\u00b7 the printed date had stolen %s \u2014 Act "
                    "2019 overrides the paper",
           "window": "\u2192 winter 2027 opens %s at 8 h \u00b7 the "
                     "second Wednesday (%s) fell after the 12th: "
                     "ADVANCED \u00b7 %s days to go",
           "be": "\u2192 winter 2027 opens %s \u00b7 standstill since %s \u00b7 %s days to go"},
    "fr": {"qr": "QR v%s \u00b7 %s\u00d7%s modules \u00b7 SVG imprimable, "
                 "d\u00e9terministe",
           "returndead": "\u2192 retour jusqu'au %s (%s) \u00b7 chez "
                         "Target la fen\u00eatre des f\u00eates fermait "
                         "le %s \u2014 le titre \u00ab jusqu'au 31 "
                         "janvier \u00bb ne le dit jamais",
           "auditcut": "\u2192 %s \u00b7 r\u00e9f\u00e9rence l\u00e9gale %s "
                       "\u00b7 vraie remise %s%%, pas les 30%% "
                       "annonc\u00e9s",
           "pricedrop": "\u2192 %s \u00e0 r\u00e9clamer avant le %s "
                        "(%s) \u00b7 la fen\u00eatre est une date "
                        "publi\u00e9e, la classe de source voyage",
           "warr": "\u2192 conformité légale jusqu'au %s (%s) \u00b7 "
                   "vices cachés jusqu'au %s depuis la DÉCOUVERTE "
                   "\u2014 la vitrine a fermé le 15 janvier, la loi "
                   "non",
           "rec": "\u2192 garder jusqu'au %s \u00b7 détruire dès le %s \u00b7 l'exemple officiel 2022-23, rejoué",
           "vouch": "\u2192 la loi dit VIVANT jusqu'au %s \u00b7 %s jours "
                    "\u00b7 le papier volait %s \u2014 la loi 2019 "
                    "couvre l'imprimé",
           "window": "→ hiver 2027 : %s, 8 h · 2e mercredi (%s) après le 12 : AVANCÉ · dans %s jours",
           "be": "→ hiver 2027 : %s · attente depuis %s · dans %s jours",
           "word": "\u2192 \u00ab %s \u00bb",
           "iban": "\u2192 cl\u00e9 de contr\u00f4le valide \u00b7 %s",
           "page": "\u2192 page autonome (%s octets) \u00b7 Ctrl-P = PDF",
           "days": "\u2192 %s jours \u00e0 tenir",
      "sale": "\u2192 %s € — en vrai -%s %%, pas -50 %%",
      "scale": "\u2192 farine %s exacte, peser %s \u00b7 les \u0153ufs "
               "sont dits, pas devin\u00e9s",
      "recur": "\u2192 %s puis %s \u00b7 bimensuel SAUTE des semaines \u2014 "
               "c'est dit",
      "shoe": "\u2192 %s mm exacts \u00b7 position EU %s \u2014 demi-"
              "grille %s, tiers %s \u2014 jamais un seul numéro",
      "comp": "\u2192 %s dus sous la NOUVELLE table (\u226523 oct. 2027) \u00b7 "
              "le transporteur PEUT payer %s \u00b7 réclamation avant le %s \u00b7 "
              "ou \u00a3220/\u00a3350/\u00a3520 sous UK261 \u00b7 même vol avant "
              "le 23 oct. 2027 : autre réponse",
      "bag": "\u2192 %s sous le siège par la LOI 2027 \u00b7 gabarit "
             "compagnie 40\u00d730\u00d720 : %s faces triées \u00b7 casier "
             ": la loi ne fixe RIEN",
      "cross": "\u2192 les deux tarifs s'inversent à %s kWh par mois "
               "(%s par an) \u00b7 exact — la presse arrondit le fixe "
               "avant de diviser",
      "points": "\u2192 %s centime par point, exactement %s \u00b7 "
                "au-dessus du plancher %s \u2192 on prend",
      "dim": "\u2192 factur\u00e9 %s kg (÷ 5 000) contre %s kg "
             "(÷ 6 000) \u2014 m\u00eame bo\u00eete, chaque \u00e9tape nomm\u00e9e",
      "bogo": "\u2192 l'affiche dit 50%%, la paire paie %s — on r\u00e8gle %s sur %s",
      "unitprice": "\u2192 500 g puis 400 g, m\u00eame \u00e9tiquette : "
                   "\u2212%s%% de produit, +%s%% au kilo \u2014 deux "
                   "d\u00e9nominateurs",
      "poultry": "\u2192 dinde 16 lb : cong\u00e9lateur avant %s, "
                 "jamais avant %s",
      "withdrawal": "\u2192 dernier jour pour se r\u00e9tracter : %s \u00b7 %s au jour dit",
      "settle": "→ net : B vire A %s \u20ac, UN virement prouvé · "
                "par reçu %s \u20ac · la remise de C vaut %s € nette vs %s "
                "€ sur le reçu",
      "prorate": "→ 1 000 € x 18 j : produit %s vs bailleur %s · "
                 "écart %s · nommés, jamais choisis pour vous",
      "payscale": "→ 52 000 ÷2 087 = %s /h · taux arrondi ×80 = %s "
                  "· ÷26 : écart %s · 2027 : %s paies",
      "leftovers": "\u2192 replay thanksgiving 2026 : \u00e0 consommer "
                   "avant %s \u00b7 bande %s",
      "ovenschedule": "\u2192 four allum\u00e9 %s, dinde dehors %s \u00b7 "
                      "conflits : %d — aucune timeline ne vérifie "
                      "ça",
      "deadline": "\u2192 dernier envoi %s (%s) \u00b7 la source discordante publie %s \u2014 nomm\u00e9e, jamais moyenn\u00e9e"},
    "pt": {"qr": "QR v%s \u00b7 %s\u00d7%s m\u00f3dulos \u00b7 SVG "
                 "impress\u00edvel, determin\u00edstico",
           "returndead": "\u2192 devolver at\u00e9 %s (%s) \u00b7 na "
                         "Target a janela de festas fechou em %s "
                         "\u2014 a manchete \u00ab at\u00e9 31 de "
                         "janeiro \u00bb nunca diz isso",
           "auditcut": "\u2192 %s \u00b7 refer\u00eancia legal %s \u00b7 "
                       "corte real %s%%, n\u00e3o os 30%% anunciados",
           "warr": "\u2192 conformidade legal at\u00e9 %s (%s) \u00b7 "
                   "v\u00edcios at\u00e9 %s desde a DESCOBERTA \u2014 "
                   "a loja fechou 15 de janeiro, a lei n\u00e3o",
           "rec": "\u2192 guardar até %s \u00b7 descartar a partir de %s \u00b7 o exemplo oficial 2022-23, refeito",
           "vouch": "\u2192 a lei diz VIVO até %s \u00b7 %s dias \u00b7 o "
                    "papel roubava %s dias \u2014 a Lei 2019 cobre o "
                    "impresso",
           "window": "\u2192 inverno 2027: %s às 8h \u00b7 a 2ª quarta "
                     "(%s) caiu após o dia 12: ANTECIPADO \u00b7 em "
                     "%s dias",
           "pricedrop": "\u2192 %s a reclamar at\u00e9 %s (%s) \u00b7 a "
                        "janela \u00e9 data publicada, a classe da "
                        "fonte viaja na linha",
           "word": "\u2192 \u201c%s\u201d",
           "iban": "\u2192 d\u00edgito verificador v\u00e1lido \u00b7 %s",
           "page": "\u2192 p\u00e1gina aut\u00f4noma (%s bytes) \u00b7 "
                   "Ctrl-P = PDF",
           "days": "\u2192 %s dias restantes",
      "sale": "→ R$ %s — na prática -%s %%, não -50%%",
      "scale": "→ farinha %s exata, pesar %s · ovos ditos, não "
               "adivinhados",
      "recur": "→ %s e %s · quinzenal PULA semanas — declarado",
      "shoe": "→ %s mm · posição EU %s — meia grade %s, "
              "terços %s · nunca um número só",
      "comp": "→ %s devidos pela NOVA tabela (≥23 out. 2027) · a "
              "companhia PODE pagar %s · reclamar até %s · ou "
              "£220/£350/£520 sob UK261 · ANAC/R$ é outra tabela, "
              "não calculada aqui",
      "bag": "→ %s sob o assento pela LEI 2027 · gabarito da cia "
             "40×30×20: %s com faces ordenadas · bagageiro: a lei "
             "não fixa NADA",
      "cross": "→ os dois planos se invertem a %s kWh por mês (%s por "
               "ano) · exato — as calculadoras da web arredondam o "
               "fixo antes",
      "points": "→ %s centavo por ponto, exato %s · acima do piso %s "
                "→ resgate",
      "dim": "→ cobrado %s kg (÷ 5 000) contra %s kg (÷ 6 000) — "
             "mesma caixa, cada passo nomeado",
      "bogo": "\u2192 a placa diz 50%%, o par sai por %s — voc\u00ea paga %s de %s",
      "unitprice": "\u2192 500 g viram 400 g, mesmo pre\u00e7o na placa: "
                   "\u2212%s%% de produto, +%s%% por quilo \u2014 dois "
                   "denominadores",
      "poultry": "\u2192 peru de 16 lb: geladeira at\u00e9 %s, nunca "
                 "antes de %s",
      "withdrawal": "\u2192 \u00faltimo dia para desistir: %s \u00b7 %s na data dita",
      "settle": "→ líquido: PIX R$ %s B→A, mínimo provado · nota a "
                "nota R$ %s · perdão de C: R$ %s no saldo, R$ %s na "
                "nota",
      "prorate": "→ R$ 1.000 x 18d: produto %s vs locador %s · "
                 "diferença %s · nomeadas, ninguém escolhe por você",
      "payscale": "→ 52.000 ÷2.087 = %s/h · taxa ×80 = %s "
                  "· ÷26: diferença %s · 2027: %s pagamentos",
      "leftovers": "\u2192 replay thanksgiving 2026: comer at\u00e9 %s "
                   "\u00b7 banda %s",
      "ovenschedule": "\u2192 forno ligado %s, peru de fora %s · "
                      "conflitos de temperatura: %d — nenhum "
                      "cronograma avisa isso",
      "deadline": "\u2192 \u00faltimo envio %s (%s) \u00b7 a fonte divergente publica %s \u2014 nomeada, nunca m\u00e9dia",
      "be": "\u2192 inverno 2027: %s \u00b7 espera desde %s \u00b7 em %s dias"},
}


_EVERYDAY_CALLS = [
    ("/api/v1/qr/generate",
     {"text": "WIFI:S:Box-Convives;T:WPA;P:soiree2026;;", "ecl": "Q",
      "format": "matrix"},
     "qr", lambda d, L: (str(d["version"]), str(d["size"]),
                         str(d["size"]))),
    ("/api/v1/number/spell",
     {"value": "1234.56", "lang": "%LANG%", "currency": "%CUR%"},
     "word", lambda d, L: (d.get("words", "?"),)),
    ("/api/v1/validate/iban",
     {"iban": "FR76 3000 4000 0312 3456 7890 143"},
     "iban", lambda d, L: (d.get("country", ""),)),
    ("/api/v1/md/render",
     {"markdown": "# Soupe du\n\ndimanche\n\n- 3 carottes\n- 2 pommes "
                  "de\nterre\n\n*feu doux, 40 min*",
      "document": True},
     "page", lambda d, L: (str(len(d["html"])),)),
    ("/api/v1/date/calc",
     {"base": "2026-11-21", "op": "diff",
      "params": {"until": "2027-07-14", "unit": "days"}},
     "days", lambda d, L: (str(d.get("days", "?")),)),
    ("/api/v1/money/discount",
     {"price": "89.90", "currency": "%CUR%",
      "steps": [{"type": "percent", "value": "30"},
                {"type": "percent", "value": "20"}]},
     "sale", lambda d, L: (("%.2f" % float(d["final_total"])).replace(
         ".", ",") if L != "en" else d["final_total"],
         ("%.2f" % float(d["effective_discount_pct"])).replace(
             ".", ",") if L != "en" else d["effective_discount_pct"])),
    ("/api/v1/table/scale",
     {"items": [{"name": "flour", "qty": "400", "unit": "g"},
                {"name": "eggs", "qty": "5", "unit": "piece",
                 "class": "egg"}],
      "servings_from": "6", "servings_to": "2"},
     "scale", lambda d, L: (d["items"][0]["exact"]["fraction"],
                             d["items"][0]["measurable"]["value"])),
    ("/api/v1/date/recurrence",
     {"dtstart": "2026-11-03T19:00:00",
      "rrule": "FREQ=WEEKLY;INTERVAL=2;BYDAY=TU;COUNT=4"},
     "recur", lambda d, L: (d["occurrences"][1]["iso"][5:10],
                             d["occurrences"][2]["iso"][5:10])),
    ("/api/v1/units/shoe_size", {"foot_mm": "271"}, "shoe",
     lambda d, L: (
         d["foot_mm"]["decimal_mm"].rstrip("0").rstrip("."),
         d["systems"]["eu"]["position"]["decimal"].replace(
             ".", ",") if L != "en"
         else d["systems"]["eu"]["position"]["decimal"],
         d["systems"]["eu"]["candidates"]["grid_1/2"][0],
         d["systems"]["eu"]["candidates"]["grid_1/3"][1])),
    ("/api/v1/money/flight_comp",
     {"regime": "EU", "flight_date": "2027-11-01", "event": "delay",
      "distance_km": "5800", "intra_eu": "no", "delay_min": "210"},
     "comp", lambda d, L: (
         d["owed"]["display"],
         d["reductions_may"][0]["amount"] if d["reductions_may"] else "?",
         d["deadlines"]["claim_by"])),
    ("/api/v1/money/baggage",
     {"flight_date": "2027-11-02", "regime": "EU", "bag": "40x18x12",
      "personal_sizer": "40x30x20"},
     "bag", lambda d, L: (
         {"en": "FREE", "fr": "GRATUIT", "pt": "GRÁTIS"}[L]
         if d["personal_law"]["within_legal_safe_harbour"]
         else {"en": "NOT free by law", "fr": "non gratuit",
               "pt": "não grátis"}[L],
         {"en": "fits", "fr": "passe", "pt": "cabe"}[L]
         if d["carrier"]["personal_vs_sizer"]["fits"]
         else {"en": "over", "fr": "dépassé", "pt": "estoura"}[L])),
    ("/api/v1/money/crossover",
     {"a_unit_rate": "0.30", "a_unit_per": "kWh", "a_fixed": "12",
      "a_fixed_per": "month", "b_unit_rate": "0.26",
      "b_unit_per": "kWh", "b_fixed": "22", "b_fixed_per": "month",
      "currency": "EUR"},
     "cross", lambda d, L: (
         {"en": lambda s: s, "fr": lambda s: s.replace(".", ","),
          "pt": lambda s: s.replace(".", ",")}[L](
             d["crossover"]["per_month"]),
         {"en": lambda s: "3,000", "fr": lambda s: "3 000",
          "pt": lambda s: "3.000"}[L](d["crossover"]["per_year"]))),
    ("/api/v1/money/points",
     {"currency": "%CUR%", "floor": "1.0", "routes": [
         {"name": "flight", "points": "29000", "cash_price": "438",
          "cash_still_paid": "5.60"}]},
     "points", lambda d, L: (
         {"en": lambda s: s, "fr": lambda s: s.replace(".", ","),
          "pt": lambda s: s.replace(".", ",")}[L](
             d["routes"][0]["cpp_press_2dp"]),
         "%s/%s" % (d["routes"][0]["cpp_exact"]["numerator"],
                    d["routes"][0]["cpp_exact"]["denominator"]),
         {"en": lambda s: s, "fr": lambda s: s.replace(".", ","),
          "pt": lambda s: s.replace(".", ",")}[L](
             d["routes"][0]["vs_floor"]["floor"]))),
    ("/api/v1/ship/dimweight",
     {"dims": {"l": "40", "w": "30", "h": "25", "unit": "cm"},
      "actual_weight": {"value": "1.2", "unit": "kg"},
      "rules": [
          {"name": "carrier-5000", "divisor": "5000",
           "divisor_unit": "cm3_kg", "dim_round": "ceil",
           "weight_step": "1"},
          {"name": "carrier-6000", "divisor": "6000",
           "divisor_unit": "cm3_kg", "dim_round": "ceil",
           "weight_step": "1"}]},
     "dim", lambda d, L: (
         d["results"][0]["billed_weight"],
         d["results"][1]["billed_weight"])),
    ("/api/v1/money/bogo",
     {"offer": "bogo_percent", "second_percent": "50",
      "pairs": [["60.00", "40.00"]]},
     "bogo", lambda d, L_: tuple(
         {"en": lambda s: s, "fr": lambda s: s.replace(".", ","),
          "pt": lambda s: s.replace(".", ",")}[L_](
             d["effective"]["percent"] + "|" + d["totals"]["paid"] +
             "|" + d["totals"]["full"]).split("|"))),
    ("/api/v1/money/unitprice",
     {"mode": "shrink", "unit": "g", "old_size": "500",
      "new_size": "400"},
     "unitprice", lambda d, L_: tuple(
         {"en": lambda s: s, "fr": lambda s: s.replace(".", ","),
          "pt": lambda s: s.replace(".", ",")}[L_](
             d["product_change"]["display"] + "|" +
             d["unit_price_change"]["display"]).split("|"))),
    ("/api/v1/food/poultry",
     {"weight": "16", "oven_at": "2026-11-26T10:00"},
     "poultry", lambda d, L_: (
         d["put_in_refrigerator"]["by"],
         d["put_in_refrigerator"]["not_before"])),
    ("/api/v1/food/ovenschedule",
     {"serve_at": "2026-11-26T16:00",
      "dishes": [
          {"name": "turkey", "minutes": 195, "temp": 325,
           "temp_unit": "F", "rest": 25},
          {"name": "stuffing", "minutes": 45, "temp": 325,
           "temp_unit": "F", "rest": 15},
          {"name": "rolls", "minutes": 15, "temp": 425,
           "temp_unit": "F"}]},
     "ovenschedule", lambda d, L_: (
         d["oven_on_at"][11:16], d["dishes"][0]["out_at"][11:16],
         d["temp_conflicts"])),
    ("/api/v1/shop/shipping-deadline",
     {"carrier": "fedex", "service": "express-saver"},
     "deadline", lambda d, L_: (
         d["ship_by"], d["ship_by_weekday"],
         d["cross_check"]["conflict"]["ship_by"])),
    ("/api/v1/shop/return-deadline",
     {"retailer": "target", "purchase_date": "2026-12-20",
      "category": "phone"},
     "returndead", lambda d, L_: (
         d["return_by"], d["return_by_weekday"],
         d["purchase_window"][1])),
    ("/api/v1/shop/discount-audit",
     {"history": [{"date": "2026-10-01", "price": "100.00"},
                  {"date": "2026-11-07", "price": "80.00"},
                  {"date": "2026-11-09", "price": "100.00"}],
      "as_of": "2026-11-27", "sale_price": "70.00",
      "previous_price": "100.00", "claimed_percent": "30"},
     "auditcut", lambda d, L_: (
         d["verdict"], d["reference_price"], d["true_percent"])),
    ("/api/v1/shop/pricedrop-refund",
     {"retailer": "target", "purchase_date": "2026-11-20",
      "drop_date": "2026-12-10", "purchase_price": "100.00",
      "new_price": "80.00"},
     "pricedrop", lambda d, L_: (
         d["refund_amount"], d["claim_by"],
         d["claim_by_weekday"])),
    ("/api/v1/shop/legal-guarantee",
     {"jurisdiction": "FR", "delivered_on": "2026-12-25",
      "discovered_on": "2027-01-16", "as_of": "2027-01-16"},
     "warr", lambda d, L_: (
         d["conformite_action_by"]["date"],
         d["conformite_action_by"]["weekday"],
         d["vices"]["action_by"])),
    ("/api/v1/money/keep-records-uk",
     {"record_kind": "self_assessment",
      "tax_year_end_on": "2023-04-05"},
     "rec", lambda d, L_: (d["retain_until"],
                           d["safe_destroy_on"])),
    ("/api/v1/shop/gift-voucher",
     {"jurisdiction": "ie", "purchased_on": "2025-11-01",
      "printed_expiry_on": "2026-11-01", "as_of": "2026-11-24"},
     "vouch", lambda d, L_: (d["legal_expiry_on"],
                             str(d["days_left"]),
                             d["paper_vs_law"]["days_the_printed_date_stole"])),
    ("/api/v1/shop/soldes-window",
     {"year": 2027, "territory": "metropole", "season": "hiver",
      "as_of": "2026-11-24"},
     "window", lambda d, L_: (d["windows"][0]["start"],
                              d["windows"][0]["rule"][
                                  "second_wednesday"],
                              str(d["windows"][0]["days_to_start"]))),
    ("/api/v1/shop/withdrawal",
     {"start_date": "2026-11-24", "as_of": "2026-11-25"},
     "withdrawal", lambda d, L_: (
         d["deadline"], d["verdict"])),
    ("/api/v1/money/settle",
     {"advances": [{"who": "A", "paid": "1375.00"},
                   {"who": "B", "paid": "0.00"},
                   {"who": "C", "paid": "865.00"}],
      "participants": ["A", "B", "C"],
      "waivers": [{"from": "C", "to": "B"}],
      "currency": "%CUR%", "mode": "compare"},
     "settle", lambda d, L: tuple(
         (v.replace(".", ",") if L != "en" else v) for v in (
             d["divergence"]["pays_net"]["B->A"],
             d["divergence"]["pays_itemized"]["B->A"],
             d["divergence"]["forgiveness_applied_net"]["C->B"],
             d["divergence"]["forgiveness_applied_itemized"]["C->B"]))),
    ("/api/v1/money/prorate",
     {"amount": "1000", "cycle_start": "2018-11-01",
      "cycle_end": "2018-11-30", "service_start": "2018-11-01",
      "service_end": "2018-11-18", "order": "quotient",
      "compare": True},
     "prorate", lambda d, L: tuple(
         (v.replace(".", ",") if L != "en" else v) for v in (
             d["conventions"]["orders"]["product"],
             d["conventions"]["orders"]["quotient"],
             d["conventions"]["orders"]["delta_product_minus_quotient"
                                        ]))),
    ("/api/v1/money/payscale",
     {"annual": "52000", "basis": "fed2087",
      "period": "biweekly", "year": 2027,
      "payday_weekday": "fri"},
     "payscale", lambda d, L: tuple(
         (v.replace(".", ",") if L != "en" else v) for v in (
             d["hourly"]["rounded_cent"],
             d["periods"]["biweekly"]["rate_first"],
             d["periods"]["biweekly"]["delta_rate_first_minus_direct"
                                        ],
             str(d["paydays_in_year"]["every_other_from_first"])))),
]


# keys that live in the locale dicts but are consumed HERE at build
# time (baked into everyday_grid), not as {{tokens}} in TEMPLATE —
# test_i18n checks parity against this list, not against luck.
BUILDER_CONSUMED = {"everyday.h2", "everyday.intro",
    "everyday.open"} | {
    "everyday.e%d.%s" % (i, f)
    for i in range(1, len(_EVERYDAY_CALLS) + 1)
    for f in ("name", "say")}


MARKET = [
    ("Tools are a new kind of software which reflects a contract between "
     "deterministic systems and non-deterministic agents.",
     "Anthropic Engineering", "Writing effective tools for AI agents, "
     "jun 2026",
     "https://www.anthropic.com/engineering/writing-tools-for-agents"),
    ("When we launched Claude's web search tool, we identified that Claude "
     "was needlessly appending 2025 to the tool's query parameter, biasing "
     "search results and degrading performance.",
     "Anthropic Engineering", "same article — mechanics the model kept "
     "re-inventing",
     "https://www.anthropic.com/engineering/writing-tools-for-agents"),
    ("Orchestrating via code makes tasks more deterministic and predictable, "
     "in terms of speed, cost and performance.",
     "OpenAI", "Agents SDK docs, Agent Orchestration",
     "https://openai.github.io/openai-agents-js/guides/multi-agent/"),
    ("If the model has to rediscover the same shell recipe every time, that "
     "is usually a sign that the recipe should be a script.",
     "OpenAI Developers blog", "Using skills to accelerate OSS maintenance, "
     "mar 2026", "https://developers.openai.com/blog/skills-agents-sdk"),
    ("When you push deterministic work through an LLM, things break in "
     "unpredictable ways and you stop trusting the system.",
     "Peter Steinberger", "creator of OpenClaw — LLMs judge, scripts do "
     "the deterministic work",
     "https://www.coldmountain.ai/wiki/people/peter-steinberger"),
    ("Grok @Bot can do your accounting.",
     "Elon Musk", "@elonmusk on X, nov 2026 — while ToolFailBench "
     "measures Grok-4.3 at 86.33% faithful tool use",
     "https://finance.yahoo.com/technology/ai/articles/elon-musk-says-"
     "grok-accounting-043007297.html"),
    ("Bots are AI teammates that do real work for you. They sign in to "
     "your tools, use them just like you do, and come back with finished "
     "work.",
     "xAI, Grok Bot launch", "@bot on X, aug 2026 — the promise; the "
     "arithmetic it leans on is exactly what we make exact",
     "https://interestingengineering.com/ai-robotics/xai-grok-bot-"
     "computer-agent"),
    ("We don't store memories; we generate them. That's what memory is "
     "like in large language models, and that's why they can confabulate.",
     "Geoffrey Hinton", "AI4 conference, 2026 — why the answer to an "
     "invoice total is generated, never retrieved",
     "https://www.rdworldonline.com/hinton-ai4-conference-language-"
     "model-insights-rd-impact/"),
    ("Traditional computers automate what you can specify in code. This "
     "latest round of LLMs can automate what you can verify.",
     "Andrej Karpathy", "Sequoia Ascent 2026 — and what can be verified "
     "deserves to be specified once, exactly",
     "https://karpathy.bearblog.dev/sequoia-ascent-2026/"),
    ("Faithful tool use is not saturated: even the best of 19 headline "
     "models — Grok-4.3 at 86.33%, Claude, GPT, Qwen behind — still "
     "fumbles a meaningful fraction of tool-required tasks.",
     "ToolFailBench", "arXiv 2607.04686, 2026 — the field measuring what "
     "we sell", "https://arxiv.org/abs/2607.04686"),
]


def market_html(lang, cat):
    cells = []
    for q, who, when, url in MARKET:
        cells.append(
            '<div class="mcard"><q>%s</q><cite><b>%s</b> — %s<br>'
            '<a href="%s">%s</a></cite></div>'
            % (q.replace("<", "&lt;"), who, when, url,
               url.split("/")[2]))
    return '<div class="mgrid">%s</div>' % "".join(cells)


def everyday_html(lang, cat):
    from fastapi.testclient import TestClient
    import main as _m
    _m.RATE_LIMIT = 10**9  # build harness: 12 cards x 3 langs > 30/min,
    # the last pt chips used to bake as "?" silently (22-11)
    cli = TestClient(_m.app)
    cur = {"en": "USD", "fr": "EUR", "pt": "BRL"}[lang]

    def sub(v):
        if isinstance(v, str):
            return v.replace("%LANG%", lang).replace("%CUR%", cur)
        if isinstance(v, dict):
            return {k: sub(x) for k, x in v.items()}
        return v

    cells = []
    for i, (path, body, wkey, argf) in enumerate(_EVERYDAY_CALLS, 1):
        try:
            r = cli.post(path, json=sub(body))
            chip = (W[lang][wkey] % argf(r.json(), lang)
                    if r.status_code == 200 else "?")
        except Exception:
            chip = "?"
        key = "e%d" % i
        cells.append(
            '<div class="play"><h3>%s</h3>'
            '<p class="playsay">%s</p>'
            '<pre class="playgot">%s</pre></div>'
            % (cat["everyday.%s.name" % key],
               cat["everyday.%s.say" % key],
               chip.replace("<", "&lt;")))
    return ('<section class="section" id="everyday">\n'
            '      <h2>%s</h2>\n'
            '      <p class="tiers" style="color: var(--muted); '
            'max-width: 720px;">%s</p>\n'
            '      <details class="bcard"><summary>%s</summary>\n'
            '      <div class="playgrid">%s</div></details>\n    </section>'
            % (cat["everyday.h2"], cat["everyday.intro"],
               cat["everyday.open"], "".join(cells)))


def catalog_grid(lang):
    """Click-first catalogue: chips (pack x tier) + search + compact cards.
    The grid has a fixed max-height, so the page budget cannot grow with
    len(TABLE): 90 tools fit the same three screens as 53. All text is
    baked server-side — the runtime substitution is a single pass."""
    chips = ['<span class="chip on" data-f="top=1">%s</span>'
                  % CAT_TOP10[lang],
             '<span class="chip" data-f="x=all">%s</span>' % CAT_ALL[lang]]
    for pk in routing.PACKS:
        chips.append('<span class="chip" data-f="pack=%s">%s</span>'
                     % (pk, PACK_TITLE[lang].get(pk, pk)))
    for t in ("free", "cap", "paid"):
        word = TIER_CHIP[lang][t]
        # b123 elagage MESURE (+stats_rate_ci, le budget FR casse de 108
        # octets, PT de 181) : l'attribut TITLE des chips TIERS est SUPPRIME
        # — il repetait mot a mot la legende visible juste dessous (la ligne
        # <span class="lg"> porte deja BADGE+MOT+REGLE pour les trois
        # paliers). Claim constant, precedent b114 « le chemin vit DEJA
        # ailleurs » : ce qui vit deux fois ne paie qu'une fois.
        chips.append('<span class="chip" data-f="tier=%s">%s %s</span>'
                     % (t, BADGE[t], word))
    legend = " · ".join('<span class="lg">%s %s — %s</span>'
                        % (BADGE[t], TIER_CHIP[lang][t], TIER_RULE[lang][t])
                        for t in ("free", "cap", "paid"))
    cards = []
    for name, path, pack, purpose, tags in routing.TABLE:
        tier = path_tier[name]
        hay = " ".join((purpose, tags)).lower()
        # b119: le NAME quitte le hay — la clause data-tool de ok()
        # (search JS) le couvre deja, mot-a-mot. ~2,7 k rendus PAR
        # page, zero vocabulaire perdu pour la recherche.
        # b110 structurel (budget FR franchi) : DEDUP mot-à-mot à
        # l'ordre de première occurrence. Le search matche par
        # indexOf de chaque mot saisi — dédoublonner ne retire
        # AUCUN vocabulaire de la carte, retire seulement la redite
        # name/purpose/tags (les trois portent les mêmes mots).
        # Gain mesuré : ~4,7 k octets PAR page (FR sous le plafond,
        # EN rendu au plafond, PT rapproché). Précédent ratissage
        # b107/b108 (prose), ce levier est chrome, pas claim.
        _seen, _uniq = set(), []
        for _w in hay.split():
            if _w not in _seen:
                _seen.add(_w)
                _uniq.append(_w)
        hay = " ".join(_uniq)
        hay = hay.replace("&", "&amp;").replace('"', "&quot;")
        purp = PURPOSES.get(lang, {}).get(name, purpose)
        purp = purp.replace("&", "&amp;").replace("<", "&lt;")
        cards.append(
            '<button class="tcard" data-pack="%s" data-tier="%s"%s'
            ' data-tool="%s" data-hay="%s"> <code>%s</code>'
            '<span class="tp">%s</span></button>'
            % (pack, tier, ' data-top="1"' if name in TOP10 else '', name, hay, name, purp))
    # b124_hermes elagage MESURE (+pdf_provenance, budget PT a 8 octets
    # de marge) : les 13 liens packs sont REPLIES en un gabarit —
    # « /SKILL-<pack>.md » se nomme lui-meme, les NOMS des packs vivent
    # deja dans les puces (data-f=pack=X). Precedent b114 du manifeste :
    # « le chemin vit DEJA ailleurs ». Le claim « les packs existent a
    # ces URLs » voyage intact.
    packs = "/SKILL-&lt;pack&gt;.md" 
    return (
        '<div class="chips">%s</div>\n'
        '<p class="tierlegend">%s</p>\n'
        '<div class="catgrid">%s</div>\n'
        '<p class="packlinks">%s %s</p>'
        % ("".join(chips), legend, "".join(cards),
           PACK_LABEL_EXTRA[lang], packs))


def bench_rows_html():
    out = []
    for m, a_ok, b_ok, a_tok, b_tok in BENCH:
        out.append(
            '        <tr><td>Qwen 2.5 %s</td>'
            '<td class="%s">%s</td><td class="%s">%s</td>'
            '<td class="num">%d → %d</td></tr>'
            % (m, "yes" if a_ok else "no", "✓" if a_ok else "✗",
               "yes" if b_ok else "no", "✓" if b_ok else "✗", a_tok, b_tok))
    return "\n".join(out)


def bench9_rows():
    """Latest v9-intake row per (model, arm). Separate file ON PURPOSE:
    a card-relay run must never overwrite what the v6 ✅ means."""
    latest = {}
    f = ROOT / "bench" / "results_v9.jsonl"
    if not f.exists():
        return []
    with open(f, encoding="utf-8") as fh:
      for line in fh:
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("harness") != "v9-intake":
            continue
        if r.get("arm") in ("naked", "intake"):
            latest[(r["model"], r["arm"])] = r
    rows = []
    for m in ("0.5b", "1.5b", "7b"):
        a = latest.get((m, "naked"))
        b = latest.get((m, "intake"))
        if a and b:
            rows.append((m, a["keys"], b["keys"], a["tokens"], b["tokens"]))
    return rows


BENCH9 = bench9_rows()


def bench10_rows():
    """Latest v10 row per (model, arm, task) from results_v10.jsonl —
    exact-answer tasks, two free LOCAL models, cost $0 audited by the
    harness itself. Its own file on purpose: a v10 ✅ must never change
    what the v6 or v9 rows mean."""
    latest = {}
    f = ROOT / "bench" / "results_v10.jsonl"
    if not f.exists():
        return []
    with open(f, encoding="utf-8") as fh:
      for line in fh:
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("harness") != "v10":
            continue
        latest[(r["model"], r["arm"], r["task"])] = r
    rows = []
    for m in ("7b", "8b"):
        tasks = sorted({t for (mm, arm, t) in latest if mm == m})
        if not tasks:
            continue
        n = len(tasks)
        a_ok = sum(1 for t in tasks
                   if latest.get((m, "naked", t), {}).get("ok"))
        b_ok = sum(1 for t in tasks
                   if latest.get((m, "relay", t), {}).get("ok"))
        a_tok = sum(latest[(m, "naked", t)].get("tokens", 0)
                    for t in tasks if (m, "naked", t) in latest)
        b_tok = sum(latest[(m, "relay", t)].get("tokens", 0)
                    for t in tasks if (m, "relay", t) in latest)
        rows.append((m, a_ok, b_ok, n, a_tok, b_tok))
    return rows


BENCH10 = bench10_rows()


def bench12_rows():
    """v12 : 4 modèles gratuits locaux × 3 bras (nu/code/relais) sur
    10 calculs exacts. Lu depuis results_v12.jsonl — le générateur ne
    peut pas inventer un ✅."""
    f = ROOT / "bench" / "results_v12.jsonl"
    if not f.exists():
        return []
    agg = {}
    with open(f, encoding="utf-8") as fh:
      for line in fh:
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("harness") != "v12":
            continue
        k = (r["model"], r["arm"])
        a = agg.setdefault(k, [0, 0])
        a[1] += 1
        a[0] += 1 if r["ok"] else 0
    rows = []
    for m in ("0.5b", "1.5b", "7b", "8b"):
        cells = [tuple(agg.get((m, arm), (0, 10)))
                 for arm in ("naked", "code", "relay")]
        if any(t for _, t in cells):
            rows.append((m, cells))
    return rows


BENCH12 = bench12_rows()
assert BENCH12, "no v12 rows — run bench/run12.py first"


# ---------------- hub des bancs : tout vient du brut -----------------
def _rows_of(fname):
    import json as _j
    f = ROOT / "bench" / fname
    if not f.exists():
        return []
    with open(f, encoding="utf-8") as fh:
        return [_j.loads(l) for l in fh if l.strip()]


def compute_hub():
    """Chaque nombre affiché par le hub est recalculé ici depuis les
    jsonls ; test_landing les recalcule à son tour indépendamment —
    le générateur ne peut pas inventer un chiffre."""
    h = {}
    m15 = _rows_of("results_v15_matrix.jsonl")
    ch = [r for r in m15 if r.get("family") in ("mix", "partage")
          and r.get("arm") in ("N", "T", "S", "C", "R")]
    h["v15_cells"] = sum(1 for r in ch if r["arm"] in ("N", "T"))
    h["v15_alone_wins"] = sum(1 for r in ch if r["arm"] in ("N", "T")
                              and r["ok"])
    h["v15_server_wins"] = sum(1 for r in ch if r["arm"] in
                               ("S", "C", "R") and r["ok"])
    per_arm = {arm: sum(1 for r in ch if r["arm"] == arm and r["ok"])
               for arm in ("S", "C", "R")}
    h["v15_best_arm"] = max(per_arm.values())
    h["v15_arm_cells"] = sum(1 for r in ch if r["arm"] ==
                             max(per_arm, key=per_arm.get))
    m16 = _rows_of("results_v16_calibration.jsonl")
    h["v16_runs"] = len(m16)
    h["v16_wrong"] = sum(1 for r in m16 if not r["ok"])
    h["v16_doubt"] = sum(1 for r in m16
                         if r.get("confident") is False)
    m17 = _rows_of("results_v17_tokens.jsonl")

    def a17(r):
        a = r["arm"]
        return ("nu" if a.startswith("nude") else
                "retry" if a.startswith("retry") else "relay")
    tbl = {}
    for r in m17:
        d = tbl.setdefault((r["model"], a17(r)), [0, 0, 0])
        d[0] += 1
        d[1] += int(bool(r["ok"]))
        d[2] += r["tokens"]
    h["v17_tbl"] = tbl
    ch17 = [r for r in m17 if r.get("family") in ("mix", "partage")
            and a17(r) == "retry"]
    h["v17_retry_cells"] = len(ch17)
    h["v17_retry_wins"] = sum(1 for r in ch17 if r["ok"])
    h["v17_cells"] = len(m17)
    m19 = _rows_of("results_v19_csv_bill.jsonl")
    agg = {}
    for r in m19:
        d = agg.setdefault((r["arm"], r["model"]),
                           {"n": 0, "c": 0, "t": 0, "s": set()})
        d["n"] += 1
        d["c"] += int(bool(r["correct"]))
        d["t"] += r["toks"]
        d["s"].add(r["sha"])
    h["v19"] = agg
    h["v19_days"] = sum(d["n"] for k, d in agg.items()
                        if k[0] in ("N", "R"))
    h["v19_wins"] = sum(d["c"] for k, d in agg.items()
                        if k[0] in ("N", "R"))
    h["v19_drift"] = max(len(d["s"]) for k, d in agg.items()
                         if k[0] == "N")
    h["v19_m_days"] = agg[("M", "machine")]["n"]
    h["v19_m_ok"] = agg[("M", "machine")]["c"]
    h["v19_mult"] = "%.1f" % (
        sum(d["t"] for k, d in agg.items() if k[0] == "R") /
        max(1, sum(d["t"] for k, d in agg.items() if k[0] == "N")))
    # ---------------- v20 : le verrou de cible (120 cellules)
    m20 = _rows_of("results_v20_target_lock.jsonl")

    def w20(mk, arm):
        return sum(1 for r in m20 if r["model"] == mk
                   and r["arm"] == arm and r["ok"])
    h["v20_8b_s"], h["v20_8b_l"] = w20("8b", "S"), w20("8b", "L")
    h["v20_7b_s"], h["v20_7b_l"] = w20("7b", "S"), w20("7b", "L")
    h["v20_15b_s"], h["v20_15b_l"] = w20("1.5b", "S"), w20("1.5b", "L")
    h["v20_replay"] = "%d/%d/%d" % (h["v20_8b_s"], h["v20_7b_s"],
                                    h["v20_15b_s"])
    from gen16 import problems as _probs
    q20 = {t["i"]: t for t in _probs()}

    def _aside(r):
        t = q20[r["i"]]
        return (r["got"] is not None and
                any(abs(float(v) - r["got"]) < 0.005 and
                    k != t["cible"] for k, v in t["qte"].items()))
    aside_i = {r["i"] for r in m20 if r["arm"] == "S" and not r["ok"]
               and _aside(r)}
    h["v20_aside"] = len(aside_i)
    h["v20_aside_conv"] = sum(
        1 for i in aside_i if any(r["arm"] == "L" and r["i"] == i
                                  and r["ok"] for r in m20))
    h["v20_cells"] = len(m20)
    # ---------------- v23 : la réplication hors-famille (60 cellules)
    m23 = _rows_of("results_v23_lfm3.jsonl")
    CH23 = ("mix", "partage")
    h["v23_chain"] = sum(1 for r in m23 if r["arm"] == "N"
                         and r["family"] in CH23 and r["ok"])
    h["v23_chain_cells"] = sum(1 for r in m23 if r["arm"] == "N"
                               and r["family"] in CH23)
    h["v23_cost"] = "%.4f" % sum(r["usd"] for r in m23
                                 if r["arm"] == "N")
    arm23, tbl23 = {}, {}
    for a in ("N", "S", "L"):
        rs = [r for r in m23 if r["arm"] == a]
        arm23[a] = sum(1 for r in rs if r["ok"])
        tbl23[a] = (arm23[a], len(rs),
                    "%.4f" % sum(r["usd"] for r in rs))
    h["v23_n_all"], h["v23_s_all"], h["v23_l_all"] = (arm23["N"],
                                                      arm23["S"],
                                                      arm23["L"])
    h["v23_refused"] = sum(1 for r in m23 if r["arm"] == "L"
                           and not r["ok"] and r["got"] is not None
                           and abs(r["got"] - r["gold"]) < 0.005)
    h["v23_tbl"] = tbl23
    h["v23_usd"] = "%.4f" % sum(r["usd"] for r in m23)
    # ---------------- les oubliées du hub : v11, v13, v14, F5,
    # ---------------- v22, v22b, v24 ----------------
    m11 = _rows_of("results_v11.jsonl")
    def w11(model_sub, arm):
        rs = [r for r in m11 if model_sub in r["model"]
              and r["arm"] == arm]
        return "%d/%d" % (sum(1 for r in rs if r["ok"]), len(rs))
    h["v11_7b_nu"] = w11("7b", "naked")
    h["v11_7b_relay"] = w11("7b", "relay")
    h["v11_8b_nu"] = w11("8b", "naked")
    h["v11_8b_relay"] = w11("8b", "relay")
    m13 = _rows_of("results_v13_gsm8k.jsonl")
    def w13(model, arm):
        rs = [r for r in m13 if r["model"] == model and r["arm"] == arm]
        return sum(1 for r in rs if r["ok"])
    h["v13_relay_05b"] = w13("0.5b", "relay")
    h["v13_relay_8b"] = w13("8b", "relay")
    h["v13_nu_05b"] = w13("0.5b", "naked")
    m14 = _rows_of("results_v14_skill.jsonl")
    h["v14_breaks"] = sum(1 for r in m14
                          if r.get("err") == "protocol_giveup")
    h["v14_steps"] = sum(1 for r in m14 if r.get("err") == "max_steps")
    h["v14_ok"] = sum(1 for r in m14 if r["ok"])
    h["v14_cells"] = len(m14)
    mf5 = _rows_of("results_f5_accept.jsonl")
    h["f5_wins"] = sum(1 for r in mf5 if r["verdict"] == "OK")
    h["f5_cells"] = len(mf5)
    h["f5_repairs"] = sum(r["repairs"] for r in mf5)
    h["f5_7b"] = "%d/%d" % (sum(1 for r in mf5 if r["model"] == "7b"
                                and r["verdict"] == "OK"),
                            sum(1 for r in mf5 if r["model"] == "7b"))
    m22 = _rows_of("results_v22.jsonl")

    def w22(arm, model=None):
        rs = [r for r in m22 if r["arm"] == arm
              and (model is None or r["model"] == model)]
        return "%d/%d" % (sum(1 for r in rs if r["ok"]), len(rs))
    h["v22_nu"] = w22("N")
    h["v22_fiche"] = w22("F")
    h["v22_code"] = w22("C")
    # meilleur/pire modèle au bras N — la carte doit nommer ses
    # dénominateurs (loi du guard : une phrase = des nombres dont
    # chacun a LE SIEN sujet, vérifié par test_bundle52).
    per_n = {m: sum(1 for r in m22 if r["arm"] == "N" and r["model"] == m
                    and r["ok"])
             for m in {r["model"] for r in m22 if r["arm"] == "N"}}
    best = max(per_n, key=lambda m: per_n[m])
    worst = min(per_n, key=lambda m: per_n[m])
    h["v22_best"] = "%d/7" % per_n[best]
    h["v22_worst"] = "%d/7" % per_n[worst]
    m22b = _rows_of("results_v22b.jsonl")
    h["v22b_ok"] = sum(1 for r in m22b if r["c_ok"])
    h["v22b_cells"] = len(m22b)
    pairs = {}
    msha = {}
    for r in m22b:
        pairs.setdefault((r["model"], str(r["i"])), set()).add(r["code_sha"])
        msha.setdefault(str(r["i"]), set()).add(r["m_sha"])
    h["v22b_stable"] = sum(1 for v in pairs.values() if len(v) == 1)
    h["v22b_shas"] = str(max(len(v) for v in msha.values()))
    m24 = _rows_of("results_v24_lfm3_30days.jsonl")
    n24 = [r for r in m24 if r["arm"] == "N"]
    mm24 = [r for r in m24 if r["arm"] == "M"]
    h["v24_days"] = len(n24)
    h["v24_sil"] = sum(1 for r in n24
                       if r["sha"] == "01ba4719c80b6fe9")
    # SILENCE STRICT = la réponse vide (sha du newline), pas
    # « forme refusée » : l'exemplaire 26 comptait comme silence le
    # seul jour de contenu mal formé non vide (d7f807). 25 vides +
    # 4 justes + 1 malformé = 30. Garde mirrors la même ligne.
    h["v24_ok"] = sum(1 for r in n24 if r["ok"])
    h["v24_usd"] = "%.4f" % sum(r["usd"] for r in n24)
    h["v24_m_ok"] = "%d/%d" % (sum(1 for r in mm24 if r["ok"]),
                               len(mm24))
    # ---------------- F7 : EN/PT sur les mêmes maths (56 cellules)
    m7 = _rows_of("results_f7_accept.jsonl")
    m7 = [r for r in m7 if r["harness"] == "f7-accept"]
    h["f7_wins"] = sum(1 for r in m7 if r["verdict"] == "OK")
    h["f7_cells"] = len(m7)
    h["f7_rep"] = sum(1 for r in m7 if r["verdict"] == "OK"
                      and r["repairs"] > 0)
    return h


HUB = compute_hub()


def _fmt_tok(n):
    return "{:,}".format(int(n)).replace(",", " ")


def bench19_rows_html():
    out = []
    for k in (("M", "machine"), ("N", "1.5b"), ("R", "1.5b"),
              ("N", "7b"), ("R", "7b")):
        d = HUB["v19"][k]
        out.append('<tr><td>%s&nbsp;%s</td><td class="%s">%d/%d</td>'
                   '<td class="num">%d</td><td class="num">%s</td></tr>'
                   % (k[0], k[1], "yes" if d["c"] == d["n"] else "no",
                      d["c"], d["n"], len(d["s"]), _fmt_tok(d["t"])))
    return "\n".join(out)


def bench17_rows_html():
    out = []
    for m in ("1.5b", "7b", "8b"):
        cells = []
        for a in ("nu", "retry", "relay"):
            d = HUB["v17_tbl"].get((m, a))
            if not d:
                cells.append('<td class="num">—</td>')
                continue
            per = ("∞" if d[1] == 0
                   else _fmt_tok(round(d[2] / d[1])))
            cells.append('<td class="num">%d/%d · %s</td>'
                         % (d[1], d[0], per))
        out.append("<tr><td>%s</td>%s</tr>" % (m, "".join(cells)))
    return "\n".join(out)


LABEL12 = {"0.5b": "qwen2.5:0.5b", "1.5b": "qwen2.5:1.5b",
           "7b": "qwen2.5:7b-q4", "8b": "llama3.1:8b"}


def bench12_rows_html():
    out = []
    for m, (nk, cd, rl) in BENCH12:
        cells = ""
        for ok, tot in (nk, cd, rl):
            cls = "yes" if ok == 10 else ("no" if ok <= 2 else "")
            cells += '<td class="%s">%d/10</td>' % (cls, ok)
        out.append("        <tr><td>%s</td>%s</tr>"
                   % (LABEL12.get(m, m), cells))
    return "\n".join(out)
assert BENCH10, "no v10 bench rows — run bench/run10.py first"


MODEL_LABEL = {"7b": "qwen2.5:7b-q4 (local)",
               "8b": "llama3.1:8b (local)"}


def bench10_rows_html():
    out = []
    for m, ak, bk, n, at, bt in BENCH10:
        out.append(
            '        <tr><td>%s</td>'
            '<td class="%s">%d/%d</td><td class="%s">%d/%d</td>'
            '<td class="num">%s → %s</td></tr>'
            % (MODEL_LABEL[m], "yes" if ak == n else "no", ak, n,
               "yes" if bk == n else "no", bk, n, at, bt))
    return "\n".join(out)


def bench9_rows_html():
    out = []
    for m, ak, bk, at, bt in BENCH9:
        out.append(
            '        <tr><td>Qwen 2.5 %s</td>'
            '<td class="%s">%d/6</td><td class="%s">%d/6</td>'
            '<td class="num">%s → %s</td></tr>'
            % (m, "yes" if ak == 6 else "no", ak,
               "yes" if bk == 6 else "no", bk,
               at if at is not None else "—",
               bt if bt is not None else "—"))
    return "\n".join(out)


def bench20_rows_html():
    out = []
    for lbl, s_, l_ in (("llama3.1:8b", HUB["v20_8b_s"],
                         HUB["v20_8b_l"]),
                        ("qwen2.5:7b-q4", HUB["v20_7b_s"],
                         HUB["v20_7b_l"]),
                        ("qwen2.5:1.5b", HUB["v20_15b_s"],
                         HUB["v20_15b_l"])):
        out.append('<tr><td>%s</td><td class="num">%d/20</td>'
                   '<td class="%s">%d/20</td></tr>'
                   % (lbl, s_, "yes" if l_ == 20 else "", l_))
    return "\n".join(out)


def bench23_rows_html():
    out = []
    for a, lbl in (("N", "nude"), ("S", "relay"), ("L", "lock")):
        w, n, u = HUB["v23_tbl"][a]
        out.append('<tr><td>%s</td><td class="%s">%d/%d</td>'
                   '<td class="num">$%s</td></tr>'
                   % (lbl, "yes" if w == n else "", w, n, u))
    return "\n".join(out)


def main():
    import main as app_mod  # after everything else, cheap sanity
    ver = app_mod.app.version
    fmt = dict(ver=ver, n_tools=len(TOOLS), n_recipes=len(RECIPES),
               n_free=N_FREE, n_cap=N_CAP, n_paid=N_PAID)
    fmt.update({k: v for k, v in HUB.items()
                if isinstance(v, (int, str))})
    r12 = next((r for r in BENCH12 if r[0] == "0.5b"), None)
    if r12:
        (nk, tk), (_cd, tc), (rl, tr) = r12[1]
        fmt["v12_zero"] = "%d/%d" % (nk, tk)
        fmt["v12_hero"] = "%d/%d" % (rl, tr)
    if BENCH10:
        m0, ak0, bk0, ntasks, _x, _y = BENCH10[0]
        fmt["v10_alone"] = "%d/%d" % (ak0, ntasks)
        fmt["v10_server"] = "%d/%d" % (bk0, ntasks)
    if BENCH9:
        m0, ak, bk, _x, _y = BENCH9[0]
        fmt["v9_alone"] = "%d/6" % ak
        fmt["v9_card"] = "%d/6" % bk
    for lang, cat in TR.items():
        cat = {k: (v.format(**fmt) if "{" in v else v)
               for k, v in cat.items()}
        cat["bundles_grid"] = catalog_grid(lang)
        cat["market_grid"] = market_html(lang, cat)
        cat["everyday_grid"] = everyday_html(lang, cat)
        cat["bench_rows"] = bench_rows_html()
        cat["bench9_rows"] = bench9_rows_html()
        cat["bench10_rows"] = bench10_rows_html()
        cat["bench12_rows"] = bench12_rows_html()
        cat["bench17_rows"] = bench17_rows_html()
        cat["bench19_rows"] = bench19_rows_html()
        cat["bench20_rows"] = bench20_rows_html()
        cat["bench23_rows"] = bench23_rows_html()
        (ROOT / "locales" / ("%s.json" % lang)).write_text(
            json.dumps(cat, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
    (ROOT / "static" / "landing.html").write_text(TEMPLATE,
                                                  encoding="utf-8")
    # parity: every {{key}} in the template exists in every locale
    keys = set(re.findall(r"\{\{([a-zA-Z0-9_.]+)\}\}", TEMPLATE))
    keys -= {"LANG"}
    keys -= {k for k in keys if k.startswith("cur.")}
    for lang in TR:
        have = set(json.loads((ROOT / "locales" / f"{lang}.json")
                              .read_text(encoding="utf-8")))
        missing = keys - have
        assert not missing, "%s missing %s" % (lang, sorted(missing))
    print("landing generated: %d keys x 3 languages, template %d bytes, "
          "bench rows: %d, v9 rows: %d"
          % (len(keys), len(TEMPLATE), len(BENCH), len(BENCH9)))


if __name__ == "__main__":
    main()
