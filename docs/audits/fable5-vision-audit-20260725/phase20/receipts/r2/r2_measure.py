"""r2_measure — whole-population census of the three generator defects.

Reads the eight regenerated close-only rosters (Session PB harness, unmodified
production generator, min_rr=1.5, true-UTC lane inputs) and the true-UTC M15
lane-input bars, and measures, for EVERY origin family:

  * fill_gap_R = (cp - entry)/risk * (+1 LONG, -1 SHORT), cp = close of the
    SELECTED closed bar (`broader_origin_generators.py:1085`), partitioned into
    past_stop / marketable / resting / target_through.
  * the selected-bar AGE at the decision instant = T - (selected.time + 15min),
    and the displacement between the emitted entry and the next actual print,
    in R, per age bucket.

The roster records `b` as the NOMINAL bar (T-15m), so the selected bar is
recovered here the way `_selected_closed_bar_open` (:2179-2199) selects it:
the last bar whose close is <= T + 2s.

No sampling.  Every roster row in every window.
"""
from __future__ import annotations

import bisect
import collections
import csv
import glob
import gzip
import json
import os
import sys
from datetime import datetime, timedelta

BARS = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
        "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/"
        "bridge_ftmo_m15_20250601_20260610")

ROSTERS = {
    "202510": "/tmp/f1/roster_202510",
    "202511": "/tmp/f1/roster_202511",
    "202512": "/tmp/f1/roster_202512",
    "202601": "/tmp/d4/rosters/202601",
    "202602": "/tmp/d4/rosters/202602",
    "202603": "/tmp/d4/rosters/202603",
    "202604": "/tmp/f1/roster_202604",
    "202605": "/tmp/f1/roster_202605",
}
RR = 1.5
POI = {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}


class Series:
    __slots__ = ("t", "o", "h", "l", "c")

    def __init__(self, rows):
        self.t = [r[0] for r in rows]
        self.o = [r[1] for r in rows]
        self.h = [r[2] for r in rows]
        self.l = [r[3] for r in rows]
        self.c = [r[4] for r in rows]


def load_series():
    out = {}
    for p in sorted(glob.glob(os.path.join(BARS, "*_M15.csv"))):
        sym = os.path.basename(p)[: -len("_M15.csv")]
        rows = []
        with open(p, newline="") as fh:
            for r in csv.DictReader(fh):
                rows.append((
                    datetime.fromisoformat(r["time"]).replace(tzinfo=None),
                    float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]),
                ))
        rows.sort()
        out[sym] = Series(rows)
    return out


def q(v, p):
    if not v:
        return None
    v = sorted(v)
    return v[min(len(v) - 1, int(p * len(v)))]


_BUCKETS = ["a==0", "0<a<=15", "15<a<=60", "60<a<=240", "240<a<=1440", "a>1440"]


def _age_bucket(age):
    if age <= 0:
        return "a==0"
    if age <= 15:
        return "0<a<=15"
    if age <= 60:
        return "15<a<=60"
    if age <= 240:
        return "60<a<=240"
    if age <= 1440:
        return "240<a<=1440"
    return "a>1440"


def main():
    S = load_series()
    fam = collections.defaultdict(lambda: {
        "n": 0, "bins": collections.Counter(), "gap": [], "risk_bps": [],
        "n_stale": 0, "no_series": 0,
        "disp_by_age": collections.defaultdict(list),
        "bins_by_age": collections.defaultdict(collections.Counter),
        "nonzero_gap": 0,
    })
    per_window = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    # global age histogram (all families) and per-symbol stale rate
    age_hist = collections.Counter()
    stale_symbol = collections.Counter()
    all_symbol = collections.Counter()
    stale_dow_hour = collections.Counter()

    for win, rd in sorted(ROSTERS.items()):
        for f in sorted(glob.glob(os.path.join(rd, "*.jsonl.gz"))):
            if not os.path.exists(f.replace(".jsonl.gz", ".stats.json")):
                continue
            for line in gzip.open(f, "rt"):
                r = json.loads(line)
                if r["k"] != 15:
                    continue
                s = S.get(r["s"])
                a = fam[r["f"]]
                a["n"] += 1
                all_symbol[r["s"]] += 1
                if s is None:
                    a["no_series"] += 1
                    continue
                T = datetime.fromisoformat(r["t"]).replace(tzinfo=None)
                # _selected_closed_bar_open: last bar whose close <= T + 2s
                i = bisect.bisect_right(s.t, T - timedelta(minutes=15) + timedelta(seconds=2)) - 1
                if i < 0:
                    a["no_series"] += 1
                    continue
                cp = s.c[i]
                e, sl = r["e"], r["sl"]
                risk = abs(e - sl)
                if risk <= 0:
                    continue
                sgn = 1.0 if r["d"] == "L" else -1.0
                gap = (cp - e) / risk * sgn
                b = ("past_stop" if gap < -1 else
                     "marketable" if gap < 0 else
                     "resting" if gap < RR else "target_through")
                a["gap"].append(gap)
                a["risk_bps"].append(risk / e * 1e4)
                a["bins"][b] += 1
                if abs(gap) > 1e-9:
                    a["nonzero_gap"] += 1
                per_window[win][r["f"]][b] += 1

                age = int((T - (s.t[i] + timedelta(minutes=15))).total_seconds() // 60)
                bucket = _age_bucket(age)
                age_hist[age] += 1
                a["bins_by_age"][bucket][b] += 1
                if age > 0:
                    a["n_stale"] += 1
                    stale_symbol[r["s"]] += 1
                    stale_dow_hour[(T.weekday(), T.hour)] += 1
                    if i + 1 < len(s.t):
                        a["disp_by_age"][bucket].append(abs(s.o[i + 1] - e) / risk)

    out = {"rr": RR, "windows": sorted(ROSTERS), "families": {}, "per_window_bins": {}}
    tot = collections.Counter()
    tot_stale = 0
    tot_n = 0
    for name, a in sorted(fam.items()):
        n = a["n"]
        tot_n += n
        tot_stale += a["n_stale"]
        tot.update(a["bins"])
        g = a["gap"]
        alldisp = [x for v in a["disp_by_age"].values() for x in v]
        out["families"][name] = {
            "kind": "POI_limit" if name in POI else "at_market",
            "n": n, "no_series": a["no_series"], "bins": dict(a["bins"]),
            "share_past_stop": round(a["bins"]["past_stop"] / n, 8) if n else None,
            "share_marketable": round(a["bins"]["marketable"] / n, 8) if n else None,
            "share_resting": round(a["bins"]["resting"] / n, 8) if n else None,
            "share_target_through": round(a["bins"]["target_through"] / n, 8) if n else None,
            "rows_with_nonzero_gap_r": a["nonzero_gap"],
            "gap_r_median": q(g, 0.5), "gap_r_p05": q(g, 0.05), "gap_r_p95": q(g, 0.95),
            "risk_bps_median": q(a["risk_bps"], 0.5),
            "n_stale": a["n_stale"],
            "share_stale": round(a["n_stale"] / n, 8) if n else None,
            "stale_disp_r_median": q(alldisp, 0.5),
            "stale_disp_r_p75": q(alldisp, 0.75),
            "stale_disp_r_p95": q(alldisp, 0.95),
            "stale_disp_share_over_1R": (
                round(sum(1 for x in alldisp if x > 1.0) / len(alldisp), 6) if alldisp else None),
            "disp_by_age_bucket": {
                k: {"n": len(v), "median_R": q(v, 0.5), "p95_R": q(v, 0.95),
                    "share_over_1R": round(sum(1 for x in v if x > 1.0) / len(v), 6)}
                for k, v in sorted(a["disp_by_age"].items(), key=lambda kv: _BUCKETS.index(kv[0]))},
            "bins_by_age_bucket": {
                k: dict(v) for k, v in
                sorted(a["bins_by_age"].items(), key=lambda kv: _BUCKETS.index(kv[0]))},
        }
    for w, d in per_window.items():
        out["per_window_bins"][w] = {k: dict(v) for k, v in sorted(d.items())}
    out["total_bins"] = dict(tot)
    out["total_rows"] = tot_n
    out["total_stale"] = tot_stale
    out["share_stale_all"] = round(tot_stale / tot_n, 8)
    out["age_hist_minutes"] = {str(k): v for k, v in sorted(age_hist.items())}
    out["stale_rate_by_symbol"] = {
        s: {"n": all_symbol[s], "stale": stale_symbol.get(s, 0),
            "share": round(stale_symbol.get(s, 0) / all_symbol[s], 6)}
        for s in sorted(all_symbol)}
    out["stale_by_weekday_hour_top"] = {
        f"dow{k[0]}_h{k[1]:02d}": v for k, v in stale_dow_hour.most_common(20)}
    json.dump(out, open(sys.argv[1], "w"), indent=1, default=str)

    hdr = f"{'family':36s} {'n':>9s} {'past_stop':>10s} {'mktable':>9s} {'resting':>9s} {'tgt_thru':>9s} {'riskbps':>8s} {'stale%':>8s}"
    print(hdr)
    for k, v in out["families"].items():
        print(f"{k:36s} {v['n']:9d} {v['share_past_stop']:10.6f} {v['share_marketable']:9.6f} "
              f"{v['share_resting']:9.6f} {v['share_target_through']:9.6f} "
              f"{(v['risk_bps_median'] or 0):8.3f} {100*v['share_stale']:8.4f}")
    print("TOTAL bins", out["total_bins"], "rows", tot_n, "stale", tot_stale,
          f"({100*out['share_stale_all']:.4f}%)")
    print("age hist (minutes:count) first 12:", list(out["age_hist_minutes"].items())[:12])


if __name__ == "__main__":
    main()
