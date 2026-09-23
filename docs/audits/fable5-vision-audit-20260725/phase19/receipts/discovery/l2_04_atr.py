"""l2 step 4a — pre-decision ATR per candidate, strictly no look-ahead.

Bars are OPEN-stamped (proved by w0-capture), so the last bar fully observable at decision
instant T is the one stamped T-1min.  ATR_n = mean true range over the n available bars whose
stamp is STRICTLY BEFORE T.  Robust to gaps (bisect, not arithmetic on timestamps).
Emits l2_ATR_V1.jsonl.gz: cid, dt, sym, atr60, atr240, rd (risk_distance), stop_in_atr60,
stop_in_atr240, spread_price, spread_in_atr60.
"""
import sys, os, json, gzip, csv, bisect
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import w0_ws

BARS = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/"
        "cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/bridge_ftmo_m1_202601")
OUT = os.path.join(D, "l2_ATR_V1.jsonl.gz")

rows = w0_ws.load()
bysym = {}
for r in rows:
    bysym.setdefault(r["symbol"], []).append(r)

n_ok = 0; n_miss = 0
with gzip.open(OUT, "wt") as fh:
    for sym, rs in sorted(bysym.items()):
        p = os.path.join(BARS, f"{sym}_M1.csv")
        if not os.path.isfile(p):
            n_miss += len(rs); continue
        ts = []; hi = []; lo = []; cl = []
        with open(p) as f:
            rd = csv.reader(f); next(rd)
            for x in rd:
                ts.append(x[0]); hi.append(float(x[2])); lo.append(float(x[3])); cl.append(float(x[4]))
        # prefix sums of true range for O(1) window means
        tr = [0.0] * len(ts)
        for i in range(len(ts)):
            if i == 0:
                tr[i] = hi[i] - lo[i]
            else:
                tr[i] = max(hi[i] - lo[i], abs(hi[i] - cl[i - 1]), abs(lo[i] - cl[i - 1]))
        pre = [0.0]
        for v in tr:
            pre.append(pre[-1] + v)
        for r in rs:
            j = bisect.bisect_left(ts, r["decision_time_utc"])   # first bar stamped >= T
            rec = {"cid": r["candidate_id"], "dt": r["decision_time_utc"], "sym": sym,
                   "rd": r["risk_distance"], "px": r.get("entry_price")}
            for n_, lab in ((60, "atr60"), (240, "atr240")):
                a = max(0, j - n_)
                cnt = j - a
                rec[lab] = ((pre[j] - pre[a]) / cnt) if cnt > 0 else None
                rec[lab + "_bars"] = cnt
            for lab in ("atr60", "atr240"):
                rec["stop_in_" + lab] = (r["risk_distance"] / rec[lab]) if rec[lab] else None
            sp_r = r.get("spread_r")
            rec["spread_price"] = (sp_r * r["risk_distance"]) if sp_r is not None else None
            rec["spread_in_atr60"] = ((sp_r * r["risk_distance"]) / rec["atr60"]) if (sp_r is not None and rec["atr60"]) else None
            fh.write(json.dumps(rec, separators=(",", ":")) + "\n")
            n_ok += 1
print("wrote", OUT, "ok", n_ok, "missing_symbol_rows", n_miss)
