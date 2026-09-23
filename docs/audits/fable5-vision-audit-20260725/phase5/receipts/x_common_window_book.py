"""The merged book on the window where every armed sleeve actually has data.

    python3 docs/audits/fable5-vision-audit-20260725/phase5/receipts/x_common_window_book.py

WHY THE FULL-ARCHIVE BOOK IS NOT THE RIGHT COMPARISON, MEASURED
----------------------------------------------------------------
`x_estate_walk.py` runs the merged book over the whole H4 archive. On the armed-4
composition that produced 66 placements — **57 `metals_core`, 9 `sub_xvol_pullback`, and
ZERO `crypto`, ZERO `energy_agri`** — and the account reached the FTMO max-drawdown entry
block on **2014-11-12**, after which no sleeve ever entered again.

The reason is data, not economics: `metals_core`'s H4 history starts 2004-06 and
`sub_xvol_pullback`'s carriers not much later, while `crypto`'s BTCUSD H4 starts **2017-06**
and `energy_agri`'s USOIL/UKOIL H4 start **2020-12**. So on the full archive the book spends
its whole risk budget on one sleeve, hits the wall, and dies a decade before two of its four
members exist. Its leave-one-out deltas for `crypto` and `energy_agri` are therefore exactly
0.0 — **vacuous by construction**, not a finding about those sleeves.

THE WINDOW IS SET BY AVAILABILITY, NOT BY RESULTS
--------------------------------------------------
The common window starts at the first date on which every sleeve in the widest composition
has bars — computed from the trade records, not chosen after seeing returns. That is the
same leak-free criterion `GateSpec.fold_rule` uses: "boundaries derive mechanically from the
sleeve's own DATA AVAILABILITY span, never from its results ... availability is a property
of the archive, not of outcomes."

WHAT THIS IS NOT
----------------
It is not a forecast and not a backtest of the funded account. A 100k account walking 2021
to 2026 at the live 2.0% ceiling dial is a statement about the sleeve mix under the live
governor, on trades labelled with a cost model measured over 37 days in 2026 and charged to
the whole window. Every number here is optimistic by that unmeasured amount.
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.research_infra.walkforward import TradeRecord  # noqa: E402
from src.research_infra.walkforward.book_replay import (  # noqa: E402
    BookConfig,
    BookTrade,
    book_daily_series,
    book_stats,
    replay_book,
)
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.panel import price_trades  # noqa: E402

IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase5/receipts/X_ESTATE_TRADES.json.gz"
OUT = REPO / "docs/audits/fable5-vision-audit-20260725/phase5/receipts/X_COMMON_WINDOW_BOOK.json"

ARMED4 = ("metals_core", "crypto", "energy_agri", "sub_xvol_pullback")
LIVE_ARMED3 = ("metals_core", "crypto", "energy_agri")
CORE8 = ("metals_core", "metals_softband", "crypto", "energy_agri", "idxrev",
         "metals_ob_micro", "fx_jpy", "fx_jpy_ny")


def main() -> dict:
    with gzip.open(IN, "rt") as fh:
        raw = json.load(fh)
    spec = OPTIONS["B_balanced"].with_(spec_id="x_common_window_cost")
    rt = dict(yaml.safe_load(open(REPO / "config/agent_config.yaml"))
              .get("gtos_vnext_runtime") or {})
    rt["ultimate_book_include_clean3"] = True

    priced_by_sleeve: dict[str, list[BookTrade]] = {}
    for sleeve, rows in raw["trades"].items():
        if not rows:
            continue
        recs = [TradeRecord(
            sleeve=r["sleeve"], symbol=r["symbol"],
            entry_utc=dt.datetime.fromisoformat(r["entry_utc"]),
            exit_utc=dt.datetime.fromisoformat(r["exit_utc"]),
            direction=int(r["direction"]),
            sl_distance_price=float(r["sl_distance_price"]),
            entry_price=float(r["entry_price"]), r_gross=float(r["r_gross"]),
            features={"symbol_canonical": r["symbol_canonical"],
                      "decision_day": r["decision_day"],
                      "decision_bar_iso": r["decision_bar_iso"],
                      "timeframe": r["timeframe"]}) for r in rows]
        priced, _cov = price_trades(recs, spec)
        keep = []
        for p in priced:
            if p.status != "priced" or p.r_net is None:
                continue
            t = p.trade
            keep.append(BookTrade(
                sleeve=t.sleeve, symbol=t.symbol,
                symbol_canonical=t.features["symbol_canonical"],
                entry_utc=t.entry_utc, exit_utc=t.exit_utc, direction=t.direction,
                stop_dist=t.sl_distance_price, entry_price=t.entry_price,
                r_net=float(p.r_net), decision_day=str(t.features["decision_day"]),
                decision_bar_iso=str(t.features["decision_bar_iso"]),
                timeframe=t.features["timeframe"]))
        if keep:
            priced_by_sleeve[sleeve] = keep

    firsts = {s: min(t.entry_utc for t in v) for s, v in priced_by_sleeve.items()}
    start = max(firsts[s] for s in ARMED4 if s in firsts)
    # floor to the month start so the boundary is a calendar fact, not a trade's timestamp
    start = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    print("first priced trade per armed sleeve:")
    for s in ARMED4:
        print(f"   {s:20s} {firsts.get(s)}")
    print(f"common window starts {start.date()} (set by availability, not by results)\n")

    comps = {
        "live_armed3": [s for s in LIVE_ARMED3 if s in priced_by_sleeve],
        "armed4_intended": [s for s in ARMED4 if s in priced_by_sleeve],
        "armed4_minus_metals_core": [s for s in ARMED4
                                     if s in priced_by_sleeve and s != "metals_core"],
        "core8_live": [s for s in CORE8 if s in priced_by_sleeve],
        "armed4_plus_mx12": sorted({s for s in ARMED4 if s in priced_by_sleeve}
                                   | {s for s in priced_by_sleeve if s.startswith("mx_")}),
        "everything_generatable": sorted(priced_by_sleeve),
    }
    runs: dict[str, dict] = {}
    daily: dict[str, dict] = {}
    for label, sleeves in comps.items():
        if not sleeves:
            continue
        flat = [t for s in sleeves for t in priced_by_sleeve[s]
                if t.entry_utc >= start]
        if not flat:
            continue
        res = replay_book(flat, BookConfig(runtime=rt, sleeves=tuple(sleeves), label=label))
        st = book_stats(res)
        by_sleeve: dict[str, int] = {}
        for p in res.placed:
            by_sleeve[p["sleeve"]] = by_sleeve.get(p["sleeve"], 0) + 1
        halted = sum(v for k, v in res.rejections.items() if "max_dd" in k)
        runs[label] = {
            "sleeves": sleeves, "stats": st,
            "placed_by_sleeve": dict(sorted(by_sleeve.items(), key=lambda kv: -kv[1])),
            "rejections": dict(sorted(res.rejections.items(), key=lambda kv: -kv[1])),
            "n_candidates_in_window": len(flat),
            "halted_on_max_dd_entry_block": halted > 0,
            "n_cycles_blocked_by_max_dd": halted,
            "daily_series_days": len(book_daily_series(res)),
        }
        daily[label] = book_daily_series(res)
        print(f"{label:28s} n={st['n_placed']:4d} sumR={st['sum_r_net']:8.2f} "
              f"ret={st['total_return_pct']:8.2f}% DD={st['max_drawdown_pct']:6.2f}% "
              f"sharpe={st['book_daily_sharpe']:+.4f} last={st['last'][:10]} "
              f"halt={'YES' if halted else 'no'} {by_sleeve}")

    # Every pairwise claim carries an interval. An adversarial refuter measured that picking
    # the best of six compositions buys +0.527 annualised Sharpe of pure winner's curse on a
    # zero-edge estate, so a ranking without a null is not a finding.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from x_estate_walk import paired_block_ci  # noqa: PLC0415

    base_label = "armed4_intended"
    pairwise = {}
    if base_label in daily:
        for label, series in daily.items():
            if label == base_label:
                continue
            pairwise[label] = paired_block_ci(series, daily[base_label])
        print(f"\npaired block-bootstrap CI on the daily-Sharpe difference vs {base_label}:")
        for label, ci in pairwise.items():
            print(f"  {label:28s} dSharpe={ci.get('observed_sharpe_delta')} "
                  f"CI={ci.get('ci_sharpe_delta')} "
                  f"significant={ci.get('sharpe_delta_significant')}")

    out = {
        "schema": "gtos.walkforward.common_window_book.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase5/receipts/"
                         "x_common_window_book.py"),
        "window_start": start.isoformat(),
        "window_basis": ("the first month in which EVERY armed sleeve has a priced trade. "
                         "Set by data availability, not by results — the same leak-free "
                         "criterion GateSpec.fold_rule uses."),
        "first_priced_trade_by_sleeve": {s: str(v) for s, v in sorted(firsts.items())},
        "runs": runs,
        "pairwise_vs_armed4_intended": pairwise,
        "pairwise_note": ("paired day-block bootstrap on the book daily-Sharpe difference. "
                          "Best-of-N composition ranking buys ~+0.53 annualised Sharpe of "
                          "winner's curse on a zero-edge estate (refuter-measured), so a "
                          "ranking without an interval is not reportable."),
        "cost_look_ahead": ("spread measured 2026-06-18..2026-07-24 and charged flat; "
                            "spreads compressed, so every number here is optimistic by an "
                            "unmeasured amount"),
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return out


if __name__ == "__main__":
    main()
