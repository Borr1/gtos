"""d4_poi — geometry audit of the three POI (limit-order) families.

For every emitted POI candidate the decision-instant market price is the close of
the selected closed M15 bar (`broader_origin_generators.py:1085`
``current_price = latest.close``).  The candidate is a RESTING LIMIT at
``entry`` = the zone midpoint (:1625) with ``stop`` = zone edge -/+ buffer*ATR
(:1627).  One scalar characterises the whole contract:

    fill_gap_R = (current_price - entry)/risk   * (+1 LONG, -1 SHORT)

  fill_gap_R  < -1        market is ALREADY BEYOND THE STOP  ("born past stop")
  -1..0                   limit is marketable (would fill now, worse than limit)
  0..rr                   proper resting limit
  >= rr                   TARGET ALREADY THROUGH: the whole reward is behind
                          the market; the limit can only fill on a >= rr
                          adverse excursion.

Nothing in `src/` compares current_price to the candidate's own stop or target
(searched: no `past_stop`/`stop_breached`/`beyond_stop` predicate exists).
"""
from __future__ import annotations
import sys, os, gzip, json, glob, collections, bisect, math
from datetime import datetime, timedelta
sys.path.insert(0, "/tmp/d4")
import d4_lib as L

RR = 1.5
BUFFER = {"current_fvg_fill": 0.25, "current_breaker_re_entry": 0.25,
          "current_ob_retest": 0.5}
PROX_TOL = 0.01


def selected_index(s, T):
    j = bisect.bisect_right(s.t, T - timedelta(minutes=15)) - 1
    return j if j >= 0 else None


def run(months, out_path):
    S = L.load_series()
    agg = collections.defaultdict(lambda: {
        "n": 0, "bins": collections.Counter(), "risk_bps": [], "gap": [],
        "prox_recorded": [], "prox_recomputed_ok": 0, "prox_recomputed_n": 0,
        "atr_ratio": [], "zone_width_atr": [], "stale": 0,
        "marketable_fillprob": 0, "fillprob_n": 0, "fillprob_paststop_sum": 0.0,
        "fillprob_paststop_n": 0, "fillprob_proper_sum": 0.0, "fillprob_proper_n": 0,
    })
    per_month = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for m in months:
        rd = f"/tmp/d4/rosters/{m}"
        if not os.path.isdir(rd):
            rd = f"/tmp/f1/roster_{m}"
        files = [f for f in sorted(glob.glob(os.path.join(rd, "*.jsonl.gz")))
                 if os.path.exists(f.replace(".jsonl.gz", ".stats.json"))]
        for f in files:
            for line in gzip.open(f, "rt"):
                r = json.loads(line)
                if r["k"] != 15 or r["f"] not in L.POI:
                    continue
                s = S.get(r["s"])
                if s is None:
                    continue
                T = datetime.fromisoformat(r["t"]).replace(tzinfo=None)
                i = selected_index(s, T)
                if i is None:
                    continue
                cp = s.c[i]                     # :1085 current_price = latest.close
                e, sl, tp = r["e"], r["sl"], r["tp"]
                risk = abs(e - sl)
                if risk <= 0:
                    continue
                sgn = 1.0 if r["d"] == "L" else -1.0
                gap = (cp - e) / risk * sgn
                a = agg[r["f"]]
                a["n"] += 1
                a["gap"].append(gap)
                a["risk_bps"].append(risk / e * 1e4)
                if (T - (s.t[i] + timedelta(minutes=15))).total_seconds() > 0:
                    a["stale"] += 1
                b = ("past_stop" if gap < -1 else
                     "marketable" if gap < 0 else
                     "resting" if gap < RR else "target_through")
                a["bins"][b] += 1
                per_month[m][r["f"]][b] += 1
                # ---- recover the implied zone and re-check the proximity gate
                a14 = L.atr(s, i, 14)
                buf = BUFFER[r["f"]]
                if r.get("cp") is not None:
                    # DIAG present: use the generator's OWN current_price + proximity
                    a["prox_recomputed_n"] += 1
                    if abs(r["cp"] - cp) / max(abs(cp), 1e-12) < 1e-9:
                        a["prox_recomputed_ok"] += 1
                if r.get("pr") is not None:
                    a["prox_recorded"].append(r["pr"])
                # zone from geometry: LONG stop = low - buf*atr_mso ; entry = (low+high)/2
                if a14 and a14 > 0:
                    # implied atr_mso from the buffer is unrecoverable without the
                    # zone, but the ZONE WIDTH in generator-ATR units is:
                    #   LONG: low = sl + buf*atr_mso ; high = 2e-low
                    #   width = 2*(e - low) = 2*(e - sl - buf*atr_mso)
                    # use the generator ATR as the yardstick and report the ratio
                    a["zone_width_atr"].append(2.0 * abs(e - sl) / a14)
                if r.get("fp") is not None:
                    a["fillprob_n"] += 1
                    if gap < 0:
                        a["marketable_fillprob"] += 1
                    if gap < -1:
                        a["fillprob_paststop_sum"] += r["fp"]; a["fillprob_paststop_n"] += 1
                    elif 0 <= gap < RR:
                        a["fillprob_proper_sum"] += r["fp"]; a["fillprob_proper_n"] += 1

    def q(v, p):
        if not v: return None
        v = sorted(v); return v[min(len(v) - 1, int(p * len(v)))]

    out = {"months": months, "rr": RR, "families": {}, "per_month_bins": {}}
    for fam, a in agg.items():
        n = a["n"]
        out["families"][fam] = {
            "n": n,
            "share_past_stop": round(a["bins"]["past_stop"] / n, 6),
            "share_marketable_inside_stop": round(a["bins"]["marketable"] / n, 6),
            "share_proper_resting_limit": round(a["bins"]["resting"] / n, 6),
            "share_target_already_through": round(a["bins"]["target_through"] / n, 6),
            "bins": dict(a["bins"]),
            "fill_gap_R_median": q(a["gap"], 0.5),
            "fill_gap_R_p05": q(a["gap"], 0.05),
            "fill_gap_R_p95": q(a["gap"], 0.95),
            "risk_bps_median": q(a["risk_bps"], 0.5),
            "risk_bps_p05": q(a["risk_bps"], 0.05),
            "zone_width_in_generator_atr_median": q(a["zone_width_atr"], 0.5),
            "stale_bar_decisions": a["stale"],
            "recorded_proximity_median": q(a["prox_recorded"], 0.5),
            "diag_current_price_matches_bar_close": (
                f'{a["prox_recomputed_ok"]}/{a["prox_recomputed_n"]}'
                if a["prox_recomputed_n"] else None),
            "fill_probability_rows": a["fillprob_n"],
            "mean_fill_prob_when_past_stop": (
                round(a["fillprob_paststop_sum"] / a["fillprob_paststop_n"], 6)
                if a["fillprob_paststop_n"] else None),
            "mean_fill_prob_when_proper_resting": (
                round(a["fillprob_proper_sum"] / a["fillprob_proper_n"], 6)
                if a["fillprob_proper_n"] else None),
            "n_past_stop_with_fillprob": a["fillprob_paststop_n"],
            "n_proper_with_fillprob": a["fillprob_proper_n"],
        }
    for m, fams in per_month.items():
        out["per_month_bins"][m] = {f: dict(c) for f, c in fams.items()}
    with open(out_path, "w") as fh:
        json.dump(out, fh, indent=1)
    for fam, v in out["families"].items():
        print(f'{fam:28s} n={v["n"]:7d} past_stop={v["share_past_stop"]:.4f} '
              f'mkt={v["share_marketable_inside_stop"]:.4f} rest={v["share_proper_resting_limit"]:.4f} '
              f'tgt_through={v["share_target_already_through"]:.4f} gapR_med={v["fill_gap_R_median"]:.3f} '
              f'riskbps_med={v["risk_bps_median"]:.2f}', flush=True)
    return out


if __name__ == "__main__":
    run(sys.argv[1:-1], sys.argv[-1])
