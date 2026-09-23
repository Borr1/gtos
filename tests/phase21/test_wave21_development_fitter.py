"""Hand-count and fail-closed tests for the Wave 21 Jeffreys fitter."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence"
    / "probability_truth/probability_truth_analysis.py"
)
PREREG = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence"
    / "outcome_authority/OUTCOME_AUTHORITY_PREREGISTRATION_V1.json"
)
SPEC = importlib.util.spec_from_file_location("wave21_development_fitter", SCRIPT)
assert SPEC and SPEC.loader
FITTER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = FITTER
SPEC.loader.exec_module(FITTER)


def _prereg():
    return json.loads(PREREG.read_text(encoding="utf-8"))


def _row(day: str, index: int, *, order_type: str, state: str, session: str):
    status = {
        "NO_FILL": "RESOLVED_NO_FILL",
        "TARGET": "RESOLVED_FILLED_TARGET",
        "STOP": "RESOLVED_FILLED_STOP",
        "TIME_STOP": "RESOLVED_FILLED_TIME_STOP",
    }[state]
    row = {
        "candidate_occurrence_key": f"{day}:{order_type}:{session}:{index}",
        "candidate_source_safe_fingerprint_sha256": "b" * 64,
        "trading_day": day,
        "evidence_class": FITTER.PRIMARY_EVIDENCE_CLASS,
        "proposed_order_type": order_type,
        "proposed_order_policy_hash_sha256": "c" * 64,
        "geometry_contract_hash_sha256": "d" * 64,
        "arm_id": "development_label",
        "origin_family": "family_a",
        "utc_session": session,
        "symbol": "EURUSD",
        "source_manifest_hash_sha256": "a" * 64,
        "lifecycle_label_status": status,
        "cost_label_status": (
            "NOT_APPLICABLE_NO_FILL" if state == "NO_FILL" else "COMPLETE"
        ),
        "label_span_status": "measured",
        "label_span_start_utc": f"{day}T08:00:00Z",
        "label_span_end_utc": f"{day}T09:00:00Z",
        "label_available_utc": f"{day}T10:00:00Z",
    }
    if state != "NO_FILL":
        row["terminal_net_r"] = {"TARGET": 1.0, "STOP": -1.0, "TIME_STOP": 0.2}[state]
        row["terminal_gross_r"] = row["terminal_net_r"]
    return row


def _estate(*, limit_per_day: int = 60, market_per_day: int = 20):
    rows = []
    for day in FITTER.DEVELOPMENT_DAYS:
        for index in range(limit_per_day):
            session = "asia" if index < 25 else "london"
            state = ("TARGET", "STOP", "TIME_STOP")[index % 3] if index < 40 else "NO_FILL"
            rows.append(
                _row(day, index, order_type="LIMIT", state=state, session=session)
            )
        for index in range(market_per_day):
            state = ("TARGET", "STOP", "TIME_STOP")[index % 3]
            rows.append(
                _row(day, index, order_type="MARKET", state=state, session="asia")
            )
    return rows


def _fit(rows):
    return FITTER.fit_wave21_development(
        rows,
        _prereg(),
        development_freeze_utc="2025-11-08T00:00:00Z",
    )


def _cell(result, level, **key):
    return next(
        row
        for row in result["final_development_fit"]["count_tables"]
        if row["hierarchy_level"] == level and row["key"] == key
    )


def test_hand_count_probabilities_market_exact_backoff_and_cost_denominators():
    rows = _estate()
    result = _fit(rows)

    root = _cell(result, "proposed_order_type", proposed_order_type="LIMIT")
    assert root["counts"]["resolved_attempts"] == 360
    assert root["counts"]["resolved_fills"] == 240
    assert root["p_modelled_fill_given_resolved"] == {
        "numerator": 481,
        "denominator": 722,
        "value": 481 / 722,
    }
    assert root["p_modelled_no_fill_given_resolved"] == {
        "numerator": 241,
        "denominator": 722,
        "value": 241 / 722,
    }
    assert sum(
        value["numerator"]
        for value in root["p_terminal_given_resolved_fill"].values()
    ) == root["p_terminal_given_resolved_fill"]["TARGET"]["denominator"]

    market = _cell(result, "proposed_order_type", proposed_order_type="MARKET")
    assert market["p_modelled_fill_given_resolved"] == {
        "numerator": 1,
        "denominator": 1,
        "value": 1.0,
    }
    assert market["p_modelled_no_fill_given_resolved"] == {
        "numerator": 0,
        "denominator": 1,
        "value": 0.0,
    }

    first = result["expanding_folds"][0]
    assert first["effective_test_start_utc"] == "2025-10-28T21:00:00Z"
    assert first["training_leakage_audit"]["clean"] is True
    assert first["cell_backoff_counts"][
        "fill:proposed_order_type_x_origin_family"
    ] > 0
    assert first["cell_backoff_counts"][
        "terminal:proposed_order_type_x_origin_family_x_utc_session"
    ] > 0
    assert first["expected_net_status_counts"]["OUT_OF_SUPPORT"] >= 20
    market_support = next(
        row for row in first["root_support"] if row["proposed_order_type"] == "MARKET"
    )
    assert market_support["additional_resolved_attempts_required_for_expected_net"] == 60
    assert market["complete_net_r_state_counts"] == {
        "TARGET": 42,
        "STOP": 42,
        "TIME_STOP": 36,
    }

    incomplete = copy.deepcopy(rows)
    victim = next(
        row
        for row in incomplete
        if row["trading_day"] == "2025-10-27"
        and row["proposed_order_type"] == "LIMIT"
        and row["utc_session"] == "london"
        and row["lifecycle_label_status"] != "RESOLVED_NO_FILL"
    )
    victim["cost_label_status"] = "INCOMPLETE_COMMISSION"
    victim.pop("terminal_net_r")
    changed = _fit(incomplete)
    changed_root = _cell(changed, "proposed_order_type", proposed_order_type="LIMIT")
    assert changed_root["p_modelled_fill_given_resolved"] == root[
        "p_modelled_fill_given_resolved"
    ]
    assert changed_root["counts"]["resolved_fills"] == 240
    assert changed_root["counts"]["cost_complete_fills"] == 239
    assert changed["expanding_folds"][0]["expected_net_status_counts"][
        "NOT_EVALUABLE_COST"
    ] > 0


def test_exact_support_shortfall_and_tick_sensitivity_never_change_primary_fit():
    rows = _estate(limit_per_day=10, market_per_day=2)
    baseline = _fit(rows)
    roots = {
        row["proposed_order_type"]: row
        for row in baseline["expanding_folds"][0]["root_support"]
    }
    assert roots["LIMIT"]["resolved_attempts"] == 20
    assert roots["LIMIT"]["additional_resolved_limit_attempts_required"] == 80
    assert roots["LIMIT"]["resolved_fills"] == 20
    assert roots["LIMIT"]["additional_resolved_fills_required"] == 10

    with_ticks = copy.deepcopy(rows)
    with_ticks[0]["ordered_tick_sensitivity"] = {
        "evidence_class": FITTER.TICK_EVIDENCE_CLASS,
        "lifecycle_label_status": "RESOLVED_FILLED_STOP",
        "terminal_gross_r": -1.1,
        "terminal_net_r": -1.2,
        "cost_label_status": "COMPLETE",
        **{field: with_ticks[0][field] for field in FITTER.TICK_PAIR_FIELDS},
    }
    sensitivity = _fit(with_ticks)
    assert sensitivity["final_development_fit"]["count_tables"] == baseline[
        "final_development_fit"
    ]["count_tables"]
    assert sensitivity["ordered_tick_sensitivity"]["paired_occurrences"] == 1
    assert sensitivity["ordered_tick_sensitivity"]["gross_r_delta_sum_tick_minus_m1"] == -2.1
    assert sensitivity["ordered_tick_sensitivity"]["net_r_delta_sum_tick_minus_m1"] == -2.2
    assert sensitivity["ordered_tick_sensitivity"]["model_count_or_probability_influence"] is False

    with_ticks[0]["ordered_tick_sensitivity"]["geometry_contract_hash_sha256"] = "e" * 64
    with pytest.raises(ValueError, match="tick identical pair key mismatch"):
        _fit(with_ticks)

    with_ticks[0]["ordered_tick_sensitivity"]["geometry_contract_hash_sha256"] = "d" * 64
    with_ticks[0]["ordered_tick_sensitivity"][
        "lifecycle_label_status"
    ] = "CENSORED_UNDECLARED_FAKE"
    with pytest.raises(ValueError, match="bad tick lifecycle status"):
        _fit(with_ticks)


def test_leakage_and_rehashed_contract_or_market_label_tampering_fail_closed():
    rows = _estate()
    with_leak = copy.deepcopy(rows)
    with_leak[0]["label_available_utc"] = "2025-10-27T08:30:00Z"
    with pytest.raises(ValueError, match="label is available before its span ends"):
        _fit(with_leak)

    at_cutoff = copy.deepcopy(rows)
    cutoff_row = next(row for row in at_cutoff if row["trading_day"] == "2025-10-28")
    cutoff_row["label_available_utc"] = "2025-10-28T21:00:00Z"
    cutoff_result = _fit(at_cutoff)
    assert cutoff_result["expanding_folds"][0]["training_row_count"] == 159
    assert cutoff_result["expanding_folds"][0]["availability_exclusions"] == {
        "label_not_strictly_before_effective_test_start": 1
    }

    market_no_fill = copy.deepcopy(rows)
    victim = next(row for row in market_no_fill if row["proposed_order_type"] == "MARKET")
    victim["lifecycle_label_status"] = "RESOLVED_NO_FILL"
    victim["cost_label_status"] = "NOT_APPLICABLE_NO_FILL"
    victim.pop("terminal_net_r")
    with pytest.raises(ValueError, match="MARKET row .* cannot resolve as NO_FILL"):
        _fit(market_no_fill)

    truncated = [row for row in rows if row["trading_day"] != "2025-11-04"]
    with pytest.raises(ValueError, match="all six development days"):
        _fit(truncated)

    tampered = _prereg()
    tampered["primary_estimator"]["support"][
        "terminal_min_resolved_fills_per_cell"
    ] = 29
    tampered.pop("payload_sha256")
    tampered["payload_sha256"] = FITTER._canonical_hash(tampered)
    with pytest.raises(ValueError, match="exact frozen OUTCOME_AUTHORITY"):
        FITTER.fit_wave21_development(
            rows,
            tampered,
            development_freeze_utc="2025-11-08T00:00:00Z",
        )
