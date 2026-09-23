"""Unit tests for ``src/research_infra/hallucination_measurement.py``.

Coverage targets (B7 brief):

  1. ``parse_ai_prices`` — extracts trade_parameters + reasoning sub-fields.
  2. ``parse_ai_prices`` — extracts explanation-text prices via regex.
  3. ``classify_price`` — exact match → ACCURATE.
  4. ``classify_price`` — within tolerance → ACCURATE.
  5. ``classify_price`` — outside tolerance → HALLUCINATED.
  6. ``classify_price`` — price exists in MSO at different role → MISATTRIBUTED.
  7. ``measure_hallucination_rate`` — per-instrument aggregation across 5 evals
     spanning 2 instruments → 2 instrument rows.
  8. ``build_mso_price_set`` — extracts OB/breaker/FVG/swing/session_levels.
  9. ``build_ohlcv_price_set`` — coarse stand-in from candle list.
 10. ``HallucinationReport.h1_h2_delta_pp`` — H1 vs H2 partition computed
     correctly when both halves carry data.
 11. End-to-end on synthetic trade_records-style records: rates dict has
     accurate%/hallucinated%/misattributed%.

F13 (B7-v2 role-stratified) coverage:

 12. ``ROLE_TAXONOMY`` completeness — every role surfaced by the parser
     is in the taxonomy (no silent AMBIGUOUS fallback for known roles).
 13. ``role_class_of`` returns correct class for canonical roles
     (MSO_GROUNDED, FORWARD_DERIVED, AMBIGUOUS) + AMBIGUOUS default for
     unknown.
 14. ``PriceClassification.role_class`` auto-derives from
     ``ROLE_TAXONOMY`` at construction time.
 15. ``measure_hallucination_rate_by_role_class`` returns per-instrument
     × per-role-class breakdown with correct rates.
 16. MSO_GROUNDED-only rate calculation: hallucinated_pct on the
     MSO_GROUNDED row excludes TP hallucinations.
 17. Backward compat: original ``measure_hallucination_rate`` signature
     and v1 schema (``by_instrument``, ``by_role`` …) still emitted
     unchanged.

All tests are pure-Python; no production paths are written.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research_infra.hallucination_measurement import (
    DEFAULT_TOLERANCE_TICKS,
    EXPLANATION_PATTERNS,
    HARNESS_VERSION_V2,
    ROLE_TAXONOMY,
    CitedPrice,
    HallucinationReport,
    HallucinationRateRow,
    MSOPriceSet,
    OHLCVLookbackProvider,
    PriceClassification,
    build_mso_price_set,
    build_ohlcv_price_set,
    classify_price,
    classify_price_detailed,
    measure_hallucination_rate,
    measure_hallucination_rate_by_role_class,
    parse_ai_prices,
    role_class_of,
)


# ---------------------------------------------------------------------------
# Synthetic MSO factory (mirrors trade_records ``mso`` shape)
# ---------------------------------------------------------------------------


def _make_synthetic_mso(*, h1_obs=None, h1_swings=None, session_levels=None):
    """Return a minimal MSO dict for unit tests."""
    h1_obs = h1_obs or []
    h1_swings = h1_swings or []
    return {
        "timestamp_utc": "2026-04-13T07:00:00+00:00",
        "timeframes": {
            "H1": {
                "swings": h1_swings,
                "order_blocks": h1_obs,
                "breaker_blocks": [],
                "fair_value_gaps": [],
                "structure_events": [],
                "candles": [
                    {"time": "2026-04-13T06:00:00", "open": 211.50, "high": 211.55, "low": 211.40, "close": 211.45},
                    {"time": "2026-04-13T07:00:00", "open": 211.45, "high": 211.60, "low": 211.42, "close": 211.55},
                ],
            },
            "H4": {"swings": [], "order_blocks": [], "breaker_blocks": [], "fair_value_gaps": [], "candles": []},
            "D1": {"swings": [], "order_blocks": [], "breaker_blocks": [], "fair_value_gaps": [], "candles": []},
            "M15": {"swings": [], "order_blocks": [], "breaker_blocks": [], "fair_value_gaps": [], "candles": []},
        },
        "session_levels": session_levels or {},
        "equal_highs": [],
        "equal_lows": [],
    }


# ---------------------------------------------------------------------------
# parse_ai_prices
# ---------------------------------------------------------------------------


def test_parse_ai_prices_extracts_trade_parameters():
    ai_response = {
        "decision": "CANDIDATE",
        "framework": "ob_retest",
        "trade_parameters": {
            "direction": "LONG",
            "entry_price": 214.261,
            "stop_loss": 214.002,
            "take_profit_1": 214.65,
            "take_profit_2": 0.0,    # sentinel — should be filtered
            "take_profit_3": 0.0,    # sentinel
            "sl_buffer_applied": 0.0,
            "risk_reward_ratio": 1.5,
        },
        "reasoning": {},
    }
    cited = parse_ai_prices(ai_response)
    roles = sorted({c.role for c in cited})
    assert "entry_price" in roles
    assert "stop_loss" in roles
    assert "take_profit" in roles
    # Filtered: 0.0 take-profit slots
    assert sum(1 for c in cited if c.role == "take_profit") == 1


def test_parse_ai_prices_extracts_reasoning_subfields():
    ai_response = {
        "decision": "CANDIDATE",
        "trade_parameters": {},
        "reasoning": {
            "h1_setup": {
                "poi_identified": True,
                "poi_type": "OB",
                "poi_price_level": 214.076,
                "explanation": "Nearest unmitigated H1 OB at 214.129-214.023 (midpoint 214.076)",
            },
            "daily_bias": {"protected_swing_level": 213.649},
            "liquidity_sweep": {"sweep_price": 214.270, "detected": True},
            "overall_reasoning": "Current price 214.30 is at H1 OB.",
        },
    }
    cited = parse_ai_prices(ai_response)
    roles = {c.role for c in cited}
    assert "ob_mid" in roles  # poi_price_level for OB poi_type
    assert "protected_swing" in roles
    assert "sweep_price" in roles
    assert "ob_high" in roles  # from explanation regex
    assert "ob_low" in roles
    assert "current_price" in roles


def test_parse_ai_prices_explanation_text_prices():
    """live_evaluations-style flat record."""
    rec = {
        "decision": "NO_TRADE",
        "framework": "none",
        "overall_reasoning": "Current price 4667.64 is not near H1 OB 4518.23-4501.61 or breakers 4730.03-4713.01.",
        "no_trade_reason": "Price not at H1 POI",
    }
    cited = parse_ai_prices(rec)
    roles = {c.role for c in cited}
    values = sorted({c.value for c in cited})
    assert "current_price" in roles
    assert "ob_high" in roles
    assert "ob_low" in roles
    assert "breaker_high" in roles
    assert "breaker_low" in roles
    # Sanity: includes the high we expect
    assert any(abs(c.value - 4667.64) < 1e-6 for c in cited)
    assert any(abs(c.value - 4518.23) < 1e-6 for c in cited)


# ---------------------------------------------------------------------------
# build_mso_price_set
# ---------------------------------------------------------------------------


def test_build_mso_price_set_extracts_obs_and_swings():
    mso = _make_synthetic_mso(
        h1_obs=[
            {"type": "bullish", "high": 214.13, "low": 214.02, "open": 214.05, "close": 214.10},
            {"type": "bearish", "high": 215.50, "low": 215.30, "open": 215.40, "close": 215.32},
        ],
        h1_swings=[
            {"type": "high", "price": 215.80, "index": 5},
            {"type": "low", "price": 213.60, "index": 8},
        ],
        session_levels={"asian_high": 214.50, "asian_low": 213.90, "pdh": 215.00, "pdl": 213.40},
    )
    ps = build_mso_price_set(mso)
    # OBs
    ob_highs = [v for v, _ in ps.by_role.get("ob_high", [])]
    assert 214.13 in ob_highs and 215.50 in ob_highs
    # OB midpoints
    ob_mids = sorted(v for v, _ in ps.by_role.get("ob_mid", []))
    assert pytest.approx(214.075, abs=1e-6) in ob_mids
    # Swings
    sh = [v for v, _ in ps.by_role.get("swing_high", [])]
    sl = [v for v, _ in ps.by_role.get("swing_low", [])]
    assert 215.80 in sh
    assert 213.60 in sl
    # Session levels also push to swing_high / swing_low (and sweep_price)
    assert 214.50 in [v for v, _ in ps.by_role.get("swing_high", [])]
    assert 213.40 in [v for v, _ in ps.by_role.get("sweep_price", [])]


# ---------------------------------------------------------------------------
# classify_price
# ---------------------------------------------------------------------------


def test_classify_price_exact_match_is_accurate():
    mso = _make_synthetic_mso(
        h1_obs=[{"type": "bullish", "high": 214.13, "low": 214.02, "open": 214.05, "close": 214.10}]
    )
    res = classify_price(214.13, "ob_high", mso, tolerance_ticks=5, symbol="GBPJPY")
    assert res == "accurate"


def test_classify_price_within_tolerance_is_accurate():
    mso = _make_synthetic_mso(
        h1_obs=[{"type": "bullish", "high": 214.13, "low": 214.02, "open": 214.05, "close": 214.10}]
    )
    # GBPJPY tick = 0.001; 5 ticks = 0.005; cited 214.131 is within tolerance
    res = classify_price(214.131, "ob_high", mso, tolerance_ticks=5, symbol="GBPJPY")
    assert res == "accurate"


def test_classify_price_outside_tolerance_is_hallucinated():
    # MSO has only OB high 214.13. Cite 220.00 → no match anywhere → hallucinated.
    mso = _make_synthetic_mso(
        h1_obs=[{"type": "bullish", "high": 214.13, "low": 214.02, "open": 214.05, "close": 214.10}]
    )
    res = classify_price(220.00, "ob_high", mso, tolerance_ticks=5, symbol="GBPJPY")
    assert res == "hallucinated"


def test_classify_price_misattributed_when_role_wrong():
    # MSO has swing high 215.80; AI cites it as "ob_high" instead.
    mso = _make_synthetic_mso(
        h1_obs=[],  # no OBs at all
        h1_swings=[{"type": "high", "price": 215.80, "index": 5}],
    )
    res = classify_price(215.80, "ob_high", mso, tolerance_ticks=5, symbol="GBPJPY")
    assert res == "misattributed"


def test_classify_price_synthesized_role_entry_matches_any():
    """entry_price is allowed to match against any MSO band within tolerance.

    The AI synthesizes entry from OB geometry; ``entry_price`` does not appear
    directly in the MSO. We accept ANY MSO price within tolerance as accurate
    (the AI is allowed to derive entry from OB high/low/midpoint).
    """
    mso = _make_synthetic_mso(
        h1_obs=[{"type": "bullish", "high": 214.13, "low": 214.02, "open": 214.05, "close": 214.10}]
    )
    res = classify_price(214.10, "entry_price", mso, tolerance_ticks=5, symbol="GBPJPY")
    assert res == "accurate"  # close-to OB.close


def test_classify_price_detailed_reports_delta_ticks():
    mso = _make_synthetic_mso(
        h1_obs=[{"type": "bullish", "high": 214.13, "low": 214.02, "open": 214.05, "close": 214.10}]
    )
    ps = build_mso_price_set(mso)
    cited = CitedPrice(role="ob_high", value=214.131, source_field="test")
    res = classify_price_detailed(cited, ps, symbol="GBPJPY", tolerance_ticks=5)
    assert res.classification == "accurate"
    assert res.matched_mso_value == pytest.approx(214.13)
    assert res.delta_ticks is not None
    # 0.001 / 0.001 (tick size) = 1 tick
    assert abs(res.delta_ticks - 1.0) < 1e-6


# ---------------------------------------------------------------------------
# build_ohlcv_price_set
# ---------------------------------------------------------------------------


def test_build_ohlcv_price_set_collects_candle_extremes():
    candles = [
        {"high": 214.50, "low": 214.10, "close": 214.30},
        {"high": 214.80, "low": 214.20, "close": 214.65},
    ]
    ps = build_ohlcv_price_set(candles)
    swing_highs = sorted(v for v, _ in ps.by_role.get("swing_high", []))
    swing_lows = sorted(v for v, _ in ps.by_role.get("swing_low", []))
    cps = sorted(v for v, _ in ps.by_role.get("current_price", []))
    assert 214.50 in swing_highs and 214.80 in swing_highs
    assert 214.10 in swing_lows and 214.20 in swing_lows
    assert 214.30 in cps and 214.65 in cps


# ---------------------------------------------------------------------------
# measure_hallucination_rate end-to-end
# ---------------------------------------------------------------------------


def _make_trade_record(symbol, candle_time, *, accurate=True, framework="ob_retest"):
    """Build a synthetic trade_records-style record."""
    if accurate:
        # AI cites the exact OB midpoint that exists in MSO
        ai_poi = 214.076
        explanation = "H1 OB at 214.129-214.023 (midpoint 214.076)"
        entry = 214.10
    else:
        # AI cites 220.00 — nowhere in MSO
        ai_poi = 220.00
        explanation = "H1 OB at 220.00-219.50 (midpoint 219.75)"
        entry = 220.00

    return {
        "metadata": {"symbol": symbol, "candle_time": candle_time},
        "decision_pipeline": {"ai_decision": "CANDIDATE", "ai_framework": framework},
        "mso": _make_synthetic_mso(
            h1_obs=[{"type": "bullish", "high": 214.129, "low": 214.023, "open": 214.05, "close": 214.10}]
        ),
        "ai_response": {
            "decision": "CANDIDATE",
            "framework": framework,
            "trade_parameters": {
                "direction": "LONG",
                "entry_price": entry,
                "stop_loss": 213.95,
                "take_profit_1": 214.50,
                "take_profit_2": 0.0,
                "take_profit_3": 0.0,
                "sl_buffer_applied": 0.0,
                "risk_reward_ratio": 1.5,
            },
            "reasoning": {
                "h1_setup": {
                    "poi_identified": True,
                    "poi_type": "OB",
                    "poi_price_level": ai_poi,
                    "explanation": explanation,
                },
                "overall_reasoning": "All three C-gates pass.",
            },
        },
    }


def test_measure_hallucination_rate_per_instrument_aggregation():
    """5-eval fixture across 2 instruments → 2 rate rows."""
    records = [
        _make_trade_record("GBPJPY", "2026-04-13T07:00:00+00:00", accurate=True),
        _make_trade_record("GBPJPY", "2026-04-14T07:00:00+00:00", accurate=True),
        _make_trade_record("GBPJPY", "2026-04-15T07:00:00+00:00", accurate=False),
        _make_trade_record("USDJPY", "2026-04-13T07:00:00+00:00", accurate=True),
        _make_trade_record("USDJPY", "2026-04-14T07:00:00+00:00", accurate=False),
    ]
    report = measure_hallucination_rate(records, tolerance_ticks=5)

    assert report.n_records_scanned == 5
    assert len(report.by_instrument) == 2
    keys = sorted(r.key for r in report.by_instrument)
    assert keys == ["GBPJPY", "USDJPY"]

    # Both instruments should have classifications
    for r in report.by_instrument:
        assert r.n_evaluations >= 1
        assert r.n_prices >= 1
        # at least one accurate hit per instrument
        assert r.n_accurate >= 1


def test_measure_hallucination_rate_handles_h1_h2_partition():
    """H1+H2 evaluations → ``h1_h2_delta_pp`` populated."""
    # Half-year split: Jan-Jun = H1; Jul-Dec = H2.
    # We synthesize one H1-2026 (Jan) record (accurate) and one H2-2026 (Aug)
    # record (heavy hallucination) so the delta is positive (H2 > H1).
    records = [
        _make_trade_record("GBPJPY", "2026-01-15T07:00:00+00:00", accurate=True),
        _make_trade_record("GBPJPY", "2026-08-15T07:00:00+00:00", accurate=False),
    ]
    report = measure_hallucination_rate(records, tolerance_ticks=5)
    assert report.h1_h2_delta_pp is not None
    # H2 should be more hallucinated than H1
    assert report.h1_h2_delta_pp > 0


def test_measure_hallucination_rate_skips_records_without_mso():
    """A live-eval-style record without ``mso``/``ai_response`` is handled."""
    records = [
        # live_evaluations style — no MSO; classifications=None unless OHLCV provider given
        {
            "symbol": "XAUUSD",
            "candle_time": "2026-04-13T07:00:00+00:00",
            "decision": "NO_TRADE",
            "framework": "none",
            "overall_reasoning": "Current price 4667.64 is not near H1 OB 4518.23-4501.61.",
            "no_trade_reason": "Price not at H1 POI",
        },
        # Trade-records style with full MSO+AI
        _make_trade_record("XAUUSD", "2026-04-14T07:00:00+00:00", accurate=True),
    ]
    report = measure_hallucination_rate(records, tolerance_ticks=5)
    # 2 records scanned; only the trade_record has classifications (live_eval w/o OHLCV provider gives classification=None)
    assert report.n_records_scanned == 2
    # Live_evaluations row contributes None classifications, so n_records_with_classifications==1
    assert report.n_records_with_classifications == 1


def test_measure_hallucination_rate_emits_to_summary_dict():
    records = [_make_trade_record("GBPJPY", "2026-04-13T07:00:00+00:00", accurate=True)]
    report = measure_hallucination_rate(records, tolerance_ticks=5)
    summary = report.to_summary_dict()
    assert "harness_version" in summary
    assert "tolerance_ticks" in summary
    assert summary["tolerance_ticks"] == 5
    assert "by_instrument" in summary
    # Round-trip through json
    s = json.dumps(summary)
    assert json.loads(s)["harness_version"] == "B7-v1"


# ---------------------------------------------------------------------------
# OHLCV provider
# ---------------------------------------------------------------------------


def test_ohlcv_lookback_provider_returns_pre_target_window(tmp_path: Path):
    """Provider should return only candles strictly <= target candle_time."""
    csv = tmp_path / "GBPJPY_H1.csv"
    csv.write_text(
        "time,open,high,low,close,volume\n"
        "2026-04-13 06:00:00,211.40,211.55,211.30,211.50,100\n"
        "2026-04-13 07:00:00,211.50,211.65,211.42,211.60,120\n"
        "2026-04-13 08:00:00,211.60,211.75,211.55,211.70,110\n"
    )
    provider = OHLCVLookbackProvider(ohlcv_dir=tmp_path, timeframe="H1", lookback_bars=10)
    window = provider.get_window("GBPJPY", "2026-04-13T07:30:00+00:00")
    assert len(window) == 2
    times = [c["time"] for c in window]
    assert "2026-04-13 06:00:00" in times
    assert "2026-04-13 07:00:00" in times
    # The 08:00 bar must NOT appear (after target)
    assert "2026-04-13 08:00:00" not in times


def test_classify_price_with_ohlcv_provider_accurate_match():
    """Live_evaluations row + OHLCV provider → accurate classification."""
    from src.research_infra.hallucination_measurement import _check_live_evaluation
    rec = {
        "symbol": "GBPJPY",
        "candle_time": "2026-04-13T07:30:00+00:00",
        "decision": "NO_TRADE",
        "framework": "none",
        "overall_reasoning": "Current price 211.55 is not at any H1 OB.",
    }

    class StubProvider:
        def get_window(self, symbol, candle_time):
            return [
                {"high": 211.55, "low": 211.40, "close": 211.50},
                {"high": 211.65, "low": 211.42, "close": 211.60},
            ]

    check = _check_live_evaluation(rec, tolerance_ticks=5, ohlcv_provider=StubProvider())
    assert check is not None
    # current_price 211.55 matches a candle high → accurate
    assert any(c.classification == "accurate" for c in check.classifications)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_parse_ai_prices_empty_record():
    cited = parse_ai_prices({})
    assert cited == []


def test_classify_price_with_empty_mso():
    mso = {"timeframes": {}}
    res = classify_price(214.13, "ob_high", mso, tolerance_ticks=5, symbol="GBPJPY")
    assert res == "hallucinated"


def test_measure_hallucination_rate_empty_input():
    report = measure_hallucination_rate([], tolerance_ticks=5)
    assert report.n_records_scanned == 0
    assert report.by_instrument == []
    assert report.h1_h2_delta_pp is None


# ===========================================================================
# F13 — B7-v2 role-stratified hallucination rates
# ===========================================================================


def _make_record_with_tp_hallucination(symbol, candle_time, *, tp_value=99999.99):
    """Synthetic record with accurate MSO-grounded prices + hallucinated TP.

    Tests the canonical F13 scenario: the AI cites a forward-derived TP
    not in the MSO; under v1 this counts as a hallucination, but under
    v2 it should be excluded from the MSO-grounded rate.
    """
    return {
        "metadata": {"symbol": symbol, "candle_time": candle_time},
        "decision_pipeline": {"ai_decision": "CANDIDATE", "ai_framework": "ob_retest"},
        "mso": _make_synthetic_mso(
            h1_obs=[{"type": "bullish", "high": 214.129, "low": 214.023, "open": 214.05, "close": 214.10}]
        ),
        "ai_response": {
            "decision": "CANDIDATE",
            "framework": "ob_retest",
            "trade_parameters": {
                "direction": "LONG",
                "entry_price": 214.10,
                "stop_loss": 214.023,  # within tolerance of OB low
                "take_profit_1": tp_value,  # forward-derived, not in MSO
                "take_profit_2": 0.0,
                "take_profit_3": 0.0,
                "sl_buffer_applied": 0.0,
                "risk_reward_ratio": 1.5,
            },
            "reasoning": {
                "h1_setup": {
                    "poi_identified": True,
                    "poi_type": "OB",
                    "poi_price_level": 214.076,
                    "explanation": "OB at 214.129-214.023 (midpoint 214.076)",
                },
                "overall_reasoning": "ok.",
            },
        },
    }


def test_role_taxonomy_completeness_covers_parser_emitted_roles():
    """Every role the parser/classifier can emit must be in ROLE_TAXONOMY.

    Reasoning: if a known role drops to AMBIGUOUS via the default
    fallback, MSO_GROUNDED rates silently undercount real failures.
    The taxonomy must enumerate all canonical roles explicitly.
    """
    # Roles surfaced by parse_ai_prices structured-block path
    structured_roles = {
        "entry_price", "stop_loss", "take_profit",
        "ob_high", "ob_low", "ob_mid",
        "fvg_mid",
        "breaker_mid",
        "protected_swing", "sweep_price",
    }
    # Roles surfaced by EXPLANATION_PATTERNS regex path
    pattern_roles = set()
    for role, _pat, _label in EXPLANATION_PATTERNS:
        if role.endswith("_pair"):
            base = role.replace("_pair", "")
            pattern_roles.add(f"{base}_high")
            pattern_roles.add(f"{base}_low")
        else:
            pattern_roles.add(role)

    # Roles surfaced by build_mso_price_set
    mso_roles = {
        "ob_high", "ob_low", "ob_mid", "ob_body",
        "breaker_high", "breaker_low", "breaker_mid",
        "fvg_high", "fvg_low", "fvg_mid",
        "swing_high", "swing_low",
        "current_price",
        "sweep_price", "liquidity_high", "liquidity_low",
    }

    all_known = structured_roles | pattern_roles | mso_roles
    missing = sorted(all_known - set(ROLE_TAXONOMY.keys()))
    assert missing == [], f"Roles emitted by the harness but missing from ROLE_TAXONOMY: {missing}"


def test_role_class_of_returns_correct_class_per_role():
    # MSO_GROUNDED — anchored to MSO data
    assert role_class_of("ob_high") == "MSO_GROUNDED"
    assert role_class_of("ob_low") == "MSO_GROUNDED"
    assert role_class_of("ob_mid") == "MSO_GROUNDED"
    assert role_class_of("fvg_high") == "MSO_GROUNDED"
    assert role_class_of("fvg_low") == "MSO_GROUNDED"
    assert role_class_of("swing_high") == "MSO_GROUNDED"
    assert role_class_of("swing_low") == "MSO_GROUNDED"
    assert role_class_of("current_price") == "MSO_GROUNDED"
    assert role_class_of("breaker_high") == "MSO_GROUNDED"
    assert role_class_of("breaker_low") == "MSO_GROUNDED"
    assert role_class_of("entry_price") == "MSO_GROUNDED"
    assert role_class_of("stop_loss") == "MSO_GROUNDED"
    assert role_class_of("protected_swing") == "MSO_GROUNDED"
    assert role_class_of("sweep_price") == "MSO_GROUNDED"

    # FORWARD_DERIVED — not in MSO by construction
    assert role_class_of("take_profit") == "FORWARD_DERIVED"
    assert role_class_of("trailing_stop_target") == "FORWARD_DERIVED"

    # AMBIGUOUS — case-by-case
    assert role_class_of("equilibrium") == "AMBIGUOUS"

    # Unknown roles default to AMBIGUOUS (do NOT silently inflate
    # MSO_GROUNDED rate)
    assert role_class_of("__unknown_role__") == "AMBIGUOUS"
    assert role_class_of("") == "AMBIGUOUS"


def test_price_classification_auto_derives_role_class_at_construction():
    """The dataclass __post_init__ should populate role_class from role."""
    pc = PriceClassification(
        role="ob_high", value=214.13, source_field="test", classification="accurate",
    )
    assert pc.role_class == "MSO_GROUNDED"

    pc_tp = PriceClassification(
        role="take_profit", value=215.00, source_field="test", classification="hallucinated",
    )
    assert pc_tp.role_class == "FORWARD_DERIVED"

    pc_amb = PriceClassification(
        role="equilibrium", value=214.50, source_field="test", classification="accurate",
    )
    assert pc_amb.role_class == "AMBIGUOUS"

    # Unknown role keeps AMBIGUOUS
    pc_un = PriceClassification(
        role="my_novel_role", value=0.0, source_field="test", classification=None,
    )
    assert pc_un.role_class == "AMBIGUOUS"


def test_measure_hallucination_rate_by_role_class_returns_per_class_breakdown():
    """measure_hallucination_rate_by_role_class returns 3-deep dict structure."""
    records = [
        _make_record_with_tp_hallucination("GBPJPY", "2026-04-13T07:00:00+00:00", tp_value=99999.99),
        _make_record_with_tp_hallucination("GBPJPY", "2026-04-14T07:00:00+00:00", tp_value=88888.88),
        _make_record_with_tp_hallucination("USDJPY", "2026-04-13T07:00:00+00:00", tp_value=77777.77),
    ]
    out = measure_hallucination_rate_by_role_class(records, tolerance_ticks=5)

    assert "GBPJPY" in out
    assert "USDJPY" in out
    # Both instruments have at least MSO_GROUNDED + FORWARD_DERIVED rows
    for inst, by_class in out.items():
        assert "MSO_GROUNDED" in by_class
        assert "FORWARD_DERIVED" in by_class
        # All rows are HallucinationRateRow + correctly tagged role_class
        for cl, row in by_class.items():
            assert isinstance(row, HallucinationRateRow)
            assert row.role_class == cl
            assert row.instrument == inst
            assert row.n_prices > 0


def test_mso_grounded_only_rate_excludes_forward_derived_artifacts():
    """The MSO_GROUNDED rate should be lower than the all-roles rate when
    every record carries a forward-derived TP hallucination."""
    records = [
        _make_record_with_tp_hallucination("GBPJPY", "2026-04-13T07:00:00+00:00", tp_value=99999.99),
        _make_record_with_tp_hallucination("GBPJPY", "2026-04-14T07:00:00+00:00", tp_value=88888.88),
        _make_record_with_tp_hallucination("GBPJPY", "2026-04-15T07:00:00+00:00", tp_value=77777.77),
    ]
    report = measure_hallucination_rate(records, tolerance_ticks=5)

    # All-roles per-instrument rate (v1 metric)
    inst_row = next(r for r in report.by_instrument if r.instrument == "GBPJPY")
    all_roles_pct = inst_row.hallucinated_pct
    assert all_roles_pct is not None and all_roles_pct > 0  # the 3 TPs hallucinated

    # MSO_GROUNDED-only rate (v2 metric)
    mso_row = next(
        r for r in report.by_instrument_role_class
        if r.instrument == "GBPJPY" and r.role_class == "MSO_GROUNDED"
    )
    mso_pct = mso_row.hallucinated_pct

    # MSO-grounded rate must be strictly less than the all-roles rate
    # (the only hallucinations were forward-derived TPs).
    assert mso_pct is not None
    assert mso_pct < all_roles_pct, (
        f"Expected MSO-grounded rate ({mso_pct:.2f}%) < all-roles rate "
        f"({all_roles_pct:.2f}%) when all hallucinations are forward-derived TPs."
    )

    # FORWARD_DERIVED row should be 100% hallucinated
    fwd_row = next(
        r for r in report.by_instrument_role_class
        if r.instrument == "GBPJPY" and r.role_class == "FORWARD_DERIVED"
    )
    assert fwd_row.hallucinated_pct == pytest.approx(100.0)

    # Summary dict round-trip with v2 fields
    summary = report.to_summary_dict()
    assert "by_instrument_role_class" in summary
    assert "by_instrument_mso_grounded" in summary
    # MSO-grounded list is filtered to MSO_GROUNDED rows only
    for row in summary["by_instrument_mso_grounded"]:
        assert row["role_class"] == "MSO_GROUNDED"


def test_backward_compat_v1_signature_and_schema_unchanged():
    """The original measure_hallucination_rate(seq, tolerance_ticks) call
    must keep working and emit the v1 schema with the same field set."""
    records = [
        _make_trade_record("GBPJPY", "2026-04-13T07:00:00+00:00", accurate=True),
        _make_trade_record("USDJPY", "2026-04-13T07:00:00+00:00", accurate=False),
    ]
    # Call with positional args, exactly as the v1 signature demands
    report = measure_hallucination_rate(records, 5)

    # v1 fields still present
    assert hasattr(report, "harness_version")
    assert hasattr(report, "tolerance_ticks")
    assert hasattr(report, "n_records_scanned")
    assert hasattr(report, "by_instrument")
    assert hasattr(report, "by_instrument_period")
    assert hasattr(report, "by_instrument_month")
    assert hasattr(report, "by_instrument_framework")
    assert hasattr(report, "by_role")
    assert hasattr(report, "h1_h2_delta_pp")
    assert hasattr(report, "most_hallucinated_role")

    # v1 instrument rows still keyed by symbol (no role_class collapse)
    keys = sorted(r.instrument for r in report.by_instrument)
    assert keys == ["GBPJPY", "USDJPY"]
    for r in report.by_instrument:
        # role_class None on v1-shape rows (instrument-level aggregate)
        assert r.role_class is None

    # v1 schema in summary dict
    summary = report.to_summary_dict()
    expected_v1_keys = {
        "harness_version", "tolerance_ticks", "n_records_scanned",
        "n_records_with_classifications", "by_instrument",
        "by_instrument_period", "by_instrument_month",
        "by_instrument_framework", "by_role",
        "h1_h2_delta_pp", "most_hallucinated_role",
    }
    assert expected_v1_keys.issubset(summary.keys()), (
        f"v1 schema missing keys: {expected_v1_keys - set(summary.keys())}"
    )

    # v2 keys appear additively (additive, not breaking)
    assert "by_instrument_role_class" in summary
    assert "by_instrument_mso_grounded" in summary

    # Per-row dict still has the v1 fields
    inst_dict = summary["by_instrument"][0]
    for k in ("key", "instrument", "n_evaluations", "n_prices", "n_accurate",
              "n_hallucinated", "n_misattributed", "accurate_pct",
              "hallucinated_pct", "misattributed_pct"):
        assert k in inst_dict, f"v1 row missing key: {k}"

    # Harness version v2 constant exists and is distinct from v1
    assert HARNESS_VERSION_V2 == "B7-v2"
    assert report.harness_version == "B7-v1"  # default callers see v1 tag
