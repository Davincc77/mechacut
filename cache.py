"""Bundle 25 — CACHE. The privilege determinism buys you.

'Same inputs -> same bytes' is not only a promise to the caller; it is a
LICENSE TO CACHE. A nondeterministic service that caches responses is a
liar (the first answer was never guaranteed to repeat). Here the cache is
provably lossless: a HIT returns the exact bytes a MISS produced.

Doctrine: zero storage means no database, no disk, nothing user-shaped
outliving the process. This is a bounded in-memory LRU — the same class
of transient state as the misses ledger: it dies with the redeploy, caps
itself, and holds no identity, only hashes of requests.

Free rides are on purpose: an identical paid call that we already computed
costs us nothing to serve — charging it again would be paying for noise.
"""
import hashlib
import time
from collections import OrderedDict

MAX_ENTRIES = 256

_cache = OrderedDict()  # key -> (mono_ts, status, body_bytes)


def key_of(version, path, raw_body):
    return hashlib.sha256(
        (version + "\0" + path + "\0").encode() + raw_body).hexdigest()


def get(key):
    hit = _cache.get(key)
    if not hit:
        return None
    _cache.move_to_end(key)
    return hit[1], hit[2]


def put(key, status, body_bytes):
    if status != 200 or len(body_bytes) > 2_000_000:
        return  # cache only clean small answers
    _cache[key] = (int(time.monotonic()), status, body_bytes)
    _cache.move_to_end(key)
    while len(_cache) > MAX_ENTRIES:
        _cache.popitem(last=False)  # LRU eviction, bounded always


def stats():
    return {"entries": len(_cache), "cap": MAX_ENTRIES}


def clear():
    _cache.clear()
