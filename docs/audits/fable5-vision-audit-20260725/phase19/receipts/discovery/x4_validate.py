#!/usr/bin/env python3
"""x4 validation: prove the M1 composition IS the M15 bar the generator read, and that
nothing in the feature set can see past the decision instant."""
import bisect, csv, datetime as dt, gzip, json, os, sys, collections
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import w0_ws
from x4_build_intrabar import BARS, load_sym, tmin, slice_idx

M15 = os.path.join(BARS, "bridge_ftmo_m15_20250601_20260610")
out = {}

# ---- 1. composition identity: M1[T-15..T-1] must reproduce the M15 bar stamped T-15 ----
comp = {}
for sym in ["EURUSD", "GER40", "BTCUSD", "XAUUSD", "US30_cash", "UK100"]:
    b = load_sym(sym)
    p = os.path.join(M15, f"{sym}_M15.csv")
    if not os.path.isfile(p):
        comp[sym] = "no_m15_file"; continue
    nt = nm = nhl = 0
    with open(p) as fh:
        rd = csv.reader(fh); next(rd)
        for r in rd:
            t = tmin(r[0])
            if t < tmin("2026-01-01T00:00:00+00:00") or t >= tmin("2026-02-01T00:00:00+00:00"):
                continue
            a, z = slice_idx(b, t, t + 15)
            if z - a != 15:
                continue
            nt += 1
            H = max(b["h"][a:z]); L = min(b["l"][a:z])
            O = b["o"][a]; C = b["c"][z - 1]
            if abs(H - float(r[2])) < 1e-9 and abs(L - float(r[3])) < 1e-9:
                nhl += 1
            if abs(O - float(r[1])) < 1e-9 and abs(C - float(r[4])) < 1e-9:
                nm += 1
    comp[sym] = {"full_15bar_m15_bars": nt, "high_low_match": nhl, "open_close_match": nm}
out["composition_identity_open_stamped"] = comp

# ---- 2. lag / coverage census -----------------------------------------------
rows = {w0_ws.key(r): r for r in w0_ws.load()}
lag = collections.Counter(); nbar = collections.Counter(); miss = collections.Counter()
X = []
with gzip.open(os.path.join(D, "x4_INTRABAR_V1.jsonl.gz"), "rt") as fh:
    for line in fh:
        f = json.loads(line); X.append(f)
        nbar[f.get("n_m1_in_bar", 0)] += 1
        if f.get("n_m1_in_bar"):
            lag[f.get("bar_end_lag_min")] += 1
out["n_m1_in_bar_hist"] = dict(sorted(nbar.items()))
out["bar_end_lag_min_hist"] = dict(sorted(lag.items())[:10])
out["rows"] = len(X)
out["join_ok"] = sum(1 for f in X if (f["candidate_id"], f["decision_time_utc"]) in rows)

# ---- 3. leakage guard: correlate close_to_entry_R with the known born-state anchor ----
anc = {}
with gzip.open(os.path.join(D, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz"), "rt") as fh:
    for line in fh:
        a = json.loads(line); anc[(a["candidate_id"], a["decision_time_utc"])] = a
agree = 0; tot = 0; dmax = 0.0
for f in X:
    k = (f["candidate_id"], f["decision_time_utc"])
    a = anc.get(k)
    if a is None or f.get("close_to_entry_R") is None:
        continue
    tot += 1
    dd = abs(a["mkt_r_prev_close"] - f["close_to_entry_R"])
    dmax = max(dmax, dd)
    if dd < 1e-4:
        agree += 1
out["anchor_cross_check"] = {"compared": tot, "agree_within_1e-4": agree,
                             "max_abs_diff": round(dmax, 6),
                             "note": "close_to_entry_R must equal w0-capture's mkt_r_prev_close "
                                     "(last fully closed M1 bar strictly before the decision)"}

# ---- 4. missing-feature census -----------------------------------------------
keys = sorted({k for f in X for k in f})
nn = {k: sum(1 for f in X if f.get(k) is None) for k in keys}
out["null_counts"] = {k: v for k, v in sorted(nn.items(), key=lambda kv: -kv[1]) if v}
print(json.dumps(out, indent=1))
json.dump(out, open(os.path.join(D, "x4_VALIDATE_V1.json"), "w"), indent=1)
