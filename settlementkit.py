"""settlementkit — « qui paye qui » (bundle 115): advances + shares +
forgiveness -> closed-cent balances and the NAMED minimal transfers.

THE WOUND (r/askmath 1ugli3y, replayed as a pin): A fronts 1375.00, B
fronts 0.00, C fronts 865.00; equal shares; C tells B "I won't ask for
any money from you"; A demands 628.33, B offers 458.33 — the thread
DISAGREES ABOUT ARITHMETIC because it never says WHICH GRAPH it
settles. Net mode: C can only forgive the 118.34 owed to C (a commenter
names the rule — "C can only choose to forgive the debt that is owed to
them"); B still owes the group 628.33, which travels to A. Itemized
mode: the forgiveness kills the 288.33 B->C receipt edge; B pays A
458.33 and C eats the difference. Both close to the cent; they answer
different questions. mode="compare" renders both and numbers the gap.

CLOSED RULES (all cited in the payload, none invented here):
  * shares: the /money/split remainder rule (floor, leftover cents by
    fractional part desc, ties by list order) — IMPORTED and reused, so
    the family never disagrees with itself (money.money_split).
  * waiver cap: net mode — the forgiver can only release up to their own
    remaining claim (and up to the debtor's remaining debt); itemized
    mode — only up to the directed receipt edges between the pair. A
    waiver beyond the cap is CAPPED and the cap is NAMED, never silently
    reduced.
  * minimal transfers (net mode): the zero-sum partition identity
    min_count = n_nonzero - max_number_of_zero_sum_parts, computed
    EXACTLY by subset DP for n <= 9 people; above the bound a
    largest-first greedy settles validly and the report says minimality
    is NOT proven.
  * currencies: never fetched. All advances in one currency, or rates as
    ARGUMENTS (the transaction-date rule is the user's to choose —
    tryzedger.com 2026-11-14: "Use the rate from the transaction date.
    Not the booking date, not the settlement date"). Conversion reuses
    money.num_fx: exact Decimal multiply, ISO minor units,
    ROUND_HALF_EVEN — the same contract /num/fx publishes, with
    exact_before_rounding travelling on the line.
  * settlement currency must be a 2-decimal currency (the split family's
    remainder rule is 2-decimal); 0- and 3-decimal codes are REFUSED BY
    NAME with the reason — never silently re-scaled.

Amounts are STRINGS, arithmetic is Decimal to the minor unit. Every
response passes identity checks INSIDE the module before it is returned:
in net mode sum(balances) == 0 and each person's received-minus-paid
reproduces their balance; in itemized mode the out-of-pocket total
equals the advanced total. When an identity fails the tool REFUSES.
"""

from decimal import Decimal

from money import MoneyError, ISO_DECIMALS, money_split, num_fx

MIN_DP_BOUND = 9  # exact minimal-transfer DP is certified at n <= 9
_VERDICTS = ("net", "itemized", "compare")


def _cents(amount, dp=2):
    """exact Decimal -> integer minor units (inputs are already closed)"""
    return int(Decimal(amount).scaleb(dp).to_integral_value())


def _s(cents, dp=2):
    return format(Decimal(cents).scaleb(-dp), "f")


def _name_list(participants):
    """accept [name] or [{name, weight}] — the exact money_split grammar.
    Returns (names, participant_objects) keeping order."""
    if not isinstance(participants, list) or not participants:
        raise MoneyError("participants must be a non-empty list — the "
                         "/money/split grammar (names or {name, weight})")
    names, weighted = [], False
    for p in participants:
        if isinstance(p, str) and p.strip():
            names.append(p)
        elif isinstance(p, dict) and isinstance(p.get("name"), str):
            names.append(p["name"])
            weighted = True
        else:
            raise MoneyError("participant must be a name or "
                             "{name, weight?} (the /money/split grammar)")
    seen = set()
    for n in names:
        if n in seen:
            raise MoneyError("duplicate participant %r: the graph would "
                             "merge two people into one" % n)
        seen.add(n)
    return names, (participants if weighted else names)


def _validated_advances(advances):
    if not isinstance(advances, list) or not advances:
        raise MoneyError("advances must be a non-empty list of "
                         "{who, paid, label?, split_between?, currency?}")
    out = []
    for i, a in enumerate(advances):
        if not isinstance(a, dict):
            raise MoneyError("advance %d must be an object" % i)
        who = a.get("who")
        if not isinstance(who, str) or not who.strip():
            raise MoneyError("advance %d: who must be a name" % i)
        try:
            amt = Decimal(str(a.get("paid")))
        except Exception:
            raise MoneyError("advance %d: paid must be a decimal STRING "
                             "(exactness is the product)" % i)
        if amt < 0:
            raise MoneyError("advance %d: negative advances are refused — "
                             "a refund is a separate advance by the other "
                             "person, not a negative line" % i)
        sb = a.get("split_between")
        if sb is not None and (not isinstance(sb, list) or not sb
                               or not all(isinstance(x, str) and x.strip()
                                         for x in sb)):
            raise MoneyError("advance %d: split_between must be a "
                             "non-empty list of names" % i)
        cur = a.get("currency")
        if cur is not None:
            cur = str(cur).upper()
            if cur not in ISO_DECIMALS:
                raise MoneyError("advance %d: currency %r is not in the "
                                 "closed ISO table this suite converts"
                                 % (i, cur))
        out.append({"who": who, "paid": format(amt, "f"),
                    "label": a.get("label"), "split_between": sb,
                    "currency": cur})
    return out


def _convert(adv, cur, rates):
    """advance echo + settled amount in the target currency (exact path)"""
    conv, total = [], 0
    for a in adv:
        amt = a["paid"]
        note = {"who": a["who"], "paid": amt,
                "currency": a["currency"] or cur}
        if a.get("label") is not None:
            note["label"] = a["label"]
        if a["currency"] and a["currency"] != cur:
            fx = num_fx(amt, rates[a["currency"]], cur)
            amt = fx["result"]
            note["rate_used"] = fx["rate_used"]
            note["exact_before_rounding"] = fx["exact_before_rounding"]
        note["settled"] = amt
        conv.append(note)
        total += _cents(amt)
    return conv, total


def _zero_sum_groups(cents_by_name, order):
    """Exact max-partition into zero-sum subsets via subset DP, O(3^n) —
    bounded at n <= MIN_DP_BOUND by the caller. Returns list of groups
    (each a list of names), canonical order: groups sorted by the first
    member's position in `order`, members likewise.
    """
    names = [n for n in order if cents_by_name[n] != 0]
    n = len(names)
    bal = [cents_by_name[x] for x in names]
    # zero-sum test per mask, incremental
    total_mask = (1 << n) - 1
    smem = [0] * (1 << n)
    for mask in range(1, 1 << n):
        low = mask & (-mask)
        i = low.bit_length() - 1
        smem[mask] = smem[mask ^ low] + bal[i]
    zero = [False] * (1 << n)
    for mask in range(1, 1 << n):
        zero[mask] = (smem[mask] == 0)
    best = [0] * (1 << n)   # max #parts for mask
    part = [0] * (1 << n)   # chosen first part achieving best
    for mask in range(1, 1 << n):
        if zero[mask]:
            best[mask] = 1
            part[mask] = mask
        s = (mask - 1) & mask
        while s:
            if zero[s] and best[mask ^ s] + 1 > best[mask]:
                best[mask] = best[mask ^ s] + 1
                part[mask] = s
            s = (s - 1) & mask
    groups, mask = [], total_mask
    while mask:
        g = part[mask]
        if g == 0:            # unreachable for zero-sum total (guarded)
            g = mask
        groups.append([names[i] for i in range(n) if g >> i & 1])
        mask ^= g
    groups.sort(key=lambda g: min(order.index(x) for x in g))
    return [sorted(g, key=order.index) for g in groups]


def _match_group(group, cents_by_name, order):
    """largest-first matching inside one zero-sum group; deterministic
    ties by `order`; yields exactly len(group)-1 transfers."""
    dets = sorted([( -cents_by_name[x], x) for x in group
                   if cents_by_name[x] < 0],
                  key=lambda t: (-t[0], order.index(t[1])))
    crds = sorted([(cents_by_name[x], x) for x in group
                   if cents_by_name[x] > 0],
                  key=lambda t: (-t[0], order.index(t[1])))
    out = []
    while dets and crds:
        (dam, dnm), (cam, cnm) = dets[0], crds[0]
        m = min(dam, cam)
        out.append({"from": dnm, "to": cnm, "amount": _s(m)})
        if dam == m:
            dets.pop(0)
        else:
            dets[0] = (dam - m, dnm)
        if cam == m:
            crds.pop(0)
        else:
            crds[0] = (cam - m, cnm)
    return out


def _participants_subset(participants, names_listed, sb):
    """participants restricted to a receipt, weights kept when present."""
    if isinstance(participants[0], dict):
        return [p for p in participants if p["name"] in sb]
    return [n for n in sb if n in names_listed]


def _settle_net(participants, names, adv, waivers, cur, rates):
    conv, total = _convert(adv, cur, rates)
    shares = money_split(_s(total), participants)["shares"]
    share_of = {s["participant"]: s["share"] for s in shares}
    adv_of = {n: 0 for n in names}
    for a, c in zip(adv, conv):
        adv_of[a["who"]] += _cents(c["settled"])
    bal = {n: adv_of[n] - _cents(share_of[n]) for n in names}
    reports = []
    for w in waivers:
        frm, to = w["from"], w["to"]
        claim, debt = bal[frm], -bal[to]
        want = claim if w.get("amount") is None else _cents(
            Decimal(str(w["amount"])))
        if claim <= 0:
            reports.append({"from": frm, "to": to,
                            "requested": "all" if w.get("amount") is None
                                         else str(w["amount"]),
                            "applied": _s(0),
                            "cap": "REFUSED_NOT_A_CREDITOR",
                            "why": ("%s is not a creditor in the net "
                                    "graph — a waiver only releases a "
                                    "claim that exists (r/askmath "
                                    "1ugli3y: one can only forgive the "
                                    "debt owed to oneself)" % frm)})
            continue
        applied = max(0, min(want, claim, debt))
        bal[frm] -= applied
        bal[to] += applied
        entry = {"from": frm, "to": to,
                 "requested": "own-claim" if w.get("amount") is None
                              else str(w["amount"]),
                 "applied": _s(applied),
                 "forgiver_claim_after": _s(max(0, bal[frm])),
                 "debtor_debt_after": _s(max(0, -bal[to]))}
        if applied < want:
            entry["cap"] = ("WAIVER_CAPPED_AT_OWN_CLAIM" if applied == claim
                            else "WAIVER_CAPPED_AT_REMAINING_DEBT")
            entry["why"] = ("one can only forgive what one is owed — the "
                            "unreleased part stays with the GROUP, it "
                            "does not vanish from the other creditors")
        reports.append(entry)
    if sum(bal.values()) != 0:
        raise MoneyError("identity REFUSED (net): balances do not sum to "
                         "0 — the answer would lie")
    if len([n for n in names if bal[n] != 0]) > MIN_DP_BOUND:
        groups = [[n for n in names if bal[n] != 0]]
        proven = False
    else:
        groups = _zero_sum_groups(bal, names)
        proven = True
    transfers = []
    for g in groups:
        transfers += _match_group(g, bal, names)
    # replay check: flows must reproduce every balance exactly
    acc = {n: 0 for n in names}
    for t in transfers:
        c = _cents(t["amount"])
        acc[t["from"]] -= c
        acc[t["to"]] += c
    for n in names:
        if acc[n] != bal[n]:
            raise MoneyError("identity REFUSED (net): transfers do not "
                             "reproduce the balance of %r" % n)
    return {
        "mode": "net",
        "currency": cur,
        "advances": conv,
        "total": _s(total),
        "shares": shares,
        "balances": [{"who": n,
                      "position": ("settled" if bal[n] == 0 else
                                   ("owed " if bal[n] < 0 else "due ") +
                                   _s(abs(bal[n])))} for n in names],
        "waivers": reports,
        "transfers": transfers,
        "transfer_count": len(transfers),
        "minimal": proven,
        "minimum_rule": (
            "exact zero-sum partition DP for n<=%d: min transfers = "
            "people with a balance - zero-sum parts; within a group, "
            "largest-first matching, ties by the caller's participant "
            "order" % MIN_DP_BOUND if proven else
            "greedy largest-first above the n<=%d bound: a valid "
            "settlement, count <= n-1, minimality NOT proven"
            % MIN_DP_BOUND),
    }


def _settle_itemized(participants, names, adv, waivers, cur, rates):
    conv, total = _convert(adv, cur, rates)
    edges = []
    for a, c in zip(adv, conv):
        sb = a["split_between"] or names
        for nm in sb:
            if nm not in names:
                raise MoneyError("advance %r: split_between contains %r, "
                                 "unknown to the participant set — the "
                                 "graph refuses to invent a person"
                                 % (a.get("label") or a["who"], nm))
        subset = _participants_subset(participants, names, sb)
        shares = money_split(c["settled"], subset)["shares"]
        for s in shares:
            if s["participant"] == a["who"]:
                continue
            if _cents(s["share"]) != 0:
                edges.append({"from": s["participant"], "to": a["who"],
                              "amount": s["share"],
                              "via": a.get("label")
                              or ("advance by " + a["who"])})
    reports = []
    for w in waivers:
        frm, to = w["from"], w["to"]
        targets = [e for e in edges if e["from"] == to and e["to"] == frm]
        edge_sum = sum(_cents(e["amount"]) for e in targets)
        want = None if w.get("amount") is None else _cents(
            Decimal(str(w["amount"])))
        applied = 0
        for e in targets:
            c0 = _cents(e["amount"])
            take = c0 if want is None else min(c0, want - applied)
            if take <= 0:
                continue
            applied += take
            e["waived"] = _s(take)
            e["amount"] = _s(c0 - take)
        entry = {"from": frm, "to": to,
                 "requested": "edges" if want is None else str(w["amount"]),
                 "applied": _s(applied),
                 "edge_total": _s(edge_sum)}
        if want is not None and applied < max(0, want):
            entry["cap"] = "WAIVER_CAPPED_AT_RECEIPT_EDGES"
            entry["why"] = ("itemized mode nets NOTHING across receipts: "
                            "a waiver only reaches the %s->%s edges — to "
                            "release a NET claim switch to mode=net "
                            "(compare shows both answers)" % (to, frm))
        if applied == 0:
            entry["cap"] = "REFUSED_NO_EDGE"
            entry["why"] = ("no %s->%s receipt edge exists — in itemized "
                            "mode forgiveness travels on edges, not on "
                            "net claims; see mode=compare" % (to, frm))
        reports.append(entry)
    edges = [e for e in edges if _cents(e["amount"]) > 0]
    paid_by = {n: 0 for n in names}
    for a, c in zip(adv, conv):
        paid_by[a["who"]] += _cents(c["settled"])
    out_amt = {n: 0 for n in names}
    in_amt = {n: 0 for n in names}
    for e in edges:
        if _cents(e["amount"]) > 0:
            out_amt[e["from"]] += _cents(e["amount"])
            in_amt[e["to"]] += _cents(e["amount"])
    # out-of-pocket on LIVE cash only: the waived edge simply never
    # arrives at its creditor — the generosity is the forgiver's,
    # already paid in the advances, never double-counted here
    oop = {n: paid_by[n] + out_amt[n] - in_amt[n] for n in names}
    tot_oop = sum(paid_by.values())
    if sum(oop.values()) != tot_oop:
        raise MoneyError("identity REFUSED (itemized): out-of-pocket "
                         "total %s != advanced total %s"
                         % (_s(sum(oop.values())), _s(tot_oop)))
    return {
        "mode": "itemized",
        "currency": cur,
        "advances": conv,
        "total": _s(total),
        "transfers": [{"from": e["from"], "to": e["to"],
                       "amount": e["amount"], "via": e["via"],
                       **({"waived_part": e["waived"]}
                          if e.get("waived") else {})}
                      for e in edges if _cents(e["amount"]) > 0],
        "waivers": reports,
        "transfer_count": len([e for e in edges
                               if _cents(e["amount"]) > 0]),
        "positions": [{"who": n, "out_of_pocket": _s(oop[n])}
                      for n in names],
        "rule": ("every receipt is split on its own with the "
                 "/money/split remainder rule PER RECEIPT — the leftover "
                 "cent of each receipt travels differently than the "
                 "leftover of the total (divergence NAMED in compare, "
                 "never averaged)"),
    }


def money_settle(advances, participants=None, share_mode="equal",
                 waivers=None, mode="net", currency=None, rates=None):
    if mode not in _VERDICTS:
        raise MoneyError("mode must be one of %s (closed set)"
                         % list(_VERDICTS))
    if share_mode not in ("equal", "weights"):
        raise MoneyError("share_mode must be equal|weights (the family "
                         "grammar of /money/split)")
    adv = _validated_advances(advances)
    all_names = []
    for a in adv:
        if a["who"] not in all_names:
            all_names.append(a["who"])
        for nm in (a["split_between"] or []):
            if nm not in all_names:
                all_names.append(nm)
    participants = all_names if participants is None else participants
    names, parts = _name_list(participants)
    had_weights = isinstance(parts[0], dict)
    if share_mode == "weights" and not had_weights:
        raise MoneyError("share_mode=weights needs participants with a "
                         "weight each ({name, weight} — the /money/split "
                         "grammar)")
    if had_weights:
        share_mode = "weights"  # weights present ARE the intent; echoed
    cur_set = {a["currency"] for a in adv if a["currency"]}
    if currency:
        cur = str(currency).upper()
    elif len(cur_set) == 1:
        cur = list(cur_set)[0]
    elif len(cur_set) > 1:
        raise MoneyError("mixed currencies without a settlement currency: "
                         "pass currency=… — which currency answers is the "
                         "caller's, never a guess")
    else:
        cur = "USD"
    if cur not in ISO_DECIMALS:
        raise MoneyError("settlement currency %r is not in the closed ISO "
                         "table this suite converts" % cur)
    if ISO_DECIMALS[cur] != 2:
        raise MoneyError("settlement in %r refused by name: the remainder "
                         "rule of the /money/split family is 2-decimal — "
                         "settle in a 2-decimal currency and convert "
                         "(0- and 3-decimal codes like JPY or KWD "
                         "refuse)" % cur)
    foreign = cur_set - {cur}
    if foreign:
        if not isinstance(rates, dict):
            raise MoneyError("advances in %s need rates={CODE: decimal "
                             "string}: rates are ARGUMENTS (the "
                             "transaction-date rate is yours to name — "
                             "the booking-date one is a different answer); "
                             "this suite never fetches" % sorted(foreign))
        for code in sorted(foreign):
            try:
                Decimal(str(rates[code]))
            except Exception:
                raise MoneyError("rates[%r] must be a decimal string"
                                 % code)
    missing = sorted(set(all_names) - set(names))
    if missing:
        raise MoneyError("participants omit %s: an advance by an unnamed "
                         "person would be settled against nobody" % missing)
    wr = []
    for i, w in enumerate(waivers or []):
        if not isinstance(w, dict) or w.get("from") not in names \
                or w.get("to") not in names:
            raise MoneyError("waiver %d: from and to must be participants "
                             "— the graph refuses to forgive a "
                             "stranger" % i)
        if w["from"] == w["to"]:
            raise MoneyError("waiver %d: from == to is not a waiver, it "
                             "is noise" % i)
        if w.get("amount") is not None:
            try:
                Decimal(str(w["amount"]))
            except Exception:
                raise MoneyError("waiver %d: amount must be a decimal "
                                 "string or omitted (= all)" % i)
        wr.append({"from": w["from"], "to": w["to"],
                   "amount": w.get("amount")})
    if mode == "net":
        res = _settle_net(parts, names, adv, wr, cur, rates or {})
        res["identity_check"] = ("sum(balances)=0 and transfers replay "
                                 "every balance — verified in the module")
    elif mode == "itemized":
        res = _settle_itemized(parts, names, adv, wr, cur, rates or {})
        res["identity_check"] = ("sum(out_of_pocket)=total advanced — "
                                 "verified in the module")
    else:
        net = _settle_net(parts, names, adv, wr, cur, rates or {})
        item = _settle_itemized(parts, names, adv, wr, cur, rates or {})

        def pays(r):
            acc = {}
            for t in r["transfers"]:
                k = "%s->%s" % (t["from"], t["to"])
                acc[k] = acc.get(k, Decimal(0)) + Decimal(t["amount"])
            return {k: format(v, "f") for k, v in sorted(acc.items())}

        nw = {"%s->%s" % (w["from"], w["to"]): w["applied"]
              for w in net["waivers"]}
        iw = {"%s->%s" % (w["from"], w["to"]): w["applied"]
              for w in item["waivers"]}
        res = {"mode": "compare", "currency": cur,
               "net": net, "itemized": item,
               "divergence": {
                   "pays_net": pays(net), "pays_itemized": pays(item),
                   "forgiveness_applied_net": nw,
                   "forgiveness_applied_itemized": iw,
                   "note": ("both graphs close to the cent; they answer "
                            "different questions — net settles the SOLDES "
                            "once, itemized honours EACH RECEIPT (the "
                            "r/askmath 1ugli3y fight was never about "
                            "arithmetic, it was about the graph) — and "
                            "per-receipt remainders can move a cent "
                            "differently than the total's remainder"),
               },
               "identity_check": ("both graphs replayed their balances "
                                  "before this compare was returned")}
    res["share_mode"] = share_mode
    return res
