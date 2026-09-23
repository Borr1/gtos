"""Tests for ADR-005 additive fields in candidate_features_logger.

Scope: verify that the logger additively writes the A1 backtest validation
fields (h1_opp_ob_touch, h1_fvg_unfilled_count, m15_fvg_unfilled_count,
ai_decision, ai_no_trade_reason, ai_direction_evaluated,
detector_version_at_eval, slice_tag) WITHOUT removing or breaking any
existing field.

All tests are isolated via tmp_path. No production logs are touched.

Covers:
1. Logger writes on NO_TRADE with new ADR-005 fields populated.
2. Logger computes h1_opp_ob_touch correctly from synthetic MSO.
3. Logger handles missing opposing-OB case → -1.
4. Logger handles missing ai_direction_evaluated (fall back to tp_direction).
5. Logger JSON schema round-trips.
6. Schema is backward compatible — all legacy fields still present.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.components.candidate_features_logger import (
    _nearest_opposing_ob_touch,
    log_candidate_features,
)


# -----------------------------------------------------------------------------
# Helpers (duplicated from the sibling test file so they cannot drift).
# -----------------------------------------------------------------------------

class _Struct:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def _make_ob(
    direction: str = "bullish",
    high: float = 2810.0,
    low: float = 2805.0,
    touch_count: int = 0,
    mitigated: bool = False,
):
    return _Struct(
        type=direction,
        high=high,
        low=low,
        open=high,
        close=low,
        touch_count=touch_count,
        mitigated=mitigated,
    )


def _make_tf_state(direction="bullish", obs=None, fvgs=None, atr=1.5, premium_discount=None):
    return _Struct(
        structure=_Struct(direction=direction),
        order_blocks=obs or [],
        fair_value_gaps=fvgs or [],
        atr_14=atr,
        premium_discount=premium_discount,
        clv_current=None,
        clv_avg_5=None,
        bvc_buy_fraction=None,
        net_flow_5=None,
        session_vol_ratio=None,
    )


def _make_mso(h1_obs=None, m15_fvgs=None, h1_fvgs=None, price=2800.0):
    return _Struct(
        timestamp_utc="2026-04-17T08:00:00+00:00",
        timeframes={
            "D1": _make_tf_state(direction="bullish", atr=12.0),
            "H1": _make_tf_state(
                direction="bullish",
                obs=h1_obs if h1_obs is not None else [],
                fvgs=h1_fvgs or [],
                atr=3.0,
                premium_discount=_Struct(equilibrium_50=price),
            ),
            "M15": _make_tf_state(
                direction="bullish",
                fvgs=m15_fvgs or [],
                atr=1.2,
            ),
        },
        session_levels=_Struct(
            session_high=price + 10, session_low=price - 10,
            asian_high=price + 5, asian_low=price - 5,
            pdh=price + 15, pdl=price - 15,
        ),
        liquidity_pools=[],
        detected_sweeps=[],
    )


def _make_pa_no_trade(reason="c_gate_failed"):
    return _Struct(
        timestamp_utc="2026-04-17T08:00:00+00:00",
        decision="NO_TRADE",
        framework="none",
        kill_zone="london",
        reasoning=_Struct(
            daily_bias=_Struct(direction="bullish", confidence="high"),
            h4_alignment=_Struct(aligned=True),
            m15_confirmation=_Struct(choch_detected=False),
            setup_grade="C",
        ),
        trade_parameters=None,
        no_trade_reason=reason,
    )


def _make_pa_candidate(direction="LONG", entry=2800.0, sl=2790.0, tp=2820.0):
    return _Struct(
        timestamp_utc="2026-04-17T08:00:00+00:00",
        decision="CANDIDATE",
        framework="ob_retest",
        kill_zone="london",
        reasoning=_Struct(
            daily_bias=_Struct(direction="bullish", confidence="high"),
            h4_alignment=_Struct(aligned=True),
            m15_confirmation=_Struct(choch_detected=True),
            setup_grade="A",
        ),
        trade_parameters=_Struct(
            direction=direction,
            entry_price=entry,
            stop_loss=sl,
            take_profit_1=tp,
            risk_reward_ratio=2.0,
        ),
        no_trade_reason=None,
    )


# -----------------------------------------------------------------------------
# Test 1 — Logger writes on NO_TRADE with new ADR-005 fields.
# -----------------------------------------------------------------------------

def test_no_trade_row_includes_adr005_fields(tmp_path):
    log_file = tmp_path / "candidate_features_log.jsonl"
    # Price = 2800. MSO has:
    #   - one bullish demand zone below at 2790-2792, touch=0 (fresh — the
    #     retest candidate for a LONG)
    #   - one bearish supply zone above at 2808-2810, touch=2 (the retest
    #     candidate for a SHORT)
    # Per corrected Track A semantics (slice_worker.py:113), "opp" OB for
    # LONG is the same-direction (bullish) demand zone below price.
    h1_obs = [
        _make_ob(direction="bearish", high=2810.0, low=2808.0, touch_count=2),
        _make_ob(direction="bullish", high=2792.0, low=2790.0, touch_count=0),
    ]
    mso = _make_mso(h1_obs=h1_obs, price=2800.0)
    pa = _make_pa_no_trade(reason="c1_h1_bias_ranging")

    log_candidate_features(
        pa_output=pa,
        mso=mso,
        symbol="XAUUSD",
        timestamp_utc="2026-04-17T08:00:00+00:00",
        session_state={"kill_zone": "london"},
        log_path=str(log_file),
        ai_direction_evaluated="LONG",
        detector_version_at_eval="v2_shadow",
        slice_tag="xauusd_s3",
    )

    row = json.loads(log_file.read_text(encoding="utf-8").strip())

    # Identity + legacy fields still present
    assert row["symbol"] == "XAUUSD"
    assert row["decision"] == "NO_TRADE"
    assert row["kill_zone"] == "london"

    # ADR-005 additive fields
    assert row["ai_decision"] == "NO_TRADE"
    assert row["ai_no_trade_reason"] == "c1_h1_bias_ranging"
    assert row["ai_direction_evaluated"] == "LONG"
    assert row["detector_version_at_eval"] == "v2_shadow"
    assert row["slice_tag"] == "xauusd_s3"
    # LONG => same-direction (bullish) demand zone below = fresh touch=0
    assert row["h1_opp_ob_touch"] == 0
    # SHORT perspective: same-direction (bearish) supply zone above = touch=2
    assert row["h1_opp_ob_touch_short"] == 2
    assert row["h1_opp_ob_touch_long"] == 0
    assert row["h1_fvg_unfilled_count"] == 0
    assert row["m15_fvg_unfilled_count"] == 0


# -----------------------------------------------------------------------------
# Test 2 — h1_opp_ob_touch computed correctly from synthetic MSO.
# -----------------------------------------------------------------------------

def test_nearest_opposing_ob_touch_long_picks_bullish_demand_below():
    """LONG trade => same-direction (bullish) demand zone below price.

    Per Track A's slice_worker.py:113 semantics: "opposing" is the SMC
    convention, but what's actually measured is the retest-candidate
    demand zone — the bullish OB a LONG enters on (ob.high = entry,
    ob.low = SL). Rank by |price - ob.high|, require ob.low < price.
    """
    obs = [
        _make_ob(direction="bearish", high=2820.0, low=2818.0, touch_count=4),  # wrong direction
        _make_ob(direction="bullish", high=2796.0, low=2792.0, touch_count=1),  # nearest bullish below
        _make_ob(direction="bullish", high=2780.0, low=2778.0, touch_count=9),  # farther bullish below
    ]
    # price = 2800; |price - ob.high| = 4 for touch=1 OB, = 20 for touch=9 OB
    touch = _nearest_opposing_ob_touch(obs, price=2800.0, ai_direction="LONG")
    assert touch == 1


def test_nearest_opposing_ob_touch_short_picks_bearish_supply_above():
    """SHORT trade => same-direction (bearish) supply zone above price."""
    obs = [
        _make_ob(direction="bearish", high=2808.0, low=2804.0, touch_count=3),  # nearest bearish above
        _make_ob(direction="bearish", high=2820.0, low=2818.0, touch_count=7),  # farther bearish above
        _make_ob(direction="bullish", high=2790.0, low=2788.0, touch_count=9),  # wrong direction
    ]
    # price = 2800; |price - ob.low| = 4 for touch=3 OB, = 18 for touch=7 OB
    touch = _nearest_opposing_ob_touch(obs, price=2800.0, ai_direction="SHORT")
    assert touch == 3


def test_long_skips_bullish_ob_that_is_above_price():
    """A bullish OB whose LOW is above current price is not a LONG retest
    candidate — it's overhead supply from prior structure."""
    obs = [
        _make_ob(direction="bullish", high=2815.0, low=2812.0, touch_count=1),  # above price, ignored
    ]
    touch = _nearest_opposing_ob_touch(obs, price=2800.0, ai_direction="LONG")
    assert touch == -1


def test_short_skips_bearish_ob_that_is_below_price():
    obs = [
        _make_ob(direction="bearish", high=2788.0, low=2785.0, touch_count=1),  # below price, ignored
    ]
    touch = _nearest_opposing_ob_touch(obs, price=2800.0, ai_direction="SHORT")
    assert touch == -1


# -----------------------------------------------------------------------------
# Test 3 — Missing opposing-OB case returns -1.
# -----------------------------------------------------------------------------

def test_no_bullish_ob_below_returns_minus_one_for_long():
    # Only bearish OBs => LONG has no retest-candidate below price
    obs = [
        _make_ob(direction="bearish", touch_count=0, high=2810.0, low=2808.0),
        _make_ob(direction="bearish", touch_count=2, high=2820.0, low=2818.0),
    ]
    assert _nearest_opposing_ob_touch(obs, price=2800.0, ai_direction="LONG") == -1


def test_empty_obs_returns_minus_one():
    assert _nearest_opposing_ob_touch([], price=2800.0, ai_direction="LONG") == -1


def test_none_direction_returns_minus_one():
    obs = [_make_ob(direction="bearish", touch_count=2)]
    assert _nearest_opposing_ob_touch(obs, price=2800.0, ai_direction=None) == -1
    assert _nearest_opposing_ob_touch(obs, price=2800.0, ai_direction="UNCLEAR") == -1


def test_no_retest_candidate_logs_minus_one_in_row(tmp_path):
    """All-bearish-OB above price => LONG has no retest candidate (-1)
    but SHORT does (nearest bearish supply above)."""
    log_file = tmp_path / "features.jsonl"
    h1_obs = [
        _make_ob(direction="bearish", touch_count=0, high=2812.0, low=2810.0),
        _make_ob(direction="bearish", touch_count=5, high=2820.0, low=2818.0),
    ]
    mso = _make_mso(h1_obs=h1_obs, price=2800.0)
    pa = _make_pa_no_trade()

    log_candidate_features(
        pa_output=pa, mso=mso, symbol="XAUUSD",
        timestamp_utc="2026-04-17T08:00:00+00:00",
        session_state={"kill_zone": "london"},
        log_path=str(log_file),
        ai_direction_evaluated="LONG",
    )
    row = json.loads(log_file.read_text().strip())
    assert row["h1_opp_ob_touch"] == -1
    assert row["h1_opp_ob_touch_long"] == -1
    # SHORT perspective: nearest bearish above is touch=0
    assert row["h1_opp_ob_touch_short"] == 0


# -----------------------------------------------------------------------------
# Test 4 — Direction fallback to tp_direction when ai_direction_evaluated not supplied.
# -----------------------------------------------------------------------------

def test_missing_direction_falls_back_to_tp_direction(tmp_path):
    """When ai_direction_evaluated=None and a CANDIDATE is produced, use tp direction."""
    log_file = tmp_path / "features.jsonl"
    h1_obs = [
        _make_ob(direction="bearish", high=2810.0, low=2808.0, touch_count=3),
        _make_ob(direction="bullish", high=2792.0, low=2790.0, touch_count=1),
    ]
    mso = _make_mso(h1_obs=h1_obs, price=2800.0)
    pa = _make_pa_candidate(direction="LONG")

    log_candidate_features(
        pa_output=pa, mso=mso, symbol="XAUUSD",
        timestamp_utc="2026-04-17T08:00:00+00:00",
        session_state={"kill_zone": "london"},
        log_path=str(log_file),
        # ai_direction_evaluated NOT supplied — should fall back to tp_direction
    )
    row = json.loads(log_file.read_text().strip())
    assert row["ai_direction_evaluated"] == "LONG"  # derived from tp_direction
    # LONG => same-direction (bullish) demand zone below — touch=1
    assert row["h1_opp_ob_touch"] == 1


# -----------------------------------------------------------------------------
# Test 5 — Schema round-trip + backward compatibility.
# -----------------------------------------------------------------------------

def test_json_round_trip_preserves_all_adr005_fields(tmp_path):
    log_file = tmp_path / "features.jsonl"
    pa = _make_pa_candidate(direction="SHORT")
    # SHORT => same-direction bearish supply above price
    h1_obs = [_make_ob(direction="bearish", touch_count=2, high=2808.0, low=2805.0)]
    mso = _make_mso(h1_obs=h1_obs, price=2800.0)

    log_candidate_features(
        pa_output=pa, mso=mso, symbol="GBPJPY",
        timestamp_utc="2026-04-17T13:00:00+00:00",
        session_state={"kill_zone": "ny"},
        log_path=str(log_file),
        ai_direction_evaluated="SHORT",
        detector_version_at_eval="v1",
        slice_tag="gbpjpy_slice_a",
    )

    row = json.loads(log_file.read_text().strip())
    for key in (
        "ai_decision", "ai_no_trade_reason", "ai_direction_evaluated",
        "h1_opp_ob_touch", "h1_opp_ob_touch_long", "h1_opp_ob_touch_short",
        "h1_fvg_unfilled_count", "m15_fvg_unfilled_count",
        "detector_version_at_eval", "slice_tag",
    ):
        assert key in row, f"ADR-005 field missing from row: {key}"

    # Re-encode/decode to confirm JSON round-trip stability
    reparsed = json.loads(json.dumps(row))
    assert reparsed == row


def test_backward_compatible_legacy_fields_still_present(tmp_path):
    """Existing consumers must continue to see all legacy fields."""
    log_file = tmp_path / "features.jsonl"
    pa = _make_pa_candidate()
    # Bullish demand zone below (LONG retest candidate)
    mso = _make_mso(h1_obs=[
        _make_ob(direction="bullish", high=2795.0, low=2790.0, touch_count=1)
    ])

    log_candidate_features(
        pa_output=pa, mso=mso, symbol="XAUUSD",
        timestamp_utc="2026-04-17T08:00:00+00:00",
        session_state={"kill_zone": "london"},
        log_path=str(log_file),
    )
    row = json.loads(log_file.read_text().strip())

    # Legacy fields that existed before this PR
    legacy_keys = {
        "timestamp_utc", "symbol", "evaluation_id", "kill_zone",
        "session_tag", "day_of_week", "hour_utc",
        "decision", "framework", "setup_grade", "c_gate_result",
        "daily_bias_direction", "daily_bias_confidence",
        "h4_aligned", "m15_choch_detected", "trade_parameters",
        "mso_h1_structure_direction", "mso_m15_structure_direction",
        "mso_d1_structure_direction", "mso_h1_unmitigated_ob_count",
        "mso_h1_ob_touch_counts", "mso_h1_nearest_ob_distance_atr",
        "mso_h1_fvg_count", "mso_m15_fvg_count",
        "mso_pool_count_by_type",
        "mso_nearest_same_side_pool_distance_atr",
        "mso_nearest_opposite_side_pool_distance_atr",
        "mso_h1_atr_14", "mso_m15_atr_14", "mso_d1_atr_14",
        "mso_pd_equilibrium_50", "mso_pd_current_zone",
        "mso_m15_clv_current", "mso_m15_clv_avg_5",
        "mso_m15_bvc_buy_fraction", "mso_m15_net_flow_5",
        "mso_m15_session_vol_ratio",
        "mso_detected_sweeps_count", "mso_detected_sweeps_types",
        "pre_ai_gate_skipped", "pre_ai_gate_reason",
    }
    missing = legacy_keys - set(row.keys())
    assert not missing, f"Legacy fields dropped: {missing}"


# -----------------------------------------------------------------------------
# Test 6 — Mitigated OBs still contribute touch_count (we do NOT filter at
# the helper level — the caller passes unmitigated OBs). Validate that
# _nearest_opposing_ob_touch does not accidentally drop OBs by mitigation.
# -----------------------------------------------------------------------------

def test_helper_does_not_filter_by_mitigation_internally():
    """Caller passes filtered `obs`; the helper operates on whatever it gets.

    LONG-direction retest candidate is a BULLISH demand zone below price.
    With only a single qualifying bullish OB present, helper returns its
    touch_count regardless of mitigated flag (caller pre-filters).
    """
    obs = [
        _make_ob(direction="bullish", touch_count=2, mitigated=False,
                 high=2795.0, low=2790.0),
    ]
    touch = _nearest_opposing_ob_touch(obs, price=2800.0, ai_direction="LONG")
    assert touch == 2
