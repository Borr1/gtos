"""Prompt blindspot smoke test.

Approach:
1. Read MSO Pydantic schema to enumerate ALL fields.
2. Read the prompt's rendering functions (_format_tf, build_static_context,
   build_dynamic_context) to enumerate every key actually sent to the AI.
3. Compute the difference.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
PROMPT_PATH = ROOT / "src/prompts/primary_analyzer_prompt.py"
MSO_PATH = ROOT / "src/models/market_state_models.py"

# ── Fields the prompt actually renders (by manual reading) ──
RENDERED_BY_PROMPT = {
    # top-level MSO
    "timestamp_utc": "yes — via candle_time",
    "timeframes": "D1 + H4 (static_context), H1 + M15 (dynamic_context)",
    "session_levels": {
        "asian_high": "yes (static)",
        "asian_low": "yes (static)",
        "pdh": "yes (static)",
        "pdl": "yes (static)",
        "session_high": "yes (dynamic)",
        "session_low": "yes (dynamic)",
        "london_high": "yes (both static + dynamic)",
        "london_low": "yes (both static + dynamic)",
    },
    "equal_highs": "NO — not rendered anywhere",
    "equal_lows": "NO — not rendered anywhere",
    "liquidity_pools": "PARTIAL — static_context renders max 10 sorted by proximity to PDH/PDL midpoint",
    "detected_sweeps": "yes (dynamic_context, max 5)",
    "spread_cents": "NO — not rendered",
    "high_impact_events": "NO — not rendered",
    "data_quality": "PARTIAL — only all_TFs + spread_ok",
    # Per-timeframe fields
    "timeframe.swings": "PARTIAL — only M15 recent (last 10); D1/H4/H1 swings NOT rendered",
    "timeframe.structure.direction": "yes",
    "timeframe.structure.protected_swing": "yes",
    "timeframe.structure.swing_sequence": "NO — not rendered",
    "timeframe.structure.hh_count": "NO — not rendered",
    "timeframe.structure.hl_count": "NO — not rendered",
    "timeframe.structure.lh_count": "NO — not rendered",
    "timeframe.structure.ll_count": "NO — not rendered",
    "timeframe.structure_events": "PARTIAL — only last 5",
    "timeframe.order_blocks": "PARTIAL — only last 5 unmitigated",
    "timeframe.breaker_blocks": "PARTIAL — only last 5 unretested",
    "timeframe.fair_value_gaps": "PARTIAL — only last 5 unfilled",
    "timeframe.premium_discount.equilibrium_50": "yes",
    "timeframe.premium_discount.fib_62": "yes",
    "timeframe.premium_discount.fib_79": "yes",
    "timeframe.premium_discount.impulse_low": "NO — not rendered",
    "timeframe.premium_discount.impulse_high": "NO — not rendered",
    "timeframe.premium_discount.discount_zone": "NO — not rendered",
    "timeframe.premium_discount.premium_zone": "NO — not rendered",
    "timeframe.premium_discount.ote_zone": "NO — not rendered",
    "timeframe.avg_candle_body": "yes",
    "timeframe.atr_14": "yes",
    "timeframe.clv_current": "yes",
    "timeframe.clv_avg_5": "yes",
    "timeframe.bvc_buy_fraction": "yes",
    "timeframe.net_flow_5": "yes",
    "timeframe.atr_session": "yes (XAUUSD M15 only)",
    "timeframe.session_vol_ratio": "yes",
    # Per-OB fields
    "ob.type": "yes",
    "ob.high": "yes",
    "ob.low": "yes",
    "ob.open": "yes (body=open-close)",
    "ob.close": "yes",
    "ob.causing_event_type": "yes",
    "ob.touch_count": "yes",
    "ob.formation_time": "yes",
    "ob.formation_index": "NO — not rendered",
    "ob.causing_bos_index": "NO — not rendered",
    "ob.mitigated": "filtered out (unmitigated only)",
    # Per-Sweep fields
    "sweep.pool.type": "yes",
    "sweep.pool.price": "NO — not rendered",
    "sweep.pool.side": "NO — not rendered",
    "sweep.sweep_type": "yes",
    "sweep.wick_extreme": "yes",
    "sweep.body_close": "yes",
    "sweep.time": "yes",
    "sweep.candle_index": "NO — not rendered",
}


def main():
    # Enumerate every top-level key in the output
    omitted = []
    partial = []
    rendered = []
    for k, v in RENDERED_BY_PROMPT.items():
        if isinstance(v, dict):
            for sk, sv in v.items():
                if "NO" in sv:
                    omitted.append(f"{k}.{sk}: {sv}")
                elif "PARTIAL" in sv:
                    partial.append(f"{k}.{sk}: {sv}")
                else:
                    rendered.append(f"{k}.{sk}: {sv}")
        else:
            if "NO" in v:
                omitted.append(f"{k}: {v}")
            elif "PARTIAL" in v:
                partial.append(f"{k}: {v}")
            else:
                rendered.append(f"{k}: {v}")

    print(f"=== RENDERED FULLY ({len(rendered)}) ===")
    for r in rendered:
        print(f"  {r}")
    print(f"\n=== PARTIAL / TRUNCATED ({len(partial)}) ===")
    for r in partial:
        print(f"  {r}")
    print(f"\n=== OMITTED ENTIRELY ({len(omitted)}) ===")
    for r in omitted:
        print(f"  {r}")

    # Prompt-side bias-inducing language (scan prompt text)
    prompt_src = PROMPT_PATH.read_text(encoding="utf-8")
    # Look for leading-question or anchoring language
    print("\n=== Structural prompt hints (sample phrases) ===")
    for pat in [
        r"CANDIDATE",
        r"NO_TRADE",
        r"Do NOT",
        r"over-reject",
        r"C-gate",
        r"0\.0",
    ]:
        count = len(re.findall(pat, prompt_src))
        print(f"  {pat!r}: {count}")


if __name__ == "__main__":
    main()
