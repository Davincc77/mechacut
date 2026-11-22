import re


def _esc(x):
    return re.escape(x)


def match_naked(text, gold, cmp):
    """Bras NU : la JUSTESSE compte champ par champ. Un champ court
    (chiffre, %) doit apparaître ISOLÉ (bornes non-alphanumériques) —
    le dernier occurrence = la réponse après raisonnement. Un champ
    long (hex, base64, url) = sous-chaîne exacte. Set = égalité
    d'ensemble des tokens pos:digit. json = parse-égalité."""
    if not text or not text.strip():
        return False
    # pré-nettoyage : un « 1. » de fin de phrase ne doit pas casser
    # la frontière d'un champ court, sans toucher aux décimales
    text = re.sub(r'(?<=\d)\.(?=\s|$)', ' ', text)
    if cmp == "set":
        toks = set(re.findall(r"\d{1,2}:\d", text))
        return toks == set(gold[0].split(","))
    if cmp == "json":
        for m in re.finditer(r"\{.*?\}", text, re.S):
            try:
                return __import__("json").loads(m.group(0)) == \
                    __import__("json").loads(gold[0])
            except Exception:
                continue
        return False
    for gf in gold:
        g = str(gf).strip()
        if len(g) <= 3:
            hits = re.findall(r"(?<![\w.])%s(?![\w.])" % _esc(g), text)
            if not hits:
                return False
        elif g not in text:
            # tolérance minuscule : le dernier caractère d'une URL avec
            # un point final de phrase collé
            if not re.search(_esc(g) + r"(?=[\s).,]|$)", text):
                return False
    return True
