from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).with_name(
    "build_b7_5_selection_sizing_source_authority_amendment_r3.py"
)
SPEC = importlib.util.spec_from_file_location(
    "build_b7_5_selection_sizing_source_authority_amendment_r3",
    MODULE_PATH,
)
assert SPEC is not None and SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


def _current_fixture() -> dict:
    _contract, old, _digest = builder._load_sealed_january()
    current = copy.deepcopy(old)
    current["source_resolution_row_count"] = (
        builder.EXPECTED_CURRENT_RESOLUTION_ROW_COUNT
    )
    current["source_resolution_rows_digest_sha256"] = (
        builder.EXPECTED_CURRENT_RESOLUTION_DIGEST_SHA256
    )
    current["source_cache_cleanup_valid"] = True
    plan = current["source_authority_plan"]
    plan["valid"] = True
    plan["source_row_count"] = builder.EXPECTED_CURRENT_SOURCE_ROW_COUNT
    plan["plan_digest_sha256"] = builder.EXPECTED_CURRENT_PLAN_DIGEST_SHA256
    plan["static_source_row_count"] = builder.EXPECTED_STATIC_ROW_COUNT
    plan["static_source_digest_sha256"] = builder.EXPECTED_STATIC_DIGEST_SHA256
    plan["m1_symbol_day_authority_row_count"] = builder.EXPECTED_M1_ROW_COUNT
    plan["m1_day_plan_digest_sha256"] = builder.EXPECTED_M1_DIGEST_SHA256
    plan["tick_window_authority_row_count"] = (
        builder.EXPECTED_TICK_AUTHORITY_ROW_COUNT
    )
    plan["tick_component_source_digest_sha256"] = (
        builder.EXPECTED_CURRENT_TICK_COMPONENT_DIGEST_SHA256
    )
    plan["tick_window_plan_digest_sha256"] = (
        builder.EXPECTED_CURRENT_TICK_WINDOW_PLAN_DIGEST_SHA256
    )
    plan["tick_window_integrity_failure_symbols"] = []
    plan["incomplete_sources"] = []
    covered = set(builder.EXPECTED_CURRENT_COVERED_TICK_SYMBOLS)
    for row in plan["tick_window_authority_rows"]:
        symbol = row["symbol"]
        row["tick_window_authority_digest_sha256"] = builder.canonical_sha256(
            {"current_test_fixture": symbol}
        )
        row["integrity_valid"] = True
        row["integrity_failures"] = []
        row["covered_day_count"] = 31 if symbol in covered else 0
        row["status"] = "covered" if symbol in covered else "none"
    return current


def test_r3_is_two_pass_self_hashed_january_only_and_replay_free() -> None:
    current = _current_fixture()
    calls = 0

    def resolver() -> dict:
        nonlocal calls
        calls += 1
        return copy.deepcopy(current)

    payload = builder.build_amendment_payload(
        sealed_at_utc="2026-07-17T01:00:00Z",
        resolver=resolver,
    )

    assert calls == 2
    assert payload["schema"] == builder.SCHEMA
    assert payload["status"] == builder.STATUS
    assert builder.verify_self_hash(payload)
    assert payload["scope"] == {
        "decision_window_id": "development_january",
        "source_window_contract_window_id": "b7_5_2026_01",
        "start": "2026-01-01",
        "end": "2026-01-31",
        "repair_class": "source_authority_only",
        "factorial_treatment_change": False,
        "all_other_decision_windows_unchanged": True,
    }
    transition = payload["active_source_plan_transition"]
    assert transition[
        "protocol_and_sealed_contract_source_plan_digest_sha256"
    ] == builder.EXPECTED_OLD_PLAN_DIGEST_SHA256
    assert transition[
        "current_reproduced_source_plan_digest_sha256"
    ] == builder.EXPECTED_CURRENT_PLAN_DIGEST_SHA256
    assert payload["component_transition"]["static_component_unchanged"] is True
    assert payload["component_transition"]["m1_component_unchanged"] is True
    assert payload["component_transition"][
        "only_tick_component_tick_window_and_composite_plan_changed"
    ] is True
    assert len(payload["tick_authority_row_transition"]) == 24
    assert all(
        row["digest_changed"]
        for row in payload["tick_authority_row_transition"]
    )
    audit = payload["reproduction_audit"]
    assert audit["resolver_run_count"] == 2
    assert audit["resolver_runs_identical"] is True
    assert audit["run_campaign_call_count"] == 0
    assert audit["outcome_ledger_read_count"] == 0
    assert audit["outcome_artifact_read_count"] == 0
    assert audit["march_window_evaluation_count"] == 0
    assert audit["march_window_replay_count"] == 0
    assert audit["march_outcome_artifact_read_count"] == 0
    assert audit["march_outcome_read"] is False
    assert audit[
        "selected_january_authority_file_integrity_hashes_may_traverse_"
        "multi_month_raw_source_containers"
    ] is True
    assert audit[
        "raw_source_container_byte_reads_are_not_march_outcome_evaluation"
    ] is True
    assert payload["prior_chain_binding"]["r2"][
        "remains_active_for_window_id"
    ] == "engineering_june_04"

    tampered = copy.deepcopy(payload)
    tampered["active_source_plan_transition"][
        "current_reproduced_source_plan_digest_sha256"
    ] = "f" * 64
    assert not builder.verify_self_hash(tampered)


def test_r3_fails_when_two_current_reproductions_differ() -> None:
    first = _current_fixture()
    second = copy.deepcopy(first)
    second["source_authority_plan"]["tick_window_authority_rows"][0][
        "status"
    ] = "different_second_pass_status"
    rows = iter((first, second))

    with pytest.raises(
        builder.AmendmentValidationError,
        match="current_january_reproduction_runs_differ",
    ):
        builder.build_amendment_payload(
            sealed_at_utc="2026-07-17T01:00:00Z",
            resolver=lambda: copy.deepcopy(next(rows)),
        )


def test_r3_fails_closed_on_static_or_m1_drift() -> None:
    current = _current_fixture()
    current["source_authority_plan"]["static_source_digest_sha256"] = "f" * 64

    with pytest.raises(
        builder.AmendmentValidationError,
        match="current_snapshot_mismatch:static_source_digest_sha256",
    ):
        builder.build_amendment_payload(
            sealed_at_utc="2026-07-17T01:00:00Z",
            resolver=lambda: copy.deepcopy(current),
        )


def test_sealed_contract_binding_and_code_cause_are_exact() -> None:
    contract, january, digest = builder._load_sealed_january()
    assert digest == builder.EXPECTED_SOURCE_WINDOW_CONTRACT_FILE_SHA256
    assert contract["schema"] == builder.EXPECTED_SOURCE_WINDOW_CONTRACT_SCHEMA
    assert january["source_authority_plan"]["plan_digest_sha256"] == (
        builder.EXPECTED_OLD_PLAN_DIGEST_SHA256
    )
    code = builder._validate_code_inputs()
    assert code["resolver_file_sha256"] == builder.EXPECTED_RESOLVER_FILE_SHA256
    assert code["causal_change"] == builder.RESOLVER_CAUSE_COMMIT
    assert code["cause_class"] == (
        "resolver_code_semantics_change_after_source_contract_seal"
    )
