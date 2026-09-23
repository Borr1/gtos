"""Settle the `time_stop_bars` unit from the RUNTIME, then convert it onto the research grids.

    python3 docs/audits/fable5-vision-audit-20260725/phase7/receipts/ad_timestop_units.py

WHY THIS RUNS FIRST
-------------------
`SESSION_AA_ESTATE_WALK_RESULT.md` §4 ends with an item assigned to "Nobody, yet":
`time_stop_bars` is recorded per sleeve in `AA_ESTATE_TRADES.json.gz` and deliberately NOT
applied, because its unit is ambiguous *in the table*. Every time-stop sweep in wave 7
depends on it, so it is resolved here before any sweep runs — and resolved from the code
path that closes live positions, not from the table.

THE ANSWER, WITH ITS CITATIONS
------------------------------
`time_stop_bars` is in **M15 bars, counted as bars that actually PRINTED** (trading bars),
for every sleeve. Three independent sites say so:

1. `src/components/execution.py:8953-8958` — `_trading_m15_bars_since` docstring, verbatim:
   *"Count actual CLOSED M15 bars that PRINTED since entry_dt -- TRADING bars (they exist
   only while the market is open), so this skips nights/weekends/holidays, matching the
   validated route's bar count instead of wall-clock. time_stop_bars is in M15 units for
   EVERY sleeve (the H4 sleeves' route maxbars 60/80 were pre-scaled x16 -> 960/1280 M15)."*
   The count itself is `self.mt5.get_candles(self.symbol, 15, want)` filtered to bars whose
   time is `> entry_dt`, dropping the forming bar (`:8961-8977`).

2. `src/components/execution.py:9010-9014` — the book's own time stop
   (`check_time_stop_and_close`, the path `execution.py:6940` names as the W7 book's exit
   owner) calls that counter and only falls back to wall clock when the feed cannot be read:
   `elapsed = self._trading_m15_bars_since(...)`, else
   `j46_j49_policy.bars_elapsed_since_fill(entry_dt)`.

3. `src/components/j46_j49_policy.py:50-64` — the fallback, whose docstring is
   *"M15 bars elapsed since fill, integer floor"* and whose body is
   `delta_seconds // (15 * 60)`. Wall clock, same unit.

So AA's two readings resolve as: `crypto`'s 1280 IS M15 units (= 80 H4 bars, the H4
structural horizon) and the `mx_*` family's 96 is ALSO M15 units — it is **not** 96 D1
bars. `FOURTH_REVIEW.md` §3.3's reading of 96 as D1 bars is wrong, and the direction of the
error matters: the live time stop on the fourteen `mx_*` D1 sleeves is far TIGHTER than
anyone reading the table assumed.

`book_owner.py:4139` is a notification card (`f"time stop {time_stop:g} bars"`) and indeed
never resolves the unit — AA was right about that line; it is just not the deciding line.

THE SECOND FINDING, WHICH IS WHY THIS SCRIPT MEASURES RATHER THAN DIVIDES
-------------------------------------------------------------------------
"96 printed M15 bars" is not a fixed amount of calendar time, and it is not a fixed number
of D1 bars either. It is a fixed number of bars the market printed — so it converts to a
DIFFERENT number of D1 bars per symbol, depending on how many M15 bars that symbol prints
per trading day. A 24/7 crypto symbol prints ~96 a day; an index CFD with a daily break
prints far fewer. `execution.py:9008` already knows this ("wall-clock over-counts -- index
CFDs ~3x") without writing the ratio down.

So the conversion factor is MEASURED here, per symbol, from the archive: group the M15 bar
stamps by the D1 (and H4) bar that contains them and take the median count. Published with
its dispersion, because a ratio quoted without one invites exactly the divide-by-96 that
this script exists to replace.

Offline and pure: reads the gzipped archive through `CsvBarSource` (which converts broker
wall clock to true UTC at load — the F7 seam), imports no broker module, writes one JSON.
"""

from __future__ import annotations

import collections
import datetime as dt
import glob
import json
import os
import statistics
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.bar_provider import TF_D1, TF_H4, TF_M15  # noqa: E402
from src.components.ultimate_book.execution_packets import (  # noqa: E402
    DEFAULT_EXIT_PROFILE,
    SLEEVE_EXIT_PROFILES,
)
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource  # noqa: E402

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
OUT = HERE / "AD_TIMESTOP_UNITS_V1.json"
AA = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"

TF_NAME = {TF_M15: "M15", TF_H4: "H4", TF_D1: "D1"}
TF_MINUTES = {TF_M15: 15, TF_H4: 240, TF_D1: 1440}

RESOLUTION = {
    "unit": "M15 bars, counted as bars that PRINTED (trading bars), for every sleeve",
    "authority": [
        {
            "file_line": "src/components/execution.py:8953-8958",
            "symbol": "ExecutionEngine._trading_m15_bars_since",
            "quote": (
                "Count actual CLOSED M15 bars that PRINTED since entry_dt -- TRADING bars "
                "(they exist only while the market is open), so this skips "
                "nights/weekends/holidays, matching the validated route's bar count instead "
                "of wall-clock. time_stop_bars is in M15 units for EVERY sleeve (the H4 "
                "sleeves' route maxbars 60/80 were pre-scaled x16 -> 960/1280 M15)."
            ),
        },
        {
            "file_line": "src/components/execution.py:9010-9014",
            "symbol": "ExecutionEngine.check_time_stop_and_close",
            "quote": (
                "elapsed = self._trading_m15_bars_since(entry_dt, int(time_stop)); "
                "elapsed_basis = 'trading' if elapsed is not None else 'wallclock'; "
                "if elapsed is None: elapsed = "
                "j46_j49_policy.bars_elapsed_since_fill(entry_dt)"
            ),
        },
        {
            "file_line": "src/components/j46_j49_policy.py:50-64",
            "symbol": "bars_elapsed_since_fill",
            "quote": "M15 bars elapsed since fill, integer floor -- delta_seconds // (15 * 60)",
        },
        {
            "file_line": "src/components/execution.py:6938-6942",
            "symbol": "ExecutionEngine._manage_open_position",
            "quote": (
                "W7 ultimate_book trades own their exit at the broker (SL=-1R / "
                "TP=final_target_r) plus the per-trade time-stop "
                "(check_time_stop_and_close, driven by book_owner)"
            ),
            "why_it_matters": (
                "identifies check_time_stop_and_close as the book's time-stop owner, so the "
                "PRINTED-bar counter is the live rule for W7 sleeves. exit_policy_v4's own "
                "time stop (exit_policy_v4.py:585) is wall-clock M15 "
                "(execution.py:7248, `// (15 * 60)`) but execution.py:6945 gates the whole "
                "exit_policy_v4 branch off for book-native trades, so it is NOT the W7 rule."
            ),
        },
    ],
    "aa_ambiguity_resolved": {
        "aa_said": (
            "crypto's 1280 reads as M15 units against a 320 h H4 horizon; the fourteen mx_* "
            "sleeves' 96 reads as D1 bars against a ~3-bar median hold; book_owner.py:4139 "
            "never resolves it"
        ),
        "answer": (
            "BOTH are M15 units. book_owner.py:4139 is a Telegram card "
            "(f'time stop {time_stop:g} bars') and never resolves anything -- AA was right "
            "about the line and it is not the deciding line."
        ),
        "consequence": (
            "FOURTH_REVIEW.md §3.3's reading of 96 as 96 D1 bars is wrong, and the error's "
            "direction matters: the live time stop on the fourteen mx_* D1 sleeves is far "
            "TIGHTER than the table suggests, not looser."
        ),
    },
    "second_finding": (
        "PRINTED bars, not wall clock -- so 96 M15 bars is a different amount of calendar "
        "time and a different number of D1 bars on every symbol. execution.py:9008 knows "
        "this ('wall-clock over-counts -- index CFDs ~3x') without writing the ratio down. "
        "Measured per symbol below."
    ),
}


def load_series() -> dict:
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    files: dict[tuple[str, int], str] = {}
    for p in glob.glob(f"{BARS}/FTMO_*.csv.gz"):
        stem = os.path.basename(p)[len("FTMO_"):-len(".csv.gz")]
        sym, _, tfs = stem.rpartition("_")
        tf = {v: k for k, v in TF_NAME.items()}.get(tfs)
        if tf is None:
            continue
        files[(res(sym), tf)] = p
    src = CsvBarSource(files, label="vps-bars-20260727-FTMO")
    times: dict[tuple[str, int], list[dt.datetime]] = {}
    for key in files:
        rows = src._load(key)
        if not rows:
            continue
        times[key] = [dt.datetime.fromisoformat(r["time"]) for r in rows]
    return times


def m15_per_bar(m15: list[dt.datetime], coarse: list[dt.datetime], span_min: int) -> dict:
    """Median / IQR count of M15 bars whose stamp falls inside each coarse bar.

    Measured only over the coarse bars fully inside the M15 series' own span, because a
    partially covered bar reads as a low count and would drag the median down for a reason
    that is about archive coverage rather than about the market's session.
    """
    if not m15 or not coarse:
        return {"available": False, "reason": "one of the two series is empty"}
    lo, hi = m15[0], m15[-1]
    width = dt.timedelta(minutes=span_min)
    idx = 0
    counts: list[int] = []
    for t in coarse:
        if t < lo or t + width > hi:
            continue
        while idx < len(m15) and m15[idx] < t:
            idx += 1
        j, n = idx, 0
        while j < len(m15) and m15[j] < t + width:
            n += 1
            j += 1
        counts.append(n)
    if not counts:
        return {"available": False, "reason": "no coarse bar fully covered by the M15 span"}
    counts.sort()
    q = lambda f: counts[min(len(counts) - 1, int(f * len(counts)))]  # noqa: E731
    return {
        "available": True,
        "n_coarse_bars": len(counts),
        "median": q(0.5),
        "mean": round(statistics.fmean(counts), 2),
        "p10": q(0.10),
        "p90": q(0.90),
        "max": counts[-1],
        "frac_zero": round(sum(1 for c in counts if c == 0) / len(counts), 4),
        "span": [lo.isoformat(), hi.isoformat()],
    }


def main() -> dict:
    times = load_series()
    print(f"loaded {len(times)} (symbol, timeframe) stamp series")

    ratios: dict[str, dict] = {}
    for (sym, tf), ts in sorted(times.items()):
        m15 = times.get((sym, TF_M15))
        if not m15:
            continue
        if tf == TF_M15:
            # An M15 bar contains exactly one M15 bar. Stated rather than measured, and
            # stated because leaving it out is what made the first run of this script print
            # "-" for all ten M15 sleeves -- whose time stops (fx_jpy_ny's 48 = 12 h against
            # MAXBARS 80 = 20 h) are precisely the ones that BIND.
            ratios.setdefault(sym, {})["M15"] = {
                "available": True, "n_coarse_bars": len(ts), "median": 1, "mean": 1.0,
                "p10": 1, "p90": 1, "max": 1, "frac_zero": 0.0,
                "span": [m15[0].isoformat(), m15[-1].isoformat()],
                "basis": "identity, not measured: one M15 bar per M15 bar",
            }
            continue
        r = m15_per_bar(m15, ts, TF_MINUTES[tf])
        ratios.setdefault(sym, {})[TF_NAME[tf]] = r

    print(f"\n{'symbol':16s} {'M15/D1':>18s} {'M15/H4':>18s}")
    for sym in sorted(ratios):
        d = ratios[sym].get("D1") or {}
        h = ratios[sym].get("H4") or {}
        f = lambda r: ("        -" if not r.get("available")  # noqa: E731
                       else f"{r['median']:4d} [{r['p10']}-{r['p90']}]")
        print(f"{sym:16s} {f(d):>18s} {f(h):>18s}")

    # ---- what each sleeve's contract MEANS on its own grid ------------------------------
    import gzip

    aa = json.load(gzip.open(AA, "rt"))
    tf_of = {s: {"M15": TF_M15, "H4": TF_H4, "D1": TF_D1}[v]
             for s, v in aa["timeframe_by_sleeve"].items()}
    holds: dict[str, list[float]] = {}
    stops: dict[str, list[int]] = {}
    syms: dict[str, collections.Counter] = {}
    for sleeve, rows in aa["trades"].items():
        for r in rows:
            holds.setdefault(sleeve, []).append(float(r["hold_hours"]))
            stops.setdefault(sleeve, []).append(int(r["exit_bar_offset"]))
            syms.setdefault(sleeve, collections.Counter())[r["symbol"]] += 1

    contracts: dict[str, dict] = {}
    for sleeve in sorted(tf_of):
        prof = SLEEVE_EXIT_PROFILES.get(sleeve, DEFAULT_EXIT_PROFILE)
        tsb = prof.get("time_stop_bars")
        tf = tf_of[sleeve]
        tfn = TF_NAME[tf]
        # the sleeve's own symbols, weighted by how often they traded
        per_sym: dict[str, dict] = {}
        for sym, n in (syms.get(sleeve) or {}).items():
            r = (ratios.get(sym) or {}).get(tfn) or {}
            if not r.get("available"):
                per_sym[sym] = {"n_trades": n, "m15_per_bar": None,
                                "time_stop_in_own_bars": None}
                continue
            k = r["median"]
            per_sym[sym] = {
                "n_trades": n,
                "m15_per_bar_median": k,
                "m15_per_bar_p10_p90": [r["p10"], r["p90"]],
                "time_stop_in_own_bars": (round(tsb / k, 3) if tsb and k else None),
                "time_stop_trading_hours": (round(tsb / k * TF_MINUTES[tf] / 60.0, 2)
                                            if tsb and k else None),
            }
        ks = [v["m15_per_bar_median"] for v in per_sym.values()
              if v.get("m15_per_bar_median")]
        ns = [v["n_trades"] for v in per_sym.values() if v.get("m15_per_bar_median")]
        k_w = (sum(k * n for k, n in zip(ks, ns)) / sum(ns)) if ks and sum(ns) else None
        hold = sorted(holds.get(sleeve) or [])
        off = sorted(stops.get(sleeve) or [])
        ts_own = (tsb / k_w) if (tsb and k_w) else None
        contracts[sleeve] = {
            "timeframe": tfn,
            "policy": prof.get("policy"),
            "time_stop_bars_m15": tsb,
            "m15_per_own_bar_trade_weighted": (round(k_w, 3) if k_w else None),
            "time_stop_in_own_bars": (round(ts_own, 3) if ts_own else None),
            "time_stop_trading_hours": (round(ts_own * TF_MINUTES[tf] / 60.0, 2)
                                        if ts_own else None),
            "maxbars_research": aa["maxbars"],
            "time_stop_binds_before_maxbars": (
                None if ts_own is None else bool(ts_own < aa["maxbars"])),
            "realised_median_hold_hours": (
                round(hold[len(hold) // 2], 3) if hold else None),
            "realised_p90_hold_hours": (
                round(hold[int(0.90 * len(hold))], 3) if hold else None),
            "realised_median_exit_bar_offset": (off[len(off) // 2] if off else None),
            "n_trades": len(hold),
            "frac_trades_the_time_stop_would_truncate": (
                None if ts_own is None or not off
                else round(sum(1 for o in off if o > ts_own) / len(off), 4)),
            "by_symbol": per_sym,
        }

    print(f"\n{'sleeve':42s} {'tf':4s} {'tsb':>5s} {'M15/bar':>8s} {'=own bars':>10s} "
          f"{'=hours':>8s} {'med hold':>9s} {'trunc%':>7s}")
    for s, c in sorted(contracts.items()):
        g = lambda k, p=2: ("       -" if c[k] is None else f"{c[k]:.{p}f}")  # noqa: E731
        tr = ("     -" if c["frac_trades_the_time_stop_would_truncate"] is None
              else f"{100*c['frac_trades_the_time_stop_would_truncate']:.1f}")
        print(f"{s:42s} {c['timeframe']:4s} {str(c['time_stop_bars_m15']):>5s} "
              f"{g('m15_per_own_bar_trade_weighted'):>8s} {g('time_stop_in_own_bars'):>10s} "
              f"{g('time_stop_trading_hours'):>8s} "
              f"{g('realised_median_hold_hours'):>9s} {tr:>7s}")

    out = {
        "schema": "gtos.walkforward.timestop_units.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "session": "AD",
        "block": "B750",
        "resolution": RESOLUTION,
        "measurement": {
            "what": ("printed M15 bars per coarse bar, per FTMO symbol, from "
                     "vps-bars-20260727 through CsvBarSource (broker wall clock -> true "
                     "UTC at load)"),
            "method": ("count M15 stamps in [t, t + span) for every coarse bar fully "
                       "inside the M15 series' own span; median and p10/p90 published"),
            "caveat": ("the M15 archive starts 2023-12-31 and the D1 archive starts as "
                       "early as 2000, so this ratio is measured on 2024-2026 and applied "
                       "to the whole panel. Session hours change over decades; the ratio "
                       "is a current-session measurement, not a historical one."),
            "m15_per_coarse_bar": ratios,
        },
        "sleeve_contracts": contracts,
        "how_to_use": (
            "Multiply nothing. To apply a sleeve's live time stop on its own research grid, "
            "use `time_stop_in_own_bars` = time_stop_bars_m15 / m15_per_own_bar; for a "
            "per-symbol sweep use `by_symbol[sym].time_stop_in_own_bars`. Rounding is the "
            "caller's: ExitPolicy.time_stop_bars is an integer >= 1."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return out


if __name__ == "__main__":
    main()
