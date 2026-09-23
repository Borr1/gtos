"""Behavioral tests for the Wave 21 geometry-bound outcome calibration model.

The hand-count fixture pins the exact Jeffreys arithmetic the preregistration
declares; the acceptance tests drive the real disposition function in both
directions -- a fully valid packet is accepted end-to-end, and every broken
atom (geometry hash, artifact sha, cell support, tampered counts, decision
atoms) refuses fail-closed.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from src.research_infra.geometry_bound_outcome_model import (
    CONDITIONAL_ENDPOINT,
    EVALUATED_STATUS,
    HIERARCHY_LEVELS,
    OUT_OF_SUPPORT_STATUS,
    PRIMARY_EVIDENCE_CLASS,
    REASON_DECISION_ATOMS_INVALID,
    REASON_MODEL_ARTIFACT_SHA_MISMATCH,
    REASON_MODEL_ARTIFACT_UNVERIFIED,
    REASON_OUT_OF_SUPPORT,
    REASON_PACKET_HASH_INVALID,
    REASON_STALE_GEOMETRY,
    REASON_SUPPORT_BELOW_MINIMUM,
    SUPPORTED_MODEL_VERSION,
    build_geometry_bound_outcome_calibration_packet,
    canonical_payload_sha256,
    fit_geometry_bound_outcome_model,
    load_geometry_bound_outcome_model,
    validate_geometry_bound_outcome_calibration_packet,
)
from src.research_infra.wave21_full_flow_truth import (
    GEOMETRY_BOUND_OUTCOME_ACCEPTED_REASON,
    GEOMETRY_BOUND_OUTCOME_ACCEPTED_STATUS,
    PROBABILITY_TRUTH_STATUS,
    geometry_bound_outcome_calibration_disposition,
    is_preserved_geometry_bound_outcome_calibration,
    strip_probability_economic_authority,
)

_REPO = Path(__file__).resolve().parents[2]
_PREREGISTRATION = json.loads(
    (
        _REPO
        / "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence"
        / "outcome_authority/OUTCOME_AUTHORITY_PREREGISTRATION_V1.json"
    ).read_text(encoding="utf-8")
)
_LIMIT_FAMILIES = ("current_breaker_re_entry", "current_fvg_fill", "current_ob_retest")


def _row(
    key: str,
    day: str,
    family: str,
    session: str,
    status: str,
    *,
    net: float | None = None,
) -> dict:
    order_type = "LIMIT" if family in _LIMIT_FAMILIES else "MARKET"
    resolved = status.startswith("RESOLVED")
    row = {
        "candidate_occurrence_key": key,
        "trading_day": day,
        "evidence_class": PRIMARY_EVIDENCE_CLASS,
        "proposed_order_type": order_type,
        "origin_family": family,
        "utc_session": session,
        "candidate_source_safe_fingerprint_sha256": "1" * 64,
        "proposed_order_policy_hash_sha256": "2" * 64,
        "geometry_contract_hash_sha256": "3" * 64,
        "arm_id": "TEST_ARM",
        "source_manifest_hash_sha256": "4" * 64,
        "lifecycle_label_status": status,
        "cost_label_status": (
            "NOT_APPLICABLE_NO_FILL"
            if status == "RESOLVED_NO_FILL"
            else "COMPLETE"
            if resolved
            else "INCOMPLETE_OTHER_EXPLICIT_REASON"
        ),
        "label_span_status": "measured" if resolved else "censored",
        "label_span_start_utc": f"{day}T10:00:00+00:00" if resolved else None,
        "label_span_end_utc": f"{day}T12:00:00+00:00" if resolved else None,
        "label_available_utc": f"{day}T12:00:00+00:00" if resolved else None,
    }
    if resolved and status != "RESOLVED_NO_FILL":
        row["terminal_net_r"] = net if net is not None else 1.0
    return row


def _hand_count_corpus() -> tuple[dict[str, list[dict]], list[dict]]:
    """Two-day corpus with one hand-countable LIMIT cell and one MARKET cell.

    LIMIT current_fvg_fill/london totals: 120 resolved attempts =
    40 NO_FILL + 80 fills (30 TARGET, 40 STOP, 10 TIME_STOP).
    MARKET displacement_continuation/moonshot_h00_01: 140 fills
    (40 TARGET, 70 STOP, 30 TIME_STOP), plus one censored row.
    """

    days = ("2025-12-01", "2025-12-02")
    rows_by_day: dict[str, list[dict]] = {day: [] for day in days}
    counter = 0

    def add(day: str, family: str, session: str, status: str) -> None:
        nonlocal counter
        counter += 1
        rows_by_day[day].append(
            _row(f"occ-{counter:05d}", day, family, session, status)
        )

    limit_plan = (
        ("RESOLVED_NO_FILL", 40),
        ("RESOLVED_FILLED_TARGET", 30),
        ("RESOLVED_FILLED_STOP", 40),
        ("RESOLVED_FILLED_TIME_STOP", 10),
    )
    market_plan = (
        ("RESOLVED_FILLED_TARGET", 40),
        ("RESOLVED_FILLED_STOP", 70),
        ("RESOLVED_FILLED_TIME_STOP", 30),
    )
    for status, count in limit_plan:
        for index in range(count):
            add(days[index % 2], "current_fvg_fill", "london", status)
    for status, count in market_plan:
        for index in range(count):
            add(days[index % 2], "displacement_continuation", "moonshot_h00_01", status)
    add(days[0], "displacement_continuation", "moonshot_h00_01", "CENSORED_SOURCE_INTERVAL_GAP")

    corpus_days = [
        {
            "trading_day": day,
            "window_id": "test_window",
            "compact_root": f"/tmp/fixture/{day}",
            "authority_root_sha256": "5" * 64,
            "source_manifest_root_sha256": "6" * 64,
        }
        for day in days
    ]
    return rows_by_day, corpus_days


@pytest.fixture(scope="module")
def fitted_model() -> dict:
    rows_by_day, corpus_days = _hand_count_corpus()
    return fit_geometry_bound_outcome_model(
        rows_by_day,
        corpus_days=corpus_days,
        limit_origin_families=_LIMIT_FAMILIES,
        preregistration=_PREREGISTRATION,
        created_utc="2026-08-11T00:00:00Z",
    )


def _cell(model: dict, level_name: str, **key: str) -> dict:
    for cell in model["final_fit"]["cells"]:
        if cell["hierarchy_level"] == level_name and cell["key"] == key:
            return cell
    raise AssertionError(f"cell not found: {level_name} {key}")


def test_hand_count_jeffreys_arithmetic_is_exact(fitted_model: dict) -> None:
    cell = _cell(
        fitted_model,
        HIERARCHY_LEVELS[2],
        proposed_order_type="LIMIT",
        origin_family="current_fvg_fill",
        utc_session="london",
    )
    assert cell["counts"] == {
        "resolved_attempts": 120,
        "resolved_fills": 80,
        "no_fill": 40,
        "target": 30,
        "stop": 40,
        "time_stop": 10,
    }
    # Beta(1/2,1/2): (2*80+1)/(2*120+2) and (2*40+1)/(2*120+2).
    assert cell["p_modelled_fill_given_resolved"]["numerator"] == 161
    assert cell["p_modelled_fill_given_resolved"]["denominator"] == 242
    assert cell["p_modelled_no_fill_given_resolved"]["numerator"] == 81
    assert cell["p_modelled_no_fill_given_resolved"]["denominator"] == 242
    # Dirichlet(1/2,1/2,1/2): denominator 2*80+3 = 163.
    terminal = cell["p_terminal_given_resolved_fill"]
    assert terminal["TARGET"]["numerator"] == 61
    assert terminal["STOP"]["numerator"] == 81
    assert terminal["TIME_STOP"]["numerator"] == 21
    assert all(terminal[state]["denominator"] == 163 for state in terminal)
    assert sum(terminal[state]["numerator"] for state in terminal) == 163
    # Restricted Beta endpoint: (2*30+1)/(2*(30+40)+2) = 61/142.
    strict = cell["p_target_before_stop_given_filled_terminal_target_or_stop"]
    assert strict["numerator"] == 61
    assert strict["denominator"] == 142
    assert strict["value"] == 61 / 142
    assert cell["fill_probability_status"] == EVALUATED_STATUS
    assert cell["terminal_probability_status"] == EVALUATED_STATUS

    market = _cell(
        fitted_model,
        HIERARCHY_LEVELS[2],
        proposed_order_type="MARKET",
        origin_family="displacement_continuation",
        utc_session="moonshot_h00_01",
    )
    assert market["counts"]["resolved_fills"] == 140
    assert market["p_modelled_fill_given_resolved"] == {
        "numerator": 1,
        "denominator": 1,
        "value": 1.0,
    }
    market_strict = market[
        "p_target_before_stop_given_filled_terminal_target_or_stop"
    ]
    assert market_strict["numerator"] == 81  # 2*40+1
    assert market_strict["denominator"] == 222  # 2*(40+70)+2
    totals = fitted_model["training_corpus"]["totals"]
    assert totals["all_occurrences"] == 261
    assert totals["censored_by_reason"] == {"CENSORED_SOURCE_INTERVAL_GAP": 1}


def test_fitter_refuses_wrong_preregistration() -> None:
    rows_by_day, corpus_days = _hand_count_corpus()
    tampered = dict(_PREREGISTRATION)
    tampered["objective"] = {"primary_question": "tampered"}
    with pytest.raises(ValueError, match="payload_sha256"):
        fit_geometry_bound_outcome_model(
            rows_by_day,
            corpus_days=corpus_days,
            limit_origin_families=_LIMIT_FAMILIES,
            preregistration=tampered,
            created_utc="2026-08-11T00:00:00Z",
        )


def test_prequential_report_is_day_ordered_and_paired(fitted_model: dict) -> None:
    evaluation = fitted_model["prequential_evaluation"]
    days = [entry["trading_day"] for entry in evaluation["days"]]
    assert days == ["2025-12-01", "2025-12-02"]
    first, second = evaluation["days"]
    # Day 1 has no prior data: everything strict is out of support.
    assert first["training_rows_admitted"] == 0
    assert first["strict_scored_rows"] == 0
    assert first["strict_out_of_support_rows"] == first["strict_target_or_stop_rows"]
    # Day 2 trains on day 1 only and scores what its tables support.
    assert second["training_rows_admitted"] > 0
    assert second["strict_scored_rows"] > 0
    strict = evaluation["strict_endpoint"]
    assert strict["endpoint"] == CONDITIONAL_ENDPOINT
    assert strict["scored_rows"] == second["strict_scored_rows"]
    assert strict["brier"] is not None
    assert strict["base_rate_brier"] is not None
    assert evaluation["training_leakage_audit"]["clean"] is True
    for bin_row in strict["reliability_by_predicted_decile"]:
        assert bin_row["count"] > 0
        assert 0.0 <= bin_row["observed_frequency"] <= 1.0


def _model_file(tmp_path: Path, model: dict) -> tuple[Path, str]:
    path = tmp_path / "model.json"
    path.write_text(
        json.dumps(model, indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def _valid_packet(model: dict, artifact_sha: str) -> dict:
    return build_geometry_bound_outcome_calibration_packet(
        model,
        origin_family="current_fvg_fill",
        utc_session="london",
        decision_action="LONG",
        decision_time_utc="2026-05-14T00:00:00+00:00",
        outcome_horizon_utc="2026-05-14T02:00:00+00:00",
        geometry_contract_hash_sha256="e" * 64,
        model_artifact_sha256=artifact_sha,
    )


def test_loader_verifies_file_sha_and_payload_seal(
    tmp_path: Path, fitted_model: dict
) -> None:
    path, file_sha = _model_file(tmp_path, fitted_model)
    model, observed = load_geometry_bound_outcome_model(
        path, expected_artifact_sha256=file_sha
    )
    assert observed == file_sha
    assert model["model_version"] == SUPPORTED_MODEL_VERSION

    with pytest.raises(ValueError, match="sha256 mismatch"):
        load_geometry_bound_outcome_model(
            path, expected_artifact_sha256="f" * 64
        )

    tampered = copy.deepcopy(fitted_model)
    tampered["final_fit"]["cells"][0]["counts"]["target"] += 1
    tampered_path = tmp_path / "tampered.json"
    tampered_path.write_text(
        json.dumps(tampered, indent=2, sort_keys=True), encoding="utf-8"
    )
    tampered_sha = hashlib.sha256(tampered_path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="payload_sha256 mismatch"):
        load_geometry_bound_outcome_model(
            tampered_path, expected_artifact_sha256=tampered_sha
        )


def test_packet_builder_emits_every_required_atom(
    tmp_path: Path, fitted_model: dict
) -> None:
    _path, file_sha = _model_file(tmp_path, fitted_model)
    packet = _valid_packet(fitted_model, file_sha)
    assert packet["probability_status"] == EVALUATED_STATUS
    assert packet["model_version"] == SUPPORTED_MODEL_VERSION
    assert packet["model_artifact_sha256"] == file_sha
    assert packet["model_payload_sha256"] == fitted_model["payload_sha256"]
    assert packet["geometry_contract_hash_sha256"] == "e" * 64
    assert packet["decision_action"] == "LONG"
    assert packet["endpoint"] == CONDITIONAL_ENDPOINT
    strict = packet["p_target_before_stop_given_filled_terminal_target_or_stop"]
    assert (strict["numerator"], strict["denominator"]) == (61, 142)
    assert packet["terminal_given_fill"]["hierarchy_level"] == HIERARCHY_LEVELS[2]
    assert packet["execution_and_censor_masses"] == {
        "no_fill_is_execution_mass_not_loss": True,
        "time_stop_is_separate_terminal_mass_not_loss": True,
        "censored_rows_are_coverage_masses_not_losses": True,
    }
    payload = dict(packet)
    claimed = payload.pop("packet_hash_sha256")
    assert canonical_payload_sha256(payload) == claimed
    assert (
        validate_geometry_bound_outcome_calibration_packet(
            packet,
            geometry_contract_hash_sha256="e" * 64,
            expected_model_artifact_sha256=file_sha,
        )
        == []
    )


def test_unknown_family_backs_off_to_order_type_root(
    tmp_path: Path, fitted_model: dict
) -> None:
    _path, file_sha = _model_file(tmp_path, fitted_model)
    packet = build_geometry_bound_outcome_calibration_packet(
        fitted_model,
        origin_family="never_seen_family",
        utc_session="london",
        decision_action="SHORT",
        decision_time_utc="2026-05-14T00:00:00+00:00",
        outcome_horizon_utc="2026-05-14T02:00:00+00:00",
        geometry_contract_hash_sha256="e" * 64,
        model_artifact_sha256=file_sha,
    )
    assert packet["probability_status"] == EVALUATED_STATUS
    assert packet["cell"]["proposed_order_type"] == "MARKET"
    assert packet["terminal_given_fill"]["hierarchy_level"] == HIERARCHY_LEVELS[0]


def test_out_of_support_cell_is_refused_never_defaulted(tmp_path: Path) -> None:
    rows_by_day = {
        "2025-12-01": [
            _row(f"tiny-{index}", "2025-12-01", "displacement_continuation", "tokyo",
                 "RESOLVED_FILLED_STOP")
            for index in range(20)
        ]
    }
    corpus_days = [
        {
            "trading_day": "2025-12-01",
            "window_id": "test_window",
            "compact_root": "/tmp/fixture/tiny",
            "authority_root_sha256": "5" * 64,
            "source_manifest_root_sha256": "6" * 64,
        }
    ]
    tiny = fit_geometry_bound_outcome_model(
        rows_by_day,
        corpus_days=corpus_days,
        limit_origin_families=_LIMIT_FAMILIES,
        preregistration=_PREREGISTRATION,
        created_utc="2026-08-11T00:00:00Z",
    )
    _path, file_sha = _model_file(tmp_path, tiny)
    packet = build_geometry_bound_outcome_calibration_packet(
        tiny,
        origin_family="displacement_continuation",
        utc_session="tokyo",
        decision_action="LONG",
        decision_time_utc="2026-05-14T00:00:00+00:00",
        outcome_horizon_utc="2026-05-14T02:00:00+00:00",
        geometry_contract_hash_sha256="e" * 64,
        model_artifact_sha256=file_sha,
    )
    assert packet["probability_status"] == OUT_OF_SUPPORT_STATUS
    assert (
        packet["support_shortfall_at_order_type_root"][
            "additional_resolved_fills_required"
        ]
        == 10
    )
    assert "p_target_before_stop_given_filled_terminal_target_or_stop" not in packet
    disposition = geometry_bound_outcome_calibration_disposition(
        packet,
        {"packet_hash_sha256": "e" * 64},
        expected_model_artifact_sha256=file_sha,
    )
    assert disposition["status"] == PROBABILITY_TRUTH_STATUS
    assert disposition["reason"] == REASON_OUT_OF_SUPPORT
    assert disposition["economic_authority_allowed"] is False


def test_disposition_accepts_only_the_fully_bound_packet(
    tmp_path: Path, fitted_model: dict
) -> None:
    _path, file_sha = _model_file(tmp_path, fitted_model)
    packet = _valid_packet(fitted_model, file_sha)
    geometry = {"packet_hash_sha256": "e" * 64}

    accepted = geometry_bound_outcome_calibration_disposition(
        packet, geometry, expected_model_artifact_sha256=file_sha
    )
    assert accepted == {
        "status": GEOMETRY_BOUND_OUTCOME_ACCEPTED_STATUS,
        "reason": GEOMETRY_BOUND_OUTCOME_ACCEPTED_REASON,
        "source_required_field": "geometry_bound_outcome_calibration",
        "economic_authority_allowed": True,
    }

    stale = geometry_bound_outcome_calibration_disposition(
        packet,
        {"packet_hash_sha256": "f" * 64},
        expected_model_artifact_sha256=file_sha,
    )
    assert stale["status"] == PROBABILITY_TRUTH_STATUS
    assert stale["reason"] == REASON_STALE_GEOMETRY
    assert stale["economic_authority_allowed"] is False

    unverified = geometry_bound_outcome_calibration_disposition(packet, geometry)
    assert unverified["reason"] == REASON_MODEL_ARTIFACT_UNVERIFIED
    assert unverified["economic_authority_allowed"] is False

    mismatched = geometry_bound_outcome_calibration_disposition(
        packet, geometry, expected_model_artifact_sha256="f" * 64
    )
    assert mismatched["reason"] == REASON_MODEL_ARTIFACT_SHA_MISMATCH
    assert mismatched["economic_authority_allowed"] is False

    tampered = copy.deepcopy(packet)
    tampered["terminal_given_fill"]["counts"]["target"] += 1
    tampered_disposition = geometry_bound_outcome_calibration_disposition(
        tampered, geometry, expected_model_artifact_sha256=file_sha
    )
    assert tampered_disposition["reason"] == REASON_PACKET_HASH_INVALID
    assert tampered_disposition["economic_authority_allowed"] is False


def test_disposition_refuses_low_support_and_bad_decision_atoms(
    tmp_path: Path, fitted_model: dict
) -> None:
    _path, file_sha = _model_file(tmp_path, fitted_model)
    geometry = {"packet_hash_sha256": "e" * 64}

    low_support = copy.deepcopy(_valid_packet(fitted_model, file_sha))
    low_support["terminal_given_fill"]["counts"] = {
        "resolved_fills": 29,
        "target": 10,
        "stop": 10,
        "time_stop": 9,
    }
    denominator = 2 * 29 + 3
    low_support["terminal_given_fill"]["p_terminal_given_resolved_fill"] = {
        "TARGET": {"numerator": 21, "denominator": denominator, "value": 21 / denominator},
        "STOP": {"numerator": 21, "denominator": denominator, "value": 21 / denominator},
        "TIME_STOP": {"numerator": 19, "denominator": denominator, "value": 19 / denominator},
    }
    low_support["p_target_before_stop_given_filled_terminal_target_or_stop"] = {
        "numerator": 21,
        "denominator": 42,
        "value": 0.5,
    }
    low_support.pop("packet_hash_sha256")
    low_support["packet_hash_sha256"] = canonical_payload_sha256(low_support)
    refused = geometry_bound_outcome_calibration_disposition(
        low_support, geometry, expected_model_artifact_sha256=file_sha
    )
    assert refused["reason"] == REASON_SUPPORT_BELOW_MINIMUM
    assert refused["economic_authority_allowed"] is False

    bad_horizon = build_geometry_bound_outcome_calibration_packet(
        fitted_model,
        origin_family="current_fvg_fill",
        utc_session="london",
        decision_action="LONG",
        decision_time_utc="2026-05-14T02:00:00+00:00",
        outcome_horizon_utc="2026-05-14T00:00:00+00:00",
        geometry_contract_hash_sha256="e" * 64,
        model_artifact_sha256=file_sha,
    )
    refused = geometry_bound_outcome_calibration_disposition(
        bad_horizon, geometry, expected_model_artifact_sha256=file_sha
    )
    assert refused["reason"] == REASON_DECISION_ATOMS_INVALID
    assert refused["economic_authority_allowed"] is False


def test_legacy_disposition_behavior_is_unchanged() -> None:
    empty = geometry_bound_outcome_calibration_disposition({}, {})
    assert empty["reason"].endswith("source_required")
    bare = geometry_bound_outcome_calibration_disposition(
        {"geometry_contract_hash_sha256": "a" * 64},
        {"packet_hash_sha256": "a" * 64},
    )
    assert bare["reason"].endswith("model_version_unsupported")
    assert bare["economic_authority_allowed"] is False


def test_strip_preserves_only_the_validated_accepted_wrapper(
    tmp_path: Path, fitted_model: dict
) -> None:
    _path, file_sha = _model_file(tmp_path, fitted_model)
    packet = _valid_packet(fitted_model, file_sha)
    disposition = geometry_bound_outcome_calibration_disposition(
        packet,
        {"packet_hash_sha256": "e" * 64},
        expected_model_artifact_sha256=file_sha,
    )
    wrapper = {"packet": packet, "disposition": disposition}
    assert is_preserved_geometry_bound_outcome_calibration(wrapper) is True

    surface = {
        "geometry_bound_outcome_calibration": wrapper,
        "probability": 0.9,
        "candidate_ev_r": 1.0,
    }
    stripped = strip_probability_economic_authority(surface)
    assert stripped["geometry_bound_outcome_calibration"] == wrapper
    assert "probability" not in stripped
    assert "candidate_ev_r" not in stripped

    tampered = copy.deepcopy(wrapper)
    tampered["packet"]["decision_action"] = "SHORT"
    assert is_preserved_geometry_bound_outcome_calibration(tampered) is False
    stripped = strip_probability_economic_authority(
        {"geometry_bound_outcome_calibration": tampered}
    )
    assert stripped == {}

    refused_wrapper = {
        "packet": packet,
        "disposition": {
            "status": PROBABILITY_TRUTH_STATUS,
            "reason": REASON_OUT_OF_SUPPORT,
            "source_required_field": "geometry_bound_outcome_calibration",
            "economic_authority_allowed": False,
        },
    }
    assert is_preserved_geometry_bound_outcome_calibration(refused_wrapper) is False
    assert strip_probability_economic_authority(
        {"geometry_bound_outcome_calibration": refused_wrapper}
    ) == {}
