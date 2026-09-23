"""Generate the four sleeves the production path cannot reach, over the whole archive, WITH the path.

    python3 docs/audits/fable5-vision-audit-20260725/phase8/receipts/ak_supply_generate.py
    AK_ONLY=structural_retest python3 .../ak_supply_generate.py      # one spec at a time

WHAT IS NEW HERE, AGAINST AA AND AF
------------------------------------
AA walked the 29 sleeves `GenerationPort` can resolve; AF widened five production mechanisms
across the archive surface. Neither could touch `vol_squeeze`, `ny_index_momentum`,
`structural_retest` or `session_leadlag_genuine`, because those have no `SleeveSpec` at all —
`active_specs` cannot return them, so `GenerationPort` cannot drive them. This driver walks the
series directly against `walkforward.supply.SUPPLY_SPECS`, which is AF's measured-equivalent
approach (`SESSION_AF_FAMILY_EXPANSION_RESULT.md` §1: 10 of 10 trade counts and median holds
exact against `W_MX_PILOT.json`) applied to sleeves that are in no registry rather than to
symbols that are in no registry.

Four things it does that no prior driver did:

1. **Both exit labellings, with the AUTHORED contract as primary.** None of these four has a row
   in `SLEEVE_EXIT_PROFILES`, so each one's own docstring is the only statement of the contract
   its research validated: `vol_squeeze` a fixed 3R target, `ny_index_momentum` a targetless
   20-bar time stop, `structural_retest` 2R plus a 32-bar time stop, `session_leadlag_genuine`
   64 bars with a per-leg geometry. AD §6.2 measured that the live contract and the plain
   labelling differ materially on 15 of 25 sleeves and that nobody had checked; asking that
   question at generation time costs nothing, so `r_gross` is the authored contract and
   `r_gross_plain` is AA's estate-comparable stop/target/MAXBARS-80.

2. **Both clock readings for `structural_retest`.** Its F7 repair (B950) moves bars between
   session buckets, and the bucket is its whitelist key, so the repair changes which trades exist
   rather than only what they cost. Published as two populations, exactly as `EXIT_FRONTIER_V1`
   publishes both trail bounds.

3. **The HTF window-phase sensitivity, measured.** `bar_count` is not a free parameter for
   `structural_retest` (`supply.py` docstring). The same walk is re-run at a misaligned phase on
   a subset and the trade-set difference is reported, so the choice of 513 rests on a number.

4. **A prefilter parity run.** Each spec's prefilter is a necessary condition argued from
   `atr14`'s lookback; on real data one symbol per spec is walked with the prefilter DISABLED and
   the trade sets compared. A prefilter that dropped candidates would shrink the sleeve silently.

MEMORY
------
Three wave-8 sessions share this machine and the M15 archive is 2.7 M bars, so series are loaded
ONE (symbol, timeframe) at a time and dropped. The union close grid `engine_reachable` needs is
built in a first pass that reads only the time column, which is ~90 k distinct instants rather
than 2.7 M bars.

Offline and pure: reads gzipped CSV bars through `CsvBarSource` (which converts broker wall clock
to true UTC at the seam), imports no broker module, writes one gzipped JSON.
"""

from __future__ import annotations

import collections
import datetime as dt
import glob
import gzip
import json
import os
import statistics
import sys
import time
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.bar_provider import TF_H4, TF_M15, decision_day_of  # noqa: E402
from src.components.ultimate_book.primitives import Bar  # noqa: E402
from src.components.ultimate_book.sleeves import session_leadlag as SL  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import supply as SUP  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
OUT = REPO / "docs/audits/fable5-vision-audit-20260725/phase8/receipts/AK_SUPPLY_TRADES.json.gz"

#: AA's and AF's plain-labelling horizon, kept so `r_gross_plain` is comparable to the estate.
MAXBARS = 80
TF_NAME = SUP.TF_NAME
TF_MINUTES = SUP.TF_MINUTES

#: `af_family_generate.DUPLICATE_ALIASES` — the archive exports one instrument twice under two
#: spellings. Counted once, or a symbol family gets free breadth.
DUPLICATE_ALIASES = {"GER40_cash": "GER40", "JP225_cash": "JP225"}

#: The misaligned window length used for the HTF phase measurement (528 = 33*16, so the HTF
#: reference block ends 16 bars before the decision bar instead of 1).
PHASE_PROBE_BAR_COUNT = 528
PHASE_PROBE_SYMBOLS = ("BTCUSD", "XAUUSD", "SPX500")

#: One symbol per spec walked with the prefilter disabled, for the parity claim. Chosen as the
#: longest series in each surface so the comparison has the most bars to disagree on.
PARITY_SYMBOL = {
    "vol_squeeze": "US30_cash",
    "ny_index_momentum": "SPX500",
    "structural_retest": "XAUUSD",
    "session_leadlag_genuine": "AUDJPY",
}


# =====================================================================================
# archive access, one series at a time
# =====================================================================================

def archive_index() -> dict[tuple[str, int], str]:
    """(canonical, timeframe) -> path, for the FTMO M15/H4 exports."""
    out: dict[tuple[str, int], str] = {}
    for p in sorted(glob.glob(f"{BARS}/FTMO_*.csv.gz")):
        stem = os.path.basename(p)[len("FTMO_"):-len(".csv.gz")]
        sym, _, tfs = stem.rpartition("_")
        tf = {"M15": TF_M15, "H4": TF_H4}.get(tfs)
        if tf is None or sym in DUPLICATE_ALIASES:
            continue
        out[(sym, tf)] = p
    return out


def load_one(key: tuple[str, int], path: str) -> tuple[list[Bar], list[dt.datetime]]:
    """One series, through the production loader so the broker->UTC conversion is at the seam.

    A fresh `CsvBarSource` per call on purpose: the class caches decoded rows on itself, and a
    shared instance over 46 series would hold the whole archive resident.
    """
    rows = CsvBarSource({key: path}, label="vps-bars-20260727-FTMO")._load(key)
    if not rows:
        return [], []
    bars = [Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0)) for r in rows]
    times = [dt.datetime.fromisoformat(r["time"]) for r in rows]
    return bars, times


def load_times(key: tuple[str, int], path: str) -> list[dt.datetime]:
    bars, times = load_one(key, path)
    del bars
    return times


def union_close_grids(index: dict[tuple[str, int], str],
                      timeframes: set[int]) -> dict[int, list[dt.datetime]]:
    """Per timeframe, every archive symbol's bar CLOSE instants, unioned and sorted.

    Same construction as `af_family_generate.main` and `aa_estate_generate.main`: a symbol whose
    history starts later must not be truncated to another symbol's calendar.
    """
    stamps: dict[int, set[dt.datetime]] = {tf: set() for tf in timeframes}
    for (sym, tf), path in sorted(index.items()):
        if tf not in timeframes:
            continue
        for t in load_times((sym, tf), path):
            stamps[tf].add(t)
    return {tf: sorted(t + dt.timedelta(minutes=TF_MINUTES[tf]) for t in s)
            for tf, s in stamps.items()}


def engine_reachable(times: list[dt.datetime], grid: list[dt.datetime], ivl: dt.timedelta,
                     warm: int) -> set[int]:
    """`af_family_generate.engine_reachable`, verbatim in behaviour.

    At each cycle instant the engine drops the last visible candle as *forming*
    (`bar_provider.py:92`) and refuses a decision bar more than two intervals old
    (`book_engine.py:512`), which together make the last closed bar before every weekend or
    holiday unreachable. Kept as the PRIMARY population so a verdict is about trades the armed
    engine could take; the pre-gap population is generated anyway and published as a delta.
    """
    import bisect

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


# =====================================================================================
# labelling
# =====================================================================================

def authored_policy(spec: SUP.ResearchSleeveSpec, intent, tf: int) -> ExitPolicy:
    """The sleeve's OWN validated exit contract, per `spec.authored_exit`.

    `time_stop_bars` is in the sleeve's own decision-timeframe bars here, not in M15 units — for
    the three M15 sleeves those are the same thing, and `vol_squeeze` authors no time stop, so
    B750's M15-units finding does not bite. Stated because getting it wrong is exactly what B750
    found on the twelve `mx_*` sleeves.
    """
    ex = spec.authored_exit
    ts = ex.get("time_stop_bars")
    arm = gap = None
    if spec.tag == "session_leadlag_genuine":
        geom = (intent.ll_impulse or "@T2.0").rsplit("@", 1)[-1]
        arm, gap = SL.trail_for(geom, float(intent.stop_dist))
    return ExitPolicy(
        target_dist=(float(intent.target_dist) if intent.target_dist else None),
        trail_arm=arm, trail_gap=gap,
        time_stop_bars=(int(ts) if ts else None),
        maxbars=MAXBARS,
        label=f"authored:{ex['policy']}",
    )


def label(spec: SUP.ResearchSleeveSpec, symbol: str, broker_symbol: str, bars, times,
          i: int, intent, tf: int, reachable: bool, clock: str) -> dict:
    ivl = dt.timedelta(minutes=TF_MINUTES[tf])
    d = int(intent.direction)
    sd = float(intent.stop_dist)
    td = float(intent.target_dist) if intent.target_dist else None

    plain = ExitPolicy(target_dist=td, maxbars=MAXBARS, label="plain")
    pr_plain = replay(bars, i, d, stop_dist=sd, policy=plain)
    pol = authored_policy(spec, intent, tf)
    pr = replay(bars, i, d, stop_dist=sd, policy=pol)
    # AD's standing rule (B754, §7): every trail cell is run at BOTH bounds and both are
    # published. `session_leadlag_genuine`'s TRAIL leg is the only trailing contract here.
    r_honest = None
    if pol.trail_arm is not None:
        import dataclasses

        honest = dataclasses.replace(pol, trail_lag_extremes=True,
                                     label=pol.label + ":intrabar_honest")
        r_honest = float(winsorize_R(replay(bars, i, d, stop_dist=sd, policy=honest).r_gross))
    xi = pr.exit_index
    return {
        "r_gross_trail_intrabar_honest": r_honest,
        "sleeve": spec.tag,
        "symbol": broker_symbol,
        "symbol_canonical": symbol,
        "entry_utc": (times[i] + ivl).isoformat(),
        "exit_utc": (times[xi] + ivl).isoformat(),
        "direction": d,
        "sl_distance_price": sd,
        "entry_price": float(bars[i].c),
        "r_gross": float(winsorize_R(pr.r_gross)),
        "r_gross_plain": float(winsorize_R(pr_plain.r_gross)),
        "exit_policy": pol.label,
        "exit_reason": pr.exit_reason,
        "exit_reason_plain": pr_plain.exit_reason,
        "mfe_r": round(pr.mfe_r, 6),
        "mae_r": round(pr.mae_r, 6),
        "bars_to_mfe": int(pr.bars_to_mfe),
        "exit_bar_offset": int(xi - i),
        "exit_bar_offset_plain": int(pr_plain.exit_index - i),
        "hold_hours": round((xi - i) * TF_MINUTES[tf] / 60.0, 4),
        "target_dist": td,
        "intra_size": 1.0,
        "timeframe": int(tf),
        "decision_bar_iso": times[i].isoformat(),
        "decision_day": intent.decision_day,
        "entry_hour_utc": (times[i] + ivl).hour,
        "decision_hour_server": intent.decision_hour,
        "ll_impulse": intent.ll_impulse,
        "engine_reachable": reachable,
        "clock": clock,
        "bar_index": i,
    }


# =====================================================================================
# the walk
# =====================================================================================

def walk_symbol(spec: SUP.ResearchSleeveSpec, symbol: str, bars, times, reach: set[int],
                res, *, clock: str = "server_repaired", bar_count: int | None = None,
                leader_feeds=None, use_prefilter: bool = True) -> list[dict]:
    """One (spec, symbol) series. Returns labelled rows in bar order."""
    gen = spec.generator()
    L = int(bar_count or spec.bar_count)
    ctx = SUP.build_series_context(symbol, spec.timeframe, bars, times, **spec.needs())
    authored_utc = (clock == "authored_utc")
    out: list[dict] = []
    kw = {"leader_feeds": leader_feeds} if leader_feeds is not None else {}
    for i in range(L - 1, len(bars) - 2):
        if use_prefilter and not spec.prefilter(ctx, i, authored_utc_clock=authored_utc):
            continue
        lo = i - (L - 1)
        intent = gen(symbol, bars[lo:i + 1], decision_day_of(times[i]),
                     bar_time=times[i], bar_times=times[lo:i + 1],
                     aux_bars=None, aux_times=None, **kw)
        if intent is None:
            continue
        if int(intent.direction) not in (1, -1) or not (float(intent.stop_dist) > 0):
            continue
        out.append(label(spec, symbol, res(symbol), bars, times, i, intent,
                         spec.timeframe, i in reach, clock))
    return out


def apply_min_gap(rows: list[dict], min_gap: int) -> tuple[list[dict], int]:
    """`mine_pair`'s `min_gap`, applied per FOLLOWER in bar order. Returns (kept, dropped).

    Deliberately outside the generator (see `session_leadlag.py`'s docstring): it is per-series
    state, and a generator that remembered its own last fire would not be a pure function of the
    decision bar. Both counts are published so the research proxy is visible rather than assumed.
    """
    kept: list[dict] = []
    last: dict[str, int] = {}
    dropped = 0
    for r in sorted(rows, key=lambda x: (x["symbol_canonical"], x["bar_index"])):
        sym, i = r["symbol_canonical"], r["bar_index"]
        if i - last.get(sym, -10 ** 9) < min_gap:
            dropped += 1
            continue
        last[sym] = i
        kept.append(r)
    kept.sort(key=lambda x: x["entry_utc"])
    return kept, dropped


def build_leader_feeds(index, want: set[str]) -> dict[str, SL.LeaderImpulse]:
    feeds: dict[str, SL.LeaderImpulse] = {}
    for leader in sorted(want):
        key = (leader, TF_M15)
        path = index.get(key)
        if path is None:
            continue
        bars, times = load_one(key, path)
        if not bars:
            continue
        feeds[leader] = SL.LeaderImpulse(times, [b.c for b in bars])
        del bars
    return feeds


def _summary(rows: list[dict], field: str = "r_gross") -> dict:
    if not rows:
        return {"n": 0}
    r = [x[field] for x in rows]
    rr = [x for x in rows if x["engine_reachable"]]
    return {
        "n": len(rows),
        "n_engine_reachable": len(rr),
        "mean_r_gross": round(statistics.fmean(r), 6),
        "sum_r_gross": round(sum(r), 3),
        "mean_r_gross_reachable": (
            round(statistics.fmean(x[field] for x in rr), 6) if rr else None),
        "win_frac": round(sum(1 for x in r if x > 0) / len(r), 5),
        "mean_mfe_r": round(statistics.fmean(x["mfe_r"] for x in rows), 5),
        "mean_mae_r": round(statistics.fmean(x["mae_r"] for x in rows), 5),
        "median_hold_hours": round(statistics.median(x["hold_hours"] for x in rows), 4),
        "first": min(x["entry_utc"] for x in rows)[:10],
        "last": max(x["entry_utc"] for x in rows)[:10],
        "n_long": sum(1 for x in rows if x["direction"] > 0),
        "n_short": sum(1 for x in rows if x["direction"] < 0),
        "by_symbol": dict(
            sorted(collections.Counter(x["symbol_canonical"] for x in rows).items())),
        "mean_r_gross_by_symbol": {
            s: round(statistics.fmean(x[field] for x in rows
                                      if x["symbol_canonical"] == s), 5)
            for s in sorted({x["symbol_canonical"] for x in rows})},
    }


def _key(rows: list[dict]) -> set[tuple]:
    return {(r["symbol_canonical"], r["decision_bar_iso"], r["direction"]) for r in rows}


def main() -> dict:
    t_start = time.time()
    only = [s for s in (os.environ.get("AK_ONLY") or "").split(",") if s]
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AK")
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)

    index = archive_index()
    specs = {k: v for k, v in SUP.SUPPLY_SPECS.items() if not only or k in only}
    tfs = {s.timeframe for s in specs.values()}
    print(f"archive: {len(index)} (canonical, timeframe) series; specs: {sorted(specs)}")

    t0 = time.time()
    grids = union_close_grids(index, tfs)
    for tf, g in sorted(grids.items()):
        print(f"  {TF_NAME[tf]} union grid: {len(g)} closes {g[0].date()} .. {g[-1].date()}"
              f"  ({time.time()-t0:.0f}s)")

    trades: dict[str, list[dict]] = {}
    per_spec: dict[str, dict] = {}
    phase: dict = {}
    parity: dict = {}
    clock_ab: dict = {}

    for tag, spec in specs.items():
        print(f"\n=== {tag} [{TF_NAME[spec.timeframe]}] "
              f"{len(spec.on_surface)} symbols, bar_count={spec.bar_count} ===", flush=True)
        ts = time.time()
        feeds = None
        if spec.needs_cross_symbol_feed:
            feeds = build_leader_feeds(index, set(SL.LEADERS))
            print(f"  leader feeds: {sorted(feeds)}", flush=True)
            missing = sorted(set(SL.LEADERS) - set(feeds))
            if missing:
                print(f"  MISSING LEADERS {missing} — legs using them cannot fire")

        rows: list[dict] = []
        rows_authored_clock: list[dict] = []
        rows_phase: list[dict] = []
        dropped: list[tuple[str, str]] = []
        for symbol in spec.on_surface:
            key = (symbol, spec.timeframe)
            path = index.get(key)
            if path is None:
                dropped.append((symbol, "no bars for this (symbol, timeframe) in the archive"))
                continue
            bars, times = load_one(key, path)
            if len(bars) < spec.bar_count + 3:
                dropped.append((symbol, f"only {len(bars)} bars, need "
                                        f">= {spec.bar_count + 3}"))
                del bars, times
                continue
            reach = engine_reachable(times, grids[spec.timeframe],
                                     dt.timedelta(minutes=TF_MINUTES[spec.timeframe]),
                                     spec.bar_count)
            got = walk_symbol(spec, symbol, bars, times, reach, res, leader_feeds=feeds)
            rows.extend(got)
            print(f"  {symbol:12s} {len(bars):7d} bars -> {len(got):5d} intents "
                  f"({time.time()-ts:.0f}s)", flush=True)

            if spec.f7_ab:
                with SUP.authored_clock(spec.module):
                    rows_authored_clock.extend(
                        walk_symbol(spec, symbol, bars, times, reach, res,
                                    clock="authored_utc", leader_feeds=feeds))
            if tag == "structural_retest" and symbol in PHASE_PROBE_SYMBOLS:
                rows_phase.extend(walk_symbol(spec, symbol, bars, times, reach, res,
                                              bar_count=PHASE_PROBE_BAR_COUNT))
            if symbol == PARITY_SYMBOL.get(tag):
                unf = walk_symbol(spec, symbol, bars, times, reach, res,
                                  leader_feeds=feeds, use_prefilter=False)
                fil = [r for r in got if r["symbol_canonical"] == symbol]
                parity[tag] = {
                    "symbol": symbol,
                    "n_with_prefilter": len(fil),
                    "n_without_prefilter": len(unf),
                    "identical_trade_sets": _key(fil) == _key(unf),
                    "missed_by_prefilter": sorted(
                        f"{s}|{b}|{d}" for (s, b, d) in (_key(unf) - _key(fil)))[:20],
                    "extra_from_prefilter": sorted(
                        f"{s}|{b}|{d}" for (s, b, d) in (_key(fil) - _key(unf)))[:20],
                    "why": ("the prefilter is a NECESSARY condition argued from atr14's 14-bar "
                            "lookback; this is the measurement of that argument on real bars"),
                }
                print(f"  prefilter parity on {symbol}: "
                      f"{parity[tag]['identical_trade_sets']} "
                      f"({len(fil)} vs {len(unf)})", flush=True)
            del bars, times

        n_dropped_gap = 0
        if tag == "session_leadlag_genuine":
            all_rows = rows
            rows, n_dropped_gap = apply_min_gap(rows, SL.MIN_GAP_BARS)
            print(f"  min_gap={SL.MIN_GAP_BARS}: {len(all_rows)} -> {len(rows)} "
                  f"({n_dropped_gap} dropped)")
            per_spec.setdefault(tag, {})["without_min_gap"] = _summary(all_rows)
            if rows_authored_clock:
                rows_authored_clock, _ = apply_min_gap(rows_authored_clock, SL.MIN_GAP_BARS)

        rows.sort(key=lambda r: r["entry_utc"])
        trades[tag] = rows
        per_spec.setdefault(tag, {}).update({
            "timeframe": TF_NAME[spec.timeframe],
            "bar_count": spec.bar_count,
            "on_surface": list(spec.on_surface),
            "dropped_symbols": [{"symbol": s, "reason": w} for s, w in dropped],
            "authored_exit": spec.authored_exit,
            "provenance": spec.provenance,
            "why_unreachable": spec.why_unreachable,
            "notes": list(spec.notes),
            "min_gap_dropped": n_dropped_gap,
            "seconds": round(time.time() - ts, 1),
            "summary_authored_exit": _summary(rows, "r_gross"),
            "summary_plain_exit": _summary(rows, "r_gross_plain"),
        })

        if spec.f7_ab:
            clock_ab[tag] = {
                "repaired_server_clock": _summary(rows),
                "authored_utc_clock": _summary(rows_authored_clock),
                "n_only_repaired": len(_key(rows) - _key(rows_authored_clock)),
                "n_only_authored": len(_key(rows_authored_clock) - _key(rows)),
                "n_shared": len(_key(rows) & _key(rows_authored_clock)),
                "what": ("the F7 repair (B950/B960) moves bars between session buckets, and for "
                         "structural_retest the bucket is the whitelist key — so the repair "
                         "changes WHICH trades exist, not only what they cost. Both populations "
                         "published; the repaired one is primary because the server clock is what "
                         "the rule was mined on."),
            }
            print(f"  clock A/B: repaired n={len(rows)} vs authored-UTC "
                  f"n={len(rows_authored_clock)}; shared={clock_ab[tag]['n_shared']}")

        if rows_phase:
            a, b = _key([r for r in rows if r["symbol_canonical"] in PHASE_PROBE_SYMBOLS]), _key(rows_phase)
            phase = {
                "aligned_bar_count": spec.bar_count,
                "probe_bar_count": PHASE_PROBE_BAR_COUNT,
                "symbols": list(PHASE_PROBE_SYMBOLS),
                "n_aligned": len(a), "n_probe": len(b),
                "n_shared": len(a & b),
                "n_only_aligned": len(a - b), "n_only_probe": len(b - a),
                "jaccard": round(len(a & b) / max(1, len(a | b)), 5),
                "what": ("_htf_trend_at chunks HTF blocks from index 0 of the WINDOW, so which "
                         "absolute bars it reads depends on bar_count mod 16. At 513 the "
                         "reference block is the 16 bars immediately before the decision bar; at "
                         "528 it ends 16 bars earlier. This is the size of that difference in "
                         "TRADES, which is why bar_count is not a free parameter."),
            }
            print(f"  HTF phase probe: {phase['n_shared']} shared of "
                  f"{phase['n_aligned']}/{phase['n_probe']}, jaccard {phase['jaccard']}")

        ledger.record(
            mechanism="unregistered_sleeve_generation", sleeve=tag,
            variant={"timeframe": TF_NAME[spec.timeframe], "bar_count": spec.bar_count,
                     "exit": spec.authored_exit["policy"], "maxbars": MAXBARS,
                     "clock": "server_repaired", "archive": "vps-bars-20260727-FTMO"},
            window=(f"{rows[0]['entry_utc'][:10]}..{rows[-1]['entry_utc'][:10]}" if rows else ""),
            outcome="evaluated", metric=float(len(rows)), metric_name="n_trades_generated",
            note="AK sleeve supply — first walk of a generator with no SleeveSpec")

    out = {
        "schema": "gtos.walkforward.supply_trades.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase8/receipts/"
                         "ak_supply_generate.py"),
        "session": "AK", "blocks": "B950-B999",
        "bars_archive": BARS,
        "maxbars_plain": MAXBARS,
        "labelling": {
            "primary": "r_gross — the sleeve's OWN authored exit contract (see authored_exit)",
            "secondary": ("r_gross_plain — stop/target/MAXBARS-80, AA's and AF's convention, so "
                          "every number here is comparable to AA_ESTATE_TRADES and "
                          "AF_FAMILY_TRADES"),
            "why_both": ("none of these four has a SLEEVE_EXIT_PROFILES row, so the authored "
                         "contract is the only statement of what their research validated; AD "
                         "§6.2 measured that the two differ materially on 15 of 25 sleeves"),
            "engine": ("walkforward.exits.replay, fuzz-verified identical to "
                       "primitives.simulate_detail on R and exit index"),
        },
        "specs": per_spec,
        "prefilter_parity": parity,
        "clock_ab": clock_ab,
        "htf_phase_sensitivity": phase,
        "registry_edit_proposal": SUP.REGISTRY_EDIT_PROPOSAL,
        "live_wiring_gap": SUP.LIVE_WIRING_GAP,
        "n_trades_by_sleeve": {k: len(v) for k, v in sorted(trades.items())},
        "n_trades_total": sum(len(v) for v in trades.values()),
        "seconds_total": round(time.time() - t_start, 1),
        "trades": trades,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT, "wt") as fh:
        json.dump(out, fh, default=str)
    print(f"\nwrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1e6:.1f} MB) in "
          f"{time.time()-t_start:.0f}s")
    for k, v in sorted(trades.items(), key=lambda kv: -len(kv[1])):
        s = per_spec[k]["summary_authored_exit"]
        print(f"  {k:26s} {len(v):6d} trades  mean_gross_R "
              f"{s.get('mean_r_gross')}  reachable {s.get('n_engine_reachable')}")
    print(f"ledger: {ledger.n_written} rows written, {ledger.write_errors} errors")
    return out


if __name__ == "__main__":
    main()
