#!/usr/bin/env python3
"""w0_ws — one import for every wave-19 discovery lane.

    import sys; sys.path.insert(0, "docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery")
    import w0_ws
    rows = w0_ws.load()                 # list[dict], 27,658 rows, ~5 s
    df   = w0_ws.load_df()              # pandas DataFrame (only if pandas is installed)

Bar-level R paths (only load these if you actually simulate exits):
    for rp in w0_ws.iter_rpaths():      # streaming, low memory
        rp["fav"], rp["adv"], rp["cls"], rp["off"]
    paths = w0_ws.load_rpaths(ids)      # dict candidate_id -> path row, optionally filtered

Convenience:
    w0_ws.gross(r)                      # the pool's gross (pre-cost) R for a row
    w0_ws.walk(rp, target_r=2.0, stop_r=-1.0, be_at=None, trail=None, max_bars=None)
                                        # honest first-touch exit simulation on one R path

SIGN CONVENTION: every *_r column is signed for the trade's OWN side, so +1R is a gain
for LONG and SHORT alike. See w0_WORKING_SET_README.md.
"""
from __future__ import annotations

import gzip
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
WORKING_SET = os.path.join(HERE, "w0_WORKING_SET.jsonl.gz")
R_PATHS = os.path.join(HERE, "w0_R_PATHS.jsonl.gz")
BUILD_RECEIPT = os.path.join(HERE, "w0_WORKING_SET_BUILD_V2.json")

FAV_LADDER = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0, 5.0]
ADV_LADDER = [-0.25, -0.5, -0.75, -1.0]
BAND_ORDER = ["ge_target", "b_1_to_target", "b_05_to_1", "b_01_to_05",
              "scratch_0_to_01", "partial_loss", "full_stop"]


# --------------------------------------------------------------- loading
def iter_rows(path=WORKING_SET):
    """Stream the scalar working set. Use when you do not need it all in RAM."""
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def load(path=WORKING_SET):
    """Whole scalar working set as list[dict]. ~27,658 rows."""
    return list(iter_rows(path))


def load_df(path=WORKING_SET):
    """pandas DataFrame of the scalar working set."""
    import pandas as pd  # noqa: F401  (optional dependency)
    return pd.DataFrame(load(path))


def iter_rpaths(path=R_PATHS):
    """Stream bar-level R paths: {candidate_id, decision_time_utc, symbol, side,
    risk_distance, policy_target_r, off[], fav[], adv[], cls[]}."""
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def key(row):
    """THE PRIMARY KEY. `candidate_id` ALONE IS NOT UNIQUE -- 21,880 distinct ids across
    27,658 rows, 967 ids repeat, one of them 140 times, and 24.39 % of the pool sits on a
    repeated id. Keying on candidate_id alone silently drops or mis-joins a quarter of the
    pool (91.9 % of `current_fvg_fill`). Always use this."""
    return (row["candidate_id"], row["decision_time_utc"])


def load_rpaths(ids=None, path=R_PATHS):
    """dict (candidate_id, decision_time_utc) -> R-path row.
    `ids` = optional iterable of KEYS (tuples) or bare candidate_ids to keep."""
    keep = set(ids) if ids is not None else None
    out = {}
    for rp in iter_rpaths(path):
        k = key(rp)
        if keep is None or k in keep or rp["candidate_id"] in keep:
            out[k] = rp
    return out


def dedup(rows, how="first"):
    """Collapse pseudo-replication: one row per distinct setup (candidate_id).

    how='first'  keep the earliest emission (is_first_emission)  -> n=21,880
    how='last'   keep the latest emission
    Pool gross mean moves -0.2175 (as shipped) -> -0.2403 (first emission only), so the
    shipped pool is optimistically biased ~0.023 R/trade by the repeats. Any significance
    test over `current_fvg_fill` on the raw 7,146 rows is inflated ~12x. See w0_RESULT.md
    finding W0-F1."""
    if how == "first":
        return [r for r in rows if r.get("is_first_emission")]
    best = {}
    for r in rows:
        c = r["candidate_id"]
        if c not in best or r["setup_dup_rank"] > best[c]["setup_dup_rank"]:
            best[c] = r
    return list(best.values())


def build_receipt(path=BUILD_RECEIPT):
    with open(path) as fh:
        return json.load(fh)


# --------------------------------------------------------------- helpers
def gross(row):
    """Gross (pre-cost) realized R of a pool row: opportunity_net_proxy_r + cost_r.
    Already materialised as row['gross_r']; this is the definition, for auditability."""
    return float(row["opportunity_net_proxy_r"]) + float(row["cost_r"])


def bars_to_fav(row, level):
    """1-based bar index at which +level R was first touched, or None."""
    return row["bars_to_fav"][FAV_LADDER.index(level)]


def bars_to_adv(row, level):
    return row["bars_to_adv"][ADV_LADDER.index(level)]


def walk(rp, target_r=2.0, stop_r=-1.0, be_at=None, trail=None, max_bars=None,
         partial_at=None, partial_frac=0.5, require_fill=True):
    """First-touch exit walk over one R path.

    rp        a row from iter_rpaths()/load_rpaths()
    target_r  take-profit level in R (None = no target)
    stop_r    initial stop in R (normally -1.0)
    be_at     move stop to 0.0 once this favourable R is touched (None = off)
    trail     trail the stop `trail` R behind the running MFE, once MFE >= trail (None = off)
    max_bars  time stop: exit at close of this 1-based bar (None = ride to path end)
    partial_at / partial_frac  scale `partial_frac` of the position out at partial_at R

    require_fill  DEFAULT TRUE, AND YOU ALMOST CERTAINLY WANT IT.  A resting limit at
        entry_price cannot capture excursion that happened before price ever traded there.
        With require_fill the walk starts at the first bar with adv <= 0 and returns
        r=0.0 / exit_reason='no_fill' when entry is never traded.
        Setting it False reproduces the FILL-BLIND convention the pool itself uses, which
        measures +0.041 R/trade over the pool against -0.237 R/trade fill-honest.  In
        `current_fvg_fill` and `current_ob_retest` the fill-blind convention manufactures
        +0.75 and +0.63 R/trade of edge that a limit order could never have taken:
        81.5 % and 80.6 % of their "target-first" paths reach +2R BEFORE entry is traded.
        See w0_RESULT.md finding W0-F2.

    CONSERVATIVE TIE RULE, same as the working set: if stop and target are both reachable
    inside the same M1 bar, the STOP is taken. Returns dict(r, exit_reason, exit_bar).
    """
    fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
    n = len(fav)
    start = 0
    if require_fill:
        start = next((i for i in range(n) if adv[i] <= 1e-12), None)
        if start is None:
            return {"r": 0.0, "exit_reason": "no_fill", "exit_bar": None}
    stop = stop_r
    peak = -1e18
    booked = 0.0
    rem = 1.0
    last = min(n, max_bars) if max_bars else n
    if last <= start:
        return {"r": 0.0, "exit_reason": "no_fill", "exit_bar": None}
    for i in range(start, last):
        f, a = fav[i], adv[i]
        if a <= stop + 1e-12:
            return {"r": booked + rem * stop, "exit_reason": "stop", "exit_bar": i + 1}
        if partial_at is not None and rem > partial_frac and f >= partial_at - 1e-12:
            booked += partial_frac * partial_at
            rem -= partial_frac
        if target_r is not None and f >= target_r - 1e-12:
            return {"r": booked + rem * target_r, "exit_reason": "target", "exit_bar": i + 1}
        if f > peak:
            peak = f
        if be_at is not None and peak >= be_at - 1e-12 and stop < 0.0:
            stop = 0.0
        if trail is not None and peak >= trail:
            stop = max(stop, peak - trail)
    j = last - 1
    return {"r": booked + rem * cls[j], "exit_reason": ("time_stop" if max_bars and n > last else "path_end"),
            "exit_bar": last}


if __name__ == "__main__":
    rows = load()
    n = len(rows)
    g = [r["gross_r"] for r in rows]
    w = [x for x in g if x > 0]
    l = [x for x in g if x <= 0]
    print("rows=%d gross_mean=%.4f win=%.4f winM=%.4f lossM=%.4f"
          % (n, sum(g) / n, len(w) / n, sum(w) / len(w), sum(l) / len(l)))
