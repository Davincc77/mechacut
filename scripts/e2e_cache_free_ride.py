"""E2E cache free-ride, shape conforme au client OFFICIEL x402 v1
(eip3009.ts de coinbase/x402) : authorization {from,to,value,validAfter,
validBefore,nonce} en chaînes DÉCIMALES (value="500", validAfter="0"),
payload={authorization,signature} sans discriminateur, network = écho de
la requirement du serveur. Settlement réel USDC mainnet via payai."""
import json, time, secrets, base64, httpx
from eth_account import Account

KEYFILE = "/tmp/x402_burner_mainnet.json"
BASE = "https://mechacut.studio"
PATH = "/api/v1/reshape"

k = json.load(open(KEYFILE))
acct = Account.from_key(k["key"] if isinstance(k, dict) else k)

# 1. demander la requirement au serveur : on ne devine rien
_req = httpx.post(BASE + PATH, content=b"")
acc0 = _req.json()["accepts"][0]
print("requirement:", acc0["network"], acc0["maxAmountRequired"], acc0["payTo"])

now = int(time.time())
auth = {
    "from": acct.address,
    "to": acc0["payTo"],
    "value": str(acc0["maxAmountRequired"]),      # chaîne décimale atomique
    "validAfter": "0",
    "validBefore": str(now + acc0.get("maxTimeoutSeconds", 60)),
    "nonce": "0x" + secrets.token_hex(32),
}
td = {
    "types": {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"},
        ],
        "TransferWithAuthorization": [
            {"name": "from", "type": "address"},
            {"name": "to", "type": "address"},
            {"name": "value", "type": "uint256"},
            {"name": "validAfter", "type": "uint256"},
            {"name": "validBefore", "type": "uint256"},
            {"name": "nonce", "type": "bytes32"},
        ],
    },
    "primary": "TransferWithAuthorization",
    "domain": {"name": acc0["extra"]["name"],
               "version": acc0["extra"]["version"],
               "chainId": 8453,
               "verifyingContract": acc0["asset"]},
    "message": {"from": auth["from"], "to": auth["to"],
                "value": int(auth["value"]),
                "validAfter": int(auth["validAfter"]),
                "validBefore": int(auth["validBefore"]),
                "nonce": auth["nonce"]},
}
_s = acct.sign_typed_data(full_message=td)["signature"]
sig = _s.hex() if str(_s).startswith("0x") else "0x" + _s.hex()

payment = {"x402Version": 1, "scheme": acc0["scheme"],
           "network": acc0["network"],
           "payload": {"authorization": auth, "signature": sig}}
hdr = base64.b64encode(json.dumps(payment).encode()).decode()

body = {"input": {"n": 7}, "mapping": {"fields": {"out": {"path": "n"}}}}

r1 = httpx.post(BASE + PATH, json=body, headers={"X-PAYMENT": hdr},
                timeout=90)
pr = None
if r1.headers.get("x-payment-response"):
    pr = json.loads(r1.headers["x-payment-response"]).get("tx")
if r1.status_code == 402:
    print("REFUS:", json.dumps(r1.json())[:300])
print("1) payé:", r1.status_code, "| X-Cache:", r1.headers.get("x-cache"),
      "| tx:", pr)

r2 = httpx.post(BASE + PATH, json=body, timeout=30)
print("2) même corps SANS voucher:", r2.status_code,
      "| X-Cache:", r2.headers.get("x-cache"),
      "| mêmes octets:", r2.content == r1.content)

r3 = httpx.post(BASE + PATH, json=body, headers={"X-PAYMENT": hdr},
                timeout=30)
print("3) voucher rejoué:", r3.status_code, "(attendu 402)")
