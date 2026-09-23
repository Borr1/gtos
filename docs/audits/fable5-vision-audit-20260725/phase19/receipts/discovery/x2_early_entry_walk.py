"""x2 — EXACT economics of entering at m* instead of the M15 close.

Contract: identical stop_loss and take_profit_1 PRICE LEVELS; only the entry price
changes (close of M1 minute m* instead of the M15 close). Outcome is expressed in
units of the ORIGINAL risk_distance d, so it is directly comparable to plain_walk_r.

Because the exit levels are unchanged:
    R_early = plain_walk_r + price_edge_r
UNLESS the position resolves inside the remaining minutes of the decision bar
(minutes m*+1 .. 15), which the sidecar path — which starts at the bar AFTER the
decision — cannot see. That remainder is walked here on M1, conservatively
(target and stop in the same M1 bar -> stop, matching w0_ws.walk).
"""
from __future__ import annotations

import gzip
import json
import os
import sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws  # noqa: E402
import x2_bars  # noqa: E402

ROWS = os.path.join(HERE, "x2_EARLINESS_ROWS_V1.jsonl.gz")
OUT = os.path.join(HERE, "x2_EARLY_ENTRY_WALK_V1.jsonl.gz")

CLOSE_ENTRY = {
    "liquidity_sweep_reclaim", "displacement_continuation",
    "volatility_compression_expansion", "session_open_range_break",
    "regime_transition_break", "structural_distance_extreme",
    "cross_asset_lead_lag",
}


def main():
    pool = {(r["candidate_id"], r["decision_time_utc"]): r for r in w0_ws.load()}
    out = gzip.open(OUT, "wt")
    n = 0
    for line in gzip.open(ROWS, "rt"):
        e = json.loads(line)
        if e["status"] != "ok" or not e["reproduces_at_close"]:
            continue
        if e["origin_family"] not in CLOSE_ENTRY:
            continue
        m = e.get("first_true_minute")
        if m is None or e.get("price_edge_r") is None:
            continue
        p = pool[(e["candidate_id"], e["decision_time_utc"])]
        side = p["side"]
        d = p["risk_distance"]
        sl = p["stop_loss"]
        tp = p["take_profit_1"]
        entry_e = e["price_at_first_true"]
        T = datetime.fromisoformat(e["decision_time_utc"])
        seg = x2_bars.m1_slice(p["symbol"], T - timedelta(minutes=15) + timedelta(minutes=m), T)
        resolved = None
        res_bar = None
        for k, bar in enumerate(seg, start=1):
            hi, lo = bar[2], bar[3]
            if side == "LONG":
                hit_stop = lo <= sl
                hit_tp = hi >= tp
            else:
                hit_stop = hi >= sl
                hit_tp = lo <= tp
            if hit_stop:                      # conservative tie rule
                resolved, res_bar = "stop", k
                break
            if hit_tp:
                resolved, res_bar = "target", k
                break
        if resolved == "stop":
            r_early = ((sl - entry_e) if side == "LONG" else (entry_e - sl)) / d
        elif resolved == "target":
            r_early = ((tp - entry_e) if side == "LONG" else (entry_e - tp)) / d
        else:
            r_early = p["plain_walk_r"] + e["price_edge_r"]
        rec = {
            "candidate_id": e["candidate_id"],
            "decision_time_utc": e["decision_time_utc"],
            "symbol": p["symbol"],
            "origin_family": e["origin_family"],
            "side": side,
            "first_true_minute": m,
            "price_edge_r": e["price_edge_r"],
            "plain_walk_r": p["plain_walk_r"],
            "gross_r": p.get("gross_r"),
            "r_early": r_early,
            "delta_r": r_early - p["plain_walk_r"],
            "resolved_in_bar": resolved,
            "resolved_bar_offset": res_bar,
            "remaining_minutes_walked": len(seg),
            "is_first_emission": p.get("is_first_emission"),
            "cost_r": p.get("cost_r"),
        }
        out.write(json.dumps(rec) + "\n")
        n += 1
    out.close()
    print("wrote", OUT, n)


if __name__ == "__main__":
    main()
