"""S2 - the decisive artifact test: rebuild M15 bars from ticks as BID and as MID.

The archive's OHLC is bid-based (MT5 convention).  If the negative
autocorrelation Lane 1 measured is spread-driven -- the bid falling and
recovering as the quote widens and re-tightens around the broker-midnight
rollover -- then the same bars built on the MID will not carry it, because the
mid is unaffected by symmetric widening.  If the reversion is information, bid
and mid carry it equally.

This is the same class of test that killed Lane 5's quote-imbalance signal
(LANE_5 §2.2), run on the other side: not an anchor gap, an anchor *swap*.

Also emitted: a time-weighted mid, which removes the "last print of the bar is a
stale extreme" defect that flipped Lane 5's IC sign.
"""
from __future__ import annotations
import glob, json, os, sys
import numpy as np
import pandas as pd

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "receipts")
CACHE = "/Users/borr/.claude/jobs/adb9e69b/tmp/b4cache"
ROOT = "/Users/borr/GTOSActive/vps-ticks-20260726/ftmo"
os.makedirs(OUT, exist_ok=True)

SYMS = ["CHFJPY", "EURGBP", "EURJPY", "NZDUSD", "GBPJPY", "USDCHF",
        "USDCAD", "GBPUSD", "AUDUSD", "EURUSD", "USDJPY", "AUDJPY"]


def bars_from_ticks(sym):
    f = glob.glob(f"{ROOT}/FTMO_{sym}_ticks_*.csv.gz")
    if not f:
        return None
    d = pd.read_csv(f[0], compression="gzip", usecols=["time", "time_msc", "bid", "ask"])
    t = d["time_msc"].values.astype("int64")
    bid = d["bid"].values.astype(float); ask = d["ask"].values.astype(float)
    ok = np.isfinite(bid) & np.isfinite(ask) & (ask > bid) & (bid > 0)
    t, bid, ask = t[ok], bid[ok], ask[ok]
    mid = 0.5 * (bid + ask)
    slot = t // (15 * 60 * 1000)                    # broker 15-min slot id
    df = pd.DataFrame({"slot": slot, "t": t, "bid": bid, "ask": ask, "mid": mid})
    # time-weighted mid inside each slot: weight each quote by its life
    df["dt"] = np.append(np.diff(t), 0)
    df.loc[df.index[-1], "dt"] = 0
    df["dt"] = df["dt"].clip(lower=0, upper=15 * 60 * 1000)
    g = df.groupby("slot")
    out = pd.DataFrame({
        "bid_c": g["bid"].last(),
        "mid_c": g["mid"].last(),
        "sp_c": (g["ask"].last() - g["bid"].last()) / g["mid"].last(),
        "sp_med": g.apply(lambda x: float(np.median((x.ask - x.bid) / x.mid)), include_groups=False),
        "n": g.size(),
    })
    tw = df.groupby("slot").apply(
        lambda x: float(np.sum(x.mid * x.dt) / max(np.sum(x.dt), 1)) if np.sum(x.dt) > 0
        else float(x.mid.mean()), include_groups=False)
    out["mid_tw"] = tw
    out = out.reset_index()
    out["bt"] = pd.to_datetime(out["slot"] * 15 * 60, unit="s")
    out["bh"] = out["bt"].dt.hour
    out["bdate"] = out["bt"].dt.normalize()
    return out


def ac1_by(series, grp):
    """lag-1 autocorrelation of log returns computed inside contiguous groups."""
    vals = []
    for _, g in grp:
        r = np.diff(np.log(g))
        r = r[np.isfinite(r)]
        if len(r) > 3:
            vals.append(r)
    if not vals:
        return np.nan, 0
    x = np.concatenate([v[:-1] for v in vals])
    y = np.concatenate([v[1:] for v in vals])
    if len(x) < 50:
        return np.nan, len(x)
    return float(np.corrcoef(x, y)[0, 1]), len(x)


def main():
    rows = []
    for s in SYMS:
        b = bars_from_ticks(s)
        if b is None or len(b) < 500:
            print("no ticks", s, flush=True); continue
        b = b.sort_values("bt").reset_index(drop=True)
        b["is_late"] = b["bh"].isin([20, 21, 22, 23, 0, 1, 2])   # broker cover of UTC 17-24
        for cell, sel in (("all", np.ones(len(b), bool)),
                          ("late_broker", b["is_late"].values),
                          ("roll_h23_00", b["bh"].isin([23, 0]).values),
                          ("late_no_roll", (b["is_late"] & ~b["bh"].isin([23, 0])).values)):
            bb = b[sel]
            if len(bb) < 300:
                continue
            grp_key = bb["bdate"].astype(str) + "_" + (bb["bh"] // 6).astype(str)
            r = {}
            for col in ("bid_c", "mid_c", "mid_tw"):
                a, n = ac1_by(bb[col].values, bb.groupby(grp_key, sort=False)[col])
                r[f"ac1_{col}"] = a; r["n"] = n
            rows.append(dict(sym=s, cell=cell,
                             sp_med_bp=float(bb["sp_med"].median() * 1e4),
                             sp_close_bp=float(bb["sp_c"].median() * 1e4),
                             sp_close_p90_bp=float(bb["sp_c"].quantile(.9) * 1e4),
                             nbars=int(len(bb)), **r))
        print("done", s, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(f"{OUT}/S2_BID_VS_MID_AC1.csv", index=False)
    print(df.to_string())


if __name__ == "__main__":
    main()
