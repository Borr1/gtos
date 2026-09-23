"""w0-capture (2nd pass): reconstruct the DECISION-TIME market price from raw M1 bars.

The sidecar path starts at decision_time + 1 minute, so no prior lane could see where the
market actually was when the candidate was emitted.  That is the difference between
  "a resting limit that price later collapsed through"  (legitimate trade, real loss)
  "a limit emitted already beyond its own stop"          (simulation artifact, fake loss)
Both look identical at path bar 1.  This settles it.
"""
import sys, os, json, gzip, bisect, csv, statistics as st
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import w0_ws

BARS = "/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/bridge_ftmo_m1_202601"

def load_bars(sym):
    p = os.path.join(BARS, f"{sym}_M1.csv")
    if not os.path.isfile(p): return None
    ts, o, h, l, c = [], [], [], [], []
    with open(p) as f:
        rd = csv.reader(f); next(rd)
        for r in rd:
            ts.append(r[0]); o.append(float(r[1])); h.append(float(r[2])); l.append(float(r[3])); c.append(float(r[4]))
    return {"t": ts, "o": o, "h": h, "l": l, "c": c}

rows = w0_ws.load()
syms = sorted({r["symbol"] for r in rows})
cache = {}
missing = []
for s in syms:
    b = load_bars(s)
    if b is None: missing.append(s)
    else: cache[s] = b

out = []
nofit = 0
for r in rows:
    sym = r["symbol"]; b = cache.get(sym)
    if b is None:
        nofit += 1; continue
    dt = r["decision_time_utc"]
    i = bisect.bisect_right(b["t"], dt) - 1          # last bar with time <= decision_time
    if i < 0:
        nofit += 1; continue
    entry = r["entry_price"]; d = r["risk_distance"]; side = r["side"]
    sgn = 1.0 if side == "LONG" else -1.0
    def rr(px): return sgn * (px - entry) / d
    # anchor A: the bar STAMPED at/just before the decision minute  (covers the decision instant)
    aC = rr(b["c"][i]); aH = rr(b["h"][i]); aL = rr(b["l"][i]); aO = rr(b["o"][i])
    exact = (b["t"][i] == dt)
    # anchor B: the last FULLY CLOSED bar strictly before the decision minute
    j = i - 1 if exact else i
    if j < 0: j = 0
    bC = rr(b["c"][j])
    # the "hole": is there a bar between the decision anchor and the first path bar?
    out.append({
        "candidate_id": r["candidate_id"], "decision_time_utc": dt, "symbol": sym, "side": side,
        "family": r.get("family"), "gross_r": r.get("gross_r"),
        "risk_distance": d, "entry_price": entry,
        "anchor_bar_time": b["t"][i], "anchor_exact": exact,
        "mkt_r_close": round(aC, 6), "mkt_r_high": round(max(aH, aL), 6), "mkt_r_low": round(min(aH, aL), 6),
        "mkt_r_open": round(aO, 6),
        "mkt_r_prev_close": round(bC, 6),
        "bars_to_entry_touch": r.get("bars_to_entry_touch"),
        "fill_class_fav_at_touch": None,
    })

with gzip.open(os.path.join(D, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz"), "wt") as f:
    for o_ in out: f.write(json.dumps(o_) + "\n")
print(json.dumps({"rows": len(out), "no_bar_fit": nofit, "missing_symbols": missing,
                  "anchor_exact_share": round(sum(1 for o_ in out if o_["anchor_exact"]) / max(1, len(out)), 6)}))
