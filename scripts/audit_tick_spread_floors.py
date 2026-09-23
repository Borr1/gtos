#!/usr/bin/env python3
"""F40: audit the deployed ``TICK_SPREAD_FLOOR_R`` table against measured spread.

`admission.py:73-84` holds 9 per-symbol round-trip spread floors in R, derived from
`KB7_TICK_TRUTH_RESULT`'s `mean_entry_spread_R`. `GATE_G1B_RECEIPT.md` §5.2c found them
never enforced, covering 22.2% of live symbols, and understated (XAUUSD 3.47x, BTCUSD
77.8x). That comparison used a one-day tick read; this one uses the full archive
(263.9M ticks) and, where the symbol traded live, the actual median stop distance from
the 300 W7-era rows -- so the R conversion uses the same denominator the floors claim.

It also reports the symbols the table *omits*, which is the larger half of F40: GBPJPY
carried 23 live trades and the worst measured spread of any instrument, and has no floor.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.components.ultimate_book.admission import (  # noqa: E402
    TICK_SPREAD_FLOOR_R,
    TICK_SPREAD_FLOOR_UNTRADEABLE_R,
)
from src.costs import load_broker_true_costs  # noqa: E402

W7_ROWS = REPO / "docs/audits/fable5-vision-audit-20260725/phase1/w7_forensics/LIVE_TRADE_ROWS.jsonl"

# admission.py's table uses the replay's canonical tickers; the archive uses each
# broker's own. Only the names that differ need mapping.
FLOOR_TO_BROKER = {
    "USOIL_cash": {"FTMO": "USOIL_cash", "redacted_account": "USOUSD"},
    "UKOIL_cash": {"FTMO": "UKOIL_cash", "redacted_account": "UKOUSD"},
}


def live_median_stop(rows: list[dict]) -> dict:
    by: dict = {}
    for r in rows:
        sym = r.get("canonical_symbol") or r.get("broker_symbol")
        sl = r.get("risk_distance_price")
        if sym and sl:
            by.setdefault(sym, []).append(float(sl))
    return {k: statistics.median(v) for k, v in by.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", type=Path, default=None)
    args = ap.parse_args()

    truth = load_broker_true_costs()
    rows = [json.loads(x) for x in W7_ROWS.read_text("utf-8-sig").splitlines() if x.strip()]
    stops = live_median_stop(rows)
    live_syms = {r.get("canonical_symbol") or r.get("broker_symbol") for r in rows if r.get("stack_era") == "w7_book"}

    findings = []
    print("=== deployed floors vs measured spread ===")
    print(f"{'symbol':<12} {'floor_R':>9} {'acct':<11} {'p50 price':>10} {'stop':>10} "
          f"{'measured_R':>11} {'ratio':>8}")
    for sym, floor in sorted(TICK_SPREAD_FLOOR_R.items()):
        found = False
        for acct in truth.accounts:
            broker_sym = FLOOR_TO_BROKER.get(sym, {}).get(acct, sym)
            try:
                rec = truth.instrument(acct, broker_sym)
            except Exception:
                continue
            sp = rec.get("spread_price")
            if not sp:
                continue
            found = True
            p50 = sp["percentiles"]["p50"]
            stop = stops.get(sym)
            if stop:
                measured_r = p50 / stop
                ratio = measured_r / floor if floor else float("inf")
                print(f"{sym:<12} {floor:>9.4f} {acct:<11} {p50:>10.5f} {stop:>10.4f} "
                      f"{measured_r:>11.4f} {ratio:>7.2f}x")
            else:
                measured_r = ratio = None
                print(f"{sym:<12} {floor:>9.4f} {acct:<11} {p50:>10.5f} {'no live stop':>10} "
                      f"{'-':>11} {'-':>8}")
            findings.append({
                "symbol": sym, "account": acct, "floor_r": floor,
                "measured_spread_price_p50": p50, "live_median_stop_price": stop,
                "measured_spread_r": measured_r, "understatement_ratio": ratio,
            })
        if not found:
            print(f"{sym:<12} {floor:>9.4f} {'-- no tick coverage on either account --':<52}")
            findings.append({"symbol": sym, "floor_r": floor, "tick_coverage": False})

    # The omissions -- the larger half of F40.
    omitted = []
    print("\n=== live-traded symbols with NO floor ===")
    for acct in truth.accounts:
        for sym in truth.symbols(acct):
            rec = truth.instrument(acct, sym)
            canon = sym
            if canon in TICK_SPREAD_FLOOR_R or not rec.get("spread_price"):
                continue
            if not rec.get("traded_in_export_window"):
                continue
            sp = rec["spread_price"]["percentiles"]["p50"]
            stop = stops.get(sym)
            r = (sp / stop) if stop else None
            omitted.append({"account": acct, "symbol": sym, "spread_price_p50": sp,
                            "live_median_stop_price": stop, "spread_r": r})
    for o in sorted(omitted, key=lambda x: -(x["spread_r"] or 0))[:12]:
        r = f"{o['spread_r']:.4f}" if o["spread_r"] else "n/a"
        print(f"  {o['account']:<11} {o['symbol']:<12} p50={o['spread_price_p50']:<10.5f} "
              f"spread_R={r}")

    covered = sum(1 for s in live_syms if s in TICK_SPREAD_FLOOR_R)
    print(f"\nlive W7 symbols with a floor: {covered}/{len(live_syms)} "
          f"({100*covered/max(1,len(live_syms)):.1f}%)")
    print(f"floor symbols with no tick coverage: "
          f"{sum(1 for f in findings if f.get('tick_coverage') is False)}")
    print(f"untradeable threshold: {TICK_SPREAD_FLOOR_UNTRADEABLE_R}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({
            "schema": "gtos.broker_truth.tick_spread_floor_audit.v1",
            "deployed_table": dict(TICK_SPREAD_FLOOR_R),
            "untradeable_threshold_r": TICK_SPREAD_FLOOR_UNTRADEABLE_R,
            "floor_vs_measured": findings,
            "live_traded_without_floor": omitted,
            "live_w7_symbol_coverage": {"with_floor": covered, "total": len(live_syms)},
        }, indent=1, sort_keys=True, default=str))
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
