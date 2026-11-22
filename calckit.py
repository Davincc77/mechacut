"""calckit — /api/v1/math/calc : la calculatrice fermée.

Un modèle écrit « 7834*9217 » et DOIT ressortir le produit — donc il le
fabrique. Ici le modèle (ou l'humain) ÉCRIT l'expression, la machine
COMPTE : AST Python fermé, Decimal exact, zéro eval, zéro nom, zéro
attribut, zéro import — tout le reste est refusé PAR LE NOM.

Fermé, ça veut dire :
  opérateurs   +  -  *  /  //  %  **   (parenthèses, unaire ±)
  fonctions    round(x[, n])  sqrt(x)  abs(x)
  nombres      entiers et décimaux pris TELS QU'ÉCRITS (texte source
               du littéral, jamais le binaire float) : 0.1+0.2 = 0.3
  rounding     round()/digits = HALF_UP, déclaré dans chaque réponse
  refus        lettre inconnue, nom, attribut, index, comparaison,
               lambda, guillemets, exposant > 64, nombre 1000+ chiffres

Aucun état module : tout est passé en paramètre (threads FastAPI).
C'est le socle du catalogue de formules (catalogue de formules) : une formule
= une substitution dans expr. Le produit calcule, le modèle relit.
"""
import ast
import re
from decimal import (Decimal, InvalidOperation, ROUND_HALF_UP,
                     localcontext)

MAX_EXPR = 512
MAX_DIGITS = 1000
MAX_EXP = 64

OPS = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
       ast.FloorDiv: "//", ast.Mod: "%", ast.Pow: "**"}
FUNCS = {"round", "sqrt", "abs"}


class CalcError(Exception):
    pass


def _num_text(source, node):
    """Texte brut du littéral — la virgule flottante binaire du
    parseur ne doit JAMAIS toucher la valeur."""
    t = source[node.col_offset:node.end_col_offset]
    if not re.fullmatch(r"\d+(\.\d+)?", t):
        raise CalcError("numbers only, written plainly")
    if len(t.replace(".", "").lstrip("0")) > MAX_DIGITS:
        raise CalcError("number over %d digits — refused" % MAX_DIGITS)
    try:
        return Decimal(t)
    except InvalidOperation:
        raise CalcError("bad number %r" % t)


def _ev(node, source):
    if isinstance(node, ast.Expression):
        return _ev(node.body, source)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            raise CalcError("booleans are not numbers")
        if isinstance(node.value, (int, float)):
            return _num_text(source, node)
        raise CalcError("only numbers — no %s"
                        % type(node.value).__name__)
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        a, b = _ev(node.left, source), _ev(node.right, source)
        op = OPS[type(node.op)]
        if op == "**":
            if b != b.to_integral_value():
                raise CalcError("fractional exponents refused")
            if abs(b) > MAX_EXP:
                raise CalcError("exponent over %d refused" % MAX_EXP)
            return a ** b
        if op in ("/", "//", "%") and b == 0:
            raise CalcError("division by zero — refused, not infinity")
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            return a / b
        if op == "//":
            return a // b
        return a % b
    if isinstance(node, ast.UnaryOp):
        v = _ev(node.operand, source)
        if isinstance(node.op, ast.USub):
            return -v
        if isinstance(node.op, ast.UAdd):
            return v
        raise CalcError("only +/- unary signs")
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or \
                node.func.id not in FUNCS:
            raise CalcError("functions allowed: round, sqrt, abs — "
                            "by name, nothing else")
        name = node.func.id
        args = [_ev(a, source) for a in node.args]
        if name == "round":
            if not 1 <= len(args) <= 2:
                raise CalcError("round(x) or round(x, n)")
            n = int(args[1]) if len(args) == 2 else 0
            if abs(n) > 30:
                raise CalcError("round digits over 30 refused")
            q = (Decimal(1).scaleb(-n) if n > 0 else Decimal(1)
                 if n == 0 else Decimal("1e%d" % -n))
            return args[0].quantize(q, rounding=ROUND_HALF_UP)
        if len(args) != 1:
            raise CalcError("%s takes exactly one argument" % name)
        if name == "sqrt":
            if args[0] < 0:
                raise CalcError("sqrt of a negative — refused, no i")
            return args[0].sqrt()
        return abs(args[0])
    raise CalcError("expression language is closed: numbers, + - * / "
                    "// % ** ( ) round/sqrt/abs only")


def calc(expr, digits=None):
    if not isinstance(expr, str) or not expr.strip():
        raise CalcError('expr: a string like "round(7834*9217/100, 2)"')
    if len(expr) > MAX_EXPR:
        raise CalcError("expression over %d chars — refused" % MAX_EXPR)
    for stray in re.findall(r"[a-zA-Z_][a-zA-Z_0-9]*", expr.lower()):
        if stray not in FUNCS:
            raise CalcError("name %r is not in the closed language"
                            % stray)
    if "__" in expr or '"' in expr or "'" in expr:
        raise CalcError("strings/dunder refused by construction")
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise CalcError("not a valid expression: %s" % e.msg)
    with localcontext() as ctx:
        ctx.prec = 50
        value = _ev(tree, expr)
    if value == value.to_integral_value() and \
            abs(value.as_tuple().exponent) < 30:
        raw = str(value.quantize(Decimal(1)))
    else:
        raw = str(value.normalize()) if value.copy_abs() >= 1 or \
            value == 0 else str(value)
    out = {"expr": expr, "value": raw, "digits_context": 50,
           "language": "closed: + - * / // % ** ( ) round/2, sqrt, "
                       "abs; Decimal literals from SOURCE text, never "
                       "float binary; HALF_UP on round; refusals named"}
    if digits is not None:
        try:
            d = int(digits)
        except (TypeError, ValueError):
            raise CalcError("digits must be an integer 0..30")
        if not 0 <= d <= 30:
            raise CalcError("digits must be 0..30")
        out["value"] = str(Decimal(raw).quantize(
            Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP))
        out["rounded_to"] = d
    return out
