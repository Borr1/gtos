from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research_infra.forward_capture import (
    PROMOTION_VERDICT,
    SCID_CAPTURE_GROUPS,
    SCID_FORWARD_SOURCE_CAPTURE_SCHEMA_VERSION,
    build_scid_forward_source_capture_row,
    record_scid_forward_capture_candidate_groups,
    record_scid_forward_capture_group,
    validate_scid_forward_source_capture_row,
)


def _read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _assert_cp281_event_contract(row: dict) -> None:
    for field in (
        "symbol",
        "source_symbol",
        "symbol_family",
        "market_timeframe",
        "route_session",
        "horizon_id",
        "side",
        "source_path_sha256",
        "source_file_sha256",
    ):
        assert row.get(field) not in (None, ""), field


def _base_fields() -> dict:
    return {
        "symbol": "NAS100",
        "broker_symbol": "NDX100",
        "source_symbol": "NQ",
        "session": "ny",
        "kill_zone": "ny",
        "side": "LONG",
        "candidate_id": "NAS100_2026-05-04T13:30:00+00:00",
        "trade_id": "lim_NAS100_20260504_133000",
        "decision_time_utc": "2026-05-04T13:30:00+00:00",
        "analysis_decision": "CANDIDATE",
        "framework": "ob_retest",
        "frameworks_evaluated": {
            "ob_retest": {"qualified": True},
            "fvg_fill": {"qualified": False},
            "breaker_re_entry": {"qualified": False},
        },
        "trade_parameters": {
            "direction": "LONG",
            "entry_price": 213.257,
            "stop_loss": 212.64,
            "take_profit_1": 214.183,
            "risk_reward": 1.5,
        },
        "h1_setup": {
            "poi_type": "OB",
            "poi_price_level": 213.26,
            "zone": "discount",
        },
        "mso_summary": {
            "timestamp_utc": "2026-05-04T13:30:00+00:00",
            "timeframes": ["H1", "M15"],
        },
        "fvg_ob_geometry": {
            "ob_bounds": {"lower": 213.10, "upper": 213.40},
            "fvg_bounds": {"lower": 213.15, "upper": 213.35},
        },
    }


def test_scid_capture_group_registry_is_exact_accepted_set():
    assert len(SCID_CAPTURE_GROUPS) == 10
    assert set(SCID_CAPTURE_GROUPS) == {
        "baseline_control_fields",
        "framework_setup_family",
        "future_orderflow_depth_proxy_requirements",
        "intended_entry_reference",
        "intended_side_direction",
        "intended_stop_reference",
        "intended_target_reference",
        "lifecycle_fill_cancel_expiry_source_status",
        "lower_timeframe_asof_path_availability",
        "poi_type_bounds_source",
    }


@pytest.mark.parametrize("group", SCID_CAPTURE_GROUPS)
def test_scid_builder_emits_schema_safe_valid_rows_for_each_group(group):
    row = build_scid_forward_source_capture_row(
        _base_fields(),
        {
            "field_group": group,
            "intent_after_check": "expired_48h",
            "checked_candle_time_utc": "2026-05-04T13:45:00+00:00",
        },
    )
    validation = validate_scid_forward_source_capture_row(row)

    assert validation["ok"] is True
    assert row["schema_version"] == SCID_FORWARD_SOURCE_CAPTURE_SCHEMA_VERSION
    assert row["promotion_verdict"] == PROMOTION_VERDICT
    assert row["validation_safe"] is False
    assert row["outcome_review_opened"] is False
    assert row["live_effect"] is False
    _assert_cp281_event_contract(row)
    assert row["opens_result_scoring"] is False
    assert row["opens_live_trading_behavior"] is False


def test_scid_validator_rejects_missing_required_field():
    row = build_scid_forward_source_capture_row(
        _base_fields(),
        {"field_group": "intended_entry_reference"},
    )
    row.pop("entry_reference_price")

    validation = validate_scid_forward_source_capture_row(row)

    assert validation["ok"] is False
    assert "missing_required_fields" in validation["issues"]


def test_scid_validator_rejects_forbidden_broker_result_surface():
    row = build_scid_forward_source_capture_row(
        _base_fields(),
        {"field_group": "intended_side_direction"},
    )
    row["broker_account_id"] = "SECRET_ACCOUNT_123"
    row["actual_r"] = 1.25

    validation = validate_scid_forward_source_capture_row(row)

    assert validation["ok"] is False
    assert "unexpected_fields" in validation["issues"]
    assert "forbidden_raw_fields" in validation["issues"]


def test_scid_validator_rejects_stale_asof_path():
    row = build_scid_forward_source_capture_row(
        _base_fields(),
        {"field_group": "intended_side_direction"},
    )
    row["source_observed_asof_utc"] = "2026-05-04T13:31:00+00:00"

    validation = validate_scid_forward_source_capture_row(row)

    assert validation["ok"] is False
    assert "stale_or_invalid_asof" in validation["issues"]


def test_scid_validator_rejects_duplicate_key_drift():
    row = build_scid_forward_source_capture_row(
        _base_fields(),
        {"field_group": "intended_side_direction"},
    )
    drifted = dict(row)
    drifted["source_hash"] = "0" * 64
    registry: dict[str, str] = {}

    first = validate_scid_forward_source_capture_row(row, duplicate_key_registry=registry)
    second = validate_scid_forward_source_capture_row(drifted, duplicate_key_registry=registry)

    assert first["ok"] is True
    assert second["ok"] is False
    assert "duplicate_key_drift" in second["issues"]


def test_scid_unavailable_ltf_and_orderflow_rows_are_fail_closed_not_fetches():
    fields = _base_fields()
    ltf = build_scid_forward_source_capture_row(
        fields,
        {"field_group": "lower_timeframe_asof_path_availability"},
    )
    orderflow = build_scid_forward_source_capture_row(
        fields,
        {"field_group": "future_orderflow_depth_proxy_requirements"},
    )

    assert validate_scid_forward_source_capture_row(ltf)["ok"] is True
    assert validate_scid_forward_source_capture_row(orderflow)["ok"] is True
    assert ltf["source_hash"] is None
    assert ltf["source_hash_policy"] == "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED"
    assert ltf["ltf_availability_status"] == "UNAVAILABLE_FAIL_CLOSED"
    assert orderflow["source_hash"] is None
    assert orderflow["orderflow_proxy_availability_status"] == "UNAVAILABLE_FAIL_CLOSED"
    assert orderflow["opens_paid_or_vendor_access"] is False


def test_scid_group_writer_fail_open_on_append_failure(monkeypatch):
    import src.research_infra.forward_capture as forward_capture_mod

    def _boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(forward_capture_mod, "append_jsonl", _boom)
    row = build_scid_forward_source_capture_row(
        _base_fields(),
        {"field_group": "intended_side_direction"},
    )

    assert record_scid_forward_capture_group(row) is False


def test_scid_candidate_group_writer_appends_nine_candidate_groups(tmp_path):
    path = tmp_path / "scid_forward_source_capture.jsonl"
    statuses = record_scid_forward_capture_candidate_groups(_base_fields(), log_path=path)
    rows = _read_rows(path)

    assert all(statuses.values())
    assert len(rows) == 9
    assert {row["field_group"] for row in rows} == set(SCID_CAPTURE_GROUPS) - {
        "lifecycle_fill_cancel_expiry_source_status",
    }
    assert all(validate_scid_forward_source_capture_row(row)["ok"] for row in rows)
    payload = json.dumps(rows, sort_keys=True)
    assert "SECRET" not in payload
    assert '"validation_safe": true' not in payload
