"""Variant C Partial Close — Historical Backtest Replay (Path A).

Replays historical batch trades to evaluate the hypothetical Variant C
outcome (33% partial close at +1.0R with BE stop on remainder).

Zero API cost. Uses existing batch datasets that contain per-trade
r_multiple + mfe_r + optional r_path. Writes same-schema output as the
live `partial_close_shadow_logger` so results merge cleanly when live
data finally accumulates.

Trigger: mfe_r >= 1.0 (price touched +1R intra-trade).

After trigger, for the remaining 67%:
  - If r_path available: walk bars after the +1R touch; flag reversal
    past entry (r <= 0) -> remaining_r = 0 (BE stop).
  - If r_path NOT available: approximate from final r_multiple.
      Winners (r_multiple > 0): remaining_r = r_multiple (assumes no
      reversal past entry — typical for trades that closed favorable).
      Losers (r_multiple <= 0): remaining_r = 0 (BE stop; price must
      have passed entry on the way from +1R to SL).

Decision gate (after running):
  - n_triggered >= 30
  - Wilcoxon signed-rank on delta_r (variant_c_r - actual_r) with p < 0.05
  - Positive cumulative delta_r -> promote
  - Negative / non-significant -> kill or keep shadow-logging

Usage:
  python scripts/variant_c_replay.py                            # defaults
  python scripts/variant_c_replay.py --trades <path> [--out <path>]
  python scripts/variant_c_replay.py --trades a.json b.json     # multiple
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

PARTIAL_CLOSE_FRACTION = 0.33
TRIGGER_R = 1.0

DEFAULT_TRADES = [
    "knowledge_base_backtest/analysis/unified_trades_v2_20260331.json",
    "knowledge_base_backtest/analysis/phase1_all_trades_merged.json",
]
DEFAULT_OUT = "shadow_logs/partial_close_backtest.jsonl"


def _compute_r(price: float, entry: float, sl: float, direction: str) -> float:
    sl_dist = abs(entry - sl)
    if sl_dist <= 0:
        return 0.0
    if direction == "LONG":
        return (price - entry) / sl_dist
    return (entry - price) / sl_dist


def _walk_r_path_for_reversal(r_path: list, after_index: int) -> bool:
    """After the +1R trigger at after_index, did price reverse past entry (r <= 0)?"""
    for bar in r_path[after_index + 1 :]:
        r_low = bar.get("r_at_low")
        r_close = bar.get("r_at_close")
        for r in (r_low, r_close):
            if r is not None and r <= 0:
                return True
    return False


def _find_trigger_index(r_path: list) -> int | None:
    for i, bar in enumerate(r_path):
        r_high = bar.get("r_at_high")
        r_close = bar.get("r_at_close")
        for r in (r_high, r_close):
            if r is not None and r >= TRIGGER_R:
                return i
    return None


def compute_variant_c(trade: dict) -> dict | None:
    """Returns a variant-c entry for this trade, or None if no trigger."""
    mfe_r = trade.get("mfe_r")
    r_mult = trade.get("r_multiple")
    direction = trade.get("direction")
    entry = trade.get("entry_price")
    sl = trade.get("stop_loss")
    r_path = trade.get("r_path") or []

    if mfe_r is None or r_mult is None or direction not in ("LONG", "SHORT"):
        return None

    triggered = False
    reversed_past_entry: bool | None = None
    mode = "approx"

    if r_path:
        trigger_idx = _find_trigger_index(r_path)
        if trigger_idx is not None:
            triggered = True
            reversed_past_entry = _walk_r_path_for_reversal(r_path, trigger_idx)
            mode = "exact_r_path"
    if not triggered and mfe_r >= TRIGGER_R:
        triggered = True
        if reversed_past_entry is None:
            reversed_past_entry = r_mult <= 0

    if not triggered:
        return None

    if reversed_past_entry:
        remaining_r = 0.0
    else:
        remaining_r = float(r_mult) if r_mult is not None else 0.0

    variant_c_r = PARTIAL_CLOSE_FRACTION * TRIGGER_R + (1.0 - PARTIAL_CLOSE_FRACTION) * remaining_r
    delta_r = variant_c_r - float(r_mult)

    trade_id = trade.get("trade_id") or f"{trade.get('symbol', 'UNK')}_{trade.get('date', '?')}_{trade.get('candle_time', '?')}"

    return {
        "trade_id": trade_id,
        "mode": mode,
        "direction": direction,
        "entry_price": entry,
        "stop_loss": sl,
        "take_profit_1": trade.get("take_profit_1"),
        "actual_r_multiple": round(float(r_mult), 4),
        "mfe_r": round(float(mfe_r), 4),
        "mae_r": round(float(trade.get("mae_r") or 0), 4),
        "reversed_past_entry": bool(reversed_past_entry),
        "partial_close_r": TRIGGER_R,
        "partial_close_fraction": PARTIAL_CLOSE_FRACTION,
        "remaining_r": round(remaining_r, 4),
        "variant_c_blended_r": round(variant_c_r, 4),
        "delta_r": round(delta_r, 4),
        "variant_c_better": delta_r > 0,
        "source": "historical_replay",
        "date": trade.get("date"),
        "kill_zone": trade.get("kill_zone"),
        "outcome": trade.get("outcome"),
        "exit_substate": trade.get("exit_substate"),
    }


def load_trades(paths: Iterable[str]) -> list[dict]:
    trades: list[dict] = []
    seen_ids: set[str] = set()
    for p in paths:
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"[warn] not found: {p}", file=sys.stderr)
            continue
        if not isinstance(data, list):
            continue
        for t in data:
            if not isinstance(t, dict):
                continue
            tid = t.get("trade_id") or f"{t.get('date')}_{t.get('kill_zone')}_{t.get('candle_time')}_{t.get('entry_price')}"
            if tid in seen_ids:
                continue
            seen_ids.add(tid)
            trades.append(t)
    return trades


def wilcoxon_signed_rank(deltas: list[float]) -> tuple[float, float]:
    """Return (W, p) — two-sided Wilcoxon signed-rank test via scipy."""
    try:
        from scipy.stats import wilcoxon
    except ImportError:
        return (float("nan"), float("nan"))
    nonzero = [d for d in deltas if d != 0]
    if len(nonzero) < 6:
        return (float("nan"), float("nan"))
    res = wilcoxon(nonzero, alternative="two-sided", zero_method="wilcox")
    return (float(res.statistic), float(res.pvalue))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", nargs="+", default=DEFAULT_TRADES,
                    help="Path(s) to trade JSON list(s). Defaults to unified_trades_v2 + phase1_merged.")
    ap.add_argument("--out", default=DEFAULT_OUT,
                    help=f"Output JSONL path. Default: {DEFAULT_OUT}")
    args = ap.parse_args()

    trades = load_trades(args.trades)
    print(f"loaded {len(trades)} unique trades from {len(args.trades)} file(s)")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()

    results: list[dict] = []
    for t in trades:
        entry = compute_variant_c(t)
        if entry is None:
            continue
        results.append(entry)
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    if not results:
        print("No trades triggered — nothing to evaluate.")
        return 0

    n = len(results)
    n_exact = sum(1 for r in results if r["mode"] == "exact_r_path")
    n_approx = n - n_exact
    deltas = [r["delta_r"] for r in results]
    actual_rs = [r["actual_r_multiple"] for r in results]
    variant_rs = [r["variant_c_blended_r"] for r in results]
    better = sum(1 for r in results if r["variant_c_better"])
    reversed_count = sum(1 for r in results if r["reversed_past_entry"])

    cum_delta = sum(deltas)
    mean_delta = cum_delta / n
    stat, pval = wilcoxon_signed_rank(deltas)

    actual_exp = sum(actual_rs) / n
    variant_exp = sum(variant_rs) / n

    print()
    print(f"=== Variant C historical replay results ===")
    print(f"Output: {out_path}")
    print(f"Triggered trades (+1R touched): {n}")
    print(f"  exact (r_path available):     {n_exact}")
    print(f"  approx (mfe_r only):          {n_approx}")
    print(f"Reversed past entry (BE stop):  {reversed_count}  ({100*reversed_count/n:.1f}%)")
    print(f"Variant C better on delta_r:    {better}/{n}  ({100*better/n:.1f}%)")
    print()
    print(f"Expectancy (R/trade):")
    print(f"  actual:     {actual_exp:+.4f}")
    print(f"  variant C:  {variant_exp:+.4f}")
    print(f"  delta:      {variant_exp - actual_exp:+.4f}")
    print()
    print(f"Cumulative delta_r:  {cum_delta:+.4f}")
    print(f"Mean delta_r:        {mean_delta:+.4f}")
    print(f"Wilcoxon signed-rank (two-sided): W={stat:.2f}, p={pval:.4g}")
    print()
    n_gate = n >= 30
    sig_gate = pval < 0.05 if pval == pval else False  # NaN check
    if n_gate and sig_gate and cum_delta > 0:
        verdict = "PROMOTE: significant positive delta"
    elif n_gate and sig_gate and cum_delta < 0:
        verdict = "KILL: significant negative delta"
    elif not n_gate:
        verdict = f"INCONCLUSIVE: n={n} < 30, need more triggered trades"
    else:
        verdict = "INCONCLUSIVE: p >= 0.05, no significant difference"
    print(f"Verdict: {verdict}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
