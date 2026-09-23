from __future__ import annotations

import json

from scripts import audit_sierra_6b_si_depth_policy as script
from src.research_infra import sierra_6b_si_depth_policy as mod


def _window(classification: str, *, common: int, jaccard: float, all_delta: float, common_delta: float) -> dict:
    return {
        "classification": classification,
        "coverage": {
            "sierra_count": common + 10,
            "databento_count": common,
            "common_count": common,
            "coverage_jaccard": jaccard,
        },
        "all_seconds": {"delta_summary": {"max_abs_delta": all_delta, "nonzero_delta_count": 4}},
        "common_seconds": {"delta_summary": {"max_abs_delta": common_delta, "nonzero_delta_count": 2}},
    }


def _audit(symbol: str, source: str, futures: str, event15: dict, pre60: dict) -> dict:
    return {
        "event": {
            "gtos_symbol": symbol,
            "source_symbol": source,
            "futures_symbol": futures,
        },
        "windows": {
            "event15": event15,
            "pre60": pre60,
        },
    }


def test_6b_policy_requires_common_second_alignment_and_keeps_current_rows_blocked():
    audit = _audit(
        "GBPUSD",
        "6BM26-CME",
        "6B.v.0",
        _window("SAMPLING_CLOCK_MAJOR_CONTRIBUTOR", common=632, jaccard=0.925, all_delta=51, common_delta=5),
        _window("SAMPLING_CLOCK_MAJOR_CONTRIBUTOR", common=2756, jaccard=0.967, all_delta=93, common_delta=5),
    )

    row = mod.build_6b_status_row(audit, generated_at_utc="2026-05-05T00:00:00+00:00", source_dependency_signature="sig")

    assert row["status"] == "COMMON_SECOND_ALIGNMENT_POLICY_REGISTERED"
    assert row["depth_interpretation_allowed_current"] is False
    assert row["depth_interpretation_allowed_after_policy"] is True
    assert row["current_rows_policy"] == "KEEP_CURRENT_ROWS_BLOCKED_UNTIL_ALIGNED_FEATURE_ROW"
    assert row["sample_alignment_policy"]["required_mode"] == "INTERSECT_SIERRA_EOB_SECONDS_WITH_REFERENCE_MBP10_SECONDS"


def test_si_policy_stays_source_depth_definition_blocked_when_common_second_deltas_remain():
    audit = _audit(
        "XAGUSD",
        "SIM26-COMEX",
        "SI.v.0",
        _window("SOURCE_OR_DEPTH_DEFINITION_DIFFERENCE_REMAINS", common=718, jaccard=0.967, all_delta=25, common_delta=25),
        _window("SOURCE_OR_DEPTH_DEFINITION_DIFFERENCE_REMAINS", common=2880, jaccard=0.971, all_delta=52, common_delta=26),
    )

    rows = mod.build_si_status_rows([audit], generated_at_utc="2026-05-05T00:00:00+00:00", source_dependency_signature="sig")

    assert rows[0]["status"] == "SOURCE_DEPTH_DEFINITION_BLOCKED"
    assert rows[0]["depth_interpretation_allowed_after_policy"] is False
    assert "do not interpret SI depth rows" in rows[0]["requirements_before_interpretation"][-1]


def test_report_payload_uses_existing_audit_artifacts_and_preserves_no_promotion(tmp_path):
    audit_6b = _audit(
        "GBPUSD",
        "6BM26-CME",
        "6B.v.0",
        _window("SAMPLING_CLOCK_MAJOR_CONTRIBUTOR", common=632, jaccard=0.925, all_delta=51, common_delta=5),
        _window("SAMPLING_CLOCK_MAJOR_CONTRIBUTOR", common=2756, jaccard=0.967, all_delta=93, common_delta=5),
    )
    audit_si = _audit(
        "XAGUSD",
        "SIM26-COMEX",
        "SI.v.0",
        _window("SOURCE_OR_DEPTH_DEFINITION_DIFFERENCE_REMAINS", common=718, jaccard=0.967, all_delta=25, common_delta=25),
        _window("SOURCE_OR_DEPTH_DEFINITION_DIFFERENCE_REMAINS", common=2880, jaccard=0.971, all_delta=52, common_delta=26),
    )
    audit_sil = _audit(
        "XAGUSD",
        "SILM26-COMEX",
        "SI.v.0",
        _window("SOURCE_OR_DEPTH_DEFINITION_DIFFERENCE_REMAINS", common=679, jaccard=0.866, all_delta=25, common_delta=25),
        _window("SAMPLING_CLOCK_MAJOR_CONTRIBUTOR", common=2660, jaccard=0.858, all_delta=137, common_delta=27),
    )
    paths = {}
    for name, payload in {"6b": audit_6b, "si": audit_si, "sil": audit_sil}.items():
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        paths[name] = path

    payload = mod.build_report_payload(audit_paths=paths, generated_at_utc="2026-05-05T00:00:00+00:00")

    assert payload["status"] == "OK_WITH_6B_POLICY_AND_SI_BLOCKER"
    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["completion_evidence"]["common_second_alignment_policy_registered_for_6b"] is True
    assert payload["completion_evidence"]["si_depth_definition_remains_blocked"] is True
    assert payload["completion_evidence"]["databento_calls"] == 0


def test_append_status_rows_is_idempotent(tmp_path):
    row = {
        "row_key": "same",
        "schema_version": "sierra_6b_si_depth_policy_status_v1",
    }
    path = tmp_path / "status.jsonl"

    assert script.append_status_rows_if_missing([row], path) == 1
    assert script.append_status_rows_if_missing([row], path) == 0
    assert path.read_text(encoding="utf-8").count("\n") == 1
