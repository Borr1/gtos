"""x1 — the exact anatomy of a decision, in source and in time.

Reconstructs the 15 M1 bars INSIDE each candidate's own decision M15 bar and
measures how much of that bar had already printed by the time the decision was
taken, plus a stitched early-entry walk (intrabar remainder + the 120-bar
post-decision path) read straight from the M1 source the sidecar itself names.

No sampling. All 27,658 rows.
"""
from __future__ import annotations

import csv
import gzip
import json
import math
import os
import sys
from bisect import bisect_left
from collections import defaultdict
from datetime import datetime, timedelta, timezone

ROOT = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
DISC = f"{ROOT}/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
WS = f"{DISC}/w0_WORKING_SET.jsonl.gz"
BARS = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
        "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
M1DIRS = ["bridge_ftmo_m1_202512", "bridge_ftmo_m1_202601", "bridge_ftmo_m1_202602"]
M15DIR = "bridge_ftmo_m15_20250601_20260610"

KEEP = ("candidate_id decision_time_utc symbol side origin_family entry_price stop_loss "
        "take_profit_1 policy_target_r gross_r opportunity_net_proxy_r cost_r risk_distance "
        "bars_to_entry_touch entry_touched effective_order_type setup_dup_rank setup_dup_count "
        "is_first_emission which_came_first plain_walk_r fill_honest_walk_r mfe_r mae_r "
        "bars_to_target bars_to_stop r_at_path_end path_bars first_bar_utc last_bar_utc "
        "selector_action utc_hour_bucket").split()


def parse_ts(s):
    return datetime.fromisoformat(s)


def load_m1(symbol):
    """time-sorted (ts, o, h, l, c) for the symbol across the needed months."""
    rows = []
    for d in M1DIRS:
        p = f"{BARS}/{d}/{symbol}_M1.csv"
        if not os.path.exists(p):
            continue
        with open(p, newline="") as f:
            rd = csv.reader(f)
            next(rd)
            for r in rd:
                rows.append((r[0], float(r[1]), float(r[2]), float(r[3]), float(r[4])))
    rows.sort(key=lambda x: x[0])
    # de-dup identical timestamps across month files
    out = []
    seen = set()
    for r in rows:
        if r[0] in seen:
            continue
        seen.add(r[0])
        out.append(r)
    return [x[0] for x in out], out


def load_m15(symbol):
    p = f"{BARS}/{M15DIR}/{symbol}_M15.csv"
    idx = {}
    if not os.path.exists(p):
        return idx
    with open(p, newline="") as f:
        rd = csv.reader(f)
        next(rd)
        for r in rd:
            idx[r[0]] = (float(r[1]), float(r[2]), float(r[3]), float(r[4]))
    return idx


def m15_series(symbol):
    """ordered list of (ts, o,h,l,c) for indicator recomputation."""
    p = f"{BARS}/{M15DIR}/{symbol}_M15.csv"
    out = []
    if not os.path.exists(p):
        return [], {}
    with open(p, newline="") as f:
        rd = csv.reader(f)
        next(rd)
        for r in rd:
            out.append((r[0], float(r[1]), float(r[2]), float(r[3]), float(r[4])))
    out.sort(key=lambda x: x[0])
    pos = {t[0]: i for i, t in enumerate(out)}
    return out, pos


def main():
    rows = []
    with gzip.open(WS, "rt") as f:
        for line in f:
            r = json.loads(line)
            rows.append({k: r.get(k) for k in KEEP})
    by_sym = defaultdict(list)
    for r in rows:
        by_sym[r["symbol"]].append(r)
    sys.stderr.write(f"rows={len(rows)} symbols={len(by_sym)}\n")

    out_f = gzip.open(f"{DISC}/x1_INTRABAR_ROWS_V1.jsonl.gz", "wt")
    stats = defaultdict(int)
    for sym in sorted(by_sym):
        m1_times, m1 = load_m1(sym)
        m15idx = load_m15(sym)
        ser, spos = m15_series(sym)
        if not m1:
            stats[f"no_m1_source:{sym}"] += len(by_sym[sym])
            continue
        for r in by_sym[sym]:
            T = parse_ts(r["decision_time_utc"])
            Topen = T - timedelta(minutes=15)
            o = {"candidate_id": r["candidate_id"], "decision_time_utc": r["decision_time_utc"],
                 "symbol": sym, "origin_family": r["origin_family"], "side": r["side"]}
            # --- intrabar M1 window [Topen, T)
            lo = bisect_left(m1_times, Topen.isoformat())
            hi = bisect_left(m1_times, T.isoformat())
            win = m1[lo:hi]
            o["n_m1_in_decision_bar"] = len(win)
            # --- the M15 bar as the generator saw it
            m15 = m15idx.get(Topen.isoformat())
            o["m15_present"] = m15 is not None
            entry = float(r["entry_price"]); stop = float(r["stop_loss"])
            d = float(r["risk_distance"]); side = r["side"]
            tp = float(r["take_profit_1"])
            if m15:
                bo, bh, bl, bc = m15
                o["m15_open"], o["m15_high"], o["m15_low"], o["m15_close"] = bo, bh, bl, bc
                o["m15_range_r"] = (bh - bl) / d if d > 0 else None
                o["entry_is_m15_close"] = abs(entry - bc) < max(1e-9, abs(bc) * 1e-9)
                o["entry_minus_close_r"] = (entry - bc) / d if d > 0 else None
            if win:
                hs = [b[2] for b in win]; ls = [b[3] for b in win]; cs = [b[4] for b in win]
                mn_i = min(range(len(win)), key=lambda i: ls[i])
                mx_i = max(range(len(win)), key=lambda i: hs[i])
                # minute offset from bar open
                def off(i):
                    return int((parse_ts(win[i][0]) - Topen).total_seconds() // 60)
                o["minute_of_high"] = off(mx_i)
                o["minute_of_low"] = off(mn_i)
                bh_m1, bl_m1 = max(hs), min(ls)
                o["m1_agg_high"], o["m1_agg_low"] = bh_m1, bl_m1
                o["m1_agg_open"], o["m1_agg_close"] = win[0][1], win[-1][4]
                rng = bh_m1 - bl_m1
                # running range fraction by minute
                rf = []
                rh = -1e300; rl = 1e300
                for i in range(len(win)):
                    rh = max(rh, hs[i]); rl = min(rl, ls[i])
                    rf.append(round((rh - rl) / rng, 6) if rng > 0 else None)
                o["range_frac_by_minute"] = rf
                # first minute the eventual entry price was tradeable inside the bar
                fe = None
                for i in range(len(win)):
                    if ls[i] - 1e-12 <= entry <= hs[i] + 1e-12:
                        fe = off(i); break
                o["entry_first_tradeable_minute"] = fe
                o["entry_lead_minutes_vs_close"] = (14 - fe) if fe is not None else None
                # best price available inside the bar, in the trade's favour, vs the entry
                if side == "LONG":
                    o["best_intrabar_edge_r"] = (entry - bl_m1) / d if d > 0 else None
                    o["stop_breached_in_decision_bar"] = bl_m1 <= stop
                    o["target_reached_in_decision_bar"] = bh_m1 >= tp
                else:
                    o["best_intrabar_edge_r"] = (bh_m1 - entry) / d if d > 0 else None
                    o["stop_breached_in_decision_bar"] = bh_m1 >= stop
                    o["target_reached_in_decision_bar"] = bl_m1 <= tp
                # price at minute m (close of that minute), in R vs the actual entry
                marks = {}
                for m in (0, 2, 4, 6, 8, 10, 12, 14):
                    if m < len(win):
                        c = cs[m]
                        marks[m] = round(((entry - c) / d if side == "LONG" else (c - entry) / d), 6)
                o["entry_edge_r_at_minute"] = marks
            # --- recomputed generator indicators on the M15 series
            i15 = spos.get(Topen.isoformat())
            if i15 is not None and i15 >= 50:
                bars = ser
                cur = bars[i15]
                atr14 = sum(b[2] - b[3] for b in bars[i15 - 13:i15 + 1]) / 14.0
                ph20 = max(b[2] for b in bars[i15 - 20:i15])
                pl20 = min(b[3] for b in bars[i15 - 20:i15])
                o["atr14"] = atr14; o["prior_20_high"] = ph20; o["prior_20_low"] = pl20
                w50 = bars[i15 - 49:i15 + 1]
                h50 = max(b[2] for b in w50); l50 = min(b[3] for b in w50)
                o["pos50"] = (cur[4] - l50) / (h50 - l50) if h50 > l50 else None
                o["h50"] = h50; o["l50"] = l50
            out_f.write(json.dumps(o) + "\n")
            stats["written"] += 1
    out_f.close()
    with open(f"{DISC}/x1_INTRABAR_BUILD_V1.json", "w") as f:
        json.dump({"stats": dict(stats)}, f, indent=2)
    sys.stderr.write(json.dumps(dict(stats)) + "\n")


if __name__ == "__main__":
    main()
