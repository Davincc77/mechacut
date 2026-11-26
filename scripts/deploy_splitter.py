# -*- coding: utf-8 -*-
"""deploy_splitter — la porte humaine du 50/50 (Base mainnet).

Usage recommandé (Terminal, chez toi — rien ne passe par le chat) :

  cd ~/Projets/mechacut
  export TREASURY_ADDRESS="0x…ton-portefeuille-principal"   # PUBLIC
  .venv/bin/python scripts/deploy_splitter.py factory
  # le script demande la clé du compte qui PAYE LE GAZ : saisie
  # masquée (getpass), jamais dans l'historique du shell, jamais
  # écrite, jamais imprimée — elle vit dans la mémoire du processus.

Le compte de gaz peut être un compte jetable avec ~5 $ d'ETH sur Base :
les contrats n'ont PAS d'owner — ce compte ne contrôle rien après le
déploiement, il a seulement payé l'essence. Le trésorier (moitié noyau
des splits) est TREASURY_ADDRESS, pas le deployer.

Autres commandes :
  … ensure <tool> <0xpayout>   # FACTORY_ADDRESS=*** requis
  … predict <tool> <0xpayout>  # lecture seule, sans clé

Le script refuse si la RPC ne répond pas chain id 8453 (Base mainnet) —
déployer sur le mauvais réseau est une perte, pas une erreur récupérable.
"""
import json
import os
import sys

USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "contracts", "build", "artifacts.json")


def _unlock(w3):
    """Clé : env si l'humain l'a déjà mise dans SA session, sinon
    saisie masquée. On ne l'imprime jamais, on ne l'écrit nulle part."""
    key = os.environ.get("PRIVATE_KEY", "").strip()
    if not key:
        import getpass
        key = getpass.getpass(
            "clé privée du compte qui PAYE LE GAZ (masquée, jamais "
            "stockée) : ").strip()
    if not key:
        sys.exit("no key, no deploy — this tool never asks it in chat")
    return w3.eth.account.from_key(key)


def main():
    rpc = os.environ.get("RPC_URL", "https://mainnet.base.org").strip()
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    from web3 import Web3
    w3 = Web3(Web3.HTTPProvider(rpc))
    cid = w3.eth.chain_id
    if cid != 8453:
        sys.exit("chain guard: RPC %s answers chain id %d, not Base "
                 "mainnet (8453) — refusing to deploy there" % (rpc, cid))
    with open(ART) as f:
        art = json.load(f)
    cmd = sys.argv[1]

    if cmd == "predict":
        tool, payout = sys.argv[2], sys.argv[3]
        fac_addr = os.environ.get("FACTORY_ADDRESS", "").strip()
        if not fac_addr:
            sys.exit("export FACTORY_ADDRESS from step factory")
        fac = w3.eth.contract(address=Web3.to_checksum_address(fac_addr),
                              abi=art["SplitterFactory"]["abi"])
        print(tool, "->", fac.functions.predicted(
            tool, Web3.to_checksum_address(payout)).call())
        return

    acct = _unlock(w3)
    treasury = os.environ.get("TREASURY_ADDRESS", "").strip() \
        or acct.address
    treasury = Web3.to_checksum_address(treasury)
    bal = w3.eth.get_balance(acct.address)
    print("deployer", acct.address, "| gaz dispo %.6f ETH | trésorier %s"
          % (bal / 1e18, treasury))
    if bal < w3.to_wei(0.0005, "ether"):
        sys.exit("moins de 0.0005 ETH sur ce compte Base — le gaz "
                 "coûte ~0.0001 ETH, passe d'abord un peu d'ETH sur "
                 "ce compte (réseau BASE, pas Ethereum)")

    if cmd == "factory":
        c = w3.eth.contract(abi=art["SplitterFactory"]["abi"],
                            bytecode=art["SplitterFactory"]["bytecode"])
        tx = c.constructor(Web3.to_checksum_address(USDC_BASE),
                           treasury, 5000).build_transaction(
            {"from": acct.address, "gas": 3_000_000,
             "gasPrice": w3.eth.gas_price,
             "nonce": w3.eth.get_transaction_count(acct.address)})
        signed = acct.sign_transaction(tx)
        h = w3.eth.send_raw_transaction(signed.raw_transaction)
        r = w3.eth.wait_for_transaction_receipt(h)
        if r.status != 1:
            sys.exit("tx reverted — ne pas continuer, vérifier la RPC")
        addr = r.contractAddress
        code = w3.eth.get_code(addr)
        print("factory", addr, "tx", h.hex())
        print("garde post-deploy : %d octets de code à cette adresse"
              % len(code))
        print("→ colle l'adresse de factory dans le chat (elle est "
              "publique), la suite est commit + redéploiement côté API")
    elif cmd == "ensure":
        tool, payout = sys.argv[2], sys.argv[3]
        fac_addr = os.environ.get("FACTORY_ADDRESS", "").strip()
        if not fac_addr:
            sys.exit("export FACTORY_ADDRESS from step factory")
        fac = w3.eth.contract(address=Web3.to_checksum_address(fac_addr),
                              abi=art["SplitterFactory"]["abi"])
        pred = fac.functions.predicted(
            tool, Web3.to_checksum_address(payout)).call()
        print(tool, "->", pred)
        tx = fac.functions.ensure(
            tool, Web3.to_checksum_address(payout)).build_transaction(
            {"from": acct.address, "gas": 600_000,
             "gasPrice": w3.eth.gas_price,
             "nonce": w3.eth.get_transaction_count(acct.address)})
        signed = acct.sign_transaction(tx)
        h = w3.eth.send_raw_transaction(signed.raw_transaction)
        r = w3.eth.wait_for_transaction_receipt(h)
        if r.status != 1:
            sys.exit("tx reverted — les termes ne matchent pas le sel ?")
        got = fac.functions.splitterFor(Web3.keccak(text=tool)).call()
        print("ensured", got, "tx", h.hex(), "| predicted==onchain:",
              got.lower() == pred.lower())
    else:
        sys.exit("unknown command — see __doc__")


if __name__ == "__main__":
    main()
