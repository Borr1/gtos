"""Tests for the frozen segment exit-policy table loader/resolver and the
default-off router branch that consumes a resolution.

The router branch must be purely additive: events without
``segment_policy_resolution`` produce byte-identical decisions.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.research.moonshot_default_off_policy_router import (
    DEFAULT_POLICY,
    EXECUTION_POLICY_IDS,
    SEGMENT_EXIT_POLICY_FAMILY_TO_LIVE_POLICY,
    SUPPORTED_LIVE_EXECUTION_POLICIES,
    route_moonshot_dynamic_execution,
)
from src.research.moonshot_segment_exit_policy_table import (
    GLOBAL_DEFAULT_FALLBACK_LEVEL,
    SEGMENT_TABLE_SCHEMA_VERSION,
    SESSION_VOCABULARY_UNMAPPED_FALLBACK_LEVEL,
    load_segment_policy_table,
    normalize_session_vocabulary,
    resolve_segment_policy,
    segment_table_validation_errors,
)

INCUMBENT_PARAMS = {
    "name": "incumbent",
    "final_target_r": 2.0,
    "trailing_trigger_r": 1.0,
    "trailing_gap_r": 0.4,
}
TRAILING_PARAMS = {
    "name": "trailing_t0p5_g0p35_c6",
    "final_target_r": 6.0,
    "trailing_trigger_r": 0.5,
    "trailing_gap_r": 0.35,
}


def _segment(
    segment_id: str,
    level: str,
    match: dict,
    policy_id: str,
    family: str,
    params: dict,
    promoted: bool,
) -> dict:
    return {
        "segment_id": segment_id,
        "match": match,
        "fallback_level": level,
        "policy_id": policy_id,
        "family": family,
        "params": params,
        "n_trades": 50,
        "n_days": 8,
        "robust_score": 1.0,
        "incumbent_delta_r_per_trade": 0.5,
        "corrected_p": 0.01,
        "promoted": promoted,
        "reasons": [],
    }


def _table_dict() -> dict:
    return {
        "schema_version": SEGMENT_TABLE_SCHEMA_VERSION,
        "default_policy": {
            "policy_id": "incumbent",
            "family": "momentum",
            "params": dict(INCUMBENT_PARAMS),
        },
        "segments": [
            _segment(
                "leaf|jpy_fx|liquidity_sweep_reclaim|tokyo",
                "leaf",
                {
                    "asset_class": "jpy_fx",
                    "origin_family": "liquidity_sweep_reclaim",
                    "session_bucket": "tokyo",
                },
                "trailing_t0p5_g0p35_c6",
                "trailing",
                dict(TRAILING_PARAMS),
                True,
            ),
            _segment(
                "leaf|jpy_fx|fvg_fill|tokyo",
                "leaf",
                {
                    "asset_class": "jpy_fx",
                    "origin_family": "fvg_fill",
                    "session_bucket": "tokyo",
                },
                "fixed_target_3r",
                "fixed_target",
                {"name": "fixed_target_3r", "final_target_r": 3.0},
                False,  # recorded but never routing authority
            ),
            _segment(
                "asset_class_session|jpy_fx|*|london",
                "asset_class_session",
                {
                    "asset_class": "jpy_fx",
                    "origin_family": None,
                    "session_bucket": "london",
                },
                "be_only_t0p75",
                "be_only",
                {"name": "be_only_t0p75", "tp1_r": 0.75, "final_target_r": 2.0},
                True,
            ),
            _segment(
                "asset_class|fx|*|*",
                "asset_class",
                {"asset_class": "fx", "origin_family": None, "session_bucket": None},
                "fixed_target_2p5r",
                "fixed_target",
                {"name": "fixed_target_2p5r", "final_target_r": 2.5},
                True,
            ),
        ],
    }


def _write_table(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "segment_table.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def test_load_valid_table_attaches_sha256(tmp_path: Path) -> None:
    path = _write_table(tmp_path, _table_dict())
    table = load_segment_policy_table(path)
    assert table["schema_version"] == SEGMENT_TABLE_SCHEMA_VERSION
    assert table["table_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_load_sha_pin_match_passes_and_mismatch_fails_closed(tmp_path: Path) -> None:
    path = _write_table(tmp_path, _table_dict())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    table = load_segment_policy_table(path, expected_sha256=digest)
    assert table["table_sha256"] == digest

    with pytest.raises(ValueError, match="sha256_mismatch"):
        load_segment_policy_table(path, expected_sha256="0" * 64)


def test_load_rejects_wrong_schema_version(tmp_path: Path) -> None:
    payload = _table_dict()
    payload["schema_version"] = "exit_policy_segment_table_v999"
    path = _write_table(tmp_path, payload)
    with pytest.raises(ValueError, match="schema_version_mismatch"):
        load_segment_policy_table(path)


def test_load_rejects_malformed_segments(tmp_path: Path) -> None:
    payload = _table_dict()
    del payload["segments"][0]["params"]
    path = _write_table(tmp_path, payload)
    with pytest.raises(ValueError, match="params_not_a_mapping"):
        load_segment_policy_table(path)


def test_validation_errors_on_non_mapping_payload() -> None:
    assert segment_table_validation_errors([1, 2]) == ["table_payload_not_a_mapping"]


# ---------------------------------------------------------------------------
# Resolver hierarchy
# ---------------------------------------------------------------------------

def test_resolver_exact_leaf_match_wins(tmp_path: Path) -> None:
    table = load_segment_policy_table(_write_table(tmp_path, _table_dict()))
    resolution = resolve_segment_policy(
        table,
        asset_class="jpy_fx",
        origin_family="liquidity_sweep_reclaim",
        session_bucket="tokyo",
    )
    assert resolution["promoted"] is True
    assert resolution["fallback_level"] == "leaf"
    assert resolution["policy_id"] == "trailing_t0p5_g0p35_c6"
    assert resolution["params"]["trailing_gap_r"] == 0.35
    assert resolution["table_sha256"] == table["table_sha256"]


def test_resolver_normalizes_origin_prefix(tmp_path: Path) -> None:
    table = load_segment_policy_table(_write_table(tmp_path, _table_dict()))
    resolution = resolve_segment_policy(
        table,
        asset_class="JPY_FX",
        origin_family="origin_liquidity_sweep_reclaim",
        session_bucket="Tokyo",
    )
    assert resolution["policy_id"] == "trailing_t0p5_g0p35_c6"


def test_resolver_skips_unpromoted_leaf_and_falls_to_default(tmp_path: Path) -> None:
    table = load_segment_policy_table(_write_table(tmp_path, _table_dict()))
    resolution = resolve_segment_policy(
        table,
        asset_class="jpy_fx",
        origin_family="fvg_fill",
        session_bucket="tokyo",
    )
    # The fvg_fill leaf row exists but promoted=false; no tokyo session row,
    # no jpy_fx asset-class row, no global row -> incumbent default.
    assert resolution["promoted"] is False
    assert resolution["fallback_level"] == GLOBAL_DEFAULT_FALLBACK_LEVEL
    assert resolution["policy_id"] == "incumbent"
    assert resolution["params"] == INCUMBENT_PARAMS


def test_resolver_walks_to_session_and_asset_class_levels(tmp_path: Path) -> None:
    table = load_segment_policy_table(_write_table(tmp_path, _table_dict()))

    session_level = resolve_segment_policy(
        table,
        asset_class="jpy_fx",
        origin_family="anything_else",
        session_bucket="london",
    )
    assert session_level["fallback_level"] == "asset_class_session"
    assert session_level["policy_id"] == "be_only_t0p75"

    asset_level = resolve_segment_policy(
        table,
        asset_class="fx",
        origin_family="anything",
        session_bucket="ny",
    )
    assert asset_level["fallback_level"] == "asset_class"
    assert asset_level["policy_id"] == "fixed_target_2p5r"

    default = resolve_segment_policy(
        table,
        asset_class="metals",
        origin_family="anything",
        session_bucket="tokyo",
    )
    assert default["fallback_level"] == GLOBAL_DEFAULT_FALLBACK_LEVEL
    assert default["promoted"] is False
    assert default["reason"] is None


# ---------------------------------------------------------------------------
# Session vocabulary normalization (MAJOR 1)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("london", "london"),
        ("london_core", "london"),
        ("London Core", "london"),
        ("ny", "ny"),
        ("ny_core", "ny"),
        ("new_york", "ny"),
        ("tokyo", "tokyo"),
        ("tokyo_kz", "tokyo"),
        ("asia", "tokyo"),
        ("off_kz", "off_kz"),
        ("off_core_session", "off_kz"),
        ("off_configured_session", "off_kz"),
        ("moonshot_h06_07", "moonshot_h06_07"),
        ("MOONSHOT_H22_23", "moonshot_h22_23"),
        ("moonshot_hxx_yy", None),
        ("frankfurt", None),
        ("", None),
        (None, None),
    ],
)
def test_normalize_session_vocabulary(raw, expected) -> None:
    assert normalize_session_vocabulary(raw) == expected


def _mixed_vocab_table_dict() -> dict:
    """Frozen table whose session keys mix raw ledger vocabulary and config
    kill-zone vocabulary — both must canonicalize through the single map."""

    payload = _table_dict()
    payload["segments"] = [
        _segment(
            "leaf|jpy_fx|liquidity_sweep_reclaim|tokyo_kz",
            "leaf",
            {
                "asset_class": "jpy_fx",
                "origin_family": "liquidity_sweep_reclaim",
                "session_bucket": "tokyo_kz",  # config vocab in the table
            },
            "trailing_t0p5_g0p35_c6",
            "trailing",
            dict(TRAILING_PARAMS),
            True,
        ),
        _segment(
            "asset_class_session|jpy_fx|*|london_core",
            "asset_class_session",
            {
                "asset_class": "jpy_fx",
                "origin_family": None,
                "session_bucket": "london_core",  # config vocab in the table
            },
            "be_only_t0p75",
            "be_only",
            {"name": "be_only_t0p75", "tp1_r": 0.75, "final_target_r": 2.0},
            True,
        ),
        _segment(
            "asset_class_session|fx|*|off_kz",
            "asset_class_session",
            {
                "asset_class": "fx",
                "origin_family": None,
                "session_bucket": "off_kz",  # raw ledger vocab in the table
            },
            "fixed_target_2p5r",
            "fixed_target",
            {"name": "fixed_target_2p5r", "final_target_r": 2.5},
            True,
        ),
        _segment(
            "leaf|fx|fvg_fill|moonshot_h06_07",
            "leaf",
            {
                "asset_class": "fx",
                "origin_family": "fvg_fill",
                "session_bucket": "moonshot_h06_07",  # hourly bucket passthrough
            },
            "fixed_target_3r",
            "fixed_target",
            {"name": "fixed_target_3r", "final_target_r": 3.0},
            True,
        ),
    ]
    return payload


def test_mixed_vocab_table_and_queries_meet_on_canonical_sessions(tmp_path: Path) -> None:
    table = load_segment_policy_table(_write_table(tmp_path, _mixed_vocab_table_dict()))

    # Table 'tokyo_kz' x query 'asia' -> canonical 'tokyo' leaf match.
    leaf = resolve_segment_policy(
        table,
        asset_class="jpy_fx",
        origin_family="liquidity_sweep_reclaim",
        session_bucket="asia",
    )
    assert leaf["fallback_level"] == "leaf"
    assert leaf["policy_id"] == "trailing_t0p5_g0p35_c6"

    # Table 'london_core' x query raw ledger 'london' -> canonical 'london'.
    session_level = resolve_segment_policy(
        table,
        asset_class="jpy_fx",
        origin_family="other",
        session_bucket="london",
    )
    assert session_level["fallback_level"] == "asset_class_session"
    assert session_level["policy_id"] == "be_only_t0p75"

    # Table raw 'off_kz' x query config 'off_configured_session'.
    off_level = resolve_segment_policy(
        table,
        asset_class="fx",
        origin_family="other",
        session_bucket="off_configured_session",
    )
    assert off_level["fallback_level"] == "asset_class_session"
    assert off_level["policy_id"] == "fixed_target_2p5r"

    # moonshot hourly bucket passes through both sides unchanged.
    hourly = resolve_segment_policy(
        table,
        asset_class="fx",
        origin_family="fvg_fill",
        session_bucket="moonshot_h06_07",
    )
    assert hourly["fallback_level"] == "leaf"
    assert hourly["policy_id"] == "fixed_target_3r"


def test_load_time_normalization_rewrites_table_session_keys(tmp_path: Path) -> None:
    table = load_segment_policy_table(_write_table(tmp_path, _mixed_vocab_table_dict()))
    sessions = [
        segment["match"]["session_bucket"]
        for segment in table["segments"]
        if segment["match"].get("session_bucket")
    ]
    assert sessions == ["tokyo", "london", "off_kz", "moonshot_h06_07"]


def test_unknown_session_vocabulary_surfaces_reason_not_global_default(tmp_path: Path) -> None:
    table = load_segment_policy_table(_write_table(tmp_path, _table_dict()))
    resolution = resolve_segment_policy(
        table,
        asset_class="jpy_fx",
        origin_family="liquidity_sweep_reclaim",
        session_bucket="frankfurt_open",
    )
    assert resolution["fallback_level"] == SESSION_VOCABULARY_UNMAPPED_FALLBACK_LEVEL
    assert resolution["promoted"] is False
    assert resolution["policy_id"] == "incumbent"
    assert resolution["params"] == INCUMBENT_PARAMS
    assert (
        resolution["reason"]
        == "session_vocabulary_unmapped_unknown_token_frankfurt_open"
    )


def test_empty_session_vocabulary_surfaces_reason(tmp_path: Path) -> None:
    table = load_segment_policy_table(_write_table(tmp_path, _table_dict()))
    resolution = resolve_segment_policy(
        table,
        asset_class="fx",
        origin_family="fvg_fill",
        session_bucket="",
    )
    assert resolution["fallback_level"] == SESSION_VOCABULARY_UNMAPPED_FALLBACK_LEVEL
    assert resolution["reason"] == "session_vocabulary_unmapped_empty_input"
    assert resolution["policy_id"] == "incumbent"


# ---------------------------------------------------------------------------
# Router branch (purely additive, default-off)
# ---------------------------------------------------------------------------

def _event(**overrides):
    event = {
        "symbol": "GBPJPY",
        "side": "LONG",
        "framework": "fvg_fill",
        "candidate_origin_family": "origin_current_fvg_fill",
        "branch_label": "FOLLOW",
        "activated_frameworks": ["breaker_re_entry", "fvg_fill", "ob_retest"],
        "required_branch_labels": ["FOLLOW"],
        "broker_native_eligible": True,
        "broker_native_exact_excluded": False,
        "session_bucket": "london_broad",
        "kill_zone_position": "in_london_early",
        "source_mode": "OHLC_M15_CSV",
        "source_path_feature_status": "computed_from_source_ohlc_asof",
        "source_window_complete": "True",
        "ordered_path_status": "ordered_path_not_ambiguous_in_m15_replay",
        "current_bar_displacement_atr14": 0.5,
        "remaining_daily_cushion_r": 6.0,
        "remaining_overall_cushion_r": 8.0,
    }
    event.update(overrides)
    return event


def _trailing_resolution(**overrides) -> dict:
    resolution = {
        "promoted": True,
        "policy_id": "trailing_t0p5_g0p35_c6",
        "family": "trailing",
        "segment_id": "leaf|jpy_fx|liquidity_sweep_reclaim|tokyo",
        "fallback_level": "leaf",
        "params": dict(TRAILING_PARAMS),
        "table_sha256": "f" * 64,
    }
    resolution.update(overrides)
    return resolution


def test_router_without_resolution_key_is_byte_identical_noop() -> None:
    baseline = route_moonshot_dynamic_execution(
        _event(), enabled=True, apply_to_execution=True
    )
    with_null_key = route_moonshot_dynamic_execution(
        _event(segment_policy_resolution=None), enabled=True, apply_to_execution=True
    )
    assert baseline.to_record() == with_null_key.to_record()
    assert "segment_exit_policy" not in baseline.route_dimensions
    assert "selected_policy_params" not in baseline.route_dimensions
    assert baseline.selected_policy == DEFAULT_POLICY


def test_router_applies_promoted_trailing_resolution_with_provenance() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(
            segment_policy_resolution=_trailing_resolution(),
            segment_policy_params_consumer_ready=True,
        ),
        enabled=True,
        apply_to_execution=True,
    )
    assert decision.selected_policy == "trailing_runner"
    assert decision.execution_policy_id == EXECUTION_POLICY_IDS["trailing_runner"]

    provenance = decision.route_dimensions["segment_exit_policy"]
    assert provenance["applied"] is True
    assert provenance["application_status"] == "applied"
    assert provenance["not_applied_reason"] is None
    assert provenance["params_consumer_ready"] is True
    assert provenance["promoted"] is True
    assert provenance["policy_id"] == "trailing_t0p5_g0p35_c6"
    assert provenance["mapped_live_policy"] == "trailing_runner"
    assert provenance["segment_id"] == "leaf|jpy_fx|liquidity_sweep_reclaim|tokyo"
    assert provenance["fallback_level"] == "leaf"
    assert provenance["table_sha256"] == "f" * 64
    assert provenance["selected_policy_params"]["trailing_gap_r"] == 0.35
    assert decision.route_dimensions["selected_policy_params"]["trailing_gap_r"] == 0.35
    assert (
        "segment_exit_policy_promoted_tournament_resolution_applied_to_selected_policy"
        in decision.evidence_notes
    )


def test_router_resolution_without_consumer_flag_is_observed_not_applied() -> None:
    """MAJOR 2 gate: a promoted, mappable resolution must stay inert unless
    the caller explicitly asserts execution-side param consumption."""

    decision = route_moonshot_dynamic_execution(
        _event(segment_policy_resolution=_trailing_resolution()),
        enabled=True,
        apply_to_execution=True,
    )
    assert decision.selected_policy == DEFAULT_POLICY
    assert decision.execution_policy_id == EXECUTION_POLICY_IDS[DEFAULT_POLICY]

    provenance = decision.route_dimensions["segment_exit_policy"]
    assert provenance["applied"] is False
    assert provenance["application_status"] == "observed_not_applied"
    assert (
        provenance["not_applied_reason"]
        == "segment_policy_params_consumer_not_ready_exact_params_required"
    )
    assert provenance["params_consumer_ready"] is False
    assert provenance["promoted"] is True
    assert provenance["mapped_live_policy"] == "trailing_runner"
    # Full resolution provenance is still recorded for forensic joins.
    assert provenance["selected_policy_params"]["trailing_gap_r"] == 0.35
    assert "selected_policy_params" not in decision.route_dimensions
    assert (
        "segment_exit_policy_resolution_observed_not_applied_params_consumer_not_ready"
        in decision.evidence_notes
    )
    assert (
        "segment_exit_policy_promoted_tournament_resolution_applied_to_selected_policy"
        not in decision.evidence_notes
    )


def test_router_ignores_unpromoted_resolution_but_keeps_provenance() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(
            segment_policy_resolution=_trailing_resolution(promoted=False),
            segment_policy_params_consumer_ready=True,
        ),
        enabled=True,
        apply_to_execution=True,
    )
    assert decision.selected_policy == DEFAULT_POLICY
    provenance = decision.route_dimensions["segment_exit_policy"]
    assert provenance["applied"] is False
    assert provenance["application_status"] == "observed_not_applied"
    assert provenance["not_applied_reason"] == "resolution_not_promoted"
    assert provenance["promoted"] is False
    assert "selected_policy_params" not in decision.route_dimensions


def test_router_ignores_unmappable_promoted_resolution() -> None:
    decision = route_moonshot_dynamic_execution(
        _event(
            segment_policy_resolution=_trailing_resolution(
                policy_id="zzz_unknown", family="weird_family"
            ),
            segment_policy_params_consumer_ready=True,
        ),
        enabled=True,
        apply_to_execution=True,
    )
    assert decision.selected_policy == DEFAULT_POLICY
    provenance = decision.route_dimensions["segment_exit_policy"]
    assert provenance["applied"] is False
    assert provenance["application_status"] == "observed_not_applied"
    assert provenance["not_applied_reason"] == "no_supported_live_policy_mapping"
    assert provenance["mapped_live_policy"] is None


@pytest.mark.parametrize(
    ("family", "policy_id", "expected_live"),
    [
        ("momentum", "momentum_t1p25_p0p3_c3", "momentum_exhaustion"),
        ("trailing", "trailing_t1_g0p5_c6", "trailing_runner"),
        ("fixed_target", "fixed_target_3r", "be_after_trigger"),
        ("be_only", "be_only_t0p75", "be_after_trigger"),
        ("time_stop", "time_stop_12", "time_stop"),
        (None, "momentum_t1p25_p0p3_c3__abort_a0p4_m0p25", "momentum_exhaustion"),
    ],
)
def test_router_family_mapping(family, policy_id, expected_live) -> None:
    decision = route_moonshot_dynamic_execution(
        _event(
            segment_policy_resolution=_trailing_resolution(
                policy_id=policy_id, family=family
            ),
            segment_policy_params_consumer_ready=True,
        ),
        enabled=True,
        apply_to_execution=True,
    )
    assert decision.selected_policy == expected_live
    assert expected_live in SUPPORTED_LIVE_EXECUTION_POLICIES


def test_family_map_targets_only_supported_live_policies() -> None:
    assert set(SEGMENT_EXIT_POLICY_FAMILY_TO_LIVE_POLICY.values()) <= set(
        SUPPORTED_LIVE_EXECUTION_POLICIES
    )


def test_end_to_end_resolution_from_loaded_table_steers_router(tmp_path: Path) -> None:
    path = _write_table(tmp_path, _table_dict())
    table = load_segment_policy_table(path)
    resolution = resolve_segment_policy(
        table,
        asset_class="jpy_fx",
        origin_family="liquidity_sweep_reclaim",
        session_bucket="tokyo",
    )
    decision = route_moonshot_dynamic_execution(
        _event(
            segment_policy_resolution=resolution,
            segment_policy_params_consumer_ready=True,
        ),
        enabled=True,
        apply_to_execution=True,
    )
    assert decision.selected_policy == "trailing_runner"
    provenance = decision.route_dimensions["segment_exit_policy"]
    assert provenance["applied"] is True
    assert provenance["application_status"] == "applied"
    assert provenance["table_sha256"] == table["table_sha256"]
