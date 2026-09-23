from pathlib import Path

from build_lane03_historical_candidate_reconstruction import (
    RESULT_USE_STATUS,
    RUNTIME_EFFECT_BOUNDARY,
    SourceSpec,
    build_event_row,
    classify_row,
    mechanism_family_for,
)


def spec(row_family: str = "candidate_generation") -> SourceSpec:
    return SourceSpec(
        source_id="unit_source",
        path=Path("shadow_logs/unit_source.jsonl"),
        category="full_replay",
        row_family=row_family,
        source_use_state="consumed_projection_source",
        evidence_class="historical_mechanical_replay_projection",
        asof_status="asof_replay_projection",
    )


def test_mechanism_mapping_covers_prompt_families() -> None:
    assert mechanism_family_for({"framework": "ob_retest"}, spec()) == "ob_retest"
    assert mechanism_family_for({"source_origin": "fair_value_gap fvg_fill"}, spec()) == "fvg_fill"
    assert mechanism_family_for({"setup_family": "breaker re-entry"}, spec()) == "breaker_re_entry"
    assert mechanism_family_for({"origin_family": "liquidity_sweep_reclaim"}, spec()) == "liquidity_sweep_reclaim"
    assert mechanism_family_for({"mechanism": "failed_displacement"}, spec()) == "failed_displacement"
    assert mechanism_family_for({"mechanism": "session_open_range break"}, spec()) == "session_flow_continuation"
    assert mechanism_family_for({"decision": "inverse avoid veto"}, spec()) == "inverse_avoid"


def test_classification_keeps_projection_and_lifecycle_classes() -> None:
    classes = classify_row(
        {
            "candidate_id": "C1",
            "decision": "accepted selected",
            "simulated_r": 1.25,
        },
        spec("candidate_generation"),
    )
    assert "raw generated" in classes
    assert "selected" in classes
    assert "accepted" in classes
    assert "projection-only" in classes

    missed = classify_row({"event": "missed_opportunity no_entry skipped"}, spec("missed_opportunity"))
    assert "missed opportunity" in missed
    assert "no-entry" in missed
    assert "skipped" in missed


def test_event_row_has_canonical_ids_boundaries_and_r_state() -> None:
    event = build_event_row(
        {
            "candidate_id": "C1",
            "symbol": "XAUUSD",
            "side": "LONG",
            "session": "london",
            "framework": "ob_retest",
            "candidate_time_utc": "2026-05-01T10:00:00Z",
            "simulated_r": "2.5",
            "decision": "accepted",
        },
        spec(),
        12,
    )
    assert event["canonical_event_id"].startswith("lane03_evt_")
    assert event["canonical_candidate_id"].startswith("lane03_cand_")
    assert event["canonical_duplicate_key"].startswith("lane03_dup_")
    assert event["runtime_effect_boundary"] == RUNTIME_EFFECT_BOUNDARY
    assert event["result_use_status"] == RESULT_USE_STATUS
    assert event["r_source_state"] == "proxy_r_available"
    assert event["proxy_r"] == 2.5
    assert event["exact_r"] is None


def test_exact_r_field_takes_precedence_over_proxy_r() -> None:
    event = build_event_row(
        {
            "candidate_id": "C2",
            "symbol": "GBPJPY",
            "side": "SHORT",
            "framework": "breaker",
            "candidate_time_utc": "2026-05-02T11:00:00Z",
            "simulated_r": "1.0",
            "broker_r": "-0.4",
        },
        spec(),
        99,
    )
    assert event["mechanism_family"] == "breaker_re_entry"
    assert event["r_source_state"] == "exact_r_available"
    assert event["exact_r"] == -0.4
    assert event["proxy_r"] == 1.0
