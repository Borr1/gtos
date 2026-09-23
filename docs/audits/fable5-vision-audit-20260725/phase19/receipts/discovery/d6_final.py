"""d6_final — the three numbers the verdict rests on, plus the strict out-of-sample cut.

  * the counterfactual ceiling under the LIVE placement contract (capacity-true)
  * every arm re-scored on February + March only, i.e. with the January window
    that CHOSE the five families removed entirely
  * total R, not just R/trade, because the partial book takes 1.4x the trades
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[5]))

import d6_lib as D  # noqa: E402
from src.research_infra.walkforward import stats as S  # noqa: E402


def econ(trades, label):
    g = c = 0.0
    n = 0
    by_day = defaultdict(float)
    trunc = 0
    for r, arm in trades:
        a = r.get(arm)
        if not a:
            continue
        g += a["g2"]
        c += a["cr"]
        n += 1
        trunc += (a["x2"] == "path_end")
        day = (r["day_part"] if arm in ("P", "D") else r["day_close"])
        by_day[r["m"] + "|" + day] += a["g2"] - a["cr"]
    if not n:
        return {"label": label, "n": 0}
    days = sorted(by_day)
    ser = np.array([by_day[d] for d in days])
    block = S.block_length_auto(list(ser)) if len(ser) > 3 else 1
    p = (S.day_block_bootstrap_p(list(ser), block=int(block), n_boot=20000)["p_value"]
         if len(ser) > 3 else float("nan"))
    return {"label": label, "n": n,
            "gross_r": g / n, "cost_r": c / n, "net_r": (g - c) / n,
            "total_net_r": float(ser.sum()),
            "truncation_share": trunc / n,
            "n_days": len(days), "days_positive": int((ser > 0).sum()),
            "r_per_day": float(ser.mean()), "trades_per_day": n / len(days),
            "p_value_day_blocked": p}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    months = [m for m in args.months.split(",") if m] or D.months_available()
    E5 = set(D.EARLY5)
    atm = {m: D.load(m, fams=set(D.AT_MARKET)) for m in months}

    def sel(fams, mode, arm, ms):
        out = []
        for m in ms:
            rr = [r for r in atm[m] if r["f"] in fams]
            if arm == "paired_partial":
                cand = [(r, "P") for r in rr if r.get("C") and r.get("P")]
            elif arm == "paired_close":
                cand = [(r, "C") for r in rr if r.get("C") and r.get("P")]
            elif arm == "partial":
                cand = ([(r, "P") for r in rr if r.get("P")]
                        + [(r, "C") for r in rr if r.get("C") and not r.get("P")])
            else:
                cand = [(r, "C") for r in rr if r.get("C")]
            if mode == "live":
                best = {}
                for r, a in cand:
                    t = r["t_part"] if a == "P" else r["t_close"]
                    day = r["day_part"] if a == "P" else r["day_close"]
                    k = (r["f"], r["s"], day)
                    if k not in best or t < best[k][2]:
                        best[k] = (r, a, t)
                cand = [(r, a) for r, a, _t in best.values()]
            out += cand
        return out

    res = {"months": months,
           "generated_utc": datetime.now(timezone.utc).isoformat(), "cuts": {}}
    cuts = {"ALL": months}
    oos = [m for m in months if m != "202601"]
    if oos:
        cuts["OOS_EXCLUDING_THE_SELECTION_MONTH"] = oos
    for cut, ms in cuts.items():
        res["cuts"][cut] = {
            "close_book_nodedup": econ(sel(E5, "none", "close", ms), "close_book"),
            "partial_book_nodedup": econ(sel(E5, "none", "partial", ms), "partial_book"),
            "close_book_live_dedup": econ(sel(E5, "live", "close", ms), "close_live"),
            "partial_book_live_dedup": econ(sel(E5, "live", "partial", ms), "partial_live"),
            "paired_close_COUNTERFACTUAL": econ(sel(E5, "none", "paired_close", ms), "paired_close"),
            "paired_partial_COUNTERFACTUAL": econ(sel(E5, "none", "paired_partial", ms), "paired_partial"),
            "paired_partial_live_dedup_COUNTERFACTUAL": econ(
                sel(E5, "live", "paired_partial", ms), "paired_partial_live"),
            "paired_close_live_dedup_COUNTERFACTUAL": econ(
                sel(E5, "live", "paired_close", ms), "paired_close_live"),
        }
    Path(args.out).write_text(json.dumps(res, indent=1))
    print("wrote", args.out)


if __name__ == "__main__":
    main()
