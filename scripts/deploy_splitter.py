# -*- coding: utf-8 -*-
"""deploy_splitter — la porte humaine du 50/50 (Base mainnet).

Usage:
  export RPC_URL=https://mainnet.base.org PRIVATE_KEY=***  # jamais en chat, jamais en git
  python scripts/deploy_splitter.py factory
  python scripts/deploy_splitter.py ensure <tool> <0xpayout>
  python scripts/deploy_splitter.py predict <tool> <0xpayout>

Refuse sans clé. N'écrit jamais la clé. Imprime, ne devine pas.
"""
import json
import os
import sys

USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "contracts", "build", "artifacts.json")


def main():
    key = os.environ.get("PRIVATE_KEY", "").strip()
    rpc = os.environ.get("RPC_URL", "https://mainnet.base.org").strip()
    if not key:
        sys.exit("no key: export PRIVATE_KEY in your shell — this tool "
                 "never asks it in chat and never stores it")
    from web3 import Web3
    w3 = Web3(Web3.HTTPProvider(rpc))
    acct = w3.eth.account.from_key(key)
    art = json.load(open(ART))
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "factory":
        c = w3.eth.contract(abi=art["SplitterFactory"]["abi"],
                            bytecode=art["SplitterFactory"]["bytecode"])
        tx = c.constructor(Web3.to_checksum_address(USDC_BASE),
                           acct.address, 5000).build_transaction(
            {"from": acct.address, "gas": 3_000_000, "gasPrice":
             w3.eth.gas_price})
        signed = acct.sign_transaction(tx)
        h = w3.eth.send_raw_transaction(signed.raw_transaction)
        r = w3.eth.wait_for_transaction_receipt(h)
        print("factory", r.contractAddress, "tx", h.hex())
    elif cmd in ("ensure", "predict"):
        tool, payout = sys.argv[2], sys.argv[3]
        fac_addr = os.environ.get("FACTORY_ADDRESS", "").strip()
        if not fac_addr:
            sys.exit("export FACTORY_ADDRESS from step factory")
        fac = w3.eth.contract(address=Web3.to_checksum_address(fac_addr),
                              abi=art["SplitterFactory"]["abi"])
        pred = fac.functions.predicted(tool,
                                       Web3.to_checksum_address(payout)
                                       ).call()
        print(tool, "->", pred)
        if cmd == "predict":
            return
        tx = fac.functions.ensure(tool,
                                  Web3.to_checksum_address(payout)
                                  ).build_transaction(
            {"from": acct.address, "gas": 600_000,
             "gasPrice": w3.eth.gas_price})
        signed = acct.sign_transaction(tx)
        h = w3.eth.send_raw_transaction(signed.raw_transaction)
        w3.eth.wait_for_transaction_receipt(h)
        print("ensured", pred, "tx", h.hex())
    else:
        sys.exit("unknown command — see __doc__")


if __name__ == "__main__":
    main()
