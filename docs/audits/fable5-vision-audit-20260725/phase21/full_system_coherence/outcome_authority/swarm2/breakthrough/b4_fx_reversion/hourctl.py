"""S2b - per-broker-hour lag-1 autocorrelation on three price constructions,
plus the Roll (1984) bound computed against the spread that actually prevails
IN THE HOUR CARRYING THE REVERSION rather than against a seven-hour session median.

That substitution is the whole disagreement with Lane 1 §3.2.  Roll bounds the
bounce-implied spread; comparing it to a quiet-hour median understates the
denominator by an order of magnitude when the reversion is concentrated at the
rollover, where S2 measured a close spread of 3.6-12.9 bp against a 0.4-1.2 bp
quiet median.

Pairing convention: a pair (r_t, r_{t+1}) is assigned to the broker hour of
r_t's own bar, and both bars must lie in the same broker day (no pair crosses
the weekend or the rollover-to-next-day hole).  Three price series:
  bid_c  - last bid of the bar.  What the archive stores.
  mid_c  - last mid of the bar.  Immune to symmetric spread widening.
  mid_tw - quote-life-weighted mid.  Immune to a stale last print.
A pure random walk observed through a time-average has ac1 = +0.25 exactly
(Working 1960), so mid_tw ~ +0.25 with no reversion is the null being confirmed,
not a bug.
"""
from __future__ import annotations
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from bidmid import bars_from_ticks, SYMS   # noqa: E402

OUT = os.path.join(HERE, "receipts")


def pairs_by_hour(b, col):
    lp = np.log(b[col].values)
    r = np.diff(lp)
    bh = b["bh"].values[1:]                 # hour of the bar ENDING the return
    day = b["bdate"].values
    same = (day[1:] == day[:-1])
    ok = np.isfinite(r) & same
    # lag pair (r_t, r_{t+1}) valid when both returns valid and contiguous
    p_ok = ok[:-1] & ok[1:] & (bh[:-1] == bh[1:] - 0)  # r_t hour label
    return r[:-1][ok[:-1] & ok[1:]], r[1:][ok[:-1] & ok[1:]], bh[:-1][ok[:-1] & ok[1:]]


def main():
    rows = []
    for s in SYMS:
        b = bars_from_ticks(s)
        if b is None:
            continue
        b = b.sort_values("bt").reset_index(drop=True)
        store = {}
        for col in ("bid_c", "mid_c", "mid_tw"):
            store[col] = pairs_by_hour(b, col)
        for bh in range(24):
            rec = dict(sym=s, bh=bh)
            n = 0
            for col in ("bid_c", "mid_c", "mid_tw"):
                x, y, h = store[col]
                m = (h == bh)
                if m.sum() < 60:
                    continue
                rec[f"ac1_{col}"] = float(np.corrcoef(x[m], y[m])[0, 1])
                rec[f"sd_{col}_bp"] = float(x[m].std() * 1e4)
                n = int(m.sum())
            if "ac1_bid_c" not in rec:
                continue
            rec["npair"] = n
            g = b[b.bh == bh]
            rec["nbars"] = int(len(g))
            rec["sp_close_med_bp"] = float(g["sp_c"].median() * 1e4)
            rec["sp_close_mean_bp"] = float(g["sp_c"].mean() * 1e4)
            rec["sp_close_p90_bp"] = float(g["sp_c"].quantile(.9) * 1e4)
            rec["sp_intra_med_bp"] = float(g["sp_med"].median() * 1e4)
            var = (rec["sd_bid_c_bp"] * 1e-4) ** 2
            cov1 = rec["ac1_bid_c"] * var
            rec["roll_implied_bp"] = float(2 * np.sqrt(-cov1) * 1e4) if cov1 < 0 else 0.0
            rows.append(rec)
        print("done", s, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/S2b_HOURLY_BIDMID_ROLL.csv", index=False)

    pd.set_option("display.width", 220)
    print("\n=== mean over 12 FX, by BROKER hour (bh 00 = rollover = UTC 21/22) ===")
    print(df.groupby("bh")[["ac1_bid_c", "ac1_mid_c", "ac1_mid_tw",
                            "sp_close_med_bp", "sp_close_p90_bp",
                            "roll_implied_bp", "npair"]].mean().round(4).to_string())
    d = df.copy()
    d["r_med"] = d.roll_implied_bp / d.sp_close_med_bp
    d["r_mean"] = d.roll_implied_bp / d.sp_close_mean_bp
    d["r_p90"] = d.roll_implied_bp / d.sp_close_p90_bp
    print("\n=== Roll-implied / actual close spread (>1 = exceeds the bounce bound) ===")
    print(d.groupby("bh")[["r_med", "r_mean", "r_p90"]].mean().round(3).to_string())


if __name__ == "__main__":
    main()
