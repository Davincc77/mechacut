#!/usr/bin/env python3
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

TR = {
 "en": {
  "meta.title": "Mechacut — same request, same bytes",
  "meta.desc": "Deterministic transforms for AI agents: 53 tools, three "
               "tiers, machine payments. No signup, no key, no storage.",
  "nav.tools": "Bundles", "nav.numbers": "Proof", "nav.vision": "Vision",
  "nav.api": "Contract",
  "pill": "v{ver} · {n_tools} transforms · {n_recipes} recipes",
  "hero1": "Meaning is learned.",
  "hero.why": "<strong>Why determinism?</strong> Because a right answer that changes on every run is not an answer — it is a dice roll. A machine that returns the same bytes for the same question makes agents auditable: every response carries its checksum, every error names the offending field, and what you test in the morning is what you ship at night.",
  "hero2": "Mechanics are known.",
  "hero3": "Competence is not learned. It is served.",
  "lede": "A suite of <strong>{n_tools} deterministic transforms</strong> "
          "for AI agents — {n_free} free forever, {n_cap} free under "
          "32 KB then pay-per-call, {n_paid} machine-payable — plus "
          "{n_recipes} one-call recipes, free. The model stops guessing "
          "what a checksum can prove.",
  "bundles.h2": "The catalogue",
  "bundles.creed": "A model computes. A server knows.",
  "cat.search": "search a tool or your problem…",
  "cat.hits": "~n~ of ~t~ tools",
  "panel.copy": "copy curl",
  "panel.copied": "copied",
  "panel.close": "close",
  "panel.say": "dis to your agent:",
  "panel.got": "the server answered:",
  "nav.menu": "menu",
  "bundles.intro": "Same request, same bytes — every response carries its "
                   "own sha256. Install one pack, or read the whole "
                   "manifest in one request and let <code>GET /route</code> pick.",
  "tiers.h2": "Three tiers, no accounts",
  "tiers.intro": "Agents do not read pricing pages — so the price is in "
                 "the protocol: a free route answers keyless, a capped "
                 "route answers free under 32 KB, anything else gets an "
                 "honest <code>402</code> with an x402 USDC-on-Base "
                 "challenge, settled by a facilitator. Between a server "
                 "and a robot, only prices and receipts exist.",
  "bench.h2": "Measured, not promised",
  "bench.creed": "The wall is FORM, not size — and we priced the door.",
  "bench9.intro": "One deliberately vague French sentence, six required "
                  "fields — money sorted to 2 decimals, percents, unique "
                  "dates, URL, email, total. Expectations hand-computed "
                  "before any run. The server builds the card "
                  "(/intent/card); the model relays one line and the "
                  "answer never passes through it.",
  "bench9.with": "with the intake card",
  "bench9.foot": "The 0.5B row reproduced on an independent second pass. "
                 "Three identical live calls returned one sha256. The "
                 "autonomous variant (the model picks the tool itself, no "
                 "card played by the harness) also scores 6/6. Seeds, "
                 "scripts, failures: bench/results_v9.jsonl.\n",
  "bench10.intro": "Eighteen tasks with ONE right answer each — GS1 check "
                   "digits, a SHA-256, chained discounts, a money column "
                   "that proves its own decimal comma. Two free LOCAL "
                   "models, no API spend: the harness asserts every route "
                   "it calls is free. Golds were computed from the "
                   "published specs before any model ran.",
  "bench10.with": "with one relay call",
  "bench10.foot": "Naked failures reproduce on an independent second "
                  "pass, 18/18 verdicts identical — at temp 0 a retry "
                  "never converges, it repeats. Raw runs: "
                  "bench/results_v10.jsonl, method: "
                  "bench/FINDINGS-V10.md.\n",
        "bench.v23.sum": "A 1.7B trained for agents solved "
                        "{v23_chain}/{v23_chain_cells} chains naked for "
                        "${v23_cost} — our wall was TRAINING, not size; "
                        "and the lock refused {v23_refused} right "
                        "answers over their names.",
        "bench.v23.intro": "The cross-family replication: the same 20 "
                           "seeded problems, the same arms as v20, one "
                           "model of another lineage (LFM3-1.7B, "
                           "tri-hybrid, post-trained for tool calls). "
                           "Nude {v23_n_all}/20, relayed {v23_s_all}/20, "
                           "locked {v23_l_all}/20. Nothing here refutes "
                           "v19: answering right once is not answering "
                           "with the same byte thirty days running.",
        "bench.v23.arm": "arm", "bench.v23.wins": "right /20",
        "bench.v23.usd": "cost",
        "bench.v23.foot": "Raw: bench/results_v23_lfm3.jsonl · method: "
                          "bench/FINDINGS-V23.md · $ at frozen "
                          "per-token prices.\n",
        "bench.v20.sum": "The wall is AIM: llama 8B went "
                         "{v20_8b_s}→{v20_8b_l}/20 with a target lock; "
                         "the 7B signed its first {v20_7b_l}/20.",
        "bench.v20.intro": "The promise of v17, measured: the answer "
                           "must name the quantity it returns. Nude, "
                           "the 8B computed right and answered beside "
                           "it — {v20_aside} of its misses carried "
                           "another quantity of the chain; the lock "
                           "converted {v20_aside_conv}. {v20_cells} "
                           "cells, and the naked arm replays v15 "
                           "exactly ({v20_replay}).",
        "bench.v20.model": "model", "bench.v20.naked": "naked",
        "bench.v20.locked": "with the lock",
        "bench.v20.foot": "Raw: bench/results_v20_target_lock.jsonl · "
                          "method: bench/FINDINGS-V20.md.\n",
        "bench.g1": "What they miss is executing, not thinking",
        "bench.g2": "The wall is a SHAPE — and shapes are a training target",
        "bench.g3": "Nobody says \"I'm not sure\" — paying more doesn't dodge the "
                        "shape",
        "bench.g4": "Reading is the ceiling no tool breaks",
        "bench.g5": "The real regime: thirty days of the same job",
        "bench.v11.sum": "Fifteen hostile tasks: the 7B goes {v11_7b_nu} to "
                        "{v11_7b_relay} relayed; the 8B {v11_8b_nu} to "
                        "{v11_8b_relay}.",
        "bench.v11.foot": "Raw: bench/results_v11.jsonl · method: "
                        "bench/FINDINGS-V11.md",
        "bench.f5.sum": "{f5_wins}/{f5_cells} chain attempts with the fiche — "
                        "criterion ≥19 PASSED; {f5_repairs} repaired by a named "
                        "refusal; the 7B alone {f5_7b}.",
        "bench.f5.foot": "Raw: bench/results_f5_accept.jsonl · method: "
                        "bench/FINDINGS-F5.md",
        "bench.v13.sum": "The negative result, published first: on real GSM8K the "
                        "relay card falls to {v13_relay_05b}/20 for the 0.5B — "
                        "asking the model for the decomposition still leaves it "
                        "doing the decomposition.",
        "bench.v13.foot": "Raw: bench/results_v13_gsm8k.jsonl · method: "
                        "bench/FINDINGS-V13.md",
        "bench.v14.sum": "Strict skill: {v14_breaks}/{v14_cells} protocol breaks — "
                        "the class the form can guarantee — while reading stays "
                        "free.",
        "bench.v14.foot": "Raw: bench/results_v14_skill.jsonl · method: "
                        "bench/FINDINGS-V14.md",
        "bench.v22.sum": "Three frontier models answer {v22_nu} naked — one at "
                        "{v22_best}, another at {v22_worst}. Through the frozen "
                        "fiche: {v22_fiche}. Paying more doesn't change the shape.",
        "bench.v22.foot": "Raw: bench/results_v22.jsonl · method: "
                        "bench/FINDINGS-V22.md",
        "bench.v22b.sum": "Five passes at agent temperature: {v22b_ok}/{v22b_cells} "
                        "right — the SAME program twice: {v22b_stable}/14. The "
                        "server: {v22b_shas} sha per problem.",
        "bench.v22b.foot": "Raw: bench/results_v22b.jsonl · method: "
                        "bench/FINDINGS-V22.md",
        "bench.v24.sum": "Thirty days of the same CSV with a model that CAN do "
                        "chains: {v24_sil}/{v24_days} days of empty answers after "
                        "8,192 reasoning tokens, {v24_ok} right, billed ${v24_usd}. "
                        "The machine: {v24_m_ok} at $0.00.",
        "bench.f7.sum": "EN/PT copies of the seven chains: {f7_wins}/{f7_cells} — "
                        "criterion ≥19 passed; {f7_rep} of them won by the named "
                        "refusal. PT copy at 4/7 vs FR's 0/7 on the 0.5B: the "
                        "reading ceiling belongs to model × language × form.",
        "bench.f7.foot": "Raw: bench/results_f7_accept.jsonl · frozen criterion: bench/FINDINGS-F7.md",
        "bench.v24.foot": "Raw: bench/results_v24_lfm3_30days.jsonl · the amendment "
                        "lives in git history (run24 amendé)",
        "bench.v19.sum": "{v19_wins}/{v19_days} attempts right for the models — "
                        "machine: {v19_m_ok}/{v19_m_days} days on one identical "
                        "hash; {v19_drift} different outputs from one model in 30 "
                        "days.",
        "bench.v19.intro": "The same dirty CSV cleaned 30 days in a "
                        "row. Six-rule spec, a gold file written BY "
                        "HAND before the harness, a retry arm that "
                        "only ever sees its own format — never the "
                        "answer. Temperature 0.7: the real regime of "
                        "agents, disclosed.",
        "bench.v19.arm": "arm", "bench.v19.right": "right days /30",
        "bench.v19.distinct": "distinct outputs",
        "bench.v19.foot": "Raw: bench/results_v19_csv_bill.jsonl · "
                        "method + dollars: bench/FINDINGS-V19.md · "
                        "replay: python bench/run19.py",
        "bench.v17.sum": "Retry ×5 on a systematic miss: "
                        "{v17_retry_wins}/{v17_retry_cells} chains "
                        "fixed — the same mistake, ×5 the price.",
        "bench.v17.intro": "Three arms, the same 20 fresh problems, "
                        "every token counted: answer naked, retry "
                        "five times, or hand the calculation to the "
                        "server. Cells: {v17_cells}.",
        "bench.v17.nu": "naked", "bench.v17.retry": "retry ×5",
        "bench.v17.relay": "server does it (ok · tokens/right)",
        "bench.v17.foot": "Raw: bench/results_v17_tokens.jsonl · "
                        "bench/FINDINGS-V17.md · replay: python "
                        "bench/run17.py",
        "bench.v16.sum": "{v16_wrong} wrong answers in {v16_runs} "
                        "runs — 'I'm not sure' said {v16_doubt} "
                        "times.",
        "bench.v16.intro": "Everyday word problems, freshly "
                        "generated, each model asked to mark its own "
                        "confidence honestly. They failed the same "
                        "way every time: confidently.",
        "bench.v16.foot": "Raw: bench/results_v16_calibration.jsonl · "
                        "bench/FINDINGS-V16.md · generator: "
                        "bench/gen16.py (seeded, double oracle).",
        "bench.v15.sum": "The wall is a SHAPE: {v15_alone_wins}/"
                        "{v15_cells} chain attempts solved naked or "
                        "retried — {v15_best_arm}/{v15_arm_cells} by "
                        "the best server arm.",
        "bench.v15.intro": "The full matrix: 5 transports × 4 free "
                        "models × 20 seeded problems (400 cells), "
                        "hypotheses committed BEFORE the first run, "
                        "failed predictions published first.",
        "bench.v15.foot": "Raw: bench/results_v15_matrix.jsonl · "
                        "bench/FINDINGS-V15.md · replay: python "
                        "bench/run15.py && python bench/score15.py",
        "bench.v12.sum": "{v12_zero} alone → {v12_hero} with one "
                        "relay call. The zero becomes the hero.",
        "bench.v10.sum": "One right answer each: {v10_alone} alone → "
                        "{v10_server} relayed — at $0, audited by "
                        "the harness itself.",
        "bench.v9.sum": "One vague sentence, six keys: {v9_alone} → "
                        "{v9_card} with the intake card.",
        "bench.v6.sum": "The first matrix — naked vs relay. Every "
                        "row, harness and failure: "
                        "bench/FINDINGS.md.",
  "bench12.intro": "Ten exact calculations (7834×9217, 0.1+0.2, chained "
                   "percentages…) × four FREE local models × three arms: "
                   "answering naked, writing Python, or relaying one "
                   "expression to math/calc. Scores shown; the code arm's "
                   "answers are float, the relay's are exact — same "
                   "table, different physics.",
  "bench12.code": "writes Python",
  "bench12.relay": "relays to Mechacut",
  "bench12.foot": "The 8B fails RELAY on protocol babble, not math — "
                  "which is why the intake card writes the line for it. "
                  "The 0.5B invented 89000098 naked and posts 9/10 "
                  "relayed at 0.2 s median. Raw: bench/results_v12.jsonl, "
                  "method: bench/FINDINGS-V12.md.\n",
  "bench.intro": "A frozen task (seed 20261120): dirty CSV + broken JSON + "
                 "URL list → one canonical YAML, expected answer pinned by "
                 "sha256. Same weak local model (Qwen 2.5, temperature 0), "
                 "one arm alone, one arm driving Mechacut. We publish the "
                 "failures too — the 0.5B fails both arms, and a "
                 "capability ceiling is a result.",
  "bench.model": "model", "bench.alone": "alone", "bench.with": "with "
                 "mechacut", "bench.tokens": "tokens consumed",
  "bench.foot": "The 7B goes from 0 % to 100 % in a single pipeline call. "
                "Every run, every token, is in bench/results.jsonl.",
    "nav.build": "Build",
      "nav.market": "Market",
      "market.h2": "They say it too",
      "market.creed": "The big houses converged on the same sentence — only the delivery differs.",
  "build.h2": "What you can build tonight",
  "build.intro": "You have a free small model on your machine. Here are "
                 "three things to make it do — the quoted lines are what "
                 "you say to your agent, the answers below are what the "
                 "server really returned. No account, no card, no prayer.",
  "build.r1.name": "The tax-ID gate",
  "build.r1.say": "\u201cIs my client\u2019s VAT number FR40303265045 "
                  "valid for the invoice?\u201d",
  "build.r1.got": "{{ \"valid\": true, \"algorithm\": \"EU VAT "
                  "check-digit rule for FR (published)\" }}",
  "build.r1.why": "Alone, a 0.5B model computes check digits — and gets "
                  "them wrong. Here the digits decide, so the invoice "
                  "does not die at the accountant\u2019s. Every country\u2019s "
                  "flavour lives on its own page: CNPJ for Brazil, SIREN "
                  "and TVA for France.",
  "build.r2.name": "The leak guard",
  "build.r2.say": "\u201cScan this log before I paste it into a "
                  "chatbot.\u201d",
  "build.r2.got": "2 findings \u2192 seed [SEED_PHRASE] and key "
                  "[OPENAI_KEY_1]",
  "build.r2.why": "The scan answers with positions, never the value; the "
                  "mask never returns the key. The secret came here for "
                  "safekeeping — it stays safe from us too.",
  "build.r3.name": "The incident relay",
  "build.r3.say": "\u201crel\u00e8ve les montants et dates de cette note "
                  "d\u2019incident\u201d \u2014 said in French, to a "
                  "0.5B.",
  "build.r3.got": "money [3200.00, 12450.75] \u00b7 6/6 keys in 320 "
                  "tokens (alone: 0/6)",
  "build.r3.why": "That is bench v9 verbatim: same task, same model, one "
                  "relay line. Every run is in bench/results_v9.jsonl — "
                  "replay it yourself.",
  "build.connect": "Or skip the story and wire it now: paste this ONE "
                 "line into ANY agent, even the smallest — it becomes "
                 "the full manual:",
    "everyday.h2": "For everyone",
      "everyday.open": "Expand the proofs — real server outputs, no mockups.",
  "everyday.intro": "No code, no jargon. Twenty-seven things a normal person "
                    "asks an agent on a Tuesday — every answer below is "
                    "the server's real output, not a mockup.",
  "everyday.e1.name": "Guest Wi-Fi, one scan",
  "everyday.e1.say": "\u201cTurn our Wi-Fi into a QR so guests stop "
                    "asking the password.\u201d",
  "everyday.e2.name": "The check, in words",
  "everyday.e2.say": "\u201cWrite $1,234.56 in words for the check — "
                    "the bank rejects typos.\u201d",
  "everyday.e3.name": "IBAN before the wire",
  "everyday.e3.say": "\u201cDid I copy this IBAN right? A bounced "
                    "wire costs $45.\u201d",
  "everyday.e4.name": "Recipe to printable page",
  "everyday.e4.say": "\u201cMake my recipe notes a clean page \u2014 "
                    "I want a PDF for the fridge.\u201d",
  "everyday.e5.name": "Counting the days",
  "everyday.e5.say": "\u201cHow many days until our trip?\u201d",
  "everyday.e6.name": "Sale math the register will not do",
  "everyday.e6.say": "\u201cMinus 30 %, then another 20 % \u2014 that "
                     "is 50 % off, right?\u201d It is 44 %.",
  "everyday.e7.name": "A third of the cake, nothing rounded in the dark",
  "everyday.e7.say": "\u201cThis 6-serving cake, I want it for 2 \u2014 "
                     "400 g flour, 5 eggs?\u201d 400 \u00d7 1/3 = 133 1/3 g "
                     "exact, 135 g to weigh. The eggs are stated, not "
                     "guessed.",
  "everyday.e8.name": "Every other Tuesday, on the dot",
  "everyday.e8.say": "\u201cBook club every other Tuesday at 7 \u2014 "
                     "the next four dates?\u201d Nov 3, 17, Dec 1, 15: "
                     "every two weeks means SKIPPING the weeks between \u2014 "
                     "and the skipped weeks are named, not guessed.",
  "everyday.e9.name": "One foot, three right answers",
  "everyday.e9.say": "\u201cEU 42 2/3 or 42.5 \u2014 which one am I?\u201d "
                     "Both charts round: the millimetre is exact, the "
                     "half-size and third-size candidates are all "
                     "printed, and the drift between systems is a "
                     "stated number. Never one confident size.",
  "everyday.e10.name": "Delayed flight — who owes me what",
  "everyday.e10.say": "\u201cMy flight landed 3 h 20 late \u2014 what "
                      "am I actually owed?\u201d The FLIGHT DATE picks "
                      "the rule: before 2027-10-23 the old EC261 + "
                      "case-law; on or after it, the new codified "
                      "\u2018EXCEEDING three hours\u2019 table. Same "
                      "facts either side of that line can pay "
                      "differently. \u20ac or \u00a3, with the claim "
                      "deadline as a real date.",
  "everyday.e11.name": "Will my bag pass the gate",
  "everyday.e11.say": "\u201cMy bag is 40\u00d718\u00d712, flight in "
                      "November 2027 \u2014 free under the seat? The "
                      "FLIGHT DATE decides: the 2027 law caps the "
                      "under-seat item at 40\u00d730\u00d715, nothing "
                      "before it. Rotation counts \u2014 faces sorted, "
                      "never the order you typed.",
  "everyday.e12.name": "The two tariffs, one honest number",
  "everyday.e12.say": "\u201cPlan A is cheaper per kWh, plan B is "
                      "cheaper per month \u2014 when does A really "
                      "win?\u201d The crossover is (fixed gap \u00d7 "
                      "days) \u00f7 (rate gap) \u2014 and the exact "
                      "fraction, not the web's rounded intermediate: "
                      "4,623\u2153 kWh where the article says \u201cabout "
                      "4,623\u201d. \u201cNever\u201d is also an answer, "
                      "named, when one plan wins on both parts.",
  "everyday.e13.name": "What a point is really worth",
  "everyday.e13.say": "\u201c29,000 points for a $438 flight minus "
                      "$5.60 taxes — how much is a point, really?\u201d "
                      "cpp = (cash − taxes) ÷ points × 100: the "
                      "printed 1.49 hides the exact 1081/725 = "
                      "1.491034…, subtracted BEFORE dividing. And the "
                      "floor that says take-it-or-pay-cash is yours, "
                      "never a stale table.",
  "everyday.e14.name": "The billed weight, both chains printed",
  "everyday.e14.say": "\u201cTwo carriers bill 6 kg and 5 kg for my "
                      "40×30×25 box — who is wrong?\u201d Neither: "
                      "30 000 cm³ ÷ 5 000 = 6 exactly, ÷ 6 000 = 5 "
                      "exactly — two divisors, one honest chain, each "
                      "step named. And carrier tables ROT (USPS moved "
                      "166 → 139 in July 2026), so the divisor stays "
                      "YOUR argument — never our memory.",
  "everyday.e15.name": "The BOGO sign says 50 % — the bill does not",
  "everyday.e15.say": "\u201cBuy one, get the second 50 % off — a "
                      "$60 and a $40 hoodie, am I at −50, −25?\u201d "
                      "Neither: the % hits the CHEAPER item (published "
                      "retail rule), so the pair is 80 of 100 = −20 %. "
                      "Equal prices would be −25 %, BOGO free −50 %, "
                      "and a −30 coupon on top gives −47.5, never 55 — "
                      "percentages multiply.",
  "everyday.e16.name": "The 500 g pack became 400 g — at the same price",
  "everyday.e16.say": "\u201c\u221220 % on the package?\u201d Not the "
                      "same number as the shelf: losing 1/5 of the "
                      "product costs +1/4 per unit (20 % vs 25 % — two "
                      "denominators, 500 and 400). \u201c2 for $7\u201d "
                      "of 15 oz jars vs one 24 oz at $3.99? The eye "
                      "says promo, the exact fraction says the single "
                      "jar wins — the bundle pays 40.3509 % more per "
                      "ounce. And \u201c1 lb 4 oz\u201d IS 20 oz: the "
                      "coupon was right, the cashier wasn\u2019t.",
  "everyday.e17.name": "Thanksgiving Thursday: what time does the turkey leave the freezer",
  "everyday.e17.say": "Eight calculators of Nov 2026 cite the same "
                      "USDA table yet disagree: one puts the 16 lb bird "
                      "in the fridge by Sat 21 10:00, the other says the "
                      "long end means the 20th? This tool decides by a "
                      "named rule: put in by = oven minus the long end "
                      "of the published bracket; not before = minus the "
                      "1-to-2-day hold. Hours are arguments, never the "
                      "wall clock. And done is 165\u00b0F at the "
                      "thermometer \u2014 the real judge.",
  "everyday.e18.name": "The turkey is leftovers now \u2014 which day "
                       "does the fridge window close",
  "everyday.e18.say": "The press prints the rule in stone: \u201ceat "
                      "it by Monday Nov 30\u201d (NBC, 19-Nov) next to "
                      "\u201cno more than three days, 72 hours "
                      "optimal\u201d (ky3, same day) \u2014 expired on "
                      "Dec 1 and already disagreeing. The two FSIS "
                      "pages themselves fight about the freezer (2-6 "
                      "months vs 3-4): this tool renders the UNION of "
                      "both published windows with both anchors, the "
                      "2-hour gate STRICT from cooked_at (exactly 2 h "
                      "passes, 2 h 01 discards), the 4th day named "
                      "LAST_DAY \u2014 and quality labelled quality: "
                      "safe indefinitely at 0\u00b0F. Dates are "
                      "arguments; 165\u00b0F is the judge, gravy a "
                      "rolling boil.",
  "everyday.e19.name": "Three dishes want the oven — the countdown, "
                       "every conflict named",
  "everyday.e19.say": "Eight 2026 timelines publish the same dinner "
                      "with rests of 20 to 60 minutes, 325 or 350 °F "
                      "— and nobody counts the preheat that "
                      "eats 45 minutes. Scheduled BACKWARDS from your "
                      "serve_at (an argument, never the wall clock): "
                      "one oven, one dish, rests outside; a dish "
                      "entering the instant the previous leaves at "
                      "another setting is a named conflict; a bare "
                      "180 without a unit is refused; rest beyond 2 h "
                      "hits the FSIS danger zone — same rule as "
                      "the leftovers window.",
  "everyday.e20.name": "Christmas ship-by dates \u2014 \u22652 sources "
                     "per row, the outlier NAMED",
  "everyday.e20.say": "Six holiday tables published Nov 13\u201321, "
                      "2026 disagree: one syndicate prints FedEx "
                      "Saver, 2Day and Overnight a full day later \u2014 "
                      "silently, because its target is Dec 25, not "
                      "Dec 24. This table keeps only rows where \u22652 "
                      "sources agree, names the dissenter WITH its "
                      "reason, derives every weekday from the "
                      "calendar the press itself cites, refuses UPS "
                      "Ground (zone-dependent \u2014 no single date "
                      "exists) and never extrapolates a year. as_of "
                      "is an argument: \u00ab how many days are left "
                      "\u00bb is arithmetic, not a clock. The window "
                      "dies Dec 23.",
  "everyday.e21.name": "Holiday RETURN deadlines \u2014 \u22652 sources, "
                     "provenance class on every row",
  "everyday.e21.say": "The shared January-31 headline is a lie of "
                      "omission: Target's purchase window closes Dec "
                      "24, Best Buy's member rule splits at Dec 4, "
                      "and parcelmonitor publishes last year's dates "
                      "shifted by one as \u0027likely pattern\u0027 while "
                      "Seller Central had published the 2026 text "
                      "verbatim. This table keeps only rows with two "
                      "concordant sources, carries provenance "
                      "(published|press), names the Day-1 counting "
                      "convention, refuses single-source retailers "
                      "WITH the candidate fact, and never lets "
                      "\u0027whichever is later\u0027 quietly become a "
                      "guess: delivery date is an argument.",
  "everyday.e22.name": "Is that crossed-out price LEGAL \u2014 the "
                     "Omnibus 30-day rule, audited from your own "
                     "history",
  "everyday.e22.say": "EU law names the reference: the LOWEST price "
                      "the shop applied in the previous 30 days "
                      "(Directive 2019/2161 art. 6a) \u2014 and a "
                      "weekend sale lowers that floor even after the "
                      "price went back up (CJEU C-330/23). 100 "
                      "\u2192 80 \u2192 100 \u2192 70 is a 12.5% cut, "
                      "not 30%. The Commission's March 2026 sweep: "
                      "30% of 314 traders got the reference wrong; "
                      "Spain fined seven shops up to 350,000 EUR. "
                      "Paste the shop's own price history and the "
                      "cut's date \u2014 the machine returns the "
                      "legal reference, the true percentage and a "
                      "named verdict. It never fetches a price.",
  "everyday.e23.name": "Price DROPPED after you paid — who owes the "
                       "difference, by when, in which money",
  "everyday.e23.say": "You bought at 100, the shop now shows 80. No "
                      "law forces a refund — but the shops' own "
                      "published guarantees do, and those windows "
                      "are DATES: Target Dec 24, Best Buy Jan 15, "
                      "Costco 30 days, Fnac-Darty the campaign "
                      "itself (gift card, not cash), Amazon nothing "
                      "at all. Paste purchase + drop dates and both "
                      "prices — the machine returns the verdict, the "
                      "claim deadline, the amount and the refund "
                      "mode, with the source class on every row. It "
                      "never fetches a price.",
  "everyday.e24.name": "The gift broke AFTER the return window — "
                       "what does the LAW still owe you, to the day",
  "everyday.e24.say": "Christmas gift, delivered Dec 25, dies Jan "
                      "16: the shop's goodwill window closed Jan 15 "
                      "and the press stops answering here. The "
                      "statute doesn't. France: the conformity "
                      "guarantee runs 2 years from DELIVERY, the "
                      "hidden-defect clock 2 years from DISCOVERY "
                      "under a 20-year cap — three different "
                      "anchors under the word 'garantie'. UK: "
                      "three clocks again, 30 days to reject, six "
                      "months of reversed burden (a PROOF rule, "
                      "not a deadline), six years to sue — five in "
                      "Scotland. Every answer is dated from your "
                      "one input; where the official page "
                      "contradicts itself (refurbished goods, "
                      "24 vs 12 months), BOTH dates travel named. "
                      "US and AU are refused by name: no federal "
                      "countable window; 'reasonable time' is not "
                      "a date.",
    "everyday.e25.name": "Can I shred this folder? — the UK drawer "
                       "hides FOUR clocks",
  "everyday.e25.say": "\u201cSix years\u201d is ONE phrase for four "
                      "different dates: VAT invoices count from "
                      "the date ON THE DOCUMENT (even a paper "
                      "describing a future event \u2014 the HMRC "
                      "manual says so in those words), a limited "
                      "company counts from the END of the financial "
                      "year it relates to, Companies Act s.388 "
                      "counts the same records THREE years if "
                      "private, SIX if a plc \u2014 from the date "
                      "MADE \u2014 and Self Assessment counts five "
                      "years from a 31 January deadline that is on "
                      "no document at all. The official examples "
                      "are replayed: a 2022-23 return sent by 31 "
                      "January 2024 keeps the paper until 31 "
                      "January 2029, shred from 1 February. The "
                      "four \u201cor longer if\u201d cases (late "
                      "return, open compliance check) come back "
                      "BLOCKED with their published reason \u2014 "
                      "no invented date ever. The CH15400 minima "
                      "table (replayed the day after it was "
                      "updated, 23 November 2026) travels with the "
                      "arbitrage: when two rules touch one paper, "
                      "the LONGER governs.",
  "everyday.e26.name": "The gift voucher that 'expired' may be legally "
                       "alive — Ireland counts from the BUY",
  "everyday.e26.say": "Ireland, Consumer Protection (Gift Vouchers) "
                      "Act 2019, text replayed: a printed expiry "
                      "shorter than FIVE YEARS from the purchase day "
                      "is not voided — it is DEEMED REPLACED by five "
                      "years, and the legal date OVERRIDES the paper "
                      "one (66B(1)(b)+(c)). That is the JD Sports "
                      "shape: one-year vouchers, ~\u20ac250,000 "
                      "refunded this July after the CCPC's 20 "
                      "November call-in. A card received at Christmas "
                      "starts no clock that day — the anchor is the "
                      "contract date and the RECIPIENT holds every "
                      "right (66B(10)). A leftover of \u20ac1 or "
                      "more is a refund owed \u2014 and this tool "
                      "ships the \u20ac1.00 boundary conflict by "
                      "name: the Act says 'or more', the CCPC FAQ "
                      "says 'more than'. France, replayed too: NO "
                      "statutory minimum exists \u2014 the printed "
                      "date is contractual, and the '30 years' rumour "
                      "belongs to real-property prescription, refused "
                      "here by name.",
  "everyday.e27.name": "French sales dates are a LAW, not a "
                       "memory — 2027 opens Wednesday January "
                       "6, and the law itself moved 2021",
  "everyday.e27.say": "The arr\u00eate du 27 mai 2019, replayed: "
                      "winter opens the second Wednesday of "
                      "January at 8 h, ADVANCED to the first "
                      "when the second falls after the 12th \u2014 "
                      "2027 opens January 6, and every site "
                      "printing \u00ab9 f\u00e9vrier\u00bb dropped the "
                      "clause. Summer carries its own: last "
                      "Wednesday of June, penultimate when the "
                      "last falls after the 28th \u2014 2027 opens "
                      "June 23. Four weeks, the start day "
                      "counted. And the seven annual "
                      "derogations no press table copies: "
                      "\u00e9t\u00e9 2020 fixed to July 15; winter 2021 "
                      "fixed to January 20 then CARRIED TO SIX "
                      "WEEKS; Moselle opening June 26 ALONE; "
                      "Guadeloupe moved to Thursday October 7, "
                      "2021; the heatwaves carried 2023 and "
                      "2026 to five weeks. The four eastern "
                      "departments open \u00abpremier jour ouvr\u00e9\u00bb "
                      "\u2014 an undefined word: for 2027 both "
                      "windows travel, Monday 4 first, Saturday "
                      "2 named, never averaged. Belgium, "
                      "Luxembourg, Quebec: refused by name. "
                      "Years before 2020: refused with art. 4. "
                      "as_of is an argument \u2014 \u00ab43 days left\u00bb "
                      "is arithmetic, not a clock.",
"nav.kit": "Kit",
  "kit.h2": "The suite on your disk",
  "kit.creed": "The protocol is not the transport \u2014 it is the birth certificate of the tool.",
  "kit.intro": "The free transforms are not only an API. They are a suite: an agent can install them on its own machine, call them locally, and \u2014 the part no marketplace does \u2014 build new tools on the same gates. curl becomes kit call; a repeated task becomes a proposed contract; a proposal becomes a published tool only if its golds were drawn before its code.",
  "kit.c1.sum": "Install \u2014 the base suite on the machine",
  "kit.c1.foot": "Verified sha, no daemon, no auto-update, no network inside the engine. Stateless is the contract: the human decides when the kit moves.",
  "kit.c2.sum": "Call \u2014 consult before acting",
  "kit.c2.foot": "The skill asks the directory first. Same canon, same refusals, same golds as the datacenter \u2014 what is verified here is verified there, byte for byte.",
  "kit.c3.sum": "Build \u2014 the second time, write the tool",
  "kit.c3.foot": "Golds drawn BEFORE the code, AST-gate, pin-gate. Status: proposed, attested, network-verified \u2014 the kit grows locally, the proof grows back to the network. A lesson is a proposal; the bench locks it.",
  "kit.howto.p1": "Install the skill: <code>curl https://mechacut.studio/SKILL-MINI.md -o SKILL.md</code> \u2014 drop the file into your agent (CLAUDE.md, AGENTS.md, skills/). ~1,000 tokens, sized for small models.",
  "kit.howto.p2": "Make it consult first: before acting, the agent describes the problem in one sentence to /route/resolve \u2014 the directory returns the tool that already exists, or says none does.",
  "kit.howto.p3": "Call: stateless POSTs, keyless on free; the response carries its sha256, the refusal carries field + expected + example. Everything on this page works right now: one line installs the skill file, the directory answers, the free calls need no key.",
  "kit.plain.sum": "Not a developer? No problem \u2014 we translate.",
  "kit.plain.p1": "Open your usual AI assistant (Claude, ChatGPT, Grok, Copilot\u2026).",
  "kit.plain.p2": "Send it this message: \u0022Read https://mechacut.studio/SKILL-MINI.md and follow it for my calculations.\u0022 Nothing to install, nothing to pay, no account.",
  "kit.plain.p3": "Then ask your real task: \u002230% then 20% discount \u2014 what is that really?\u0022, \u0022how many days overdue is this invoice?\u0022 The numbers no longer come from its head \u2014 they come from the suite, and they are the same for everyone.",
  "kit.plain.p4": "Did you ask for something the suite cannot do? Propose it \u0022 in plain words on the same page \u2014 every proposal is public, its verdict too: shipped, waiting, or refused with the reason named, at /proposals.",
  "kit.dev.sum": "For developers \u2014 three lines, no account",
  "kit.propose": "Propose a tool: POST /api/v1/agent/propose — a contract, never code; duplicate named, evidence shown, eligibility returned as a commit-ready blob. Nothing stored server-side. Protocol skill: /SKILL-KIT.md",
  "bench.d82.sum": "Tool-call traces, judged: the same agent motion was re-emitted identically 0 out of 14 times (V22b) and a retry multiplied the bill \u00d74 without converging (V17) \u2014 loop/doom-check now says DOOM, CYCLIC or STORM on canonical bytes, thresholds named.",
  "bench.d82.foot": "Identity on canonical (tool, args): key order never hides a loop. Two identical calls are not a loop \u2014 the threshold is stated, never guessed. All signals reported, the verdict is the most severe. Sources: bench/FINDINGS-V17.md \u00b7 run22b.",
  "bench.e76.sum": "The bench judge became a route: eval/compare returns OK or WRONG with divergences named \u2014 2.5 versus \"2.50\" is never a disagreement, floats are never an argument.",
  "bench.e76.foot": "Rule born from the V2 judge incident (it copied its own expectation): same quantity is never a divergence; a different quantity is named by pointer, kind, expected, got. Exact Decimal, never float.",
  "bench.a79.sum": "Policy as closed grammar: check/allowlist returns ALLOW, DENY or AMBIGUOUS \u2014 the most specific rule wins, ties go to the human, silence never authorizes.",
  "bench.a79.foot": "A regex-shaped action is refused, not evaluated: a gate that interprets is a backdoor. Exact Decimal amounts, ISO currency table, default deny true. Same law as the directory's R3, another domain.",
"x402.h2": "Machine payments",
  "x402.p1": "The paying path is four bytes of protocol: the server "
             "answers <code>402</code> with requirements; the agent signs "
             "an EIP-3009 USDC transfer; a facilitator verifies and "
             "settles; the response replays proof in "
             "<code>X-PAYMENT-RESPONSE</code>. The server holds no keys.",
  "x402.p2": "Replayed payments are refused. Errors on paid routes stay "
             "free. The ledger of every refusal is public: "
             "<a href=\"/misses.json\">/misses.json</a>.",
  "x402.bankr": "Same endpoints, second home: four paid transforms are also deployed on <a href=\"https://bankr.bot\">Bankr</a> x402 Cloud \u2014 identical code paths, identical sha256, paid through the Bankr rails: <a href=\"https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/chart_from_data\">chart</a> &middot; <a href=\"https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/reshape_json\">reshape</a> &middot; <a href=\"https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/validate_json\">validate</a> &middot; <a href=\"https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/csv_join\">csv-join</a>. The other 68 live only here, free tier included.",
  "vision.h2": "Why determinism, why now",
  "vision.p1": "A large language model is a machine that approximates. "
               "Ask it what <code>sha256(\"abc\")</code> is and it will "
               "answer confidently, fluently, and wrong. Ask it to "
               "re-clean the same CSV every day and it will bill you in "
               "tokens to re-derive what a function returns in "
               "milliseconds — with the same bytes every time.",
  "vision.p2": "The Apollo guidance computer had 4 KB of RAM. It landed "
               "humans because the math was never asked to improvise: "
               "constants were computed once, on the ground, in cold "
               "blood, then frozen into core rope memory.",
  "vision.quote": "Determinism was coded the first time to send us to the "
                  "moon. Determinism will send AI to work.",
  "vision.p3": "Mechacut is that frozen math for agents: closed "
               "vocabularies, contracts that refuse what is outside the "
               "table, errors that name the expected shape — the error is "
               "the repair prompt. Meaning stays with the model. "
               "Mechanics move here.",
  "contract.h2": "The contract",
  "contract.li1": "Same request → same bytes, sha256 on every response",
  "contract.li2": "No signup, no API key, no rate wall below 30 req/min",
  "contract.li3": "No storage: the only state is a 1-minute window, a "
                  "60-minute ledger and a payment-nonce replay set",
  "contract.li4": "Closed vocabularies — everything outside the table is "
                  "refused, named, pointed at its expected shape",
  "contract.li5": "Errors that repair: field, message, expected, always",
  "contract.li6": "x402 machine payments: USDC on Base, facilitator "
                  "verified, zero human in the loop",
  "agents.line": "Speak agent: MCP tools, GET /agent/manifest ("
                 "the whole suite in one request), GET /route?q=…, "
                 "POST /api/v1/pipeline.",
  "agents.hint": "install one pack",
  "footer.family": "Mechacut is part of the C.V. family — see moovicut.",
 },
 "fr": {
  "meta.title": "Mechacut — même requête, mêmes octets",
  "meta.desc": "Transformations déterministes pour agents IA : 53 outils, "
               "trois paliers, paiements machine. Sans inscription, sans "
               "clé, sans stockage.",
  "nav.tools": "Bundles", "nav.numbers": "Preuves", "nav.vision":
  "Vision", "nav.api": "Contrat",
  "pill": "v{ver} · {n_tools} transformations · {n_recipes} recettes",
  "hero1": "Le sens s'apprend.",
  "hero.why": "<strong>Pourquoi le déterminisme ?</strong> Parce qu'une réponse juste qui change à chaque exécution n'est pas une réponse — c'est un dé. Une machine qui rend les mêmes octets à la même question rend les agents auditables : chaque réponse porte son empreinte, chaque erreur nomme le champ fautif, et ce que vous testez le matin est ce que vous vendez le soir.",
  "hero2": "La mécanique se sait.",
  "hero3": "La compétence ne s'apprend pas. Elle se sert.",
  "lede": "Une suite de <strong>{n_tools} transformations "
          "déterministes</strong> pour agents IA — {n_free} gratuites à "
          "jamais, {n_cap} gratuites sous 32 Ko puis payables à l\u2019appel, "
          "{n_paid} payables par machine — plus {n_recipes} recettes "
          "prêtes à l\u2019appel unique, gratuites. Le modèle arrête de "
          "deviner ce qu\u2019une somme de contrôle peut prouver.",
  "bundles.h2": "Le catalogue",
  "bundles.creed": "Un modèle calcule. Un serveur sait.",
  "cat.search": "chercher un outil ou votre problème…",
  "cat.hits": "~n~ outils sur ~t~",
  "panel.copy": "copier curl",
  "panel.copied": "copié",
  "panel.close": "fermer",
  "panel.say": "dis à ton agent :",
  "panel.got": "le serveur a répondu :",
  "nav.menu": "menu",
  "bundles.intro": "Même requête, mêmes octets — chaque réponse porte son "
                   "sha256. Installez un pack, ou lisez le manifeste entier "
                   "en une requête et laissez <code>GET /route</code> choisir.",
  "tiers.h2": "Trois paliers, zéro compte",
  "tiers.intro": "Les agents ne lisent pas les pages de tarifs — donc le "
                 "prix est dans le protocole : une route gratuite répond "
                 "sans clé, une route plafonnée répond gratuitement sous "
                 "32 Ko, toute autre reçoit un <code>402</code> honnête "
                 "avec défi x402 USDC sur Base, réglé par un "
                 "facilitateur. Entre un serveur et un robot, il n'existe "
                 "que des prix et des reçus.",
  "bench.h2": "Mesuré, pas promis",
  "bench.creed": "Le mur, c'est la FORME, pas la taille — et nous avons chiffré la porte.",
  "bench9.intro": "Une phrase française volontairement floue, six champs "
                  "requis — montants triés à 2 décimales, pourcentages, "
                  "dates uniques, URL, email, total. Attentes calculées à "
                  "la main avant toute exécution. Le serveur construit la "
                  "fiche (/intent/card) ; le modèle relais une ligne et la "
                  "réponse ne le traverse jamais.",
  "bench9.with": "avec la fiche d'intention",
  "bench9.foot": "La ligne 0.5B reproduite lors d'un second passage "
                 "indépendant. Trois appels live identiques → un seul "
                 "sha256. La variante autonome (le modèle choisit l'outil "
                 "lui-même) marque aussi 6/6. Graines, scripts, échecs : "
                 "bench/results_v9.jsonl.\n",
  "bench10.intro": "Dix-huit tâches à réponse UNIQUE — chiffres de "
                   "contrôle GS1, un SHA-256, remises en cascade, une "
                   "colonne de montants qui prouve elle-même sa virgule. "
                   "Deux modèles gratuits et LOCAUX, zéro dépense d'API : "
                   "le harnais vérifie que chaque route appelée est "
                   "gratuite. Les réponses justes ont été calculées à "
                   "partir des specs publiées AVANT tout appel modèle.",
  "bench10.with": "avec un seul appel-relais",
  "bench10.foot": "Les échecs nus se reproduisent à l'identique lors "
                  "d'un second passage indépendant : 18/18 verdicts "
                  "inchangés — à temp 0, recommencer ne converge pas, "
                  "ça répète. Exécutions brutes : "
                  "bench/results_v10.jsonl, méthode : "
                  "bench/FINDINGS-V10.md.\n",
        "bench.v23.sum": "Un 1,7 B entraîné pour les agents a résolu "
                        "{v23_chain}/{v23_chain_cells} chaînes à nu pour "
                        "${v23_cost} — notre mur était l'ENTRAÎNEMENT, "
                        "pas la taille ; et le verrou a refusé "
                        "{v23_refused} bonnes réponses pour leurs noms.",
        "bench.v23.intro": "La réplication hors-famille : les mêmes 20 "
                           "problèmes seedés, les mêmes bras que v20, un "
                           "modèle d'une autre lignée (LFM3-1.7B, "
                           "tri-hybride, post-entraîné au tool calling). "
                           "Nu {v23_n_all}/20, relayé {v23_s_all}/20, "
                           "verrouillé {v23_l_all}/20. Rien ici ne "
                           "réfute v19 : répondre juste une fois n'est "
                           "pas répondre au même octet trente jours de "
                           "suite.",
        "bench.v23.arm": "bras", "bench.v23.wins": "justes /20",
        "bench.v23.usd": "coût",
        "bench.v23.foot": "Brut : bench/results_v23_lfm3.jsonl · "
                          "méthode : bench/FINDINGS-V23.md · $ aux "
                          "tarifs par token gelés.\n",
        "bench.v20.sum": "Le mur est une CIBLE : le llama 8B passe de "
                         "{v20_8b_s} à {v20_8b_l}/20 avec le verrou de "
                         "cible ; le 7B signe son premier "
                         "{v20_7b_l}/20.",
        "bench.v20.intro": "La promesse de v17 mesurée : la réponse "
                           "doit nommer la quantité qu'elle rend. Nu, "
                           "le 8B calculait juste et répondait à côté — "
                           "{v20_aside} de ses fautes portaient une "
                           "autre quantité de la chaîne, le verrou en a "
                           "converti {v20_aside_conv}. {v20_cells} "
                           "cellules, et le bras nu rejoue v15 à "
                           "l'identique ({v20_replay}).",
        "bench.v20.model": "modèle", "bench.v20.naked": "nu",
        "bench.v20.locked": "avec verrou",
        "bench.v20.foot": "Brut : bench/results_v20_target_lock.jsonl · "
                          "méthode : bench/FINDINGS-V20.md.\n",
        "bench.g1": "Ce qu'ils ratent n'est pas de réfléchir — c'est d'exécuter",
        "bench.g2": "Le mur est une FORME — et les formes sont un objectif "
                        "d'entraînement",
        "bench.g3": "Personne ne dit « je ne suis pas sûr » — payer plus "
                        "n'esquive pas la forme",
        "bench.g4": "La lecture est le plafond qu'aucun outil ne franchit",
        "bench.g5": "Le régime réel : trente jours du même job",
        "bench.v11.sum": "Quinze tâches hostiles : le 7B passe de {v11_7b_nu} à "
                        "{v11_7b_relay} en relais ; le 8B de {v11_8b_nu} à "
                        "{v11_8b_relay}.",
        "bench.v11.foot": "Brut : bench/results_v11.jsonl · méthode : "
                        "bench/FINDINGS-V11.md",
        "bench.f5.sum": "{f5_wins}/{f5_cells} tentatives en chaîne avec la fiche — "
                        "critère ≥19 PASSÉ ; {f5_repairs} réparées par un refus "
                        "nommé ; le 7B seul {f5_7b}.",
        "bench.f5.foot": "Brut : bench/results_f5_accept.jsonl · méthode : "
                        "bench/FINDINGS-F5.md",
        "bench.v13.sum": "Le résultat négatif, publié en premier : sur GSM8K réel, "
                        "la fiche-relais s'effondre à {v13_relay_05b}/20 pour le "
                        "0.5B — demander la décomposition au modèle, c'est encore "
                        "la lui laisser faire.",
        "bench.v13.foot": "Brut : bench/results_v13_gsm8k.jsonl · méthode : "
                        "bench/FINDINGS-V13.md",
        "bench.v14.sum": "Skill stricte : {v14_breaks}/{v14_cells} ruptures de "
                        "protocole — la seule classe que la forme garantit — la "
                        "lecture, elle, reste libre.",
        "bench.v14.foot": "Brut : bench/results_v14_skill.jsonl · méthode : "
                        "bench/FINDINGS-V14.md",
        "bench.v22.sum": "Trois modèles frontière, {v22_nu} justes nus — l'un "
                        "{v22_best}, l'autre {v22_worst}. Par la fiche gelée : "
                        "{v22_fiche}. Payer plus ne change pas la forme.",
        "bench.v22.foot": "Brut : bench/results_v22.jsonl · méthode : "
                        "bench/FINDINGS-V22.md",
        "bench.v22b.sum": "Cinq passes au régime des agents : {v22b_ok}/{v22b_cells} "
                        "justes — le MÊME programme deux fois : {v22b_stable}/14. "
                        "Le serveur : {v22b_shas} sha par problème.",
        "bench.v22b.foot": "Brut : bench/results_v22b.jsonl · méthode : "
                        "bench/FINDINGS-V22.md",
        "bench.v24.sum": "Trente jours sur le même CSV avec un modèle QUI SAIT les "
                        "chaînes : {v24_sil}/{v24_days} jours de réponse vide après "
                        "8 192 tokens de raisonnement, {v24_ok} justes, facturés "
                        "${v24_usd}. La machine : {v24_m_ok} à 0,00 $.",
        "bench.f7.sum": "Les sept chaînes recopiées EN/PT : {f7_wins}/{f7_cells} — "
                        "critère ≥19 PASSÉ ; {f7_rep} gagnées par le refus nommé. "
                        "Le 0.5b copie 4/7 en PT là où le FR le mettait à 0/7 : le "
                        "plafond de lecture est du modèle × langue × forme.",
        "bench.f7.foot": "Brut : bench/results_f7_accept.jsonl · critère gelé : bench/FINDINGS-F7.md",
        "bench.v24.foot": "Brut : bench/results_v24_lfm3_30days.jsonl · l'amendement "
                        "est dans l'historique git (run24 amendé)",
        "bench.v19.sum": "{v19_wins}/{v19_days} tentatives justes pour les modèles — "
                        "machine : {v19_m_ok}/{v19_m_days} jours sur un même octet "
                        "; {v19_drift} sorties différentes pour un seul modèle en "
                        "30 jours.",
        "bench.v19.intro": "Le même CSV sale nettoyé 30 jours de suite. "
                        "Spéc à six règles, gold ÉCRIT À LA MAIN avant "
                        "le banc, un bras retry qui ne voit que sa "
                        "propre forme — jamais la réponse. Température "
                        "0,7 : le régime réel des agents, publié.",
        "bench.v19.arm": "bras", "bench.v19.right": "jours justes /30",
        "bench.v19.distinct": "sorties distinctes",
        "bench.v19.foot": "Brut : bench/results_v19_csv_bill.jsonl · "
                        "méthode + dollars : bench/FINDINGS-V19.md · "
                        "rejeu : python bench/run19.py",
        "bench.v17.sum": "Retry ×5 sur une erreur systématique : "
                        "{v17_retry_wins}/{v17_retry_cells} chaînes "
                        "réparées — la même faute, 5× le prix.",
        "bench.v17.intro": "Trois bras, les mêmes 20 problèmes neufs, "
                        "chaque token compté : répondre nu, recommencer "
                        "cinq fois, ou donner le calcul au serveur. "
                        "Cellules : {v17_cells}.",
        "bench.v17.nu": "nu", "bench.v17.retry": "retry ×5",
        "bench.v17.relay": "serveur (ok · tokens/juste)",
        "bench.v17.foot": "Brut : bench/results_v17_tokens.jsonl · "
                        "bench/FINDINGS-V17.md · rejeu : python "
                        "bench/run17.py",
        "bench.v16.sum": "{v16_wrong} fautes en {v16_runs} runs — "
                        "« je ne suis pas sûr » dit {v16_doubt} fois.",
        "bench.v16.intro": "Des problèmes du quotidien générés à la "
                        "volée, chaque modèle prié de marquer "
                        "honnêtement sa confiance. Ils ont échoué "
                        "toujours de la même façon : avec assurance.",
        "bench.v16.foot": "Brut : bench/results_v16_calibration.jsonl "
                        "· bench/FINDINGS-V16.md · générateur : "
                        "bench/gen16.py (seedé, double oracle).",
        "bench.v15.sum": "Le mur a une FORME : {v15_alone_wins}/"
                        "{v15_cells} tentatives en chaîne nues ou en "
                        "retry — {v15_best_arm}/{v15_arm_cells} avec "
                        "le meilleur bras serveur.",
        "bench.v15.intro": "La matrice complète : 5 transports × 4 "
                        "modèles gratuits × 20 problèmes seedés "
                        "(400 cellules), hypothèses commitées AVANT la "
                        "première cellule, prédictions ratées publiées "
                        "en premier.",
        "bench.v15.foot": "Brut : bench/results_v15_matrix.jsonl · "
                        "bench/FINDINGS-V15.md · rejeu : python "
                        "bench/run15.py && python bench/score15.py",
        "bench.v12.sum": "{v12_zero} seul → {v12_hero} avec un seul "
                        "relais. Le zéro devient héros.",
        "bench.v10.sum": "Une seule bonne réponse chacun : {v10_alone} "
                        "seul → {v10_server} relayé — à 0 $, audité "
                        "par le banc lui-même.",
        "bench.v9.sum": "Une phrase vague, six clés : {v9_alone} → "
                        "{v9_card} avec la carte d'intention.",
        "bench.v6.sum": "La première matrice — nu vs relais. Chaque "
                        "ligne, chaque harnais, chaque échec : "
                        "bench/FINDINGS.md.",
  "bench12.intro": "Dix calculs exacts (7834×9217, 0.1+0.2, pourcentages "
                   "en chaîne…) × quatre modèles locaux GRATUITS × trois "
                   "bras : répondre nu, écrire du Python, ou relayer une "
                   "expression vers math/calc. Même tableau, deux "
                   "physiques : le bras code rend du flottant, le relais "
                   "rend de l'exact.",
  "bench12.code": "écrit du Python",
  "bench12.relay": "relais Mechacut",
  "bench12.foot": "Le 8B échoue au RELAIS sur le babil protocole, pas "
                  "sur les maths — c'est pourquoi la fiche d'intention "
                  "écrit la ligne à sa place. Nu, le 0.5B inventait "
                  "89000098 ; relayé, il sort 9/10 en 0,2 s médian. "
                  "Brut : bench/results_v12.jsonl, méthode : "
                  "bench/FINDINGS-V12.md.\n",
  "bench.intro": "Une tâche gelée (seed 20261120) : CSV sale + JSON cassé "
                 "+ liste d'URLs → un YAML canonique, réponse attendue "
                 "épinglée par sha256. Même modèle local faible (Qwen "
                 "2.5, température 0), un bras seul, un bras avec "
                 "Mechacut. On publie aussi les échecs — le 0.5B échoue "
                 "aux deux bras, et un plafond de capacité est un "
                 "résultat.",
  "bench.model": "modèle", "bench.alone": "seul", "bench.with": "avec "
                 "mechacut", "bench.tokens": "tokens consommés",
  "bench.foot": "Le 7B passe de 0 % à 100 % en un seul appel pipeline. "
                "Chaque exécution, chaque token, est dans "
                "bench/results.jsonl.",
    "nav.build": "Construire",
      "nav.market": "Eux aussi",
      "market.h2": "Ils le disent aussi",
      "market.creed": "Les grandes maisons ont convergé sur la même phrase — seule la façon de la livrer diffère.",
  "build.h2": "Ce que tu peux construire ce soir",
  "build.intro": "Tu as un petit mod\u00e8le gratuit sur ta machine. "
                 "Voici trois choses \u00e0 lui faire faire — les phrases "
                 "cit\u00e9es sont celles que tu dis \u00e0 l\u2019agent, "
                 "les r\u00e9ponses sont celles que le serveur a vraiment "
                 "rendues. Pas de compte, pas de carte, pas de pri\u00e8re.",
  "build.r1.name": "Le contr\u00f4le de TVA (France)",
  "build.r1.say": "\u00ab Le num\u00e9ro de TVA de mon client, "
                  "FR40303265045, est-il valide pour la facture ? \u00bb",
  "build.r1.got": "{{ \"valid\": true, \"algorithm\": \"EU VAT "
                  "check-digit rule for FR (published)\" }}",
  "build.r1.why": "Seul, un 0.5B \u00ab calcule \u00bb la cl\u00e9 de "
                  "contr\u00f4le \u2014 et se trompe. Ici ce sont les "
                  "chiffres qui d\u00e9cident : la facture ne meurt pas "
                  "chez le comptable.",
"build.r2.name": "Le garde-fuite",
  "build.r2.say": "\u00ab Scanne ce log avant que je le colle dans un "
                  "chatbot. \u00bb",
  "build.r2.got": "2 findings \u2192 graine [SEED_PHRASE] et cl\u00e9 "
                  "[OPENAI_KEY_1]",
  "build.r2.why": "Le scan r\u00e9pond des positions, jamais la valeur ; "
                  "le masque ne renvoie jamais la cl\u00e9. Le secret est "
                  "venu ici — et il reste prot\u00e9g\u00e9 m\u00eame de "
                  "nous.",
  "build.r3.name": "Le relai d\u2019incident",
  "build.r3.say": "\u00ab rel\u00e8ve les montants et dates de cette note "
                  "d\u2019incident \u00bb \u2014 dit en fran\u00e7ais,\u00e0 un 0.5B.",
  "build.r3.got": "money [3200.00, 12450.75] \u00b7 6/6 en 320 tokens "
                  "(seul : 0/6)",
  "build.r3.why": "C\u2019est le bench v9, \u00e0 l\u2019identique : "
                  "m\u00eame t\u00e2che, m\u00eame mod\u00e8le, une "
                  "ligne de relai. Toutes les ex\u00e9cutions sont dans "
                  "bench/results_v9.jsonl — rejoue-les.",
  "build.connect": "Ou branche-le tout de suite : colle CETTE ligne "
                 "dans n'importe quel agent, m\u00eame le plus petit "
                 "\u2014 elle devient le manuel complet :",
    "everyday.h2": "Pour tout le monde",
      "everyday.open": "Dérouler les preuves — sorties réelles du serveur, pas des maquettes.",
  "everyday.intro": "Pas de code, pas de jargon. Vingt-sept choses qu'un humain "
                    "demande à son agent un mardi "
                    "\u2014 chaque preuve ci-dessous est ouverte.",
  "everyday.e1.name": "Wi-Fi invit\u00e9s, un scan",
  "everyday.e1.say": "\u00ab Transforme le Wi-Fi en QR pour que les "
                     "invit\u00e9s arr\u00eatent de demander le mot de "
                     "passe. \u00bb",
  "everyday.e2.name": "Le ch\u00e8que, en lettres",
  "everyday.e2.say": "\u00ab \u00c9cris 1 234,56 \u20ac en toutes "
                     "lettres pour le ch\u00e8que \u2014 la banque "
                     "refuse les approximations. \u00bb",
  "everyday.e3.name": "IBAN avant le virement",
  "everyday.e3.say": "\u00ab J'ai bien recopi\u00e9 cet IBAN ? 60 \u20ac "
                     "de frais si le virement rebondit. \u00bb",
  "everyday.e4.name": "Recette en page imprimable",
  "everyday.e4.say": "\u00ab Mets mes notes de recette en page propre "
                     "\u2014 je veux un PDF pour le frigo. \u00bb",
  "everyday.e5.name": "Compter les jours",
  "everyday.e5.say": "\u00ab Combien de jours avant les "
                     "vacances ? \u00bb",
  "everyday.e6.name": "Le compte que la caisse ne fera pas",
  "everyday.e6.say": "\u00ab -30 % puis -20 %, \u00e7a fait -50 %, "
                     "non ? \u00bb En fait -44 %.",
  "everyday.e7.name": "Un tiers du g\u00e2teau, sans arrondi cach\u00e9",
  "everyday.e7.say": "\u00ab Mon g\u00e2teau pour 6, je le veux pour 2 "
                     "\u2014 400 g de farine, 5 \u0153ufs ? \u00bb 400 "
                     "\u00d7 1/3 = 133 1/3 g exacts, 135 g \u00e0 la "
                     "balance. Les \u0153ufs sont dits, pas devin\u00e9s.",
  "everyday.e8.name": "Un mardi sur deux, à l'heure",
  "everyday.e8.say": "« Club de lecture un mardi sur deux à 19 h — "
                     "les quatre prochaines dates ? » 3 et 17 nov., "
                     "1er et 15 déc. : tous les quinze jours veut dire "
                     "SAUTER les semaines du milieu, et le moteur les "
                     "nomme.",
  "everyday.e9.name": "Un pied, trois bonnes réponses",
  "everyday.e9.say": "EU 42⅔ ou 42,5 ? Les deux tableaux arrondissent : le millimètre est exact, les candidats demi et tiers sont écrits, la dérive entre systèmes est un nombre dit — jamais un seul numéro confiant.",
  "everyday.e10.name": "Vol retardé — qui me doit quoi",
  "everyday.e10.say": "Vol en retard de 3 h 20 — la DATE DU VOL choisit la règle : avant le 23 oct. 2027 l'ancien EC261 + jurisprudence, après la table codifiée « PLUS DE trois heures ». Mêmes faits de part et d'autre, réponses différentes. € ou £, délai de recours en vraie date.",
  "everyday.e11.name": "Mon sac passera-t-il la porte",
  "everyday.e11.say": "Mon sac 40×18×12, vol en novembre 2027 — la DATE DU VOL décide : la règle 2027 plafonne le sous-siège à 40×30×15, avant rien n'est fixé. Rotation compte — faces triées, jamais l'ordre tapé.",
  "everyday.e12.name": "Deux tarifs, un seul chiffre honnête",
  "everyday.e12.say": "La bascule = (écart de fixe × jours) ÷ (écart de prix), en fraction EXACTE : 4 623⅓ kWh là où l'article écrit « environ 4 623 ». « Jamais » est aussi une réponse, nommée, quand un plan gagne sur les deux parties.",
  "everyday.e13.name": "Ce que vaut vraiment un point",
  "everyday.e13.say": "29 000 points pour un vol à 438 € moins 5,60 € de taxes : le 1,49 affiché cache l'exact 1081/725 = 1,491034… La soustraction passe AVANT la division ; c'est VOTRE plancher qui décide.",
  "everyday.e14.name": "Le poids vraiment factur\u00e9, les deux "
                       "cha\u00eenes imprim\u00e9es",
  "everyday.e14.say": "Deux transporteurs facturent 6 kg et 5 kg pour la même boîte 40×30×25 — personne n'a tort : 30 000 cm³ ÷ 5 000 = 6 pile, ÷ 6 000 = 5 pile. Les tables transporteurs POURRISSENT (USPS 166→139 en juillet 2026) : le diviseur reste VOTRE argument, jamais notre mémoire.",
  "everyday.e15.name": "L'affiche dit 50 % — la note, jamais",
  "everyday.e15.say": "Deux sweats à 60 € et 40 €, « le deuxième à −50 % » : ni 50 ni 25 — la remise porte sur le MOINCHER (règle de détail publiée), la paire rend 80 sur 100 = −20 %. À prix égaux −25 %, BOGO gratuit −50 %, coupon −30 % par dessus −47,5 %, jamais 55.",
  "everyday.e16.name": "Le 500 g est devenu 400 g — au même prix",
  "everyday.e16.say": "Perdre 1/5 du produit (500→400 g, même étiquette), c'est +1/4 au kilo : 20 % contre 25 %, deux dénominateurs. Le « 2 pour 7 $ » de pots de 15 oz perd 40,3509 % à l'once contre le pot de 24 oz — la fraction tranche, pas l'œil.",
  "everyday.e17.name": "Thanksgiving : à quelle heure la dinde sort du congélateur",
  "everyday.e17.say": "Huit calculateurs de nov. 2026 citent la même table USDA et se contredisent sur la dinde de 16 lb. Règle nommée : au plus tard = four moins le bout long du créneau ; pas avant = moins la garde de 1 à 2 jours. Heures = arguments, jamais l'horloge ; cuit est 165 °F à la sonde.",
  "everyday.e18.name": "La dinde en restes — quel jour ferme la fenêtre du frigo",
  "everyday.e18.say": "« À manger avant lundi 30 novembre » (NBC, 19 nov) côtoie « trois jours, 72 h optimales » (ky3) pour la même dinde ; FSIS se contredit au congélateur (2-6 vs 3-4 mois). L'outil rend l'UNION des fenêtres, deux ancres citées, 2 h STRICTES depuis cooked_at (2 h pile passe, 2 h 01 jette), 4ᵉ jour nommé LAST_DAY, qualité nommée qualité.",
  "everyday.e19.name": "Trois plats veulent le four — le compte à rebours, conflits nommés",
  "everyday.e19.say": "Huit timelines 2026 publient le même dîner avec des repos de 20 à 60 minutes, 325 ou 350 °F — et personne ne compte le préchauffage qui mange 45 minutes. Calcul à REBOURS depuis l'heure de service (argument, jamais l'horloge) : un four, un plat à la fois, repos dehors ; entrée à la minute de la sortie à une autre consigne = conflit nommé ; « 180 » sans unité = refusé ; repos au-delà de 2 h = zone FSIS.",
  "everyday.e20.name": "Dates limites d'envoi de Noël — ≥2 sources, divergente nommée",
  "everyday.e20.say": "Six tableaux du 13 au 21 nov. 2026 se contredisent : un syndicat imprime FedEx Saver, 2Day, Overnight un jour plus tard — sa cible est le 25, pas le 24. Ligne gardée si ≥2 sources concordent ; divergente nommée ; UPS Ground refusé, pas de date unique. Fenêtre close le 23 déc.",
  "everyday.e21.name": "Retours des fêtes — ≥2 sources, provenance par ligne",
  "everyday.e21.say": "Le titre « jusqu'au 31 janvier » est un mensonge par omission : chez Target la fenêtre d'achat ferme le 24 déc., chez Best Buy la règle membres se coupe au 4 déc., et un blog a republié les dates de l'an passé décalées pendant que Seller Central publiait le texte 2026 mot pour mot. Ligne gardée si deux sources concordent ; provenance par ligne ; mono-sources refusées avec le fait candidat. « Au plus tard des deux » exige la date de livraison.",
  "everyday.e22.name": "Le prix barré est-il LÉGAL ? règle Omnibus des 30 jours",
  "everyday.e22.say": "La référence légale : le prix le PLUS BAS des 30 jours précédents (directive 2019/2161 art. 6a) — une promo du week-end l'ABAISSE même si le prix est remonté (CJEU C-330/23). 100 → 80 → 100 → 70 = 12,5 %, pas 30 %. Sweep Commission mars 2026 : 30 % des 314 commerces se trompent ; l'Espagne a amendé jusqu'à 350 000 €. Historique en entrée, référence et vrai pourcentage en sortie.",
  "everyday.e23.name": "Le prix a BAISSÉ après l'achat — qui doit la différence",
  "everyday.e23.say": "Acheté 100, affiché 80. Aucune loi n'oblige au remboursement — les garanties publiées oui, et leurs fenêtres sont des DATES : Target 24 déc, Best Buy 15 janv, Costco 30 jours, Fnac-Darty la campagne elle-même (carte cadeau, pas espèces), Amazon rien. Verdict, date limite, montant, monnaie — classe de source par ligne. Zéro fetch.",
  "everyday.e24.name": "Le cadeau mort APRÈS le retour — ce que la LOI doit, jour pour jour",
  "everyday.e24.say": "Cadeau livré le 25 décembre, en panne le 16 janvier : vitrine fermée le 15, presse muette ; la loi, si. France : conformité 2 ans depuis la DÉLIVRANCE, vices cachés 2 ans depuis la DÉCOUVERTE, plafond 20 ans depuis la vente — trois ancres sous « garantie ». UK : 30 jours pour rejeter, six mois de preuve INVERSÉE (règle de preuve, pas échéance), six ans — cinq en Écosse. Page officielle contradictoire (reconditionné 24 ou 12 mois) : les DEUX dates voyagent. US/AU refusés par nom.",
    "everyday.e25.name": "Puis-je jeter ce dossier ? — QUATRE horloges dans le carton",
  "everyday.e25.say": "« Six ans » est UNE phrase pour quatre dates : la TVA depuis la date ÉCRITE SUR LE DOCUMENT (événement futur compris, HMRC l'écrit), la limited company depuis la CLÔTURE, s.388 TROIS ans si private, SIX si plc — depuis la CRÉATION —, le Self Assessment cinq ans depuis le 31 janvier, deadline sans papier. Exemple officiel : 2022-23 avant le 31 janvier 2024 → gardé jusqu'au 31 janvier 2029, détruit dès le 1er février. Les « ou plus si » reviennent BLOCKED. CH15400 : la PLUS LONGUE gouverne.",
  "everyday.e26.name": "Carte cadeau « périmée » ? Peut-être vivante — l'ACHAT ancre",
  "everyday.e26.say": "Irlande, Gift Vouchers Act 2019 rejoué : une date imprimée plus courte que cinq ans depuis l'achat est REMPLACÉE d'office par cinq ans — le légal COUVRE le papier (66B(1)(b)+(c)). Forme JD Sports : bons d'un an, ≈250 000 € rendus en juillet. L'horloge part de l'achat ; le porteur tient tous les droits (66B(10)). Solde d'1 € ou plus : dû. France : AUCUNE durée légale ; le mythe des « 30 ans » est immobilier (art. 2227), refusé.",
  "everyday.e27.name": "Les soldes sont UNE LOI, pas une mémoire — 2027 : 6 janvier",
  "everyday.e27.say": "Arrêté du 27 mai 2019 rejoué : hiver le 2e mercredi de janvier à 8 h, AVANCÉ au 1er quand le 2e tombe après le 12 — 2027 : 6 janvier ; qui imprime « 9 février » a raté la clause. Été : dernier mercredi de juin, avant-dernier si le dernier tombe après le 28 — 2027 : 23 juin. Quatre semaines, début compté. Sept dérogations annuelles au verbatim : été 2020 au 15 juillet ; hiver 2021 au 20 janvier puis SIX SEMAINES ; Moselle seule au 26 juin 2021 ; Guadeloupe au jeudi 7 octobre 2021 ; canicule 2023 et 2026 à cinq semaines. « Premier jour ouvré » non défini : 2027 porte lundi 4 premier et samedi 2 nommé. Avant 2020 et hors France, refusé par nom.",
"nav.kit": "Kit",
  "kit.h2": "La suite sur votre disque",
  "kit.creed": "Le protocole n'est pas le transport \u2014 c'est l'acte de naissance de l'outil.",
  "kit.intro": "Les transformations libres ne sont pas seulement une API. Elles sont une suite : un agent peut l'installer sur sa propre machine, l'appeler en local et \u2014 c'est la partie qu'aucun marché ne fait \u2014 construire de nouveaux outils sur les mêmes portes. curl devient kit call ; une tâche répétée devient une proposition de contrat ; la proposition ne devient un outil publié que si ses golds furent tracés avant son code.",
  "kit.c1.sum": "Installer \u2014 la suite basique sur la machine",
  "kit.c1.foot": "Sha vérifié, pas de daemon, pas d'auto-update, pas de réseau dans le moteur. Le sans-état est le contrat : l'humain décide quand le kit bouge.",
  "kit.c2.sum": "Appeler \u2014 consulter avant d'agir",
  "kit.c2.foot": "La skill interroge l'annuaire d'abord. Même canon, mêmes refus, mêmes golds qu'au datacenter \u2014 ce qui est vérifié ici l'est là-bas, octet pour octet.",
  "kit.c3.sum": "Construire \u2014 dès la deuxième fois, écrire l'outil",
  "kit.c3.foot": "Golds tracés AVANT le code, AST-gate, pin-gate. Statuts : proposé, attesté, réseau-vérifié \u2014 le kit grandit localement, la preuve repousse au réseau. Une leçon est une proposition ; le banc la verrouille.",
  "kit.howto.p1": "Installer la skill : <code>curl https://mechacut.studio/SKILL-MINI.md -o SKILL.md</code> \u2014 déposer le fichier chez l'agent (CLAUDE.md, AGENTS.md, skills/). ~1 000 jetons, calibré pour les petits modèles.",
  "kit.howto.p2": "Le faire consulter d'abord : avant d'agir, l'agent décrit son problème en une phrase à /route/resolve \u2014 l'annuaire rend l'outil qui existe déjà, ou dit qu'aucun n'existe.",
  "kit.howto.p3": "Appeler : POST sans état, sans clé sur le libre ; la réponse porte son sha256, le refus porte champ + attendu + exemple. Tout ce qui tient sur cette page fonctionne déjà : une ligne installe le fichier de skill, l’annuaire répond, les appels libres vont sans clé.",
  "kit.plain.sum": "Vous n'êtes pas développeurs ? Pas grave, on traduit.",
  "kit.plain.p1": "Ouvrez votre assistant IA habituel (Claude, ChatGPT, Grok, Copilot\u2026).",
  "kit.plain.p2": "Envoyez-lui ce message : \u0022 Lis https://mechacut.studio/SKILL-MINI.md et suis-le pour tous mes calculs.\u0022 Rien à installer, rien à payer, pas de compte.",
  "kit.plain.p3": "Demandez ensuite votre véritable tâche : \u0022 30 % puis 20 % de remise, ça fait combien réellement ?\u0022, \u0022 cette facture est en retard de combien de jours ?\u0022 Les chiffres ne sortent plus de sa tête \u2014 ils sortent de la suite, et ils sont les mêmes pour tout le monde.",
  "kit.plain.p4": "Vous avez demandé quelque chose que la suite ne sait pas faire ? Proposez-le en mots simples \u2014 chaque proposition est publique, et son verdict aussi : livré, en banc, ou refusé avec la raison nommée, sur /proposals.",
  "kit.dev.sum": "Pour les développeurs \u2014 trois lignes, sans compte",
  "kit.propose": "Proposer un outil : POST /api/v1/agent/propose — un contrat, jamais du code ; doublon nommé, preuve affichée, éligibilité rendue en blob prêt au commit. Rien n'est stocké côté serveur. Skill du protocole : /SKILL-KIT.md",
  "bench.d82.sum": "Traces d'appels d'outils jugées : le même geste d'agent n'a jamais été réémis à l'identique (0 sur 14, V22b) et un retry a multiplié la facture ×4 sans converger (V17) \u2014 loop/doom-check dit désormais DOOM, CYCLIC ou STORM sur des bytes canoniques, seuils nommés.",
  "bench.d82.foot": "Identité en (outil, args) canoniques : l'ordre des clés ne cache jamais une boucle. Deux appels identiques ne sont pas une boucle \u2014 le seuil est dit, jamais deviné. Tous les signaux rapportés, verdict le plus grave. Sources : bench/FINDINGS-V17.md · run22b.",
  "bench.e76.sum": "Le juge du banc est devenu route : eval/compare rend OK ou WRONG avec les divergences nommées \u2014 2,5 contre \u00222.50\u0022 n'est jamais un désaccord, les flottants ne sont jamais un argument.",
  "bench.e76.foot": "Règle née de l'incident du juge V2 (il recopiait son attente) : même quantité n'est jamais une divergence ; quantité différente est nommée par pointer, kind, expected, got. Decimal exact, jamais float.",
  "bench.a79.sum": "La politique en grammaire fermée : check/allowlist rend ALLOW, DENY ou AMBIGUOUS \u2014 la règle la plus spécifique gagne, l'égalité remonte à l'humain, le silence n'autorise jamais.",
  "bench.a79.foot": "Une action en forme de regex est refusée, pas évaluée : un gate qui interprète est une porte dérobée. Montants Decimal exacts, table devises ISO, default deny vrai. Même loi que R3 de l'annuaire, autre domaine.",
"x402.h2": "Paiements machine",
  "x402.p1": "Le chemin payant tient en quatre octets de protocole : le "
             "serveur répond <code>402</code> avec ses exigences ; "
             "l'agent signe un transfert USDC EIP-3009 ; un facilitateur "
             "vérifie et règle ; la réponse rejoue la preuve dans "
             "<code>X-PAYMENT-RESPONSE</code>. Le serveur ne détient "
             "aucune clé.",
  "x402.p2": "Les paiements rejoués sont refusés. Les erreurs sur routes "
             "payantes restent gratuites. Le registre de chaque refus est "
             "public : <a href=\"/misses.json\">/misses.json</a>.",
  "x402.bankr": "M\u00eames endpoints, second domicile : quatre transforms payants sont aussi d\u00e9ploy\u00e9s sur le x402 Cloud de <a href=\"https://bankr.bot\">Bankr</a> \u2014 m\u00eames chemins de code, m\u00eames sha256, pay\u00e9s via les rails Bankr : <a href=\"https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/chart_from_data\">chart</a> &middot; <a href=\"https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/reshape_json\">reshape</a> &middot; <a href=\"https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/validate_json\">validate</a> &middot; <a href=\"https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/csv_join\">csv-join</a>. Les 68 autres vivent ici seulement, palier gratuit compris.",
  "vision.h2": "Pourquoi le déterminisme, pourquoi maintenant",
  "vision.p1": "Un grand modèle de langage est une machine qui "
               "approxime. Demandez-lui <code>sha256(\"abc\")</code> : il "
               "répondra avec assurance, élégance, et faux. Demandez-lui "
               "de nettoyer le même CSV tous les jours : il vous facturera "
               "des tokens pour redériver ce qu'une fonction rend en "
               "millisecondes — avec les mêmes octets, chaque fois.",
  "vision.p2": "L'ordinateur de guidage Apollo avait 4 Ko de RAM. Il a "
               "posé des humains sur la Lune parce que les maths n'ont "
               "jamais eu à improviser : chaque constante a été calculée "
               "une fois, au sol, à froid, puis gelée dans la mémoire à "
               "cordes tressées.",
  "vision.quote": "Le déterminisme a été codé la première fois pour nous "
                  "envoyer sur la Lune. Le déterminisme enverra l'IA au "
                  "travail.",
  "vision.p3": "Mechacut est cette math gelée pour les agents : vocabu-"
               "laires fermés, contrats qui refusent ce qui sort de la "
               "table, erreurs qui nomment la forme attendue — l'erreur "
               "est le prompt qui répare. Le sens reste avec le modèle. "
               "La mécanique déménage ici.",
  "contract.h2": "Le contrat",
  "contract.li1": "Même requête → mêmes octets, sha256 sur chaque réponse",
  "contract.li2": "Sans inscription, sans clé, sans mur de débit sous "
                  "30 req/min",
  "contract.li3": "Zéro stockage : le seul état est une fenêtre d'une "
                  "minute, un registre de 60 minutes et un jeu de nonces "
                  "de paiement",
  "contract.li4": "Vocabulaires fermés — tout ce qui sort de la table est "
                  "refusé, nommé, renvoyé à sa forme attendue",
  "contract.li5": "Des erreurs qui réparent : champ, message, attendu, "
                  "toujours",
  "contract.li6": "Paiements machine x402 : USDC sur Base, vérifiés par "
                  "facilitateur, zéro humain dans la boucle",
  "agents.line": "Parlez agent : outils MCP, GET /agent/manifest ("
                 "toute la suite en une requête), GET /route?q=…, "
                 "POST /api/v1/pipeline.",
  "agents.hint": "installez un pack",
  "footer.family": "Mechacut fait partie de la famille C.V. — voir moovicut.",
 },
 "pt": {
  "meta.title": "Mechacut — mesma requisição, mesmos bytes",
  "meta.desc": "Transformações determinísticas para agentes de IA: 53 "
               "ferramentas, três níveis, pagamentos entre máquinas. Sem "
               "cadastro, sem chave, sem armazenamento.",
  "nav.tools": "Bundles", "nav.numbers": "Provas", "nav.vision": "Visão",
  "nav.api": "Contrato",
  "pill": "v{ver} · {n_tools} transformações · {n_recipes} receitas",
  "hero1": "Significado se aprende.",
  "hero.why": "<strong>Por que determinismo?</strong> Porque uma resposta certa que muda a cada execução não é uma resposta — é um dado lançado. Uma máquina que devolve os mesmos bytes para a mesma pergunta torna agentes auditáveis: cada resposta traz sua impressão, cada erro nomeia o campo culpado, e o que você testa de manhã é o que você entrega à noite.",
  "hero2": "Mecânica se conhece.",
  "hero3": "Competência não se aprende. Serve-se.",
  "lede": "Uma suíte de <strong>{n_tools} transformações "
          "determinísticas</strong> para agentes de IA — {n_free} grátis "
          "para sempre, {n_cap} grátis abaixo de 32 KB e depois pagas "
          "por chamada, {n_paid} pagáveis por máquina — mais "
          "{n_recipes} receitas de chamada única, grátis. O modelo para "
          "de adivinhar o que um checksum pode provar.",
  "bundles.h2": "O catálogo",
  "bundles.creed": "Um modelo calcula. Um servidor sabe.",
  "cat.search": "busque uma ferramenta ou seu problema…",
  "cat.hits": "~n~ ferramentas de ~t~",
  "panel.copy": "copiar curl",
  "panel.copied": "copiado",
  "panel.close": "fechar",
  "panel.say": "diga ao seu agente:",
  "panel.got": "o servidor respondeu:",
  "nav.menu": "menu",
  "bundles.intro": "Mesma requisição, mesmos bytes — cada resposta carrega "
                   "seu sha256. Instale um pack, ou leia o manifesto inteiro "
                   "em uma requisição e deixe <code>GET /route</code> escolher.",
  "tiers.h2": "Três níveis, zero contas",
  "tiers.intro": "Agentes não leem páginas de preço — então o preço está "
                 "no protocolo: uma rota grátis responde sem chave, uma "
                 "rota com teto responde grátis abaixo de 32 KB, qualquer "
                 "outra recebe um <code>402</code> honesto com desafio "
                 "x402 USDC na Base, liquidado por um facilitador. Entre "
                 "um servidor e um robô, só existem preços e recibos.",
  "bench.h2": "Medido, não prometido",
  "bench.creed": "O muro é a FORMA, não o tamanho — e nós precificamos a porta.",
  "bench9.intro": "Uma frase vaga (em francês), seis campos obrigatórios — "
                  "valores com 2 decimais, percentuais, datas únicas, URL, "
                  "e-mail, total. Expectativas calculadas à mão antes de "
                  "rodar. O servidor monta o cartão (/intent/card); o "
                  "modelo repassa uma linha e a resposta nunca passa por "
                  "ele.",
  "bench9.with": "com o cartão de intenção",
  "bench9.foot": "A linha 0.5B reproduziu em uma segunda rodada "
                 "independente. Três chamadas iguais → um único sha256. A "
                 "variante autônoma (o modelo escolhe a ferramenta) também "
                 "marca 6/6. Sementes, scripts, falhas: "
                 "bench/results_v9.jsonl.\n",
  "bench10.intro": "Dezoito tarefas com UMA resposta certa cada — "
                   "dígitos de controle GS1, um SHA-256, descontos em "
                   "cascata, uma coluna de valores que prova o próprio "
                   "ponto decimal. Dois modelos gratuitos e LOCAIS, "
                   "zero gasto de API: o harness verifica que cada "
                   "rota chamada é gratuita. Os gabaritos saíram das "
                   "specs publicadas ANTES de qualquer modelo rodar.",
  "bench10.with": "com uma chamada-relé",
  "bench10.foot": "As falhas nuas se reproduzem num segundo passe "
                  "independente: 18/18 vereditos idênticos — a temp 0, "
                  "repetir não converge, repete. Execuções brutas: "
                  "bench/results_v10.jsonl, método: "
                  "bench/FINDINGS-V10.md.\n",
        "bench.v23.sum": "Um 1,7B treinado para agentes resolveu "
                        "{v23_chain}/{v23_chain_cells} correntes nu por "
                        "${v23_cost} — nosso muro era o TREINAMENTO, "
                        "não o tamanho; e o cadeado recusou "
                        "{v23_refused} respostas certas pelos nomes.",
        "bench.v23.intro": "A replicação fora da família: os mesmos 20 "
                           "problemas com semente, os mesmos braços do "
                           "v20, um modelo de outra linhagem (LFM3-1.7B, "
                           "tri-híbrido, pós-treinado para tool "
                           "calling). Nu {v23_n_all}/20, retransmitido "
                           "{v23_s_all}/20, com cadeado "
                           "{v23_l_all}/20. Nada aqui refuta o v19: "
                           "acertar uma vez não é responder no mesmo "
                           "byte trinta dias seguidos.",
        "bench.v23.arm": "braço", "bench.v23.wins": "acertos /20",
        "bench.v23.usd": "custo",
        "bench.v23.foot": "Bruto: bench/results_v23_lfm3.jsonl · "
                          "método: bench/FINDINGS-V23.md · $ a preços "
                          "por token congelados.\n",
        "bench.v20.sum": "O muro é um ALVO: o llama 8B vai de "
                         "{v20_8b_s} para {v20_8b_l}/20 com o cadeado "
                         "de alvo; o 7B fecha seu primeiro "
                         "{v20_7b_l}/20.",
        "bench.v20.intro": "A promessa de v17 medida: a resposta deve "
                           "nomear a quantidade que devolve. Nu, o 8B "
                           "calculava certo e respondia ao lado — "
                           "{v20_aside} de seus erros traziam outra "
                           "quantidade da cadeia, e o cadeado converteu "
                           "{v20_aside_conv}. {v20_cells} células, e o "
                           "braço nu reencena o v15 exatamente "
                           "({v20_replay}).",
        "bench.v20.model": "modelo", "bench.v20.naked": "nu",
        "bench.v20.locked": "com cadeado",
        "bench.v20.foot": "Bruto: bench/results_v20_target_lock.jsonl · "
                          "método: bench/FINDINGS-V20.md.\n",
        "bench.g1": "O que eles erram não é pensar — é executar",
        "bench.g2": "O muro é uma FORMA — e formas são alvo de treino",
        "bench.g3": "Ninguém diz «não tenho certeza» — pagar mais não desvia da "
                        "forma",
        "bench.g4": "A leitura é o teto que nenhuma ferramenta fura",
        "bench.g5": "O regime real: trinta dias do mesmo trabalho",
        "bench.v11.sum": "Quinze tarefas hostis: o 7B vai de {v11_7b_nu} a "
                        "{v11_7b_relay} com relé; o 8B de {v11_8b_nu} a "
                        "{v11_8b_relay}.",
        "bench.v11.foot": "Bruto: bench/results_v11.jsonl · método: "
                        "bench/FINDINGS-V11.md",
        "bench.f5.sum": "{f5_wins}/{f5_cells} tentativas encadeadas com a ficha — "
                        "critério ≥19 APROVADO; {f5_repairs} reparadas por recusa "
                        "nomeada; o 7B sozinho {f5_7b}.",
        "bench.f5.foot": "Bruto: bench/results_f5_accept.jsonl · método: "
                        "bench/FINDINGS-F5.md",
        "bench.v13.sum": "O resultado negativo, publicado primeiro: no GSM8K real o "
                        "cartão-relé desaba a {v13_relay_05b}/20 no 0.5B — pedir a "
                        "decomposição ao modelo ainda é deixá-la com o modelo.",
        "bench.v13.foot": "Bruto: bench/results_v13_gsm8k.jsonl · método: "
                        "bench/FINDINGS-V13.md",
        "bench.v14.sum": "Skill estrita: {v14_breaks}/{v14_cells} rupturas de "
                        "protocolo — a única classe que a forma garante — a leitura "
                        "segue livre.",
        "bench.v14.foot": "Bruto: bench/results_v14_skill.jsonl · método: "
                        "bench/FINDINGS-V14.md",
        "bench.v22.sum": "Três modelos fronteira respondem {v22_nu} nus — um "
                        "{v22_best}, outro {v22_worst}. Pela ficha congelada: "
                        "{v22_fiche}. Pagar mais não muda a forma.",
        "bench.v22.foot": "Bruto: bench/results_v22.jsonl · método: "
                        "bench/FINDINGS-V22.md",
        "bench.v22b.sum": "Cinco passes no regime dos agentes: {v22b_ok}/{v22b_cells} "
                        "certos — o MESMO programa duas vezes: {v22b_stable}/14. "
                        "O servidor: {v22b_shas} sha por problema.",
        "bench.v22b.foot": "Bruto: bench/results_v22b.jsonl · método: "
                        "bench/FINDINGS-V22.md",
        "bench.v24.sum": "Trinta dias no mesmo CSV com um modelo QUE SABE cadeias: "
                        "{v24_sil}/{v24_days} dias de resposta vazia após 8.192 "
                        "tokens de raciocínio, {v24_ok} certas, faturados "
                        "${v24_usd}. A máquina: {v24_m_ok} a $0,00.",
        "bench.f7.sum": "As sete cadeias copiadas EN/PT: {f7_wins}/{f7_cells} — "
                        "critério ≥19 APROVADO; {f7_rep} ganhas pela recusa "
                        "nomeada. O 0.5b copia 4/7 em PT onde o FR o punha a 0/7: o "
                        "teto de leitura é do modelo × língua × forma.",
        "bench.f7.foot": "Bruto: bench/results_f7_accept.jsonl · critério gelado: bench/FINDINGS-F7.md",
        "bench.v24.foot": "Bruto: bench/results_v24_lfm3_30days.jsonl · a emenda está "
                        "no histórico git (run24 amendado)",
        "bench.v19.sum": "{v19_wins}/{v19_days} tentativas corretas para os modelos "
                        "— máquina: {v19_m_ok}/{v19_m_days} dias no mesmo byte; "
                        "{v19_drift} saídas diferentes de um só modelo em 30 dias.",
        "bench.v19.intro": "O mesmo CSV sujo limpo 30 dias seguidos. "
                        "Especificação de seis regras, gold ESCRITO À "
                        "MÃO antes do banco, um braço retry que só vê "
                        "sua própria forma — nunca a resposta. "
                        "Temperatura 0,7: o regime real dos agentes, "
                        "divulgado.",
        "bench.v19.arm": "braço", "bench.v19.right": "dias certos /30",
        "bench.v19.distinct": "saídas distintas",
        "bench.v19.foot": "Bruto: bench/results_v19_csv_bill.jsonl · "
                        "método + dólares: bench/FINDINGS-V19.md · "
                        "replay: python bench/run19.py",
        "bench.v17.sum": "Retry ×5 num erro sistemático: "
                        "{v17_retry_wins}/{v17_retry_cells} cadeias "
                        "consertadas — o mesmo erro, 5× o preço.",
        "bench.v17.intro": "Três braços, os mesmos 20 problemas novos, "
                        "cada token contado: responder nuo, tentar "
                        "cinco vezes, ou entregar o cálculo ao "
                        "servidor. Células: {v17_cells}.",
        "bench.v17.nu": "nu", "bench.v17.retry": "retry ×5",
        "bench.v17.relay": "servidor (ok · tokens/certo)",
        "bench.v17.foot": "Bruto: bench/results_v17_tokens.jsonl · "
                        "bench/FINDINGS-V17.md · replay: python "
                        "bench/run17.py",
        "bench.v16.sum": "{v16_wrong} erros em {v16_runs} execuções — "
                        "«não tenho certeza» dito {v16_doubt} vezes.",
        "bench.v16.intro": "Problemas do dia a dia gerados na hora, "
                        "cada modelo convidado a marcar sua confiança "
                        "com honestidade. Falharam sempre do mesmo "
                        "modo: com certeza.",
        "bench.v16.foot": "Bruto: bench/results_v16_calibration.jsonl "
                        "· bench/FINDINGS-V16.md · gerador: "
                        "bench/gen16.py (semeado, duplo oráculo).",
        "bench.v15.sum": "O muro tem FORMA: {v15_alone_wins}/{v15_cells} "
                        "tentativas em cadeia nuas ou com retry — "
                        "{v15_best_arm}/{v15_arm_cells} com o melhor "
                        "braço servidor.",
        "bench.v15.intro": "A matriz completa: 5 transportes × 4 "
                        "modelos gratuitos × 20 problemas semeado "
                        "(400 células), hipóteses comitadas ANTES da "
                        "primeira célula, previsões furadas "
                        "publicadas primeiro.",
        "bench.v15.foot": "Bruto: bench/results_v15_matrix.jsonl · "
                        "bench/FINDINGS-V15.md · replay: python "
                        "bench/run15.py && python bench/score15.py",
        "bench.v12.sum": "{v12_zero} sozinho → {v12_hero} com um só "
                        "relé. O zero vira herói.",
        "bench.v10.sum": "Uma resposta certa cada: {v10_alone} sozinho "
                        "→ {v10_server} com relé — a $0, auditado pelo "
                        "próprio banco.",
        "bench.v9.sum": "Uma frase vaga, seis chaves: {v9_alone} → "
                        "{v9_card} com o cartão de intenção.",
        "bench.v6.sum": "A primeira matriz — nu vs relé. Cada linha, "
                        "cada harness, cada falha: bench/FINDINGS.md.",
  "bench12.intro": "Dez cálculos exatos (7834×9217, 0.1+0.2, porcentagens "
                   "em cadeia…) × quatro modelos locais GRATUITOS × três "
                   "braços: responder nu, escrever Python, ou repassar uma "
                   "expressão ao math/calc. Mesmo quadro, duas físicas: o "
                   "braço código devolve float, o relé devolve exato.",
  "bench12.code": "escreve Python",
  "bench12.relay": "relé Mechacut",
  "bench12.foot": "O 8B falha no RELÉ por tagarelice de protocolo, não "
                  "por matemática — por isso a ficha de intenção escreve a "
                  "linha por ele. Nu, o 0.5B inventou 89000098; em relé, "
                  "9/10 com mediana de 0,2 s. Bruto: bench/"
                  "results_v12.jsonl, método: bench/FINDINGS-V12.md.\n",
  "bench.intro": "Uma tarefa congelada (seed 20261120): CSV sujo + JSON "
                 "quebrado + lista de URLs → um YAML canônico, resposta "
                 "espera fixada por sha256. O mesmo modelo local fraco "
                 "(Qwen 2.5, temperatura 0), um braço sozinho, um braço "
                 "guiando o Mechacut. Publicamos também os fracassos — o "
                 "0.5B falha nos dois braços, e um teto de capacidade é "
                 "um resultado.",
  "bench.model": "modelo", "bench.alone": "sozinho", "bench.with": "com "
                 "mechacut", "bench.tokens": "tokens consumidos",
  "bench.foot": "O 7B vai de 0 % a 100 % em uma única chamada de "
                "pipeline. Cada execução, cada token, está em "
                "bench/results.jsonl.",
    "nav.build": "Construir",
      "nav.market": "Mercado",
      "market.h2": "Eles também dizem",
      "market.creed": "As grandes casas convergiram na mesma frase — só o modo de entregá-la difere.",
  "build.h2": "O que voc\u00ea pode construir hoje",
  "build.intro": "Voc\u00ea tem um modelo pequeno e gratuito na sua "
                 "m\u00e1quina. Tr\u00eas coisas para fazer com ele — as "
                 "frases citadas s\u00e3o o que voc\u00ea diz ao agente, "
                 "as respostas s\u00e3o o que o servidor realmente "
                 "devolveu. Sem conta, sem cart\u00e3o, sem reza.",
  "build.r1.name": "A portaria da nota (Brasil)",
  "build.r1.say": "\u201cO CNPJ 11.222.333/0001-81 do meu cliente \u00e9 "
                  "v\u00e1lido para a nota?\u201d",
  "build.r1.got": "{{ \"valid\": true, \"algorithm\": \"mod-11 double "
                  "DV (Receita Federal)\" }}",
  "build.r1.why": "Sozinho, um 0.5B \u201ccalcula\u201d d\u00edgitos de "
                  "confer\u00eancia — e erra. Aqui os d\u00edgitos "
                  "decidem: a nota n\u00e3o morre no contador.",
  "build.r2.name": "O guarda-vazamento",
  "build.r2.say": "\u201cEscaneie este log antes de eu colar num "
                  "chatbot.\u201d",
  "build.r2.got": "2 achados \u2192 semente [SEED_PHRASE] e chave "
                  "[OPENAI_KEY_1]",
  "build.r2.why": "O scan devolve posi\u00e7\u00f5es, nunca o valor; a "
                  "m\u00e1scara nunca devolve a chave. O segredo veio "
                  "guardar-se aqui — proteg\u00e9o at\u00e9 de n\u00f3s.",
  "build.r3.name": "O r\u00e9lay do incidente",
  "build.r3.say": "\u201crel\u00e8ve les montants et dates de cette note "
                  "d\u2019incident\u201d \u2014 em franc\u00eas, para um "
                  "0.5B.",
  "build.r3.got": "money [3200.00, 12450.75] \u00b7 6/6 em 320 tokens "
                  "(sozinho: 0/6)",
  "build.r3.why": "\u00c9 o bench v9, igual: mesma tarefa, mesmo modelo, "
                  "uma linha de relay. Cada execu\u00e7\u00e3o est\u00e1 "
                  "em bench/results_v9.jsonl — reproduza voc\u00ea mesmo.",
  "build.connect": "Ou ligue agora: cole ESTA linha em qualquer agente, "
                 "at\u00e9 o menor \u2014 ela vira o manual completo:",
    "everyday.h2": "Para todo mundo",
      "everyday.open": "Expandir as provas — saídas reais do servidor, não maquetes.",
  "everyday.intro": "Sem código, sem jargão. Vinte e sete coisas que "
                    "uma pessoa pede ao agente numa terça — cada "
                    "resposta abaixo é a saída real do servidor, "
                    "não uma maquete.",
  "everyday.e1.name": "Wi-Fi de visitas, um scan",
  "everyday.e1.say": "\u201cColoca o Wi-Fi num QR para as pararem de "
                     "perguntar a senha.\u201d",
  "everyday.e2.name": "O cheque, por extenso",
  "everyday.e2.say": "\u201cEscreva R$ 1.234,56 por extenso no cheque "
                     "\u2014 o banco recusa erro.\u201d",
  "everyday.e3.name": "IBAN antes da transfer\u00eancia",
  "everyday.e3.say": "\u201cCopiei certo este IBAN? Se voltar, pago "
                     "tarifa.\u201d",
  "everyday.e4.name": "Receita em p\u00e1gina imprim\u00edvel",
  "everyday.e4.say": "\u201cTransforma minhas anota\u00e7\u00f5es da "
                     "receita numa p\u00e1gina limpa \u2014 quero o PDF "
                     "para a geladeira.\u201d",
  "everyday.e5.name": "Contando os dias",
  "everyday.e5.say": "\u201cQuantos dias at\u00e9 a "
                     "viagem?\u201d",
  "everyday.e6.name": "A conta que o caixa não fará",
  "everyday.e6.say": "\u201c-30 % e depois -20 % é -50 %, "
                     "certo?\u201d \u00c9 -44 %.",
  "everyday.e7.name": "Um terço do bolo, sem arredondar escondido",
  "everyday.e7.say": "\u201cMeu bolo de 6 porções, quero para 2 — "
                     "400 g de farinha, 5 ovos?\u201d 400 × 1/3 = "
                     "133 1/3 g exato, 135 g na balança. Os ovos são "
                     "ditos, não adivinhados.",
  "everyday.e8.name": "Uma terça sim, outra não",
  "everyday.e8.say": "“Clube do livro a cada duas terças às 19h — "
                     "as próximas quatro datas?” 3 e 17 de nov., 1º e "
                     "15 de dez.: quinzenal é PULAR as semanas do meio "
                     "— e o motor nomeia os pulos.",
  "everyday.e9.name": "Um pé, três respostas certas",
  "everyday.e9.say": "“EU 42⅔ ou 42,5 — qual é o meu número?” As duas "
                     "tabelas arredondam: o milímetro é exato, os "
                     "candidatos de meia e de terço aparecem escritos, "
                     "e a deriva entre sistemas é um número dito. "
                     "Nunca um número único confiante.",
  "everyday.e10.name": "Voo atrasado — quem me deve quanto",
  "everyday.e10.say": "“Meu voo chegou 3h20 atrasado — quanto me "
                      "devem de fato?” A DATA DO VOO escolhe a regra: "
                      "antes de 23 out. 2027 o antigo EC261 + "
                      "jurisprudência; depois, a nova tabela codificada "
                      "“ACIMA DE três horas”. Mesmos fatos de cada lado "
                      "dessa linha pagam diferente. € ou £, com o prazo "
                      "de reclamar em data real.",
  "everyday.e11.name": "Minha bagagem passa no portão",
  "everyday.e11.say": "“Minha mala é 40×18×12, voo em novembro de "
                      "2027 — grátis sob o assento?” A DATA DO VOO "
                      "decide: a regra de 2027 limita o item sob o "
                      "assento a 40×30×15; antes dela, nada é fixo. "
                      "Rotação conta — faces ordenadas, nunca a ordem "
                      "digitada.",
  "everyday.e12.name": "Dois planos, um número honesto",
  "everyday.e12.say": "“O plano A é mais barato por kWh, o B mais "
                      "barato por mês — quando o A ganha de fato?” A "
                      "virada = (diferença de fixo × dias) ÷ "
                      "(diferença de preço), em fração EXATA: "
                      "4.623⅓ kWh onde o artigo diz “cerca de "
                      "4.623”. “Nunca” também é resposta, nomeada, "
                      "quando um plano vence nos dois componentes.",
  "everyday.e13.name": "Quanto vale um ponto de verdade",
  "everyday.e13.say": "“29 000 pontos por um voo de R$ 438 menos R$ "
                      "5,60 de taxas — quanto vale o ponto?” (438 − "
                      "5,60) ÷ 29 000 × 100: o 1,49 impresso esconde o "
                      "exato 1081/725 = 1,491034… Subtraia ANTES de "
                      "dividir; é o SEU piso que diz “resgate” ou "
                      "“pague em dinheiro”.",
  "everyday.e14.name": "O peso de fato cobrado, as duas correntes "
                       "impressas",
  "everyday.e14.say": "“Duas transportadoras cobram 6 kg e 5 kg pela "
                      "minha caixa 40×30×25 — quem erra?” Nenhuma: "
                      "30 000 cm³ ÷ 5 000 = 6 exatos, ÷ 6 000 = 5 "
                      "exatos — dois divisores, uma corrente honesta, "
                      "cada passo nomeado. E as tabelas ESTRAGAM "
                      "(USPS: 166→139 em julho de 2026); o divisor "
                      "continua SEU argumento — nunca nossa memória.",
  "everyday.e15.name": "A placa diz 50 % — a conta, nunca",
  "everyday.e15.say": "“Compre um e leve o segundo com 50% off — duas "
                      "camisetas de R$ 60 e R$ 40, quanto eu pago?” Nem "
                      "50 nem 25: o desconto cai sobre a MAIS BARATA "
                      "(regra de varejo publicada), o par sai por 80 de "
                      "100 = −20 %. Preços iguais = −25 %; BOGO grátis = "
                      "−50 %; e um cupom de −30 % por cima dá −47,5 %, "
                      "nunca 55 — percentuais multiplicam.”",
  "everyday.e16.name": "Os 500 g viraram 400 g — pelo mesmo preço",
  "everyday.e16.say": "\u201c−20 % na embalagem?\u201d Não é o mesmo "
                      "número da prateleira: perder 1/5 do produto "
                      "custa +1/4 por quilo (20 % contra 25 % — dois "
                      "denominadores, 500 e 400). E \u201c2 por "
                      "R$ 7\u201d de potes de 15 oz perde 40,3509 % "
                      "por onça para o pote único de 24 oz — a fração "
                      "exata decide, não o olho.",
  "everyday.e17.name": "Ação de graça quinta: a que horas tirar o peru do congelador",
  "everyday.e17.say": "Oito calculadoras de nov. 2026 citam a mesma tabela USDA e se contradizem sobre o peru de 16 lb. Regra nomeada: no mais tardar = forno menos a ponta longa da faixa; não antes = menos a guarda de 1 a 2 dias. Horas são argumentos, nunca o relógio; pronto é 165 °F na sonda.",
  "everyday.e18.name": "O peru virou sobra — que dia fecha a janela da "
                       "geladeira",
  "everyday.e18.say": "A imprensa grava « comer até segunda 30 de novembro » (NBC, 19 nov) ao lado de « três dias, 72 h ideais » (ky3) para o mesmo peru; as duas páginas FSIS brigam no freezer (2-6 vs 3-4 meses). A ferramenta devolve a UNIÃO das janelas com as duas âncoras citadas, a regra das 2 h ESTRICTA desde cooked_at (2 h exatas passa, 2 h 01 descarta), o 4º dia nomeado LAST_DAY; segura a −18 °C, qualidade nomeada qualidade.",
  "everyday.e19.name": "Três pratos querem o forno — a contagem e os "
                       "conflitos nomeados",
  "everyday.e19.say": "Oito timelines 2026 publicam o mesmo jantar com descansos de 20 a 60 minutos, 325 ou 350 °F — e ninguém conta o pré-aquecimento que come 45 minutos. Cálculo AO CONTRÁRIO da hora de servir (argumento, nunca relógio): um forno, um prato por vez, descanso fora; entrada no minuto da saída em outra temperatura = conflito nomeado; «180» sem unidade = recusado; descanso além de 2 h = zona FSIS.",
  "everyday.e20.name": "Prazos de envio do Natal \u2014 \u22652 fontes "
                     "por linha, a divergente nomeada",
  "everyday.e20.say": "Seis tabelas de 13 a 21/nov/2026 se "
                      "contradizem: um sindicato imprime FedEx "
                      "Saver, 2Day e Overnight um dia depois \u2014 a "
                      "meta dele \u00e9 25, n\u00e3o 24. Linha s\u00f3 com "
                      "\u22652 fontes concordantes; a divergente \u00e9 "
                      "nomeada com o motivo. UPS Ground recusado: "
                      "data \u00fanica n\u00e3o existe. as_of \u00e9 "
                      "argumento, n\u00e3o rel\u00f3gio. Janela morre "
                      "em 23/dez.",
  "everyday.e21.name": "Prazos de DEVOLU\u00c7\u00c3O das festas \u2014 \u22652 "
                     "fontes, classe de proven\u00e2ncia por linha",
  "everyday.e21.say": "A manchete « até 31 de janeiro » é mentira por omissão: na Target a janela de compra fecha 24/dez, na Best Buy a regra de membros corta em 4/dez, e um blog republicou as datas do ano passado deslocadas enquanto o Seller Central publicava o texto 2026 literal. Linha só com duas fontes concordantes; proveniência por linha; convenção nomeada; fonte única recusada pelo nome, com o fato candidato. « O mais tarde dos dois » exige a data de entrega.",
  "everyday.e22.name": "O pre\u00e7o riscado \u00e9 LEGAL \u2014 a "
                     "regra Omnibus dos 30 dias, auditada do SEU "
                     "hist\u00f3rico",
  "everyday.e22.say": "A lei nomeia a referência: o preço MAIS BAIXO dos 30 dias anteriores (Diretiva 2019/2161 art. 6a) — promoção de fim de semana ABAIXA a referência mesmo se o preço subiu depois (TJUE C-330/23). 100 → 80 → 100 → 70 é 12,5%, não 30%. Varredura da Comissão, março de 2026: 30% de 314 lojas erram; a Espanha multou até 350.000 EUR. Histórico entra, referência e porcentagem real saem — nunca busca preços.",
  "everyday.e23.name": "O pre\u00e7o CAIU depois da compra \u2014 quem "
                       "deve a diferen\u00e7a, at\u00e9 quando, em que dinheiro",
  "everyday.e23.say": "Comprou por 100, a loja mostra 80 agora. "
                      "Nenhuma lei obriga o reembolso \u2014 mas as "
                      "garantias publicadas das lojas sim, e essas "
                      "janelas s\u00e3o DATAS: Target 24 dez, Best "
                      "Buy 15 jan, Costco 30 dias, Amazon nada. Cole "
                      "as datas da compra e da queda e os dois "
                      "pre\u00e7os \u2014 a m\u00e1quina devolve o "
                      "veredicto, o prazo do pedido, o valor e a "
                      "forma do reembolso, com a classe de fonte em "
                      "cada linha. Ela nunca busca pre\u00e7os.",
  "everyday.e24.name": "O presente quebrou DEPOIS do prazo de "
                       "troca — o que a LEI ainda deve, ao dia",
  "everyday.e24.say": "Presente entregue em 25 de dezembro, morto em 16 de janeiro: a janela da loja fechou dia 15 e a imprensa cala; a lei não. França: conformidade 2 anos desde a ENTREGA, vícios ocultos 2 anos desde a DESCOBERTA, teto de 20 anos da venda — três âncoras. Reino Unido: 30 dias para rejeitar, seis meses de ônus INVERTIDO (prova, não prazo), seis anos para agir — cinco na Escócia. Página oficial se contradiz (recondicionado: 24 ou 12): as DUAS datas viajam. EUA e Austrália recusados por nome.",
    "everyday.e25.name": "Posso descartar esta pasta? — a gaveta "
                       "britânica esconde QUATRO relógios",
  "everyday.e25.say": "«Seis anos» é UMA frase para quatro datas: VAT conta da data ESCRITA NO DOCUMENTO (evento futuro incluso — o manual da HMRC diz), limited company do FIM do exercício, Companies Act s.388 TRÊS anos se private, SEIS se plc — desde a CRIAÇÃO —, Self Assessment cinco anos do prazo de 31 de janeiro que não está em papel nenhum. Exemplo refeito: 2022-23 até 31 de janeiro de 2024 → guardar até 31 de janeiro de 2029, descartar de 1º de fevereiro. Os «ou mais se» voltam BLOCKED — nunca data inventada. CH15400: a MAIS LONGA governa. Jurisdição Reino Unido; notas do Brasil seguem outra lei.",
  "everyday.e26.name": "O vale-presente « vencido » pode estar vivo "
                       "— na Irlanda conta-se da COMPRA",
  "everyday.e26.say": "Irlanda, Gift Vouchers Act 2019 rejogado: validade impressa menor que CINCO ANS desde a compra é SUBSTITUÍDA por cinco anos e a data legal COBRE o papel (66B(1)(b)+(c)). Forma JD Sports: vales de um ano, ≈€250.000 devolvidos em julho após a notificação do CCPC de 20 de novembro. A âncora é o contrato e quem segura o vale tem TODOS os direitos (66B(10)). Saldo de €1 ou mais é devido. França: nenhuma duração legal; o boato dos «30 anos» é prescrição imobiliária, recusado por nome.",
  "everyday.e27.name": "As datas dos saldos na Fran\u00e7a s\u00e3o "
                       "LEI, n\u00e3o mem\u00f3ria \u2014 2027 abre a 6 de "
                       "janeiro",
  "everyday.e27.say": "O arrêté de 27 de maio de 2019 rejogado: inverno abre na 2ª quarta de janeiro às 8h, ANTECIPADO se a 2ª cai após o dia 12 — 2027: 6 de janeiro; quem imprime «9 de fevereiro» perdeu a cláusula. Verão idem: última quarta de junho, penúltima se a última cai após o 28 — 2027: 23 de junho. Quatro semanas contando o dia de abertura. As sete derrogações anuais com o texto: verão 2020 a 15 de julho; inverno 2021 a 20 de janeiro e depois SEIS SEMANAS; Mosela sozinha a 26 de junho de 2021; Guadalupe a 7 de outubro de 2021; canícula 2023 e 2026 a cinco semanas. «Primeiro dia útil» sem definição: em 2027 segunda 4 primeiro, sábado 2 nomeado. Antes de 2020 e estrangeiro recusados por nome; contagem é subtração, não relógio.",
"nav.kit": "Kit",
  "kit.h2": "A suíte no seu disco",
  "kit.creed": "O protocolo não é o transporte \u2014 é a certidão de nascimento da ferramenta.",
  "kit.intro": "As transformações livres não são só uma API. São uma suíte: um agente pode instalá-la na própria máquina, chamá-la localmente e \u2014 a parte que nenhum mercado faz \u2014 construir ferramentas novas sobre os mesmos portões. curl vira kit call; tarefa repetida vira proposta de contrato; a proposta vira ferramenta publicada apenas se seus golds foram traçados antes do código.",
  "kit.c1.sum": "Instalar \u2014 a suíte básica na máquina",
  "kit.c1.foot": "Sha verificado, sem daemon, sem auto-update, sem rede dentro do motor. O sem-estado é o contrato: o humano decide quando o kit se move.",
  "kit.c2.sum": "Chamar \u2014 consultar antes de agir",
  "kit.c2.foot": "A skill consulta o diretório primeiro. Mesmo cânone, mesmas recusas, mesmos golds do datacenter \u2014 o que é verificado aqui é verificado lá, byte por byte.",
  "kit.c3.sum": "Construir \u2014 na segunda vez, escrever a ferramenta",
  "kit.c3.foot": "Golds traçados ANTES do código, AST-gate, pin-gate. Status: proposto, atestado, rede-verificado \u2014 o kit cresce localmente, a prova cresce de volta na rede. Uma lição é uma proposta; o banco a tranca.",
  "kit.howto.p1": "Instalar a skill: <code>curl https://mechacut.studio/SKILL-MINI.md -o SKILL.md</code> \u2014 soltar o arquivo no agente (CLAUDE.md, AGENTS.md, skills/). ~1,000 tokens, calibrado para modelos pequenos.",
  "kit.howto.p2": "Fazê-lo consultar primeiro: antes de agir, o agente descreve o problema em uma frase a /route/resolve \u2014 o diretório devolve a ferramenta que já existe, ou diz que não há.",
  "kit.howto.p3": "Chamar: POSTs sem estado, sem chave no livre; a resposta traz seu sha256, a recusa traz campo + esperado + exemplo. Tudo o que há nesta página já funciona: uma linha instala o arquivo de skill, o diretório responde, as chamadas livres não têm chave.",
  "kit.plain.sum": "Você não é desenvolvedor? Sem problema \u2014 a gente traduz.",
  "kit.plain.p1": "Abra seu assistente de IA de sempre (Claude, ChatGPT, Grok, Copilot\u2026).",
  "kit.plain.p2": "Envie esta mensagem: \u0022Leia https://mechacut.studio/SKILL-MINI.md e siga-o para os meus cálculos.\u0022 Nada para instalar, nada para pagar, sem conta.",
  "kit.plain.p3": "Depois peça a tarefa real: \u002230% e depois 20% de desconto dá quanto?\u0022, \u0022quantos dias de atraso tem esta fatura?\u0022 Os números não saem mais da cabeça dele \u2014 saem da suíte, e são os mesmos para todos.",
  "kit.plain.p4": "Pediu algo que a suíte não faz? Proponha em palavras simples \u2014 cada proposta é pública, e seu veredito também: entregue, em bancada ou recusado com o motivo nomeado, em /proposals.",
  "kit.dev.sum": "Para desenvolvedores \u2014 três linhas, sem conta",
  "kit.propose": "Proporcionar uma ferramenta: POST /api/v1/agent/propose — um contrato, nunca código; duplicado nomeado, evidência exibida, elegibilidade devolvida como blob pronto para commit. Nada é guardado no servidor. Skill do protocolo: /SKILL-KIT.md",
  "bench.d82.sum": "Traces de chamadas julgadas: o mesmo gesto de agente nunca foi reemitido igual (0 de 14, V22b) e um retry multiplicou a fatura ×4 sem convergir (V17) \u2014 loop/doom-check agora diz DOOM, CYCLIC ou STORM sobre bytes canônicos, limiares nomeados.",
  "bench.d82.foot": "Identidade em (ferramenta, args) canônicos: a ordem das chaves nunca esconde um loop. Duas chamadas iguais não são loop \u2014 o limiar é dito, nunca adivinhado. Todos os sinais reportados, veredito o mais grave. Fontes: bench/FINDINGS-V17.md · run22b.",
  "bench.e76.sum": "O juiz do banco virou rota: eval/compare devolve OK ou WRONG com as divergências nomeadas \u2014 2.5 versus \u00222.50\u0022 nunca é discordância, floats nunca são argumento.",
  "bench.e76.foot": "Regra nascida do incidente do juiz V2 (ele copiava a própria expectativa): mesma quantidade nunca é divergência; quantidade diferente é nomeada por pointer, kind, expected, got. Decimal exato, nunca float.",
  "bench.a79.sum": "Política como gramática fechada: check/allowlist devolve ALLOW, DENY ou AMBIGUOUS \u2014 a regra mais específica vence, empate sobe ao humano, silêncio nunca autoriza.",
  "bench.a79.foot": "Uma ação em forma de regex é recusada, não avaliada: um gate que interpreta é porta dos fundos. Valores Decimal exatos, tabela ISO de moedas, default deny verdadeiro. A mesma lei do R3 do diretório, outro domínio.",
"x402.h2": "Pagamentos entre máquinas",
  "x402.p1": "O caminho pago cabe em quatro bytes de protocolo: o "
             "servidor responde <code>402</code> com os requisitos; o "
             "agente assina uma transferência USDC EIP-3009; um "
             "facilitador verifica e liquida; a resposta reproduz a prova "
             "em <code>X-PAYMENT-RESPONSE</code>. O servidor não guarda "
             "chaves.",
  "x402.p2": "Pagamentos repetidos são recusados. Erros em rotas pagas "
             "continuam grátis. O registro de cada recusa é público: "
             "<a href=\"/misses.json\">/misses.json</a>.",
  "x402.bankr": "Mesmos endpoints, segunda casa: quatro transforms pagos tamb\u00e9m est\u00e3o no x402 Cloud do <a href=\"https://bankr.bot\">Bankr</a> \u2014 mesmos caminhos de c\u00f3digo, mesmos sha256, pagos pelos trilhos Bankr: <a href=\"https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/chart_from_data\">chart</a> &middot; <a href=\"https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/reshape_json\">reshape</a> &middot; <a href=\"https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/validate_json\">validate</a> &middot; <a href=\"https://x402.bankr.bot/0x00f04a2a505116daf3b88eae17445d85bed4fbac/csv_join\">csv-join</a>. Os outros 68 vivem s\u00f3 aqui, tier gratuito incluso.",
  "vision.h2": "Por que determinismo, por que agora",
  "vision.p1": "Um grande modelo de linguagem é uma máquina de aproximar. "
               "Pergunte <code>sha256(\"abc\")</code> e ele responderá "
               "com confiança, elegância e erro. Peça para limpar o mesmo "
               "CSV todo dia e ele cobrará tokens para re-derivar o que "
               "uma função entrega em milissegundos — com os mesmos "
               "bytes, sempre.",
  "vision.p2": "O computador de navegação Apollo tinha 4 KB de RAM. Pousou "
               "humanos na Lua porque a matemática nunca precisou "
               "improvisar: cada constante foi calculada uma vez, no solo, "
               "a frio, e congelada na memória de corda.",
  "vision.quote": "O determinismo foi codificado a primeira vez para nos "
                  "levar à Lua. O determinismo levará a IA ao trabalho.",
  "vision.p3": "Mechacut é essa matemática congelada para agentes: "
               "vocabulários fechados, contratos que recusam o que está "
               "fora da tabela, erros que nomeiam a forma esperada — o "
               "erro é o prompt que conserta. O significado fica com o "
               "modelo. A mecânica se muda para cá.",
  "contract.h2": "O contrato",
  "contract.li1": "Mesma requisição → mesmos bytes, sha256 em cada "
                  "resposta",
  "contract.li2": "Sem cadastro, sem chave, sem muro de taxa abaixo de "
                  "30 req/min",
  "contract.li3": "Zero armazenamento: o único estado é uma janela de 1 "
                  "minuto, um registro de 60 minutos e um conjunto de "
                  "nonces de pagamento",
  "contract.li4": "Vocabulários fechados — tudo fora da tabela é recusado, "
                  "nomeado, apontado à forma esperada",
  "contract.li5": "Erros que consertam: campo, mensagem, esperado, sempre",
  "contract.li6": "Pagamentos x402 entre máquinas: USDC na Base, "
                  "verificados por facilitador, zero humano no circuito",
  "agents.line": "Fale agente: ferramentas MCP, GET /agent/manifest "
                 "(a suíte inteira em uma requisição), GET /route?q=…, "
                 "POST /api/v1/pipeline.",
  "agents.hint": "instale um pack",
  "footer.family": "Mechacut faz parte da família C.V. — veja moovicut.",
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
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{meta.title}}</title>
<meta name="description" content="{{meta.desc}}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='18' fill='%23141414'/><path d='M20 70 L40 45 L55 55 L80 25' stroke='%23d4af37' stroke-width='9' fill='none' stroke-linecap='round' stroke-linejoin='round'/></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0a0a0a; --fg: #ececec; --muted: #8f8f8f;
    --gold: #d4af37; --line: #232323; --card: #121212;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: var(--bg); color: var(--fg);
    font-family: "Inter", system-ui, -apple-system, sans-serif;
    line-height: 1.6; -webkit-font-smoothing: antialiased; }
  .wrap { max-width: 1020px; margin: 0 auto; padding: 0 24px; }
  header.top { display: flex; align-items: center; justify-content: space-between;
    padding: 26px 0; border-bottom: 1px solid var(--line); }
  .brand { display: flex; align-items: center; gap: 12px;
    font-family: "Space Grotesk", sans-serif; font-weight: 700; letter-spacing: -.3px; }
  .brand svg { display: block; }
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
  .why { font-size: 15px; font-weight: 400; line-height: 1.6; max-width: 680px; margin: 14px 0 0; color: var(--muted); }
  .why strong { color: var(--gold); font-weight: 600; }
  .lede { font-size: 16px; color: var(--muted); max-width: 700px; margin-bottom: 36px; }
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
  .tcard .tierdot { font-size: 10px; }
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
  @media (max-width: 480px) {
    .catgrid { grid-template-columns: 1fr; }
    .navbtn { display: block; }
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
  .tcard .tp{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
  .mgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
  .mcard{border-left:2px solid var(--gold);padding:14px 18px;background:var(--card);border-radius:0 10px 10px 0}
  .mcard q{display:block;color:var(--fg);font-size:14.5px;line-height:1.55;font-style:italic}
  .mcard cite{display:block;margin-top:10px;font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:var(--muted);font-style:normal}
  .mcard cite b{color:var(--gold);font-weight:400}
  .mcard cite a{color:var(--muted)}
.bcard{border:1px solid var(--line,#232b3d);border-radius:10px;margin:10px 0;background:var(--card,#121724)}\n.bcard summary{cursor:pointer;padding:13px 16px;font-weight:700;color:var(--ink,#e8ecf4);list-style-position:outside}\n.bcard summary .bv{color:var(--gold,#ffcf5c);margin-right:10px}\n.bcard .bbody{padding:4px 18px 16px}\n.bgroup{color:var(--gold,#ffcf5c);margin:30px 0 8px;font-size:1.08em;letter-spacing:.02em}\n</style>
</head>
<body>
<div class="wrap">

  <header class="top">
    <div class="brand">
      <svg width="26" height="26" viewBox="0 0 100 100" aria-hidden="true"><rect width="100" height="100" rx="18" fill="#141414"/><path d="M20 70 L40 45 L55 55 L80 25" stroke="#d4af37" stroke-width="9" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>
      MechaCut
    </div>
    <nav>
      <a href="#bundles">{{nav.tools}}</a>
      <a href="#bench">{{nav.numbers}}</a>
      <a href="#market">{{nav.market}}</a>
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
      <p class="why">{{hero.why}}</p>
    </section>

    <section class="section" id="market">
      <h2>{{market.h2}}</h2>
      <p class="quote">{{market.creed}}</p>
{{market_grid}}
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
      <p class="tiers" style="margin-top: 14px;"><a href="https://github.com/Davincc77/mechacut/blob/master/PROTOCOL-KIT.md">PROTOCOL-KIT.md</a> · <a href="https://github.com/Davincc77/mechacut/blob/master/SKILL-NETWORK.md">SKILL-NETWORK.md</a></p>
      <p class="tiers" style="margin-top: 10px;">{{kit.propose}}</p>
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

    <section class="section tiers" id="tiers">
      <h2>{{tiers.h2}}</h2>
      <p>{{tiers.intro}}</p>
    </section>

    <section class="section" id="bench">
      <h2>{{bench.h2}}</h2>
      <p class="quote">{{bench.creed}}</p>
      <p class="tiers" style="color: var(--muted); max-width: 720px;">{{bench.intro}}</p>
      <h3 class="bgroup">{{bench.g1}}</h3>
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
            <h3 class="bgroup">{{bench.g2}}</h3>
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
            <h3 class="bgroup">{{bench.g3}}</h3>
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
            <h3 class="bgroup">{{bench.g4}}</h3>
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
            <h3 class="bgroup">{{bench.g5}}</h3>
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

<section class="section build" id="build">
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

    {{everyday_grid}}

    <section class="section x402" id="x402">
      <h2>{{x402.h2}}</h2>
      <p>{{x402.p1}}</p>
      <p>{{x402.p2}}</p>
      <p>{{x402.bankr}}</p>
    </section>

    <section class="section vision" id="vision">
      <h2>{{vision.h2}}</h2>
      <p>{{vision.p1}}</p>
      <p>{{vision.p2}}</p>
      <div class="quote">{{vision.quote}}</div>
      <p>{{vision.p3}}</p>
    </section>

    <section class="section" id="contract">
      <h2>{{contract.h2}}</h2>
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
    </section>
  </main>

  <footer>
    <div class="row">
      <div>{{footer.family}}</div>
      <div><a href="/misses.json">/misses.json</a> · <a href="/route?q=dirty%20csv%20into%20yaml">/route</a> · <a href="/api/v1/recipes">/recipes</a></div>
      <div><a href="https://github.com/Davincc77/mechacut" rel="me">GitHub</a> · <a href="https://x.com/Davincc" rel="me">Follow on X</a></div>
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
           (!w || c.dataset.hay.indexOf(w) >= 0);
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
    var cmd = trycmd || "curl -s https://" + location.host + "/tools/" +
              pname.textContent + ".json";
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
            "en-têtes Retry-After et X-RateLimit-* lus (delta-seconds ou IMF-fixdate strict) ; en désaccord, les deux attendus sont NOMMÉS, jamais choisis ; now est un argument, jamais l’horloge murale",
        "number_words_pair":
            "forme écrite et forme chiffrée vérifiées l’une contre l’autre — trente (40) refuse : AGREE/MISMATCH/NO_PAIR, les deux valeurs gardées",
        "agent_mcpaudit":
            "la liste d'outils MCP collée jugée contre des "
            "règles de rejet nommées, avant qu'un client ne "
            "la descarte en silence",
        "agent_mcpsurface":
            "empreinte SHA-256 de la surface d'outils MCP collée, "
            "puis dérive NOMMÉE contre un relevé antérieur — "
            "annotations canoniquées à leurs défauts publics de la "
            "spec, l'angle mort du AI SDK fermé ; ordre compris "
            "dans le contrat",
        "agent_contexttax":
            "combien coûte VOTRE liste MCP collée, mesurée en octets et tokens (estimateur publié chars÷4, plancher déclaré), par outil et par champ — contre-fait names-only chiffré, facture PAR TOUR, dollars au prix que VOUS portez ; mcp-audit dit REJETÉ, mcp-surface dit CHANGÉ, ici on dit COMBIEN",
        "shop_gift_voucher":
            "carte cadeau « périmée » d'un an REMPLACÉE d'office par cinq ans depuis l'achat — le légal couvre le papier (loi irlandaise 2019 rejouée, forme JD Sports) ; solde d'1 € ou plus = dû, frontière 1 € en conflit NOMMÉ ; France NÉGATIVE : aucune durée légale, le mythe des « 30 ans » est immobilier, refusé par nom",
        "shop_soldes_window":
            "les dates légales des soldes viennent de l'arrêté du 27 mai 2019 rejoué : clauses d'avance aux deux saisons (2027 : 6 janvier, pas 13 ; 23 juin, pas 30), sept dérogations au verbatim (hiver 2021 à six semaines, Moselle seule au 26 juin 2021), annexe versionnée, « ouvré » ambigu nommé ; hors France refusé par nom",
        "agent_retrybudget":
            "re-tenter cet échec est-il rationnel ? taxonomie "
            "fermée, plafond de hachage, budget de session, backoff "
            "déterministe",
        "shop_discount_audit":
            "règle Omnibus des trente jours : le prix barré est-il "
            "légal ? référence, vrai pourcentage, verdict nommé",
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
            "prorata exact avant dernier arrondi",
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
            "mise à l'échelle de recette avec l'arrondi DÉCLARÉ : fraction exacte + pas mesurable par classe d'ingrédient + delta, multiplicateur dit une fois",
        "check_format":
            "validation de format en ensemble fermé pour les règles que JSON Schema ne peut pas exprimer (dates, semver, uuid, decimal-string…) — violations avec pourquoi + attendu",
        "csv_money_columns":
            "colonnes CSV financières lues par convention PROUVÉE — les valeurs non ambiguës de la colonne décident, contradictions refusées, pas devinées",
        "date_relative":
            "expressions de date relative (EN/FR/PT) vers ISO exact — grammaire fermée, « now » en argument, ambiguïtés signalées jamais tranchées",
        "date_recurrence":
            "RRULE déroulé en dates — sous-ensemble RFC 5545 fermé, mois invalides sautés LISTÉS, ancrage du DTSTART déclaré, COUNT ou UNTIL jamais les deux, refus nommés, cap 500",
        "date_tz_ambiguity":
            "Heure murale + zone → single | fold | gap : les heures qui n'existent pas (spring forward) ou qui existent DEUX FOIS (fall back), chaque instant UTC nommé avec offset et abréviation, la règle PEP 495 dite, les voisins du trou rendus — le verdict que date/tz applique en silence, cron_next ne signale pas",
        "date_tz_anchor":
            "Une heure murale ÉCRITE dans la zone du job, ANCRÉE par la machine dans sa zone : chaque instant UTC candidat, la dérive SIGNÉE en minutes (positif = en retard), les deux horloges relues ; l'offset gagne (résolution Composio #4148) ; single/fold/gap rendus par l'engine date/tz_ambiguity APPELÉ, jamais dupliqué",
        "money_flight_comp":
            "Date de vol = TABLE de compensation : 261/2004 + Sturgeon/Nelson avant 2027-10-23, (UE) 2026/2202 codifié APRÈS (seuil « EXCEEDING 3 h » STRICT, 180 min pile ne paye pas), UK261 £220/350/520 avec la ligne officielle £260 sous 4 h, plafond intra-UE €400 nommé, réductions = options « le transporteur PEUT », forclusion 9 mois en date exacte, zéro fetch",
        "date_week":
            "Semaine ISO aller-retour — année ISO SÉPARÉE du %Y, W53 par LE THÉORÈME (53 jeudis ⟺ Jan-1 jeudi, ou mercredi + bissextile ; zéro table), semaine inexistante refusée avec l'artefact %Y-W%V nommé, conventions Excel/US (%U %W WEEKNUM) côte à côte, notes PostgreSQL/Snowflake",
        "units_shoe_size":
            "Pointures en millimètres exacts — pas publiés en fractions (barleycorn 127/15, Paris point 20/3), demi ET tiers comme candidats de grille, dérive entre systèmes DITE, jamais un seul numéro confiant, charts marques hors contrat",
        "net_sri":
            "Attribut Subresource Integrity depuis des OCTETS LOCAUX — jamais de fetch : integrity prêt à coller, crossorigin, audit du style d'attribut (classe CVE-2026-120423 TAB), URL @latest ou range signalées comme panne programmée",
        "text_url_canonical":
            "RFC 3986 §6.2.2 canonicalisation d'URL — toute transformation listée, paramètres de tracking retirés par opt-in nommé, IDN en punycode",
        "xml_to_json":
            "XML vers JSON avec les règles de conversion imprimées dans la réponse ; force_array fige la cardinalité, DTD refusé par son nom",
        "web_cert":
            "Lint de certificat X.509 depuis PEM : SANs, validité, flags de dépréciation, forme de la chaîne ; as_of rend le verdict rejouable",
        "id_checkdigit":
            "clés de contrôle : ISBN/EAN/GTIN/ISIN/LEI… vérifier, réparer, scanner",
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
            "jours fériés légaux FR BR PT DE US avec la loi citée sur chaque ligne",
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
            "la chaîne « du RESTE » en un appel : total, vendus du matin, % de l'après-midi → la trace des trois pas et le reste exact ; 0/28 nu et retry sur cette forme (bench v15) — la décomposition est le travail, il est déjà fait ici",
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
            "règle de trois, dilution C1V1, dosage mg/kg, EDD Naegele, hydratation du boulanger, part en pourcentage — la formule publiée, vos nombres substitués, le calcul exact",
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
            "Date du vol = palier LOI (40×30×15 sous le siège GRATUIT depuis 2027-10-23, RIEN avant — chaque compagnie décide) ; casier : la loi ne fixe AUCUNE taille ; gabarits transporteur EN ARGUMENTS, jamais fetchus ; ajustement PAR DIMENSION avec ROTATION (40×18×30 passe dans 40×30×20) ; le « cumul 100 cm / 7 kg » de la presse rendu comme affirmation TESTÉE (55+40+20=115), jamais comme règle",
        "csv_excel_damage":
            "Ce qu'Excel DÉTRUIT au double-clic, PRÉDIT avant : zéros de tête (02134→2134), mur des 15 chiffres (…1111→…1110), notation scientifique (1E5→100000), dates forcées (SEPT2, MARCH1, « 3-4 » = 4 mars EN / 3 avril EU — locale ARGUMENT, année figée par as_of), formes de formule (=-+@), pleine chasse ; règles = les trois interrupteurs Microsoft nommés ; import colonne-Texte PRESCRIT ; csv/fix répare, ici on PRÉDIT",
        "money_crossover":
            "Prix de reviens de DEUX tarifs à composantes (unitaire + fixe) : la bascule en FRACTION EXACTE — les sept calculateurs publiés arrondissent le Δ fixe avant de diviser et se contredisent ; conventions de jours NOMMÉES (mensuel ×12 exact, jamais 30 jours ; journalier ×365 ou 366 bissextile fourni ; « semaine » refusée) ; DOMINATION rendue « never » nommée ; km si consommation FOURNIE ; frais one-off en mois de payback, séparés de la bascule structurelle",
        "money_points":
            "Combien vaut un POINT : cpp = (prix cash - reste cash - rewards forgoes) / points x 100 en FRACTION EXACTE (1081/725 là où la presse dit 1.49) ; voies côte à côte triées, égalités nommées, verdict contre FLOOR fourni, solde x cpp, retour effectif pts/$ x cpp ; jamais de table de valorisation embarquée",
        "csv_excel_display":
            "Ce qu'Excel AFFICHE d'une valeur STOCKÉE sous un code numFmt : la virgule trailing SCALE par mille (« $#,##0, » + 1 000 000 → $1,000 — l'attaque mesurée arXiv 2611.05806, six extracteurs python aveugles) ; exemples de la table Microsoft rejoués (« #.0,, »→12.2, « (000) »→(012), « 0% »→50%) ; arrondi de display demi-vers-le-large dit ; locale en ARGUMENT (les séparateurs du fichier sont des symboles — ingénieur Microsoft) ; General/dates/couleurs refusés PAR LE NOM ; rendu de style, la prédiction d'import est une autre route",
        "ship_dimweight":
            "Le poids VRAIMENT facturé du colis : dimensions arrondies AU POUCE SUPÉRIEUR avant volume, volume ÷ diviseur (son unité est DECLAREE — le piège mm÷139 x16,4 devient impossible), max(actual, dimensionnel), ceil au palier, plafond. rollo 35 lb vs amzprep 34,5 sur les MÊMES pouces : la fraction exacte 4800/139 tranche et chaque étape est nommée ; tables transporteurs en ARGUMENTS (USPS 166→139 le 12-juil-2026 = elles pourrissent)",
        "json_coerce":
            "Répare les ARGUMENTS d'un appel d'outil qu'un lecteur STRICT refuse : 8.0→8 (classe serde « invalid type: floating point 2500.0, expected u64 », 11/11 tours mesurés), exposants et fractions vraies laissés TELS QUELS, 'false' en chaîne refusé PAR LE NOM (piège truthy), string→number seulement si cast_strings=on, '007' JAMAIS (les zéros de tête sont du payload), clés dupliquées refusées ; la notation d'origine est CONSERVÉE à la sortie",
        "money_bogo":
            "Le pourcentage que la CAISSE applique vraiment sous un panneau « BUY ONE GET ONE 50 % » : la remise porte sur le MOINS CHER des deux (règle de détail publiée — 60+40 rend 80 sur 100, soit 20 %, ni 25 ni 50), prix égaux = 25 % de la paire JAMAIS 50, l'article impair se paie PLEIN (les paires sont DONNÉES, jamais devinées), le coupon s'EMPILE en produit de facteurs (25 puis 30 = 47,5, jamais 55) ; trace par paire, fraction exacte à côté de l'affichage",
        "agent_modelid":
            "audit des ids de modèle contre un catalogue collé — verdicts nommés, did-you-mean à une distance nommée, ne jure jamais avoir fait le GET (V23)",
        "food_poultry":
            "fenêtre décongélation et cuisson de la dinde, tables USDA FSIS, horloge ISO en argument — jamais l'horloge murale, jamais de nombres inventés",
        "food_leftovers":
            "fenêtre des restes, USDA FSIS : seuil 2h, 3-4 jours frigo, 2-6 mois congélateur (UNION des deux pages FSIS contradictoires) — tous les temps en ARGUMENTS, jamais l'horloge murale, jamais de tables inventées",
        "food_ovenschedule":
            "un four, des plats, une heure de service : compte à rebours à l'envers, conflits de température nommés, jamais d'horloge murale — les timelines web ne vérifient rien de tout ça",
    },    "pt": {
        "address_parse":
            "endereço postal → país, CEP validado contra 50 gramáticas, linhas restantes; ambiguidade NOMEADA, nunca adivinhada",
        "date_civil":
            "instante + fuso IANA nomeado → a data civil que o fuso habita; mudança de exercício sinalizada, fuso do servidor nunca lido",
        "text_fold_report":
            "quais reducoes de acentos ou caixa APAGAM uma identidade distinta — relatado, nomeado; o dobramento em si fica com o chamador",
        "text_novel_words":
            "descricao contra titulo: palavras novas contadas por item, feeds eco nomeados, limite dito (padrao 3)",
        "date_window":
            "limites de uma cláusula (min..max dias antes/depois de um evento) → a janela INCLUSIVE inteira, span e sentido ditos; limites invertidas recusadas por nome (não se reordena um contrato)",
        "date_deemed":
            "data de envio + modo de envio → recebimento reputado; sem modo, sem data (tabela fechada nomeada, override por argumento declarado)",
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
            "quanto custa A SUA lista MCP colada, medida em bytes e tokens (estimador publicado chars÷4, piso declarado), por ferramenta e campo — contrafactual names-only cifrado, conta POR TURNO, dólares se VOCÊ trouxer o preço; mcp-audit diz REJEITADO, mcp-surface diz MUDOU, aqui se diz QUANTO",
        "shop_gift_voucher":
            "vale-presente « vencido » de um ano é SUBSTITUÍDO por cinco anos desde a compra — a data legal COBRE o papel (Lei irlandesa de 2019 rejogada, forma JD Sports); saldo de €1 ou mais é devido, fronteira €1 com conflito NOMEADO; França NEGATIVA: nenhuma duração legal, o boato dos « 30 anos » é imobiliário, recusado por nome",
        "shop_soldes_window":
            "as datas legais dos saldos na França vêm do arrêté de 27 de maio de 2019 rejogado: cláusulas de antecipação nas duas estações (2027: 6 de janeiro, não 13; 23 de junho, não 30), sete derrogações anuais com o texto — inverno 2021 em SEIS SEMANAS, Mosela sozinha a 26 de junho de 2021 — anexo versionado; antes de 2020 e fora da França, recusado por nome",
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
            "rateio exato antes do arredondamento final",
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
            "Hora do relógio + fuso → single | fold | gap : as horas que não existem (spring forward) ou que existem DUAS VEZES (fall back), cada instante UTC nomeado com offset e abreviação, a regra PEP 495 declarada, os vizinhos do buraco exibidos — o veredicto que date/tz aplica em silêncio, cron_next não sinaliza",
        "date_tz_anchor":
            "Uma hora do relógio ESCRITA no fuso do job, ANCORADA pela máquina no seu fuso: cada instante UTC candidato, o desvio ASSINADO em minutos (positivo = atrasado), os dois relógios relidos; o offset vence (resolução Composio #4148); single/fold/gap exibidos pelo engine date/tz_ambiguity CHAMADO, nunca duplicado",
        "money_flight_comp":
            "Data do voo = TABELA de compensação: 261/2004 + Sturgeon/Nelson antes de 2027-10-23, (UE) 2026/2202 codificado DEPOIS (limiar “EXCEEDING 3 h” ESTRITO, 180 min exatos não pagam), UK261 £220/350/520 com a linha oficial £260 abaixo de 4 h, teto intra-UE €400 nomeado, reduções = opções “a transportadora PODE”, prescrição 9 meses em data exata, zero fetch",
        "date_week":
            "Semana ISO ida e volta — ano ISO SEPARADO do %Y, W53 PELO TEOREMA (53 quintas-feiras ⟺ Jan-1 quinta-feira, ou quarta-feira + bissexto; zero tabela), semana inexistente recusada com o artefato %Y-W%V nomeado, convenções Excel/US (%U %W WEEKNUM) lado a lado, notas PostgreSQL/Snowflake",
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
            "dígitos verificadores: ISBN/EAN/GTIN/ISIN/LEI… verificar, reparar, escanear",
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
            "feriados legais FR BR PT DE US com a lei citada em cada linha",
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
            "Data do voo = faixa da LEI (40×30×15 sob o assento GRÁTIS desde 2027-10-23, NADA antes — cada companhia decide); compartimento superior: a lei não fixa NENHUM tamanho; gabaritos da transportadora COMO ARGUMENTOS, nunca fetchados; ajuste POR DIMENSÃO com ROTAÇÃO (40×18×30 cabe em 40×30×20); o «total 100 cm / 7 kg» da imprensa apresentado como afirmação TESTADA (55+40+20=115), nunca como regra",
        "csv_excel_damage":
            "O que o Excel DESTRÓI no duplo clique, PREDITO antes: zeros à esquerda (02134→2134), muro dos 15 dígitos (…1111→…1110), notação científica (1E5→100000), datas forçadas (SEPT2, MARCH1, « 3-4 » = 4 de março EN / 3 de abril EU — locale como ARGUMENTO, ano travado por as_of), formas de fórmula (=-+@), largura total; regras = os três interruptores da Microsoft nomeados; importação Texto para Colunas PRESCRITA; csv/fix conserta, aqui se PREDIT",
        "money_crossover":
            "Preço de custo de DUAS tabelas com componentes (unitário + fixo): a virada em FRAÇÃO EXATA — as sete calculadoras arredondam o Δ fixo antes de dividir e se contradizem; convenções de dias NOMEADAS (mensal ×12 exato, nunca 30 dias; diário ×365 ou 366 bissexto fornecido; «semana» recusada); DOMINAÇÃO entregue como «never» nomeado; km se o consumo for FORNECIDO; taxas one-off em meses de payback, separadas da virada estrutural",
        "money_points":
            "Quanto vale um PONTO: cpp = (preço cash - resto cash - rewards forgoes) / pontos x 100 em FRAÇÃO EXATA (1081/725 onde a imprensa diz 1.49); vias lado a lado, ordenadas, igualdades nomeadas, veredito contra FLOOR fornecido, saldo x cpp, retorno efetivo pts/$ x cpp; nunca tabela de valoração embarcada",
        "csv_excel_display":
            "O que o Excel EXIBE de um valor ARMAZENADO sob um código numFmt: a vírgula trailing ESCALA por mil (« $#,##0, » + 1 000 000 → $1,000 — o ataque medido arXiv 2611.05806, seis extratores python cegos); exemplos da tabela Microsoft reproduzidos (« #.0,, »→12.2, « (000) »→(012), « 0% »→50%); arredondamento de display meio-para-fora dito; locale como ARGUMENTO (os separadores do arquivo são símbolos — engenheiro da Microsoft); General/datas/cores recusados PELO NOME; renderização de estilo, a predição de importação é outra rota",
        "ship_dimweight":
            "O peso REALMENTE cobrado do pacote: dimensões arredondadas PARA A POLEGADA SUPERIOR antes do volume, volume ÷ divisor (a unidade é DECLARADA — a pegadinha mm÷139 x16,4 fica impossível), max(real, dimensional), ceil na faixa, teto. rollo 35 lb vs amzprep 34,5 nas MESMAS polegadas: a fração exata 4800/139 resolve e cada etapa é nomeada; tabelas da transportadora COMO ARGUMENTOS (USPS 166→139 em 12-jul-2026 = elas apodrecem)",
        "json_coerce":
            "Conserta os ARGUMENTOS de uma chamada de ferramenta que um leitor RÍGIDO recusa: 8.0→8 (classe serde « invalid type: floating point 2500.0, expected u64 », 11/11 rodadas medidas), exponentes e frações reais deixados TAIS QUAIS, 'false' em string recusado PELO NOME (pegadinha truthy), string→number só se cast_strings=on, '007' NUNCA (zeros à esquerda são payload), chaves duplicadas recusadas; a notação original é CONSERVADA na saída",
        "money_bogo":
            "A porcentagem que o CAIXA realmente aplica sob uma placa « BUY ONE GET ONE 50 % »: o desconto incide sobre o MAIS BARATO dos dois (regra de varejo publicada — 60+40 vira 80 em 100, ou seja, 20 %, nem 25 nem 50), preços iguais = 25 % do par NUNCA 50, o item ímpar se paga CHEIO (os pares são DADOS, nunca adivinhados), o cupom se EMPILHA como produto de fatores (25 depois 30 = 47,5, nunca 55); rastro por par, fração exata ao lado do exibido",
        "agent_modelid":
            "audita ids de modelo contra um catálogo colado — vereditos nomeados, did-you-mean a uma distância nomeada, nunca jura que fez o GET (V23)",
        "food_poultry":
            "janela de descongelar e assar o peru, tabelas USDA FSIS, relógio ISO como argumento — nunca relógio de parede, nunca números inventados",
        "food_leftovers":
            "janela das sobras, USDA FSIS: limite 2h, 3-4 dias na geladeira, 2-6 meses no congelador (UNIÃO das duas páginas FSIS que se contradizem) — todos os tempos como ARGUMENTOS, nunca relógio de parede, nunca tabelas inventadas",
        "food_ovenschedule":
            "um forno, vários pratos, um horário de servir: contagem regressiva de trás para frente, conflitos de temperatura nomeados, nunca relógio de parede — as timelines da web não verificam nada disso",
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
              "\u00a3350/\u00a3520 under UK261 \u00b7 same flight date, "
              "old rules: a different answer",
      "bag": "\u2192 %s under the seat by the 2027 LAW \u00b7 carrier "
             "gauge 40\u00d730\u00d720: %s once faces are sorted \u00b7 "
             "overhead: the law sets NO size",
      "cross": "\u2192 the two tariffs flip at %s kWh a month (%s a "
               "year) \u00b7 exact \u2014 web calculators round the "
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
           "rec": "\u2192 keep until %s \u00b7 shred from %s \u00b7 the official 2022-23 example, replayed",
           "vouch": "\u2192 the law reads ALIVE to %s \u00b7 %s days left "
                    "\u00b7 the printed date had stolen %s \u2014 Act "
                    "2019 overrides the paper",
           "window": "\u2192 winter 2027 opens %s at 8 h \u00b7 the "
                     "second Wednesday (%s) fell after the 12th: "
                     "ADVANCED \u00b7 %s days to go"},
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
      "shoe": "→ %s mm exatos · posição EU %s — meia grade %s, "
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
      "leftovers": "\u2192 replay thanksgiving 2026: comer at\u00e9 %s "
                   "\u00b7 banda %s",
      "ovenschedule": "\u2192 forno ligado %s, peru de fora %s · "
                      "conflitos de temperatura: %d — nenhum "
                      "cronograma avisa isso",
      "deadline": "\u2192 \u00faltimo envio %s (%s) \u00b7 a fonte divergente publica %s \u2014 nomeada, nunca m\u00e9dia"},
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
    ("/api/v1/food/leftovers",
     {"category": "turkey", "cooked_at": "2026-11-26T17:00",
      "stored_at": "2026-11-26T19:00", "as_of": "2026-11-30"},
     "leftovers", lambda d, L_: (
         d["fridge"]["last_day"], d["as_of"]["band"])),
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
        chips.append('<span class="chip" data-f="tier=%s" title="%s %s — %s">'
                     '%s %s</span>'
                     % (t, BADGE[t], word, TIER_RULE[lang][t], BADGE[t], word))
    legend = " · ".join('<span class="lg">%s %s — %s</span>'
                        % (BADGE[t], TIER_CHIP[lang][t], TIER_RULE[lang][t])
                        for t in ("free", "cap", "paid"))
    cards = []
    for name, path, pack, purpose, tags in routing.TABLE:
        tier = path_tier[name]
        hay = " ".join((name, purpose, tags)).lower()
        hay = hay.replace("&", "&amp;").replace('"', "&quot;")
        purp = PURPOSES.get(lang, {}).get(name, purpose)
        purp = purp.replace("&", "&amp;").replace("<", "&lt;")
        cards.append(
            '<button class="tcard" data-pack="%s" data-tier="%s" '
            'data-top="%s" data-tool="%s" data-hay="%s"><span class="tierdot" '
            'title="%s %s — %s">%s'
            '</span> <code>%s</code><span class="tp">%s</span></button>'
            % (pack, tier, "1" if name in TOP10 else "0", name, hay, BADGE[tier], TIER_CHIP[lang][tier],
               TIER_RULE[lang][tier], BADGE[tier], name, purp))
    packs = " · ".join('<a href="/SKILL-%s.md">%s</a>' % (pk, pk)
                       for pk in routing.PACKS)
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
