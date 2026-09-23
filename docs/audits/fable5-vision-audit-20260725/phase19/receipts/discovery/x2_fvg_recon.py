#!/usr/bin/env python3
"""x2 step 1 - reconstruct the M15 FVG zone behind every current_fvg_fill candidate.

FVG zone edges (market_state.identify_fvgs:926-1010):
  bullish: bottom = c[i-1].high, top = c[i+1].low   (gap = top-bottom)
  bearish: bottom = c[i+1].high, top = c[i-1].low
Generator geometry (broader_origin_generators._current_framework_geometry:1616-1629):
  entry = (zone_low+zone_high)/2  ->  entry_price IS the FVG midpoint, exactly.
So an exact float match on midpoint identifies the zone and its formation bar.
"""
import sys, os, json, gzip, collections, datetime as dt
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import x2_bars, w0_ws

TOL = 1e-9

def fvgs_upto(m15, upto_idx):
    """All 3-candle FVGs whose confirmation bar index <= upto_idx (no min_gap filter).
    Returns dict midpoint -> list of (form_idx, conf_idx, lo, hi, type)."""
    out = collections.defaultdict(list)
    for i in range(1, upto_idx):
        c_lo, c_mid, c_hi = m15[i-1], m15[i], m15[i+1]
        bull = c_hi[3] - c_lo[2]          # low[i+1] - high[i-1]
        if bull > 0:
            lo, hi = c_lo[2], c_hi[3]
            out[round((lo+hi)/2, 12)].append((i, i+1, lo, hi, "bullish"))
        bear = c_lo[3] - c_hi[2]          # low[i-1] - high[i+1]
        if bear > 0:
            lo, hi = c_hi[2], c_lo[3]
            out[round((lo+hi)/2, 12)].append((i, i+1, lo, hi, "bearish"))
    return out


def main():
    rows = [r for r in w0_ws.load() if r["origin_family"] == "current_fvg_fill"]
    bysym = collections.defaultdict(list)
    for r in rows:
        bysym[r["symbol"]].append(r)
    res = []
    stats = collections.Counter()
    for sym, rs in sorted(bysym.items()):
        m15 = x2_bars.load_m15(sym)
        idx = {b[0]: i for i, b in enumerate(m15)}
        # cache fvg table per decision index (rebuild is O(n); build once for the whole month
        # then filter by conf_idx <= decision idx)
        allf = fvgs_upto(m15, len(m15) - 1)
        for r in rs:
            bt = dt.datetime.fromisoformat(r["decision_time_utc"]) - dt.timedelta(minutes=15)
            di = idx.get(bt)
            if di is None:
                stats["no_decision_bar"] += 1
                continue
            key = round(r["entry_price"], 12)
            cands = [c for c in allf.get(key, ()) if c[1] <= di]
            if not cands:
                # relaxed match on nearest midpoint
                stats["no_zone_match"] += 1
                res.append({"key": list(w0_ws.key(r)), "symbol": sym, "matched": False})
                continue
            # the MSO holds every unfilled FVG; the newest match is the live one
            cands.sort(key=lambda c: c[1])
            f = cands[-1]
            stats["matched"] += 1
            stats["multi" if len(cands) > 1 else "single"] += 1
            age_bars = di - f[1]           # 0 == formed BY the decision bar itself
            stats["age0"] += 1 if age_bars == 0 else 0
            half = (f[3] - f[2]) / 2.0
            res.append({
                "key": list(w0_ws.key(r)), "symbol": sym, "matched": True,
                "conf_idx": f[1], "decision_idx": di, "age_bars": age_bars,
                "zone_low": f[2], "zone_high": f[3], "half_width": half,
                "fvg_type": f[4], "side": r["side"],
                "risk_distance": r["risk_distance"],
                "implied_buffer_atr": r["risk_distance"] - half,
                "conf_bar_time": m15[f[1]][0].isoformat(),
            })
    with gzip.open(os.path.join(D, "x2_FVG_ZONES_V1.jsonl.gz"), "wt") as fh:
        for x in res:
            fh.write(json.dumps(x) + "\n")
    print(json.dumps(dict(stats), indent=1))
    ages = [x["age_bars"] for x in res if x.get("matched")]
    ages.sort()
    n = len(ages)
    print("age_bars n=%d min=%d p10=%d p25=%d med=%d p75=%d p90=%d max=%d"
          % (n, ages[0], ages[n//10], ages[n//4], ages[n//2], ages[3*n//4], ages[9*n//10], ages[-1]))
    print("age==0 (formed BY the decision bar):", sum(1 for a in ages if a == 0), "/", n)
    print("age>=1 (zone existed before bar opened):", sum(1 for a in ages if a >= 1), "/", n)


if __name__ == "__main__":
    main()
