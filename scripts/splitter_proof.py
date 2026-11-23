# -*- coding: utf-8 -*-
"""splitter_proof — bundle 91 : la mécanique 50/50 prouvée sur EVM local.

Se LANCE HORS du dépôt (cwd = dossier de travail) : à la racine du repo,
notre eth.py éclipse le package py-evm — ce n'est pas un bug, c'est une
contrainte d'espace de noms, écrite ici pour le prochain lecteur.

Imprime un JSON de mesures ; tests/test_bundle91.py asserte chaque champ.
"""
import json
import sys

ART = json.load(open(sys.argv[1]))

from eth_tester import EthereumTester, PyEVMBackend
from web3 import Web3

w3 = Web3(Web3.EthereumTesterProvider(EthereumTester(PyEVMBackend())))
accts = list(w3.eth.accounts)
OWNER, PAYER, STRANGER = accts[0], accts[1], accts[2]
# payouts EIP-55 valides (variations de casse checksummées)
P = Web3.to_checksum_address(
    "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed")
P2 = Web3.to_checksum_address(
    "0xAbC8603B53B47A1E1F5f94B77E1B30E173752E60")
TREASURY = Web3.to_checksum_address(accts[3])


def deploy(name, *args):
    c = w3.eth.contract(abi=ART[name]["abi"], bytecode=ART[name]["bytecode"])
    txh = c.constructor(*args).transact({"from": OWNER})
    return w3.eth.get_transaction_receipt(txh)["contractAddress"]


usdc_addr = deploy("MockUSDC")
usdc = w3.eth.contract(address=usdc_addr, abi=ART["MockUSDC"]["abi"])
fac_addr = deploy("SplitterFactory", usdc_addr, TREASURY, 5000)
fac = w3.eth.contract(address=fac_addr, abi=ART["SplitterFactory"]["abi"])

out = {}
one = 1_000_000  # $1 in USDC 6-decimals
usdc.functions.mint(PAYER, 100 * one).transact({"from": OWNER})

# S1 — predicted == deployed (CREATE2 respecte le git)
pred = fac.functions.predicted("money_tip", P).call()
fac.functions.ensure("money_tip", P).transact({"from": OWNER})
key = Web3.keccak(text="money_tip")
dep = fac.functions.splitterFor(key).call()
out["s1_predicted_eq_deployed"] = pred.lower() == dep.lower()

# S2 — idempotence + garde de termes
fac.functions.ensure("money_tip", P).transact({"from": STRANGER})  # ok same
same = fac.functions.splitterFor(key).call()
out["s2_idempotent"] = same.lower() == dep.lower()
try:
    fac.functions.ensure("money_tip", P2).transact({"from": OWNER})
    out["s2_mismatch_reverted"] = False
except Exception:
    out["s2_mismatch_reverted"] = True

# S3 — $1 via authorization (geste du facilitateur) tiers flush
usdc.functions.transferWithAuthorization(
    PAYER, dep, one, 0, 2**64 - 1, b"\x11" * 32, 27, b"\x22" * 32,
    b"\x33" * 32).transact({"from": STRANGER})
splitter = w3.eth.contract(address=dep, abi=ART["USDCSplitter"]["abi"])
splitter.functions.flush().transact({"from": STRANGER})
out["s3_payout"] = usdc.functions.balanceOf(P).call()
out["s3_treasury"] = usdc.functions.balanceOf(TREASURY).call()
out["s3_splitter_empty"] = usdc.functions.balanceOf(dep).call()

# S4 — impair 999_999 : floor au proposer, reste arrondi au noyau.
# Comptes DÉDIÉS : les soldes ne se relèvent pas en soustrayant des
# épisodes précédents — le 24-11 un delta à -1 l'a prouvé.
key2 = Web3.keccak(text="date_civil")
fac.functions.ensure("date_civil", P).transact({"from": OWNER})
dep2 = fac.functions.splitterFor(key2).call()
usdc.functions.transferWithAuthorization(
    PAYER, dep2, 999_999, 0, 2**64 - 1, b"\x11" * 32, 27, b"\x22" * 32,
    b"\x33" * 32).transact({"from": STRANGER})
sp2 = w3.eth.contract(address=dep2, abi=ART["USDCSplitter"]["abi"])
sp2.functions.flush().transact({"from": STRANGER})
out["s4_odd_splitter_empty"] = usdc.functions.balanceOf(dep2).call()
out["s4_odd_payout_total"] = usdc.functions.balanceOf(P).call()
out["s4_odd_treasury_total"] = usdc.functions.balanceOf(TREASURY).call()

# S5 — pas d'ETH
try:
    w3.eth.send_transaction({"from": PAYER, "to": dep, "value": 1})
    out["s5_eth_rejected"] = False
except Exception:
    out["s5_eth_rejected"] = True

# S6 — isolement par outil
out["s6_distinct"] = dep.lower() != dep2.lower()

# immuabilité : treasury/bps du clone == ceux nés du contrat
out["s7_invariants"] = (
    splitter.functions.treasury().call().lower() == TREASURY.lower()
    and splitter.functions.payoutBps().call() == 5000
    and splitter.functions.token().call().lower() == usdc_addr.lower())

print(json.dumps(out, sort_keys=True))
