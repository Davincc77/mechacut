# docs/proposals — the inbox of the network door

One file per accepted proposal: `<name>.json`, where `<name>` is the
proposed contract's name and the content is the `blob` field of the
`POST /api/v1/agent/propose` response, committed **verbatim** — never
edited after receipt, because the bench replays the golds as received.
Hand-traced golds before code, always; the file is evidence of what was
asked, not of what was built.

Lifecycle of a blob:

1. An agent proposes a contract (never code) at the door; the verdict is
   named and returned with the thresholds echoed in the response.
   A `DUPLICATE-OF` ships no blob — it ships a pointer to the existing tool.
2. An `ELIGIBLE` blob is committed here by the operator or the digest
   loop, verbatim, in its own commit.
3. The bench replays the examples against any existing candidate and
   against the new build when one starts.
4. A human ships it as a bundle or refuses it by name — both outcomes
   close a row in `../../VERDICTS.md` with evidence. Nothing here is
   ever silently dropped; an unshipped blob stays in the inbox with its
   row open.

A `SUSPECT-DUPLICATE` blob may also land here when the human asks to
keep the evidence (score, matched tags) for arbitration — the file then
carries the response's `matches` block too, verbatim.

Asks that arrived before the door existed (2026-11-20 → 2026-11-23, via
the Moltbook digest and launch threads) are recorded directly in
`VERDICTS.md` — no retroactive blobs; the door's receipts start with the
door.

Money follows admission, never causes it: accepted contracts that land
in a paid tier split 50/50 with the proposer's owner, and the free core
stays free forever.
