from __future__ import annotations

import copy

from build_nofill_forward_source_capture_implementation_design_plan_2026_05_10 import (
    CONTRACT_PATH,
    EXISTING_READY_FIELDS,
    FORBIDDEN_OR_REDACTED_FIELDS,
    FUTURE_LOGGER_FIELDS,
    ROOT,
    SCHEMA_ONLY_CONTROL_FIELDS,
    build_field_map,
    read_json,
)
from verify_nofill_forward_source_capture_implementation_design_plan_2026_05_10 import (
    REQUIRED_FUTURE_ROW_COLUMNS,
    verify_field_map,
    verify_flags,
)


def test_status_sets_cover_exact_contract_fields() -> None:
    contract = read_json(CONTRACT_PATH)
    contract_names = {field["field_name"] for field in contract["fields"]}
    mapped_names = (
        EXISTING_READY_FIELDS
        | FUTURE_LOGGER_FIELDS
        | SCHEMA_ONLY_CONTROL_FIELDS
        | FORBIDDEN_OR_REDACTED_FIELDS
    )
    assert len(contract_names) == 55
    assert mapped_names == contract_names
    assert not (
        EXISTING_READY_FIELDS & FUTURE_LOGGER_FIELDS
        or EXISTING_READY_FIELDS & SCHEMA_ONLY_CONTROL_FIELDS
        or EXISTING_READY_FIELDS & FORBIDDEN_OR_REDACTED_FIELDS
        or FUTURE_LOGGER_FIELDS & SCHEMA_ONLY_CONTROL_FIELDS
        or FUTURE_LOGGER_FIELDS & FORBIDDEN_OR_REDACTED_FIELDS
        or SCHEMA_ONLY_CONTROL_FIELDS & FORBIDDEN_OR_REDACTED_FIELDS
    )


def test_field_map_has_exact_terminal_closure() -> None:
    field_map = build_field_map(read_json(CONTRACT_PATH))
    failures: dict[str, object] = {}
    summary = verify_field_map(field_map, failures)
    assert not failures
    assert summary["field_count"] == 55
    assert summary["unique_field_count"] == 55
    assert sum(summary["terminal_status_counts"].values()) == 55


def test_future_logger_rows_have_required_design_columns() -> None:
    field_map = build_field_map(read_json(CONTRACT_PATH))
    future_rows = [
        row
        for row in field_map["fields"]
        if row["terminal_implementation_design_status"] == "FUTURE_LOGGER_FIELD_REQUIRED"
    ]
    assert future_rows
    for row in future_rows:
        assert all(row.get(column) for column in REQUIRED_FUTURE_ROW_COLUMNS)


def test_verifier_rejects_placeholder_terminal_status() -> None:
    field_map = copy.deepcopy(build_field_map(read_json(CONTRACT_PATH)))
    field_map["fields"][0]["terminal_implementation_design_status"] = "UN" + "KNOWN"
    failures: dict[str, object] = {}
    verify_field_map(field_map, failures)
    assert "terminal_status_values" in failures


def test_verifier_rejects_unsafe_flags() -> None:
    payload = {
        "_artifact_name": "synthetic.json",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": True,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    failures: dict[str, object] = {}
    verify_flags([payload], failures)
    assert "closed_route_flags" in failures


def test_contract_input_exists_under_repo_root() -> None:
    assert (ROOT / CONTRACT_PATH).exists()
