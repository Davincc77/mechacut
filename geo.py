"""Bundle 28 lot 7 — GEO. Haversine & geohash: the two closed earth
maths an agent gets wrong with floats in prose. Great-circle distances
are arithmetic with a published formula; geohash is a published base32
grid. Both here in exact steps, same inputs -> same 6-decimal answer."""
import math

EARTH_RADIUS_M = 6_371_008.8  # mean radius, IUGG published value
_B32 = "0123456789bcdefghjkmnpqrstuvwxyz"   # geohash alphabet (no a,i,l,o)


def _pt(v, what):
    if not isinstance(v, dict):
        raise ValueError("%s must be {lat, lon}" % what)
    lat, lon = float(v["lat"]), float(v["lon"])
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError("%s out of range (-90..90, -180..180)" % what)
    return lat, lon


def geo_distance(a, b=None, route=None):
    """Two modes: point-to-point, or a closed route (sum of successive
    great-circle legs, order preserved — a route is not a set)."""
    if route:
        pts = [_pt(p, "route[%d]" % i) for i, p in enumerate(route)]
        if len(pts) < 2:
            raise ValueError("route needs >= 2 points")
        total = 0.0
        legs = []
        for (la1, lo1), (la2, lo2) in zip(pts, pts[1:]):
            d = _hav(la1, lo1, la2, lo2)
            legs.append(round(d, 1))
            total += d
        return {"mode": "route", "legs_m": legs,
                "total_m": round(total, 1),
                "total_km": round(total / 1000.0, 3),
                "points": len(pts)}
    if not b:
        raise ValueError("give b (point) or route (list)")
    la1, lo1 = _pt(a, "a")
    la2, lo2 = _pt(b, "b")
    d = _hav(la1, lo1, la2, lo2)
    return {"mode": "pair", "meters": round(d, 1),
            "km": round(d / 1000.0, 3), "miles": round(d / 1609.344, 3)}


def _hav(la1, lo1, la2, lo2):
    p1, p2 = math.radians(la1), math.radians(la2)
    dp, dl = p2 - p1, math.radians(lo2 - lo1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) \
        * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))


def _geohash_encode(lat, lon, precision):
    lats = [-90.0, 90.0]
    lons = [-180.0, 180.0]
    even = True
    bits, ch, out = 0, 0, []
    while len(out) < precision:
        if even:
            mid = (lons[0] + lons[1]) / 2
            if lon >= mid:
                ch |= 1 << (4 - bits)
                lons[0] = mid
            else:
                lons[1] = mid
        else:
            mid = (lats[0] + lats[1]) / 2
            if lat >= mid:
                ch |= 1 << (4 - bits)
                lats[0] = mid
            else:
                lats[1] = mid
        even = not even
        bits += 1
        if bits == 5:
            out.append(_B32[ch])
            bits, ch = 0, 0
    return "".join(out), lats, lons


def geo_geohash(lat=None, lon=None, geohash=None, precision=6):
    p = int(precision)
    if not 1 <= p <= 12:
        raise ValueError("precision must be 1..12")
    if geohash:
        g = str(geohash).strip().lower()
        bad = [c for c in g if c not in _B32]
        if bad:
            raise ValueError("invalid geohash chars: %s (alphabet has no "
                             "a i l o)" % "".join(sorted(set(bad))))
        # decode to centre + error box
        lats = [-90.0, 90.0]
        lons = [-180.0, 180.0]
        even = True
        for c in g:
            v = _B32.index(c)
            for bit in (16, 8, 4, 2, 1):
                mid = (lons[0] + lons[1]) / 2 if even \
                    else (lats[0] + lats[1]) / 2
                on = bool(v & bit)
                if even:
                    lons = [mid, lons[1]] if on else [lons[0], mid]
                else:
                    lats = [mid, lats[1]] if on else [lats[0], mid]
                even = not even
        cl = (lats[0] + lats[1]) / 2
        co = (lons[0] + lons[1]) / 2
        return {"geohash": g, "lat": round(cl, 6), "lon": round(co, 6),
                "box": {"lat": [round(lats[0], 6), round(lats[1], 6)],
                        "lon": [round(lons[0], 6), round(lons[1], 6)]},
                "precision": len(g)}
    la, lo = _pt({"lat": lat, "lon": lon}, "point")
    g, blats, blons = _geohash_encode(la, lo, p)
    return {"geohash": g, "precision": p,
            "box": {"lat": [round(blats[0], 6), round(blats[1], 6)],
                    "lon": [round(blons[0], 6), round(blons[1], 6)]}}
