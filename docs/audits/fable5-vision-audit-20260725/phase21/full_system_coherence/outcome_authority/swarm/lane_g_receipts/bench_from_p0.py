"""Reproduce Phase 0's per-row driftless benchmark from its own walk records,
then apply the quote-frame correction."""
import gzip, pickle, math, json
from collections import Counter, defaultdict
import numpy as np

MONTHS = ["feb","apr","may","jun","jul"]
recs = []
for mo in MONTHS:
    with gzip.open(f"/private/tmp/phase0-inversion/walk_{mo}.pkl.gz","rb") as fh:
        for r in pickle.load(fh):
            r["month"] = mo
            recs.append(r)
print("total walk records:", len(recs))

def p0_driftless(row, arm):
    """VERBATIM re-implementation of p0_full.driftless_p."""
    fill = row[arm]["fill_price"]
    if fill is None: return None
    entry, risk = row["entry_price"], row["risk_price"]
    long_orig = row["side"] == "LONG"
    stop_o, target_o = ((entry-risk, entry+row["risk_price_inv"]) if long_orig
                        else (entry+risk, entry-row["risk_price_inv"]))
    if arm == "orig":
        stop, target, direction = stop_o, target_o, (1 if long_orig else -1)
    else:
        stop, target, direction = target_o, stop_o, (-1 if long_orig else 1)
    down = direction*(fill-stop); up = direction*(target-fill)
    if down <= 0 or up <= 0: return None
    return down/(down+up)

def spread_at_fill(row):
    """MARKET fill = successor-bar open on the executable ENTRY side. The orig and
    inv arms are opposite directions at the same instant, so they differ by exactly
    one spread."""
    a, b = row["orig"]["fill_price"], row["inv"]["fill_price"]
    if a is None or b is None: return None
    if row["orig"]["fill_time"] != row["inv"]["fill_time"]: return None
    return abs(float(a)-float(b))

def corrected_driftless(row, arm):
    """Same as p0 but with the entry moved into the EXIT-side quote frame.

    quote_side._side_offset with bar_quote=BID:  entry offset = +s for LONG, 0 for
    SHORT; exit offset = 0 for LONG, +s for SHORT. So the tape-frame entry is
    fill - direction*s, i.e. down' = down - s, up' = up + s."""
    p = p0_driftless(row, arm)
    if p is None: return None
    s = spread_at_fill(row)
    if s is None: return None
    entry, risk = row["entry_price"], row["risk_price"]
    long_orig = row["side"] == "LONG"
    stop_o, target_o = ((entry-risk, entry+row["risk_price_inv"]) if long_orig
                        else (entry+risk, entry-row["risk_price_inv"]))
    corridor = abs(target_o-stop_o)   # |T-S| -- identical for both arms
    fill = row[arm]["fill_price"]
    if arm == "orig":
        stop, target, direction = stop_o, target_o, (1 if long_orig else -1)
    else:
        stop, target, direction = target_o, stop_o, (-1 if long_orig else 1)
    down = direction*(fill-stop) - s
    up   = direction*(target-fill) + s
    if down <= 0 or up <= 0: return None
    return down/(down+up)

def block(rows, arm, benchfn):
    states = Counter(r[arm]["state"] for r in rows)
    barrier = states["TARGET"]+states["STOP"]
    bench = [benchfn(r,arm) for r in rows if r[arm]["state"] in ("TARGET","STOP")]
    bench = [b for b in bench if b is not None]
    if not bench or barrier == 0: return None
    hit = states["TARGET"]/barrier
    var = sum(p*(1-p) for p in bench)
    z = (states["TARGET"]-sum(bench))/math.sqrt(var) if var>0 else None
    return {"barrier_n": barrier, "bench_n": len(bench), "hit": hit,
            "bench": float(np.mean(bench)), "z": z}

byfam = defaultdict(list)
for r in recs: byfam[r["family"]].append(r)

print(f"\n{'family':34s} {'n':>7s} {'hit':>7s} | {'P0bench':>8s} {'P0 z':>8s} | {'corr.b':>8s} {'corr z':>8s} | {'d_bench':>8s}")
out = {}
for fam, rows in sorted(byfam.items(), key=lambda kv: -len(kv[1])):
    a = block(rows,"orig",p0_driftless); b = block(rows,"orig",corrected_driftless)
    if not a or not b: continue
    out[fam] = {"p0": a, "corrected": b}
    print(f"{fam:34s} {a['barrier_n']:7d} {a['hit']:7.4f} | {a['bench']:8.4f} {a['z']:8.2f} | "
          f"{b['bench']:8.4f} {b['z']:8.2f} | {b['bench']-a['bench']:8.4f}")

# pooled
a = block(recs,"orig",p0_driftless); b = block(recs,"orig",corrected_driftless)
print(f"{'POOLED (all MARKET)':34s} {a['barrier_n']:7d} {a['hit']:7.4f} | {a['bench']:8.4f} {a['z']:8.2f} | "
      f"{b['bench']:8.4f} {b['z']:8.2f} | {b['bench']-a['bench']:8.4f}")
out["_POOLED"] = {"p0": a, "corrected": b}
json.dump(out, open("/tmp/laneG/bench_p0_vs_corrected.json","w"), indent=1)
