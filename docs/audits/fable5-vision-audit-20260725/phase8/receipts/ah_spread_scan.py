"""Session AH -- the substrate for the era x hour composition repair.

Two scans, both outcome-independent (they touch broker quotes, never returns):

``tick-hours``
    Per FTMO symbol, the quoted-spread distribution per broker hour-of-day and per
    (weekday, hour) cell over the 37-day tick window. This is the *ground truth* the
    hour term in ``spread_model_v1`` was fitted on, re-derived here so the composition
    test can use the same numbers the model uses and can also see the tail.

``bar-semantics``
    What the MT5 bar ``spread`` column actually IS. ``spread_model_v1`` reads it as a
    level whose ratios track the era; nothing had asked which instant of the bar it
    describes. Answered by exact-match against tick truth at M15 in the reference
    window, over five candidate statistics (min / median / open / close / max).

Both write JSON caches beside this file so the composition driver never re-streams
1.03 GB of ticks.

Broker wall clock: the tick and bar ``time`` columns are broker wall clock already
(every file carries a ``.timebase.json`` saying so), so hour-of-day is
``(t // 3600) % 24`` and weekday is ``((t // 86400) + 3) % 7`` -- epoch day 0 was a
Thursday, which is asserted in ``test_ah_spread_v2.py`` rather than trusted.
"""

from __future__ import annotations

import argparse
import bisect
import collections
import gzip
import json
import os
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))

BARS = Path("/Users/borr/GTOSActive/vps-bars-20260727")
TICK_ROOT = Path("/Users/borr/GTOSActive/vps-ticks-20260726")
TICK_SUFFIX = "_ticks_20260618_to_20260726.csv.gz"

#: Both servers are `new_york_plus_7` (each tick file's `.timebase.json` says so and
#: `broker_clock.py` registers it), so an hour-of-day cell means the same wall hour on both
#: and the two accounts' profiles are directly comparable. That is the whole basis of the
#: cross-broker composition test in `ah_spread_compose.py` -- if the two clocks differed the
#: hour cells would be offset and the test would compare hour 00 with hour 04.
ACCOUNTS = {"FTMO": ("ftmo", "FTMO_"), "redacted_account": ("redacted_account", "redacted_account_")}

TICKS = TICK_ROOT / "ftmo"

# The reference window the spread model anchors on, in broker wall-clock epoch.
REF_LO = 1781740800   # 2026-06-18 00:00 broker
REF_HI = 1784937600   # 2026-07-25 00:00 broker

COSTS = REPO / "research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json"

PCTS = (5, 10, 25, 50, 75, 90, 95, 99)


def hour_of(t: int) -> int:
    return (t // 3600) % 24


def weekday_of(t: int) -> int:
    return ((t // 86400) + 3) % 7


def instruments(account: str = "FTMO") -> dict:
    doc = json.loads(COSTS.read_text())
    return doc["accounts"][account]["instruments"]


def spec_for(inst: dict, sym: str) -> dict | None:
    for k in (sym, sym.replace("_cash", ".cash"), sym.replace("_", "."),
              sym.replace(".cash", "_cash")):
        if k in inst:
            return inst[k]
    return None


def tick_symbols(account: str = "FTMO") -> list[tuple[str, Path]]:
    sub, prefix = ACCOUNTS[account]
    d = TICK_ROOT / sub
    out = []
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".csv.gz"):
            out.append((fn[len(prefix):-len(TICK_SUFFIX)], d / fn))
    return out


def pct(vals: list[float], p: float) -> float:
    """Nearest-rank percentile on a sorted list -- no interpolation, because a quoted
    spread is quantised to the point and an interpolated value is not a spread."""
    if not vals:
        return float("nan")
    i = min(len(vals) - 1, max(0, int(round((p / 100.0) * (len(vals) - 1)))))
    return vals[i]


# ---------------------------------------------------------------- tick-hours

def scan_tick_hours(out_path: Path, subsample: int = 1, account: str = "FTMO") -> dict:
    inst = instruments(account)
    result = {"schema": "gtos.ah.tick_hour_cells.v1", "account": account,
              "tick_archive": str(TICK_ROOT / ACCOUNTS[account][0]), "subsample": subsample,
              "reference_window_broker_epoch": [REF_LO, REF_HI], "symbols": {}}
    for sym, path in tick_symbols(account):
        t0 = time.time()
        sp_ = spec_for(inst, sym)
        by_hour: dict[int, list[float]] = collections.defaultdict(list)
        by_cell: dict[str, list[float]] = collections.defaultdict(list)
        prices: list[float] = []
        n = 0
        with gzip.open(path, "rt") as f:
            f.readline()
            for i, line in enumerate(f):
                if subsample > 1 and i % subsample:
                    continue
                # time,bid,ask,last,volume,time_msc,flags,volume_real
                p = line.split(",", 3)
                try:
                    t = int(p[0]); b = float(p[1]); a = float(p[2])
                except (ValueError, IndexError):
                    continue
                s = a - b
                if s <= 0:
                    continue
                n += 1
                h = hour_of(t)
                by_hour[h].append(s)
                by_cell[f"{weekday_of(t)}|{h}"].append(s)
                if not (n % 97):
                    prices.append(b)
        rec = {
            "n_ticks": n,
            "point": (sp_ or {}).get("spec", {}).get("point"),
            "instrument_class": (sp_ or {}).get("instrument_class"),
            "price_median": statistics.median(prices) if prices else None,
            "by_hour": {}, "by_cell": {},
        }
        for h, v in sorted(by_hour.items()):
            v.sort()
            rec["by_hour"][str(h)] = {"n": len(v), **{f"p{p}": pct(v, p) for p in PCTS}}
        for k, v in sorted(by_cell.items()):
            v.sort()
            rec["by_cell"][k] = {"n": len(v), "p50": pct(v, 50), "p90": pct(v, 90)}
        result["symbols"][sym] = rec
        print(f"  {sym:16s} n={n:9d}  {time.time()-t0:5.1f}s", flush=True)
    out_path.write_text(json.dumps(result))
    print(f"wrote {out_path} ({out_path.stat().st_size/1e6:.1f} MB)")
    return result


# ------------------------------------------------------------ bar-semantics

def bar_rows(sym: str, tf: str, lo: int | None = None, hi: int | None = None):
    p = BARS / f"FTMO_{sym}_{tf}.csv.gz"
    if not p.exists():
        return
    with gzip.open(p, "rt") as f:
        f.readline()
        for line in f:
            q = line.rstrip("\n").split(",")
            if len(q) < 7:
                continue
            t = int(q[0])
            if lo is not None and t < lo:
                continue
            if hi is not None and t >= hi:
                continue
            yield t, float(q[1]), float(q[2]), float(q[3]), float(q[4]), int(q[6])


def scan_bar_semantics(out_path: Path) -> dict:
    """Is bar.spread the min, the median, the open, the close, or the max?

    Exact integer match against tick truth at M15 inside the reference window. M15 is
    the finest bar the archive holds (2024+) and 900 s is short enough that the five
    candidates separate; at H4 they do not.
    """
    inst = instruments()
    res = {"schema": "gtos.ah.bar_spread_semantics.v1", "timeframe": "M15",
           "reference_window_broker_epoch": [REF_LO, REF_HI], "symbols": {}}
    for sym, path in tick_symbols():
        sp_ = spec_for(inst, sym)
        if not sp_:
            continue
        pt = sp_["spec"]["point"]
        bb = [(t, s) for t, *_rest, s in bar_rows(sym, "M15", REF_LO, REF_HI) if s > 0]
        if len(bb) < 200:
            continue
        ts: list[int] = []
        sps: list[float] = []
        with gzip.open(path, "rt") as f:
            f.readline()
            for line in f:
                p = line.split(",", 3)
                try:
                    t = int(p[0]); b = float(p[1]); a = float(p[2])
                except (ValueError, IndexError):
                    continue
                if a - b <= 0:
                    continue
                ts.append(t); sps.append(a - b)
        hit = collections.Counter()
        n = 0
        for t, s in bb:
            i = bisect.bisect_left(ts, t)
            j = bisect.bisect_left(ts, t + 900)
            if j - i < 5:
                continue
            seg = sps[i:j]
            n += 1
            for k, v in (("min", min(seg)), ("median", statistics.median(seg)),
                         ("open", seg[0]), ("close", seg[-1]), ("max", max(seg))):
                if round(v / pt) == s:
                    hit[k] += 1
        if n < 100:
            continue
        res["symbols"][sym] = {"n_bars": n,
                               "exact_match_rate": {k: hit[k] / n for k in
                                                    ("min", "median", "open", "close", "max")}}
        print(f"  {sym:16s} n={n:5d} " + "  ".join(
            f"{k}={hit[k]/n:.3f}" for k in ("min", "median", "open", "close", "max")), flush=True)
    rates = res["symbols"]
    if rates:
        res["median_exact_match_rate"] = {
            k: statistics.median([v["exact_match_rate"][k] for v in rates.values()])
            for k in ("min", "median", "open", "close", "max")}
        res["verdict"] = max(res["median_exact_match_rate"],
                             key=res["median_exact_match_rate"].get)
        print("MEDIAN: " + "  ".join(f"{k}={v:.3f}" for k, v in
                                     res["median_exact_match_rate"].items()))
        print("verdict:", res["verdict"])
    out_path.write_text(json.dumps(res, indent=1))
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("tick-hours", "bar-semantics"))
    ap.add_argument("--subsample", type=int, default=1)
    ap.add_argument("--account", default="FTMO", choices=tuple(ACCOUNTS))
    a = ap.parse_args()
    if a.cmd == "tick-hours":
        suffix = "" if a.account == "FTMO" else f"_{a.account.upper()}"
        scan_tick_hours(HERE / f"AH_TICK_HOUR_CELLS{suffix}.json", a.subsample, a.account)
    else:
        scan_bar_semantics(HERE / "AH_BAR_SPREAD_SEMANTICS.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
