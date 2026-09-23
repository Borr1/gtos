"""Pilot: walk the live 12-sleeve market-expansion family through the gate, for real.

    python3 docs/audits/fable5-vision-audit-20260725/phase5/receipts/w_mx_pilot.py

WHY A PILOT IS IN SESSION W'S SCOPE
------------------------------------
Session W owes Borhen an admission standard he can actually decide on: "a small number of
coherent options with the trade-off stated, and -- the part that matters -- what each
option would admit and reject out of the 23, so he is choosing between outcomes rather than
between adjectives." That sentence cannot be honoured with adjectives. It needs the family
actually run.

The full estate walk (all 14 collision-winners, the three orphan cache sleeves, the deep
archive, the full rigour) is Session X's. This is the 12 sleeves the LIVE config resolves,
over the archive that exists, at broker truth, so the options table has numbers in it.

WHAT DRIVES IT
--------------
Production code the whole way down, because reimplementing any of these is the failure mode
that bit three agents this week:

    sleeve set      `admission.effective_registry` via `GenerationPort.active_sleeve_names`
    canonical->broker `symbol_map.build_broker_symbol_resolver(profile)`
    generation      `replay_policy.generation.GenerationPort` (Session K's port)
    outcome         `ultimate_book.primitives.simulate_detail` -- the sanctioned single fill
                    authority (`admission.py:29`: "ALL fills go through geometry_lib.simulate
                    (leak-free pessimistic labeler) -- never hand-rolled")
    cost            `src.costs.cost_r`
    verdict         `src.research_infra.walkforward.run_gate`

FOUR LIMITATIONS, STATED UP FRONT RATHER THAN IN A FOOTNOTE
------------------------------------------------------------
1. **Entry is the decision bar's CLOSE, not the next D1 OPEN.** The sleeve's contract is
   next-open (`market_expansion_d1.py:5-8`), but `simulate` enters at `bars[i].c`
   (`primitives.py:37`) and it is the only sanctioned labeler. Hand-rolling a next-open
   variant would be exactly the "never hand-rolled" this repo forbids. The divergence is
   the overnight gap, so this run MEASURES the gap distribution in R units and publishes it
   rather than waving at it. Both are leak-free; neither uses future information.
2. **Port fidelity for this family is TRANSFERRED, on n=5.** K measured one mx sleeve
   (`mx_nzdjpy_d1_donchian_20_breakout`, 5 agreed / 0 live-only). The 96% per-bar class rate
   is real but 148 of its 160 agreed intents come from three core-book sleeves. Every
   verdict here carries that stamp; see `walkforward/fidelity.py`.
3. **Two sleeves cannot be generated and three cannot be priced.** `EU50.cash` and
   `FRA40.cash` are absent from the bars archive entirely; `CADJPY`, `EU50.cash` and
   `FRA40.cash` have no measured spread in `BROKER_TRUE_COSTS_V1.json`, so `cost_r` refuses
   them (`model.py:349-352`). That leaves **9 of 12** evaluable. This is a data-capture
   requirement, not a modelling choice.
4. **D13 is worked around, not fixed.** For market-expansion sleeves the port's
   `decision_day` is the runtime WALL-CLOCK date, not the bar's
   (`GENERATION_PORT_DEFECT_REGISTER.md` D13). This driver keys everything off
   `decision_bar_iso` and `features["bar_decision_day"]`, never `decision_day`.

Offline and pure: reads gzipped CSV bars and the cost artifact, imports no broker module,
writes one JSON.
"""

from __future__ import annotations

import collections
import datetime as dt
import glob
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
from src.components.ultimate_book.bar_provider import TF_D1  # noqa: E402
from src.components.ultimate_book.primitives import Bar, simulate_detail  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource, GenerationPort  # noqa: E402
from src.research_infra.walkforward import TradeRecord, run_gate  # noqa: E402
from src.research_infra.walkforward.spec import GateSpec  # noqa: E402

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
OUT = REPO / "docs/audits/fable5-vision-audit-20260725/phase5/receipts/W_MX_PILOT.json"

def build_port():
    base = yaml.safe_load(open(REPO / "config/agent_config.yaml"))
    cfg = dict(base.get("gtos_vnext_runtime") or {})
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    files = {}
    for p in glob.glob(f"{BARS}/FTMO_*_D1.csv.gz"):
        sym = os.path.basename(p)[len("FTMO_"):-len("_D1.csv.gz")]
        files[(res(sym), TF_D1)] = p
    src = CsvBarSource(files, label="vps-bars-FTMO-D1")
    port = GenerationPort(cfg, src, namespace="w_mx_pilot", broker_symbol=res)
    return port, src, res, files


def load_series(src, key) -> tuple[list[Bar], list[dt.datetime]]:
    rows = src._load(key)
    bars = [Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0)) for r in rows]
    times = [dt.datetime.fromisoformat(r["time"]) for r in rows]
    return bars, times


def build_trades(maxbars: int = 80):
    """Generate and label the family's trades. Extracted from `main` unchanged.

    Extracted by Session AG (wave 6) so the same labelled trades can be run through the
    gate at more than one spread band without regenerating them, and WITHOUT re-implementing
    the loop -- this file's own header names re-implementation as the failure mode that bit
    three agents. `main` calls it and behaves exactly as before; equality of the trade
    counts against the committed W_MX_PILOT.json is asserted by the banded driver.

    Returns ``(trades, mx, meta)``.
    """
    port, src, res, files = build_port()
    active = port.active_sleeve_names()
    mx = sorted(s for s in active if s.startswith("mx_"))
    print(f"live effective registry: {len(active)} sleeves; market-expansion: {len(mx)}")

    series: dict[str, tuple[list[Bar], list[dt.datetime]]] = {}
    index: dict[str, dict[dt.datetime, int]] = {}
    for (sym, tf) in files:
        if tf != TF_D1:
            continue
        b, t = load_series(src, (sym, tf))
        if sym in series and len(series[sym][0]) >= len(b):
            continue
        series[sym] = (b, t)
        index[sym] = {ts: i for i, ts in enumerate(t)}

    # Drive the UNION of D1 closes across every symbol the family can trade, so a symbol
    # whose history starts later is not silently truncated to another symbol's grid.
    grid = sorted({ts + dt.timedelta(minutes=1440) for _s, (_b, t) in series.items() for ts in t})
    print(f"driving {len(grid)} union D1 closes {grid[0].date()} .. {grid[-1].date()}")

    t0 = time.time()
    cands: list = []
    for i, ts in enumerate(grid):
        cands.extend(port.generate(ts, tags=mx).candidates)
        if (i + 1) % 4000 == 0:
            print(f"  {i+1}/{len(grid)}  {time.time()-t0:.0f}s  candidates={len(cands)}", flush=True)
    print(f"generation: {len(cands)} candidates in {time.time()-t0:.0f}s")

    # ---- label outcomes through the sanctioned fill authority ---------------------------
    # Seed EVERY sleeve in the family, including ones that will produce nothing. A
    # defaultdict populated only inside the labelling loop silently dropped the two sleeves
    # with no bars, shrinking the multiplicity family from 12 to 10 — a 40% weaker
    # Bonferroni threshold — in a gate whose own docstring says refused sleeves must stay in
    # the family precisely so they cannot make the survivors easier to admit.
    trades: dict[str, list[TradeRecord]] = {s: [] for s in mx}
    gaps: list[float] = []
    skipped: collections.Counter = collections.Counter()
    # Live places each (sleeve, symbol, decision_bar) AT MOST ONCE — `book_owner.py:163`,
    # enforced by `PlacementLedger`, with `decision_bar_iso` named as the idempotency key at
    # `book_engine.py:546-548`. The union D1 grid re-fires a 5-day symbol's last closed bar
    # on the weekend instants contributed by the 7-day crypto symbols, and the staleness
    # guard permits it for two intervals. Un-deduped that was 589 of 2,675 rows (22.0%),
    # reaching 36% on the FX/index sleeves and 0.5-11% on crypto — 2/7 = 28.6%, the shape of
    # the cause. Duplicates are byte-identical so the day-MEAN is unchanged, but the sample
    # gate counts trades, not days, and would have been told it had 28% more evidence.
    seen: set = set()
    deduped = []
    for c in cands:
        key = (c.sleeve, c.symbol, c.decision_bar_iso)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(c)
    n_dupes = len(cands) - len(deduped)
    print(f"  deduped on (sleeve, symbol, decision_bar_iso): dropped {n_dupes} of "
          f"{len(cands)} ({100.0*n_dupes/max(1,len(cands)):.1f}%)")
    cands = deduped

    for c in cands:
        # `PolicyCandidate.symbol` is the sleeve's CANONICAL/file symbol -- the market-
        # expansion generator matches on `spec.file_symbol` (`market_expansion_d1.py:199`),
        # so it emits e.g. "US500_cash", not "US500.cash". The bar series and `cost_r` are
        # both keyed on the BROKER symbol. Cross that boundary with the production resolver,
        # never by hand: the first draft of this driver matched `c.symbol` straight against
        # the broker-keyed series and silently dropped 716 candidates across five index
        # sleeves, reporting all five as "produced no trade at all".
        sym = res(c.symbol)
        bt = index.get(sym)
        if bt is None:
            skipped[f"{c.sleeve}:no_series[{c.symbol}->{sym}]"] += 1
            continue
        iso = c.decision_bar_iso
        if not iso:
            skipped[f"{c.sleeve}:no_decision_bar_iso"] += 1
            continue
        i = bt.get(dt.datetime.fromisoformat(iso))
        if i is None or i + 2 >= len(series[sym][0]):
            skipped[f"{c.sleeve}:bar_not_found_or_no_room"] += 1
            continue
        bars, times = series[sym]
        r, xi = simulate_detail(
            bars, i, c.direction, stop_dist=c.stop_dist,
            target_dist=c.target_dist, maxbars=maxbars, cost=0.0,
        )
        r = winsorize_R(r)  # the book's own bounds, imported not re-declared
        entry = bars[i].c
        # Limitation 1, measured: how far is the decision-bar close from the next open,
        # in R units? That is the size of the entry-convention divergence.
        # SIGNED and direction-adjusted: positive means the next open would have been
        # BETTER for the trade, i.e. close entry is disadvantaged. The absolute value
        # published by an earlier revision overstated the bias by 107x (|gap| 0.07706 R
        # against a signed +0.00072 R) and would have led a reader to assume a large
        # advantage in the optimistic direction. It is neither large nor optimistic.
        gaps.append(c.direction * (bars[i + 1].o - entry) / c.stop_dist)
        trades[c.sleeve].append(TradeRecord(
            sleeve=c.sleeve, symbol=sym, entry_utc=times[i],
            exit_utc=times[xi], direction=c.direction,
            sl_distance_price=float(c.stop_dist), entry_price=float(entry),
            r_gross=float(r),
            features={"bar_decision_day": c.features.get("bar_decision_day"),
                      "exit_bar_index_offset": xi - i},
        ))

    print(f"\nlabelled {sum(len(v) for v in trades.values())} trades over "
          f"{len(trades)} sleeves; skipped {sum(skipped.values())}")
    if skipped:
        print("  skips:", dict(skipped))

    silent = [s for s in mx if s not in trades]
    print(f"  produced no trade at all: {silent}")

    abs_gaps = [abs(g) for g in gaps]
    entry_gap = {
        "n": len(gaps),
        "mean_signed_R": round(statistics.fmean(gaps), 5) if gaps else None,
        "median_signed_R": round(statistics.median(gaps), 5) if gaps else None,
        "mean_abs_R": round(statistics.fmean(abs_gaps), 5) if abs_gaps else None,
        "p95_abs_R": round(sorted(abs_gaps)[int(0.95 * len(abs_gaps))], 5) if abs_gaps else None,
        "note": ("direction * (next_open - decision_close) / stop_dist. POSITIVE means the "
                 "next open would have been better for the trade, i.e. entering at the close "
                 "is DISADVANTAGED. Reported signed because the absolute value overstates "
                 "the bias by two orders of magnitude and in the flattering direction."),
    }
    print(f"  entry-convention gap: signed mean {entry_gap['mean_signed_R']} R "
          f"(|gap| mean {entry_gap['mean_abs_R']} R)")
    print(f"  duplicates removed: {n_dupes}")

    meta = {
        "maxbars": maxbars,
        "live_registry_size": len(active),
        "market_expansion_sleeves_live": mx,
        "n_candidates": len(cands),
        "n_duplicate_candidates_removed": n_dupes,
        "n_trades_by_sleeve": {s: len(v) for s, v in sorted(trades.items())},
        "sleeves_producing_no_trade": silent,
        "entry_convention_gap": entry_gap,
        "skips": dict(skipped),
        "grid": {"n_closes": len(grid), "first": str(grid[0]), "last": str(grid[-1])},
        "median_hold_bars_d1": {s: (statistics.median(
            [t.features["exit_bar_index_offset"] for t in v]) if v else None)
            for s, v in trades.items()},
    }
    return trades, mx, meta


def main(maxbars: int = 80) -> dict:
    trades, mx, meta = build_trades(maxbars)

    # ---- run the gate under each admission option ---------------------------------------
    from src.research_infra.walkforward.options import OPTIONS  # noqa: PLC0415

    runs = {}
    for name, spec in OPTIONS.items():
        spec = spec.with_(spec_id=f"{spec.spec_id}_mxpilot_maxbars{maxbars}")
        res_g = run_gate(trades, spec)
        rows = []
        for s, v in sorted(res_g.verdicts.items()):
            rows.append({
                "sleeve": s, "verdict": v.verdict.value, "n_trades": v.n_trades,
                "pooled_oos_mean_r": v.pooled_oos_mean_r, "p_raw": v.p_raw,
                "q_value": v.q_value,
                "oos_positive_fold_frac": v.gates.get("stability", {}).get("oos_positive_fold_frac"),
                "coverage_frac": v.gates.get("cost_coverage", {}).get("coverage_frac"),
                "n_folds_evaluable": v.gates.get("sample", {}).get("n_folds_evaluable"),
                "median_hold_bars": None,
                "first_reason": (v.reasons[0] if v.reasons else None),
            })
        runs[name] = {
            "spec_sha256": spec.seal(), "spec_id": spec.spec_id,
            "admitted": res_g.admitted, "rejected": res_g.rejected,
            "not_evaluable": res_g.not_evaluable, "rows": rows,
            "family": {k: v for k, v in res_g.family.items() if k != "n_trials_basis"},
        }
        print(f"\n--- {name} ---")
        print(f"{'sleeve':40s} {'verdict':14s} {'n':>5s} {'meanR':>9s} {'q':>9s} {'pos':>5s}")
        for r in rows:
            m = "-" if r["pooled_oos_mean_r"] is None else f"{r['pooled_oos_mean_r']:.5f}"
            q = "-" if r["q_value"] is None else f"{r['q_value']:.4g}"
            pf = "-" if r["oos_positive_fold_frac"] is None else f"{r['oos_positive_fold_frac']:.0%}"
            print(f"{r['sleeve']:40s} {r['verdict']:14s} {r['n_trades']:5d} {m:>9s} {q:>9s} {pf:>5s}")
        print(f"  ADMIT({len(res_g.admitted)}): {res_g.admitted}")

    out = {
        "schema": "gtos.walkforward.mx_pilot.v1",
        "generated_by": "docs/audits/fable5-vision-audit-20260725/phase5/receipts/w_mx_pilot.py",
        **meta,
        "runs": runs,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return out


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main(maxbars=int(sys.argv[1]) if len(sys.argv) > 1 else 80)
