from __future__ import annotations

import json
from pathlib import Path

from src.research_infra.gtos_vnext_evidence_system import (
    EvidenceSourceSpec,
    build_evidence_matrix,
    build_instruction_coverage_rows,
    build_runtime_architecture_ledger,
    find_safety_issues,
    rows_for_target,
    summarize_exact_proxy_expectancy,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _spec(path: Path, name: str, targets: tuple[str, ...]) -> EvidenceSourceSpec:
    return EvidenceSourceSpec(
        source_name=name,
        evidence_family=f"{name}_family",
        source_role=f"{name}_role",
        path=path,
        system_surface=f"{name}_surface",
        implementation_action=f"{name}_action",
        ledger_targets=targets,
        row_id_fields=("row_id",),
    )


def test_build_evidence_matrix_preserves_input_lines_and_hashes(tmp_path: Path) -> None:
    source_a = Path("source_a.jsonl")
    source_b = Path("nested/source_b.jsonl")
    _write_jsonl(
        tmp_path / source_a,
        [
            {"row_id": "a1", "symbol": "XAUUSD", "cost_adjusted_simulated_r": {"count": 2, "sum": 1.5}},
            {"row_id": "a2", "source_row": {"symbol": "USDJPY", "registry_surface_score": 0.15}},
        ],
    )
    _write_jsonl(tmp_path / source_b, [{"row_id": "b1", "target_effective_n": 9, "live_effect": False}])

    matrix_rows, inventory_rows = build_evidence_matrix(
        tmp_path,
        source_specs=(
            _spec(source_a, "source_a", ("scorer_filter_router", "exact_proxy_r")),
            _spec(source_b, "source_b", ("ai_decision_architecture",)),
        ),
    )

    assert len(matrix_rows) == 3
    assert sum(row["source_rows"] for row in inventory_rows) == 3
    assert [row["source_line_no"] for row in matrix_rows] == [1, 2, 1]
    assert {row["source_row_id"] for row in matrix_rows} == {"a1", "a2", "b1"}
    assert all(row["source_artifact_sha256"] for row in matrix_rows)
    assert all(row["source_row_payload_sha256"] for row in matrix_rows)
    assert all(row["candidate_use_allowed_now"] is False for row in matrix_rows)
    assert matrix_rows[0]["r_metrics"]["cost_adjusted_simulated_r"]["sum"] == 1.5
    assert matrix_rows[1]["r_metrics"]["proxy_score"]["sum"] == 0.15
    assert matrix_rows[2]["r_metrics"]["effective_n"]["sum"] == 9


def test_ledger_splits_and_architecture_preserve_counts(tmp_path: Path) -> None:
    source = Path("rows.jsonl")
    _write_jsonl(
        tmp_path / source,
        [
            {"row_id": "r1", "symbol": "XAUUSD"},
            {"row_id": "r2", "symbol": "XAGUSD"},
        ],
    )
    matrix_rows, inventory_rows = build_evidence_matrix(
        tmp_path,
        source_specs=(_spec(source, "rows", ("scorer_filter_router", "market_timeframe_expansion")),),
    )

    assert len(rows_for_target(matrix_rows, "scorer_filter_router")) == 2
    assert len(rows_for_target(matrix_rows, "market_timeframe_expansion")) == 2

    architecture = build_runtime_architecture_ledger(matrix_rows, inventory_rows)
    assert architecture == [
        {
            "schema_version": "gtos_vnext_evidence_system_v1",
            "row_type": "gtos_vnext_runtime_architecture_decision",
            "runtime_architecture_row_id": architecture[0]["runtime_architecture_row_id"],
            "source_name": "rows",
            "evidence_family": "rows_family",
            "source_artifact": "rows.jsonl",
            "source_artifact_sha256": architecture[0]["source_artifact_sha256"],
            "source_rows_preserved": 2,
            "source_rows_expected": 2,
            "all_source_rows_preserved": True,
            "runtime_architecture_decision": "DEFAULT_OFF_LEDGERED_SYSTEM_SURFACE_NO_RUNTIME_ENABLEMENT",
            "candidate_use_allowed_now": False,
            "runtime_candidate_use_permitted": False,
            "runtime_score_allowed": False,
            "runtime_effect_now": False,
            "paid_api_or_vendor_call": False,
            "broker_operation": False,
            "system_surface_counts": {"rows_surface": 2},
            "implementation_action_counts": {"rows_action": 2},
        }
    ]


def test_exact_proxy_summary_aggregates_dict_scalar_and_proxy_rows(tmp_path: Path) -> None:
    source = Path("metrics.jsonl")
    _write_jsonl(
        tmp_path / source,
        [
            {"row_id": "m1", "cost_adjusted_simulated_r": {"count": 3, "sum": 2.25}, "effective_n": {"sum": 11}},
            {"row_id": "m2", "average_selected_intrabar_cost_adjusted_simulated_r": 1.25},
            {"row_id": "m3", "source_row": {"avoid_comparator_score": -0.4, "proxy_r_class": "STRONG_NEGATIVE_PROXY_R"}},
        ],
    )
    matrix_rows, _ = build_evidence_matrix(
        tmp_path,
        source_specs=(_spec(source, "metrics", ("exact_proxy_r",)),),
    )

    summary = summarize_exact_proxy_expectancy(matrix_rows)

    assert summary["overall"]["source_rows"] == 3
    assert summary["overall"]["simulated_r_rows"] == 2
    assert summary["overall"]["proxy_r_rows"] == 1
    assert summary["overall"]["cost_adjusted_simulated_r_sum"] == 3.5
    assert summary["overall"]["effective_n_sum"] == 11.0
    assert summary["overall"]["proxy_score_sum"] == -0.4


def test_instruction_coverage_and_safety_validator_flag_runtime_enablement(tmp_path: Path) -> None:
    source = Path("unsafe.jsonl")
    _write_jsonl(tmp_path / source, [{"row_id": "bad", "live_effect": True}])
    matrix_rows, inventory_rows = build_evidence_matrix(
        tmp_path,
        source_specs=(_spec(source, "unsafe", ("scorer_filter_router",)),),
    )

    issues = find_safety_issues(matrix_rows)
    coverage = build_instruction_coverage_rows(matrix_rows, inventory_rows)

    assert issues == [f"forbidden_true_field:{matrix_rows[0]['vnext_matrix_row_id']}:runtime_effect_now"]
    default_off_check = [row for row in coverage if row["instruction"] == "default_off_no_runtime_enablement"][0]
    assert default_off_check["coverage_status"] == "FAIL"
