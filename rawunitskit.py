# -*- coding: utf-8 -*-
"""erc20_raw_units — l'echelle exacte qu'aucun voisin ne sait rendre
(registre L21, blob sha256 887dffa67cadaab476e8182e29513b290b07f31a
6e8c40fb3d66a199311c311e — sha cite AU REGISTRE, reçu 26-11, ADMIS 27-11).

Contrat d'admission, LITTERAL de la compilation des rapports de campagne
(l. 1984-1985) : « raw uint256 + decimals 0..77 -> exact string » ;
« takes the token's own decimals (any 0..77, e.g. 6 USDC, 8 cbBTC) as
an argument and returns an exact string for any uint256 (up to 78
digits), with no rounding and a named 400 on overflow » — une seule
regle d'echelle exacte, decimals EN ARGUMENT, jamais devines.

Douleur mesuree (same lines) : eth_units n'a que les barreaux
wei/gwei/ether (aucun 10^6 ni 10^8) et ARRONDIT EN SILENCE au-dela de
30 chiffres significatifs — B1 c2c4d33a, B2 46ecf95f : MOG-Base
totalSupply 116162348802077343159857936548537 rendu ...549000, soit
+463 WEI fabriques. num_parse idem (B13 44d860ee, 0/3 OK) ; math_calc
rend un HTTP 500 des 31 chiffres et tue le batch entier (B3a). La
reproduction au tip 1554d85 (27-11) : eth_units wei echo
"116162348802077343159857936549000" — +463 encore reel, rejoue en
CLAIM dans le test du lot, jamais fondu ici.

References publiees nommees :
  - EIP-20 « ERC-20 Token Standard » (ethereum EIPs), decimals() :
    « returns the decimals used in both the _value and allowance
    parameters » — uint8 ; le scaling humain = value / 10**decimals.
    https://eips.ethereum.org/EIPS/eip-20
  - uint256 = entier non signe 0 .. 2**256 - 1 (78 chiffres ; EVM word,
    spec Yellow Paper — totalSupply/balanceOf retournent un uint256).
  - decimales PAR TOKEN citees du corpus de campagne (l. 1963, prises
    de CoinGecko detail_platforms.base puis recoupees on-chain) :
    USDC 6, cbBTC 8, AERO 18, DEGEN 18, BRETT 18, TOSHI 18, MOG 18.
  - borne SUPERIEURE du contrat : decimals 0..77 — la du contract
    admis (jamais inventee ici) : le max uint256 fait 78 chiffres, une
    echelle de 78 placerait le chiffre dans un rang que le type ne
    peut atteindre ; 77 = 78 - 1, et le contrat d'admission le nomme
    tel quel.

Golds (6 traces main — classe « decalage de virgule sur valeurs brutes
on-chain », l. 1984) : MOG litteral du rapport ; 2**256-1 a d18 (78
chiffres exacts) ; 1 a d77 ; 1000000 a d0 ; 42069000000 a d8 (classe
cbBTC — raw synthetique, decimals 8 citees) ; 1000000000000 a d6
(classe USDC — raw synthetique, decimals 6 citees). 2**256 refuse par
le nom (l. 1984 : « 2^256 refused »).
"""
import re

UINT256_MAX = (1 << 256) - 1          # 2**256 - 1, 78 digits
UINT256_LIMIT = 1 << 256              # refused by name
DEC_MIN, DEC_MAX = 0, 77              # closed range of the admitted contract
_DIGITS = re.compile(r"\d+\Z")

REF_EIP20 = ("EIP-20 decimals() returns uint8; the human-unit scaling "
             "is value / 10**decimals — exact decimal-point shift, no "
             "rounding exists in this rule (eips.ethereum.org/EIPS/"
             "eip-20)")
REF_UINT256 = ("raw is a uint256: 0 <= raw <= 2**256-1 (78 digits max, "
               "what totalSupply/balanceOf return per the EVM word "
               "type); 2**256 and above are refused by name, never "
               "wrapped (twos-complement wrap is a different contract)")
REF_DEC_RANGE = ("decimals is bounded 0..77 by THIS tool's admitted "
                 "contract (uint256 reaches 78 digits; EIP-20 declares "
                 "uint8 — 78..255 are out of this door's published "
                 "range, said not silent); real tokens cited from the "
                 "campaign corpus: USDC 6, cbBTC 8, AERO/DEGEN/BRETT/"
                 "TOSHI/MOG 18")


class RawUnitsError(Exception):
    def __init__(self, field, msg):
        self.field = field
        self.msg = msg
        super().__init__(msg)


def scale(raw, decimals):
    if isinstance(raw, bool):
        raise RawUnitsError("raw",
                            "raw: a non-negative integer string (the "
                            "decoded uint256, e.g. \"116162348802\" "
                            ") — booleans are not amounts")
    if isinstance(raw, float):
        raise RawUnitsError("raw",
                            "raw: pass the decoded uint256 as a digit "
                            "STRING — binary64 would round the value "
                            "before this door ever sees it")
    if isinstance(raw, int):
        s = str(raw)
    elif isinstance(raw, str):
        s = raw.strip()
    else:
        raise RawUnitsError("raw",
                            "raw: a digit string of the decoded uint256")
    if s.lower().startswith("0x"):
        raise RawUnitsError("raw",
                            "raw: decode the eth_call hex (0x…) to a "
                            "base-10 digit string first — this door "
                            "scales integers, it does not parse RPC "
                            "hex")
    if s.startswith("-"):
        raise RawUnitsError("raw",
                            "raw: uint256 is unsigned — negative "
                            "amounts are refused, not abs()'d")
    if not _DIGITS.match(s):
        raise RawUnitsError("raw",
                            "raw: base-10 digits only (0-9), the "
                            "integer string the chain actually returns")
    leading = len(s) > 1 and s[0] == "0"
    n = int(s)
    if n > UINT256_MAX:
        raise RawUnitsError("raw",
                            "raw: above 2**256-1 (11579208923731619542"
                            "35709850086879078532699846656405640394575"
                            "84007913129639935, 78 digits) is not a "
                            "uint256 — refused, never wrapped mod 2**256")
    if isinstance(decimals, bool) or not isinstance(decimals, int):
        raise RawUnitsError("decimals",
                            "decimals: an integer 0..77 (the token's "
                            "own decimals() as an argument — EIP-20 "
                            "declares uint8; this door refuses to "
                            "guess it)")
    if not DEC_MIN <= decimals <= DEC_MAX:
        raise RawUnitsError("decimals",
                            "decimals: 0..77 (closed range of this "
                            "tool's admitted contract) — the token's "
                            "decimals() is an argument, never guessed")
    digits = str(n)
    if decimals == 0:
        human = digits
        ip, fp = digits, ""
    else:
        padded = digits.zfill(decimals + 1)
        ip, fp = padded[:-decimals], padded[-decimals:]
        human = ip + "." + fp
    out = {
        "raw": digits,
        "decimals": decimals,
        "human": human,
        "integer_part": ip,
        "fraction_part": fp,
        "raw_digits": len(digits),
        "rule": {
            "scaling": REF_EIP20,
            "domain": REF_UINT256,
            "decimals_range": REF_DEC_RANGE,
            "no_rounding": "the answer is a digit-string shift: every "
                           "digit of raw survives in order; eth_units "
                           "and num_parse silently round past 30 "
                           "significant digits (measured, B1/B2/B13 "
                           "of the campaign) — this door never does",
        },
        "applied_defaults": (["raw_leading_zeros_stripped"]
                             if leading else []),
    }
    return out
