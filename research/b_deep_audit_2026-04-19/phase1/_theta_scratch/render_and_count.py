"""Agent θ — render the PA system prompt + 5 user messages across 5 diverse MSOs
and estimate token budget via char-length heuristic.

No AI calls. No writes to prompts/ or src/. Pure analysis.

Usage:
    python render_and_count.py

Outputs:
    - samples/{symbol}__system.txt    (rendered system message per instrument)
    - samples/{symbol}__user.txt      (rendered user message per instrument)
    - token_counts.json               (aggregate table)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Make the project importable from research/b_deep_audit_2026-04-19/phase1/_theta_scratch/
REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from src.prompts import primary_analyzer_prompt as pap  # noqa: E402
from src.models.market_state_models import MarketStateObject  # noqa: E402

OUT_DIR = Path(__file__).parent / "samples"
OUT_DIR.mkdir(exist_ok=True)

# 5 diverse instruments covering the precision spectrum
# (matches config/agent_config.yaml per-instrument price_format)
INSTRUMENTS = [
    ("XAUUSD",    ".2f",  {"symbol": "XAUUSD",    "kill_zones": {"london": {"start_utc": "07:00", "end_utc": "10:30"}, "ny":     {"start_utc": "13:00", "end_utc": "17:00"}}, "sl_absolute_min": 5.0}),
    ("US30_cash", ".2f",  {"symbol": "US30_cash", "kill_zones": {"london": {"start_utc": "08:00", "end_utc": "10:30"}, "ny":     {"start_utc": "13:30", "end_utc": "16:00"}}, "sl_absolute_min": 20.0}),
    ("USDJPY",    ".3f",  {"symbol": "USDJPY",    "kill_zones": {"tokyo":  {"start_utc": "00:00", "end_utc": "03:00"}, "london": {"start_utc": "07:00", "end_utc": "09:30"}, "ny": {"start_utc": "13:00", "end_utc": "15:30"}}, "sl_absolute_min": 0.085}),
    ("GBPJPY",    ".3f",  {"symbol": "GBPJPY",    "kill_zones": {"tokyo":  {"start_utc": "00:00", "end_utc": "03:00"}, "london": {"start_utc": "07:00", "end_utc": "09:30"}, "ny": {"start_utc": "13:00", "end_utc": "15:30"}}, "sl_absolute_min": 0.14}),
    ("EURUSD",    ".5f",  {"symbol": "EURUSD",    "kill_zones": {"london": {"start_utc": "07:00", "end_utc": "12:00"}, "ny":     {"start_utc": "13:00", "end_utc": "15:30"}}, "sl_absolute_min": 0.0003}),
]

MSO_PATH = REPO_ROOT / "knowledge_base" / "pipeline_state" / "02_market_state.json"


def rough_tokens(s: str) -> int:
    """Claude tokenization is ~3.3-3.8 chars/token for English+numeric."""
    return len(s) // 4  # conservative lower bound (actual is usually 10-20% higher)


def rough_tokens_hi(s: str) -> int:
    """Upper estimate for dense numeric content (~3 char/tok)."""
    return len(s) // 3


def load_mso() -> dict:
    with MSO_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def render_for_instrument(symbol: str, price_fmt: str, market_cfg: dict, mso: dict) -> tuple[str, str]:
    """Render both system and user prompts for a given instrument."""
    # Build config the way build_prompt() does
    config = {
        "market": {
            "symbol": market_cfg["symbol"],
            "kill_zones": market_cfg["kill_zones"],
        },
        "risk": {
            "sl_absolute_min": market_cfg["sl_absolute_min"],
        },
        "prompt": {"price_format": price_fmt},
    }

    # Apply price format (the production call-site does this in primary_analyzer.py:194)
    pap.set_price_format(price_fmt)

    # System prompt (instrument-specific render)
    system_text = pap.build_system_prompt(config)

    # Static context (D1/H4/session) + user message (dynamic H1/M15)
    # Need to coerce dict-based MSO to the pydantic model for model_dump compatibility
    try:
        mso_obj = MarketStateObject.model_validate(mso)
        mso_input = mso_obj
    except Exception as e:
        # fall back to dict path; build_static_context handles both
        print(f"[warn] MarketStateObject validation failed: {type(e).__name__}: {str(e)[:120]}")
        mso_input = mso

    static_ctx = pap.build_static_context(mso_input)
    combined_system = system_text + "\n\n## Static Context (D1/H4/Session)\n" + static_ctx

    user_msg = pap.build_user_message(
        mso_input,
        kb_context={"layer1": {}, "layer2": {}, "layer3": []},
        current_time="2026-04-17T15:15:00Z",
        kill_zone="ny",
        session_memory="",
        cross_instrument_context="",
        additional_context="",
    )

    return combined_system, user_msg


def main():
    print(f"REPO_ROOT: {REPO_ROOT}")
    print(f"MSO_PATH: {MSO_PATH}  ({MSO_PATH.stat().st_size:,} bytes)")
    mso = load_mso()
    print(f"MSO keys: {list(mso.keys())}\n")

    results: dict[str, Any] = {}

    for symbol, fmt, market_cfg in INSTRUMENTS:
        try:
            system_text, user_msg = render_for_instrument(symbol, fmt, market_cfg, mso)
        except Exception as e:
            print(f"[FAIL] {symbol}: {type(e).__name__}: {e}")
            results[symbol] = {"error": f"{type(e).__name__}: {e}"}
            continue

        system_path = OUT_DIR / f"{symbol}__system.txt"
        user_path = OUT_DIR / f"{symbol}__user.txt"
        system_path.write_text(system_text, encoding="utf-8")
        user_path.write_text(user_msg, encoding="utf-8")

        sys_chars = len(system_text)
        user_chars = len(user_msg)
        total_chars = sys_chars + user_chars
        results[symbol] = {
            "price_format": fmt,
            "system_chars": sys_chars,
            "user_chars": user_chars,
            "total_chars": total_chars,
            "system_tokens_lo": rough_tokens(system_text),
            "system_tokens_hi": rough_tokens_hi(system_text),
            "user_tokens_lo": rough_tokens(user_msg),
            "user_tokens_hi": rough_tokens_hi(user_msg),
            "total_tokens_lo": rough_tokens(system_text + user_msg),
            "total_tokens_hi": rough_tokens_hi(system_text + user_msg),
        }
        print(f"{symbol:10s} fmt={fmt} sys={sys_chars:,} user={user_chars:,} "
              f"tot={total_chars:,} chars "
              f"(~{rough_tokens(system_text + user_msg):,} lo / {rough_tokens_hi(system_text + user_msg):,} hi tokens)")

    out = {
        "mso_source": str(MSO_PATH),
        "mso_timestamp": mso.get("timestamp_utc"),
        "sonnet_4_6_context_limit_tokens": 200_000,
        "instruments": results,
    }
    (OUT_DIR.parent / "token_counts.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT_DIR.parent / 'token_counts.json'}")


if __name__ == "__main__":
    main()
