"""r1-1b — the same quote-side question on the M1 packs the broad lanes walk.

The M15 archive (r1_quoteside_verify.py) and the M1 packs are DIFFERENT exports:
different directory, different clock stamping (the packs are true UTC, the M15
archive is broker wall clock), no overlapping window with the broker tick export.
So the M15 result transfers to them by provenance only, which is not a
measurement.  This closes it directly, against the true-UTC tick hold.

    bars  : .../LANE_INPUTS_TRUE_UTC_V1/sources/bars/bridge_ftmo_m1_<YYYYMM>/<SYM>_M1.csv
            `time` = ISO-8601 TRUE UTC
    ticks : .../LANE_INPUTS_TRUE_UTC_V1/sources/ticks/<YYYYMM>/<SYM>/microstructure_ticks.jsonl
            `time` / `ts_utc` = ISO-8601 TRUE UTC.  `time_msc` is a BROKER epoch
            and is deliberately NOT read here (p3 §4.1 measured the 2 h gap).

Whole population: every symbol, every month, every bar with >= 3 ticks in its own
minute.  Nothing sampled.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/"
            "evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources")
BARS = ROOT / "bars"
TICKS = ROOT / "ticks"
OUT = Path(__file__).resolve().parent / "R1_QUOTESIDE_M1_V1.json"


def iso_to_min(s: str) -> int:
    # "2026-01-01T22:05:00.405000+00:00" -> minute index since epoch
    y = int(s[0:4]); mo = int(s[5:7]); d = int(s[8:10])
    h = int(s[11:13]); mi = int(s[14:16])
    return int(datetime(y, mo, d, h, mi, tzinfo=timezone.utc).timestamp()) // 60


def load_ticks(month: str, sym: str):
    p = TICKS / month / sym / "microstructure_ticks.jsonl"
    if not p.is_file():
        return None
    per: dict[int, list] = defaultdict(list)
    with p.open("r") as fh:
        for line in fh:
            ia = line.find('"ask":')
            ib = line.find('"bid":')
            it = line.find('"time":"')
            if ia < 0 or ib < 0 or it < 0:
                continue
            a = float(line[ia + 6:line.find(",", ia)])
            b = float(line[ib + 6:line.find(",", ib)])
            if a <= 0 or b <= 0:
                continue
            ts = line[it + 8:it + 8 + 26]
            per[iso_to_min(ts)].append((b, a))
    return per


def measure(month: str, sym: str) -> dict | None:
    bp = BARS / f"bridge_ftmo_m1_{month}" / f"{sym}_M1.csv"
    if not bp.is_file():
        return None
    per = load_ticks(month, sym)
    if not per:
        return None
    n = 0
    eq_bid = eq_ask = 0
    hi_eq_maxbid = lo_eq_minbid = 0
    cm, hm, lm = [], [], []
    spreads = []
    n_bars_total = 0
    n_bars_with_tick = 0
    with bp.open("r") as fh:
        for row in csv.DictReader(fh):
            n_bars_total += 1
            m = iso_to_min(row["time"])
            tk = per.get(m)
            if not tk:
                continue
            n_bars_with_tick += 1
            if len(tk) < 3:
                continue
            c = float(row["close"]); h = float(row["high"]); lo = float(row["low"])
            bids = [x[0] for x in tk]
            asks = [x[1] for x in tk]
            lb, la = tk[-1]
            s = la - lb
            tol = max(abs(c) * 1e-9, 1e-10)
            n += 1
            eq_bid += abs(c - lb) <= tol
            eq_ask += abs(c - la) <= tol
            mxb, mnb = max(bids), min(bids)
            hi_eq_maxbid += abs(h - mxb) <= tol
            lo_eq_minbid += abs(lo - mnb) <= tol
            if s > 0:
                cm.append((c - (lb + la) / 2.0) / s)
                hm.append((h - mxb) / s)
                lm.append((lo - mnb) / s)
                spreads.append(s / c * 1e4)
    if not n:
        return None
    return {
        "month": month, "symbol": sym,
        "n_bars_in_pack": n_bars_total,
        "n_bars_with_any_tick": n_bars_with_tick,
        "tick_coverage": round(n_bars_with_tick / n_bars_total, 6),
        "n_bars_scored": n,
        "close_eq_last_bid": round(eq_bid / n, 6),
        "close_eq_last_ask": round(eq_ask / n, 6),
        "high_eq_max_bid": round(hi_eq_maxbid / n, 6),
        "low_eq_min_bid": round(lo_eq_minbid / n, 6),
        "close_minus_mid_over_spread_median": (
            round(float(np.median(cm)), 6) if cm else None),
        "high_minus_maxbid_over_spread_median": (
            round(float(np.median(hm)), 6) if hm else None),
        "low_minus_minbid_over_spread_median": (
            round(float(np.median(lm)), 6) if lm else None),
        "tick_spread_bps_median": round(float(np.median(spreads)), 5) if spreads else None,
    }


def main() -> int:
    months = sorted(p.name for p in TICKS.iterdir() if p.is_dir())
    rows = []
    for mo in months:
        for sym in sorted(p.name for p in (TICKS / mo).iterdir() if p.is_dir()):
            r = measure(mo, sym)
            if r:
                rows.append(r)
                print(json.dumps(r), flush=True)
    tot = sum(r["n_bars_scored"] for r in rows)
    agg = {
        "what": "quote side of the true-UTC M1 packs, against the true-UTC tick hold",
        "bars": str(BARS), "ticks": str(TICKS),
        "clock": "both true UTC; `time_msc` (a broker epoch) deliberately unread",
        "n_files": len(rows), "n_bars_scored": tot,
        "weighted_close_eq_last_bid": (
            sum(r["close_eq_last_bid"] * r["n_bars_scored"] for r in rows) / tot
            if tot else None),
        "min_close_eq_last_bid": min((r["close_eq_last_bid"] for r in rows), default=None),
        "close_minus_mid_over_spread_range": [
            min((r["close_minus_mid_over_spread_median"] for r in rows
                 if r["close_minus_mid_over_spread_median"] is not None), default=None),
            max((r["close_minus_mid_over_spread_median"] for r in rows
                 if r["close_minus_mid_over_spread_median"] is not None), default=None)],
        "per_file": rows,
    }
    OUT.write_text(json.dumps(agg, indent=1, sort_keys=True))
    print("WROTE", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
