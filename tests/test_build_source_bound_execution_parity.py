from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from src.components.poi_state_contract import finalize_poi_state, stable_poi_id
from src.components.executable_value_semantics import (
    LEGACY_UNTYPED_EXPECTED_VALUE,
    LEGACY_UNTYPED_EXPECTED_VALUE_SOURCE,
)
from src.research.moonshot_scheduler_v4_best_trade_allocator import (
    PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT,
    PACKAGE_NEW_ENTRY_AUTHORITY_PAYLOAD_SCHEMA,
    package_new_entry_authority_payload_hash_sha256,
)


ROOT = Path(__file__).resolve().parents[1]
PARITY_BUILDER_PATH = (
    ROOT
    / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
    / "build_source_bound_execution_parity.py"
)
HARNESS_PATH = (
    ROOT
    / "src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py"
)
DENOMINATOR_BUILDER_PATH = (
    ROOT
    / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
    / "build_denominator_to_deployment_execution.py"
)
SELECTED_PACKAGE_REPLAY_BRIDGE_PATH = (
    ROOT
    / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
    / "run_selected_package_replay_bridge.py"
)
COMPARE_BROAD_REPLAY_PATH = (
    ROOT
    / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
    / "compare_broad_live_as_if_replay_runs.py"
)
FLOW_ANALYZER_PATH = (
    ROOT
    / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
    / "analyze_broad_live_as_if_replay_flow.py"
)


def load_parity_builder():
    spec = importlib.util.spec_from_file_location(
        "build_source_bound_execution_parity", PARITY_BUILDER_PATH
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_sparse_candidate_enrichment_materializes_only_accessed_defaults() -> None:
    module = load_parity_builder()
    row = module.SparseCandidateEnrichment()

    assert row == {}
    row["source_join_class_counts"]["candidate_instance_exact"] += 1
    row["selected_candidate_ids"].add("candidate-1")
    row["gross_r"] += 1.25
    row["scheduler_rank_min"] = 2

    assert set(row) == {
        "gross_r",
        "scheduler_rank_min",
        "selected_candidate_ids",
        "source_join_class_counts",
    }
    assert row["source_join_class_counts"] == {
        "candidate_instance_exact": 1
    }
    assert row["selected_candidate_ids"] == {"candidate-1"}
    assert row["gross_r"] == 1.25
    assert row["scheduler_rank_min"] == 2
    with pytest.raises(KeyError):
        row["unknown_enrichment_field"]


def test_authority_envelope_compaction_preserves_cross_stage_truth_only() -> None:
    module = load_parity_builder()
    digest = "a" * 64
    selection = {
        "valid": True,
        "status": "single_current_schema_immutable_envelope",
        "source": "root",
        "surface": {
            "package_new_entry_authority_status": (
                "valid_signed_predecision_new_entry_authority"
            ),
            "large_source_row": ["do-not-retain"] * 100,
        },
        "payload": {
            "selector_action": "open-reduced-risk",
            "selector_reason": "signed_package_quality",
            "package_replay_order_executable_candidate_use_allowed": True,
            "package_replay_order_executable_candidate_use_allowed_reason": (
                "signed_package_authority"
            ),
            "large_payload": ["do-not-retain"] * 100,
        },
        "digest": digest,
        "reasons": [],
        "records": [
            {
                "source": "root",
                "surface": {"large_source_row": ["do-not-retain"] * 100},
                "payload": {"large_payload": ["do-not-retain"] * 100},
                "digest": digest,
                "valid": True,
                "reasons": [],
            }
        ],
        "valid_sources": ["root"],
    }

    compact = module.compact_package_new_entry_authority_envelope_selection(
        selection
    )

    assert compact == {
        "valid": True,
        "status": "single_current_schema_immutable_envelope",
        "source": "root",
        "digest": digest,
        "reasons": [],
        "payload": {
            "selector_action": "open-reduced-risk",
            "selector_reason": "signed_package_quality",
            "package_replay_order_executable_candidate_use_allowed": True,
            "package_replay_order_executable_candidate_use_allowed_reason": (
                "signed_package_authority"
            ),
        },
        "surface": {
            "package_new_entry_authority_status": (
                "valid_signed_predecision_new_entry_authority"
            )
        },
        "records": [
            {
                "source": "root",
                "digest": digest,
                "valid": True,
                "reasons": [],
            }
        ],
        "valid_sources": ["root"],
    }
    assert "large_source_row" not in compact["surface"]
    assert "large_payload" not in compact["payload"]
    assert "surface" not in compact["records"][0]
    assert "payload" not in compact["records"][0]


def load_broad_replay_harness():
    spec = importlib.util.spec_from_file_location(
        "run_broad_live_as_if_replay_harness", HARNESS_PATH
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_projection_summary_accepts_one_shot_rows_without_length_contract():
    builder = load_parity_builder()
    rows = [
        {
            "candidate_instance_parity_key": "candidate-a@@2026-06-01T08:15:00Z",
            "broad_replay_profile": "repaired_package_conversion_v3",
            "decision_time_utc": "2026-06-01T08:15:00Z",
            "candidate_present": True,
            "scorecard_present": True,
            "scheduler_selected": True,
            "order_present": True,
            "trade_present": True,
            "missed_present": False,
            "origin_family": "current_fvg_fill",
        },
        {
            "candidate_instance_parity_key": "candidate-b@@2026-06-01T08:30:00Z",
            "broad_replay_profile": "repaired_package_conversion_v3",
            "decision_time_utc": "2026-06-01T08:30:00Z",
            "candidate_present": True,
            "scorecard_present": False,
            "scheduler_selected": False,
            "order_present": False,
            "trade_present": False,
            "missed_present": True,
            "origin_family": "current_ob_retest",
        },
    ]

    materialized = builder.summarize_candidate_instance_projection_rows(rows)
    one_shot = builder.summarize_candidate_instance_projection_rows(
        (row for row in rows)
    )

    assert one_shot == materialized
    assert one_shot["row_count"] == 2


def test_main_streams_high_cardinality_rows_and_preserves_parity_order(
    tmp_path,
    monkeypatch,
):
    builder = load_parity_builder()
    cyclic_gc_was_enabled = builder.gc.isenabled()
    monkeypatch.setattr(builder, "ROUTE", tmp_path)
    monkeypatch.setattr(
        builder,
        "parse_args",
        lambda: builder.argparse.Namespace(
            broad_prefix="BROAD_LIVE_AS_IF_REPLAY_UNIT",
            artifact_tag="UNIT",
        ),
    )
    monkeypatch.setattr(builder, "artifact_status", lambda: "complete")
    monkeypatch.setattr(
        builder,
        "build_big_r_provenance",
        lambda _status: {"formula_delta": 0.0},
    )

    axis_row = {"row_type": "source_member_axis_to_executable_replay", "id": "axis"}
    trace_row = {
        "row_type": "source_member_axis_candidate_execution_trace",
        "id": "trace",
    }
    projection_row = {"candidate_instance_parity_key": "candidate@@decision"}
    bucket_row = {"row_type": "execution_leakage_bucket", "id": "bucket"}

    def fake_build(*, candidate_projection_sink, candidate_trace_sink):
        candidate_projection_sink(projection_row)
        candidate_trace_sink(trace_row)
        return (
            [axis_row],
            [bucket_row],
            [],
            {
                "parity_ledger_rows": 2,
                "candidate_instance_parity_projection_rows": 1,
                "artifacts": {},
            },
        )

    monkeypatch.setattr(
        builder,
        "_build_parity_rows_and_projection_with_sinks",
        fake_build,
    )
    monkeypatch.setattr(
        builder,
        "build_execution_leakage_repair_plan",
        lambda **_kwargs: {"status": "unit"},
    )

    assert builder.main() == 0
    parity_rows = list(builder.iter_jsonl(builder.PARITY_LEDGER_PATH))
    projection_rows = list(
        builder.iter_jsonl(builder.CANDIDATE_INSTANCE_PARITY_PROJECTION_PATH)
    )

    assert parity_rows == [axis_row, trace_row]
    assert projection_rows == [projection_row]
    assert list(builder.iter_jsonl(builder.LEAKAGE_BUCKET_PATH)) == [bucket_row]
    assert not list(tmp_path.glob("*.building.tmp"))
    assert not list(tmp_path.glob("*.spool.tmp"))
    assert builder.gc.isenabled() is cyclic_gc_was_enabled


def load_selected_package_replay_bridge():
    spec = importlib.util.spec_from_file_location(
        "run_selected_package_replay_bridge", SELECTED_PACKAGE_REPLAY_BRIDGE_PATH
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_broad_replay_comparator():
    spec = importlib.util.spec_from_file_location(
        "compare_broad_live_as_if_replay_runs", COMPARE_BROAD_REPLAY_PATH
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_flow_analyzer():
    spec = importlib.util.spec_from_file_location(
        "analyze_broad_live_as_if_replay_flow", FLOW_ANALYZER_PATH
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_flow_analyzer_resolves_projection_from_parity_producer_summary(
    tmp_path: Path,
) -> None:
    analyzer = load_flow_analyzer()
    analyzer.ROUTE = tmp_path
    prefix = "BROAD_LIVE_AS_IF_REPLAY_V245_LONG_RUNTIME_PREFIX"
    broad_summary = tmp_path / f"{prefix}_SUMMARY.json"
    projection = tmp_path / "CANDIDATE_INSTANCE_PARITY_PROJECTION_V245_LEDGER.jsonl"
    parity_summary = (
        tmp_path / "SOURCE_BOUND_TO_EXECUTED_PARITY_V245_SUMMARY.json"
    )
    broad_summary.write_text("{}\n", encoding="utf-8")
    projection.write_text("{}\n", encoding="utf-8")
    parity_summary.write_text(
        json.dumps(
            {
                "artifacts": {
                    "broad_replay_summary": str(broad_summary),
                    "candidate_instance_parity_projection_ledger": str(projection),
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )

    analyzer.configure_paths(prefix)

    assert analyzer.CANDIDATE_INSTANCE_PARITY_PROJECTION_PATH == projection


def test_flow_analyzer_reads_compact_candidate_index_when_full_ledger_is_absent(
    tmp_path: Path,
    monkeypatch,
) -> None:
    analyzer = load_flow_analyzer()
    candidate_path = tmp_path / "candidate.jsonl"
    candidate_index_path = tmp_path / "candidate-index.jsonl"
    write_jsonl(
        candidate_index_path,
        [
            {
                "row_type": "candidate_index",
                "candidate_index_schema": "compact_broad_replay_candidate_index_v1",
                "candidate_id": "candidate-index-authority",
                "decision_time_utc": "2026-05-13T08:15:00Z",
            }
        ],
    )
    monkeypatch.setattr(analyzer, "CANDIDATE_PATH", candidate_path)
    monkeypatch.setattr(analyzer, "CANDIDATE_INDEX_PATH", candidate_index_path)

    rows = list(analyzer.candidate_flow_rows())

    assert [row["candidate_id"] for row in rows] == [
        "candidate-index-authority"
    ]


def load_denominator_builder():
    spec = importlib.util.spec_from_file_location(
        "build_denominator_to_deployment_execution", DENOMINATOR_BUILDER_PATH
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _parity_unit_poi_state() -> dict:
    source_times = [
        "2026-05-14T00:00:00+00:00",
        "2026-05-14T00:15:00+00:00",
        "2026-05-14T00:30:00+00:00",
    ]
    return finalize_poi_state(
        {
            "poi_id": stable_poi_id(
                symbol="US30_CASH",
                timeframe="M15",
                poi_type="fair_value_gap",
                direction="bullish",
                source_candle_times=source_times,
                zone_low=42000.0,
                zone_high=42010.0,
            ),
            "poi_type": "fair_value_gap",
            "poi_timeframe": "M15",
            "poi_direction": "bullish",
            "poi_zone_low": 42000.0,
            "poi_zone_high": 42010.0,
            "poi_source_candle_times": source_times,
            "poi_created_at_utc": "2026-05-14T00:45:00+00:00",
            "poi_state_asof_utc": "2026-05-14T01:00:00+00:00",
            "poi_age_hours": 0.25,
            "poi_touch_count": 0,
            "poi_first_touch_time_utc": "",
            "poi_last_touch_time_utc": "",
            "poi_mitigation_status": "untouched",
            "poi_filled": False,
            "poi_invalidated": False,
            "poi_invalidation_time_utc": "",
            "poi_invalidation_reason": "",
            "poi_state_uses_outcome_fields": False,
        }
    )


def test_poi_lineage_projection_is_exact_across_executable_stages() -> None:
    builder = load_parity_builder()
    state = _parity_unit_poi_state()
    candidate = {
        "candidate_id": "fvg-candidate",
        "decision_time_utc": "2026-05-14T01:00:00+00:00",
        "origin_family": "current_fvg_fill",
        "current_framework": "fvg_fill",
        "poi_state": state,
        "poi_id": state["poi_id"],
        "poi_state_hash_sha256": state["poi_state_hash_sha256"],
    }
    downstream = {
        "candidate_id": candidate["candidate_id"],
        "decision_time_utc": candidate["decision_time_utc"],
        "poi_state": state,
        "poi_id": state["poi_id"],
        "poi_state_hash_sha256": state["poi_state_hash_sha256"],
    }

    projection = builder.poi_lineage_projection_fields(
        candidate=candidate,
        scorecard=dict(downstream),
        order=dict(downstream),
        trade=dict(downstream),
        missed={},
    )

    assert projection["poi_cross_stage_lineage_exact"] is True
    assert projection["poi_lineage_status"] == "exact_cross_stage_poi_lineage"
    assert projection["poi_missing_bound_stages"] == []
    assert set(projection["poi_stage_ids"].values()) == {state["poi_id"]}
    assert set(projection["poi_stage_hashes"].values()) == {
        state["poi_state_hash_sha256"]
    }


def test_poi_lineage_projection_rejects_downstream_hash_swap() -> None:
    builder = load_parity_builder()
    state = _parity_unit_poi_state()
    candidate = {
        "candidate_id": "fvg-candidate",
        "decision_time_utc": "2026-05-14T01:00:00+00:00",
        "origin_family": "current_fvg_fill",
        "current_framework": "fvg_fill",
        "poi_state": state,
    }
    swapped = {"poi_state": {**state, "poi_state_hash_sha256": "0" * 64}}

    projection = builder.poi_lineage_projection_fields(
        candidate=candidate,
        scorecard=swapped,
        order={},
        trade={},
        missed={},
    )

    assert projection["poi_cross_stage_lineage_exact"] is False
    assert projection["poi_lineage_status"] == "poi_lineage_mismatch"


def configure_broad_loader_fixture(builder, tmp_path, monkeypatch, *, prefix: str):
    monkeypatch.setattr(builder, "ROUTE", tmp_path)
    monkeypatch.setattr(builder, "BROAD_PREFIX", prefix)
    summary_path = tmp_path / f"{prefix}_SUMMARY.json"
    monkeypatch.setattr(builder, "BROAD_SUMMARY_PATH", summary_path)
    suffixes = {
        "BROAD_CANDIDATE_PATH": "CANDIDATE_LEDGER.jsonl",
        "BROAD_CANDIDATE_INDEX_PATH": "CANDIDATE_INDEX_LEDGER.jsonl",
        "BROAD_SCORECARD_PATH": "SCORECARD_LEDGER.jsonl",
        "BROAD_ORDER_PATH": "ORDER_LEDGER.jsonl",
        "BROAD_ORACLE_PATH": "ORDERED_PATH_ORACLE_LEDGER.jsonl",
        "BROAD_TRADE_PATH": "TRADE_LEDGER.jsonl",
        "BROAD_MISSED_PATH": "MISSED_OPPORTUNITY_LEDGER.jsonl",
        "BROAD_PACKET_SIDECAR_PATH": "PACKET_SIDECAR_LEDGER.jsonl",
    }
    for attribute, suffix in suffixes.items():
        path = tmp_path / f"{prefix}_{suffix}"
        monkeypatch.setattr(builder, attribute, path)
        write_jsonl(path, [])
    return summary_path


def _signed_parity_router_refusal_row(
    selector_reason: str,
    *,
    authority_family: str = "router_refusal_softening",
) -> dict:
    candidate_id = f"candidate-{selector_reason}"
    decision_time = "2026-05-15T10:15:00+00:00"
    authority_fields = _current_authority_fields(
        candidate_id=candidate_id,
        decision_time_utc=decision_time,
        order_allowed=True,
    )
    authority_fields.pop(
        "ultimate_candidate_package_open_reduced_risk_authority",
        None,
    )
    payload = authority_fields["package_new_entry_authority_payload"]
    payload.update(
        {
            "selector_reason": selector_reason,
            "authority_family": authority_family,
            "expected_net_r": 0.774821084989,
            "probability": 0.7528224077568244,
            "fill_probability": 0.9134878427148885,
            "execution_fill_probability": 0.9134878427148885,
            "entry_quality_fill_probability": 0.9134878427148885,
            "limit_fillability_probability": 0.9134878427148885,
            "predecision_limit_fillability_probability": 0.9134878427148885,
            "source_bound_router_refusal_materialization_floors": {
                "expected_net_r": 0.55,
                "probability": 0.70,
                "fill_probability": 0.80,
                "source_completeness": 0.95,
            },
        }
    )
    digest = package_new_entry_authority_payload_hash_sha256(payload)
    authority_fields["package_new_entry_authority_hash_sha256"] = digest
    authority_fields["expected_package_new_entry_authority_hash_sha256"] = digest
    authority_fields["package_new_entry_authority_authority_family"] = authority_family
    for field, value in payload.items():
        authority_fields[f"package_new_entry_authority_{field}"] = value
    nested_authority = {
        **authority_fields,
        "allowed": True,
        "applies": True,
        "authority_family": authority_family,
        "authority_source": "unit_test_predecision_authority",
        "selector_reason": selector_reason,
        "source_boundary": payload["source_boundary"],
        "positive_predecision_package_edge": True,
    }
    return {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "candidate_instance_identity_status": "materialized",
        "selector_action": "open-reduced-risk",
        "selector_reason": selector_reason,
        "scheduler_materialization_action_intent": "new_position",
        "expected_net_r": 0.774821084989,
        "candidate_expected_net_r": 0.774821084989,
        "probability": 0.7528224077568244,
        "candidate_probability": 0.7528224077568244,
        "fill_probability": 0.9134878427148885,
        "candidate_fill_probability": 0.9134878427148885,
        "predecision_limit_fillability_probability": 0.9134878427148885,
        "limit_fillability_probability": 0.9134878427148885,
        "source_completeness": 1.0,
        "source_completeness_status": "complete",
        "pretrade_cost_packet_status": "PASSED",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "cost_authority": "broker_calibrated_replay_cost",
        "candidate_cost_r_fallback_is_authority": False,
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_source_bound_candidate_use_allowed": True,
        "package_open_reduced_authority_family": authority_family,
        **authority_fields,
        "ultimate_candidate_package_open_reduced_risk_authority": nested_authority,
    }


def test_parity_source_bound_router_refusal_uses_materialization_floors() -> None:
    builder = load_parity_builder()
    row = _signed_parity_router_refusal_row(
        "source_bound_router_refusal_open_reduced_materialized_for_replay"
    )

    assert (
        builder.signed_package_new_entry_authority_block_reason(
            row,
            action_intent="new_position",
        )
        is None
    )


def test_effective_selector_action_uses_valid_package_authority_over_raw_reject() -> None:
    builder = load_parity_builder()
    row = _signed_parity_router_refusal_row(
        "source_bound_router_refusal_open_reduced_materialized_for_replay"
    )
    row["selector_action"] = "reject"
    row["selector_reason"] = "raw_router_reject"
    row["scheduler_materialization_selector_action"] = "reject"
    row["scheduler_materialization_selector_reason"] = "raw_scheduler_reject"
    row["package_new_entry_authority_selector_action"] = "open-reduced-risk"
    row["package_new_entry_authority_selector_reason"] = (
        "source_bound_router_refusal_open_reduced_materialized_for_replay"
    )

    assert builder.effective_selector_action(row) == "open-reduced-risk"
    assert (
        builder.effective_selector_reason(row)
        == "source_bound_router_refusal_open_reduced_materialized_for_replay"
    )


def test_effective_selector_action_does_not_promote_invalid_package_authority() -> None:
    builder = load_parity_builder()
    row = _signed_parity_router_refusal_row(
        "source_bound_router_refusal_open_reduced_materialized_for_replay"
    )
    row["selector_action"] = "reject"
    row["scheduler_materialization_selector_action"] = "reject"
    row["package_new_entry_authority_selector_action"] = "open-reduced-risk"
    row["package_new_entry_authority_valid"] = False
    row["package_new_entry_authority_status"] = "invalid_or_missing_signed_new_entry_authority"
    row["package_new_entry_authority_hash_sha256"] = "tampered-digest"
    nested = dict(row["ultimate_candidate_package_open_reduced_risk_authority"])
    nested["package_new_entry_authority_hash_sha256"] = "tampered-digest"
    row["ultimate_candidate_package_open_reduced_risk_authority"] = nested

    assert builder.effective_selector_action(row) == "reject"


def test_replay_executable_detail_uses_valid_package_action_with_raw_reject() -> None:
    builder = load_parity_builder()
    row = _signed_parity_router_refusal_row(
        "source_bound_router_refusal_open_reduced_materialized_for_replay"
    )
    row.update(
        {
            "selector_action": "reject",
            "package_new_entry_authority_selector_action": "open-reduced-risk",
            "pretrade_cost_packet_status": "PASSED",
            "cost_authority": "broker_calibrated_replay_cost",
            "cost_source_gap_status": "source_bound_cost_authority_present",
            "candidate_cost_r_fallback_is_authority": False,
            "source_gap_cost_fallback_blocked": False,
            "source_completeness": 1.0,
            "source_completeness_status": "source_completeness_present",
            "execution_fill_probability": 0.82,
            "execution_fill_probability_source": "predecision_limit_fillability",
            "predecision_limit_fillability_probability": 0.82,
            "limit_fillability_probability": 0.82,
            "scheduler_materialization_action_intent": "new_position",
            "entry_price": 2400.0,
            "stop_loss": 2390.0,
            "take_profit_1": 2420.0,
        }
    )

    allowed, reason = builder.replay_executable_package_use_detail(
        row,
        source_bound_allowed=True,
        package_replay_allowed=True,
    )

    assert allowed is True
    assert reason == "broker_cost_selector_and_scheduler_action_executable"


def test_replay_executable_detail_allows_signed_soft_scheduler_transfer_skip() -> None:
    builder = load_parity_builder()
    row = _signed_parity_router_refusal_row(
        "source_bound_router_refusal_open_reduced_materialized_for_replay"
    )
    row.update(
        {
            "selector_action": "reject",
            "package_new_entry_authority_selector_action": "open-reduced-risk",
            "pretrade_cost_packet_status": "PASSED",
            "cost_authority": "broker_calibrated_replay_cost",
            "cost_source_gap_status": "source_bound_cost_authority_present",
            "candidate_cost_r_fallback_is_authority": False,
            "source_gap_cost_fallback_blocked": False,
            "source_completeness": 1.0,
            "source_completeness_status": "source_completeness_present",
            "execution_fill_probability": 0.82,
            "execution_fill_probability_source": "predecision_limit_fillability",
            "predecision_limit_fillability_probability": 0.82,
            "limit_fillability_probability": 0.82,
            "scheduler_materialization_action_intent": "new_position",
            "scheduler_materialization_skip_reason": (
                "candidate_generated_not_scheduler_selected"
            ),
            "scheduler_terminal_vs_soft_guard": {
                "schema_version": "scheduler_reallocation_terminal_vs_soft_guard_v1",
                "soft_guard_vetoes": ["not_scheduler_selected"],
                "terminal_vetoes": [],
                "pool_eligible": True,
                "pool_status": "eligible",
            },
            "reallocation_soft_guard_vetoes": ["not_scheduler_selected"],
            "reallocation_soft_guard_pool_eligible": True,
            "reallocation_soft_guard_pool_status": "eligible",
            "terminal_vetoes": [],
            "entry_price": 2400.0,
            "stop_loss": 2390.0,
            "take_profit_1": 2420.0,
        }
    )

    assert builder.replay_executable_package_use_detail(
        row,
        source_bound_allowed=True,
        package_replay_allowed=True,
    ) == (True, "broker_cost_selector_and_scheduler_action_executable")

    explicit_order_exec_false = {
        **row,
        "package_replay_order_executable_candidate_use_allowed": False,
    }
    assert builder.replay_executable_package_use_detail(
        explicit_order_exec_false,
        source_bound_allowed=True,
        package_replay_allowed=True,
    ) == (True, "broker_cost_selector_and_scheduler_action_executable")

    ambiguous_soft_string = dict(row)
    for key in (
        "scheduler_terminal_vs_soft_guard",
        "reallocation_soft_guard_vetoes",
        "reallocation_soft_guard_pool_eligible",
        "reallocation_soft_guard_pool_status",
        "terminal_vetoes",
    ):
        ambiguous_soft_string.pop(key, None)
    assert builder.replay_executable_package_use_detail(
        ambiguous_soft_string,
        source_bound_allowed=True,
        package_replay_allowed=True,
    ) == (
        False,
        "scheduler_materialization_skipped:candidate_generated_not_scheduler_selected",
    )

    cost_refused = {
        **row,
        "pretrade_cost_packet_status": "REFUSED",
    }
    assert builder.replay_executable_package_use_detail(
        cost_refused,
        source_bound_allowed=True,
        package_replay_allowed=True,
    ) == (True, "broker_cost_selector_and_scheduler_action_executable")


def test_replay_executable_detail_keeps_immutable_envelope_over_stale_secondary_fill_surface(
    monkeypatch,
) -> None:
    builder = load_parity_builder()
    row = _signed_parity_router_refusal_row(
        "source_bound_router_refusal_open_reduced_materialized_for_replay"
    )
    row.update(
        {
            "scheduler_materialization_action_intent": "new_position",
            "entry_price": 1.081,
            "stop_loss": 1.079,
            "take_profit_1": 1.085,
            "ultimate_candidate_package_reduce_risk_authority": {
                "package_new_entry_authority_required": True,
                "package_new_entry_authority_valid": False,
                "package_new_entry_authority_status": (
                    "legacy_or_invalid_authority_diagnostic_only"
                ),
            },
        }
    )

    envelope = builder.package_new_entry_authority_envelope_selection(
        row,
        action_intent="new_position",
    )
    assert envelope["valid"] is True
    monkeypatch.setattr(
        builder,
        "execution_fillability_authority",
        lambda _row: (None, "invalid_signed_execution_fillability_authority"),
    )
    assert builder.replay_executable_package_use_detail(
        row,
        source_bound_allowed=True,
        package_replay_allowed=True,
    ) == (True, "broker_cost_selector_and_scheduler_action_executable")


def test_replay_executable_detail_ignores_optional_invalid_reduced_envelope_for_trade() -> None:
    builder = load_parity_builder()
    row = {
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_source_bound_candidate_use_allowed": True,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "source_gap_cost_fallback_blocked": False,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "decision_time_utc": "2026-06-02T09:15:00+00:00",
        "predecision_limit_fillability_probability": 0.82,
        "limit_fillability_probability": 0.82,
        "execution_fill_probability": 0.82,
        "execution_fill_probability_source": "predecision_limit_fillability",
        "execution_fill_probability_source_time_utc": (
            "2026-06-02T09:00:00+00:00"
        ),
        "execution_fill_probability_source_boundary": (
            "closed_m15_predecision_asof_no_postdecision_path"
        ),
        "scheduler_materialization_action_intent": "new_position",
        "selector_action": "trade",
        "entry_price": 1.081,
        "stop_loss": 1.079,
        "take_profit_1": 1.085,
        "package_new_entry_authority_required": False,
        "package_new_entry_authority_valid": False,
        "package_new_entry_authority_status": (
            "legacy_or_invalid_authority_diagnostic_only"
        ),
    }

    assert builder.replay_executable_package_use_detail(
        row,
        source_bound_allowed=True,
        package_replay_allowed=True,
    ) == (True, "broker_cost_selector_and_scheduler_action_executable")


def test_remember_executable_proof_keeps_candidate_authority_over_missed_reject() -> None:
    builder = load_parity_builder()
    authority_hash = "b" * 64
    candidate_row = {
        "row_type": "candidate",
        "selector_action": "open-reduced-risk",
        "effective_selector_action": "open-reduced-risk",
        "scheduler_materialization_selector_action": "open-reduced-risk",
        "selector_reason": "candidate_package_authority",
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "predecision_limit_fillability_probability": 0.82,
        "limit_fillability_probability": 0.82,
        "execution_fill_probability": 0.82,
        "scheduler_materialization_action_intent": "new_position",
        "entry_price": 2400.0,
        "stop_loss": 2390.0,
        "take_profit_1": 2420.0,
        "package_new_entry_authority_valid": True,
        "package_new_entry_authority_status": (
            "valid_signed_predecision_new_entry_authority"
        ),
        "package_new_entry_authority_failures": [],
        "package_new_entry_authority_hash_sha256": authority_hash,
        "expected_package_new_entry_authority_hash_sha256": authority_hash,
        "package_new_entry_authority_target_action_intent": "new_position",
        "package_new_entry_authority_source_boundary": (
            "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
        ),
        "package_new_entry_authority_uses_outcome_fields": False,
        "package_new_entry_authority_selector_action": "open-reduced-risk",
        "package_new_entry_authority_selector_reason": "candidate_package_authority",
    }
    missed_row = {
        **candidate_row,
        "row_type": "missed_opportunity",
        "selector_action": "reject",
        "effective_selector_action": "reject",
        "raw_selector_action": "reject",
        "selector_reason": "missed_row_demoted_selector_action",
    }
    enrichment = {}

    builder.remember_executable_proof(enrichment, candidate_row)
    builder.remember_executable_proof(enrichment, missed_row)

    assert enrichment["executable_proof_row"]["selector_action"] == "open-reduced-risk"
    assert (
        enrichment["executable_proof_row"]["selector_reason"]
        == "candidate_package_authority"
    )


def test_parity_explicit_non_router_family_ignores_stale_router_reason() -> None:
    builder = load_parity_builder()
    row = _signed_parity_router_refusal_row(
        "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk",
        authority_family="fill_floor_softening",
    )
    row["expected_net_r"] = 0.01
    row["candidate_expected_net_r"] = 0.01
    row["probability"] = 0.01
    row["candidate_probability"] = 0.01
    row["fill_probability"] = 0.01
    row["candidate_fill_probability"] = 0.01
    row["predecision_limit_fillability_probability"] = 0.01
    row["limit_fillability_probability"] = 0.01

    assert builder.source_bound_router_refusal_materialization_applies(row) is False
    assert (
        builder.signed_package_new_entry_authority_block_reason(
            row,
            action_intent="new_position",
        )
        is None
    )


def test_parity_router_refusal_rejects_candidate_fill_without_execution_fillability() -> None:
    builder = load_parity_builder()
    row = _signed_parity_router_refusal_row(
        "source_bound_router_refusal_open_reduced_materialized_for_replay"
    )
    row.pop("predecision_limit_fillability_probability", None)
    row.pop("limit_fillability_probability", None)

    assert (
        builder.signed_package_new_entry_authority_block_reason(
            row,
            action_intent="new_position",
        )
        is None
    )


def test_parity_fillability_preserves_invalid_signed_authority_reason() -> None:
    builder = load_parity_builder()
    row = _signed_parity_router_refusal_row(
        "source_bound_router_refusal_open_reduced_materialized_for_replay"
    )
    authority_field = row["package_new_entry_authority_authority_field"]
    authority = dict(row[authority_field])
    forged_payload = dict(authority["package_new_entry_authority_payload"])
    forged_payload["execution_fill_probability"] = 0.99
    authority["package_new_entry_authority_payload"] = forged_payload
    row[authority_field] = authority
    row.update(
        {
            "execution_fill_probability": 0.77,
            "execution_fill_probability_source": "predecision_limit_fillability",
            "predecision_limit_fillability_probability": 0.77,
            "limit_fillability_probability": 0.77,
        }
    )

    assert builder.execution_fillability_authority(row) == (
        None,
        "invalid_signed_execution_fillability_authority",
    )


def test_selected_package_bridge_rejects_generic_predecision_fill_as_execution_authority() -> None:
    module = load_selected_package_replay_bridge()
    row = {
        "candidate_id": "bridge-generic-predecision-fill",
        "decision_time_utc": "2026-05-05T08:15:00+00:00",
        "selector_action": "trade",
        "selector_reason": "trade",
        "scheduler_materialization_action_intent": "new_position",
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "package_replay_source_bound_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "expected_net_r": 1.11,
        "probability": 0.91,
        "fill_probability": 0.92,
        "candidate_fill_probability": 0.92,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "entry_price": 2400.0,
        "stop_loss": 2390.0,
        "take_profit_1": 2420.0,
        "candidate_decision_quality_field_sources": {
            "expected_net_r": "fixture.predecision.expected_net_r",
            "probability": "fixture.predecision.probability",
            "fill_probability": "fixture.predecision.fill_probability",
            "source_completeness": "fixture.predecision.source_completeness",
        },
    }

    assert module.execution_fillability_authority(row) == (
        None,
        module.EXECUTION_FILLABILITY_MISSING_SOURCE,
    )
    assert module.executable_package_use_detail(
        row,
        source_bound_allowed=True,
    ) == (False, module.EXECUTION_FILLABILITY_MISSING_SOURCE)


def test_parity_positive_predecision_router_refusal_stays_strict() -> None:
    builder = load_parity_builder()
    row = _signed_parity_router_refusal_row(
        "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk"
    )

    assert (
        builder.signed_package_new_entry_authority_block_reason(
            row,
            action_intent="new_position",
        )
        == "router_refusal_expected_net_r_below_floor"
    )


def test_parity_summary_reports_exact_replay_window_denominator(tmp_path: Path, monkeypatch):
    builder = load_parity_builder()
    broad_summary_path = tmp_path / "BROAD_UNIT_SMOKE_SUMMARY.json"
    broad_summary_path.write_text(
        json.dumps(
            {
                "date_start": "2026-05-13",
                "date_end": "2026-05-13",
                "selected_day_count": 1,
                "coverage_status": "bounded_replay_materialization_not_full_available_universe",
                "full_available_configured_day_count": 901,
                "days_by_split": {"holdout": ["2026-05-13"], "train": [], "development": []},
                "full_available_days_by_split": {
                    "train": {"start": "2024-01-01", "end": "2025-06-30", "day_count": 547},
                    "development": {"start": "2025-07-01", "end": "2026-05-12", "day_count": 316},
                    "holdout": {"start": "2026-05-13", "end": "2026-06-19", "day_count": 38},
                },
                "split_profile_stats": [
                    {
                        "profile": "repaired",
                        "headline_net_r": 1.5,
                        "headline_gross_r": 2.4,
                        "headline_final_r": 2.0,
                        "cash_pnl": 150.0,
                        "headline_trade_rows": 1,
                    }
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(builder, "BROAD_PREFIX", "BROAD_UNIT_SMOKE")
    monkeypatch.setattr(builder, "BROAD_SUMMARY_PATH", broad_summary_path)

    parity_rows = [
        {
            "broad_replay_profile": "repaired",
            "execution_leakage_label": "executed_positive_r",
            "candidate_generation_label": "candidate_generated",
            "selected_package_bridge_candidate_generated": False,
            "scheduler_option_present_count": 1,
            "scorecard_selected_count": 1,
            "order_present_count": 1,
            "trade_count": 1,
            "source_bound_r": 10.0,
            "package_source_bound_r": 10.0,
            "effective_source_bound_r": 10.0,
            "effective_package_source_bound_r": 10.0,
            "diagnostic_source_bound_r": 1000.0,
            "diagnostic_package_source_bound_r": 1000.0,
            "actual_r_sum": 2.0,
            "gross_r_sum": 2.4,
            "final_r_sum": 2.0,
            "cash_pnl_sum": 200.0,
            "unique_trade_actual_r_by_candidate_instance_key": {
                "repaired|candidate-1|2026-05-13T10:00:00Z": 2.0
            },
            "unique_trade_gross_r_by_candidate_instance_key": {
                "repaired|candidate-1|2026-05-13T10:00:00Z": 2.4
            },
            "unique_trade_final_r_by_candidate_instance_key": {
                "repaired|candidate-1|2026-05-13T10:00:00Z": 2.0
            },
            "unique_trade_cash_pnl_by_candidate_instance_key": {
                "repaired|candidate-1|2026-05-13T10:00:00Z": 200.0
            },
            "trade_candidate_id_samples": ["candidate-1"],
        },
        {
            "broad_replay_profile": "repaired",
            "execution_leakage_label": "candidate_not_generated",
            "candidate_generation_label": "candidate_not_generated",
            "selected_package_bridge_candidate_generated": False,
            "source_bound_r": 5.0,
            "package_source_bound_r": 5.0,
            "effective_source_bound_r": 5.0,
            "effective_package_source_bound_r": 5.0,
            "diagnostic_source_bound_r": 500.0,
            "diagnostic_package_source_bound_r": 500.0,
        },
        {
            "broad_replay_profile": "repaired",
            "execution_leakage_label": "candidate_generated_selector_reject",
            "candidate_generation_label": "candidate_not_generated",
            "selected_package_bridge_candidate_generated": True,
            "source_bound_r": 0.0,
            "package_source_bound_r": 0.0,
            "effective_source_bound_r": 0.0,
            "effective_package_source_bound_r": 0.0,
            "diagnostic_source_bound_r": 700.0,
            "diagnostic_package_source_bound_r": 700.0,
        },
        {
            "broad_replay_profile": "repaired",
            "execution_leakage_label": "candidate_generated_negative_source_bound",
            "candidate_generation_label": "candidate_not_generated",
            "selected_package_bridge_candidate_generated": False,
            "source_bound_r": -3.0,
            "package_source_bound_r": -3.0,
            "effective_source_bound_r": -3.0,
            "effective_package_source_bound_r": -3.0,
            "diagnostic_source_bound_r": 300.0,
            "diagnostic_package_source_bound_r": 300.0,
        },
    ]

    summary = builder.build_parity_summary(
        parity_rows=parity_rows,
        bucket_rows=[],
        observation_status="completed_broad_replay_summary_present",
        exact_package_candidate_rows=0,
        exact_package_candidate_ids=0,
        package_authority_order_geometry_status_counts={},
        broad_candidate_count=3,
        broad_candidate_physical_count=3,
        broad_candidate_physical_count_source="unit",
        broad_candidate_expanded_index_count=3,
        profiles=("repaired",),
        candidate_instance_projection_summary={
            "profile_stage_presence_counts": {
                "repaired": {
                    "candidate": 3,
                    "scorecard": 1,
                    "scheduler_selected": 1,
                    "order": 1,
                    "trade": 1,
                    "missed": 2,
                }
            }
        },
    )

    window = summary["exact_replay_window_transfer"]
    assert summary["broad_replay_prefix"] == "BROAD_UNIT_SMOKE"
    assert window["denominator_scope"] == (
        "selected_replay_window_axis_presence_with_non_additive_"
        "source_member_signal_diagnostics"
    )
    assert window["source_bound_r_additive_allowed"] is False
    assert window["executable_r_to_source_bound_r_percentage_allowed"] is False
    assert window["source_bound_r_denominator_field"] is None
    assert window["full_reservoir_transfer_claim_allowed"] is False
    assert window["interpretation"] == (
        "This smoke proves or disproves the local repair; it does not prove "
        "total reservoir conversion."
    )
    repaired = window["profiles"]["repaired"]
    assert repaired["package_axes_available_inside_replay_window"] == 4
    assert repaired["source_bound_r_nonzero_package_axes_inside_replay_window"] == 3
    assert repaired["source_bound_r_positive_package_axes_inside_replay_window"] == 2
    assert repaired["package_axes_in_global_diagnostic_surface"] == 4
    assert repaired["candidate_generated_axes_inside_replay_window"] == 2
    assert repaired["scorecard_present_axes_inside_replay_window"] == 1
    assert repaired["scheduler_selected_axes_inside_replay_window"] == 1
    assert repaired["scorecard_or_order_present_axes_inside_replay_window"] == 1
    assert repaired["filled_trade_axes_inside_replay_window"] == 1
    assert repaired["axis_attributed_scorecard_selected_count_inside_replay_window"] == 1
    assert repaired["axis_attributed_order_present_count_inside_replay_window"] == 1
    assert repaired["axis_attributed_trade_count_inside_replay_window"] == 1
    assert repaired["scorecard_selected_count_inside_replay_window"] == 1
    assert repaired["order_present_count_inside_replay_window"] == 1
    assert repaired["trade_count_inside_replay_window"] == 1
    assert repaired["candidate_instance_count_authority"] == (
        "candidate_instance_parity_projection_exact_unique"
    )
    assert repaired["candidate_instance_rows_inside_replay_window"] == 3
    assert (
        repaired[
            "scorecard_present_candidate_instance_rows_inside_replay_window"
        ]
        == 1
    )
    assert (
        repaired[
            "scheduler_selected_candidate_instance_rows_inside_replay_window"
        ]
        == 1
    )
    assert repaired["order_present_candidate_instance_rows_inside_replay_window"] == 1
    assert repaired["filled_candidate_instance_rows_inside_replay_window"] == 1
    assert repaired["missed_candidate_instance_rows_inside_replay_window"] == 2
    assert repaired["source_bound_r_available_inside_replay_window"] == 12.0
    assert repaired[
        "non_additive_executable_gated_source_bound_signal_r_inside_replay_window"
    ] == 12.0
    assert repaired["diagnostic_global_source_bound_r_sum_not_denominator"] == 2500.0
    assert repaired["actual_executable_r_inside_replay_window"] == 2.0
    assert repaired["actual_executable_r_pct_of_window_source_bound_r"] is None
    assert repaired["actual_executable_r_pct_disposition"] == (
        "forbidden_non_additive_source_member_axis_overlap_signal"
    )
    assert repaired["headline_replay_net_r_inside_replay_window"] == 1.5
    assert repaired["headline_replay_trade_rows_inside_replay_window"] == 1
    assert repaired["headline_vs_unique_actual_r_delta"] == -0.5
    assert repaired["headline_vs_axis_attributed_actual_r_delta"] == -0.5
    assert repaired["unique_actual_vs_axis_attributed_actual_r_delta"] == 0.0
    assert repaired["r_metric_reconciliation_status"] == (
        "headline_unique_axis_r_surfaces_differ_explicit"
    )


def test_relational_candidate_materialization_is_physical_parity_authority() -> None:
    builder = load_parity_builder()
    summary = {
        "candidate_ledger_omitted": True,
        "candidate_index_ledger_omitted": True,
        "candidate_rows_written": 0,
        "candidate_index_rows_written": 0,
        "candidate_rows": 35191,
        "candidate_relational_materialization": {
            "schema": (
                "gtos.final_moonshot.broad_replay."
                "candidate_relational_materialization.v1"
            ),
            "enabled": True,
            "exact": True,
            "status": "exact_candidate_equals_missed_order_trade_union",
            "candidate_rows": 35191,
            "candidate_unique_profile_scoped_instance_keys": 35191,
            "terminal_union_unique_profile_scoped_instance_keys": 35191,
            "candidate_duplicate_profile_scoped_instance_rows": 0,
            "candidate_minus_terminal_union_count": 0,
            "terminal_union_minus_candidate_count": 0,
            "missing_instance_key_counts": {
                "candidate": 0,
                "missed": 0,
                "order": 0,
                "trade": 0,
            },
        },
    }

    assert builder.broad_summary_declared_candidate_rows(summary) == 35191
    assert builder.broad_physical_candidate_ledger_rows(summary) == (
        35191,
        "exact_missed_order_trade_relational_candidate_rows",
    )

    summary["candidate_relational_materialization"][
        "candidate_minus_terminal_union_count"
    ] = 1
    assert builder.exact_candidate_relational_materialization_count(summary) is None


def test_package_candidate_resolution_rejects_bare_id_and_requires_exact_instance():
    builder = load_parity_builder()
    package_row = {
        "candidate_id": "candidate-reused",
        "decision_time_utc": "2026-05-05T10:00:00Z",
        "symbol": "XAUUSD",
        "side": "LONG",
    }
    exact_key = builder.package_candidate_exact_instance_key(package_row)
    index = {
        "by_signed_instance": {},
        "by_exact_instance": {exact_key: [package_row]},
        "by_candidate_id": {"candidate-reused": [package_row]},
    }

    missing, status, count = builder.resolve_package_candidate(
        {
            **package_row,
            "decision_time_utc": "2026-05-13T10:00:00Z",
        },
        index,
    )
    assert missing is None
    assert status == "candidate_id_only_non_exact_match_rejected"
    assert count == 1

    resolved, status, count = builder.resolve_package_candidate(package_row, index)
    assert resolved is not None
    assert status == "exact_candidate_time_symbol_side_match"
    assert count == 1


def test_enrichment_unique_r_uses_candidate_instance_not_bare_candidate_id():
    builder = load_parity_builder()
    items = []
    enrichment = {}
    for suffix, actual_r in (("a", 0.75), ("b", -0.5)):
        instance_key = f"profile|candidate-reused|{suffix}"
        items.append(
            {
                "candidate_id": "candidate-reused",
                "candidate_instance_key": instance_key,
                "stable_decision_window_id": f"window-{suffix}",
                "selector_action": "trade",
                "selector_reason": "unit",
            }
        )
        enrichment[instance_key] = {
            "trade_present": True,
            "trade_count": 1,
            "trade_candidate_ids": {"candidate-reused"},
            "trade_candidate_instance_keys": {instance_key},
            "trade_actual_r_by_candidate_id": {"candidate-reused": actual_r},
            "trade_gross_r_by_candidate_id": {"candidate-reused": actual_r},
            "trade_final_r_by_candidate_id": {"candidate-reused": actual_r},
            "trade_cash_pnl_by_candidate_id": {"candidate-reused": actual_r * 100},
            "trade_actual_r_by_candidate_instance_key": {instance_key: actual_r},
            "trade_gross_r_by_candidate_instance_key": {instance_key: actual_r},
            "trade_final_r_by_candidate_instance_key": {instance_key: actual_r},
            "trade_cash_pnl_by_candidate_instance_key": {
                instance_key: actual_r * 100
            },
            "net_r": actual_r,
            "gross_r": actual_r,
            "final_r": actual_r,
            "cash_pnl": actual_r * 100,
        }

    summary = builder.summarize_enrichment(items, enrichment)
    assert summary["unique_trade_candidate_instance_count"] == 2
    assert summary["unique_trade_bare_candidate_id_count"] == 1
    assert summary["unique_actual_r_sum"] == 0.25
    assert summary["unique_replay_trade_identity"] == (
        "candidate_instance_key_exact_within_broad_replay_profile"
    )


def test_session_tokens_include_symmetric_broad_aliases():
    builder = load_parity_builder()

    off_tokens = builder.session_tokens({"session_bucket": "off_configured_session"})
    assert "off_kz_broad" in off_tokens

    tokyo_tokens = builder.session_tokens({"session_bucket": "tokyo"})
    assert "tokyo_broad" in tokyo_tokens

    ny_tokens = builder.session_tokens({"session_bucket": "ny"})
    assert "ny_broad" in ny_tokens
    assert "new_york" in ny_tokens

    hour_tokens = builder.session_tokens({"utc_hour_bucket": "h18_19"})
    assert "h18_19" in hour_tokens
    assert "moonshot_h18_19" in hour_tokens

    bridge = load_selected_package_replay_bridge()
    assert {"h18_19", "moonshot_h18_19"}.issubset(
        bridge.session_variants("h18_19")
    )

    denominator_builder = load_denominator_builder()
    assert {"h18_19", "moonshot_h18_19"}.issubset(
        denominator_builder.session_aliases(("h18_19",))
    )


def test_sleeve_axis_matches_candidate_across_session_namespaces():
    builder = load_parity_builder()

    candidate = {
        "symbol": "XAUUSD",
        "side": "SHORT",
        "framework": "origin_liquidity_sweep_reclaim",
        "origin_family": "liquidity_sweep_reclaim",
        "session_tokens": builder.session_tokens(
            {"session_bucket": "off_configured_session"}
        ),
    }
    axis = {
        "symbol": "XAUUSD",
        "side": "SHORT",
        "framework": "broader_origin",
        "origin_family": "liquidity_sweep_reclaim",
        "session_bucket": "off_kz_broad",
    }

    assert builder.sleeve_axis_matches_candidate(axis, candidate)


def test_axis_unmatched_diagnostic_respects_session_aliases():
    builder = load_parity_builder()
    axis = {
        "symbol": "GBPJPY",
        "side": "SHORT",
        "framework": "broader_origin",
        "origin_family": "structural_distance_extreme",
        "session_bucket": "ny_broad",
    }
    candidates = [
        {
            "symbol": "GBPJPY",
            "side": "SHORT",
            "framework": "origin_structural_distance_extreme",
            "origin_family": "structural_distance_extreme",
            "session_tokens": builder.session_tokens({"session_bucket": "ny"}),
        }
    ]

    diagnostic = builder.axis_unmatched_diagnostic(axis, candidates)

    assert diagnostic["candidate_generation_mismatch_reason"] == "candidate_namespace_tuple_mismatch"
    assert diagnostic["candidate_generation_mismatch_fields"] == []


def test_candidate_matches_stable_member_axis_id_overrides_tuple_alias_debt():
    builder = load_parity_builder()

    member = {
        "stable_member_axis_id": "member_axis:abc123",
        "symbol": "GBPJPY",
        "side": "LONG",
        "framework": "broader_origin",
        "origin_family": "cross_asset_lead_lag",
        "session_bucket": "tokyo_broad",
    }
    candidate = {
        "symbol": "GBPJPY",
        "side": "LONG",
        "framework": "broader_origin",
        "origin_family": "origin_cross_asset_lead_lag",
        "session_tokens": builder.session_tokens({"session_bucket": "london"}),
        "ultimate_package_matched_member_axis_ids": ["member_axis:abc123"],
    }

    assert not builder.sleeve_axis_matches_candidate(member, candidate)
    assert builder.candidate_matches_stable_member_axis_id(member, candidate)


def test_denominator_compact_bridge_join_uses_stable_window_instance():
    builder = load_denominator_builder()
    candidate = {
        "candidate_id": "candidate:reused",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2026-05-05T08:30:00+00:00",
    }
    right_window = builder.stable_decision_window_id_for_candidate(candidate)
    wrong_window = "decision_window:XAUUSD:LONG:2026-05-05T08:15:00+00:00"
    right_bridge = {
        "replay_candidate_id": "candidate:reused",
        "stable_decision_window_id": right_window,
        "matched_stable_member_axis_ids": ["member-axis:right-window"],
        "selected_package_replay_row": True,
    }
    wrong_bridge = {
        "replay_candidate_id": "candidate:reused",
        "stable_decision_window_id": wrong_window,
        "matched_stable_member_axis_ids": ["member-axis:wrong-window"],
        "selected_package_replay_row": True,
    }

    bridge_row = builder.lookup_compact_candidate_bridge_row(
        candidate,
        bridge_by_instance_key={
            builder.bridge_instance_key("candidate:reused", wrong_window): [wrong_bridge],
            builder.bridge_instance_key("candidate:reused", right_window): [right_bridge],
        },
        bridge_by_candidate_id={"candidate:reused": [wrong_bridge, right_bridge]},
    )
    compact = builder.compact_replay_candidate_row(
        candidate,
        bridge_row=bridge_row,
        source_namespace="unit",
    )

    assert compact["selected_package_bridge_join_status"] == "exact_candidate_window_join"
    assert compact["selected_package_bridge_join_key"] == (
        f"candidate:reused@@{right_window}"
    )
    assert compact["selected_package_bridge_candidate_id_bridge_count"] == 2
    assert compact["matched_stable_member_axis_ids"] == ["member-axis:right-window"]
    assert compact["stable_decision_window_id"] == right_window


def test_denominator_compact_bridge_join_canonicalizes_us30_cash_window_alias():
    builder = load_denominator_builder()
    candidate = {
        "candidate_id": "candidate:us30",
        "symbol": "US30_cash",
        "side": "LONG",
        "decision_time_utc": "2026-05-05T08:15:00+00:00",
        "stable_decision_window_id": (
            "decision_window:US30_CASH:LONG:2026-05-05T08:15:00+00:00"
        ),
    }
    canonical_window = "decision_window:US30_cash:LONG:2026-05-05T08:15:00+00:00"
    bridge_row = {
        "replay_candidate_id": "candidate:us30",
        "stable_decision_window_id": canonical_window,
        "matched_stable_member_axis_ids": ["member-axis:us30"],
        "selected_package_replay_row": True,
    }

    joined = builder.lookup_compact_candidate_bridge_row(
        candidate,
        bridge_by_instance_key={
            builder.bridge_instance_key("candidate:us30", canonical_window): [bridge_row],
        },
        bridge_by_candidate_id={"candidate:us30": [bridge_row]},
    )
    compact = builder.compact_replay_candidate_row(
        candidate,
        bridge_row=joined,
        source_namespace="unit",
    )

    assert builder.candidate_bridge_stable_window(candidate) == canonical_window
    assert joined["selected_package_bridge_join_status"] == "exact_candidate_window_join"
    assert compact["stable_decision_window_id"] == canonical_window
    assert compact["matched_stable_member_axis_ids"] == ["member-axis:us30"]
    indexed = builder.index_rows_by_replay_instance(
        [candidate],
        candidate_fields=("candidate_id",),
    )
    assert builder.bridge_instance_key("candidate:us30", canonical_window) in indexed


def test_denominator_compact_preserves_open_reduced_authority_contract():
    builder = load_denominator_builder()
    candidate = {
        "candidate_id": "candidate:open-reduced",
        "symbol": "GBPJPY",
        "side": "LONG",
        "decision_time_utc": "2026-06-01T17:15:00+00:00",
        "selector_action": "open-reduced-risk",
        "scheduler_materialization_selector_action": "open-reduced-risk",
        "package_replay_executable_candidate_use_allowed": True,
        "package_replay_candidate_use_allowed": True,
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_candidate_package_open_reduced_risk_authority": {
            "allowed": True,
            "authority_family": "off_session_softening",
            "source_boundary": (
                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
            ),
        },
        "package_open_reduced_authority_allowed": True,
        "package_open_reduced_authority_family": "off_session_softening",
        "ultimate_package_open_reduced_authority_allowed": True,
    }

    compact = builder.compact_replay_candidate_row(
        candidate,
        bridge_row={
            "replay_candidate_id": "candidate:open-reduced",
            "stable_decision_window_id": builder.stable_decision_window_id_for_candidate(
                candidate
            ),
            "selected_package_replay_row": True,
        },
        source_namespace="unit",
    )

    assert compact["selector_action"] == "open-reduced-risk"
    assert compact["package_open_reduced_authority_allowed"] is True
    assert compact["package_open_reduced_authority_family"] == "off_session_softening"
    assert compact["ultimate_package_open_reduced_authority_allowed"] is True
    assert compact["ultimate_candidate_package_open_reduced_risk_authority"][
        "source_boundary"
    ] == "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"


def test_denominator_compact_bridge_join_fails_closed_on_exact_window_miss():
    builder = load_denominator_builder()
    candidate = {
        "candidate_id": "candidate:reused",
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": "2026-05-05T08:30:00+00:00",
    }
    expected_window = builder.stable_decision_window_id_for_candidate(candidate)
    wrong_window = "decision_window:XAUUSD:LONG:2026-05-05T08:15:00+00:00"
    wrong_bridge = {
        "replay_candidate_id": "candidate:reused",
        "stable_decision_window_id": wrong_window,
        "matched_stable_member_axis_ids": ["member-axis:wrong-window"],
        "selected_package_replay_row": True,
    }

    bridge_row = builder.lookup_compact_candidate_bridge_row(
        candidate,
        bridge_by_instance_key={
            builder.bridge_instance_key("candidate:reused", wrong_window): [wrong_bridge]
        },
        bridge_by_candidate_id={"candidate:reused": [wrong_bridge]},
    )
    compact = builder.compact_replay_candidate_row(
        candidate,
        bridge_row=bridge_row,
        source_namespace="unit",
    )

    assert bridge_row["selected_package_bridge_join_status"] == (
        "selected_package_bridge_exact_missing"
    )
    assert bridge_row["selected_package_bridge_join_key"] == (
        f"candidate:reused@@{expected_window}"
    )
    assert compact["matched_stable_member_axis_ids"] == []
    assert compact["selected_package_replay_row"] is False


def test_denominator_compact_bridge_join_fails_closed_without_candidate_window():
    builder = load_denominator_builder()
    wrong_window = "decision_window:XAUUSD:LONG:2026-05-05T08:15:00+00:00"
    wrong_bridge = {
        "replay_candidate_id": "candidate:reused",
        "stable_decision_window_id": wrong_window,
        "matched_stable_member_axis_ids": ["member-axis:wrong-window"],
        "selected_package_replay_row": True,
    }

    bridge_row = builder.lookup_compact_candidate_bridge_row(
        {
            "candidate_id": "candidate:reused",
            "symbol": "XAUUSD",
            "side": "LONG",
        },
        bridge_by_instance_key={
            builder.bridge_instance_key("candidate:reused", wrong_window): [wrong_bridge]
        },
        bridge_by_candidate_id={"candidate:reused": [wrong_bridge]},
    )
    compact = builder.compact_replay_candidate_row(
        {
            "candidate_id": "candidate:reused",
            "symbol": "XAUUSD",
            "side": "LONG",
        },
        bridge_row=bridge_row,
        source_namespace="unit",
    )

    assert bridge_row["selected_package_bridge_join_status"] == (
        "selected_package_bridge_window_missing"
    )
    assert bridge_row["selected_package_bridge_join_key"] is None
    assert compact["matched_stable_member_axis_ids"] == []
    assert compact["selected_package_replay_row"] is False


def test_m15_order_intent_proxy_denominator_requires_exact_oracle_instance():
    builder = load_denominator_builder()
    wrong_window = "decision_window:XAUUSD:LONG:2026-05-05T08:15:00+00:00"
    right_window = "decision_window:XAUUSD:LONG:2026-05-05T08:30:00+00:00"

    result = builder.build_reconstructed_proxy_denominator_package(
        exact_denominator_join_rows=0,
        lifecycle_label_rows=0,
        replay_summary={},
        replay_scorecard_rows=[],
        replay_candidate_rows=[],
        replay_order_policy_rows=[],
        pending_created_summary={},
        pending_created_oracle_rows=[],
        pending_created_proxy_disposition_rows=[],
        m15_grid_summary={},
        m15_grid_oracle_rows=[
            {
                "candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "stable_decision_window_id": wrong_window,
                "counterfactual_final_r": 3.0,
            }
        ],
        m15_grid_all_symbol_oracle_rows=[],
        m15_grid_order_intent_rows=[
            {
                "stable_decision_window_id": right_window,
                "decision_time_utc": "2026-05-05T08:30:00+00:00",
                "symbol": "XAUUSD",
                "side": "LONG",
                "replay_candidate_ids": ["candidate:reused"],
            }
        ],
        bridge_oracle_rows=[],
        replay_split_floor_summary={},
        stress_summary={},
        stress_rows=[],
        adversarial_summary={},
        adversarial_rows=[],
        sleeve_attribution_summary={"sleeve_attribution_rows": 82},
        generated_utc="2026-06-25T00:00:00Z",
    )

    intent_rows = [
        row
        for row in result["denominator_rows"]
        if row["denominator_class"] == "m15_grid_order_intent_proxy_denominator"
    ]

    assert len(intent_rows) == 1
    intent = intent_rows[0]
    assert intent["proxy_oracle_join_status"] == "exact_candidate_window_oracle_missing"
    assert intent["candidate_id"] is None
    assert intent["candidate_ids"] == ["candidate:reused"]
    assert intent["raw_proxy_result_r"] is None
    assert intent["proxy_scoreable"] is False


def test_reconstructed_proxy_uses_broker_cost_order_policy_as_fillability_proxy():
    builder = load_denominator_builder()

    result = builder.build_reconstructed_proxy_denominator_package(
        exact_denominator_join_rows=0,
        lifecycle_label_rows=0,
        replay_summary={},
        replay_scorecard_rows=[],
        replay_candidate_rows=[],
        replay_order_policy_rows=[
            {
                "row_number": 1,
                "source_namespace": "selected_package_replay_bridge",
                "decision_time_utc": "2026-05-05T07:15:00+00:00",
                "selected_order_type_architecture": "limit_first_delay_queue",
                "replay_action": "replay_delay_queue_limit_first",
                "blocked_reference_candidate_id": "candidate:passed",
                "blocked_reference_symbol": "XAUUSD",
                "blocked_reference_side": "LONG",
                "blocked_reference_framework": "ob_retest",
                "blocked_reference_origin_family": "current_ob_retest",
                "blocked_reference_candidate_expected_net_r": 1.25,
                "blocked_reference_candidate_probability": 0.8,
                "blocked_reference_candidate_fill_probability": 0.7,
                "blocked_reference_pretrade_cost_packet_status": "PASSED",
                "blocked_reference_cost_authority": "broker_calibrated_replay_cost",
                "blocked_reference_cost_source_gap_status": (
                    "source_bound_cost_authority_present"
                ),
                "blocked_reference_candidate_cost_r_fallback_is_authority": False,
            },
            {
                "row_number": 2,
                "source_namespace": "selected_package_replay_bridge",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "selected_order_type_architecture": "limit_first_delay_queue",
                "replay_action": "replay_delay_queue_limit_first",
                "blocked_reference_candidate_id": "candidate:refused",
                "blocked_reference_symbol": "XAUUSD",
                "blocked_reference_side": "SHORT",
                "blocked_reference_framework": "fvg_fill",
                "blocked_reference_origin_family": "current_fvg_fill",
                "blocked_reference_candidate_expected_net_r": 1.1,
                "blocked_reference_pretrade_cost_packet_status": "REFUSED",
                "blocked_reference_cost_authority": "broker_calibrated_replay_cost",
                "blocked_reference_cost_source_gap_status": (
                    "source_bound_cost_authority_present"
                ),
                "blocked_reference_candidate_cost_r_fallback_is_authority": False,
            },
        ],
        pending_created_summary={},
        pending_created_oracle_rows=[],
        pending_created_proxy_disposition_rows=[],
        m15_grid_summary={},
        m15_grid_oracle_rows=[],
        m15_grid_all_symbol_oracle_rows=[],
        m15_grid_order_intent_rows=[],
        bridge_oracle_rows=[],
        replay_split_floor_summary={},
        stress_summary={},
        stress_rows=[],
        adversarial_summary={},
        adversarial_rows=[],
        sleeve_attribution_summary={"sleeve_attribution_rows": 82},
        generated_utc="2026-06-25T00:00:00Z",
    )

    broker_rows = [
        row
        for row in result["denominator_rows"]
        if row["denominator_class"] == "broker_fillability_simulation_denominator"
    ]
    assert len(broker_rows) == 2
    passed = next(row for row in broker_rows if row["candidate_id"] == "candidate:passed")
    refused = next(row for row in broker_rows if row["candidate_id"] == "candidate:refused")
    assert passed["fillability_status"] == "broker_cost_passed_order_policy_scoreable"
    assert passed["raw_proxy_result_r"] == 1.25
    assert passed["proxy_scoreable"] is True
    assert refused["fillability_status"] == (
        "broker_cost_refused_non_executable_missed_opportunity"
    )
    assert refused["raw_proxy_result_r"] == 0.0
    assert refused["missed_fill_opportunity_cost_r"] == 1.1
    assert refused["proxy_scoreable"] is True
    assert result["summary"]["broker_fillability_oracle_rows"] == 2


def test_reconstructed_proxy_replay_selection_keeps_final_live_closed():
    builder = load_denominator_builder()
    symbols = [
        "AUDUSD",
        "EURUSD",
        "GBPUSD",
        "USDJPY",
        "USDCHF",
        "XAUUSD",
        "XAGUSD",
        "USOIL_cash",
        "UKOIL_cash",
        "GER40",
    ]
    dates = [
        "2026-05-05",
        "2026-05-06",
        "2026-05-07",
        "2026-05-08",
        "2026-05-11",
    ]
    hours = [1, 8, 14, 22]

    m15_grid_oracle_rows = []
    m15_grid_order_intent_rows = []
    for index in range(250):
        symbol = symbols[index % len(symbols)]
        side = "LONG" if index % 2 == 0 else "SHORT"
        day = dates[index % len(dates)]
        hour = hours[index % len(hours)]
        decision_time = f"{day}T{hour:02d}:15:00+00:00"
        candidate_id = f"m15-candidate-{index}"
        stable_window = f"decision_window:{symbol}:{side}:{decision_time}"
        final_r = -1.0 if index == 0 else 1.0
        fill_status = ["filled", "not_filled", "partial_filled"][index % 3]
        m15_grid_oracle_rows.append(
            {
                "campaign": "phase2_m15_grid_expansion",
                "candidate_id": candidate_id,
                "symbol": symbol,
                "side": side,
                "decision_time_utc": decision_time,
                "stable_decision_window_id": stable_window,
                "counterfactual_final_r": final_r,
                "counterfactual_fill_status": fill_status,
                "counterfactual_terminal_outcome": "target_first"
                if final_r > 0
                else "stop_first",
            }
        )
        m15_grid_order_intent_rows.append(
            {
                "stable_decision_window_id": stable_window,
                "decision_time_utc": decision_time,
                "time_period": day,
                "symbol": symbol,
                "side": side,
                "frameworks": ["ob_retest"],
                "origin_families": ["synthetic_proxy_boundary_test"],
                "replay_candidate_ids": [candidate_id],
                "source_search_result": "candidate_window_found",
                "source_bound_replay_geometry_found": True,
                "original_gtos_order_intent_truth_found": False,
                "source_truth_scope": "unit_test_reconstructed_proxy_replay",
            }
        )

    replay_candidate_rows = [
        {
            "source_namespace": "unit_source_bound",
            "decision_time_utc": "2026-05-05T01:15:00+00:00",
            "candidate_id": "source-candidate-1",
            "symbol": "AUDUSD",
            "side": "LONG",
            "framework": "ob_retest",
            "origin_family": "unit_source_bound",
        }
    ]
    replay_scorecard_rows = [
        {
            "source_namespace": "unit_source_bound",
            "decision_time_utc": "2026-05-05T01:15:00+00:00",
            "package_selected_candidate_id": "source-candidate-1",
            "package_vs_baseline_delta_r": 1.0,
            "baseline_replay_result_r": 0.0,
            "package_replay_result_r": 1.0,
            "selected_order_type_architecture": "limit_first",
            "package_selected_action": "selected",
        }
    ]
    pending_created_oracle_rows = [
        {
            "campaign": "pending_created_replay_bridge",
            "candidate_id": "pending-candidate-1",
            "symbol": "EURUSD",
            "side": "SHORT",
            "decision_time_utc": "2026-05-06T08:15:00+00:00",
            "counterfactual_final_r": 1.0,
            "counterfactual_fill_status": "filled",
        }
    ]
    bridge_oracle_rows = [
        {
            "campaign": "selected_package_replay_bridge",
            "candidate_id": "bridge-candidate-1",
            "symbol": "GBPUSD",
            "side": "LONG",
            "decision_time_utc": "2026-05-07T14:15:00+00:00",
            "counterfactual_final_r": 1.0,
            "counterfactual_fill_status": "filled",
        }
    ]
    stress_rows = [
        {
            "stress_id": "guarded-stress-unit",
            "stress_scenario": "guarded_replay_policy_unit",
            "stressed_package_vs_baseline_delta_r_sum": 1.0,
            "guarded_stressed_package_vs_baseline_delta_r_sum": 1.0,
            "base_baseline_result_r_sum": 0.0,
            "base_package_result_r_sum": 1.0,
            "guarded_replay_stress_policy_action": "pass_through_positive_proxy",
            "dimension_values": {
                "symbol": "XAUUSD",
                "side": "LONG",
                "framework": "ob_retest",
                "origin_family": "guarded_unit",
            },
        }
    ]

    result = builder.build_reconstructed_proxy_denominator_package(
        exact_denominator_join_rows=0,
        lifecycle_label_rows=877,
        replay_summary={},
        replay_scorecard_rows=replay_scorecard_rows,
        replay_candidate_rows=replay_candidate_rows,
        replay_order_policy_rows=[],
        pending_created_summary={},
        pending_created_oracle_rows=pending_created_oracle_rows,
        pending_created_proxy_disposition_rows=[],
        m15_grid_summary={},
        m15_grid_oracle_rows=m15_grid_oracle_rows,
        m15_grid_all_symbol_oracle_rows=[],
        m15_grid_order_intent_rows=m15_grid_order_intent_rows,
        bridge_oracle_rows=bridge_oracle_rows,
        replay_split_floor_summary={},
        stress_summary={},
        stress_rows=stress_rows,
        adversarial_summary={},
        adversarial_rows=[],
        sleeve_attribution_summary={"sleeve_attribution_rows": 82},
        generated_utc="2026-06-25T00:00:00Z",
    )

    package_selection = result["package_selection_summary"]
    assert package_selection["proxy_package_selected_for_replay_evaluation"] is True
    assert package_selection["local_replay_proxy_package_selection_passed"] is True
    assert package_selection["local_replay_proxy_package_selection_allowed"] is True
    assert package_selection["final_package_selected"] is False
    assert package_selection["final_package_selection_allowed"] is False
    assert package_selection["deployment_dossier_allowed"] is False
    assert (
        package_selection["local_replay_deployment_dossier_drafting_allowed"] is True
    )
    assert package_selection["broker_live_promotion_allowed"] is False


def test_m15_order_intent_source_search_requires_exact_replay_instance(
    tmp_path: Path, monkeypatch
):
    builder = load_denominator_builder()
    wrong_window = "decision_window:XAUUSD:LONG:2026-05-05T08:15:00+00:00"
    right_window = "decision_window:XAUUSD:LONG:2026-05-05T08:30:00+00:00"
    paths = {
        name: tmp_path / f"{name}.jsonl"
        for name in ("candidate", "order", "trade", "oracle")
    }
    for name, path in paths.items():
        row = {
            "candidate_id": "candidate:reused",
            "symbol": "XAUUSD",
            "side": "LONG",
            "decision_time_utc": "2026-05-05T08:15:00+00:00",
            "stable_decision_window_id": wrong_window,
        }
        if name in {"order", "oracle"}:
            row["counterfactual_final_r"] = 4.0
        write_jsonl(path, [row])
        monkeypatch.setitem(
            builder.PHASE2_M15_GRID_EXPANSION_LEDGER_PATHS,
            name,
            path,
        )

    rows, summary, _ = builder.build_phase2_m15_grid_order_intent_source_search_rows(
        phase2_m15_grid_recovery_target_rows=[
            {
                "stable_decision_window_id": right_window,
                "decision_time_utc": "2026-05-05T08:30:00+00:00",
                "symbol": "XAUUSD",
                "side": "LONG",
                "replay_candidate_ids": ["candidate:reused"],
            }
        ],
        labels=[],
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["replay_candidate_rows_found"] == 0
    assert row["replay_order_rows_found"] == 0
    assert row["replay_oracle_rows_found"] == 0
    assert row["replay_trade_rows_found"] == 0
    assert row["source_bound_replay_geometry_found"] is False
    assert summary["phase2_m15_grid_order_intent_candidate_match_windows"] == 0
    assert summary["phase2_m15_grid_order_intent_order_match_windows"] == 0
    assert summary["phase2_m15_grid_order_intent_oracle_match_windows"] == 0
    assert summary["phase2_m15_grid_order_intent_trade_match_windows"] == 0


def test_phase2_proxy_targets_require_exact_candidate_instance():
    builder = load_denominator_builder()
    wrong_window = "decision_window:XAUUSD:LONG:2026-05-05T08:15:00+00:00"
    right_window = "decision_window:XAUUSD:LONG:2026-05-05T08:30:00+00:00"

    rows, *_ = builder.build_phase2_proxy_target_artifacts(
        phase2_label_value_candidate_rows=[
            {
                "label_id": "label:proxy",
                "clean_label_family_id": "candidate_accept_reject_label",
                "replay_candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:30:00+00:00",
                "stable_decision_window_id": right_window,
            }
        ],
        bridge_order_rows=[
            {
                "candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "stable_decision_window_id": wrong_window,
                "counterfactual_final_r": 4.0,
            }
        ],
        bridge_oracle_rows=[
            {
                "candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "stable_decision_window_id": wrong_window,
                "counterfactual_final_r": 4.0,
            }
        ],
        bridge_scorecard_rows=[
            {
                "selected_candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "stable_decision_window_id": wrong_window,
                "selected_action_class": "trade",
            }
        ],
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["proxy_target_status"] == "proxy_target_contract_source_gap_not_materialized"
    assert row["target_value"] is None
    assert row["order_instance_join_status"] == "exact_candidate_window_order_missing"
    assert row["oracle_instance_join_status"] == "exact_candidate_window_oracle_missing"
    assert row["scorecard_instance_join_status"] == "exact_candidate_window_scorecard_missing"


def test_phase2_proxy_targets_sum_unique_r_by_replay_instance_when_candidate_id_repeats():
    builder = load_denominator_builder()
    first_window = "decision_window:XAUUSD:LONG:2026-05-05T08:15:00+00:00"
    second_window = "decision_window:XAUUSD:LONG:2026-05-05T08:30:00+00:00"

    rows, contract, summary = builder.build_phase2_proxy_target_artifacts(
        phase2_label_value_candidate_rows=[
            {
                "label_id": "label:first",
                "clean_label_family_id": "candidate_accept_reject_label",
                "replay_candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "stable_decision_window_id": first_window,
            },
            {
                "label_id": "label:second",
                "clean_label_family_id": "candidate_accept_reject_label",
                "replay_candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:30:00+00:00",
                "stable_decision_window_id": second_window,
            },
        ],
        bridge_order_rows=[
            {
                "candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "stable_decision_window_id": first_window,
                "counterfactual_final_r": 1.25,
            },
            {
                "candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:30:00+00:00",
                "stable_decision_window_id": second_window,
                "counterfactual_final_r": 2.75,
            },
        ],
        bridge_oracle_rows=[
            {
                "candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "stable_decision_window_id": first_window,
                "counterfactual_final_r": 1.25,
            },
            {
                "candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:30:00+00:00",
                "stable_decision_window_id": second_window,
                "counterfactual_final_r": 2.75,
            },
        ],
        bridge_scorecard_rows=[
            {
                "selected_candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "stable_decision_window_id": first_window,
                "selected_action_class": "trade",
            },
            {
                "selected_candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:30:00+00:00",
                "stable_decision_window_id": second_window,
                "selected_action_class": "trade",
            },
        ],
    )

    assert [row["proxy_target_status"] for row in rows] == [
        "source_bound_proxy_target_materialized_not_training_ready",
        "source_bound_proxy_target_materialized_not_training_ready",
    ]
    assert contract["unique_replay_candidate_ids"] == 1
    assert contract["unique_replay_instance_count"] == 2
    assert contract["candidate_id_repeated_instance_count"] == 1
    assert contract["unique_candidate_proxy_final_r_sum"] == 2.75
    assert contract["unique_candidate_proxy_final_r_sum_authority"] == (
        "diagnostic_only_candidate_id_collapse"
    )
    assert contract["unique_instance_proxy_final_r_sum"] == 4.0
    assert contract["unique_instance_proxy_final_r_sum_authority"] == (
        "replay_instance_join_key_authority"
    )
    assert summary["phase2_proxy_target_instance_rows"] == 2
    assert summary["phase2_proxy_target_unique_instance_final_r_sum"] == 4.0
    assert summary["phase2_proxy_target_repeated_candidate_id_count"] == 1


def test_phase2_proxy_targets_resolve_equivalent_duplicate_order_rows():
    builder = load_denominator_builder()
    window = "decision_window:XAGUSD:LONG:2026-05-12T09:00:00+00:00"

    rows, contract, _summary = builder.build_phase2_proxy_target_artifacts(
        phase2_label_value_candidate_rows=[
            {
                "label_id": "label:proxy",
                "clean_label_family_id": "candidate_accept_reject_label",
                "replay_candidate_id": "candidate:dup",
                "symbol": "XAGUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-12T09:00:00+00:00",
                "stable_decision_window_id": window,
            }
        ],
        bridge_order_rows=[
            {
                "candidate_id": "candidate:dup",
                "selected_candidate_id": "candidate:dup",
                "symbol": "XAGUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-12T09:00:00+00:00",
                "stable_decision_window_id": window,
                "policy_net_proxy_r": -1.25,
                "risk_decision": "open-reduced-risk",
            },
            {
                "candidate_id": "candidate:dup",
                "selected_candidate_id": "candidate:dup",
                "symbol": "XAGUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-12T09:00:00+00:00",
                "stable_decision_window_id": window,
                "policy_net_proxy_r": -1.25,
                "fill_status": "filled",
                "risk_decision": "open-reduced-risk",
            },
        ],
        bridge_oracle_rows=[],
        bridge_scorecard_rows=[],
    )

    assert rows[0]["order_instance_join_status"] == (
        "exact_candidate_window_order_duplicate_equivalent_resolved"
    )
    assert rows[0]["proxy_target_status"] == "source_bound_proxy_target_materialized_not_training_ready"
    assert rows[0]["target_value"]["counterfactual_final_r"] == -1.25
    assert rows[0]["target_value"]["counterfactual_fill_status"] == "filled"
    assert contract["proxy_target_contract_ready"] is True


def test_phase2_proxy_targets_materialize_source_bound_candidate_signal_when_not_ordered():
    builder = load_denominator_builder()
    window = "decision_window:XAUUSD:SHORT:2026-05-05T08:15:00+00:00"

    rows, contract, summary = builder.build_phase2_proxy_target_artifacts(
        phase2_label_value_candidate_rows=[
            {
                "label_id": "label:source-bound",
                "clean_label_family_id": "candidate_accept_reject_label",
                "replay_candidate_id": "candidate:source-bound",
                "symbol": "XAUUSD",
                "side": "SHORT",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "stable_decision_window_id": window,
            }
        ],
        bridge_candidate_rows=[
            {
                "candidate_id": "candidate:source-bound",
                "symbol": "XAUUSD",
                "side": "SHORT",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "stable_decision_window_id": window,
                "source_bound_signal_r": 12.5,
                "selector_action": "reject",
                "selector_reason": "calibrated_admission_fill_probability_below_generalized_floor",
            }
        ],
        bridge_order_rows=[],
        bridge_oracle_rows=[],
        bridge_scorecard_rows=[],
    )

    target = rows[0]["target_value"]
    assert rows[0]["candidate_instance_join_status"] == "exact_candidate_window_candidate_joined"
    assert rows[0]["proxy_target_status"] == "source_bound_proxy_target_materialized_not_training_ready"
    assert target["counterfactual_final_r"] == 12.5
    assert target["counterfactual_final_r_source_field"].endswith(".source_bound_signal_r")
    assert target["risk_decision"] == "selector_reject_no_order_risk_not_reached"
    assert target["source_truth_scope"] == (
        "source_bound_replay_candidate_signal_not_order_or_lifecycle_truth"
    )
    assert contract["proxy_target_contract_ready"] is True
    assert summary["phase2_proxy_target_instance_rows"] == 1


def test_phase2_duplicate_collapse_reports_instance_r_authority_when_candidate_id_repeats():
    builder = load_denominator_builder()
    first_window = "decision_window:XAUUSD:LONG:2026-05-05T08:15:00+00:00"
    second_window = "decision_window:XAUUSD:LONG:2026-05-05T08:30:00+00:00"
    family_id = "candidate_accept_reject_label"

    value_rows = [
        {
            "label_id": "label:first",
            "clean_label_family_id": family_id,
            "duplicate_unit_key": f"phase2_clean_label_unit:{family_id}:{first_window}",
            "replay_candidate_id": "candidate:reused",
            "stable_decision_window_id": first_window,
            "decision_time_utc": "2026-05-05T08:15:00+00:00",
            "symbol": "XAUUSD",
            "side": "LONG",
            "label_value_status": "source_bound_proxy_target_value_materialized_not_training_ready",
            "label_value": {"target_label": "accept"},
        },
        {
            "label_id": "label:second",
            "clean_label_family_id": family_id,
            "duplicate_unit_key": f"phase2_clean_label_unit:{family_id}:{second_window}",
            "replay_candidate_id": "candidate:reused",
            "stable_decision_window_id": second_window,
            "decision_time_utc": "2026-05-05T08:30:00+00:00",
            "symbol": "XAUUSD",
            "side": "LONG",
            "label_value_status": "source_bound_proxy_target_value_materialized_not_training_ready",
            "label_value": {"target_label": "accept"},
        },
    ]
    proxy_rows = [
        {
            "label_id": "label:first",
            "clean_label_family_id": family_id,
            "replay_candidate_id": "candidate:reused",
            "replay_instance_join_key": f"candidate:reused@@{first_window}",
            "stable_decision_window_id": first_window,
            "decision_time_utc": "2026-05-05T08:15:00+00:00",
            "target_value": {"counterfactual_final_r": 1.25},
        },
        {
            "label_id": "label:second",
            "clean_label_family_id": family_id,
            "replay_candidate_id": "candidate:reused",
            "replay_instance_join_key": f"candidate:reused@@{second_window}",
            "stable_decision_window_id": second_window,
            "decision_time_utc": "2026-05-05T08:30:00+00:00",
            "target_value": {"counterfactual_final_r": 2.75},
        },
    ]

    collapse_rows, _baseline_rows, summary = (
        builder.build_phase2_duplicate_collapse_and_baseline_artifacts(
            phase2_label_value_candidate_rows=value_rows,
            phase2_proxy_target_label_rows=proxy_rows,
            phase2_split_manifest={
                "effective_decision_window_count": 2,
                "unique_replay_candidate_ids": 1,
                "split_checks": [],
            },
        )
    )

    assert len(collapse_rows) == 2
    assert all(row["replay_instance_join_keys"] for row in collapse_rows)
    assert summary["phase2_collapsed_unique_candidate_proxy_final_r_sum"] == 2.75
    assert summary["phase2_collapsed_unique_candidate_proxy_final_r_sum_authority"] == (
        "diagnostic_only_candidate_id_collapse"
    )
    assert summary["phase2_collapsed_unique_instance_proxy_final_r_sum"] == 4.0
    assert summary["phase2_collapsed_unique_instance_proxy_final_r_sum_authority"] == (
        "replay_instance_join_key_authority"
    )
    assert summary["phase2_collapsed_unique_replay_instance_count"] == 2
    assert summary["phase2_collapsed_repeated_candidate_id_count"] == 1


def test_phase2_contract_proxy_label_values_require_exact_candidate_instance():
    builder = load_denominator_builder()
    wrong_window = "decision_window:XAUUSD:LONG:2026-05-05T08:15:00+00:00"
    right_window = "decision_window:XAUUSD:LONG:2026-05-05T08:30:00+00:00"

    value_rows, *_ = builder.build_phase2_contract_artifacts(
        phase1_label_disposition_rows=[
            {
                "label_id": "label:proxy",
                "selected_package_replay_bridge_replay_candidate_ids": [
                    "candidate:reused"
                ],
            }
        ],
        phase2_clean_label_readiness_rows=[
            {
                "label_id": "label:proxy",
                "candidate_id": "label-candidate",
                "clean_label_family_id": "candidate_accept_reject_label",
                "phase2_readiness_status": "candidate_label_row_but_not_training_ready",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:30:00+00:00",
                "stable_decision_window_id": right_window,
            }
        ],
        clean_label_families=[
            {"label_id": "candidate_accept_reject_label"},
        ],
        bridge_candidate_rows=[
            {
                "candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "stable_decision_window_id": wrong_window,
            }
        ],
        bridge_order_rows=[
            {
                "candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "stable_decision_window_id": wrong_window,
                "counterfactual_final_r": 4.0,
            }
        ],
        bridge_oracle_rows=[
            {
                "candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "stable_decision_window_id": wrong_window,
                "counterfactual_final_r": 4.0,
            }
        ],
        bridge_scorecard_rows=[
            {
                "selected_candidate_id": "candidate:reused",
                "symbol": "XAUUSD",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "stable_decision_window_id": wrong_window,
                "selected_action_class": "trade",
            }
        ],
    )

    assert len(value_rows) == 1
    row = value_rows[0]
    assert row["label_value_status"] == "proxy_target_contract_source_gap_not_materialized"
    assert row["label_value"] is None
    assert row["candidate_instance_join_status"] == "exact_candidate_window_candidate_missing"
    assert row["order_instance_join_status"] == "exact_candidate_window_order_missing"
    assert row["oracle_instance_join_status"] == "exact_candidate_window_oracle_missing"
    assert row["scorecard_instance_join_status"] == "exact_candidate_window_scorecard_missing"


def test_replay_behavior_trade_enrichment_requires_exact_scorecard_and_order_instance(
    tmp_path: Path, monkeypatch
):
    builder = load_denominator_builder()
    selected_compact_path = tmp_path / "selected_compact.jsonl"
    pending_compact_path = tmp_path / "pending_compact.jsonl"
    m15_compact_path = tmp_path / "m15_compact.jsonl"
    m15_all_symbol_compact_path = tmp_path / "m15_all_symbol_compact.jsonl"
    selected_trade_path = tmp_path / "selected_trade.jsonl"
    pending_trade_path = tmp_path / "pending_trade.jsonl"
    m15_trade_path = tmp_path / "m15_trade.jsonl"
    write_jsonl(selected_compact_path, [])
    write_jsonl(pending_compact_path, [])
    write_jsonl(m15_compact_path, [])
    write_jsonl(m15_all_symbol_compact_path, [])
    write_jsonl(
        selected_trade_path,
        [
            {
                "candidate_id": "candidate:reused",
                "decision_time_utc": "2026-05-05T08:30:00+00:00",
                "simulated_trade_id": "trade-right-window",
                "symbol": "XAUUSD",
                "side": "LONG",
                "gross_r": 5.0,
                "final_r": 5.0,
                "net_r": 5.0,
                "net_proxy_r": 5.0,
            }
        ],
    )
    write_jsonl(pending_trade_path, [])
    write_jsonl(m15_trade_path, [])
    monkeypatch.setitem(
        builder.SELECTED_PACKAGE_REPLAY_BRIDGE_LEDGER_PATHS,
        "compact_candidate",
        selected_compact_path,
    )
    monkeypatch.setitem(
        builder.SELECTED_PACKAGE_REPLAY_BRIDGE_LEDGER_PATHS,
        "trade",
        selected_trade_path,
    )
    monkeypatch.setitem(
        builder.PENDING_CREATED_REPLAY_BRIDGE_LEDGER_PATHS,
        "compact_candidate",
        pending_compact_path,
    )
    monkeypatch.setitem(
        builder.PENDING_CREATED_REPLAY_BRIDGE_LEDGER_PATHS,
        "trade",
        pending_trade_path,
    )
    monkeypatch.setitem(
        builder.PHASE2_M15_GRID_EXPANSION_LEDGER_PATHS,
        "compact_candidate",
        m15_compact_path,
    )
    monkeypatch.setitem(
        builder.PHASE2_M15_GRID_EXPANSION_LEDGER_PATHS,
        "trade",
        m15_trade_path,
    )
    monkeypatch.setitem(
        builder.PHASE2_M15_GRID_ALL_SYMBOL_LEDGER_PATHS,
        "compact_candidate",
        m15_all_symbol_compact_path,
    )

    result = builder.build_ultimate_candidate_package_replay_behavior_dossier(
        candidate_rows=[],
        scorecard_rows=[
            {
                "source_namespace": "selected_package_replay_bridge",
                "package_selected_candidate_id": "candidate:reused",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "package_selected_action": "replay_take",
                "selected_order_type_architecture": "limit_first",
                "package_replay_result_r": 5.0,
                "baseline_replay_result_r": 0.0,
                "package_vs_baseline_delta_r": 5.0,
            }
        ],
        order_policy_rows=[
            {
                "source_namespace": "selected_package_replay_bridge",
                "candidate_id": "candidate:reused",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "selected_order_type_architecture": "limit_first",
            }
        ],
        replay_summary={},
        split_scorecard_summary={},
        stress_summary={},
        stress_rows=[],
        adversarial_summary={},
        reconstructed_proxy_denominator_summary={},
        reconstructed_proxy_denominator_rows=[],
        reconstructed_proxy_stress_summary={},
        reconstructed_proxy_stress_rows=[],
        reconstructed_proxy_monte_carlo_summary={},
        reconstructed_proxy_monte_carlo_rows=[],
        final_selection_summary={},
        package_selection_summary={},
        lifecycle_label_rows=0,
        exact_denominator_join_rows=0,
        generated_utc="2026-06-25T00:00:00Z",
    )

    trade_summary = result["summary"]["simulated_trade_behavior"]
    assert result["trade_rows"] == []
    assert trade_summary["trade_rows"] == 0
    assert trade_summary["source_trade_rows_excluded_without_package_scorecard"] == 1
    assert trade_summary["source_trade_excluded_unscorecarded_net_r_sum"] == 5.0


def test_replay_behavior_order_materialization_uses_blocked_reference_identity(
    tmp_path: Path, monkeypatch
):
    builder = load_denominator_builder()
    selected_compact_path = tmp_path / "selected_compact.jsonl"
    selected_trade_path = tmp_path / "selected_trade.jsonl"
    pending_trade_path = tmp_path / "pending_trade.jsonl"
    m15_trade_path = tmp_path / "m15_trade.jsonl"
    write_jsonl(
        selected_compact_path,
        [
            {
                "candidate_id": "candidate:blocked-reference-only",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "candle_close_utc": "2026-05-05T08:15:00+00:00",
                "symbol": "XAUUSD",
                "side": "LONG",
                "entry_price": 2300.0,
                "stop_loss": 2290.0,
                "take_profit_1": 2320.0,
                "trade_parameters": {
                    "entry_price": 2300.0,
                    "stop_loss": 2290.0,
                    "take_profit_1": 2320.0,
                },
                "predecision_limit_fillability": {
                    "entry_price": 2300.0,
                    "stop_loss": 2290.0,
                },
                "pretrade_cost_packet_status": "PASSED",
                "cost_source_gap_status": "source_bound_cost_authority_present",
                "cost_authority": "broker_calibrated_replay_cost",
                "pretrade_broker_net_cost_packet": {
                    "status": "PASSED",
                    "scalar_fields": {
                        "total_cost_r": 0.05,
                        "spread_r": 0.04,
                        "expected_slippage_r": 0.01,
                    },
                },
                "expected_net_r": 1.2,
                "probability": 0.8,
                "fill_probability": 0.7,
            }
        ],
    )
    write_jsonl(selected_trade_path, [])
    write_jsonl(pending_trade_path, [])
    write_jsonl(m15_trade_path, [])
    monkeypatch.setitem(
        builder.SELECTED_PACKAGE_REPLAY_BRIDGE_LEDGER_PATHS,
        "compact_candidate",
        selected_compact_path,
    )
    monkeypatch.setitem(
        builder.SELECTED_PACKAGE_REPLAY_BRIDGE_LEDGER_PATHS,
        "trade",
        selected_trade_path,
    )
    monkeypatch.setitem(
        builder.PENDING_CREATED_REPLAY_BRIDGE_LEDGER_PATHS,
        "trade",
        pending_trade_path,
    )
    monkeypatch.setitem(
        builder.PHASE2_M15_GRID_EXPANSION_LEDGER_PATHS,
        "trade",
        m15_trade_path,
    )

    result = builder.build_ultimate_candidate_package_replay_behavior_dossier(
        candidate_rows=[],
        scorecard_rows=[],
        order_policy_rows=[
            {
                "source_namespace": "selected_package_replay_bridge",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "blocked_reference_candidate_id": "candidate:blocked-reference-only",
                "blocked_reference_symbol": "XAUUSD",
                "blocked_reference_side": "LONG",
                "blocked_reference_expected_net_r": 1.2,
                "selected_order_type_architecture": "limit_first_delay_queue",
                "primary_order_type": "limit",
                "simulated_order_decisions": 1,
            }
        ],
        replay_summary={},
        split_scorecard_summary={},
        stress_summary={},
        stress_rows=[],
        adversarial_summary={},
        reconstructed_proxy_denominator_summary={},
        reconstructed_proxy_denominator_rows=[],
        reconstructed_proxy_stress_summary={},
        reconstructed_proxy_stress_rows=[],
        reconstructed_proxy_monte_carlo_summary={},
        reconstructed_proxy_monte_carlo_rows=[],
        final_selection_summary={},
        package_selection_summary={},
        lifecycle_label_rows=0,
        exact_denominator_join_rows=0,
        generated_utc="2026-06-25T00:00:00Z",
    )

    materialization = result["summary"]["package_order_policy_materialization"]
    assert materialization["source_candidate_needed_keys"] == 1
    assert materialization["source_candidate_joined_rows"] == 1
    assert materialization["source_candidate_join_missing_rows"] == 0
    assert materialization["broker_cost_passed_rows"] == 1
    assert materialization["geometry_present_rows"] == 1
    assert result["decision_rows"][0]["candidate_id"] == (
        "candidate:blocked-reference-only"
    )
    assert result["decision_rows"][0]["symbol"] == "XAUUSD"
    assert result["order_rows"][0]["materialization_status"] == (
        "source_joined_cost_passed_pending_live_as_if_order_materialization"
    )


def test_order_type_extraction_splits_architecture_from_primitive_type():
    builder = load_parity_builder()

    row = {
        "selected_order_type_architecture": "limit_first_guarded_market_fallback",
        "effective_order_type": "market",
        "primary_order_type": "limit",
        "order_type": "legacy",
        "simulated_limit_order": True,
    }
    assert (
        builder.order_architecture_from_order_row(row)
        == "limit_first_guarded_market_fallback"
    )
    assert builder.order_type_from_order_row(row) == "market"
    assert (
        builder.order_type_from_order_row(
            {
                "primary_order_type": "limit",
                "simulated_limit_order": True,
            }
        )
        == "limit"
    )
    assert (
        builder.order_type_from_order_row(
            {
                "effective_order_type": "guarded_market",
                "simulated_limit_order": True,
            }
        )
        == "market"
    )
    assert builder.order_type_from_order_row({"simulated_limit_order": True}) == "limit"


def test_namespace_materialized_lifecycle_context_gap_is_not_selected_package_source_gap():
    builder = load_parity_builder()

    assert (
        builder.executable_axis_missing_row_bound_selected_package_source(
            {
                "exact_join_status": "axis_candidate_namespace_materialized_no_lifecycle_label_context",
                "candidate_id_carried_to_member": False,
                "decision_window_id_carried_to_member": False,
                "selected_package_replay_bridge_candidate_rows": 0,
            },
            package_role="scheduler_lifecycle_core",
        )
        is False
    )
    assert (
        builder.executable_axis_missing_row_bound_selected_package_source(
            {
                "exact_join_status": "context_labels_available_but_no_selected_package_replay_rows_in_lifecycle_window",
                "candidate_id_carried_to_member": False,
                "decision_window_id_carried_to_member": False,
                "selected_package_replay_bridge_candidate_rows": 0,
            },
            package_role="scheduler_lifecycle_core",
        )
        is True
    )
    assert (
        builder.repair_stage_for_label(
            "executable_axis_candidate_namespace_materialized_no_lifecycle_label_context"
        )
        == "lifecycle_label_context_materialization"
    )


def test_selected_package_bridge_materialization_gets_source_only_label():
    builder = load_parity_builder()

    member = {
        "exact_join_status": (
            "selected_package_replay_bridge_candidate_materialized_no_lifecycle_label_join"
        ),
        "selected_package_replay_bridge_candidate_rows": 1,
        "candidate_id_carried_to_member": False,
        "decision_window_id_carried_to_member": False,
    }

    assert builder.selected_package_bridge_materialized(member) is True
    assert builder.selected_package_bridge_materialization_label(
        member,
        package_role="scheduler_lifecycle_core",
    ) == (
        "source_axis_selected_package_bridge_materialized_"
        "no_lifecycle_label_context"
    )
    member_with_axis_context = {
        **member,
        "source_axis_lifecycle_label_context_ids": ["label-axis-context"],
        "source_axis_lifecycle_label_context_rows": 1,
        "source_axis_lifecycle_context_attribution_scope": (
            "symbol_side_pair_broadcast_only"
        ),
        "source_axis_lifecycle_bridge_window_transfer_status": "source_window_missing",
        "source_materialization_transfer_status": "source_window_missing",
    }
    assert builder.selected_package_source_axis_lifecycle_context_available(
        member_with_axis_context
    ) is True
    assert builder.selected_package_lifecycle_label_context_status(
        member_with_axis_context,
        package_role="scheduler_lifecycle_core",
    ) == "pair_broadcast_lifecycle_context_available_source_window_missing"
    assert builder.selected_package_bridge_materialization_label(
        member_with_axis_context,
        package_role="scheduler_lifecycle_core",
    ) == (
        "source_axis_selected_package_bridge_materialized_"
        "pair_broadcast_lifecycle_context_source_window_missing"
    )

    member_with_pending_proxy = {
        **member_with_axis_context,
        "source_axis_lifecycle_bridge_window_transfer_status": (
            "source_window_missing_pending_created_proxy_only"
        ),
        "source_materialization_transfer_status": (
            "source_window_missing_pending_created_proxy_only"
        ),
        "source_axis_lifecycle_pending_created_proxy_only_label_count": 1,
    }
    assert builder.selected_package_lifecycle_label_context_status(
        member_with_pending_proxy,
        package_role="scheduler_lifecycle_core",
    ) == (
        "pair_broadcast_lifecycle_context_available_"
        "source_window_missing_pending_created_proxy_only"
    )
    assert builder.selected_package_bridge_materialization_label(
        member_with_pending_proxy,
        package_role="scheduler_lifecycle_core",
    ) == (
        "source_axis_selected_package_bridge_materialized_"
        "pair_broadcast_lifecycle_context_source_window_missing_"
        "pending_created_proxy_only"
    )
    member_with_window_mismatch = {
        **member_with_axis_context,
        "source_axis_lifecycle_bridge_window_transfer_status": "bridge_window_mismatch",
        "source_materialization_transfer_status": "bridge_window_mismatch",
        "source_axis_lifecycle_bridge_window_mismatch_status": (
            "different_trading_day_decision_window"
        ),
    }
    assert builder.selected_package_lifecycle_label_context_status(
        member_with_window_mismatch,
        package_role="scheduler_lifecycle_core",
    ) == (
        "pair_broadcast_lifecycle_context_available_"
        "bridge_window_mismatch_different_trading_day_decision_window"
    )
    assert builder.selected_package_bridge_materialization_label(
        member_with_window_mismatch,
        package_role="scheduler_lifecycle_core",
    ) == (
        "source_axis_selected_package_bridge_materialized_"
        "pair_broadcast_lifecycle_context_bridge_window_mismatch_"
        "different_trading_day_decision_window"
    )
    member_with_overlap = {
        **member_with_axis_context,
        "source_axis_lifecycle_bridge_window_transfer_status": "bridge_window_overlap",
        "source_materialization_transfer_status": "bridge_window_overlap",
        "source_axis_lifecycle_context_attribution_scope": "bridge_exact_denominator_join",
        "exact_denominator_join_rows": 1,
        "source_axis_lifecycle_bridge_decision_window_overlap_count": 1,
        "source_axis_lifecycle_bridge_decision_window_overlap_samples": [
            "decision_window:XAUUSD:LONG:2026-05-05T07:15:00+00:00"
        ],
    }
    assert builder.selected_package_lifecycle_label_context_status(
        member_with_overlap,
        package_role="scheduler_lifecycle_core",
    ) == (
        "axis_lifecycle_label_context_bridge_window_overlap_but_"
        "denominator_authority_closed"
    )
    assert builder.selected_package_bridge_materialization_label(
        member_with_overlap,
        package_role="scheduler_lifecycle_core",
    ) == (
        "source_axis_selected_package_bridge_materialized_"
        "axis_lifecycle_label_context_bridge_window_overlap"
    )
    member_with_closed_overlap = {
        **member_with_axis_context,
        "source_axis_lifecycle_bridge_window_transfer_status": (
            "bridge_window_overlap_pair_broadcast_context_only"
        ),
        "source_materialization_transfer_status": (
            "bridge_window_overlap_pair_broadcast_context_only"
        ),
        "source_axis_lifecycle_bridge_decision_window_overlap_count": 1,
    }
    assert builder.selected_package_lifecycle_label_context_status(
        member_with_closed_overlap,
        package_role="scheduler_lifecycle_core",
    ) == (
        "pair_broadcast_lifecycle_context_bridge_window_overlap_"
        "denominator_authority_closed"
    )
    assert builder.selected_package_bridge_materialization_label(
        member_with_closed_overlap,
        package_role="scheduler_lifecycle_core",
    ) == (
        "source_axis_selected_package_bridge_materialized_"
        "pair_broadcast_lifecycle_context_bridge_window_overlap_"
        "denominator_authority_closed"
    )
    member_with_legacy_aggregate_context = {
        **member,
        "context_lifecycle_label_rows": 7,
    }
    assert builder.selected_package_source_axis_lifecycle_context_available(
        member_with_legacy_aggregate_context
    ) is False
    assert builder.selected_package_lifecycle_label_context_status(
        member_with_legacy_aggregate_context,
        package_role="scheduler_lifecycle_core",
    ) == "axis_lifecycle_label_context_aggregate_only_producer_gap"
    assert builder.selected_package_bridge_materialization_label(
        member_with_legacy_aggregate_context,
        package_role="scheduler_lifecycle_core",
    ) == (
        "source_axis_selected_package_bridge_materialized_"
        "axis_lifecycle_label_context_aggregate_only_producer_gap"
    )
    member_with_context = {
        **member,
        "selected_package_replay_bridge_lifecycle_label_context_present": True,
        "selected_package_replay_bridge_lifecycle_label_context_rows": 2,
        "fillability_label_families": ["active_pending_no_entry_touch_internal_lifecycle"],
    }
    assert builder.selected_package_bridge_materialization_label(
        member_with_context,
        package_role="scheduler_lifecycle_core",
    ) == (
        "source_axis_selected_package_bridge_materialized_"
        "window_lifecycle_label_context_denominator_authority_closed"
    )
    member_with_exact_context = {
        **member_with_context,
        "exact_denominator_join_rows": 2,
        "source_axis_lifecycle_context_attribution_scope": "bridge_exact_denominator_join",
    }
    assert builder.selected_package_bridge_materialization_label(
        member_with_exact_context,
        package_role="scheduler_lifecycle_core",
    ) == (
        "source_axis_selected_package_bridge_materialized_"
        "stable_window_lifecycle_label_context"
    )
    member_with_stable_window_label_count = {
        **member,
        "selected_package_replay_bridge_label_window_match_count": 3,
    }
    assert builder.selected_package_bridge_materialization_label(
        member_with_stable_window_label_count,
        package_role="scheduler_lifecycle_core",
    ) == (
        "source_axis_selected_package_bridge_materialized_"
        "window_lifecycle_label_context_denominator_authority_closed"
    )
    assert builder.repair_stage_for_label(
        "source_axis_selected_package_bridge_materialized_no_lifecycle_label_context"
    ) == "selected_package_bridge_lifecycle_context_materialization"
    assert builder.repair_stage_for_label(
        "source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_not_stable_window_matched"
    ) == "selected_package_bridge_stable_window_lifecycle_context_materialization"
    assert builder.repair_stage_for_label(
        "source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_source_window_missing"
    ) == "selected_package_bridge_stable_window_lifecycle_context_materialization"
    assert builder.repair_stage_for_label(
        "source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_bridge_window_mismatch"
    ) == "selected_package_bridge_stable_window_lifecycle_context_materialization"
    assert builder.repair_stage_for_label(
        "source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_source_window_missing_pending_created_proxy_only"
    ) == "selected_package_bridge_stable_window_lifecycle_context_materialization"
    assert builder.repair_stage_for_label(
        "source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_bridge_window_mismatch_different_trading_day_decision_window"
    ) == "selected_package_bridge_stable_window_lifecycle_context_materialization"
    assert builder.repair_stage_for_label(
        "source_axis_selected_package_bridge_materialized_pair_broadcast_lifecycle_context_source_window_missing_pending_created_proxy_only"
    ) == "selected_package_bridge_stable_window_lifecycle_context_materialization"
    assert builder.repair_stage_for_label(
        "source_axis_selected_package_bridge_materialized_pair_broadcast_lifecycle_context_bridge_window_mismatch_same_trading_day_different_decision_window"
    ) == "selected_package_bridge_stable_window_lifecycle_context_materialization"
    assert builder.repair_stage_for_label(
        "source_axis_selected_package_bridge_materialized_window_lifecycle_label_context_denominator_authority_closed"
    ) == "selected_package_bridge_stable_window_lifecycle_context_materialization"
    assert builder.repair_stage_for_label(
        "source_axis_selected_package_bridge_materialized_axis_lifecycle_label_context_aggregate_only_producer_gap"
    ) == "selected_package_bridge_lifecycle_context_materialization"


def test_package_authority_materialization_uses_explicit_member_axis_ids():
    builder = load_denominator_builder()
    members = [
        {
            "source_axis_row_index": 1,
            "stable_member_axis_id": "member_axis:heuristic",
            "sleeve_id": "sleeve-heuristic",
            "symbol": "EURUSD",
            "side": "SHORT",
            "framework": "broader_origin",
            "origin_family": "displacement_continuation",
            "session_bucket": "london_broad",
        },
        {
            "source_axis_row_index": 2,
            "stable_member_axis_id": "member_axis:explicit-target",
            "sleeve_id": "sleeve-explicit",
            "symbol": "EURUSD",
            "side": "SHORT",
            "framework": "broader_origin",
            "origin_family": "different_origin_family",
            "session_bucket": "tokyo_broad",
        },
    ]
    rows = builder.package_authority_candidate_materialization_rows(
        candidate_rows=[
            {
                "candidate_id": "candidate-explicit",
                "decision_time_utc": "2026-05-05T08:00:00+00:00",
                "stable_decision_window_id": (
                    "decision_window:EURUSD:SHORT:2026-05-05T08:00:00+00:00"
                ),
                "symbol": "EURUSD",
                "side": "SHORT",
                "framework": "broader_origin",
                "origin_family": "displacement_continuation",
                "session_tokens": ["london_broad"],
                "ultimate_package_matched_member_axis_ids": [
                    "member_axis:explicit-target"
                ],
                "package_replay_candidate_use_allowed": True,
            }
        ],
        members=members,
    )

    assert len(rows) == 1
    assert rows[0]["matched_source_axis_row_indexes"] == [1, 2]
    assert rows[0]["matched_stable_member_axis_ids"] == [
        "member_axis:explicit-target",
        "member_axis:heuristic",
    ]
    assert rows[0]["candidate_explicit_stable_member_axis_ids"] == [
        "member_axis:explicit-target"
    ]
    assert (
        rows[0]["candidate_axis_materialization_binding_status"]
        == "explicit_and_heuristic_member_axis_binding"
    )


def test_repair_plan_ranks_source_gap_by_diagnostic_source_bound_r():
    builder = load_parity_builder()

    bucket_rows = builder.build_leakage_buckets(
        [
            {
                "broad_replay_observation_status": "completed_broad_replay_summary_present",
                "broad_replay_profile": "repaired",
                "sleeve_type": "scheduler_lifecycle_merge_sleeve",
                "package_role": "scheduler_lifecycle_core",
                "framework": "fvg_fill",
                "origin_family": "current_fvg_fill",
                "side": "LONG",
                "symbol": "XAUUSD",
                "session_bucket": "london_broad",
                "execution_leakage_label": (
                    "source_axis_selected_package_bridge_materialized_"
                    "axis_lifecycle_label_context_not_stable_window_matched"
                ),
                "candidate_generation_label": "candidate_generated_via_selected_package_bridge",
                "selected_package_bridge_candidate_generated": True,
                "diagnostic_source_bound_r": 1000.0,
                "source_bound_r": 0.0,
            },
            {
                "broad_replay_observation_status": "completed_broad_replay_summary_present",
                "broad_replay_profile": "repaired",
                "sleeve_type": "scheduler_lifecycle_merge_sleeve",
                "package_role": "scheduler_lifecycle_core",
                "framework": "fvg_fill",
                "origin_family": "current_fvg_fill",
                "side": "SHORT",
                "symbol": "XAUUSD",
                "session_bucket": "london_broad",
                "execution_leakage_label": "scheduler_selected_no_order_row",
                "candidate_generation_label": "candidate_generated",
                "diagnostic_source_bound_r": 5.0,
                "source_bound_r": 5.0,
            },
        ],
        "2026-07-07T13:30:00Z",
    )

    plan = builder.build_execution_leakage_repair_plan(
        summary={},
        bucket_rows=bucket_rows,
        observation_status="completed_broad_replay_summary_present",
    )

    first = plan["repair_actions"][0]
    assert (
        first["stage"]
        == "selected_package_bridge_stable_window_lifecycle_context_materialization"
    )
    assert first["diagnostic_source_bound_r_sum"] == 1000.0
    assert first["source_bound_r_sum"] == 0.0


def test_package_authority_candidate_materializes_member_axis_with_namespace_aliases():
    builder = load_denominator_builder()

    rows = builder.package_authority_candidate_materialization_rows(
        candidate_rows=[
            {
                "candidate_id": "candidate:alias-materialized",
                "source_namespace": "fixture_replay_authority",
                "symbol": "AUDJPY",
                "side": "LONG",
                "framework": "origin_liquidity_sweep_reclaim",
                "origin_family": "liquidity_sweep_reclaim",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "package_replay_candidate_use_allowed": True,
                "selected_by_package_replay": True,
                "role_disposition": "admission_candidate",
                "matched_sleeve_count": 1,
                "admission_sleeve_match_count": 1,
                "lifecycle_label_context_present": True,
                "lifecycle_label_context_row_count": 1,
                "pending_lifecycle_v4_state_group": "active_pending",
                "pending_lifecycle_v4_state_groups": ["active_pending"],
                "fillability_label_family": (
                    "active_pending_no_entry_touch_internal_lifecycle"
                ),
                "fillability_label_families": [
                    "active_pending_no_entry_touch_internal_lifecycle"
                ],
                "fill_no_fill_label": "no_fill_still_pending",
                "fill_no_fill_labels": ["no_fill_still_pending"],
            }
        ],
        members=[
            {
                "source_axis_row_index": 12,
                "symbol": "AUDJPY",
                "side": "LONG",
                "framework": "broader_origin",
                "origin_family": "current_liquidity_sweep_reclaim",
                "session_bucket": "london_broad",
            }
        ],
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["replay_candidate_id"] == "candidate:alias-materialized"
    assert row["matched_source_axis_row_indexes"] == [12]
    assert row["selected_package_replay_row"] is True
    assert row["selected_package_denominator_use_allowed"] is False
    assert row["source_truth_scope"] == (
        "local_replay_authority_candidate_axis_match_not_exact_historical_denominator"
    )
    assert row["lifecycle_label_context_present"] is True
    assert row["pending_lifecycle_v4_state_group"] == "active_pending"
    assert row["fillability_label_families"] == [
        "active_pending_no_entry_touch_internal_lifecycle"
    ]
    assert row["stable_decision_window_id"] == (
        "decision_window:AUDJPY:LONG:2026-05-05T08:15:00+00:00"
    )


def test_selected_package_bridge_emits_stable_member_axis_ids():
    spec = importlib.util.spec_from_file_location(
        "run_selected_package_replay_bridge",
        ROOT
        / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
        / "run_selected_package_replay_bridge.py",
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    member = {
        "source_axis_row_index": 12,
        "stable_member_axis_id": "member_axis:preexisting-stable-id",
        "sleeve_id": "sleeve-a",
        "symbol": "AUDJPY",
        "side": "LONG",
        "framework": "broader_origin",
        "origin_family": "current_liquidity_sweep_reclaim",
        "session_bucket": "london_broad",
        "sleeve_type": "scheduler_lifecycle_merge_sleeve",
        "combined_source_bound_signal_r": 12.5,
    }
    candidate = {
        "candidate_id": "candidate-a",
        "symbol": "AUDJPY",
        "side": "LONG",
        "framework": "origin_liquidity_sweep_reclaim",
        "origin_family": "liquidity_sweep_reclaim",
        "session_bucket": "london",
        "decision_time_utc": "2026-05-05T08:15:00+00:00",
        "expected_net_r": 0.64,
        "probability": 0.78,
        "confidence": 0.72,
        "fill_probability": 0.42,
        "source_completeness": 1.0,
        "selector_action": "reject",
        "selector_reason": "admission_quality_dynamic_router_refused_candidate_use",
    }

    bridge_rows, _label_rows, summary = module.build_denominator_bridge(
        candidates=[candidate],
        members=[member],
        labels=[],
        decision_time_source="lifecycle-labels",
    )

    assert summary["selected_package_candidate_rows"] == 1
    instance_key = "candidate-a@@2026-05-05T08:15:00+00:00"
    assert bridge_rows[0]["matched_source_axis_row_indexes"] == [12]
    assert bridge_rows[0]["matched_stable_member_axis_ids"] == [
        "member_axis:preexisting-stable-id"
    ]
    assert bridge_rows[0]["canonical_replay_candidate_instance_key"] == instance_key
    assert bridge_rows[0]["risk_finalizer_probe_instance_key"] == instance_key
    assert bridge_rows[0]["source_bound_replay_candidate_instance_key"] == instance_key
    assert bridge_rows[0]["candidate_instance_identity_status"] == "materialized"
    assert (
        bridge_rows[0]["candidate_decision_quality_source_boundary"]
        == "selected_package_bridge_predecision_quality_alias_repair"
    )
    assert bridge_rows[0]["source_boundary"] == "source_bound_asof_timewarp_decision_input"
    assert bridge_rows[0]["expected_net_r"] == 0.64
    assert bridge_rows[0]["candidate_expected_net_r"] == 0.64
    assert bridge_rows[0]["probability"] == 0.78
    assert bridge_rows[0]["candidate_probability"] == 0.78
    assert bridge_rows[0]["confidence"] == 0.72
    assert bridge_rows[0]["candidate_confidence"] == 0.72
    assert bridge_rows[0]["fill_probability"] == 0.42
    assert bridge_rows[0]["execution_fill_probability"] is None
    assert (
        bridge_rows[0]["execution_fill_probability_source"]
        == "execution_fillability_missing_source_bound_input"
    )
    assert bridge_rows[0]["entry_quality_fill_probability"] == 0.42
    assert bridge_rows[0]["candidate_fill_probability"] == 0.42
    assert bridge_rows[0]["source_completeness"] == 1.0
    bridge_quality = bridge_rows[0]["candidate_decision_quality"]
    assert bridge_quality["expected_net_r"] == 0.64
    assert bridge_quality["candidate_expected_net_r"] == 0.64
    assert bridge_quality["probability"] == 0.78
    assert bridge_quality["candidate_probability"] == 0.78
    assert bridge_quality["confidence"] == 0.72
    assert bridge_quality["candidate_confidence"] == 0.72
    assert bridge_quality["fill_probability"] == 0.42
    assert bridge_quality["execution_fill_probability"] is None
    assert (
        bridge_quality["execution_fill_probability_source"]
        == "execution_fillability_missing_source_bound_input"
    )
    assert bridge_quality["entry_quality_fill_probability"] == 0.42
    assert bridge_quality["candidate_fill_probability"] == 0.42
    assert bridge_quality["source_completeness"] == 1.0
    assert (
        bridge_quality["candidate_decision_quality_source_boundary"]
        == "selected_package_bridge_predecision_quality_alias_repair"
    )
    assert bridge_rows[0]["selector_action"] == "reject"
    assert bridge_rows[0]["selector_reason"] == (
        "admission_quality_dynamic_router_refused_candidate_use"
    )
    assert bridge_rows[0]["source_bound_package_candidate_use_allowed"] is False
    assert bridge_rows[0]["ultimate_package_source_bound_candidate_use_allowed"] is False
    assert bridge_rows[0]["package_replay_source_bound_candidate_use_allowed"] is False
    assert bridge_rows[0]["package_replay_candidate_use_allowed"] is False
    assert bridge_rows[0]["package_replay_executable_candidate_use_allowed"] is False
    assert bridge_rows[0]["replay_candidate_use_allowed_now"] is False
    assert bridge_rows[0]["replay_candidate_use_allowed_now_reason"] == (
        "no_package_axis_or_candidate_use_alias"
    )
    assert bridge_rows[0]["ultimate_package_matched_member_axis_count"] == 1
    assert bridge_rows[0]["ultimate_package_admission_member_axis_match_count"] == 1
    assert bridge_rows[0]["ultimate_package_member_axis_source_bound_signal_r_sum"] == 0.0
    assert bridge_rows[0]["ultimate_package_effective_admission_count"] == 0.0
    assert bridge_rows[0]["diagnostic_ultimate_package_effective_source_bound_signal_r"] == 12.5
    assert bridge_rows[0]["missed_opportunity_ultimate_package_effective_source_bound_signal_r"] == 12.5
    assert bridge_rows[0]["ultimate_package_effective_source_bound_signal_r"] == 0.0
    assert (
        bridge_rows[0]["ultimate_package_effective_source_bound_candidate_use_allowed"]
        is False
    )
    assert (
        bridge_rows[0][
            "diagnostic_ultimate_package_effective_source_bound_candidate_use_allowed"
        ]
        is False
    )
    assert (
        bridge_rows[0]["ultimate_package_effective_executable_authority_allowed"]
        is False
    )
    assert (
        bridge_rows[0]["ultimate_package_effective_source_bound_non_executable_reason"]
        == "no_package_axis_or_candidate_use_alias"
    )
    assert bridge_rows[0]["ultimate_package_effective_evidence_source"] == (
        "member_axis_overlap_diagnostic_only"
    )
    assert bridge_rows[0]["ultimate_package_executable_admission_status"] == (
        "member_axis_overlap_diagnostic_only"
    )
    assert bridge_rows[0]["ultimate_package_scheduler_consumed_status"] == (
        "diagnostic_not_scheduler_consumed"
    )
    compact_rows = module.compact_candidate_rows([candidate], bridge_rows)
    assert compact_rows[0]["compact_candidate_schema_version"] == 2
    assert compact_rows[0]["canonical_replay_candidate_instance_key"] == instance_key
    assert compact_rows[0]["risk_finalizer_probe_instance_key"] == instance_key
    assert compact_rows[0]["source_bound_replay_candidate_instance_key"] == instance_key
    assert compact_rows[0]["candidate_instance_identity_status"] == "materialized"
    assert (
        compact_rows[0]["candidate_decision_quality_source_boundary"]
        == "selected_package_bridge_predecision_quality_alias_repair"
    )
    compact_quality = compact_rows[0]["candidate_decision_quality"]
    assert compact_quality["expected_net_r"] == 0.64
    assert compact_quality["probability"] == 0.78
    assert compact_quality["fill_probability"] == 0.42
    assert compact_quality["source_completeness"] == 1.0
    assert (
        compact_quality["candidate_decision_quality_source_boundary"]
        == "selected_package_bridge_predecision_quality_alias_repair"
    )
    assert compact_rows[0]["source_boundary"] == "source_bound_asof_timewarp_decision_input"
    assert compact_rows[0]["matched_stable_member_axis_ids"] == [
        "member_axis:preexisting-stable-id"
    ]
    assert compact_rows[0]["source_bound_package_candidate_use_allowed"] is False
    assert compact_rows[0]["ultimate_package_source_bound_candidate_use_allowed"] is False
    assert compact_rows[0]["package_replay_source_bound_candidate_use_allowed"] is False
    assert compact_rows[0]["package_replay_candidate_use_allowed"] is False
    assert compact_rows[0]["package_replay_executable_candidate_use_allowed"] is False
    assert compact_rows[0]["replay_candidate_use_allowed_now"] is False
    assert compact_rows[0]["replay_candidate_use_allowed_now_reason"] == (
        "no_package_axis_or_candidate_use_alias"
    )
    assert compact_rows[0]["ultimate_package_admission_member_axis_match_count"] == 1
    assert compact_rows[0]["ultimate_package_effective_admission_count"] == 0.0
    assert (
        compact_rows[0][
            "diagnostic_ultimate_package_effective_source_bound_candidate_use_allowed"
        ]
        is False
    )
    assert compact_rows[0]["ultimate_package_effective_evidence_source"] == (
        "member_axis_overlap_diagnostic_only"
    )
    assert compact_rows[0]["ultimate_package_executable_admission_status"] == (
        "member_axis_overlap_diagnostic_only"
    )
    assert compact_rows[0]["ultimate_package_scheduler_consumed_status"] == (
        "diagnostic_not_scheduler_consumed"
    )
    assert compact_rows[0]["candidate_fill_probability"] == 0.42
    assert compact_rows[0]["candidate_expected_net_r"] == 0.64
    assert compact_rows[0]["candidate_probability"] == 0.78
    assert compact_rows[0]["candidate_confidence"] == 0.72
    assert compact_rows[0]["selected_package_candidate_use_allowed_status"] == (
        "no_package_axis_or_candidate_use_alias"
    )
    assert compact_rows[0]["selected_package_denominator_use_allowed"] is False
    assert compact_rows[0]["final_package_selection_allowed"] is False
    assert module.stable_member_axis_id(member) == "member_axis:preexisting-stable-id"


def test_selected_package_bridge_recovers_axis_index_from_candidate_stable_axis_id():
    module = load_selected_package_replay_bridge()

    member = {
        "source_axis_row_index": 12,
        "stable_member_axis_id": "member_axis:stable-carried",
        "sleeve_id": "sleeve-carried",
        "symbol": "AUDJPY",
        "side": "LONG",
        "framework": "broader_origin",
        "origin_family": "current_liquidity_sweep_reclaim",
        "session_bucket": "tokyo_broad",
        "sleeve_type": "scheduler_lifecycle_merge_sleeve",
    }
    candidate = {
        "candidate_id": "candidate-carried-axis",
        "symbol": "AUDJPY",
        "side": "LONG",
        "framework": "origin_liquidity_sweep_reclaim",
        "origin_family": "liquidity_sweep_reclaim",
        "session_bucket": "london",
        "decision_time_utc": "2026-05-05T08:15:00+00:00",
        "ultimate_package_matched_member_axis_ids": ["member_axis:stable-carried"],
    }

    bridge_rows, label_rows, summary = module.build_denominator_bridge(
        candidates=[candidate],
        members=[member],
        labels=[
            {
                "label_id": "label-window-context",
                "candidate_id": "different-candidate",
                "symbol": "AUDJPY",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "pending_lifecycle_v4_state_group": "active_pending",
                "fillability_label_family": "active_pending_no_entry_touch_internal_lifecycle",
                "fill_no_fill_label": "no_fill_still_pending",
            }
        ],
        decision_time_source="lifecycle-labels",
    )

    assert summary["selected_package_candidate_rows"] == 1
    assert bridge_rows[0]["matched_source_axis_row_indexes"] == [12]
    assert bridge_rows[0]["matched_stable_member_axis_ids"] == [
        "member_axis:stable-carried"
    ]
    assert bridge_rows[0]["selected_package_matched_member_axis_ids"] == [
        "member_axis:stable-carried"
    ]
    assert bridge_rows[0]["selected_package_denominator_use_allowed"] is False
    assert bridge_rows[0]["selected_package_denominator_use_reason"] == (
        "stable_window_lifecycle_context_present_denominator_authority_closed"
    )
    assert label_rows[0]["matched_source_axis_row_indexes"] == [12]
    assert label_rows[0]["matched_stable_member_axis_ids"] == [
        "member_axis:stable-carried"
    ]
    assert label_rows[0]["selected_package_matched_member_axis_ids"] == [
        "member_axis:stable-carried"
    ]
    assert label_rows[0]["selected_package_denominator_use_allowed"] is False
    assert label_rows[0]["selected_package_denominator_use_reason"] == (
        "stable_window_lifecycle_context_present_denominator_authority_closed"
    )
    assert label_rows[0]["lifecycle_label_context_present"] is True


def test_denominator_materialization_resolves_stable_axis_id_to_source_index():
    builder = load_denominator_builder()

    assert builder.source_axis_indexes_for_materialization_row(
        {
            "selected_package_replay_row": True,
            "matched_stable_member_axis_ids": ["member_axis:stable-a"],
        },
        member_index_by_stable_axis_id={"member_axis:stable-a": 12},
    ) == [12]
    assert builder.source_axis_indexes_for_materialization_row(
        {
            "selected_package_replay_row": True,
            "matched_source_axis_row_indexes": [7],
            "matched_stable_member_axis_ids": ["member_axis:stable-a"],
        },
        member_index_by_stable_axis_id={"member_axis:stable-a": 12},
    ) == [7, 12]


def test_denominator_builder_stabilizes_axis_lifecycle_context_ids():
    builder = load_denominator_builder()

    label = {
        "label_id": "label-axis-context",
        "symbol": "AUDJPY",
        "side": "LONG",
        "decision_time_utc": "2026-05-05T08:15:00+00:00",
    }

    assert builder.stable_lifecycle_label_context_id(label) == "label-axis-context"
    assert builder.stable_decision_window_id_for_label(label) == (
        "decision_window:AUDJPY:LONG:2026-05-05T08:15:00+00:00"
    )
    assert (
        builder.lifecycle_bridge_window_transfer_status(
            source_axis_lifecycle_label_context_ids={"label-axis-context"},
            source_axis_lifecycle_decision_windows={
                "decision_window:AUDJPY:LONG:2026-05-05T08:15:00+00:00"
            },
            selected_package_bridge_decision_windows={
                "decision_window:AUDJPY:LONG:2026-05-05T08:15:00+00:00"
            },
        )
        == "bridge_window_overlap"
    )
    assert (
        builder.lifecycle_bridge_window_transfer_status(
            source_axis_lifecycle_label_context_ids={"label-axis-context"},
            source_axis_lifecycle_decision_windows=set(),
            selected_package_bridge_decision_windows={
                "decision_window:AUDJPY:LONG:2026-05-05T08:15:00+00:00"
            },
        )
        == "source_window_missing"
    )
    assert (
        builder.lifecycle_bridge_window_transfer_status(
            source_axis_lifecycle_label_context_ids={"label-axis-context"},
            source_axis_lifecycle_decision_windows=set(),
            selected_package_bridge_decision_windows={
                "decision_window:AUDJPY:LONG:2026-05-05T08:15:00+00:00"
            },
            source_axis_lifecycle_pending_created_proxy_only_label_ids={
                "label-axis-context"
            },
            source_axis_lifecycle_missing_decision_label_ids={"label-axis-context"},
        )
        == "source_window_missing_pending_created_proxy_only"
    )
    assert (
        builder.lifecycle_source_window_recoverability_status(
            source_axis_lifecycle_label_context_ids={"label-axis-context"},
            source_axis_lifecycle_decision_windows=set(),
            source_axis_lifecycle_pending_created_proxy_only_label_ids={
                "label-axis-context"
            },
            source_axis_lifecycle_exact_decision_time_recovered_label_ids=set(),
            source_axis_lifecycle_missing_decision_label_ids={"label-axis-context"},
        )
        == "pending_created_proxy_only_not_exact_decision_time"
    )
    assert (
        builder.lifecycle_bridge_window_transfer_status(
            source_axis_lifecycle_label_context_ids={"label-axis-context"},
            source_axis_lifecycle_decision_windows={
                "decision_window:AUDJPY:LONG:2026-05-05T08:15:00+00:00"
            },
            selected_package_bridge_decision_windows=set(),
        )
        == "bridge_window_missing"
    )
    assert (
        builder.lifecycle_bridge_window_mismatch_status(
            source_axis_lifecycle_decision_windows={
                "decision_window:AUDJPY:LONG:2026-05-05T08:15:00+00:00"
            },
            selected_package_bridge_decision_windows={
                "decision_window:AUDJPY:LONG:2026-05-06T08:15:00+00:00"
            },
        )
        == "different_trading_day_decision_window"
    )
    fallback_id = builder.stable_lifecycle_label_context_id(
        {
            "symbol": "AUDJPY",
            "side": "LONG",
            "decision_time_utc": "2026-05-05T08:15:00+00:00",
            "candidate_id": "candidate-a",
        }
    )
    assert fallback_id.startswith("lifecycle_label_context:")


def test_parity_distinguishes_selected_package_source_gap_labels():
    builder = load_parity_builder()
    executable_role = "scheduler_lifecycle_core"

    source_missing = {
        "exact_join_status": (
            "context_labels_available_but_no_selected_package_replay_rows_in_lifecycle_window"
        ),
        "selected_package_replay_bridge_candidate_rows": 0,
        "candidate_id_carried_to_member": False,
        "decision_window_id_carried_to_member": False,
    }
    namespace_only = {
        "exact_join_status": "axis_candidate_namespace_materialized_no_lifecycle_label_context",
        "selected_package_replay_bridge_candidate_rows": 0,
        "candidate_id_carried_to_member": False,
        "decision_window_id_carried_to_member": False,
    }

    assert builder.selected_package_replay_source_materialization_status(
        source_missing,
        package_role=executable_role,
    ) == "selected_package_replay_source_not_materialized_in_current_lifecycle_window"
    assert builder.selected_package_lifecycle_label_context_status(
        namespace_only,
        package_role=executable_role,
    ) == "candidate_namespace_materialized_lifecycle_label_context_source_gap"
    assert builder.repair_stage_for_label(
        "selected_package_lifecycle_context_without_current_replay_source_materialization"
    ) == "selected_package_replay_source_materialization"
    assert builder.repair_stage_for_label(
        "selected_package_candidate_namespace_materialized_lifecycle_label_context_source_gap"
    ) == "lifecycle_label_context_materialization"


def test_parity_reclassifies_missing_selected_package_source_statuses(
    tmp_path,
    monkeypatch,
):
    builder = load_parity_builder()
    monkeypatch.setattr(builder, "ROUTE", tmp_path)
    monkeypatch.setattr(builder, "BROAD_PREFIX", "BROAD_LIVE_AS_IF_REPLAY_UNIT")
    monkeypatch.setattr(
        builder,
        "BROAD_SUMMARY_PATH",
        tmp_path / "BROAD_LIVE_AS_IF_REPLAY_UNIT_SUMMARY.json",
    )
    monkeypatch.setattr(
        builder,
        "BROAD_CANDIDATE_PATH",
        tmp_path / "BROAD_LIVE_AS_IF_REPLAY_UNIT_CANDIDATE_LEDGER.jsonl",
    )
    monkeypatch.setattr(
        builder,
        "BROAD_CANDIDATE_INDEX_PATH",
        tmp_path / "BROAD_LIVE_AS_IF_REPLAY_UNIT_CANDIDATE_INDEX_LEDGER.jsonl",
    )
    for attr, suffix in (
        ("BROAD_SCORECARD_PATH", "SCORECARD"),
        ("BROAD_ORDER_PATH", "ORDER"),
        ("BROAD_ORACLE_PATH", "ORDERED_PATH_ORACLE"),
        ("BROAD_TRADE_PATH", "TRADE"),
        ("BROAD_MISSED_PATH", "MISSED_OPPORTUNITY"),
        ("BROAD_PACKET_SIDECAR_PATH", "PACKET_SIDECAR"),
        ("BROAD_COMPARISON_PATH", "COMPARISON"),
    ):
        monkeypatch.setattr(
            builder,
            attr,
            tmp_path / f"BROAD_LIVE_AS_IF_REPLAY_UNIT_{suffix}_LEDGER.jsonl",
        )
    monkeypatch.setattr(
        builder,
        "PACKAGE_CANDIDATE_PATH",
        tmp_path / "ULTIMATE_CANDIDATE_PACKAGE_REPLAY_AUTHORITY_CANDIDATE_LEDGER.jsonl",
    )
    monkeypatch.setattr(
        builder,
        "SLEEVE_MEMBER_PATH",
        tmp_path / "SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl",
    )

    builder.BROAD_SUMMARY_PATH.write_text(
        json.dumps(
            {
                "status": "broad_live_as_if_replay_materialized_broker_live_closed",
                "profiles": ["unit_profile"],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    for path in (
        builder.BROAD_CANDIDATE_PATH,
        builder.BROAD_SCORECARD_PATH,
        builder.BROAD_ORDER_PATH,
        builder.BROAD_ORACLE_PATH,
        builder.BROAD_TRADE_PATH,
        builder.BROAD_MISSED_PATH,
        builder.BROAD_PACKET_SIDECAR_PATH,
        builder.BROAD_COMPARISON_PATH,
        builder.PACKAGE_CANDIDATE_PATH,
    ):
        write_jsonl(path, [])
    write_jsonl(
        builder.SLEEVE_MEMBER_PATH,
        [
            {
                "source_axis_row_index": 1,
                "stable_member_axis_id": "member_axis:missing-source",
                "sleeve_id": "sleeve-missing-source",
                "sleeve_type": "scheduler_lifecycle_merge_sleeve",
                "package_role": "scheduler_lifecycle_core",
                "symbol": "AUDJPY",
                "side": "LONG",
                "framework": "broader_origin",
                "origin_family": "current_liquidity_sweep_reclaim",
                "session_bucket": "london_broad",
                "combined_source_bound_signal_r": 1.0,
                "exact_join_status": (
                    "context_labels_available_but_no_selected_package_replay_rows_in_lifecycle_window"
                ),
                "selected_package_replay_bridge_candidate_rows": 0,
                "candidate_id_carried_to_member": False,
                "decision_window_id_carried_to_member": False,
            },
            {
                "source_axis_row_index": 2,
                "stable_member_axis_id": "member_axis:no-selector",
                "sleeve_id": "sleeve-no-selector",
                "sleeve_type": "scheduler_lifecycle_merge_sleeve",
                "package_role": "scheduler_lifecycle_core",
                "symbol": "GBPJPY",
                "side": "SHORT",
                "framework": "broader_origin",
                "origin_family": "current_liquidity_sweep_reclaim",
                "session_bucket": "ny_broad",
                "combined_source_bound_signal_r": 2.0,
                "exact_join_status": "no_hydrated_selector_candidate_rows_for_member_axis",
                "selected_package_replay_bridge_candidate_rows": 0,
                "candidate_id_carried_to_member": False,
                "decision_window_id_carried_to_member": False,
            },
            {
                "source_axis_row_index": 3,
                "stable_member_axis_id": "member_axis:namespace-only",
                "sleeve_id": "sleeve-namespace-only",
                "sleeve_type": "scheduler_lifecycle_merge_sleeve",
                "package_role": "scheduler_lifecycle_core",
                "symbol": "EURUSD",
                "side": "LONG",
                "framework": "broader_origin",
                "origin_family": "current_liquidity_sweep_reclaim",
                "session_bucket": "tokyo_broad",
                "combined_source_bound_signal_r": 3.0,
                "exact_join_status": "axis_candidate_namespace_materialized_no_lifecycle_label_context",
                "selected_package_replay_bridge_candidate_rows": 0,
                "candidate_id_carried_to_member": False,
                "decision_window_id_carried_to_member": False,
            },
            {
                "source_axis_row_index": 4,
                "stable_member_axis_id": "member_axis:bridge-context",
                "sleeve_id": "sleeve-bridge-context",
                "sleeve_type": "scheduler_lifecycle_merge_sleeve",
                "package_role": "scheduler_lifecycle_core",
                "symbol": "XAUUSD",
                "side": "LONG",
                "framework": "broader_origin",
                "origin_family": "current_liquidity_sweep_reclaim",
                "session_bucket": "london_broad",
                "combined_source_bound_signal_r": 4.0,
                "exact_join_status": "selected_package_replay_bridge_candidate_materialized_no_lifecycle_label_join",
                "selected_package_replay_bridge_candidate_rows": 1,
                "selected_package_replay_bridge_lifecycle_label_context_rows": 1,
                "candidate_id_carried_to_member": True,
                "decision_window_id_carried_to_member": True,
            },
        ],
    )

    axis_rows, bucket_rows, _summary = builder.build_parity_rows()
    labels = {row["execution_leakage_label"] for row in axis_rows}
    bucket_labels = {row["execution_leakage_label"] for row in bucket_rows}
    source_axis_indexes = {row["source_axis_row_index"] for row in axis_rows}

    assert "executable_axis_missing_row_bound_selected_package_replay_candidate_or_decision_window" not in labels
    assert "executable_axis_candidate_namespace_materialized_no_lifecycle_label_context" not in labels
    assert source_axis_indexes == {1, 2, 3, 4}
    assert "selected_package_lifecycle_context_without_current_replay_source_materialization" in labels
    assert "selected_package_replay_source_not_materialized_no_hydrated_selector_candidate_rows" in labels
    assert "selected_package_candidate_namespace_materialized_lifecycle_label_context_source_gap" in labels
    assert (
        "source_axis_selected_package_bridge_materialized_window_lifecycle_label_context_denominator_authority_closed"
        in labels
    )
    assert labels == bucket_labels


def test_selected_package_bridge_blocks_unsigned_open_reduced_executable_authority():
    spec = importlib.util.spec_from_file_location(
        "run_selected_package_replay_bridge",
        ROOT
        / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
        / "run_selected_package_replay_bridge.py",
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    row = {
        "candidate_id": "candidate-open-reduced-unsigned",
        "decision_time_utc": "2026-05-05T08:15:00+00:00",
        "selector_action": "open-reduced-risk",
        "selector_reason": (
            "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk"
        ),
        "scheduler_materialization_action_intent": "new_position",
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "package_replay_source_bound_candidate_use_allowed": True,
        "package_replay_executable_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "expected_net_r": 1.11,
        "probability": 0.91,
        "fill_probability": 0.92,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "entry_price": 2400.0,
        "stop_loss": 2390.0,
        "take_profit_1": 2420.0,
        "ultimate_candidate_package_open_reduced_risk_authority": {
            "applies": True,
            "allowed": True,
            "authority_family": "router_refusal_softening",
            "source_boundary": (
                "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
            ),
        },
    }

    assert module.executable_package_use_detail(
        row,
        source_bound_allowed=True,
    ) == (
        False,
        "selector_reduced_package_new_entry_signed_authority_invalid:authority_hash_missing",
    )

    fields = module.package_authority_bridge_fields(row, source_bound_allowed=True)
    assert fields["package_authority_executable_candidate_status"] == (
        "package_authority_candidate_not_executable:"
        "signed_package_new_entry_authority_invalid:authority_hash_missing"
    )
    assert fields["package_new_entry_authority_required"] is True
    assert fields["package_new_entry_authority_valid"] is False
    assert fields[
        "package_new_entry_authority_candidate_decision_quality_bridge_materialized_fields"
    ] == [
        "expected_net_r",
        "probability",
        "fill_probability",
        "source_completeness",
    ]
    assert (
        fields[
            "package_new_entry_authority_candidate_decision_quality_bridge_materialized_boundary"
        ]
        == "predecision_selected_package_bridge_quality_no_outcome_fields"
    )
    assert fields["package_new_entry_authority_failures"] == [
        "authority_hash_missing",
    ]

    stale_order = {
        **row,
        "order_id": "stale-unsigned-order",
        "package_new_entry_authority_failures": [
            "execution_fillability_missing_source_bound_input"
        ],
        "package_new_entry_authority_valid": False,
        "package_new_entry_authority_status": "stale_downstream_failure",
    }
    decorated = module.decorate_rows([stale_order], row_type="order")
    assert decorated[0]["package_new_entry_authority_failures"] == [
        "authority_hash_missing"
    ]
    assert decorated[0]["diagnostic_stale_package_new_entry_authority_failures"] == [
        "execution_fillability_missing_source_bound_input"
    ]

    kept, dropped = module.filter_executable_order_trade_rows([row], row_type="order")
    assert kept == []
    assert dropped[0]["order_filtered_from_executable_ledger"] is True
    assert dropped[0]["order_materialization_authority_blocked"] is True
    assert dropped[0]["order_filtered_from_executable_ledger_reason"] == (
        "selector_reduced_package_new_entry_signed_authority_invalid:authority_hash_missing"
    )


def test_selected_package_bridge_normalizes_cash_symbol_aliases_consistently():
    spec = importlib.util.spec_from_file_location(
        "run_selected_package_replay_bridge",
        ROOT
        / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
        / "run_selected_package_replay_bridge.py",
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    assert {
        module.norm_symbol(value)
        for value in ("US30", "US30.cash", "US30_cash", "US30_CASH", "US30CASH")
    } == {"US30_cash"}
    assert {
        module.norm_symbol(value)
        for value in ("UKOIL_cash", "UKOIL_CASH", "UKOIL.cash", "UKOILCASH")
    } == {"UKOIL_cash"}
    assert {
        module.norm_symbol(value)
        for value in ("USOIL_cash", "USOIL_CASH", "USOIL.cash", "USOILCASH")
    } == {"USOIL_cash"}


def test_broad_live_as_if_replay_requested_symbols_preserve_cash_suffix_case():
    spec = importlib.util.spec_from_file_location(
        "replay_acceleration_attempt5_typed_sparse_runner_symbols_test",
        HARNESS_PATH,
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    assert module.requested_replay_symbols(
        ["xauusd", "UKOIL_cash", "us30_cash", "UKOIL_CASH"]
    ) == ("XAUUSD", "UKOIL_cash", "US30_cash")
    assert module.active_replay_symbol_universe(("USDJPY",)) == ("USDJPY",)
    assert len(module.active_replay_symbol_universe(None)) == len(
        module.GTOS_24_SYMBOL_SURFACE
    )


def test_selected_package_bridge_window_only_label_is_not_exact_denominator():
    spec = importlib.util.spec_from_file_location(
        "run_selected_package_replay_bridge",
        ROOT
        / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
        / "run_selected_package_replay_bridge.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    bridge_rows, label_rows, summary = module.build_denominator_bridge(
        candidates=[
            {
                "candidate_id": "candidate-a",
                "symbol": "AUDJPY",
                "side": "BUY",
                "framework": "origin_liquidity_sweep_reclaim",
                "origin_family": "liquidity_sweep_reclaim",
                "session_bucket": "london",
                "decision_time_utc": "2026-05-05T08:15:00Z",
            }
        ],
        members=[
            {
                "source_axis_row_index": 12,
                "stable_member_axis_id": "member_axis:stable-a",
                "sleeve_id": "sleeve-a",
                "symbol": "AUDJPY",
                "side": "LONG",
                "framework": "broader_origin",
                "origin_family": "current_liquidity_sweep_reclaim",
                "session_bucket": "london_broad",
            }
        ],
        labels=[
            {
                "label_id": "label-window-only",
                "candidate_id": "other-candidate",
                "symbol": "AUDJPY",
                "side": "LONG",
                "decision_time_utc": "2026-05-05T08:15:00+00:00",
                "pending_lifecycle_v4_state_group": "active_pending",
                "fillability_label_family": (
                    "active_pending_no_entry_touch_internal_lifecycle"
                ),
                "fill_no_fill_label": "no_fill_still_pending",
            }
        ],
        decision_time_source="lifecycle-labels",
    )

    assert bridge_rows[0]["stable_decision_window_label_match"] is True
    assert bridge_rows[0]["exact_candidate_id_label_match"] is False
    assert bridge_rows[0]["selected_package_denominator_use_allowed"] is False
    assert bridge_rows[0]["selected_package_denominator_use_reason"] == (
        "stable_window_lifecycle_context_present_denominator_authority_closed"
    )
    assert bridge_rows[0]["lifecycle_label_context_present"] is True
    assert bridge_rows[0]["pending_lifecycle_v4_state_group"] == "active_pending"
    assert bridge_rows[0]["fillability_label_family"] == (
        "active_pending_no_entry_touch_internal_lifecycle"
    )
    assert bridge_rows[0]["fill_no_fill_label"] == "no_fill_still_pending"
    assert label_rows[0]["lifecycle_label_context_present"] is True
    assert label_rows[0]["fillability_label_families"] == [
        "active_pending_no_entry_touch_internal_lifecycle"
    ]
    assert label_rows[0]["selected_package_denominator_use_allowed"] is False
    assert label_rows[0]["selected_package_denominator_use_reason"] == (
        "stable_window_lifecycle_context_present_denominator_authority_closed"
    )
    assert summary["candidate_id_label_hits"] == 0
    assert summary["exact_denominator_join_rows"] == 0
    compact_rows = module.compact_candidate_rows(
        [
            {
                "candidate_id": "candidate-a",
                "symbol": "AUDJPY",
                "side": "BUY",
                "decision_time_utc": "2026-05-05T08:15:00Z",
            }
        ],
        bridge_rows,
    )
    assert compact_rows[0]["lifecycle_label_context_present"] is True
    assert compact_rows[0]["pending_lifecycle_v4_state_group"] == "active_pending"
    assert compact_rows[0]["fillability_label_families"] == [
        "active_pending_no_entry_touch_internal_lifecycle"
    ]


def test_parity_preserves_explicit_standalone_selected_package_bridge_mode(
    tmp_path,
    monkeypatch,
):
    builder = load_parity_builder()
    monkeypatch.setattr(builder, "ROUTE", tmp_path)
    selected_bridge_prefix = "REPLAY_EXTENSION_SELECTED_PACKAGE_REPLAY_BRIDGE"
    monkeypatch.setattr(builder, "BROAD_PREFIX", selected_bridge_prefix)
    broad_paths = (
        "BROAD_CANDIDATE_PATH",
        "BROAD_CANDIDATE_INDEX_PATH",
        "BROAD_SCORECARD_PATH",
        "BROAD_ORDER_PATH",
        "BROAD_ORACLE_PATH",
        "BROAD_TRADE_PATH",
        "BROAD_MISSED_PATH",
        "BROAD_PACKET_SIDECAR_PATH",
    )
    for attr in broad_paths:
        path = tmp_path / f"{attr}.jsonl"
        monkeypatch.setattr(builder, attr, path)
        builder.write_jsonl(path, [])
    compact_path = tmp_path / f"{selected_bridge_prefix}_COMPACT_CANDIDATE_LEDGER.jsonl"
    bridge_summary_path = tmp_path / f"{selected_bridge_prefix}_SUMMARY.json"
    monkeypatch.setattr(builder, "BROAD_SUMMARY_PATH", bridge_summary_path)
    bridge_summary_path.write_text(
        json.dumps(
            {
                "output_prefix": selected_bridge_prefix,
                "profiles": ["bridge_summary_profile"],
                "requested_replay_days": ["2026-05-05"],
                "compact_candidate_rows": 1,
            }
        ),
        encoding="utf-8",
    )
    builder.write_jsonl(
        compact_path,
        [
            {
                "selected_package_replay_row": True,
                "candidate_id": "candidate-bridge",
                "decision_time_utc": "2026-05-05T08:15:00Z",
                "symbol": "AUDJPY",
                "side": "BUY",
                "framework": "origin_liquidity_sweep_reclaim",
                "origin_family": "liquidity_sweep_reclaim",
                "session_bucket": "london",
                "ultimate_package_matched_member_axis_ids": [
                    "member_axis:stable-a"
                ],
                "lifecycle_label_context_present": True,
                "lifecycle_label_context_row_count": 1,
                "pending_lifecycle_v4_state_group": "active_pending",
                "pending_lifecycle_v4_state_groups": ["active_pending"],
                "fillability_label_family": (
                    "active_pending_no_entry_touch_internal_lifecycle"
                ),
                "fillability_label_families": [
                    "active_pending_no_entry_touch_internal_lifecycle"
                ],
                "fill_no_fill_label": "no_fill_still_pending",
                "fill_no_fill_labels": ["no_fill_still_pending"],
                "ultimate_package_matched_member_axis_count": 1,
                "ultimate_package_admission_member_axis_match_count": 1,
                "ultimate_package_member_axis_source_bound_signal_r_sum": 12.5,
                "ultimate_package_member_axis_max_source_bound_signal_r": 12.5,
                "ultimate_package_effective_matched_count": 1,
                "ultimate_package_effective_admission_count": 1,
                "ultimate_package_effective_source_bound_signal_r": 12.5,
                "ultimate_package_effective_source_bound_candidate_use_allowed": True,
                "ultimate_package_effective_evidence_source": (
                    "member_axis_admission_source_bound_use_allowed"
                ),
                "ultimate_package_executable_admission_status": (
                    "executable_source_bound_package_admission"
                ),
                "ultimate_package_scheduler_consumed_status": (
                    "eligible_for_scheduler_consumption"
                ),
            }
        ],
    )
    tagged_compact_path = (
        tmp_path
        / "REPLAY_EXTENSION_SELECTED_PACKAGE_REPLAY_BRIDGE_MARKETABLE_ROUTE_REPAIR_MAY05_SMOKE_COMPACT_CANDIDATE_LEDGER.jsonl"
    )
    builder.write_jsonl(
        tagged_compact_path,
        [
            {
                "broad_replay_profile": "tagged_row_profile",
                "selected_package_replay_row": True,
                "candidate_id": "candidate-bridge-tagged",
                "decision_time_utc": "2026-05-05T08:30:00Z",
                "symbol": "AUDJPY",
                "side": "BUY",
                "framework": "origin_liquidity_sweep_reclaim",
                "origin_family": "liquidity_sweep_reclaim",
                "session_bucket": "london",
                "ultimate_package_matched_member_axis_ids": [
                    "member_axis:stable-a"
                ],
                "ultimate_package_matched_member_axis_count": 1,
                "ultimate_package_admission_member_axis_match_count": 1,
                "ultimate_package_member_axis_source_bound_signal_r_sum": 7.0,
                "ultimate_package_member_axis_max_source_bound_signal_r": 7.0,
                "ultimate_package_effective_matched_count": 1,
                "ultimate_package_effective_admission_count": 1,
                "ultimate_package_effective_source_bound_signal_r": 7.0,
                "ultimate_package_effective_source_bound_candidate_use_allowed": True,
            }
        ],
    )

    _candidates, by_axis, _enrichment, source_scope = (
        builder._load_broad_indexes_with_scope()
    )
    member = {
        "stable_member_axis_id": "member_axis:stable-a",
        "symbol": "AUDJPY",
        "side": "LONG",
        "framework": "broader_origin",
        "origin_family": "current_liquidity_sweep_reclaim",
        "session_bucket": "london_broad",
    }
    rows = by_axis[("AUDJPY", "LONG")]

    assert len(rows) == 1
    assert rows[0]["broad_replay_profile"] == "bridge_summary_profile"
    assert rows[0]["lifecycle_label_context_present"] is True
    assert rows[0]["pending_lifecycle_v4_state_group"] == "active_pending"
    assert rows[0]["fillability_label_families"] == [
        "active_pending_no_entry_touch_internal_lifecycle"
    ]
    assert rows[0]["selected_package_replay_bridge_artifact_tag"] == (
        selected_bridge_prefix
    )
    assert rows[0]["ultimate_package_effective_admission_count"] == 1.0
    assert rows[0]["ultimate_package_effective_source_bound_signal_r"] == 12.5
    assert rows[0]["ultimate_package_scheduler_consumed_status"] == (
        "eligible_for_scheduler_consumption"
    )
    assert builder.candidate_matches_stable_member_axis_id(member, rows[0])
    assert source_scope["mode"] == "standalone_selected_package_bridge"
    assert source_scope["bridge_artifacts_considered"] == 2
    assert source_scope["bridge_artifacts_included"] == 1
    assert source_scope["bridge_artifacts_excluded"] == 1
    assert source_scope["candidate_instances_materialized"] == 1
    assert source_scope["order_trade_missed_candidate_producer_rows"] == 0
    assert source_scope["excluded_bridge_artifacts"][0]["binding_status"] == (
        "bridge_exact_broad_prefix_binding_missing"
    )


def test_parity_excludes_bridge_candidate_producers_when_broad_candidate_is_authoritative(
    tmp_path,
    monkeypatch,
):
    builder = load_parity_builder()
    prefix = "BROAD_LIVE_AS_IF_REPLAY_V219_SCOPE_UNIT"
    profile = "repaired_package_conversion_v3"
    summary_path = configure_broad_loader_fixture(
        builder,
        tmp_path,
        monkeypatch,
        prefix=prefix,
    )
    summary_path.write_text(
        json.dumps(
            {
                "output_prefix": prefix,
                "date_start": "2026-05-13",
                "date_end": "2026-05-13",
                "profiles": [profile],
                "candidate_rows_written": 1,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    authoritative_candidate = {
        "broad_replay_profile": profile,
        "candidate_id": "candidate-authoritative",
        "decision_time_utc": "2026-05-13T08:15:00Z",
        "symbol": "XAUUSD",
        "side": "LONG",
        "split": "holdout",
        "chunk_id": "chunk-authoritative",
    }
    write_jsonl(builder.BROAD_CANDIDATE_PATH, [authoritative_candidate])

    unrelated_tag = "OLD_SELECTED_PACKAGE_REPLAY_BRIDGE_MAY05"
    write_jsonl(
        tmp_path / f"{unrelated_tag}_COMPACT_CANDIDATE_LEDGER.jsonl",
        [
            {
                **authoritative_candidate,
                "candidate_id": "candidate-unrelated-may05",
                "decision_time_utc": "2026-05-05T08:15:00Z",
                "chunk_id": "chunk-unrelated",
            }
        ],
    )
    (tmp_path / f"{unrelated_tag}_SUMMARY.json").write_text(
        json.dumps(
            {
                "output_prefix": unrelated_tag,
                "requested_replay_days": ["2026-05-05"],
                "profiles": [profile],
                "compact_candidate_rows": 1,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    exact_tag = "CURRENT_SELECTED_PACKAGE_REPLAY_BRIDGE_EXACT_BOUND"
    write_jsonl(
        tmp_path / f"{exact_tag}_COMPACT_CANDIDATE_LEDGER.jsonl",
        [
            {
                **authoritative_candidate,
                "candidate_id": "candidate-exact-bound",
                "decision_time_utc": "2026-05-13T08:30:00Z",
                "chunk_id": "chunk-exact-bound",
            }
        ],
    )
    (tmp_path / f"{exact_tag}_SUMMARY.json").write_text(
        json.dumps(
            {
                "output_prefix": exact_tag,
                "source_broad_prefix": prefix,
                "requested_replay_days": ["2026-05-13"],
                "profiles": [profile],
                "compact_candidate_rows": 1,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    candidates, _by_axis, enrichment, source_scope = (
        builder._load_broad_indexes_with_scope()
    )
    candidate_ids = {row["candidate_id"] for row in candidates.values()}
    projection_rows = builder.build_candidate_instance_projection_rows(
        candidates=candidates,
        enrichment=enrichment,
        package_candidate_index={},
        generated="2026-07-10T00:00:00Z",
    )
    projection_summary = builder.summarize_candidate_instance_projection_rows(
        projection_rows,
        source_scope=source_scope,
    )

    assert candidate_ids == {"candidate-authoritative"}
    assert source_scope["bridge_artifacts_considered"] == 2
    assert source_scope["bridge_artifacts_included"] == 1
    assert source_scope["bridge_artifacts_excluded"] == 1
    assert source_scope["excluded_bridge_declared_candidate_rows"] == 1
    assert source_scope["excluded_bridge_artifacts"][0]["artifact_tag"] == (
        unrelated_tag
    )
    assert source_scope["excluded_bridge_artifacts"][0]["binding_status"] == (
        "bridge_exact_broad_prefix_binding_missing"
    )
    assert source_scope["included_bridge_artifacts"][0]["binding_status"] == (
        "bridge_summary_exact_prefix_window_profile_bound"
    )
    assert source_scope[
        "bridge_candidate_producer_artifacts_suppressed_by_authoritative_source"
    ] == [exact_tag]
    assert source_scope[
        "bridge_candidate_producer_rows_suppressed_by_authoritative_source"
    ] == 1
    assert projection_summary["projection_source_scope"]["assertion_status"] == (
        "pass"
    )
    assert projection_summary["projection_source_scope"][
        "out_of_window_candidate_instance_count"
    ] == 0
    assert projection_summary["projection_source_scope"][
        "min_decision_time_utc"
    ] == "2026-05-13T08:15:00Z"


def test_authoritative_compact_candidate_index_materializes_exact_projection(
    tmp_path,
    monkeypatch,
):
    builder = load_parity_builder()
    prefix = "BROAD_LIVE_AS_IF_REPLAY_V249_COMPACT_INDEX_UNIT"
    profile = "repaired_package_conversion_v3"
    summary_path = configure_broad_loader_fixture(
        builder,
        tmp_path,
        monkeypatch,
        prefix=prefix,
    )
    summary_path.write_text(
        json.dumps(
            {
                "output_prefix": prefix,
                "date_start": "2026-05-13",
                "date_end": "2026-05-13",
                "profiles": [profile],
                "candidate_ledger_omitted": True,
                "candidate_index_rows_written": 1,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    candidate = {
        "row_type": "candidate_index",
        "candidate_index_schema": "compact_broad_replay_candidate_index_v1",
        "candidate_index_lossless_candidate_payload": False,
        "broad_replay_profile": profile,
        "candidate_id": "candidate-index-authority",
        "decision_time_utc": "2026-05-13T08:15:00Z",
        "canonical_replay_candidate_instance_key": (
            "candidate-index-authority@@2026-05-13T08:15:00Z"
        ),
        "symbol": "XAUUSD",
        "side": "LONG",
        "split": "holdout",
        "chunk_id": "chunk-index-authority",
        "selector_action": "reject",
        "effective_selector_action": "reject",
    }
    write_jsonl(builder.BROAD_CANDIDATE_INDEX_PATH, [candidate])

    candidates, _by_axis, enrichment, source_scope = (
        builder._load_broad_indexes_with_scope()
    )
    projection_rows = builder.build_candidate_instance_projection_rows(
        candidates=candidates,
        enrichment=enrichment,
        package_candidate_index={},
        generated="2026-07-13T00:00:00Z",
    )
    projection_summary = builder.summarize_candidate_instance_projection_rows(
        projection_rows,
        source_scope=source_scope,
    )

    assert len(candidates) == 1
    assert len(projection_rows) == 1
    assert projection_rows[0]["candidate_instance_parity_key"] == (
        "candidate-index-authority@@2026-05-13T08:15:00Z"
    )
    assert source_scope["authoritative_candidate_source_class"] == (
        "authoritative_broad_candidate_index"
    )
    assert source_scope["candidate_source_row_counts"] == {
        "authoritative_broad_candidate_index": 1
    }
    assert source_scope["fallback_candidate_materialization_enabled"] is False
    assert source_scope["order_trade_missed_candidate_producer_rows"] == 0
    assert projection_summary["row_count"] == 1
    assert projection_summary["projection_source_scope"]["assertion_status"] == (
        "pass"
    )
    assert projection_summary["projection_source_scope"]["assertions"][
        "authoritative_candidate_count"
    ]["status"] == "pass"


def test_authoritative_candidate_ledger_keeps_order_trade_as_enrichment_only(
    tmp_path,
    monkeypatch,
):
    builder = load_parity_builder()
    prefix = "BROAD_LIVE_AS_IF_REPLAY_V219_PRODUCER_UNIT"
    profile = "repaired_package_conversion_v3"
    summary_path = configure_broad_loader_fixture(
        builder,
        tmp_path,
        monkeypatch,
        prefix=prefix,
    )
    summary_path.write_text(
        json.dumps(
            {
                "output_prefix": prefix,
                "date_start": "2026-05-13",
                "date_end": "2026-05-13",
                "profiles": [profile],
                "candidate_rows_written": 1,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    candidate = {
        "broad_replay_profile": profile,
        "candidate_id": "candidate-ledger-authority",
        "decision_time_utc": "2026-05-13T09:00:00Z",
        "symbol": "XAUUSD",
        "side": "LONG",
        "split": "holdout",
        "chunk_id": "chunk-authority",
    }
    write_jsonl(builder.BROAD_CANDIDATE_PATH, [candidate])
    exact_binding = {
        **candidate,
        "simulated_order_id": "order-authority",
        "order_status": "filled",
    }
    write_jsonl(
        builder.BROAD_ORDER_PATH,
        [
            exact_binding,
            {
                **exact_binding,
                "candidate_id": "candidate-order-only",
                "decision_time_utc": "2026-05-13T09:05:00Z",
                "chunk_id": "chunk-order-only",
                "simulated_order_id": "order-only",
            },
        ],
    )
    write_jsonl(
        builder.BROAD_TRADE_PATH,
        [
            {
                **exact_binding,
                "trade_id": "trade-authority",
                "net_r": 1.25,
            },
            {
                **exact_binding,
                "candidate_id": "candidate-trade-only",
                "decision_time_utc": "2026-05-13T09:10:00Z",
                "chunk_id": "chunk-trade-only",
                "simulated_order_id": "order-trade-only",
                "trade_id": "trade-only",
                "net_r": -1.0,
            },
        ],
    )

    candidates, _by_axis, enrichment, source_scope = (
        builder._load_broad_indexes_with_scope()
    )
    instance_key = builder.candidate_instance_key(candidate)
    projection_rows = builder.build_candidate_instance_projection_rows(
        candidates=candidates,
        enrichment=enrichment,
        package_candidate_index={},
        generated="2026-07-10T00:00:00Z",
    )
    projection_summary = builder.summarize_candidate_instance_projection_rows(
        projection_rows,
        source_scope=source_scope,
    )

    assert len(candidates) == 1
    assert {row["candidate_id"] for row in candidates.values()} == {
        "candidate-ledger-authority"
    }
    assert enrichment[instance_key]["order_present"] is True
    assert enrichment[instance_key]["trade_present"] is True
    assert source_scope["candidate_source_row_counts"] == {
        "authoritative_broad_candidate_ledger": 1
    }
    assert source_scope["fallback_candidate_materialization_enabled"] is False
    assert source_scope["order_trade_missed_candidate_producer_rows"] == 0
    assert len(projection_rows) == 1
    assert projection_summary["projection_source_scope"]["assertions"][
        "authoritative_candidate_count"
    ]["status"] == "pass"
    assert projection_summary["projection_source_scope"]["assertions"][
        "order_trade_missed_candidate_producer_policy"
    ]["status"] == "pass"


def test_candidate_axis_matching_accepts_selected_package_axis_alias_only():
    builder = load_parity_builder()

    row = builder.reduced_candidate(
        {
            "candidate_id": "candidate-selected-axis-alias",
            "decision_time_utc": "2026-05-05T08:15:00Z",
            "symbol": "AUDJPY",
            "side": "LONG",
            "selected_package_matched_member_axis_ids": [
                "member_axis:selected-only"
            ],
        }
    )
    member = {
        "stable_member_axis_id": "member_axis:selected-only",
        "symbol": "AUDJPY",
        "side": "LONG",
    }

    assert row["matched_stable_member_axis_ids"] == ["member_axis:selected-only"]
    assert row["ultimate_package_matched_member_axis_ids"] == [
        "member_axis:selected-only"
    ]
    assert row["selected_package_matched_member_axis_ids"] == [
        "member_axis:selected-only"
    ]
    assert builder.candidate_matches_stable_member_axis_id(member, row)


def test_reduced_candidate_preserves_top_level_quality_fields():
    builder = load_parity_builder()

    reduced = builder.reduced_candidate(
        {
            "broad_replay_profile": "repaired_package_conversion_v3",
            "candidate_id": "candidate-1",
            "decision_time_utc": "2026-05-13T10:15:00Z",
            "symbol": "XAUUSD",
            "side": "LONG",
            "source_completeness": 0.91,
            "confidence": 0.66,
            "fill_probability": 0.73,
            "source_fields": {"source_completeness": 0.12},
            "pretrade_cost_packet_status": "PASSED",
            "cost_authority": "broker_calibrated_replay_cost",
            "cost_source_gap_status": "source_bound_cost_authority_present",
            "scheduler_materialization_action_intent": "new_position",
            "selector_action": "trade",
        }
    )

    assert reduced["source_completeness"] == 0.91
    assert reduced["confidence"] == 0.66
    assert reduced["fill_probability"] == 0.73
    assert reduced["candidate_fill_probability"] == 0.73
    assert reduced["pretrade_cost_packet_status"] == "PASSED"
    assert reduced["cost_authority"] == "broker_calibrated_replay_cost"
    assert reduced["pretrade_cost_packet_authority"] == "broker_calibrated_replay_cost"
    assert reduced["cost_source_gap_status"] == "source_bound_cost_authority_present"
    assert reduced["scheduler_materialization_action_intent"] == "new_position"
    assert reduced["action_intent"] == "new_position"


def test_reduced_package_candidate_marks_missing_order_geometry_not_executable():
    builder = load_parity_builder()

    reduced = builder.reduced_package_candidate(
        {
            "candidate_id": "package-authority-only",
            "decision_time_utc": "2026-05-05T08:15:00Z",
            "symbol": "XAUUSD",
            "side": "LONG",
            "framework": "origin_liquidity_sweep_reclaim",
            "origin_family": "liquidity_sweep_reclaim",
            "session_bucket": "london",
            "source_bound_package_candidate_use_allowed": True,
            "package_replay_source_bound_candidate_use_allowed": True,
            "package_replay_candidate_use_allowed": True,
            "candidate_expected_net_r": 0.75,
            "probability": 0.72,
            "fill_probability": 0.63,
            "source_completeness": 1.0,
        }
    )

    assert reduced["package_replay_source_bound_candidate_use_allowed"] is True
    assert reduced["package_replay_candidate_use_allowed"] is False
    assert reduced["package_replay_executable_candidate_use_allowed"] is False
    assert reduced["package_replay_executable_candidate_use_allowed_reason"] == (
        "package_authority_candidate_missing_entry_stop_target_geometry"
    )
    assert reduced["package_authority_has_order_geometry"] is False
    assert reduced["package_authority_order_geometry_status"] == (
        "package_authority_candidate_missing_entry_stop_target_geometry"
    )
    assert reduced["package_authority_executable_candidate_status"] == (
        "package_authority_candidate_missing_entry_stop_target_geometry"
    )
    assert reduced["replay_candidate_use_allowed_now"] is False
    assert reduced["replay_candidate_use_allowed_now_reason"] == (
        "package_authority_candidate_missing_entry_stop_target_geometry"
    )
    assert reduced["ultimate_package_effective_executable_authority_allowed"] is False
    assert reduced["ultimate_package_effective_source_bound_non_executable"] is True
    assert reduced["candidate_expected_net_r"] == 0.75


def test_replay_executable_package_use_detail_requires_cost_action_and_geometry():
    builder = load_parity_builder()
    decision_time = "2026-05-13T10:15:00+00:00"

    def signed_authority_fields(selector_action: str) -> dict:
        return _current_authority_fields(
            candidate_id="candidate-executable",
            decision_time_utc=decision_time,
            order_allowed=True,
            selector_action=selector_action,
            selector_reason="unit_test_signed_selector_action",
        )

    base = {
        "candidate_id": "candidate-executable",
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": (
            f"candidate-executable@@{decision_time}"
        ),
        "source_bound_replay_candidate_instance_key": (
            f"candidate-executable@@{decision_time}"
        ),
        "candidate_instance_identity_status": "materialized",
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_source_bound_candidate_use_allowed": True,
        "ultimate_package_effective_admission_count": 1,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "predecision_limit_fillability_probability": 0.73,
        "limit_fillability_probability": 0.73,
        "execution_fill_probability": 0.73,
        "execution_fill_probability_source": "predecision_limit_fillability",
        "execution_fill_probability_source_time_utc": (
            "2026-05-13T10:00:00+00:00"
        ),
        "execution_fill_probability_source_boundary": (
            "asof_candidate_fields_only_no_postdecision_path"
        ),
        "scheduler_materialization_action_intent": "new_position",
        "selector_action": "open-reduced-risk",
        "entry_price": 2400.0,
        "stop_loss": 2390.0,
        "take_profit_1": 2420.0,
    }

    assert builder.replay_executable_package_use_detail(
        base,
        source_bound_allowed=True,
        package_replay_allowed=True,
    ) == (
        False,
        "selector_open_reduced_risk_new_entry_authority:"
        "immutable_authority_envelope_invalid:"
        "package_new_entry_authority_envelope_missing",
    )

    signed_open_reduced_new_entry = {
        **base,
        **signed_authority_fields("open-reduced-risk"),
    }
    assert builder.replay_executable_package_use_detail(
        signed_open_reduced_new_entry,
        source_bound_allowed=True,
        package_replay_allowed=True,
    ) == (True, "broker_cost_selector_and_scheduler_action_executable")

    unsigned_reduce_risk_new_entry = {
        **base,
        "selector_action": "reduce-risk",
    }
    assert builder.replay_executable_package_use_detail(
        unsigned_reduce_risk_new_entry,
        source_bound_allowed=True,
        package_replay_allowed=True,
    ) == (
        False,
        "selector_reduce_risk_new_entry_authority:"
        "immutable_authority_envelope_invalid:"
        "package_new_entry_authority_envelope_missing",
    )

    signed_reduce_risk_new_entry = {
        **unsigned_reduce_risk_new_entry,
        **signed_authority_fields("reduce-risk"),
    }
    assert builder.replay_executable_package_use_detail(
        signed_reduce_risk_new_entry,
        source_bound_allowed=True,
        package_replay_allowed=True,
    ) == (True, "broker_cost_selector_and_scheduler_action_executable")

    missing_cost = dict(base)
    missing_cost.pop("pretrade_cost_packet_status")
    assert builder.replay_executable_package_use_detail(
        missing_cost,
        source_bound_allowed=True,
        package_replay_allowed=True,
    ) == (False, "broker_cost_packet_status_missing")

    missing_authority = dict(base)
    missing_authority.pop("cost_authority")
    assert builder.replay_executable_package_use_detail(
        missing_authority,
        source_bound_allowed=True,
        package_replay_allowed=True,
    ) == (False, "broker_cost_authority_missing")

    proxy_authority = {**base, "cost_authority": "timewarp_candidate_cost_proxy"}
    assert builder.replay_executable_package_use_detail(
        proxy_authority,
        source_bound_allowed=True,
        package_replay_allowed=True,
    ) == (False, "broker_cost_authority_unexpected:timewarp_candidate_cost_proxy")

    missing_action = dict(base)
    missing_action.pop("scheduler_materialization_action_intent")
    assert builder.replay_executable_package_use_detail(
        missing_action,
        source_bound_allowed=True,
        package_replay_allowed=True,
    ) == (False, "scheduler_materialization_action_intent_missing")

    missing_geometry = {
        **base,
        "package_authority_has_order_geometry": False,
        "package_authority_order_geometry_status": (
            "package_authority_candidate_missing_entry_stop_target_geometry"
        ),
    }
    assert builder.replay_executable_package_use_detail(
        missing_geometry,
        source_bound_allowed=True,
        package_replay_allowed=True,
    ) == (
        False,
        "package_authority_candidate_missing_entry_stop_target_geometry",
    )


def test_candidate_trace_emits_merged_executable_proof_fields():
    builder = load_parity_builder()
    decision_time = "2026-05-13T10:15:00Z"
    instance_key = f"candidate-exec-proof@@{decision_time}"
    authority_fields = _current_authority_fields(
        candidate_id="candidate-exec-proof",
        decision_time_utc=decision_time,
        order_allowed=True,
        selector_reason="risk_scaled_package_candidate",
    )
    candidate = {
        "candidate_id": "candidate-exec-proof",
        "candidate_instance_key": "profile|candidate-exec-proof|window",
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "stable_decision_window_id": "decision_window:XAUUSD:LONG:2026-05-13T10:15:00Z",
        "symbol": "XAUUSD",
        "side": "LONG",
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "selector_action": "reject",
        "selector_reason": "raw_candidate_reject",
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "entry_price": 2400.0,
        "stop_loss": 2390.0,
        "take_profit_1": 2420.0,
    }
    enrich = {
        "executable_proof_row": {
            "pretrade_cost_packet_status": "PASSED",
            "cost_authority": "broker_calibrated_replay_cost",
            "cost_source_gap_status": "source_bound_cost_authority_present",
            "source_completeness": 1.0,
            "source_completeness_status": "source_completeness_present",
            "predecision_limit_fillability_probability": 0.73,
            "limit_fillability_probability": 0.73,
            "execution_fill_probability": 0.73,
            "execution_fill_probability_source": "predecision_limit_fillability",
            "scheduler_materialization_action_intent": "new_position",
            "scheduler_materialization_selector_action": "reject",
            "scheduler_materialization_selector_reason": "raw_scheduler_reject",
            "selector_action": "reject",
            "selector_reason": "raw_proof_reject",
            "entry_price": 2400.0,
            "stop_loss": 2390.0,
            "take_profit_1": 2420.0,
            **authority_fields,
        }
    }
    package_candidate = {
        "source_bound_package_candidate_use_allowed": True,
        "package_replay_source_bound_candidate_use_allowed": True,
    }

    trace = builder.candidate_trace(
        candidate=candidate,
        enrich=enrich,
        package_candidate=package_candidate,
        exact_package_candidate_ids=set(),
        source_bound_r=12.5,
    )

    assert trace["package_replay_executable_candidate_use_allowed"] is True
    assert trace["package_replay_executable_candidate_use_allowed_reason"] == (
        "broker_cost_selector_and_scheduler_action_executable"
    )
    assert trace["pretrade_cost_packet_status"] == "PASSED"
    assert trace["cost_authority"] == "broker_calibrated_replay_cost"
    assert trace["cost_source_gap_status"] == "source_bound_cost_authority_present"
    assert trace["scheduler_materialization_action_intent"] == "new_position"
    assert trace["action_intent"] == "new_position"
    assert trace["lifecycle_action"] == "new_position"
    assert trace["selector_action"] == "open-reduced-risk"
    assert trace["selector_reason"] == "risk_scaled_package_candidate"
    assert trace["raw_selector_action"] == "reject"


def test_candidate_trace_prefers_current_order_authority_over_stale_first_proof():
    builder = load_parity_builder()
    decision_time = "2026-06-02T09:15:00Z"
    candidate_id = "candidate-current-order-authority"
    instance_key = f"{candidate_id}@@{decision_time}"
    authority_fields = _current_authority_fields(
        candidate_id=candidate_id,
        decision_time_utc=decision_time,
        order_allowed=True,
        selector_reason="signed_current_order_authority",
    )
    candidate = {
        "candidate_id": candidate_id,
        "candidate_instance_key": "profile|current-order-authority|window",
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "symbol": "EURUSD",
        "side": "LONG",
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "selector_action": "reject",
        "selector_reason": "stale_candidate_reject",
        "entry_price": 1.081,
        "stop_loss": 1.079,
        "take_profit_1": 1.085,
    }
    stale_first_proof = {
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "scheduler_materialization_action_intent": "new_position",
        "selector_action": "reject",
        "selector_reason": "legacy_first_proof_reject",
    }
    current_order_binding = {
        **candidate,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "pretrade_cost_packet_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "source_gap_cost_fallback_blocked": False,
        "candidate_cost_r_fallback_is_authority": False,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "execution_fill_probability": 0.74,
        "execution_fill_probability_source": "predecision_limit_fillability",
        "predecision_limit_fillability_probability": 0.74,
        "scheduler_materialization_action_intent": "new_position",
        "selector_action": "open-reduced-risk",
        "selector_reason": "signed_current_order_authority",
        **authority_fields,
    }
    trace = builder.candidate_trace(
        candidate=candidate,
        enrich={
            "executable_proof_row": stale_first_proof,
            "order_binding": current_order_binding,
            "order_present": True,
        },
        package_candidate={
            "source_bound_package_candidate_use_allowed": True,
            "package_replay_source_bound_candidate_use_allowed": True,
        },
        exact_package_candidate_ids=set(),
        source_bound_r=18.75,
    )

    assert trace["package_replay_executable_candidate_use_allowed"] is True
    assert trace["effective_source_bound_r"] == 18.75
    assert trace["selector_action"] == "open-reduced-risk"
    assert trace["selector_reason"] == "signed_current_order_authority"
    assert trace["pretrade_cost_packet_status"] == "PASSED"


def test_candidate_trace_uses_terminal_pre_risk_execution_contract_for_full_risk_trade():
    builder = load_parity_builder()
    decision_time = "2026-06-04T07:45:00+00:00"
    candidate_id = "candidate-terminal-full-risk-contract"
    candidate = {
        "candidate_id": candidate_id,
        "candidate_instance_key": f"profile|{candidate_id}|window",
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "candidate_instance_identity_status": "materialized",
        "symbol": "XAUUSD",
        "side": "SHORT",
        "source_bound_package_candidate_use_allowed": True,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "selector_action": "trade",
        "raw_selector_action": "trade",
    }
    stale_first_proof = {
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "scheduler_materialization_action_intent": "new_position",
        "selector_action": "trade",
    }
    trade = {
        **candidate,
        "pretrade_cost_packet_status": "PASSED",
        "cost_authority": "broker_calibrated_replay_cost",
        "pretrade_cost_packet_authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "source_gap_cost_fallback_blocked": False,
        "candidate_cost_r_fallback_is_authority": False,
        "source_completeness": 1.0,
        "source_completeness_status": "source_completeness_present",
        "execution_fill_probability": 0.92,
        "execution_fill_probability_source": (
            "predecision_limit_fillability.fill_probability"
        ),
        "execution_fill_probability_source_time_utc": (
            "2026-06-04T07:30:00+00:00"
        ),
        "execution_fill_probability_source_boundary": (
            "closed_m15_predecision_asof_no_postdecision_path"
        ),
        "execution_fill_probability_authority_class": (
            "predecision_passive_limit_fillability_authority"
        ),
        "predecision_limit_fillability_probability": 0.92,
        "predecision_limit_fillability": {
            "fill_probability": 0.92,
            "source": "predecision_limit_fillability.fill_probability",
            "current_price_source_time_utc": "2026-06-04T07:30:00+00:00",
            "current_price_source_boundary": (
                "closed_m15_predecision_asof_no_postdecision_path"
            ),
            "decision_time_utc": decision_time,
        },
        "entry_price": 4482.66,
        "stop_loss": 4486.135,
        "take_profit_1": 4475.71,
        "scheduler_materialization_action_intent": "new_position",
        "materialized_selector_action": "trade",
        "materialized_selector_reason": (
            "broker_net_probability_confluence_lifecycle_admission_passed"
        ),
        "effective_selector_action_before_risk_expression": "trade",
        "effective_selector_action": "reduce-risk",
        "risk_decision": "open-reduced-risk",
        "package_new_entry_authority_required": False,
        "package_new_entry_authority_valid": False,
        "package_new_entry_authority_status": (
            "not_required_for_selector_action_or_action_intent"
        ),
    }
    trace = builder.candidate_trace(
        candidate=candidate,
        enrich={
            "executable_proof_row": stale_first_proof,
            "trade_binding": builder.projection_stage_binding(
                trade,
                stage="trade",
            ),
            "trade_present": True,
            "order_present": True,
        },
        package_candidate={
            "source_bound_package_candidate_use_allowed": True,
            "package_replay_source_bound_candidate_use_allowed": True,
        },
        exact_package_candidate_ids=set(),
        source_bound_r=1238.664,
    )

    assert trace["package_replay_executable_candidate_use_allowed"] is True
    assert trace["effective_source_bound_r"] == 1238.664
    assert trace["projection_execution_contract_stage"] == "trade"
    assert trace["selector_action"] == "trade"
    assert trace["execution_fill_probability"] == 0.92
    assert trace["execution_fill_probability_source"] == (
        "predecision_limit_fillability.fill_probability"
    )
    assert trace["source_completeness"] == 1.0


def test_candidate_instance_projection_emits_exact_cross_ledger_contract():
    builder = load_parity_builder()
    candidate = {
        "candidate_id": "candidate-projection",
        "candidate_instance_key": "profile|candidate-projection|window",
        "decision_time_utc": "2026-05-13T10:15:00+00:00",
        "canonical_replay_candidate_instance_key": (
            "candidate-projection@@2026-05-13T10:15:00+00:00"
        ),
        "source_bound_replay_candidate_instance_key": (
            "candidate-projection@@2026-05-13T10:15:00+00:00"
        ),
        "candidate_instance_identity_status": "materialized",
        "broad_replay_profile": "repaired_package_conversion_v3",
        "symbol": "XAUUSD",
        "side": "LONG",
        "origin_family": "current_fvg_fill",
        "raw_selector_action": "reject",
        "selector_action": "open-reduced-risk",
        "selector_reason": "signed_soft_transfer",
        "scheduler_materialization_action_intent": "new_position",
        "candidate_decision_quality": {
            "expected_net_r": 0.82,
            "probability": 0.76,
            "source_completeness": 1.0,
            "source_boundary": "predecision_fixture_no_outcome_fields",
            "field_sources": {
                "expected_net_r": "fixture.expected_net_r",
                "probability": "fixture.probability",
                "source_completeness": "fixture.source_completeness",
            },
        },
        **_current_authority_fields(
            candidate_id="candidate-projection",
            decision_time_utc="2026-05-13T10:15:00+00:00",
            order_allowed=True,
        ),
    }
    enrich = {
        "scorecard_present": True,
        "scheduler_selected": True,
        "scheduler_rank_min": 2,
        "order_present": True,
        "trade_present": False,
        "missed_present": True,
        "net_r": 0.0,
        "scorecard_binding": {
            "scheduler_rank": 2,
            "scheduler_selected": True,
            "effective_selector_action": "open-reduced-risk",
            "effective_selector_reason": "signed_soft_transfer",
            "risk_finalizer_action": "open-reduced-risk",
            "risk_finalizer_reason": "signed_reduced_risk_authority",
        },
        "order_binding": {
            "simulated_order_id": "order-1",
            "order_status": "expired_unfilled",
            "package_replay_order_executable_candidate_use_allowed": True,
            "package_replay_order_executable_candidate_use_allowed_reason": (
                "package_candidate_and_signed_new_entry_authority_executable"
            ),
            "package_replay_order_executable_transfer_status": "order_bound",
            "risk_decision": "open-reduced-risk",
            "risk_decision_reason": "signed_reduced_risk_authority",
            "risk_expression_ladder_tier": "reduced",
        },
        "oracle_binding": {
            "fill_status": "not_filled_entry_not_touched_before_expiry",
            "terminal_outcome": "not_filled_entry_not_touched_before_expiry",
            "guarded_market_fallback_configured": True,
            "guarded_market_fallback_status": "not_eligible",
            "guarded_market_fallback_reason": (
                "fallback_entry_adverse_drift_above_thesis_geometry_ceiling"
            ),
            "guarded_market_fallback_attempted": False,
            "guarded_market_fallback_applied": False,
        },
        "missed_binding": {
            "miss_reason": "order_expired_unfilled",
            "counterfactual_order_fill_status": (
                "not_filled_entry_not_touched_before_expiry"
            ),
            "missed_opportunity_counterfactual_scoreable": True,
        },
    }

    projection = builder.candidate_instance_projection(
        candidate=candidate,
        enrich=enrich,
        package_candidate=None,
        generated="2026-07-10T00:00:00Z",
    )

    assert projection["candidate_instance_parity_key"] == (
        "candidate-projection@@2026-05-13T10:15:00+00:00"
    )
    assert projection["raw_selector_action"] == "reject"
    assert projection["effective_selector_action"] == "open-reduced-risk"
    assert projection["canonical_quality_source"] == (
        "predecision_fixture_no_outcome_fields"
    )
    assert projection["canonical_expected_net_r"] == 0.82
    assert projection["canonical_probability"] == 0.76
    assert projection["canonical_source_completeness"] == 1.0
    assert projection["canonical_quality_contract_status"] == "pass"
    assert projection["package_authority_valid"] is True
    assert projection["package_order_executable_allowed"] is True
    assert projection["risk_finalizer_action"] == "open-reduced-risk"
    assert projection["scheduler_rank"] == 2
    assert projection["scheduler_selected"] is True
    assert projection["order_binding_status"] == "order_bound"
    assert projection["trade_binding_status"] == "trade_absent"
    assert projection["terminal_fallback_eligible"] is False
    assert projection["terminal_counterfactual_present"] is True
    assert projection["selected_expiry_fallback"] is True
    assert projection["risk_behavior"] == "reduced-risk"
    assert projection["exact_deviation_reason"] == (
        "selected_expiry_fallback_blocked:"
        "fallback_entry_adverse_drift_above_thesis_geometry_ceiling"
    )


def test_source_complete_source_required_deviation_uses_exact_non_source_blocker():
    builder = load_parity_builder()
    base = {
        "canonical_source_completeness": 1.0,
        "raw_selector_action": "source-required",
        "effective_selector_action": "source-required",
        "effective_selector_reason": "ultimate_candidate_package_source_required_hold",
        "package_order_executable_allowed": False,
        "scorecard_present": False,
        "scheduler_selected": False,
        "order_present": False,
        "trade_present": False,
    }
    cases = [
        (
            {
                **base,
                "pretrade_cost_packet_status": "REFUSED",
                "package_order_executable_blocker_class": "cost_authority",
                "package_order_executable_blocker_reason": (
                    "scheduler_materialization_skipped_selector_not_risk_bearing_cost_failed"
                ),
                "package_authority_valid": False,
            },
            "cost_authority",
            "source_required_cost_authority_blocked:",
        ),
        (
            {
                **base,
                "pretrade_cost_packet_status": "PASSED",
                "package_order_executable_blocker_class": "scheduler_selection",
                "package_order_executable_blocker_reason": (
                    "signed_package_new_entry_authority_surface_missing"
                ),
                "package_authority_valid": False,
                "package_authority_status": "invalid_or_missing_signed_new_entry_authority",
            },
            "signed_authority",
            "source_required_signed_authority_blocked:",
        ),
        (
            {
                **base,
                "pretrade_cost_packet_status": "PASSED",
                "package_order_executable_blocker_class": "lifecycle",
                "package_order_executable_blocker_reason": (
                    "source_required_fail_closed_pending_lifecycle_conflict"
                ),
                "package_authority_valid": True,
                "lifecycle_action": "source_required_fail_closed",
                "lifecycle_reason": "pending_lifecycle_conflict",
            },
            "lifecycle",
            "source_required_lifecycle_blocked:",
        ),
    ]

    for row, expected_stage, expected_prefix in cases:
        stage, reason = builder.exact_projection_deviation(row)
        assert stage == expected_stage
        assert reason.startswith(expected_prefix)
        assert "source_gap" not in reason


def test_projection_summary_and_flow_analyzer_consume_v220_counts(tmp_path):
    builder = load_parity_builder()
    analyzer = load_flow_analyzer()
    base = {
        "broad_replay_profile": "repaired_package_conversion_v3",
        "projection_source_scope_mode": "exact_broad_prefix",
        "projection_source_prefix": "BROAD_LIVE_AS_IF_REPLAY_V219_UNIT",
        "projection_selected_date_start": "2026-05-13",
        "projection_selected_date_end": "2026-05-17",
        "projection_selected_profiles": ["repaired_package_conversion_v3"],
        "projection_candidate_source_class": (
            "authoritative_broad_candidate_ledger"
        ),
        "projection_candidate_source_path": "/tmp/v219-candidate-ledger.jsonl",
        "projection_candidate_source_binding_status": (
            "exact_selected_broad_prefix_candidate_authority"
        ),
        "projection_source_window_status": "inside_selected_window",
        "projection_source_profile_status": "inside_selected_profile",
        "candidate_present": True,
        "scorecard_present": True,
        "scheduler_selected": True,
        "order_present": True,
        "missed_present": True,
        "raw_selector_action": "reject",
        "effective_selector_action": "open-reduced-risk",
        "canonical_quality_source": "predecision_fixture_no_outcome_fields",
        "canonical_quality_field_sources": {
            "expected_net_r": "fixture.expected_net_r",
            "probability": "fixture.probability",
            "source_completeness": "fixture.source_completeness",
        },
        "canonical_expected_net_r": 0.8,
        "canonical_probability": 0.75,
        "canonical_source_completeness": 1.0,
        "canonical_quality_contract_status": "pass",
        "canonical_quality_contract_violations": [],
        "package_authority_valid": True,
        "package_authority_status": "valid_signed_predecision_new_entry_authority",
        "package_order_executable_allowed": True,
        "package_order_executable_reason": "order_executable",
        "package_order_executable_blocker_class": "",
        "risk_finalizer_action": "open-reduced-risk",
        "risk_finalizer_reason": "signed_reduced_risk_authority",
        "scheduler_rank": 2,
        "order_binding_status": "order_bound",
        "trade_binding_status": "trade_absent",
        "order_trade_binding_status": "order_bound_trade_absent",
        "terminal_fallback_status": "not_eligible",
        "terminal_fallback_blocker": "adverse_drift_ceiling",
        "terminal_fallback_eligible": False,
        "terminal_fallback_configured": True,
        "terminal_fallback_attempted": False,
        "terminal_fallback_applied": False,
        "terminal_counterfactual_present": True,
        "selected_expiry_fallback": True,
        "risk_behavior": "reduced-risk",
        "exact_deviation_stage": "terminal_fallback",
        "exact_deviation_reason": "selected_expiry_fallback_blocked:adverse_drift_ceiling",
    }
    rows = [
        {
            **base,
            "candidate_instance_parity_key": "candidate-a@@2026-05-13T10:15:00Z",
            "decision_time_utc": "2026-05-13T10:15:00Z",
            "origin_family": "current_fvg_fill",
            "trade_present": False,
        },
        {
            **base,
            "candidate_instance_parity_key": "candidate-b@@2026-05-13T10:30:00Z",
            "decision_time_utc": "2026-05-13T10:30:00Z",
            "origin_family": "current_ob_retest",
            "trade_present": True,
            "missed_present": False,
            "canonical_quality_contract_status": "violation",
            "canonical_quality_contract_violations": [
                "canonical_quality_probability_source_missing"
            ],
            "risk_finalizer_action": "trade",
            "risk_behavior": "full-risk",
            "trade_binding_status": "trade_bound",
            "order_trade_binding_status": "exact_order_trade_bound",
            "selected_expiry_fallback": False,
            "terminal_fallback_status": "not_applicable",
            "terminal_fallback_blocker": "",
            "terminal_counterfactual_present": False,
            "exact_deviation_stage": "trade",
            "exact_deviation_reason": "executed_positive_r:target_reached_before_stop",
        },
    ]

    builder_summary = builder.summarize_candidate_instance_projection_rows(rows)
    projection_path = tmp_path / "projection.jsonl"
    write_jsonl(projection_path, rows)
    analyzer_summary = analyzer.summarize_candidate_instance_parity_projection(
        projection_path
    )

    for summary in (builder_summary, analyzer_summary):
        assert summary["row_count"] == 2
        assert summary["duplicate_candidate_instance_parity_key_count"] == 0
        if summary is builder_summary:
            assert summary["profile_stage_presence_counts"] == {
                "repaired_package_conversion_v3": {
                    "candidate": 2,
                    "missed": 1,
                    "order": 2,
                    "scheduler_selected": 2,
                    "scorecard": 2,
                    "trade": 1,
                }
            }
            assert summary[
                "package_candidate_identity_match_status_counts"
            ] == {"missing": 2}
        assert summary["canonical_quality_contract"]["violation_row_count"] == 1
        assert summary["origin_family_scorecard_order_fill_transfer"][
            "current_fvg_fill"
        ]["scorecard_to_order"] == 1
        assert summary["origin_family_scorecard_order_fill_transfer"][
            "current_fvg_fill"
        ]["order_to_fill"] == 0
        assert summary["selected_expiry_fallback_proof"][
            "selected_expiry_candidate_instances"
        ] == 1
        assert summary["selected_expiry_fallback_proof"]["proof_complete"] == 1
        assert summary["full_reduced_risk_behavior"]["order_counts"] == {
            "full-risk": 1,
            "reduced-risk": 1,
        }
        assert summary["full_reduced_risk_behavior"]["filled_trade_counts"] == {
            "full-risk": 1
        }
        assert summary["projection_source_scope"]["assertion_status"] == "pass"
        assert summary["projection_source_scope"][
            "out_of_window_candidate_instance_count"
        ] == 0
        assert summary["projection_source_scope"]["min_decision_time_utc"] == (
            "2026-05-13T10:15:00Z"
        )
        assert summary["projection_source_scope"]["max_decision_time_utc"] == (
            "2026-05-13T10:30:00Z"
        )


def test_projection_source_scope_assertion_counts_out_of_window_rows(tmp_path):
    builder = load_parity_builder()
    analyzer = load_flow_analyzer()
    row = {
        "candidate_instance_parity_key": "candidate-old@@2026-05-05T10:15:00Z",
        "candidate_id": "candidate-old",
        "decision_time_utc": "2026-05-05T10:15:00Z",
        "broad_replay_profile": "repaired_package_conversion_v3",
        "projection_source_scope_mode": "exact_broad_prefix",
        "projection_source_prefix": "BROAD_LIVE_AS_IF_REPLAY_V219_UNIT",
        "projection_selected_date_start": "2026-05-13",
        "projection_selected_date_end": "2026-05-17",
        "projection_selected_profiles": ["repaired_package_conversion_v3"],
        "projection_candidate_source_class": (
            "exact_bound_selected_package_bridge_candidate_ledger"
        ),
        "projection_candidate_source_path": "/tmp/unexpected-bridge.jsonl",
        "projection_candidate_source_binding_status": "unexpected_test_binding",
        "projection_source_window_status": "outside_selected_window",
        "projection_source_profile_status": "inside_selected_profile",
        "candidate_present": True,
    }
    projection_path = tmp_path / "projection-outside-window.jsonl"
    write_jsonl(projection_path, [row])

    summaries = (
        builder.summarize_candidate_instance_projection_rows([row]),
        analyzer.summarize_candidate_instance_parity_projection(projection_path),
    )

    for summary in summaries:
        source_scope = summary["projection_source_scope"]
        assert source_scope["out_of_window_candidate_instance_count"] == 1
        assert source_scope["assertions"]["selected_window"]["status"] == (
            "fail_projection_rows_outside_or_unverifiable_window"
        )
        assert source_scope["assertion_status"] == "fail"


def test_candidate_projection_uses_trading_day_for_session_boundary_window():
    builder = load_parity_builder()
    row = builder.candidate_instance_projection(
        candidate={
            "candidate_id": "candidate-session-boundary",
            "decision_time_utc": "2026-05-15T00:00:00Z",
            "trading_day": "2026-05-14",
            "broad_replay_profile": "repaired_package_conversion_v3",
            "projection_source_scope_mode": "exact_broad_prefix",
            "projection_source_prefix": "BROAD_LIVE_AS_IF_REPLAY_V220R12_UNIT",
            "projection_selected_date_start": "2026-05-13",
            "projection_selected_date_end": "2026-05-14",
            "projection_selected_profiles": ["repaired_package_conversion_v3"],
            "projection_candidate_source_class": (
                "authoritative_broad_candidate_ledger"
            ),
            "projection_candidate_source_path": "/tmp/v220r12-candidates.jsonl",
            "projection_candidate_source_binding_status": (
                "exact_selected_broad_prefix_candidate_authority"
            ),
            "symbol": "XAUUSD",
            "side": "LONG",
            "selector_action": "reject",
            "effective_selector_action": "reject",
        },
        enrich={},
        package_candidate=None,
        generated="2026-07-11T00:00:00Z",
    )

    assert row["projection_source_window_status"] == "inside_selected_window"
    assert row["projection_source_window_date"] == "2026-05-14"
    assert row["projection_source_window_date_source"] == "candidate.trading_day"
    summary = builder.summarize_candidate_instance_projection_rows([row])
    assert summary["projection_source_scope"][
        "row_source_window_date_source_counts"
    ] == {"candidate.trading_day": 1}
    assert summary["projection_source_scope"]["assertion_status"] == "pass"


def test_local_cache_promotes_complete_tmp_without_recopy(tmp_path, monkeypatch):
    builder = load_parity_builder()
    source = tmp_path / "source.jsonl"
    source.write_bytes(b'{"row": 1}\n')
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    monkeypatch.setattr(builder, "JSONL_BINARY_STREAM_MIN_BYTES", 1)
    monkeypatch.setattr(builder, "JSONL_LOCAL_CACHE_DIR", cache_dir)
    path_size = source.stat().st_size
    cache_key = builder.hashlib.sha256(
        f"{source.resolve()}|{path_size}|{source.stat().st_mtime_ns}".encode("utf-8")
    ).hexdigest()[:24]
    cached = cache_dir / f"{cache_key}_{source.name}"
    pending = cached.with_suffix(cached.suffix + ".tmp")
    pending.write_bytes(source.read_bytes())

    def unexpected_copy(*_args, **_kwargs):
        raise AssertionError("complete cache tmp must be promoted without recopy")

    monkeypatch.setattr(builder.subprocess, "run", unexpected_copy)

    assert builder.local_cached_jsonl_path(source) == cached
    assert cached.read_bytes() == source.read_bytes()
    assert not pending.exists()


def test_local_cache_can_be_disabled_for_direct_local_streaming(tmp_path, monkeypatch):
    builder = load_parity_builder()
    source = tmp_path / "source.jsonl"
    source.write_bytes(b'{"row": 1}\n')
    cache_dir = tmp_path / "cache"
    monkeypatch.setattr(builder, "JSONL_LOCAL_CACHE_ENABLED", False)
    monkeypatch.setattr(builder, "JSONL_LOCAL_CACHE_DIR", cache_dir)

    assert builder.local_cached_jsonl_path(source) == source
    assert not cache_dir.exists()


def test_representative_candidate_quality_prefers_executable_proof_row():
    builder = load_parity_builder()

    fields = builder.representative_candidate_quality_fields(
        [
            {
                "candidate_generated": True,
                "candidate_id": "source-only",
                "package_replay_executable_candidate_use_allowed": False,
            },
            {
                "candidate_generated": True,
                "candidate_id": "exec-proof",
                "package_replay_executable_candidate_use_allowed": True,
                "package_replay_executable_candidate_use_allowed_reason": (
                    "broker_cost_selector_and_scheduler_action_executable"
                ),
                "pretrade_cost_packet_status": "PASSED",
                "cost_authority": "broker_calibrated_replay_cost",
                "pretrade_cost_packet_authority": "broker_calibrated_replay_cost",
                "cost_source_gap_status": "source_bound_cost_authority_present",
                "scheduler_materialization_action_intent": "new_position",
                "selector_action": "trade",
            },
        ]
    )

    assert fields["candidate_id"] == "exec-proof"
    assert fields["pretrade_cost_packet_status"] == "PASSED"
    assert fields["cost_authority"] == "broker_calibrated_replay_cost"
    assert fields["pretrade_cost_packet_authority"] == "broker_calibrated_replay_cost"
    assert fields["cost_source_gap_status"] == "source_bound_cost_authority_present"
    assert fields["scheduler_materialization_action_intent"] == "new_position"


def test_packet_sidecar_selected_candidate_ids_join_without_candidate_id(tmp_path, monkeypatch):
    builder = load_parity_builder()
    broad_paths = (
        "BROAD_CANDIDATE_PATH",
        "BROAD_SCORECARD_PATH",
        "BROAD_ORDER_PATH",
        "BROAD_ORACLE_PATH",
        "BROAD_TRADE_PATH",
        "BROAD_MISSED_PATH",
        "BROAD_PACKET_SIDECAR_PATH",
    )
    for attr in broad_paths:
        path = tmp_path / f"{attr}.jsonl"
        monkeypatch.setattr(builder, attr, path)
        builder.write_jsonl(path, [])

    candidate = {
        "broad_replay_profile": "repaired_package_conversion_v3",
        "candidate_id": "candidate-1",
        "decision_time_utc": "2026-05-13T10:15:00Z",
        "symbol": "XAUUSD",
        "side": "LONG",
        "split": "holdout",
        "chunk_id": "chunk-001",
        "packet_sidecar_id": "candidate-sidecar-1",
        "packet_sidecar_hash_sha256": "candidate-hash-1",
    }
    builder.write_jsonl(builder.BROAD_CANDIDATE_PATH, [candidate])
    builder.write_jsonl(
        builder.BROAD_PACKET_SIDECAR_PATH,
        [
            {
                "sidecar_type": "scheduler_v4_window",
                "packet_sidecar_id": "scheduler-sidecar-1",
                "packet_sidecar_hash_sha256": "scheduler-hash-1",
                "selected_candidate_ids": ["candidate-1"],
                "broad_replay_profile": "repaired_package_conversion_v3",
                "decision_time_utc": "2026-05-13T10:15:00Z",
                "symbol": "XAUUSD",
                "side": "LONG",
                "split": "holdout",
                "chunk_id": "chunk-001",
            }
        ],
    )

    candidates, _by_axis, enrichment = builder.load_broad_indexes()
    key = builder.candidate_instance_key(candidate)

    assert builder.candidate_key(candidate) in candidates
    assert enrichment[key]["packet_sidecar_present"] is True
    assert "scheduler-sidecar-1" in enrichment[key]["packet_sidecar_ids"]
    assert "scheduler-hash-1" in enrichment[key]["packet_sidecar_hashes"]


def test_selector_reject_missed_r_is_blocked_counterfactual_not_execution_leakage():
    builder = load_parity_builder()

    adjusted = builder.apply_execution_leakage_accounting(
        {
            "missed_count": 3,
            "missed_net_proxy_r_sum": 12.5,
            "missed_positive_net_r_sum": 14.0,
            "missed_negative_net_r_sum": -1.5,
            "miss_reason_counts": {"selector_rejected_candidate": 3},
        },
        label="candidate_generated_selector_reject",
    )

    assert adjusted["missed_count"] == 0
    assert adjusted["missed_net_proxy_r_sum"] == 0.0
    assert adjusted["blocked_counterfactual_missed_count"] == 3
    assert adjusted["blocked_counterfactual_missed_net_proxy_r_sum"] == 12.5
    assert adjusted["blocked_counterfactual_miss_reason_counts"] == {
        "selector_rejected_candidate": 3
    }
    assert (
        adjusted["missed_opportunity_accounting"]
        == "blocked_counterfactual_not_execution_leakage"
    )


def test_cost_source_gap_missed_r_is_blocked_counterfactual_not_execution_leakage():
    builder = load_parity_builder()

    adjusted = builder.apply_execution_leakage_accounting(
        {
            "missed_count": 2,
            "missed_net_proxy_r_sum": 3.25,
            "missed_positive_net_r_sum": 3.25,
            "missed_negative_net_r_sum": 0.0,
            "miss_reason_counts": {"cost_source_gap": 2},
        },
        label=(
            "candidate_generated_broker_cost_source_gap_not_executable:"
            "SOURCE_GAP_COST_FALLBACK"
        ),
    )

    assert adjusted["missed_count"] == 0
    assert adjusted["blocked_counterfactual_missed_count"] == 2
    assert adjusted["blocked_counterfactual_missed_net_proxy_r_sum"] == 3.25
    assert (
        adjusted["missed_opportunity_accounting"]
        == "blocked_counterfactual_not_execution_leakage"
    )


def test_selector_reject_with_downstream_execution_fields_gets_materialization_label():
    builder = load_parity_builder()

    label = builder.leakage_label(
        {
            "candidate_generated_count": 1,
            "scorecard_selected_count": 0,
            "selector_action_counts": {"reject": 1},
            "scheduler_option_present_count": 1,
            "order_present_count": 0,
            "oracle_present_count": 0,
            "trade_count": 0,
            "missed_count": 0,
        }
    )

    assert label == (
        "candidate_generated_selector_reject_downstream_execution_"
        "materialized:scheduler_option_present_count"
    )
    assert builder.repair_stage_for_label(label) == "selector_admission_calibration"


def test_selector_reject_with_only_missed_diagnostic_is_not_downstream_materialized():
    builder = load_parity_builder()

    label = builder.leakage_label(
        {
            "candidate_generated_count": 1,
            "scorecard_selected_count": 0,
            "selector_action_counts": {"reject": 1},
            "scheduler_option_present_count": 0,
            "order_present_count": 0,
            "oracle_present_count": 0,
            "trade_count": 0,
            "missed_count": 7,
            "pretrade_cost_packet_status_counts": {"PASSED": 7},
            "cost_source_gap_status_counts": {"source_bound_cost_authority_present": 7},
        }
    )

    assert label == "candidate_generated_selector_reject"


def test_selector_reject_cost_refused_precedes_missed_diagnostic_label():
    builder = load_parity_builder()

    label = builder.leakage_label(
        {
            "candidate_generated_count": 1,
            "scorecard_selected_count": 0,
            "selector_action_counts": {"reject": 1},
            "scheduler_option_present_count": 0,
            "order_present_count": 0,
            "oracle_present_count": 0,
            "trade_count": 0,
            "missed_count": 5,
            "pretrade_cost_packet_status_counts": {"REFUSED": 5},
            "cost_source_gap_status_counts": {"source_bound_cost_authority_present": 5},
        }
    )

    assert label == "candidate_generated_broker_cost_refused_not_executable"


def test_selector_reject_cost_source_gap_precedes_missed_diagnostic_label():
    builder = load_parity_builder()

    label = builder.leakage_label(
        {
            "candidate_generated_count": 1,
            "scorecard_selected_count": 0,
            "selector_action_counts": {"reject": 1},
            "scheduler_option_present_count": 0,
            "order_present_count": 0,
            "oracle_present_count": 0,
            "trade_count": 0,
            "missed_count": 2,
            "pretrade_cost_packet_status_counts": {"PASSED": 2},
            "cost_source_gap_status_counts": {"SOURCE_GAP_COST_FALLBACK": 2},
        }
    )

    assert (
        label
        == "candidate_generated_broker_cost_source_gap_not_executable:"
        "SOURCE_GAP_COST_FALLBACK"
    )


def test_reduce_risk_not_scheduler_selected_maps_to_scheduler_reallocation():
    builder = load_parity_builder()

    assert (
        builder.repair_stage_for_label(
            "candidate_generated_selector_reduce_risk_not_scheduler_selected"
        )
        == "scheduler_ranking_reallocation"
    )


def test_replay_order_cost_authority_blocks_weak_cost_packets():
    from src.research_infra.v4_timewarp_simulated_live_research_loop import (
        replay_order_cost_authority_block_reason,
    )

    config = {
        "gtos_vnext_runtime": {
            "broad_live_as_if_no_broker_replay": True,
            "broad_live_as_if_replay_enforce_broker_cost_packet_status": True,
        }
    }

    assert replay_order_cost_authority_block_reason(
        {"pretrade_broker_net_cost_packet": {"status": "REFUSED"}},
        config,
    ) == "broker_cost_packet_refused:unspecified"
    assert replay_order_cost_authority_block_reason(
        {
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
                "cost_source_gap_status": "SOURCE_GAP_COST_FALLBACK",
            }
        },
        config,
    ) == "broker_cost_source_gap_not_executable:SOURCE_GAP_COST_FALLBACK"
    assert replay_order_cost_authority_block_reason(
        {
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
                "cost_source_gap_status": "source_bound_cost_authority_present",
                "candidate_cost_r_fallback_is_authority": True,
            }
        },
        config,
    ) == "candidate_cost_r_fallback_not_order_authority"
    assert replay_order_cost_authority_block_reason(
        {
            "pretrade_broker_net_cost_packet": {
                "status": "PASSED",
                "authority": "broker_calibrated_replay_cost",
                "cost_source_gap_status": "source_bound_cost_authority_present",
                "candidate_cost_r_fallback_is_authority": False,
            }
        },
        config,
    ) is None


def test_replay_normalizer_compacts_nested_source_records():
    from src.research_infra.v4_timewarp_simulated_live_research_loop import normalize_row

    row = normalize_row(
        {
            "time": "2026-05-13T07:00:00+00:00",
            "open": "1.0",
            "high": "2.0",
            "low": "0.5",
            "close": "1.5",
            "volume": "10",
            "source_records": [
                {"time": "2026-05-13T07:00:00+00:00", "open": 1.0},
                {"time": "2026-05-13T07:15:00+00:00", "open": 1.2},
            ],
        },
        symbol="XAUUSD",
    )

    assert row is not None
    assert row["source_records"] == 2.0
    assert row["source_records_compacted"] is True
    assert row["source_records_original_count"] == 2
    assert "source_records_sample_hash_sha256" in row


def test_broad_replay_compacts_probability_source_maps_before_hashing():
    from src.research_infra.v4_timewarp_simulated_live_research_loop import (
        compact_payload,
        stable_sha256,
    )

    packet = {
        "schema_version": "test",
        "field_group_statuses": {
            "source_completeness": {
                "status": "complete",
                "sources": {
                    f"source_{idx:04d}": {"nested": [{"value": idx}] * 5}
                    for idx in range(300)
                },
            }
        },
    }

    compacted = compact_payload(packet, max_bytes=500)
    assert compacted["payload_compaction_reason"] == "probability_field_group_sources"
    sources = compacted["field_group_statuses"]["source_completeness"]["sources"]
    assert sources["source_count"] == 300
    assert len(sources["source_keys_sample"]) == 50
    assert stable_sha256(compacted)


def test_broad_replay_compacts_live_decision_packet_field_groups():
    from src.research_infra.v4_timewarp_simulated_live_research_loop import compact_payload

    packet = {
        "schema_name": "LiveDecisionPacketV4",
        "schema_version": "live_decision_packet_v4_test",
        "candidate_identity": {"candidate_id": "candidate-1"},
        "source_event_hash_sha256": "source-hash",
        "packet_hash_sha256": "packet-hash",
        "required_field_groups": ["scheduler_allocator"],
        "field_groups": {
            "scheduler_allocator": {
                "owner": "scheduler_v4_best_trade_allocator",
                "group_source_status": "captured_present",
                "missing_fields": [],
                "all_options_preserved": [{"candidate_id": idx} for idx in range(500)],
            }
        },
        "source_gap_rows": [{"field": idx} for idx in range(50)],
    }

    compacted = compact_payload(packet, max_bytes=500)
    assert compacted["payload_compaction_reason"] == "live_decision_packet_v4_field_groups"
    assert compacted["source_gap_row_count"] == 50
    assert compacted["field_group_statuses"]["scheduler_allocator"]["key_count"] == 4


def test_broad_replay_compacts_unknown_large_nested_payloads():
    from src.research_infra.v4_timewarp_simulated_live_research_loop import compact_payload

    payload = {
        "packet_type": "unknown_future_packet",
        "rows": [{"candidate_id": f"candidate-{idx}", "value": idx} for idx in range(250)],
        "source_map": {f"key_{idx}": {"value": idx} for idx in range(120)},
    }

    compacted = compact_payload(payload, max_bytes=500)
    assert compacted["payload_compaction_reason"] == "generic_mapping_shape_no_full_json_probe"
    assert compacted["nested_shapes"]["rows"]["item_count"] == 250
    assert compacted["nested_shapes"]["source_map"]["key_count"] == 120
    assert compacted["payload_shape_hash_sha256"]


def test_trade_params_hash_compacts_large_candidate_payloads():
    from src.research_infra.v4_timewarp_simulated_live_research_loop import (
        build_trade_params,
        compact_payload,
        stable_sha256,
    )

    candidate = {
        "candidate_id": "candidate-large",
        "symbol": "XAUUSD",
        "side": "LONG",
        "entry_price": 2400.0,
        "stop_loss": 2390.0,
        "risk_reward_ratio": 2.0,
        "source_records": [{"time": idx, "open": idx * 1.0} for idx in range(500)],
        "source_map": {f"key_{idx}": {"value": idx} for idx in range(200)},
    }

    trade_params = build_trade_params(
        candidate=candidate,
        selector_packet={"packet_hash_sha256": "selector-hash", "action": "trade"},
        scheduler_packet={"decision": {"selected_action_class": "enter"}},
        lifecycle_packet={"action": "allow"},
        geometry_contract={"packet_hash_sha256": "geometry-hash"},
        risk_pct=0.25,
        source_hash="source-hash",
        source_path="source.csv",
        cost_r=0.05,
    )

    assert trade_params["gtos_vnext_source_event_hash"] == stable_sha256(
        compact_payload(candidate)
    )
    assert trade_params["gtos_vnext_live_as_if_replay_no_broker_authority"] is True
    assert trade_params["gtos_vnext_replay_broker_mutation_enabled"] is False
    assert trade_params["gtos_vnext_replay_source_boundary"] == (
        "local_live_as_if_replay_selected_path_no_broker_order_authority"
    )


def test_selector_hash_compacts_large_ultimate_package_payloads():
    from src.components.selector_v4 import (
        SelectorV4AdmissionDecision,
        _compact_selector_hash_payload,
    )

    component_scores = {
        "numeric_confluence": {
            "status": "complete",
            "source_count": 250,
            "sources": {
                f"source_{idx:04d}": {
                    "candidate_id": f"candidate-{idx}",
                    "source_records": [{"time": item, "open": item} for item in range(20)],
                }
                for idx in range(250)
            },
        },
        "probability_debate": {"status": "complete", "selected_action": "long"},
        "admission_quality": {
            "status": "accepted",
            "expected_net_r": 0.4,
            "probability": 0.66,
            "fill_probability": 0.74,
            "source_completeness": 0.93,
            "symbol": "XAUUSD",
            "side": "LONG",
        },
        "ultimate_candidate_package": {
            "all_options_preserved": [
                {"candidate_id": f"candidate-{idx}", "expected_net_r": 0.2}
                for idx in range(300)
            ],
            "source_map": {f"axis_{idx}": {"rows": list(range(30))} for idx in range(120)},
        },
    }

    compacted = _compact_selector_hash_payload(component_scores)
    assert compacted["ultimate_candidate_package"]["payload_compacted_for_selector_hash"]
    assert compacted["numeric_confluence"]["sources"]["payload_compacted_for_selector_hash"]

    record = SelectorV4AdmissionDecision(
        schema_version="selector_v4_test",
        component="selector_v4",
        enabled=True,
        apply_to_execution=True,
        live_activation_allowed_by_config=False,
        action="trade",
        would_action="trade",
        decision_status="selector_v4_no_runtime_effect_for_this_decision",
        reason="test",
        runtime_effect_now=False,
        candidate_use_allowed_now=False,
        source_bound_candidate_use_allowed_now=False,
        replay_candidate_use_allowed_now=False,
        risk_multiplier=1.0,
        final_risk_pct=0.25,
        component_scores=component_scores,
    ).to_record()

    assert record["source_event_hash_sha256"]
    assert record["packet_hash_sha256"]
    assert record["component_scores"] == component_scores


def test_broad_replay_raw_data_hash_uses_source_identity_not_candles():
    from src.research_infra.v4_timewarp_simulated_live_research_loop import (
        predecision_raw_data_identity_hash,
    )

    first = predecision_raw_data_identity_hash(
        symbol="XAUUSD",
        asof_utc="2026-05-13T10:15:00+00:00",
        row_counts={"M15": 240, "H1": 120},
        source_hashes={"M15": "hash-m15", "H1": "hash-h1"},
        max_source_times={"M15": "2026-05-13T10:00:00+00:00", "H1": "2026-05-13T09:00:00+00:00"},
        source_paths={"M15": "m15.csv", "H1": "h1.csv"},
    )
    second = predecision_raw_data_identity_hash(
        symbol="XAUUSD",
        asof_utc="2026-05-13T10:15:00+00:00",
        row_counts={"M15": 240, "H1": 120},
        source_hashes={"M15": "hash-m15", "H1": "hash-h1"},
        max_source_times={"M15": "2026-05-13T10:00:00+00:00", "H1": "2026-05-13T09:00:00+00:00"},
        source_paths={"M15": "m15.csv", "H1": "h1.csv"},
    )

    assert first == second


def test_historical_adapter_decision_metadata_uses_context_symbol_for_hash():
    from datetime import datetime, timezone

    from src.research_infra.v4_timewarp_simulated_live_research_loop import (
        HistoricalMT5Adapter,
        PRIMARY_DECISION_TIMEFRAMES,
    )

    adapter = HistoricalMT5Adapter({})
    asof = datetime(2026, 5, 13, 0, 15, tzinfo=timezone.utc)
    adapter.set_replay_context(symbol="XAUUSD", asof=asof)
    adapter._last_calls = {
        timeframe: {
            "returned_count": 500,
            "latest_closed_time": "2026-05-13T00:00:00+00:00",
            "source_path": f"/tmp/XAUUSD_{timeframe}.csv",
            "source_hash": f"hash-{timeframe}",
        }
        for timeframe in PRIMARY_DECISION_TIMEFRAMES
    }

    metadata = adapter.decision_metadata(raw_data={})

    assert metadata["decision_time_utc"] == "2026-05-13T00:15:00+00:00"
    assert metadata["decision_timeframes_present"] == list(PRIMARY_DECISION_TIMEFRAMES)
    assert metadata["m1_or_tick_attached_to_decision"] is False
    assert len(metadata["raw_data_hash_sha256"]) == 64


def test_package_replay_policy_survives_shadow_selected_other_candidate():
    from src.research_infra.v4_timewarp_simulated_live_research_loop import (
        selected_ultimate_execution_policy_shadow,
    )

    packet = {
        "ultimate_candidate_package_shadow": {
            "shadow_selected_candidate_id": "candidate-a",
            "execution_policy_shadow": {
                "would_guarded_market_fallback": "guarded_market_after_fillability_cost_proof"
            },
        }
    }
    candidate = {
        "candidate_id": "candidate-b",
        "ultimate_package_admission_sleeve_match_count": 1.0,
        "ultimate_package_source_bound_candidate_use_allowed": True,
        "ultimate_package_role_disposition": "admission_candidate",
    }

    policy = selected_ultimate_execution_policy_shadow(
        packet,
        "candidate-b",
        candidate=candidate,
    )

    assert policy["status"].endswith("shadow_selected_other_candidate")
    assert policy["execution_policy_shadow"]["would_guarded_market_fallback"] == (
        "guarded_market_after_fillability_cost_proof"
    )
    assert policy["execution_policy_shadow"]["broker_operation"] is False


def test_broad_replay_compaction_does_not_stringify_unknown_objects():
    from src.research_infra.v4_timewarp_simulated_live_research_loop import compact_payload

    class ExplodingStr:
        def __str__(self):
            raise AssertionError("compact_payload should not stringify unknown objects")

    compacted = compact_payload({"safe": 1, "unknown": ExplodingStr()}, max_bytes=50)

    assert compacted["payload_compaction_reason"] == "generic_mapping_shape_no_full_json_probe"
    assert compacted["nested_shapes"]["unknown"]["type"] == "ExplodingStr"


def test_selector_hash_compaction_does_not_stringify_unknown_objects():
    from src.components.selector_v4 import _compact_selector_hash_payload

    class ExplodingStr:
        def __str__(self):
            raise AssertionError("selector hash compaction should not stringify unknown objects")

    compacted = _compact_selector_hash_payload({"safe": 1, "unknown": ExplodingStr()})

    assert compacted["unknown"]["payload_compaction_reason"] == "large_text_or_object_shape"
    assert compacted["unknown"]["payload_type"] == "ExplodingStr"


def test_repaired_profile_authorizes_replay_only_profit_preservation_without_live_claims():
    harness = load_broad_replay_harness()

    config = harness.build_config(harness.PROFILE_REPAIRED)
    runtime = config["gtos_vnext_runtime"]
    harness_contract = config["broad_live_as_if_replay_harness"]

    assert runtime["scheduler_v4_best_trade_allocator_package_marketable_entry_guard_enabled"]
    assert runtime[
        "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_allowed"
    ] is True
    assert "suppressing all marketable package entries" in runtime[
        "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_demotion_reason"
    ]
    assert runtime["ultimate_candidate_package_strong_fill_floor_bypass_enabled"]
    assert (
        runtime["ultimate_candidate_package_strong_fill_floor_bypass_min_expected_net_r"]
        == 0.70
    )
    assert (
        runtime["ultimate_candidate_package_strong_fill_floor_bypass_min_probability"]
        == 0.70
    )
    assert (
        runtime["ultimate_candidate_package_strong_fill_floor_bypass_min_fill_probability"]
        == 0.20
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_enabled"
        ]
        is True
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_selector_trade_only"
        ]
        is False
    )
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_opening_quality_floor_release_enabled"
        ]
        is False
    )
    assert "regressed repaired profile" in (
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_opening_quality_floor_release_demotion_reason"
        ]
    )
    assert runtime[
        "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_namespace_status"
    ] == (
        "authoritative_namespace_only_legacy_dynamic_budget_package_fill_floor_bypass_removed"
    )
    assert runtime["profit_harvest_mfe_capture_v4_enabled"] is True
    assert "mfe_giveback_leak" in runtime[
        "profit_harvest_mfe_capture_v4_enabled_source"
    ]
    assert runtime["profit_harvest_mfe_capture_v4_min_mfe_r"] == 0.50
    assert runtime["profit_harvest_mfe_capture_v4_stop_activation_mfe_r"] == 0.50
    assert runtime["profit_harvest_mfe_capture_v4_target_activation_fraction"] == 0.75
    assert runtime["profit_harvest_mfe_capture_v4_trail_gap_r"] == 0.35
    assert runtime["profit_harvest_mfe_capture_v4_cost_aware_protect_floor_enabled"] is True
    assert runtime["profit_harvest_mfe_capture_v4_allow_m1_proxy_final_r_authority"] is True
    assert runtime[
        "profit_harvest_mfe_capture_v4_m1_proxy_final_r_authority_source"
    ] == (
        "owner_approved_reconstructed_proxy_replay_authority_m1_ordered_path_not_live"
    )
    assert runtime["profit_harvest_mfe_capture_v4_min_hold_minutes_before_stop_raise"] == 0
    assert runtime["ultimate_candidate_package_replay_execution_allowed_sides"] == []
    assert "demoted_after_BROAD_LIVE_AS_IF_REPLAY_LEDGER_TRUTH_REPAIR_SMOKE" in runtime[
        "ultimate_candidate_package_replay_execution_side_policy"
    ]
    assert (
        runtime[
            "scheduler_v4_best_trade_allocator_selected_policy_expected_net_calibration_required_for_new_risk"
        ]
        is True
    )
    assert (
        runtime["selector_v4_router_refusal_expected_net_policy_calibration_required"]
        is True
    )
    assert "candidate_expected_net_r_bridge_proxy_is diagnostic_missed_only" in runtime[
        "selected_policy_expected_net_calibration_execution_policy"
    ]
    assert (
        config["ultimate_replay_loss_bucket_policy"]["profit_harvest_overlay"][
            "enabled"
        ]
        is True
    )
    assert (
        config["ultimate_replay_loss_bucket_policy"]["profit_harvest_overlay"][
            "repair_status"
        ]
        == "sub1r_protective_floor_replay_authority_enabled_after_mfe_giveback_leak"
    )
    assert runtime["ultimate_candidate_package_live_activation_allowed"] is False
    assert runtime["ultimate_candidate_package_final_package_selected"] is False
    assert runtime["scheduler_v4_best_trade_allocator_live_activation_allowed"] is False
    assert harness_contract["live_broker_authority"] is False
    assert harness_contract["broker_mutation_enabled"] is False
    assert harness_contract["final_selection_claim"] is False


def test_replay_loss_bucket_full_admission_guard_is_diagnostic_after_reallocation_regression():
    harness = load_broad_replay_harness()

    config = harness.build_config(harness.PROFILE_REPAIRED)
    runtime = config["gtos_vnext_runtime"]
    rules = runtime["scheduler_v4_best_trade_allocator_replay_loss_bucket_guard_rules"]
    full_admission_rules = [
        row
        for row in rules
        if row.get("rule_id") == "demote_selector_trade_full_admission_uncalibrated"
    ]

    assert full_admission_rules
    assert all(row.get("enabled") is False for row in full_admission_rules)
    assert (
        full_admission_rules[0]["reason"]
        == "diagnostic_only_after_reallocation_regression"
    )
    assert "fell from +1.40956687R to -1.47512711R" in full_admission_rules[0][
        "evidence_basis"
    ]
    assert runtime["ultimate_candidate_package_live_activation_allowed"] is False
    assert runtime["ultimate_candidate_package_final_package_selected"] is False
    assert runtime["scheduler_v4_best_trade_allocator_live_activation_allowed"] is False


def test_missed_reason_splits_risk_finalizer_lifecycle_and_option_gaps():
    from src.research_infra.v4_timewarp_simulated_live_research_loop import (
        missed_reason_for_scheduler_nonselection,
    )

    assert (
        missed_reason_for_scheduler_nonselection(
            candidate_id="preselected",
            scheduler_option={"decision_status": "candidate_ranked", "reason": "ranked"},
            original_selected_id_set={"preselected"},
            final_selected_id_set=set(),
            scheduler_zeroed_window=False,
        )
        == "risk_finalizer_rejected_preselected_candidate"
    )
    assert (
        missed_reason_for_scheduler_nonselection(
            candidate_id="same-symbol",
            scheduler_option={
                "decision_status": "candidate_vetoed",
                "reason": "duplicate_position",
                "vetoes": ["same_symbol_duplicate_requires_lifecycle_scale_or_replace"],
            },
            original_selected_id_set=set(),
            final_selected_id_set=set(),
            scheduler_zeroed_window=False,
        )
        == "same_symbol_lifecycle_veto"
    )
    assert (
        missed_reason_for_scheduler_nonselection(
            candidate_id="missing",
            candidate={"scheduler_materialization_skip_reason": "selector_not_risk_bearing"},
            scheduler_option=None,
            original_selected_id_set=set(),
            final_selected_id_set=set(),
            scheduler_zeroed_window=False,
        )
        == "scheduler_materialization_skipped_selector_not_risk_bearing"
    )
    assert (
        missed_reason_for_scheduler_nonselection(
            candidate_id="missing",
            scheduler_option=None,
            original_selected_id_set=set(),
            final_selected_id_set=set(),
            scheduler_zeroed_window=False,
        )
        == "scheduler_option_missing_nonselected_candidate"
    )
    assert (
        missed_reason_for_scheduler_nonselection(
            candidate_id="ranked",
            scheduler_option={"decision_status": "candidate_ranked", "reason": "ranked"},
            original_selected_id_set=set(),
            final_selected_id_set=set(),
            scheduler_zeroed_window=True,
        )
        == "scheduler_zero_trade_window_candidate_not_preselected"
    )


def test_risk_finalizer_probe_fields_are_materialized_for_missed_rows():
    from src.research_infra.v4_timewarp_simulated_live_research_loop import (
        risk_finalizer_missed_opportunity_attribution_fields,
        risk_finalizer_probe_rows_by_candidate_id,
    )

    probe_by_id = risk_finalizer_probe_rows_by_candidate_id(
        [
            {
                "candidate_id": "candidate-a",
                "rank": 2,
                "selected": False,
                "risk_decision": "zero_trade",
                "risk_decision_reason": "package_marketable_limit_entry_guard_blocked",
                "scheduler_action_class": "enter",
                "scheduler_score": 7.25,
                "expected_net_r": 0.91,
                "candidate_expected_net_r": 0.91,
                "probability": 0.83,
                "candidate_probability": 0.83,
                "fill_probability": 0.76,
                "source_completeness": 1.0,
                "source_completeness_status": "source_completeness_present",
                "selector_action": "trade",
                "selector_reason": "package_positive",
                "framework": "origin_structural_distance_extreme",
                "current_framework": "origin_structural_distance_extreme",
                "origin_family": "structural_distance_extreme",
                "candidate_origin_family": "origin_structural_distance_extreme",
                "route_family": "scheduler_lifecycle_merge",
                "route_session": "off_configured_session",
                "session": "moonshot_h00_01",
                "setup_family": "source_bound_router_refusal",
                "dynamic_geometry_policy": "momentum_exhaustion",
                "source_bound_signal_r": 123.45,
                "source_bound_package_candidate_use_allowed": True,
                "ultimate_package_source_bound_candidate_use_allowed": True,
                "package_replay_candidate_use_allowed": True,
                "package_replay_executable_candidate_use_allowed": True,
                "ultimate_package_admission_candidate_use_allowed": True,
                "ultimate_package_admission_sleeve_match_count": 2,
                "ultimate_package_matched_sleeve_count": 4,
                "ultimate_package_role_disposition": "admission_candidate",
                "ultimate_package_effective_source_bound_candidate_use_allowed": True,
                "ultimate_package_effective_admission_count": 2,
                "ultimate_package_effective_matched_count": 4,
                "ultimate_package_effective_source_bound_signal_r": 123.45,
                "final_approved_risk_pct": 0.0,
                "pretrade_cost_refusal_reasons": ["cost_floor"],
            }
        ]
    )

    fields = risk_finalizer_missed_opportunity_attribution_fields(
        candidate_id="candidate-a",
        probe_by_candidate_id=probe_by_id,
        original_selected_id_set={"candidate-a"},
    )

    assert fields["risk_finalizer_candidate_probed"] is True
    assert fields["risk_finalizer_preselected_candidate"] is True
    assert fields["risk_finalizer_probe_status"] == "materialized"
    assert fields["risk_finalizer_reason"] == "package_marketable_limit_entry_guard_blocked"
    assert fields["risk_finalizer_expected_net_r"] == 0.91
    assert fields["risk_finalizer_probability"] == 0.83
    assert fields["risk_finalizer_fill_probability"] == 0.76
    assert fields["risk_finalizer_source_completeness"] == 1.0
    assert fields["risk_finalizer_selector_action"] == "trade"
    assert fields["risk_finalizer_selector_reason"] == "package_positive"
    assert fields["framework"] == "origin_structural_distance_extreme"
    assert fields["risk_finalizer_framework"] == "origin_structural_distance_extreme"
    assert fields["risk_finalizer_route_session"] == "off_configured_session"
    assert fields["risk_finalizer_setup_family"] == "source_bound_router_refusal"
    assert fields["risk_finalizer_dynamic_geometry_policy"] == "momentum_exhaustion"
    assert fields["risk_finalizer_source_bound_signal_r"] == 123.45
    assert (
        fields["risk_finalizer_source_bound_package_candidate_use_allowed"] is True
    )
    assert fields["risk_finalizer_package_replay_candidate_use_allowed"] is True
    assert (
        fields[
            "risk_finalizer_ultimate_package_effective_source_bound_signal_r"
        ]
        == 123.45
    )
    assert fields["risk_finalizer_final_approved_risk_pct"] == 0.0
    assert fields["risk_finalizer_pretrade_cost_refusal_reasons"] == ["cost_floor"]


def test_parity_builder_route_provenance_prefers_probe_fields_and_aliases():
    builder = load_parity_builder()

    fields = builder.route_provenance_fields(
        {
            "candidate_framework": "origin_structural_distance_extreme",
            "risk_finalizer_origin_family": "structural_distance_extreme",
            "route_session": "off_configured_session",
            "risk_finalizer_dynamic_geometry_policy": "momentum_exhaustion",
        }
    )

    assert fields["framework"] == "origin_structural_distance_extreme"
    assert fields["current_framework"] == "origin_structural_distance_extreme"
    assert fields["origin_family"] == "structural_distance_extreme"
    assert fields["route_session"] == "off_configured_session"
    assert fields["session_bucket"] == "off_configured_session"
    assert fields["session"] == "off_configured_session"
    assert fields["dynamic_geometry_policy"] == "momentum_exhaustion"


def test_parity_builder_route_provenance_accepts_finalizer_primary_probe_aliases():
    builder = load_parity_builder()

    fields = builder.route_provenance_fields(
        {
            "finalizer_primary_probe_framework": "origin_fvg_fill",
            "finalizer_primary_probe_current_framework": "fvg_fill",
            "finalizer_primary_probe_origin_family": "fvg_fill",
            "finalizer_primary_probe_candidate_origin_family": "origin_fvg_fill",
            "finalizer_primary_probe_route_family": "scheduler_lifecycle_merge",
            "finalizer_primary_probe_route_session": "off_configured_session",
            "finalizer_primary_probe_session": "moonshot_h08_09",
            "finalizer_primary_probe_session_bucket": "moonshot_h08_09",
            "finalizer_primary_probe_setup_family": "source_bound_router_refusal",
            "finalizer_primary_probe_dynamic_geometry_policy": "momentum_exhaustion",
        }
    )

    assert fields == {
        "framework": "origin_fvg_fill",
        "current_framework": "fvg_fill",
        "origin_family": "fvg_fill",
        "candidate_origin_family": "origin_fvg_fill",
        "route_family": "scheduler_lifecycle_merge",
        "route_session": "off_configured_session",
        "session": "moonshot_h08_09",
        "session_bucket": "moonshot_h08_09",
        "setup_family": "source_bound_router_refusal",
        "dynamic_geometry_policy": "momentum_exhaustion",
    }


def test_parity_signed_router_refusal_authority_requires_strong_quality_floors():
    builder = load_parity_builder()
    reason = (
        "ultimate_candidate_package_positive_predecision_router_refusal_"
        "open_reduced_risk"
    )
    row = _signed_parity_router_refusal_row(reason)
    payload = dict(row["package_new_entry_authority_payload"])
    payload["expected_net_r"] = 0.91
    digest = package_new_entry_authority_payload_hash_sha256(payload)
    row.update(
        {
            "expected_net_r": 0.91,
            "candidate_expected_net_r": 0.91,
            "package_new_entry_authority_payload": payload,
            "package_new_entry_authority_hash_sha256": digest,
            "expected_package_new_entry_authority_hash_sha256": digest,
            "package_new_entry_authority_expected_net_r": 0.91,
        }
    )
    nested = dict(row["ultimate_candidate_package_open_reduced_risk_authority"])
    nested.update(
        {
            "package_new_entry_authority_payload": dict(payload),
            "package_new_entry_authority_hash_sha256": digest,
            "expected_package_new_entry_authority_hash_sha256": digest,
            "package_new_entry_authority_expected_net_r": 0.91,
        }
    )
    row["ultimate_candidate_package_open_reduced_risk_authority"] = nested

    assert (
        builder.signed_package_new_entry_authority_block_reason(
            row,
            action_intent="new_position",
        )
        == "router_refusal_expected_net_r_below_floor"
    )


def test_scheduler_action_intent_uses_lifecycle_packet_aliases():
    from src.research_infra.v4_timewarp_simulated_live_research_loop import (
        scheduler_action_intent_from_lifecycle,
    )

    action = scheduler_action_intent_from_lifecycle(
        {},
        {"lifecycle_packet": {"action": "scale_in"}},
    )

    assert action == "same_direction_scale_in"


def test_selector_open_reduced_risk_materializes_reduced_sized_new_entry_action():
    from src.research_infra.v4_timewarp_simulated_live_research_loop import (
        selector_action_allows_scheduler_action,
        selector_reduce_risk_action_has_positive_sizing,
        selector_reduce_risk_new_entry_block_reason,
    )

    assert selector_action_allows_scheduler_action("trade", "new_position") is True
    assert selector_action_allows_scheduler_action("reduce-risk", "new_position") is False
    assert selector_action_allows_scheduler_action("reduce-risk", "scale_in") is False
    assert selector_action_allows_scheduler_action("open-reduced-risk", "new_position") is True
    assert selector_action_allows_scheduler_action("open-reduced-risk", "scale_in") is True
    assert selector_action_allows_scheduler_action("reduce-risk", "reduce_existing") is True
    assert selector_action_allows_scheduler_action("reduce-risk", "replace_pending") is True
    assert (
        selector_reduce_risk_action_has_positive_sizing(
            {"final_risk_pct": 0.5},
            "new_position",
        )
        is True
    )
    assert (
        selector_reduce_risk_new_entry_block_reason(
            {
                "final_risk_pct": 0.5,
                "reason": "numeric_confluence_structured_disagreement",
            },
            "new_position",
        )
        == (
            "selector_reduce_risk_new_entry_blocked:"
            "numeric_confluence_structured_disagreement"
        )
    )
    assert (
        selector_reduce_risk_new_entry_block_reason(
            {
                "final_risk_pct": 0.5,
                "reason": "calibrated_admission_fill_probability_below_generalized_floor",
            },
            "new_position",
        )
        == (
            "selector_reduce_risk_new_entry_blocked:"
            "calibrated_admission_fill_probability_below_generalized_floor"
        )
    )
    assert (
        selector_reduce_risk_new_entry_block_reason(
            {"final_risk_pct": 0.5, "reason": "broker_net_admission_ev_below_full_trade_floor"},
            "new_position",
        )
        is None
    )
    assert (
        selector_reduce_risk_action_has_positive_sizing(
            {"final_risk_pct": 0.0},
            "new_position",
        )
        is False
    )
    assert (
        selector_reduce_risk_action_has_positive_sizing(
            {},
            "reduce_existing",
        )
        is True
    )
    assert selector_reduce_risk_new_entry_block_reason({}, "reduce_existing") is None


def test_allocator_candidate_reads_gtos_lifecycle_action_fields():
    from src.research.moonshot_scheduler_v4_best_trade_allocator import AllocatorCandidate

    direct = AllocatorCandidate.from_mapping(
        {
            "candidate_id": "direct-action",
            "symbol": "XAUUSD",
            "side": "LONG",
            "gtos_vnext_same_symbol_lifecycle_action": "scale_in",
        }
    )
    compact_packet = AllocatorCandidate.from_mapping(
        {
            "candidate_id": "packet-action",
            "symbol": "XAUUSD",
            "side": "LONG",
            "lifecycle_packet": {"scalar_fields": {"action": "close"}},
        }
    )

    assert direct.action_intent == "same_direction_scale_in"
    assert compact_packet.action_intent == "close_existing"


def test_selected_package_bridge_full_package_scope_and_bounded_smoke_tag():
    bridge = load_selected_package_replay_bridge()
    labels = [
        {
            "symbol": "XAUUSD",
            "decision_time_utc": "2026-05-13T08:00:00Z",
        }
    ]

    scoped = bridge.install_lifecycle_label_replay_scope(
        labels,
        decision_time_source="lifecycle-labels",
        symbol_scope="lifecycle-labels",
        replay_days=("2026-05-13",),
    )
    assert scoped["symbol_scope"] == "lifecycle-labels"
    assert scoped["bounded_smoke"] is True
    assert scoped["scoped_symbols"] == ["XAUUSD"]

    full = bridge.install_lifecycle_label_replay_scope(
        labels,
        decision_time_source="lifecycle-labels",
        symbol_scope="all",
        replay_days=("2026-05-13",),
    )
    assert full["requested_symbol_scope"] == "all"
    assert full["symbol_scope"] == "full-package"
    assert full["bounded_smoke"] is False
    assert tuple(full["scoped_symbols"]) == bridge.FULL_PACKAGE_SYMBOLS


def test_broad_replay_comparator_filters_to_summary_window_and_splits(tmp_path, monkeypatch):
    comparator = load_broad_replay_comparator()
    monkeypatch.setattr(comparator, "ROUTE", tmp_path)

    for prefix in ("BASE", "CAND"):
        (tmp_path / f"{prefix}_SUMMARY.json").write_text(
            json.dumps(
                {
                    "date_start": "2026-05-13",
                    "date_end": "2026-05-13",
                    "split_profile_stats": [
                        {
                            "trade_rows": 1,
                            "net_r": 0.0,
                            "gross_r": 0.0,
                            "final_r": 0.0,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    builder = load_parity_builder()
    builder.write_jsonl(
        tmp_path / "BASE_TRADE_LEDGER.jsonl",
        [
            {
                "candidate_id": "base-in-window",
                "decision_time_utc": "2026-05-13T08:00:00Z",
                "net_r": -1.0,
                "gross_r": -0.9,
                "final_r": -0.9,
                "risk_expression_ladder_tier": "reduced",
                "risk_expression_ladder_tier_causes": ["headroom_reduced"],
                "fill_realism_class": "realism_passed",
            },
            {
                "candidate_id": "base-outside-window",
                "decision_time_utc": "2026-05-14T08:00:00Z",
                "net_r": 10.0,
                "risk_expression_ladder_tier": "full",
                "fill_realism_class": "first_touch_optimistic",
            },
        ],
    )
    builder.write_jsonl(
        tmp_path / "CAND_TRADE_LEDGER.jsonl",
        [
            {
                "candidate_id": "cand-in-window",
                "decision_time_utc": "2026-05-13T08:00:00Z",
                "net_r": 1.5,
                "gross_r": 1.7,
                "final_r": 1.7,
                "risk_expression_ladder_tier": "full",
                "risk_expression_ladder": {
                    "tier_causes": ["all_signing_conditions_passed"]
                },
                "fill_realism_class": "m15_proxy",
            },
            {
                "candidate_id": "cand-outside-window",
                "decision_time_utc": "2026-05-12T08:00:00Z",
                "net_r": -10.0,
                "risk_expression_ladder_tier": "reduced",
                "fill_realism_class": "first_touch_optimistic",
            },
        ],
    )

    result = comparator.compare("BASE", "CAND")

    assert result["trade_key_counts"]["baseline_outside_summary_window"] == 1
    assert result["trade_key_counts"]["candidate_outside_summary_window"] == 1
    assert result["baseline_trade_window_rollup"]["reduced_risk_count"] == 1
    assert result["candidate_trade_window_rollup"]["full_risk_count"] == 1
    assert result["candidate_trade_window_rollup"]["fill_realism_class_counts"] == {
        "m15_proxy": 1
    }
    assert result["candidate_trade_window_rollup"]["ladder_cause_histogram"] == {
        "all_signing_conditions_passed": 1
    }


def _current_authority_fields(
    *,
    candidate_id: str,
    decision_time_utc: str,
    order_allowed: bool,
    selector_action: str = "open-reduced-risk",
    selector_reason: str = "unit_test_authority",
) -> dict:
    instance_key = f"{candidate_id}@@{decision_time_utc}"
    matched_member_axis_ids = ["member_axis:unit-test-authority"]
    source_boundary = (
        "predecision_package_open_reduced_new_entry_authority_no_outcome_fields"
    )
    quality_boundary = (
        "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
    )
    quality_sources = {
        "expected_net_r": "candidate_decision_inputs.expected_net_r",
        "probability": "candidate_decision_inputs.probability",
        "fill_probability": "candidate_decision_inputs.fill_probability",
        "source_completeness": "candidate_decision_inputs.source_completeness",
    }
    payload = {
        "payload_schema": PACKAGE_NEW_ENTRY_AUTHORITY_PAYLOAD_SCHEMA,
        "payload_contract": PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT,
        "scope": "selector_reduced_risk_to_scheduler_new_position",
        "target_action_intent": "new_position",
        "uses_outcome_fields": False,
        "candidate_id": candidate_id,
        "candidate_id_source": "candidate_id",
        "decision_time_utc": decision_time_utc,
        "canonical_replay_candidate_instance_key": instance_key,
        "source_bound_replay_candidate_instance_key": instance_key,
        "candidate_instance_identity_status": "materialized",
        "matched_member_axis_ids": matched_member_axis_ids,
        "selector_action": selector_action,
        "selector_reason": selector_reason,
        "authority_applies": True,
        "authority_allowed": True,
        "authority_family": "unit_test_authority",
        "authority_source": "unit_test_predecision_authority",
        "source_boundary": source_boundary,
        "source_bound_package_candidate_use_allowed": True,
        "pretrade_cost_packet_status": "PASSED",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "cost_authority": "broker_calibrated_replay_cost",
        "candidate_cost_r_fallback_is_authority": False,
        "expected_net_r": 0.75,
        "expected_net_r_semantics": LEGACY_UNTYPED_EXPECTED_VALUE,
        "expected_net_r_semantics_source": (
            LEGACY_UNTYPED_EXPECTED_VALUE_SOURCE
        ),
        "probability": 0.7,
        "fill_probability": 0.8,
        "execution_fill_probability": 0.8,
        "execution_fill_probability_source": "predecision_limit_fillability",
        "execution_fill_probability_source_time_utc": (
            "2026-05-13T08:00:00+00:00"
        ),
        "execution_fill_probability_source_boundary": (
            "asof_candidate_fields_only_no_postdecision_path"
        ),
        "execution_fill_probability_authority_class": (
            "signed_predecision_execution_fillability_authority"
        ),
        "entry_quality_fill_probability": 0.8,
        "limit_fillability_probability": 0.8,
        "predecision_limit_fillability_probability": 0.8,
        "source_completeness": 1.0,
        "source_completeness_status": "complete",
        "candidate_decision_quality_field_sources": quality_sources,
        "candidate_decision_quality_source_boundary": quality_boundary,
        "candidate_decision_quality_alias_status": "exact_materialized",
        "candidate_decision_quality_alias_mismatches": [],
        "candidate_decision_quality_provenance_failures": [],
        "selected_policy_for_expected_net_r": "not_required_no_selected_policy",
        "selected_policy_expected_net_calibration_status": (
            "not_required_no_selected_policy"
        ),
        "selected_policy_expected_net_calibrated": False,
        "selected_policy_expected_net_calibration_required": False,
        "selected_policy_expected_net_calibration_source": "",
        "selected_policy_expected_net_calibration_source_boundary": "",
        "selected_policy_expected_net_calibration_hash": "",
        "package_replay_order_executable_candidate_use_allowed": order_allowed,
        "package_replay_order_executable_candidate_use_allowed_reason": (
            "unit_test_order_allowed"
            if order_allowed
            else "unit_test_order_blocked"
        ),
        "package_replay_order_executable_authority_source": (
            "unit_test_predecision_authority"
        ),
    }
    digest = package_new_entry_authority_payload_hash_sha256(payload)
    fields = {
        "matched_member_axis_ids": matched_member_axis_ids,
        "ultimate_package_matched_member_axis_ids": matched_member_axis_ids,
        "package_new_entry_authority_required": True,
        "package_new_entry_authority_valid": True,
        "package_new_entry_authority_status": (
            "valid_signed_predecision_new_entry_authority"
        ),
        "package_new_entry_authority_failures": [],
        "package_new_entry_authority_hash_sha256": digest,
        "expected_package_new_entry_authority_hash_sha256": digest,
        "package_new_entry_authority_payload_contract": (
            PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT
        ),
        "package_new_entry_authority_payload": payload,
        "package_new_entry_authority_authority_field": (
            "ultimate_candidate_package_open_reduced_risk_authority"
        ),
        "package_new_entry_authority_authority_family": "unit_test_authority",
    }
    for field, value in payload.items():
        fields[f"package_new_entry_authority_{field}"] = value
    authority_field = "ultimate_candidate_package_open_reduced_risk_authority"
    fields[authority_field] = {
        **fields,
        "allowed": True,
        "applies": True,
        "authority_family": "unit_test_authority",
        "authority_source": "unit_test_predecision_authority",
        "source_boundary": source_boundary,
    }
    return fields


def _projection_candidate(*, order_allowed: bool) -> dict:
    candidate_id = "projection-envelope-candidate"
    decision_time = "2026-05-13T08:30:00+00:00"
    quality_sources = {
        "expected_net_r": "candidate_decision_inputs.expected_net_r",
        "probability": "candidate_decision_inputs.probability",
        "source_completeness": "candidate_decision_inputs.source_completeness",
    }
    return {
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "canonical_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "source_bound_replay_candidate_instance_key": f"{candidate_id}@@{decision_time}",
        "candidate_instance_identity_status": "materialized",
        "selector_action": "open-reduced-risk",
        "scheduler_materialization_action_intent": "new_position",
        "candidate_decision_quality": {
            "expected_net_r": 0.75,
            "probability": 0.7,
            "source_completeness": 1.0,
            "field_sources": quality_sources,
            "source_boundary": (
                "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
            ),
        },
        "candidate_decision_quality_field_sources": quality_sources,
        "candidate_decision_quality_source_boundary": (
            "predecision_packet_selector_event_and_candidate_feature_signal_no_outcome_fields"
        ),
        **_current_authority_fields(
            candidate_id=candidate_id,
            decision_time_utc=decision_time,
            order_allowed=order_allowed,
        ),
    }


def test_projection_validity_and_permission_use_one_recorded_envelope() -> None:
    builder = load_parity_builder()
    candidate = _projection_candidate(order_allowed=True)
    order = {
        **candidate,
        "package_replay_order_executable_transfer_status": "order_bound",
        "package_replay_order_executable_bound_order_id": "order-envelope",
        "simulated_order_id": "order-envelope",
        "order_status": "pending_accepted",
    }
    enrich = {
        "order_present": True,
        "order_binding": builder.projection_stage_binding(order, stage="order"),
    }

    projection = builder.candidate_instance_projection(
        candidate=candidate,
        enrich=enrich,
        package_candidate=None,
        generated="2026-07-10T00:00:00Z",
    )

    assert projection["package_authority_projection_valid"] is True
    assert projection["package_order_executable_allowed"] is True
    assert projection["package_authority_envelope_source_stage"] == "order"
    assert projection["package_authority_projection_permission_same_envelope"] is True
    assert projection["package_authority_envelope_digest_sha256"] == (
        projection["package_order_executable_permission_envelope_digest_sha256"]
    )


def test_projection_authority_payload_requires_signed_fillability_class() -> None:
    builder = load_parity_builder()
    payload = dict(
        _projection_candidate(order_allowed=True)[
            "package_new_entry_authority_payload"
        ]
    )
    payload.pop("execution_fill_probability_authority_class")

    assert (
        "package_new_entry_authority_payload_atom_missing:fill:"
        "execution_fill_probability_authority_class"
        in builder.package_new_entry_authority_payload_atom_reasons(payload)
    )


def test_projection_rejects_stage_by_stage_authority_envelope_mixing() -> None:
    builder = load_parity_builder()
    candidate = _projection_candidate(order_allowed=False)
    order = {
        **_projection_candidate(order_allowed=True),
        "package_replay_order_executable_transfer_status": "order_bound",
        "package_replay_order_executable_bound_order_id": "order-mixed-envelope",
        "simulated_order_id": "order-mixed-envelope",
        "order_status": "pending_accepted",
    }
    enrich = {
        "order_present": True,
        "order_binding": builder.projection_stage_binding(order, stage="order"),
    }

    projection = builder.candidate_instance_projection(
        candidate=candidate,
        enrich=enrich,
        package_candidate=None,
        generated="2026-07-10T00:00:00Z",
    )

    assert projection["package_authority_projection_valid"] is False
    assert projection["package_order_executable_allowed"] is False
    assert projection["package_authority_envelope_status"] == (
        "cross_stage_authority_envelope_mismatch"
    )
    assert projection["package_authority_projection_permission_same_envelope"] is False
