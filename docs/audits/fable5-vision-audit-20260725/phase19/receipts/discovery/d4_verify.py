"""d4_verify — for every emitted candidate in a month's roster, check the
condition and the geometry INDEPENDENTLY.  Also checks the reverse direction:
bars where the audit predicts a candidate and the generator emitted none.

Bar resolution follows `_selected_closed_bar_open` (broader_origin_generators.py
:2179-2199): the selected bar is the LAST bar whose close is <= the decision
instant, which is NOT always decision-15m (session gaps make it older).  The
staleness of that bar is measured and reported.

Whole population, no sampling.
"""
from __future__ import annotations
import sys, os, gzip, json, glob, collections, bisect
from datetime import datetime, timedelta
sys.path.insert(0, "/tmp/d4")
import d4_lib as L

RR = 1.5
TOL_REL = 1e-9


def rel(a, b):
    return abs(a - b) / max(abs(a), abs(b), 1e-12)


def selected_index(s, T):
    """last i with t[i] + 15min <= T  (:2196-2198)."""
    j = bisect.bisect_right(s.t, T - timedelta(minutes=15)) - 1
    return j if j >= 0 else None


def run(month, roster_dir, out_path, S=None):
    S = S or L.load_series()
    files = [f for f in sorted(glob.glob(os.path.join(roster_dir, "*.jsonl.gz")))
             if os.path.exists(f.replace(".jsonl.gz", ".stats.json"))]
    emitted = collections.defaultdict(list)
    fam_count = collections.Counter()
    poi_rows = []
    n_rows = 0
    stale_hist = collections.Counter()
    stale_by_fam = collections.defaultdict(collections.Counter)
    for f in files:
        for line in gzip.open(f, "rt"):
            r = json.loads(line)
            if r["k"] != 15:
                continue
            n_rows += 1
            fam = r["f"]
            fam_count[fam] += 1
            T = datetime.fromisoformat(r["t"]).replace(tzinfo=None)
            s = S.get(r["s"])
            i = selected_index(s, T) if s else None
            r["_i"] = i
            r["_T"] = T
            stale = None
            if i is not None:
                stale = int((T - (s.t[i] + timedelta(minutes=15))).total_seconds() // 60)
                stale_hist[stale] += 1
                stale_by_fam[fam][0 if stale == 0 else (1 if stale <= 60 else 2)] += 1
            r["_stale"] = stale
            if fam in L.POI:
                poi_rows.append(r)
                continue
            emitted[(r["s"], i, fam, r["d"])].append(r)

    viol = collections.defaultdict(collections.Counter)
    stats = collections.defaultdict(lambda: {"n": 0, "cond_ok": 0, "entry_ok": 0,
                                             "stop_ok": 0, "tp_ok": 0, "risk_bps": [],
                                             "stale_n": 0})
    for (sym, i, fam, side), rows in emitted.items():
        s = S.get(sym)
        if s is None or i is None:
            viol[fam]["bar_unresolvable"] += len(rows)
            continue
        preds = L.predict_bar(s, i, S)
        pm = {(p[0], p[1]): p for p in preds}
        for r in rows:
            st = stats[fam]
            st["n"] += 1
            if r["_stale"]:
                st["stale_n"] += 1
            p = pm.get((fam, side))
            if p is None:
                viol[fam]["condition_not_satisfied"] += 1
                continue
            st["cond_ok"] += 1
            _, _, pe, pst, ev = p
            e, sl, tp = r["e"], r["sl"], r["tp"]
            if rel(pe, e) <= TOL_REL: st["entry_ok"] += 1
            else: viol[fam]["entry_mismatch"] += 1
            if rel(pst, sl) <= TOL_REL: st["stop_ok"] += 1
            else: viol[fam]["stop_mismatch"] += 1
            ptp = pe + RR * abs(pe - pst) if side == "L" else pe - RR * abs(pe - pst)
            if rel(ptp, tp) <= 1e-8: st["tp_ok"] += 1
            else: viol[fam]["target_mismatch"] += 1
            st["risk_bps"].append(abs(e - sl) / e * 1e4 if e else 0.0)

    # reverse: audit predicts on a bar the generator DID decide on
    decided = collections.defaultdict(set)   # sym -> set of selected indices
    for (sym, i, fam, side) in emitted:
        if i is not None:
            decided[sym].add(i)
    for r in poi_rows:
        if r["_i"] is not None:
            decided[r["s"]].add(r["_i"])
    predicted = collections.Counter(); missing = collections.Counter()
    for sym, idxs in decided.items():
        s = S[sym]
        for i in sorted(idxs):
            if i < 51:
                continue
            for f_, side, e, st_, ev in L.predict_bar(s, i, S):
                predicted[f_] += 1
                if (sym, i, f_, side) not in emitted:
                    missing[f_] += 1

    out = {
        "month": month, "roster_rows_k15": n_rows,
        "family_counts": dict(fam_count),
        "at_market_verification": {},
        "violation_counts": {k: dict(v) for k, v in viol.items()},
        "reverse_check": {"predicted_by_audit_on_decided_bars": dict(predicted),
                          "predicted_but_not_emitted": dict(missing)},
        "staleness_minutes_hist": dict(sorted(stale_hist.items())[:40]),
        "staleness_rows_gt0": sum(v for k, v in stale_hist.items() if k > 0),
        "staleness_rows_total": sum(stale_hist.values()),
        "poi_row_count": len(poi_rows),
    }
    for fam, st in stats.items():
        rb = sorted(st["risk_bps"])
        out["at_market_verification"][fam] = {
            "emitted": st["n"], "condition_satisfied": st["cond_ok"],
            "condition_violation_rate": round(1 - st["cond_ok"] / st["n"], 8) if st["n"] else None,
            "entry_exact": st["entry_ok"], "stop_exact": st["stop_ok"], "target_exact": st["tp_ok"],
            "stale_bar_decisions": st["stale_n"],
            "risk_bps_median": rb[len(rb)//2] if rb else None,
            "risk_bps_p05": rb[int(0.05*len(rb))] if rb else None,
            "risk_bps_p95": rb[int(0.95*len(rb))] if rb else None,
        }
    with open(out_path, "w") as fh:
        json.dump(out, fh, indent=1)
    print(month, "rows", n_rows,
          "cond_viol", sum(v.get("condition_not_satisfied", 0) for v in viol.values()),
          "geom_viol", sum(v.get("entry_mismatch",0)+v.get("stop_mismatch",0)+v.get("target_mismatch",0) for v in viol.values()),
          "unresolvable", sum(v.get("bar_unresolvable",0) for v in viol.values()),
          "missing", sum(missing.values()), "stale>0", out["staleness_rows_gt0"], flush=True)
    return out


if __name__ == "__main__":
    S = L.load_series()
    for arg in sys.argv[1:]:
        m = arg
        rd = f"/tmp/d4/rosters/{m}"
        if not os.path.isdir(rd):
            rd = f"/tmp/f1/roster_{m}"
        run(m, rd, f"/tmp/d4/out/VERIFY_{m}.json", S=S)
