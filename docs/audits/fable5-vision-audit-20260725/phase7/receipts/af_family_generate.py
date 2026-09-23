"""Generate the mechanism x symbol x timeframe grid over the whole bars archive.

    python3 docs/audits/fable5-vision-audit-20260725/phase7/receipts/af_family_generate.py

WHAT THIS IS FOR
----------------
`FOURTH_REVIEW.md` §5.4: *"Every mechanism that survives anywhere is run across all 43
archive symbols (family discipline of §3.3: judged as a family with measured trial counts)."*
W judged twelve `mx_*` sleeves standalone, which charges each the full multiplicity bill
alone; the mechanism-level question was never asked. This produces the trades it needs.

THE GRID IS PRE-SPECIFIED AND COMPLETE
---------------------------------------
Five mechanisms x every archive symbol x the timeframes named below. Not a search: every
cell is taken, in a fixed order, and the ones that cannot be run are written to `dropped`
with a reason. Nothing here looks at an outcome, so nothing here can select on one.

HOW GENERATION IS DRIVEN, AND THE ONE THING IT DOES DIFFERENTLY FROM W
-----------------------------------------------------------------------
W's pilot and AA's estate walk both drive `GenerationPort`, which constructs the live
`UltimateBookLiveEngine` and calls `_generate_intents` — the strongest available fidelity,
and the right choice when the sleeve set IS the live book. This grid is 250+ members that
are deliberately NOT in any registry, so driving the live engine would mean writing them
into `sleeves/registry.py` — a production edit, for research symbols, on a repo whose FTMO
book is armed. This driver instead walks each series bar by bar and calls the SAME
production generator with the same 260-bar window the engine would have handed it
(`book_engine.py:483` `primary_count = max(bar_count, spec.bar_count)`;
`market_expansion_d1.BAR_COUNT = 260`).

That is a claim about equivalence, so it is MEASURED, not asserted: the twelve live `mx_*`
tags are re-generated here and their trade counts compared against the committed
`W_MX_PILOT.json`, and the two core H4 rules against `AA_ESTATE_TRADES.json.gz`. The
comparison is printed and written into the artifact under `parity`. Where the two disagree
the difference is explained, in the artifact, per sleeve.

Everything else is AA's harness verbatim: labelling through `walkforward.exits.replay`
(fuzz-verified identical to `simulate_detail` on R and exit index), `winsorize_R` from the
book's own bounds, MAXBARS 80 in the member's own timeframe so every number is comparable
to `W_MX_PILOT.json` and `AA_ESTATE_WALK.json`.

Offline and pure: reads gzipped CSV bars, imports no broker module, writes one gzipped JSON.
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
from src.components.ultimate_book.bar_provider import TF_D1, TF_H4, WARMUP  # noqa: E402
from src.components.ultimate_book.bar_provider import decision_day_of  # noqa: E402
from src.components.ultimate_book.primitives import Bar  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import family as fam  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
OUT = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts/AF_FAMILY_TRADES.json.gz"
MAXBARS = 80
TF_NAME = {TF_H4: "H4", TF_D1: "D1"}
TF_MINUTES = {TF_H4: 240, TF_D1: 1440}

#: mechanism -> which timeframes to sweep it on, and why that set and not another.
#:
#: `donchian_20_breakout` gets BOTH because the armed `crypto` sleeve is the same donchian
#: mechanism on H4 (`FOURTH_REVIEW.md` §3.1) and the session prompt asks the crypto family
#: at both. The other two D1 mechanisms are swept at their authored timeframe only: a
#: timeframe variant is a fresh hypothesis on every symbol at once, and 86 more looks bought
#: nothing this session's work list asks for. That is a SCOPE CAP and it is recorded here
#: rather than left as an absence (working agreement: no silent caps).
SWEEP: dict[str, tuple[int, ...]] = {
    "donchian_20_breakout": (TF_D1, TF_H4),
    "volume_surge_reversal": (TF_D1,),
    "atr_mean_reversion": (TF_D1,),
    "crypto_h4_donchian_ac60": (TF_H4,),
    "energy_fvg_retest": (TF_H4,),
}

#: Canonical names the archive exports twice under two spellings of one broker instrument.
#: Measured: `FTMO_JP225_*` and `FTMO_JP225_cash_*` are byte-identical at D1 and H4, and the
#: GER40 pair differs in exactly one field of one row (the forming bar, re-pulled seconds
#: apart in the dotted-name top-up). Keeping both would put the same instrument in a family
#: twice and inflate its breadth for free.
DUPLICATE_ALIASES = {"GER40_cash": "GER40", "JP225_cash": "JP225"}


def load_archive(res):
    """(canonical, timeframe) -> (bars, times_utc). Broker wall clock converted at the seam."""
    files: dict[tuple[str, int], str] = {}
    for p in sorted(glob.glob(f"{BARS}/FTMO_*.csv.gz")):
        stem = os.path.basename(p)[len("FTMO_"):-len(".csv.gz")]
        sym, _, tfs = stem.rpartition("_")
        tf = {"D1": TF_D1, "H4": TF_H4}.get(tfs)
        if tf is None:
            continue
        files[(sym, tf)] = p
    # CsvBarSource is keyed on whatever the caller uses; here that is the CANONICAL name,
    # which is also how the archive files are named (BARS_MANIFEST.json "SYMBOL_NAMING").
    src = CsvBarSource(files, label="vps-bars-20260727-FTMO")
    series: dict[tuple[str, int], tuple[list[Bar], list[dt.datetime]]] = {}
    for key in files:
        rows = src._load(key)
        if not rows:
            continue
        series[key] = (
            [Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0))
             for r in rows],
            [dt.datetime.fromisoformat(r["time"]) for r in rows],
        )
    return series, files


def engine_reachable(times: list[dt.datetime], grid: list[dt.datetime], ivl: dt.timedelta,
                     warm: int) -> set[int]:
    """The bar indices the LIVE engine can ever hand a generator, on this union grid.

    Reproduced rather than approximated, because it is not a rounding difference. At each
    cycle instant `now` the engine fetches the candles visible at `now` and
    `candles_to_bars` drops the last one as *forming* (`bar_provider.py:92`) — so the
    decision bar is the second-to-last visible bar. Then `book_engine.py:512` refuses a
    decision bar whose close is more than two intervals old.

    Composed, those two rules make **the last closed bar before every weekend and holiday
    unreachable**: at its own close it is the last visible candle and is dropped as forming,
    and by the time the next session's bar makes it second-to-last it is stale. That is
    `bar_provider.py:60-80`'s own docstring, measured by Session AB (`ab_port_parity.py`,
    29 of 29 fires immediately before a >= 2-interval gap, 1.3 %-6.8 % of trades on five H4
    sleeves). This function is the D1 restatement of it, and D1 is where it bites hardest —
    every Friday is a pre-gap bar.

    Kept as the PRIMARY population because a family verdict has to be about trades the
    armed engine could actually take, and because it is what makes this driver comparable
    to `W_MX_PILOT.json` and `AA_ESTATE_TRADES.json.gz` bar for bar. The unreachable
    population is generated anyway and published as a delta, since "how much edge sits in
    bars the plumbing cannot reach" is a repair item, not a rounding error.
    """
    import bisect

    out: set[int] = set()
    two = 2 * ivl
    for now in grid:
        j = bisect.bisect_right(times, now) - 1
        if j < 1:
            continue
        d = j - 1                       # drop_forming
        if d < warm - 1:
            continue
        close = times[d] + ivl
        if close > now or (now - close) > two:
            continue
        out.add(d)
    return out


def generate_member(m: fam.FamilyMember, gen, series, warm_cluster: str,
                    reach: set[int]) -> list[dict]:
    """Walk one (symbol, timeframe) series and label every intent the rule emits.

    The window handed to the generator is `bars[i-259 : i+1]` — the engine's
    `max(bar_count=260, spec.bar_count=260)` most recent CLOSED bars at the instant bar `i`
    closes, which is what `get_closed_bars` returns after `candles_to_bars` drops the
    forming bar. `runtime_now` is that close instant, so `next_open_decision_day` stamps the
    same date the live engine would (`market_expansion_d1.py:147-161`).
    """
    key = (m.symbol, m.timeframe)
    got = series.get(key)
    if got is None:
        return []
    bars, times = got
    ivl = dt.timedelta(minutes=TF_MINUTES[m.timeframe])
    # `enough(bars, cluster)` is the live warmup floor (`book_engine.py:490`), and the
    # window is the 260 most recent CLOSED bars. Starting the walk at 259 instead of
    # `warm - 1` would silently drop every candidate between the warmup floor and the full
    # window — 60 bars of history per symbol, and rather more than that on the short-history
    # crypto minors, all of which the live engine WOULD have generated.
    warm = WARMUP.get(warm_cluster, 200)
    out: list[dict] = []
    n = len(bars)
    for i in range(warm - 1, n - 2):
        lo = max(0, i - 259)
        w = bars[lo:i + 1]
        close_at = times[i] + ivl
        intent = gen(m.symbol, w, decision_day_of(times[i]),
                     bar_time=times[i], bar_times=times[lo:i + 1],
                     aux_bars=None, aux_times=None, runtime_now=close_at)
        if intent is None:
            continue
        d = int(intent.direction)
        sd = float(intent.stop_dist)
        td = intent.target_dist
        if d not in (1, -1) or not (sd > 0):
            continue
        pol = ExitPolicy(target_dist=(float(td) if td else None), maxbars=MAXBARS,
                         label="plain")
        pr = replay(bars, i, d, stop_dist=sd, policy=pol)
        xi = pr.exit_index
        out.append({
            "member": m.member, "symbol": m.broker_symbol, "symbol_canonical": m.symbol,
            "entry_utc": (times[i] + ivl).isoformat(),
            "exit_utc": (times[xi] + ivl).isoformat(),
            "direction": d, "sl_distance_price": sd, "entry_price": float(bars[i].c),
            "r_gross": float(winsorize_R(pr.r_gross)),
            "target_dist": (float(td) if td else None),
            "exit_reason": pr.exit_reason,
            "mfe_r": round(pr.mfe_r, 6), "mae_r": round(pr.mae_r, 6),
            "bars_to_mfe": int(pr.bars_to_mfe),
            "exit_bar_offset": int(xi - i),
            "hold_hours": round((xi - i) * TF_MINUTES[m.timeframe] / 60.0, 4),
            "decision_bar_iso": times[i].isoformat(),
            "decision_day": intent.decision_day,
            "timeframe": m.timeframe,
            "entry_hour_utc": (times[i] + ivl).hour,
            "engine_reachable": (i in reach),
        })
    return out


def warm_cluster_for(parent_sleeve: str) -> str:
    """The parent's own registry cluster, so a member warms up exactly as its parent does.

    Read from the production registry rather than transcribed: the fourteen `mx_*` specs
    take their cluster from `candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_CANDIDATES`
    (`sleeves/registry.py:107`) and those names — `crypto_alt_or_major`, `indices_context`
    — are not keys in `bar_provider.WARMUP`, so they land on its default of 200. Writing
    "market_expansion" here by hand would have looked deliberate and meant the same thing
    by accident.
    """
    from src.components.ultimate_book.sleeves.registry import (
        BUILT,
        CANDIDATE_BUILT,
        MARKET_EXPANSION_BUILT,
    )

    for table in (BUILT, CANDIDATE_BUILT, MARKET_EXPANSION_BUILT):
        spec = table.get(parent_sleeve)
        if spec is not None:
            return spec.cluster
    raise KeyError(f"no registry spec for parent sleeve {parent_sleeve!r}")


def main() -> dict:
    t_start = time.time()
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AF")
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    supports = getattr(res, "supports", None)

    series, files = load_archive(res)
    print(f"archive: {len(series)} (canonical, timeframe) series loaded")

    all_syms = sorted({s for (s, _tf) in files})
    symbols = [s for s in all_syms if s not in DUPLICATE_ALIASES]
    grid = fam.FamilyGrid()
    for key, tfs in SWEEP.items():
        g = fam.family_members([key], tfs, symbols=symbols, broker_symbol=res,
                               profile_supports=(supports if callable(supports) else None))
        grid.members.extend(g.members)
        grid.dropped.extend(g.dropped)
    for alias, keep in sorted(DUPLICATE_ALIASES.items()):
        grid.dropped.append((
            f"*|{alias}|*",
            f"duplicate export of the same broker instrument as {keep} "
            f"(BARS_MANIFEST broker_symbol identical; D1/H4 content byte-identical for "
            f"JP225, one forming-bar field apart for GER40). Counted once, as {keep}."))
    for m in list(grid.members):
        if (m.symbol, m.timeframe) not in series:
            grid.members.remove(m)
            grid.dropped.append((m.member, "no bars for this (symbol, timeframe)"))

    print(f"grid: {len(grid.members)} members over {len(grid.families())} families; "
          f"{grid.n_looks} looks; {len(grid.dropped)} cells dropped")

    warm = {k: warm_cluster_for(s.parent_sleeve) for k, s in fam.MECHANISMS.items()
            if k in SWEEP}
    print(f"warmup clusters: {warm} -> "
          f"{ {k: WARMUP.get(v, 200) for k, v in warm.items()} } bars")

    # The union close grid, per timeframe, built exactly as `w_mx_pilot.build_trades` and
    # `aa_estate_generate.main` build theirs: every symbol's own bar closes, unioned, so a
    # symbol whose history starts later is not truncated to another symbol's calendar.
    grids: dict[int, list[dt.datetime]] = {}
    for tf in sorted({m.timeframe for m in grid.members}):
        stamps = {t for (s, k), (_b, ts) in series.items() if k == tf for t in ts}
        grids[tf] = sorted(t + dt.timedelta(minutes=TF_MINUTES[tf]) for t in stamps)
        print(f"  {TF_NAME[tf]} union grid: {len(grids[tf])} closes "
              f"{grids[tf][0].date()} .. {grids[tf][-1].date()}")
    reach_cache: dict[tuple[str, int, int], set[int]] = {}

    trades: dict[str, list[dict]] = {}
    t0 = time.time()
    with fam.expanded_surface(grid.members) as gens:
        for k, m in enumerate(grid.members):
            wc = warm[m.mechanism_key]
            nwarm = WARMUP.get(wc, 200)
            rk = (m.symbol, m.timeframe, nwarm)
            if rk not in reach_cache:
                got = series.get((m.symbol, m.timeframe))
                reach_cache[rk] = engine_reachable(
                    got[1], grids[m.timeframe],
                    dt.timedelta(minutes=TF_MINUTES[m.timeframe]), nwarm) if got else set()
            rows = generate_member(m, gens[m.member], series, wc, reach_cache[rk])
            trades[m.member] = rows
            if (k + 1) % 40 == 0:
                el = time.time() - t0
                print(f"  {k+1}/{len(grid.members)}  {el:.0f}s  "
                      f"eta {el/(k+1)*(len(grid.members)-k-1):.0f}s  "
                      f"trades={sum(len(v) for v in trades.values())}", flush=True)
    n_tr = sum(len(v) for v in trades.values())
    n_reach = sum(1 for v in trades.values() for r in v if r["engine_reachable"])
    print(f"generation+labelling: {n_tr} trades over {len(trades)} members in "
          f"{time.time()-t0:.0f}s; {n_reach} engine-reachable, {n_tr-n_reach} pre-gap")

    parity = check_parity(trades, grid, res)
    pre_gap = pre_gap_summary(trades, grid)

    for m in grid.members:
        ledger.record(
            mechanism=m.mechanism, sleeve=m.member,
            variant={"symbol": m.symbol, "timeframe": TF_NAME[m.timeframe],
                     "asset_class": m.asset_class, "parent_sleeve": m.parent_sleeve,
                     "maxbars": MAXBARS, "authored_cell": m.is_authored_cell,
                     "archive": "vps-bars-20260727-FTMO"},
            window=_window(trades[m.member]),
            outcome="evaluated", metric=float(len(trades[m.member])),
            metric_name="n_trades_generated",
            note="AF family expansion — one (mechanism, symbol, timeframe) cell")

    out = {
        "schema": "gtos.walkforward.family_trades.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase7/receipts/"
                         "af_family_generate.py"),
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "bars_archive": BARS,
        "maxbars": MAXBARS,
        "sweep": {k: [TF_NAME[t] for t in v] for k, v in SWEEP.items()},
        "mechanisms": {k: {"mechanism": s.mechanism, "parent_sleeve": s.parent_sleeve,
                           "authored_timeframe": TF_NAME.get(s.authored_timeframe),
                           "source": s.source}
                       for k, s in fam.MECHANISMS.items() if k in SWEEP},
        "grid": grid.as_dict(),
        "parity": parity,
        "pre_gap_population": pre_gap,
        "n_trades_by_member": {k: len(v) for k, v in sorted(trades.items())},
        "n_trades_by_member_engine_reachable": {
            k: sum(1 for r in v if r["engine_reachable"]) for k, v in sorted(trades.items())},
        "n_trades_total": n_tr,
        "n_trades_engine_reachable": n_reach,
        "members_with_no_trade": sorted(k for k, v in trades.items() if not v),
        "seconds_total": round(time.time() - t_start, 1),
        "trades": trades,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT, "wt") as fh:
        json.dump(out, fh, default=str)
    print(f"wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1e6:.1f} MB)")
    print(f"ledger: {ledger.n_written} rows written, {ledger.write_errors} errors")
    return out


def _window(rows: list[dict]) -> str:
    if not rows:
        return ""
    return f"{rows[0]['entry_utc'][:10]}..{rows[-1]['entry_utc'][:10]}"


def pre_gap_summary(trades: dict[str, list[dict]], grid: fam.FamilyGrid) -> dict:
    """How much signal sits in bars `bar_provider.py:60-80` says the live book cannot reach.

    Reported per family and in total, in R, because "the plumbing drops the pre-gap bar" is
    a sentence and "it is N trades a year worth X R" is a decision.
    """
    by_fam: dict[str, dict] = {}
    fams = grid.families()
    for f, ms in sorted(fams.items()):
        rows = [r for m in ms for r in trades.get(m.member, ())]
        gap = [r for r in rows if not r["engine_reachable"]]
        rch = [r for r in rows if r["engine_reachable"]]
        if not rows:
            continue
        by_fam[f] = {
            "n_total": len(rows), "n_reachable": len(rch), "n_pre_gap": len(gap),
            "pre_gap_frac": round(len(gap) / len(rows), 5),
            "mean_r_gross_reachable": (
                round(statistics.fmean(r["r_gross"] for r in rch), 5) if rch else None),
            "mean_r_gross_pre_gap": (
                round(statistics.fmean(r["r_gross"] for r in gap), 5) if gap else None),
            "sum_r_gross_pre_gap": round(sum(r["r_gross"] for r in gap), 4),
        }
    allrows = [r for v in trades.values() for r in v]
    gap = [r for r in allrows if not r["engine_reachable"]]
    return {
        "what": ("bars whose close is the last before a >= 2-interval gap. The live engine "
                 "drops them as forming at their own close (bar_provider.py:92) and refuses "
                 "them as stale afterwards (book_engine.py:512). PRIMARY population excludes "
                 "them, so every number here is comparable to W_MX_PILOT and AA_ESTATE."),
        "prior_measurement": ("Session AB, phase6/receipts/ab_port_parity.py — 29 of 29 fires "
                              "immediately before a >= 2-interval gap on five H4 sleeves, "
                              "1.3 %-6.8 % of trades. This is the D1 restatement."),
        "n_total": len(allrows), "n_pre_gap": len(gap),
        "pre_gap_frac": round(len(gap) / max(1, len(allrows)), 5),
        "sum_r_gross_pre_gap": round(sum(r["r_gross"] for r in gap), 3),
        "mean_r_gross_pre_gap": (
            round(statistics.fmean(r["r_gross"] for r in gap), 5) if gap else None),
        "mean_r_gross_reachable": round(statistics.fmean(
            r["r_gross"] for r in allrows if r["engine_reachable"]), 5),
        "by_family": by_fam,
    }


def check_parity(trades: dict[str, list[dict]], grid: fam.FamilyGrid, res) -> dict:
    """Does this driver reproduce the drivers that produced the estate's committed numbers?

    Compared where the same (rule, symbol, timeframe) exists on both sides:

      * W's twelve live `mx_*` sleeves, `phase5/receipts/W_MX_PILOT.json`
        (`GenerationPort` over a union D1 grid, deduped on decision_bar_iso);
      * `crypto` and `energy_agri`, `phase6/receipts/AA_ESTATE_TRADES.json.gz`
        (`GenerationPort` over the H4 grid).

    A difference is not automatically a defect — the union-grid drivers and this one visit
    different instants — but it must be explained, so both counts are published per sleeve
    with the ratio.
    """
    def _reach(member: str | None) -> int | None:
        v = trades.get(member) if member else None
        return None if v is None else sum(1 for r in v if r["engine_reachable"])

    # The registry and the archive spell the same instrument differently — `US100_cash` vs
    # `NAS100`, `US500_cash` vs `SPX500`, `JP225_cash` vs `JP225`. Both spellings resolve to
    # one BROKER symbol, which is what makes them the same instrument, so the bridge goes
    # through the production resolver rather than through a hand-written alias table. The
    # first run of this check reported six sleeves as "not compared" purely on spelling.
    by_broker = {m.broker_symbol: m for m in grid.members}

    out: dict[str, dict] = {}
    wp = REPO / "docs/audits/fable5-vision-audit-20260725/phase5/receipts/W_MX_PILOT.json"
    if wp.is_file():
        w = json.loads(wp.read_text())
        ref = w.get("n_trades_by_sleeve", {})
        rows = {}
        for tag, n_w in sorted(ref.items()):
            sym, mech = _mx_tag_parts(tag)
            if sym is None:
                continue
            hit = by_broker.get(res(sym))
            member = fam.member_name(mech, hit.symbol, TF_D1) if hit else None
            rows[tag] = {
                "w_mx_pilot": n_w,
                "af_engine_reachable": _reach(member),
                "af_all_closed_bars": (len(trades[member]) if member in trades else None),
                "member": member,
                "archive_symbol": (hit.symbol if hit else None),
                "note": (None if hit else
                         f"{sym} resolves to {res(sym)}, absent from the bars archive"),
            }
        cmp_ = [r for r in rows.values() if r["af_engine_reachable"] is not None]
        out["W_MX_PILOT"] = {
            "reference": str(wp.relative_to(REPO)),
            "driver": "GenerationPort over a union D1 close grid, deduped",
            "rows": rows,
            "n_compared": len(cmp_),
            "n_exact": sum(1 for r in cmp_ if r["af_engine_reachable"] == r["w_mx_pilot"]),
        }
    ap = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"
    if ap.is_file():
        with gzip.open(ap, "rt") as fh:
            a = json.load(fh)
        ref = a.get("n_trades_by_sleeve", {})
        rows = {}
        for parent, key, syms in (("crypto", "crypto_h4_donchian_ac60", ("BTCUSD", "DASHUSD")),
                                  ("energy_agri", "energy_fvg_retest",
                                   ("USOIL_cash", "UKOIL_cash"))):
            names = [fam.member_name(key, s, TF_H4) for s in syms]
            rows[parent] = {
                "aa_estate": ref.get(parent),
                "af_engine_reachable": sum((_reach(n) or 0) for n in names),
                "af_all_closed_bars": sum(len(trades.get(n, ())) for n in names),
                "symbols": list(syms), "members": names,
            }
        out["AA_ESTATE_TRADES"] = {
            "reference": str(ap.relative_to(REPO)),
            "driver": "GenerationPort over the H4 close grid",
            "rows": rows,
            "n_exact": sum(1 for r in rows.values()
                           if r["aa_estate"] == r["af_engine_reachable"]),
            "n_compared": len(rows),
        }
    return out


def _mx_tag_parts(tag: str) -> tuple[str | None, str]:
    from src.components.ultimate_book.sleeves import market_expansion_d1 as mx

    rule = mx.TAG_TO_RULE.get(tag)
    if rule is None:
        return None, ""
    sym, mech = rule
    key = {"d1_donchian_20_breakout": "donchian_20_breakout",
           "d1_volume_surge_reversal": "volume_surge_reversal",
           "d1_atr_mean_reversion": "atr_mean_reversion"}[mech]
    return sym, key


if __name__ == "__main__":
    main()
