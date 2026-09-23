"""Session AH item 1 -- the H4 re-entry test, end to end.

    python3 .../ah_entry_shift.py generate     # four arms over the FX cohort
    python3 .../ah_entry_shift.py gate         # verdicts per arm, per member and per family

WHAT IS BEING TESTED
--------------------
Every `mx_*` D1 sleeve decides at the D1 close and enters there. On the FTMO server a D1
bar closes at broker 00:00, which is the daily rollover and the measured 13x-38x hour of the
week (AG §5) -- so **the whole FX D1 cohort fills at the worst hour of the week by
construction**, not by choice. AF re-priced the same trades two hours later and removed
80-81 % of modelled cost, then refused to call that the gain, because the cost model itself
had the composition defect this session repaired.

The archive holds H4 bars for every FX symbol, so the entry can be MOVED rather than
re-priced: enter at the first H4 close after the D1 decision (broker 04:00), which changes
the fill PRICE and therefore the R geometry, the path, the hold and the carry -- not just the
spread charge.

FOUR ARMS, AND WHY THE MIDDLE ONE EXISTS
-----------------------------------------
====================  ===================================  =====================
arm                   entry                                exit replayed on
====================  ===================================  =====================
`A_d1close_d1exit`    D1 close (broker 00:00)              D1 bars, maxbars 80
`B_d1close_h4exit`    D1 close (the same instant)          H4 bars, maxbars 480
`C_h4next_h4exit`     first H4 close after (broker 04:00)  H4 bars, maxbars 480
`D_h4second_h4exit`   second H4 close after (broker 08:00) H4 bars, maxbars 480
====================  ===================================  =====================

A is AF's population exactly, and it is checked against `AF_FAMILY_TRADES.json.gz` trade by
trade so the whole comparison is known to be about the same program. **B is the control**:
480 H4 bars span the same 80 trading days as 80 D1 bars, but a finer bar sees a stop the
coarser one steps over, so B minus A is the resolution artifact and C minus B is the entry
shift. Reporting C against A would confound the two, and the artifact is not small.

D is a sensitivity, not a candidate: it exists so the reader can see whether the effect is a
cliff at the rollover or a slope through the morning.

WHAT MAKES THIS THE SAME RULE
------------------------------
Generation is untouched -- the same production generator, the same 260-bar D1 window, the
same `decision_day`, the same ATR-derived `stop_dist` and `target_dist` in PRICE. Only the
fill instant moves, and the stop and target ride with it, which is what a live "enter at the
next H4 close" implementation would do. No arm skips a trade on an outcome; the only drops
are structural (no H4 bar within `MAX_SHIFT_HOURS`) and they are counted.
"""

from __future__ import annotations

import argparse
import bisect
import collections
import datetime as dt
import glob
import gzip
import hashlib
import json
import os
import statistics
import sys
import time
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.bar_provider import TF_D1, TF_H4, WARMUP  # noqa: E402
from src.components.ultimate_book.bar_provider import decision_day_of  # noqa: E402
from src.components.ultimate_book.primitives import Bar  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs.model import load_broker_true_costs  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
    measured_n_trials,
)
from src.research_infra.walkforward import TradeRecord, run_gate  # noqa: E402
from src.research_infra.walkforward import family as fam  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.utils.broker_clock import resolve_rule, utc_to_broker_naive  # noqa: E402

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
AF_TRADES = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts/AF_FAMILY_TRADES.json.gz"
OUT_TRADES = HERE / "AH_ENTRY_SHIFT_TRADES.json.gz"
OUT = HERE / "ENTRY_HOUR_FRONTIER_V1.json"
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
SERVER = "FTMO-Server3"
RULE = resolve_rule(SERVER)

MAXBARS_D1 = 80
#: 480 H4 bars is the same 80 trading days as 80 D1 bars: six H4 closes per trading day, and
#: both series skip the same weekends. Using 80 on both would compare an 80-day horizon
#: against a 13-day one and read the difference as the entry shift.
MAXBARS_H4 = 480
TF_MINUTES = {TF_H4: 240, TF_D1: 1440}

#: Only the classes that PAY at the rollover. Measured from the model's own table rather than
#: assumed: `fx` 16.7x and `jpy_fx` 12.6x at broker hour 00, while `index`, `energy` and
#: `metals` have NO hour-00 cell at all (they do not quote at the rollover, AG §5) and
#: `crypto` is exactly 1.00. AF measured the same thing from the other end -- ~0.000 R of
#: hour saving on every non-FX class -- so this restriction is a measurement, not a scope cut.
COHORT_CLASSES = ("fx",)

#: A shifted entry more than this far after the decision is a different trade, not a later
#: fill. Fridays are the reason: the D1 bar closing Saturday 00:00 has its next H4 close on
#: Monday 04:00. Those bars are also `engine_reachable == False` (AF §1.1: every Friday is a
#: pre-gap bar), so almost nothing is lost, but the drop is counted rather than assumed away.
MAX_SHIFT_HOURS = 8.0

ARMS = ("A_d1close_d1exit", "B_d1close_h4exit", "C_h4next_h4exit", "D_h4second_h4exit")


def load_archive(symbols: set[str]) -> dict:
    files: dict[tuple[str, int], str] = {}
    for p in sorted(glob.glob(f"{BARS}/FTMO_*.csv.gz")):
        stem = os.path.basename(p)[len("FTMO_"):-len(".csv.gz")]
        sym, _, tfs = stem.rpartition("_")
        tf = {"D1": TF_D1, "H4": TF_H4}.get(tfs)
        if tf is None or sym not in symbols:
            continue
        files[(sym, tf)] = p
    src = CsvBarSource(files, label="vps-bars-20260727-FTMO")
    series = {}
    for key in files:
        rows = src._load(key)
        if not rows:
            continue
        series[key] = (
            [Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0))
             for r in rows],
            [dt.datetime.fromisoformat(r["time"]) for r in rows],
        )
    return series


def engine_reachable(times, grid, ivl, warm) -> set[int]:
    """AF's rule, verbatim in behaviour -- see `af_family_generate.engine_reachable`."""
    out: set[int] = set()
    two = 2 * ivl
    for now in grid:
        j = bisect.bisect_right(times, now) - 1
        if j < 1:
            continue
        d = j - 1
        if d < warm - 1:
            continue
        close = times[d] + ivl
        if close > now or (now - close) > two:
            continue
        out.add(d)
    return out


def warm_cluster_for(parent_sleeve: str) -> str:
    from src.components.ultimate_book.sleeves.registry import (
        BUILT,
        CANDIDATE_BUILT,
        MARKET_EXPANSION_BUILT,
    )
    for table in (BUILT, CANDIDATE_BUILT, MARKET_EXPANSION_BUILT):
        spec = table.get(parent_sleeve)
        if spec is not None:
            return spec.cluster
    raise KeyError(parent_sleeve)


def generate_member(m, gen, series, warm_cluster: str, reach: set[int]) -> list[dict]:
    """One member, four arms per intent."""
    d1 = series.get((m.symbol, TF_D1))
    h4 = series.get((m.symbol, TF_H4))
    if d1 is None or h4 is None:
        return []
    dbars, dtimes = d1
    hbars, htimes = h4
    # H4 CLOSE instants -> index, so the D1 close can be located exactly rather than
    # searched for approximately.
    h4_close = [t + dt.timedelta(minutes=240) for t in htimes]
    ivl = dt.timedelta(minutes=1440)
    warm = WARMUP.get(warm_cluster, 200)
    out: list[dict] = []
    for i in range(warm - 1, len(dbars) - 2):
        lo = max(0, i - 259)
        w = dbars[lo:i + 1]
        close_at = dtimes[i] + ivl
        intent = gen(m.symbol, w, decision_day_of(dtimes[i]), bar_time=dtimes[i],
                     bar_times=dtimes[lo:i + 1], aux_bars=None, aux_times=None,
                     runtime_now=close_at)
        if intent is None:
            continue
        d = int(intent.direction)
        sd = float(intent.stop_dist)
        td = intent.target_dist
        if d not in (1, -1) or not (sd > 0):
            continue
        td = float(td) if td else None
        reachable = i in reach
        wall = utc_to_broker_naive(close_at, RULE)
        common = {"member": m.member, "symbol": m.broker_symbol,
                  "symbol_canonical": m.symbol, "direction": d,
                  "sl_distance_price": sd, "target_dist": td,
                  "decision_bar_iso": dtimes[i].isoformat(),
                  "decision_day": intent.decision_day,
                  "decision_close_utc": close_at.isoformat(),
                  "decision_broker_hour": wall.hour,
                  "engine_reachable": reachable}

        # --- A: AF's arm, D1 exit resolution -------------------------------------
        pr = replay(dbars, i, d, stop_dist=sd,
                    policy=ExitPolicy(target_dist=td, maxbars=MAXBARS_D1, label="plain"))
        out.append({**common, "arm": "A_d1close_d1exit",
                    "entry_utc": close_at.isoformat(),
                    "entry_price": float(dbars[i].c),
                    "exit_utc": (dtimes[pr.exit_index] + ivl).isoformat(),
                    "r_gross": float(winsorize_R(pr.r_gross)),
                    "exit_reason": pr.exit_reason, "mfe_r": round(pr.mfe_r, 6),
                    "mae_r": round(pr.mae_r, 6), "exit_bar_offset": int(pr.exit_index - i),
                    "hold_hours": round((pr.exit_index - i) * 24.0, 4),
                    "entry_shift_hours": 0.0})

        # --- B/C/D: H4 exit resolution, entry at 0 / 1 / 2 H4 closes later --------
        j0 = bisect.bisect_left(h4_close, close_at)
        if j0 >= len(h4_close) or h4_close[j0] != close_at:
            # The D1 close has no coincident H4 close (a broker holiday truncating the
            # session). Recorded, not silently skipped -- see `arm_drops` in the artifact.
            out.append({**common, "arm": "B_d1close_h4exit", "dropped":
                        "no H4 close coincides with the D1 close"})
            continue
        for arm, step in (("B_d1close_h4exit", 0), ("C_h4next_h4exit", 1),
                          ("D_h4second_h4exit", 2)):
            j = j0 + step
            if j >= len(hbars) - 1:
                out.append({**common, "arm": arm, "dropped": "shifted entry past the archive"})
                continue
            shift = (h4_close[j] - close_at).total_seconds() / 3600.0
            if shift > MAX_SHIFT_HOURS:
                out.append({**common, "arm": arm, "dropped":
                            f"next H4 close is {shift:.1f} h after the decision "
                            f"(> {MAX_SHIFT_HOURS} h): a session gap, not a later fill"})
                continue
            prh = replay(hbars, j, d, stop_dist=sd,
                         policy=ExitPolicy(target_dist=td, maxbars=MAXBARS_H4,
                                           label="plain"))
            out.append({**common, "arm": arm,
                        "entry_utc": h4_close[j].isoformat(),
                        "entry_price": float(hbars[j].c),
                        "entry_broker_hour": utc_to_broker_naive(h4_close[j], RULE).hour,
                        "exit_utc": h4_close[prh.exit_index].isoformat(),
                        "r_gross": float(winsorize_R(prh.r_gross)),
                        "exit_reason": prh.exit_reason, "mfe_r": round(prh.mfe_r, 6),
                        "mae_r": round(prh.mae_r, 6),
                        "exit_bar_offset": int(prh.exit_index - j),
                        "hold_hours": round((prh.exit_index - j) * 4.0, 4),
                        "entry_shift_hours": round(shift, 4),
                        "entry_slip_price": float(hbars[j].c - dbars[i].c)})
    return out


def parity_vs_af(rows: list[dict]) -> dict:
    """Arm A must BE AF's population. Checked per member on count and on summed R."""
    with gzip.open(AF_TRADES, "rt") as fh:
        af = json.load(fh)
    mine = collections.defaultdict(list)
    for r in rows:
        if r["arm"] == "A_d1close_d1exit" and not r.get("dropped"):
            mine[r["member"]].append(r)
    out = {"members_compared": 0, "exact_count": 0, "exact_sum_r": 0, "detail": {}}
    for member, rs in sorted(mine.items()):
        theirs = af["trades"].get(member)
        if theirs is None:
            continue
        out["members_compared"] += 1
        a = len(rs)
        b = len(theirs)
        sa = round(sum(r["r_gross"] for r in rs), 6)
        sb = round(sum(t["r_gross"] for t in theirs), 6)
        out["exact_count"] += int(a == b)
        out["exact_sum_r"] += int(sa == sb)
        out["detail"][member] = {"n_mine": a, "n_af": b, "sum_r_mine": sa, "sum_r_af": sb}
    return out


def to_records(rows: list[dict], sleeve: str | None = None) -> list[TradeRecord]:
    return [
        TradeRecord(
            sleeve=(sleeve or r["member"]), symbol=r["symbol"],
            entry_utc=dt.datetime.fromisoformat(r["entry_utc"]),
            exit_utc=dt.datetime.fromisoformat(r["exit_utc"]),
            direction=r["direction"], sl_distance_price=r["sl_distance_price"],
            entry_price=r["entry_price"], r_gross=r["r_gross"],
            features={"mfe_r": r["mfe_r"], "mae_r": r["mae_r"],
                      "hold_hours": r["hold_hours"], "exit_reason": r["exit_reason"],
                      "entry_shift_hours": r["entry_shift_hours"]})
        for r in rows if r["engine_reachable"] and not r.get("dropped")
    ]


#: Duplicate exports of one broker instrument -- AF §1.3, kept identical here so arm A can be
#: compared member for member.
DUPLICATE_ALIASES = {"GER40_cash": "GER40", "JP225_cash": "JP225"}


def archive_symbols() -> list[str]:
    syms = set()
    for p in glob.glob(f"{BARS}/FTMO_*_D1.csv.gz"):
        stem = os.path.basename(p)[len("FTMO_"):-len(".csv.gz")]
        sym, _, _tf = stem.rpartition("_")
        if sym not in DUPLICATE_ALIASES:
            syms.add(sym)
    return sorted(syms)


def cohort_members(res, supports):
    grid = fam.FamilyGrid()
    syms = archive_symbols()
    for key, tfs in (("donchian_20_breakout", (TF_D1,)),
                     ("volume_surge_reversal", (TF_D1,)),
                     ("atr_mean_reversion", (TF_D1,))):
        g = fam.family_members([key], tfs, symbols=syms, broker_symbol=res,
                               classes=COHORT_CLASSES,
                               profile_supports=(supports if callable(supports) else None))
        grid.members.extend(g.members)
        grid.dropped.extend(g.dropped)
    return grid


def do_generate() -> dict:
    t0 = time.time()
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    supports = getattr(res, "supports", None)
    grid = cohort_members(res, supports)
    symbols = sorted({m.symbol for m in grid.members})
    print(f"cohort: {len(grid.members)} members over {len(symbols)} FX symbols "
          f"({len(grid.families())} families)")
    series = load_archive(set(symbols))
    print(f"archive: {len(series)} (symbol, timeframe) series")
    grid.members = [m for m in grid.members
                    if (m.symbol, TF_D1) in series and (m.symbol, TF_H4) in series]

    warm = {k: warm_cluster_for(s.parent_sleeve) for k, s in fam.MECHANISMS.items()}
    # The D1 union close grid, over the SAME symbol set AF used, because reachability depends
    # on which other symbols share the launcher (AF §1.2) -- restricting the grid to FX would
    # change which bars are reachable and break arm A's parity. Loaded through the same
    # `CsvBarSource` seam so the broker->UTC conversion is byte-identical to AF's; reading the
    # raw epochs here and calling them UTC is finding F7 and it would shift the whole grid.
    d1grid = [t + dt.timedelta(minutes=1440) for t in _all_d1_times()]
    print(f"D1 union grid: {len(d1grid)} closes {d1grid[0].date()}..{d1grid[-1].date()}")

    reach_cache: dict[tuple[str, int], set[int]] = {}
    rows: list[dict] = []
    with fam.expanded_surface(grid.members) as gens:
        for k, m in enumerate(grid.members):
            nwarm = WARMUP.get(warm[m.mechanism_key], 200)
            rk = (m.symbol, nwarm)
            if rk not in reach_cache:
                reach_cache[rk] = engine_reachable(
                    series[(m.symbol, TF_D1)][1], d1grid, dt.timedelta(minutes=1440), nwarm)
            rows.extend(generate_member(m, gens[m.member], series, warm[m.mechanism_key],
                                        reach_cache[rk]))
            if (k + 1) % 10 == 0:
                print(f"  {k+1}/{len(grid.members)}  {time.time()-t0:.0f}s  rows={len(rows)}",
                      flush=True)

    par = parity_vs_af(rows)
    print(f"parity vs AF: {par['exact_count']}/{par['members_compared']} exact on count, "
          f"{par['exact_sum_r']}/{par['members_compared']} exact on summed R")
    drops = collections.Counter((r["arm"], r["dropped"].split(":")[0].split("(")[0].strip())
                                for r in rows if r.get("dropped"))
    art = {
        "schema": "gtos.ah.entry_shift_trades.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "bars_archive": BARS, "arms": list(ARMS),
        "maxbars": {"D1": MAXBARS_D1, "H4": MAXBARS_H4},
        "cohort_classes": list(COHORT_CLASSES),
        "max_shift_hours": MAX_SHIFT_HOURS,
        "members": sorted({r["member"] for r in rows}),
        "n_rows": len(rows),
        "n_by_arm": dict(collections.Counter(r["arm"] for r in rows if not r.get("dropped"))),
        "arm_drops": {f"{a} | {why}": n for (a, why), n in sorted(drops.items())},
        "parity_vs_af": par,
        "decision_broker_hour_histogram": dict(collections.Counter(
            r["decision_broker_hour"] for r in rows if r["arm"] == "A_d1close_d1exit")),
        "entry_broker_hour_histogram": {
            arm: dict(collections.Counter(r["entry_broker_hour"] for r in rows
                                          if r["arm"] == arm and not r.get("dropped")))
            for arm in ARMS[1:]},
        "seconds": round(time.time() - t0, 1),
        "trades": rows,
    }
    with gzip.open(OUT_TRADES, "wt") as fh:
        json.dump(art, fh)
    print(f"wrote {OUT_TRADES.relative_to(REPO)} ({OUT_TRADES.stat().st_size/1e6:.1f} MB) "
          f"in {art['seconds']}s")
    return art


def _all_d1_times() -> list[dt.datetime]:
    """Every D1 bar time in the archive, in true UTC, through the same conversion seam."""
    files = {}
    for p in sorted(glob.glob(f"{BARS}/FTMO_*_D1.csv.gz")):
        stem = os.path.basename(p)[len("FTMO_"):-len(".csv.gz")]
        sym, _, _tf = stem.rpartition("_")
        files[(sym, TF_D1)] = p
    src = CsvBarSource(files, label="vps-bars-20260727-FTMO-d1grid")
    stamps = set()
    for key in files:
        for r in src._load(key):
            stamps.add(dt.datetime.fromisoformat(r["time"]))
    return sorted(stamps)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("generate", "gate"))
    a = ap.parse_args()
    if a.cmd == "generate":
        do_generate()
    else:
        from ah_entry_gate import do_gate  # noqa: PLC0415
        do_gate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
