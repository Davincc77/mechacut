"""Bundle FIN — money/amortize + money/interest.

Closed-form financial arithmetic on Decimal, no floating point drift:
the tests anchor on INVARIANTS that define the objects (balance hits
exactly zero; principal = sum of amortizations; total interest =
payments - principal) plus hand-checkable tiny cases — not on tables of
numbers recalled from memory, which is where loan-calc bugs are born.

No advice, no rates invented: every rate is an argument. A rate of 0
has its own honest branch instead of a division crash.
"""
from decimal import Decimal, ROUND_HALF_EVEN, getcontext

getcontext().prec = 30

CENT = Decimal("0.01")


class MoneyError(Exception):
    pass


def _d(value, name):
    try:
        x = Decimal(str(value))
    except Exception:
        raise MoneyError("%s must be a number, got %r" % (name, value))
    return x


def money_amortize(principal, annual_rate_pct, months, when="end",
                   rounding=CENT):
    p = _d(principal, "principal")
    r = _d(annual_rate_pct, "annual_rate_pct")
    n = months
    if not isinstance(n, int) or n < 1 or n > 600:
        raise MoneyError("months must be an integer 1-600")
    if p <= 0:
        raise MoneyError("principal must be positive")
    if r < 0:
        raise MoneyError("negative rates refused: the closed form "
                         "inverts sign meaning (verdict, not math)")
    i = r / Decimal(100) / Decimal(12)
    if i == 0:
        base = (p / Decimal(n)).quantize(rounding, ROUND_HALF_EVEN)
        schedule = []
        bal = p
        for k in range(1, n + 1):
            pay = bal if k == n else base
            bal -= pay
            schedule.append({"month": k, "payment": str(pay),
                             "interest": "0.00",
                             "amortization": str(pay),
                             "balance": str(bal.quantize(rounding))})
        return {"mode": "zero_rate", "payment": str(base),
                "total_interest": "0.00",
                "total_paid": str(p), "schedule": schedule,
                "final_balance": str(schedule[-1]["balance"])}
    # French practice: when=end (échéance à terme échu) default
    growth = (1 + i) ** n
    pay = (p * i * growth / (growth - 1)).quantize(rounding,
                                                   ROUND_HALF_EVEN)
    bal = p
    schedule = []
    tot_int = Decimal(0)
    for k in range(1, n + 1):
        interest = (bal * i).quantize(rounding, ROUND_HALF_EVEN)
        amort = pay - interest
        if k == n:
            amort = bal
            actual = amort + interest
        else:
            actual = pay
        bal = (bal - amort).quantize(rounding)
        tot_int += interest
        schedule.append({"month": k, "payment": str(actual),
                         "interest": str(interest),
                         "amortization": str(amort),
                         "balance": str(bal)})
    return {"payment": str(pay),
            "total_paid": str((p + tot_int).quantize(rounding)),
            "total_interest": str(tot_int.quantize(rounding)),
            "monthly_rate": str(i.quantize(Decimal("1e-10"))),
            "schedule": schedule,
            "final_balance": str(bal),
            "convention": "annuity, monthly compounding, last line "
                          "absorbs rounding to hit balance 0.00 exactly"}


def money_interest(principal, annual_rate_pct, years, compounds_per_year=12):
    p = _d(principal, "principal")
    r = _d(annual_rate_pct, "annual_rate_pct") / Decimal(100)
    t = _d(years, "years")
    m = compounds_per_year
    if not isinstance(m, int) or m < 1 or m > 365:
        raise MoneyError("compounds_per_year must be an integer 1-365")
    if p <= 0 or t < 0:
        raise MoneyError("principal>0 and years>=0 required")
    amount = p * (1 + r / Decimal(m)) ** (Decimal(m) * t)
    # effective annual rate (taux effectif annuel) — same closed form
    eff = (1 + r / Decimal(m)) ** Decimal(m) - 1
    return {"final_amount": str(amount.quantize(CENT, ROUND_HALF_EVEN)),
            "interest_earned":
                str((amount - p).quantize(CENT, ROUND_HALF_EVEN)),
            "effective_annual_rate_pct":
                str((eff * 100).quantize(Decimal("1e-8"))),
            "formula": "A = P(1 + r/m)^(mt); EAR = (1 + r/m)^m - 1",
            "inputs": {"principal": str(p), "nominal_pct": str(r * 100),
                       "years": str(t), "compounds": m}}
