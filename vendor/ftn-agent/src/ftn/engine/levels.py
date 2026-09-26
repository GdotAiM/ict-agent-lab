from __future__ import annotations

from typing import Any


PIP = 0.0001  # FX default; gold/JPY callers can override


def _mid(a: float, b: float) -> float:
    return (a + b) / 2.0


def floor_trader_pivots(h: float, l: float, c: float) -> dict[str, float]:
    """Classic floor-trader pivots + ICT midpoints (0-GMT family)."""
    pp = (h + l + c) / 3.0
    r1 = 2 * pp - l
    s1 = 2 * pp - h
    r2 = pp + (h - l)
    s2 = pp - (h - l)
    r3 = h + 2 * (pp - l)
    s3 = l - 2 * (h - pp)
    return {
        "PP": pp,
        "M3": _mid(pp, r1),
        "R1": r1,
        "M4": _mid(r1, r2),
        "R2": r2,
        "M5": _mid(r2, r3),
        "R3": r3,
        "M2": _mid(pp, s1),
        "S1": s1,
        "M1": _mid(s1, s2),
        "S2": s2,
        "M0": _mid(s2, s3),
        "S3": s3,
    }


def project_range(low: float, high: float, n: int = 4) -> dict[str, Any]:
    width = high - low
    eq = _mid(low, high)
    up = [high + i * width for i in range(n)]
    down = [low - i * width for i in range(n)]
    return {
        "low": low,
        "high": high,
        "eq": eq,
        "width": width,
        "sd_up": up,
        "sd_down": down,
    }


def build_families(pack: dict[str, Any]) -> dict[str, Any]:
    prev = pack["previous_day"]
    pivots = floor_trader_pivots(prev["high"], prev["low"], prev["close"])
    cbdr = project_range(pack["cbdr"]["low"], pack["cbdr"]["high"])
    asian = project_range(pack["asian"]["low"], pack["asian"]["high"])
    flout = project_range(pack["flout"]["low"], pack["flout"]["high"])
    swings = pack.get("swings", {})
    return {
        "previous_day": prev,
        "swings": swings,
        "pivots": pivots,
        "cbdr": cbdr,
        "asian": asian,
        "flout": flout,
        "pd_arrays": pack.get("pd_arrays", []),
    }


def detect_bias(pack: dict[str, Any], explicit: str) -> str:
    if explicit in ("bullish", "bearish"):
        return explicit
    return pack.get("htf_bias", "bullish")


def _sorted_unique(levels: list[float]) -> list[float]:
    out: list[float] = []
    for x in sorted(levels):
        if not out or abs(x - out[-1]) > 1e-9:
            out.append(x)
    return out


def family_ladder(families: dict[str, Any], family: str) -> list[tuple[str, float]]:
    if family == "pivots":
        order = ["S3", "M0", "S2", "M1", "S1", "M2", "PP", "M3", "R1", "M4", "R2", "M5", "R3"]
        p = families["pivots"]
        return [(k, p[k]) for k in order]
    block = families[family]
    down = list(reversed([(f"{family}_dn_{i}", v) for i, v in enumerate(block["sd_down"])]))
    up = [(f"{family}_up_{i}", v) for i, v in enumerate(block["sd_up"])]
    return down + up


def count_four(
    families: dict[str, Any],
    *,
    bias: str,
    price: float,
    family: str = "pivots",
) -> list[dict[str, Any]]:
    ladder = family_ladder(families, family)
    if bias == "bullish":
        ahead = [(n, v) for n, v in ladder if v > price]
    else:
        ahead = [(n, v) for n, v in reversed(ladder) if v < price]
    picked = ahead[:4]
    return [{"index": i + 1, "name": n, "price": v} for i, (n, v) in enumerate(picked)]


def overlap_pd(
    levels: list[dict[str, Any]],
    arrays: list[dict[str, Any]],
    tol: float,
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for lv in levels:
        for arr in arrays:
            lo, hi = arr.get("low", arr.get("price", 0)), arr.get("high", arr.get("price", 0))
            mid = (lo + hi) / 2.0
            if abs(lv["price"] - mid) <= tol or (lo - tol) <= lv["price"] <= (hi + tol):
                hits.append({**lv, "pd_array": arr.get("id", arr.get("kind")), "kind": arr.get("kind")})
    return hits


def atr_pips(pack: dict[str, Any], pip: float = PIP) -> float:
    atr = pack.get("atr")
    if atr is None:
        prev = pack["previous_day"]
        atr = prev["high"] - prev["low"]
    return atr / pip
