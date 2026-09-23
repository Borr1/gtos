"""ADR-006 — primary analyzer prompt parallel-dispatch + config-substituted SL buffer tests.

Validates that ``build_system_prompt`` produces the expected substitutions
under ADR-006:

1. SL buffer multipliers are pulled from ``risk.sl_buffer_atr_multiplier``
   / ``risk.sl_buffer_breaker_atr_multiplier`` / ``risk.sl_buffer_min_ticks``
   (instead of being hardcoded literals in the prompt template).

2. Per-instrument tight-FX overrides (EURUSD ob_atr_mult=0.50, min_ticks=8)
   appear in the built prompt when the per-instrument config is passed.

3. The DECISION ORDER block is now PARALLEL EVALUATION — the
   priority-cascade language ("ob_retest FIRST. ONLY IF") MUST be absent.

4. ``min_ticks`` substitution covers all template sites (both the precision
   examples block and the ob_retest TRADE PARAMETERS section).

5. The breaker addendum's ``0.5 * H1 ATR(14)`` literal is replaced by the
   ``{breaker_atr_mult}`` substitution.
"""

from __future__ import annotations

from src.prompts.primary_analyzer_prompt import build_system_prompt


# ---------------------------------------------------------------------------
# Helper config builders — minimal valid input shapes
# ---------------------------------------------------------------------------

def _base_config(**risk_overrides: float | int) -> dict:
    """Build a base config with the default risk SL buffer triple."""
    risk_block = {
        "sl_buffer_atr_multiplier": 0.25,
        "sl_buffer_breaker_atr_multiplier": 0.5,
        "sl_buffer_min_ticks": 5,
        "sl_absolute_min": 5.0,
    }
    risk_block.update(risk_overrides)
    return {
        "market": {
            "symbol": "XAUUSD",
            "kill_zones": {
                "london": {"start_utc": "07:00", "end_utc": "10:30"},
                "ny": {"start_utc": "13:00", "end_utc": "17:00"},
            },
        },
        "risk": risk_block,
        "model_a": {
            "enabled_frameworks": ["ob_retest", "fvg_fill", "breaker_re_entry"],
        },
        "prompt": {"price_format": ".2f"},
    }


# ---------------------------------------------------------------------------
# Case 1 — atr_mult tokens substituted (no raw `{ob_atr_mult}` left)
# ---------------------------------------------------------------------------


def test_prompt_replaces_atr_mult_tokens():
    """The built prompt MUST NOT contain raw substitution tokens — every
    ``{ob_atr_mult}`` / ``{breaker_atr_mult}`` / ``{min_ticks}`` must have
    been resolved to its numeric value.
    """
    cfg = _base_config()
    text = build_system_prompt(cfg)

    # Tokens must NOT survive substitution
    assert "{ob_atr_mult}" not in text
    assert "{breaker_atr_mult}" not in text
    assert "{min_ticks}" not in text

    # Default values present somewhere in the text
    # (we look for "0.25" — the default ob_atr_mult — in the SL buffer
    # phrasing; not a guarantee of every site, but a strong signal)
    assert "0.25" in text


# ---------------------------------------------------------------------------
# Case 2 — Per-instrument EURUSD override → 0.50 substitution
# ---------------------------------------------------------------------------


def test_prompt_per_instrument_eurusd():
    """When the merged config has EURUSD's tight-FX overrides
    (ob_atr_mult=0.50, min_ticks=8), the built prompt must show those values.
    """
    cfg = _base_config(
        sl_buffer_atr_multiplier=0.50,
        sl_buffer_min_ticks=8,
    )
    cfg["market"]["symbol"] = "EURUSD"
    text = build_system_prompt(cfg)

    # 0.50 substituted somewhere
    assert "0.50" in text
    # 8-tick floor substituted somewhere
    assert " 8 " in text or " 8 x" in text or " 8 *" in text or "8 x" in text


# ---------------------------------------------------------------------------
# Case 3 — DECISION ORDER says PARALLEL, no priority-cascade
# ---------------------------------------------------------------------------


def test_prompt_dispatch_section_says_parallel():
    """ADR-006: the DECISION ORDER block MUST say PARALLEL EVALUATION,
    and the legacy priority-cascade phrasing ("ONLY IF ob_retest cannot
    fire") MUST be absent.
    """
    cfg = _base_config()
    text = build_system_prompt(cfg)

    assert "PARALLEL EVALUATION" in text
    # Legacy step-C cascade must be absent
    assert "ONLY if ``ob_retest`` cannot fire" not in text
    assert "ONLY if neither ``ob_retest`` nor ``fvg_fill`` fires" not in text
    # Per ADR-006 spec, the new block has Step F tiebreakers
    assert "STRICT order" in text or "STRICT ORDER" in text or "stable\n          tiebreaker" in text


# ---------------------------------------------------------------------------
# Case 4 — min_ticks substitution (default 5 vs override)
# ---------------------------------------------------------------------------


def test_min_ticks_substitution():
    """Default ``min_ticks`` is 5; override to 8 and confirm propagation."""
    cfg_default = _base_config()
    text_default = build_system_prompt(cfg_default)
    # 5-tick floor visible
    assert " 5 x smallest tick" in text_default or " 5 x the smallest" in text_default

    cfg_eight = _base_config(sl_buffer_min_ticks=8)
    text_eight = build_system_prompt(cfg_eight)
    assert " 8 x smallest tick" in text_eight or " 8 x the smallest" in text_eight


# ---------------------------------------------------------------------------
# Case 5 — breaker addendum uses config breaker_atr_mult
# ---------------------------------------------------------------------------


def test_breaker_addendum_uses_config_mult():
    """The breaker addendum mentions ``0.5 * H1 ATR`` for the breaker's SL
    buffer. Under ADR-006 substitution, that ``0.5`` is now read from
    ``risk.sl_buffer_breaker_atr_multiplier``. Default config keeps 0.5;
    overriding it MUST show in the breaker section of the built prompt.
    """
    cfg_default = _base_config()
    text_default = build_system_prompt(cfg_default)
    # Default breaker mult 0.5 present in the addendum
    assert "0.50 * H1 ATR(14)" in text_default or "0.50*H1 ATR(14)" in text_default

    cfg_overridden = _base_config(sl_buffer_breaker_atr_multiplier=0.75)
    text_overridden = build_system_prompt(cfg_overridden)
    assert "0.75 * H1 ATR(14)" in text_overridden or "0.75*H1 ATR(14)" in text_overridden
