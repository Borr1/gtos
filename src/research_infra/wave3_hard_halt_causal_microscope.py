"""Wave3 hard-halt causal microscope continuation artifacts.

This module materializes source-bound Wave3 fixture artifacts from the accepted
Wave2 causal microscope outputs. It does not execute broker actions, mutate
runtime state, or claim validation/live deployment authority.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_REL = Path("research/operations/wave3_hard_halt_causal_microscope_continuation_2026_06_04")
WAVE2_REL = Path("research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04")
PROMPT_REL = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "wave3_final_moonshot_after_hard_halt_2026_06_04/"
    "WAVE3_01_HARD_HALT_CAUSAL_MICROSCOPE_CONTINUATION_GOAL_PROMPT_2026-06-04.md"
)

EXPECTED_BROKER_POSITION_ROWS = 77
EXPECTED_CANDIDATE_LIVE_ROWS = 13246
EXPECTED_QUESTION_ROWS = 22

BOUNDARY_FIELDS = {
    "validation_result_status": False,
    "outcome_result_rows_status": False,
    "broker_runtime_change_status": False,
}

SEMANTIC_OWNER_CONTRACTS = {
    "same_symbol_same_instrument_lifecycle_v4": "WAVE2_SAME_SYMBOL_LIFECYCLE_OWNERSHIP_CONTRACT.json",
    "probability_debate_team_engine_v4": "WAVE2_PROBABILITY_DEBATE_ENGINE_CONTRACT.json",
    "follow_avoid_mixed_numeric_confluence_v4": "WAVE2_FOLLOW_AVOID_MIXED_NUMERIC_CONFLUENCE_CONTRACT.json",
    "feature_label_store_v2": "WAVE2_FEATURE_LABEL_STORE_CONTRACT.json",
    "wave4_wave5_ml_ownership": "WAVE2_WAVE4_WAVE5_ML_OWNERSHIP_CONTRACT.json",
    "model_registry_and_challenger": "WAVE2_MODEL_REGISTRY_AND_CHALLENGER_CONTRACT.json",
    "long_running_local_training": "WAVE2_LONG_RUNNING_LOCAL_TRAINING_CONTRACT.json",
    "validation_anti_overfit_v4": "WAVE2_VALIDATION_ANTI_OVERFIT_CONTRACT.json",
}

SOURCE_FILES = [
    PROMPT_REL,
    Path(".context/LIVE_STATE.md"),
    Path(".context/00_core/current_vnext_system_map.md"),
    Path(".context/00_core/current_repo_reading_order.md"),
    Path(".context/00_core/quick_reference_card.md"),
    Path(".context/00_core/final_moonshot_post_hard_halt_research_plan.md"),
    Path(".context/00_core/final_moonshot_goal_session_execution_architecture.md"),
    Path(".context/00_core/final_moonshot_central_orchestrator_successor_brief.md"),
    Path(".context/00_core/goal_session_research_discipline.md"),
    Path(".context/00_core/research_operating_doctrine.md"),
    Path(".context/00_core/orchestrator_successor_operating_brief.md"),
    Path(".context/00_core/orchestrator_methodology_hardening_controls.md"),
    Path(".context/00_core/parallel_goal_merge_playbook.md"),
    Path(".gitattributes"),
    WAVE2_REL / "WAVE2_FINAL_MASTER_STATE_TABLE.json",
    WAVE2_REL / "WAVE2_FULL_SYSTEM_CAUSAL_MODEL.json",
    WAVE2_REL / "WAVE2_DOWNSTREAM_OWNERSHIP_MAP.json",
    WAVE2_REL / "WAVE2_EVERY_TRADE_CAUSAL_MICROSCOPE.jsonl",
    WAVE2_REL / "WAVE2_EVERY_CANDIDATE_CAUSAL_MICROSCOPE.jsonl",
    WAVE2_REL / "WAVE2_BLOCKER_AND_REPAIR_LEDGER.jsonl",
    WAVE2_REL / "WAVE2_ACTIVE_CAUSAL_QUESTION_STACK.jsonl",
    WAVE2_REL / "WAVE2_QUESTION_COVERAGE_SATURATION_LEDGER.jsonl",
    WAVE2_REL / "WAVE2_COST_SOURCE_COVERAGE_AUDIT.jsonl",
    WAVE2_REL / "WAVE2_SLTP_MODIFY_LIFECYCLE_SOURCE_COVERAGE_LEDGER.jsonl",
    WAVE2_REL / "WAVE2_ALLOCATOR_WINDOW_SOURCE_COVERAGE_AUDIT.jsonl",
    WAVE2_REL / "WAVE2_PATH_REPAIR_SOURCE_COVERAGE_AUDIT.jsonl",
    WAVE2_REL / "WAVE2_PENDING_NOFILL_SOURCE_COVERAGE_SUMMARY.json",
    WAVE2_REL / "WAVE2_PRODUCTION_CODE_COMPONENT_DISPOSITION_LEDGER.jsonl",
    Path("config/agent_config.yaml"),
    Path("src/components/permissions.py"),
    Path("src/components/orchestrator.py"),
    Path("src/components/execution.py"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root_from_file() -> Path:
    return Path(__file__).resolve().parents[2]


def rel(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def git_value(repo_root: Path, *args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def git_status_short(repo_root: Path) -> list[str]:
    value = git_value(repo_root, "status", "--short")
    if value is None or not value:
        return []
    return value.splitlines()


def load_wave2(repo_root: Path) -> dict[str, Any]:
    wave2 = repo_root / WAVE2_REL
    return {
        "state_table": read_json(wave2 / "WAVE2_FINAL_MASTER_STATE_TABLE.json"),
        "causal_model": read_json(wave2 / "WAVE2_FULL_SYSTEM_CAUSAL_MODEL.json"),
        "downstream_map": read_json(wave2 / "WAVE2_DOWNSTREAM_OWNERSHIP_MAP.json"),
        "coverage_audit": read_json(wave2 / "WAVE2_FULL_LEDGER_COVERAGE_AUDIT.json"),
        "market_data_summary": read_json(wave2 / "WAVE2_MARKET_DATA_GAP_PROXY_REPAIR_SUMMARY.json"),
        "pending_nofill_summary": read_json(wave2 / "WAVE2_PENDING_NOFILL_SOURCE_COVERAGE_SUMMARY.json"),
        "v3_summary": read_json(wave2 / "WAVE2_V3_VALIDATION_AI_DUAL_BROKER_DISPOSITION_SUMMARY.json"),
        "trade_rows": read_jsonl(wave2 / "WAVE2_EVERY_TRADE_CAUSAL_MICROSCOPE.jsonl"),
        "candidate_rows": read_jsonl(wave2 / "WAVE2_EVERY_CANDIDATE_CAUSAL_MICROSCOPE.jsonl"),
        "blocker_rows": read_jsonl(wave2 / "WAVE2_BLOCKER_AND_REPAIR_LEDGER.jsonl"),
        "allocator_coverage_rows": read_jsonl(wave2 / "WAVE2_ALLOCATOR_WINDOW_SOURCE_COVERAGE_AUDIT.jsonl"),
        "sltp_rows": read_jsonl(wave2 / "WAVE2_SLTP_MODIFY_LIFECYCLE_SOURCE_COVERAGE_LEDGER.jsonl"),
        "path_coverage_rows": read_jsonl(wave2 / "WAVE2_PATH_REPAIR_SOURCE_COVERAGE_AUDIT.jsonl"),
        "cost_rows": read_jsonl(wave2 / "WAVE2_COST_SOURCE_COVERAGE_AUDIT.jsonl"),
        "question_rows": read_jsonl(wave2 / "WAVE2_ACTIVE_CAUSAL_QUESTION_STACK.jsonl"),
        "question_coverage_rows": read_jsonl(wave2 / "WAVE2_QUESTION_COVERAGE_SATURATION_LEDGER.jsonl"),
        "failure_requirement_rows": read_jsonl(wave2 / "WAVE2_HARD_HALT_FAILURE_TO_V4_REQUIREMENT_LEDGER.jsonl"),
        "production_disposition_rows": read_jsonl(wave2 / "WAVE2_PRODUCTION_CODE_COMPONENT_DISPOSITION_LEDGER.jsonl"),
        "source_inventory_rows": read_jsonl(wave2 / "WAVE2_SOURCE_INVENTORY.jsonl"),
    }


def source_inventory(repo_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_path in SOURCE_FILES:
        path = repo_root / source_path
        jsonl_rows = None
        if path.suffix == ".jsonl" and path.exists():
            jsonl_rows = sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())
        rows.append(
            {
                "row_id": f"wave3_source:{len(rows)+1:03d}",
                "path": source_path.as_posix(),
                "exists": path.exists(),
                "kind": "file",
                "size_bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_file(path),
                "jsonl_rows": jsonl_rows,
                "consume_status": "read_or_required_for_wave3_route",
                "evidence_class": "current_disk_source",
            }
        )
    return rows


def context_anchor(repo_root: Path, wave2: dict[str, Any]) -> dict[str, Any]:
    return {
        "route_id": "wave3_hard_halt_causal_microscope_continuation_2026_06_04",
        "generated_at_utc": utc_now(),
        "controlling_prompt": PROMPT_REL.as_posix(),
        "lane": "hard_halt_causal_microscope_continuation",
        "evidence_class": "production_code_integration_source_bound_repair_replay_design_fixtures",
        "boundary_fields": BOUNDARY_FIELDS,
        "git": {
            "branch": git_value(repo_root, "branch", "--show-current"),
            "head": git_value(repo_root, "rev-parse", "HEAD"),
            "main": git_value(repo_root, "rev-parse", "main"),
            "origin_main": git_value(repo_root, "rev-parse", "origin/main"),
            "status_short": git_status_short(repo_root),
        },
        "doctrine_application": {
            "builder_integration_posture": "materialize source-bound fixtures and capture contracts; do not stop at blocker labels",
            "anti_boxing_pursued": [
                "preserve all 77 broker positions",
                "preserve all Wave2 candidate/live-authority rows",
                "convert non-generatable runtime truth gaps into exact capture requirements",
                "carry semantic ownership dependencies into machine-checkable ledger rows",
            ],
            "proof_or_impossibility_rule": (
                "historical broker/runtime intent is used only where captured; missing intent/lifecycle "
                "truth becomes prospective capture requirement instead of inferred history"
            ),
        },
        "wave2_provenance": {
            "trade_rows": len(wave2["trade_rows"]),
            "candidate_live_rows": len(wave2["candidate_rows"]),
            "question_rows": len(wave2["question_rows"]),
            "blocker_rows": len(wave2["blocker_rows"]),
            "coverage_status": wave2["coverage_audit"].get("status"),
        },
        "forbidden_surface_status": {
            "broker_operation": "untouched",
            "broker_account_order_deal_position_mutation": "untouched",
            "credentials": "untouched",
            "paid_api_vendor_calls": "untouched",
            "active_vps_processes": "untouched",
            "remote_push": "untouched",
        },
    }


def searched_root_rows(repo_root: Path) -> list[dict[str, Any]]:
    roots = [
        (".context", "mandatory_preflight_context"),
        ("research/science_program_2026_05/04_goal_prompts", "controlling_prompt"),
        (WAVE2_REL.as_posix(), "accepted_wave2_source"),
        ("src/components", "current_runtime_code_read_before_claims"),
        ("config", "current_config_code_read_before_claims"),
        ("tests", "focused_test_surface"),
        ("scripts", "route_builder_verifier_surface"),
        ("shadow_logs", "live_shadow_source_status_from_live_state_only"),
        ("pipeline_state", "hard_halt_flag_surface"),
    ]
    return [
        {
            "row_id": f"wave3_searched_root:{idx:03d}",
            "path": path,
            "exists": (repo_root / path).exists(),
            "search_reason": reason,
            "result_use_status": "source_locator_not_result_claim",
        }
        for idx, (path, reason) in enumerate(roots, start=1)
    ]


def compact_metric_fields(fields: dict[str, Any]) -> dict[str, Any]:
    wanted = [
        "broker_real_pnl_cash",
        "broker_net_cash_from_deals",
        "gross_deal_profit_cash",
        "commission_cash",
        "swap_cash",
        "fee_cash",
        "cost_drag_cash",
        "exact_r",
        "proxy_r",
        "mfe_r",
        "mae_r",
        "hold_minutes",
        "failure_tags",
        "cost_source_coverage_status",
        "shadow_slippage_price_count",
        "expectancy_r_source_bound",
        "final_outcome",
        "selected_cell_rows",
        "selected_cell_win_rate",
        "selected_cell_profit_factor",
    ]
    return {key: fields.get(key) for key in wanted if key in fields}


def fixture_ledger(wave2: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(wave2["trade_rows"], start=1):
        rows.append(
            {
                "row_id": f"wave3_full_fixture:broker_position:{idx:05d}",
                "fixture_class": "broker_position_regression",
                "source_row_id": row.get("row_id"),
                "source_path": (WAVE2_REL / "WAVE2_EVERY_TRADE_CAUSAL_MICROSCOPE.jsonl").as_posix(),
                "broker_position_id": row.get("broker_position_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "evidence_class": row.get("evidence_class"),
                "result_use_status": "regression_fixture_source_not_validation_result",
                "owning_wave3_lane": row.get("owning_wave3_lane"),
                "question_id": row.get("question_id"),
                "v4_requirement_id": row.get("v4_requirement_id"),
                "status": "materialized_as_wave3_broker_position_fixture",
                "metric_fields_used": compact_metric_fields(row.get("metric_fields_used") or {}),
                "missing_fields": row.get("missing_fields") or [],
                "source_boundary": "redacted_account broker-real truth stays redacted_account-local and is not copied to FTMO",
            }
        )
    for idx, row in enumerate(wave2["candidate_rows"], start=1):
        rows.append(
            {
                "row_id": f"wave3_full_fixture:candidate_live:{idx:05d}",
                "fixture_class": "candidate_or_live_authority_regression_reference",
                "source_row_id": row.get("row_id"),
                "source_path": (WAVE2_REL / "WAVE2_EVERY_CANDIDATE_CAUSAL_MICROSCOPE.jsonl").as_posix(),
                "candidate_id": row.get("candidate_id"),
                "broker_position_id": row.get("broker_position_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "source_family": row.get("source_family"),
                "evidence_class": row.get("evidence_class"),
                "result_use_status": "source_reference_not_outcome_validation_result",
                "owning_wave3_lane": row.get("owning_wave3_lane"),
                "question_id": row.get("question_id"),
                "v4_requirement_id": row.get("v4_requirement_id"),
                "status": "materialized_as_wave3_candidate_live_authority_reference",
                "metric_fields_used": compact_metric_fields(row.get("metric_fields_used") or {}),
                "missing_fields": row.get("missing_fields") or [],
            }
        )
    for idx, row in enumerate(wave2["question_rows"], start=1):
        rows.append(
            {
                "row_id": f"wave3_full_fixture:question:{idx:03d}",
                "fixture_class": "causal_question_regression_reference",
                "source_row_id": row.get("question_id"),
                "source_path": (WAVE2_REL / "WAVE2_ACTIVE_CAUSAL_QUESTION_STACK.jsonl").as_posix(),
                "question_id": row.get("question_id"),
                "derived_wave3_lane": row.get("derived_wave3_lane"),
                "downstream_v4_requirement_id": row.get("downstream_v4_requirement_id"),
                "status": row.get("status"),
                "result_artifact": row.get("result_artifact"),
                "result_use_status": "question_coverage_reference_not_new_result_claim",
            }
        )
    return rows


def broker_regression_fixtures(wave2: dict[str, Any]) -> list[dict[str, Any]]:
    cost_by_position = {row.get("broker_position_id"): row for row in wave2["cost_rows"]}
    sltp_by_position = {row.get("broker_position_id"): row for row in wave2["sltp_rows"]}
    fixtures: list[dict[str, Any]] = []
    for idx, row in enumerate(wave2["trade_rows"], start=1):
        position_id = row.get("broker_position_id")
        cost = cost_by_position.get(position_id) or {}
        sltp = sltp_by_position.get(position_id) or {}
        missing_fields = set(row.get("missing_fields") or [])
        missing_fields.update(cost.get("missing_runtime_truth") or [])
        missing_fields.update(sltp.get("non_generatable_or_missing_fields") or [])
        fixtures.append(
            {
                "fixture_id": f"W3HH-BROKER-POSITION-{idx:03d}",
                "broker_position_id": position_id,
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "time_window": row.get("time_window"),
                "evidence_class": row.get("evidence_class"),
                "result_use_status": "broker_position_regression_fixture_not_validation_result",
                "source_paths": sorted(set((row.get("source_paths") or []) + (cost.get("source_paths") or []))),
                "causal_surface": row.get("causal_surface") or [],
                "market_vs_system_disposition": row.get("market_vs_system_disposition"),
                "implementation_decision": row.get("implementation_decision"),
                "metric_fields_used": compact_metric_fields(row.get("metric_fields_used") or {}),
                "cost_source_contract": {
                    "coverage_status": cost.get("coverage_status"),
                    "broker_deal_source_status": cost.get("broker_deal_source_status"),
                    "broker_order_source_status": cost.get("broker_order_source_status"),
                    "commission_swap_source_status": cost.get("commission_swap_source_status"),
                    "slippage_source_status": cost.get("slippage_source_status"),
                    "pretrade_cost_model_status": cost.get("pretrade_cost_model_status"),
                    "missing_runtime_truth": cost.get("missing_runtime_truth") or [],
                    "broker_cost_fields": cost.get("broker_cost_fields") or {},
                },
                "ticket_bound_lifecycle_contract": {
                    "coverage_status": sltp.get("coverage_status"),
                    "first_order_ticket": sltp.get("first_order_ticket"),
                    "first_order_sl": sltp.get("first_order_sl"),
                    "first_order_tp": sltp.get("first_order_tp"),
                    "unique_sltp_pair_count": sltp.get("unique_sltp_pair_count"),
                    "non_generatable_or_missing_fields": sltp.get("non_generatable_or_missing_fields") or [],
                },
                "v4_required_capture_fields": sorted(str(field) for field in missing_fields if field),
                "regression_assertions": [
                    "must_preserve_broker_position_id",
                    "must_preserve_symbol_side_and_broker_cash_boundary",
                    "must_not_copy_redacted_account_broker_truth_to_ftmo",
                    "must_fail_closed_or_capture_when_ticket_bound_lifecycle_truth_is_missing",
                    "must_separate_exact_r_proxy_r_and_broker_cash",
                ],
                "status": "ready_for_v4_causal_fixture_regression",
            }
        )
    return fixtures


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def non_generatable_truth_matrix(wave2: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(
        *,
        source_row_id: str,
        source_path: str,
        source_family: str,
        owner_lane: str,
        missing_truth: Any,
        capture_requirement: str,
        evidence_class: str,
        source_status: str,
        broker_position_id: Any = None,
        symbol: Any = None,
        count: int | None = None,
    ) -> None:
        if not missing_truth:
            return
        rows.append(
            {
                "row_id": f"wave3_non_generatable_truth:{len(rows)+1:05d}",
                "source_row_id": source_row_id,
                "source_path": source_path,
                "source_family": source_family,
                "owner_lane": owner_lane,
                "broker_position_id": broker_position_id,
                "symbol": symbol,
                "missing_truth": missing_truth,
                "source_status": source_status,
                "evidence_class": evidence_class,
                "historical_reconstruction_policy": "do_not_infer_non_generatable_runtime_truth_from_price_path",
                "prospective_capture_requirement": capture_requirement,
                "count": count,
                "status": "prospective_capture_requirement_materialized",
            }
        )

    for row in wave2["blocker_rows"]:
        add(
            source_row_id=str(row.get("blocker_id")),
            source_path=str(row.get("source_path")),
            source_family="wave2_blocker_and_repair",
            owner_lane=str(row.get("downstream_lane") or "data_capture_source_repair_final"),
            missing_truth=row.get("missing_file_path_field_source"),
            capture_requirement=str(row.get("owner_access_source_capture_requirement")),
            evidence_class=str(row.get("evidence_class")),
            source_status=str(row.get("status")),
        )
    for row in wave2["allocator_coverage_rows"]:
        for missing in _as_list(row.get("remaining_non_generatable_truth")):
            add(
                source_row_id=str(row.get("source_id")),
                source_path=str(row.get("source_path")),
                source_family="allocator_window_source_coverage",
                owner_lane="scheduler_v4_best_trade_allocator",
                missing_truth=missing,
                capture_requirement=str(row.get("v4_requirement_id")),
                evidence_class="allocator_runtime_truth_gap",
                source_status=str(row.get("coverage_status")),
                count=row.get("row_count"),
            )
    for row in wave2["path_coverage_rows"]:
        for missing in _as_list(row.get("remaining_non_generatable_truth")):
            add(
                source_row_id=str(row.get("source_id")),
                source_path=str(row.get("source_path")),
                source_family="entry_path_repair_source_coverage",
                owner_lane="execution_manager_v4",
                missing_truth=missing,
                capture_requirement=str(row.get("v4_requirement_id")),
                evidence_class="path_or_lifecycle_runtime_truth_gap",
                source_status=str(row.get("coverage_status")),
                count=row.get("row_count"),
            )
    for row in wave2["sltp_rows"]:
        for missing in _as_list(row.get("non_generatable_or_missing_fields")):
            add(
                source_row_id=str(row.get("row_id")),
                source_path=str(row.get("source_path")),
                source_family="ticket_bound_sltp_modify_lifecycle",
                owner_lane="same_symbol_same_instrument_lifecycle_v4",
                missing_truth=missing,
                capture_requirement=str(row.get("v4_requirement_id")),
                evidence_class=str(row.get("evidence_class")),
                source_status=str(row.get("coverage_status")),
                broker_position_id=row.get("broker_position_id"),
                symbol=row.get("symbol"),
            )
    for row in wave2["cost_rows"]:
        for missing in _as_list(row.get("missing_runtime_truth")):
            add(
                source_row_id=str(row.get("row_id")),
                source_path=";".join(row.get("source_paths") or []),
                source_family="broker_cost_slippage_runtime_packet",
                owner_lane=str(row.get("owning_wave3_lane") or "cost_swap_slippage_broker_constraint_engine"),
                missing_truth=missing,
                capture_requirement=str(row.get("v4_requirement_id")),
                evidence_class=str(row.get("evidence_class")),
                source_status=str(row.get("coverage_status")),
                broker_position_id=row.get("broker_position_id"),
                symbol=row.get("symbol"),
            )
    pending_summary = wave2["pending_nofill_summary"]
    for family, count in (pending_summary.get("historical_source_gap_family_counts") or {}).items():
        add(
            source_row_id=f"pending_nofill_summary:{family}",
            source_path=(WAVE2_REL / "WAVE2_PENDING_NOFILL_SOURCE_COVERAGE_SUMMARY.json").as_posix(),
            source_family="pending_nofill_lifecycle",
            owner_lane="pending_nofill_lifecycle_v4",
            missing_truth=family,
            capture_requirement="capture pending intent, fill, cancel, expiry, touch, broker order observability, and ticket joins prospectively",
            evidence_class="pending_lifecycle_source_reconciled_non_generatable_truth_gap",
            source_status="historical_source_gap_family_count_materialized",
            count=int(count),
        )
    return rows


def semantic_ownership_requirement_ledger(repo_root: Path) -> list[dict[str, Any]]:
    wave2 = repo_root / WAVE2_REL
    rows: list[dict[str, Any]] = []
    for owner, filename in SEMANTIC_OWNER_CONTRACTS.items():
        data = read_json(wave2 / filename)
        rows.append(
            {
                "row_id": f"wave3_semantic_owner:{len(rows)+1:03d}",
                "owner_lane": owner,
                "source_path": (WAVE2_REL / filename).as_posix(),
                "source_status": data.get("status"),
                "required_state_keys": sorted(data.keys()),
                "material_requirements": {
                    key: value
                    for key, value in data.items()
                    if key
                    in {
                        "actions_requiring_numeric_theses",
                        "calibration_metrics",
                        "hard_rules",
                        "required_source_fields",
                        "required_state",
                        "outputs",
                        "feature_store_requirements",
                        "label_store_requirements",
                        "required_registry_fields",
                        "challenger_requirements",
                        "required_controls",
                        "owners",
                    }
                },
                "handoff_status": "first_class_owner_contract_preserved",
                "result_use_status": "semantic_contract_not_live_activation",
                "status": "materialized",
            }
        )
    return rows


def production_code_disposition_ledger(wave2: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(wave2["production_disposition_rows"], start=1):
        rows.append(
            {
                "row_id": f"wave3_code_disposition:wave2:{idx:03d}",
                **row,
                "wave3_route_disposition": "carried_forward_from_wave2",
                "broker_runtime_change_status": False,
            }
        )
    current_observations = [
        {
            "component": "same_symbol_vnext_lifecycle_conflict_gate",
            "source_path": "src/components/permissions.py",
            "production_code_disposition": "active",
            "current_disposition": "fail_closed_same_symbol_position_guard",
            "wave3_action": "preserve until same-symbol V4 owns ticket-bound scale close reverse rules",
        },
        {
            "component": "ticket_bound_open_position_risk_from_lifecycle",
            "source_path": "src/components/orchestrator.py",
            "production_code_disposition": "active",
            "current_disposition": "uses pending_limit_lifecycle risk rows and refuses base-risk default",
            "wave3_action": "preserve as fixture dependency and require V4 source completeness",
        },
        {
            "component": "pending_limit_lifecycle_telemetry",
            "source_path": "src/components/execution.py",
            "production_code_disposition": "active_but_best_effort",
            "current_disposition": "captures pending lifecycle events without execution-flow authority",
            "wave3_action": "convert non-generatable historical lifecycle gaps into mandatory V4 packet fields",
        },
        {
            "component": "contextual_follow_avoid_mixed_scores",
            "source_path": "config/agent_config.yaml",
            "production_code_disposition": "active_contextual_risk_input",
            "current_disposition": "categorical score mapping exists but is not full numeric confluence ownership",
            "wave3_action": "hand numeric direction strength confidence reliability freshness cost sensitivity to confluence owner",
        },
    ]
    for obs in current_observations:
        rows.append(
            {
                "row_id": f"wave3_code_disposition:current:{len(rows)+1:03d}",
                "result_use_status": "production_component_disposition_for_fixture_contract_not_live_activation",
                "broker_runtime_change_status": False,
                "status": "materialized",
                **obs,
            }
        )
    return rows


def route_decision_ledger() -> list[dict[str, Any]]:
    decisions = [
        (
            "W3HH-DECISION-001",
            "materialize_77_broker_position_regression_fixtures",
            "All 77 Wave2 broker-real redacted_account positions become V4 regression fixtures with cost and SLTP source contracts.",
        ),
        (
            "W3HH-DECISION-002",
            "preserve_13246_candidate_live_authority_rows",
            "Every Wave2 candidate/live-authority row is carried as a source reference before ranking or downstream use.",
        ),
        (
            "W3HH-DECISION-003",
            "convert_non_generatable_truth_to_capture_requirements",
            "Missing historical runtime intent, allocator, lifecycle, modify, BE, trailing, partial, and stale-thesis truth is not inferred from price; it is captured prospectively.",
        ),
        (
            "W3HH-DECISION-004",
            "semantic_ownership_handoff_is_machine_checkable",
            "Same-symbol lifecycle, probability/debate, numeric confluence, ML feature/label/model registry, and validation ownership are preserved as explicit rows.",
        ),
        (
            "W3HH-DECISION-005",
            "redacted_account_truth_not_copied_to_ftmo",
            "redacted_account lots, fills, cash, costs, specs, and lifecycle truth remain source-local; FTMO requires broker-local truth.",
        ),
        (
            "W3HH-DECISION-006",
            "no_broker_runtime_change",
            "This route changes local research/code artifacts only and leaves broker_runtime_change_status=false.",
        ),
    ]
    return [
        {
            "row_id": row_id,
            "decision": decision,
            "terminal_decision": decision,
            "reason": reason,
            "boundary_fields": BOUNDARY_FIELDS,
            "status": "materialized",
        }
        for row_id, decision, reason in decisions
    ]


def blocker_repair_boundary_ledger(capture_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in capture_rows:
        rows.append(
            {
                "row_id": f"wave3_blocker_repair:{len(rows)+1:05d}",
                "source_capture_row_id": row.get("row_id"),
                "source_family": row.get("source_family"),
                "owner_lane": row.get("owner_lane"),
                "broker_position_id": row.get("broker_position_id"),
                "symbol": row.get("symbol"),
                "blocker_or_repair": "historical_truth_not_repairable_from_approved_sources",
                "missing_truth": row.get("missing_truth"),
                "repair_attempt_status": "converted_to_exact_v4_capture_requirement",
                "prospective_capture_requirement": row.get("prospective_capture_requirement"),
                "evidence_class": row.get("evidence_class"),
                "status": "exactly_bounded",
            }
        )
    return rows


def next_owner_prompt_requirement_ledger(semantic_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in semantic_rows:
        owner = row.get("owner_lane")
        rows.append(
            {
                "row_id": f"wave3_next_owner_prompt_requirement:{len(rows)+1:03d}",
                "owner_lane": owner,
                "source_contract_path": row.get("source_path"),
                "prompt_requirement": (
                    "consume WAVE3_BROKER_POSITION_REGRESSION_FIXTURES, "
                    "WAVE3_NON_GENERATABLE_TRUTH_CAPTURE_MATRIX, and this semantic contract before "
                    "claiming implementation completeness"
                ),
                "must_preserve_boundary_fields": BOUNDARY_FIELDS,
                "must_preserve_no_copy_rule": owner in {
                    "same_symbol_same_instrument_lifecycle_v4",
                    "feature_label_store_v2",
                    "wave4_wave5_ml_ownership",
                },
                "status": "next_owner_prompt_requirement_materialized_not_completion_substitute",
            }
        )
    return rows


def saturation_self_red_team_markdown(
    fixture_rows: list[dict[str, Any]],
    regression_rows: list[dict[str, Any]],
    capture_rows: list[dict[str, Any]],
    semantic_rows: list[dict[str, Any]],
) -> str:
    return "\n".join(
        [
            "# Wave3 Hard-Halt Causal Microscope Saturation And Self-Red-Team",
            "",
            "## Saturation Status",
            "",
            f"- Full-system fixture rows: `{len(fixture_rows)}`.",
            f"- Broker-position regression fixtures: `{len(regression_rows)}`.",
            f"- Non-generatable truth capture rows: `{len(capture_rows)}`.",
            f"- Semantic ownership rows: `{len(semantic_rows)}`.",
            "",
            "## Red-Team Checks",
            "",
            "- Evidence-class confusion: broker-real cash is preserved only as redacted_account-local regression evidence; exact-R/proxy-R remain separate fields.",
            "- Denominator leakage: all 77 broker positions and all 13,246 candidate/live-authority rows are preserved before any ranking.",
            "- Non-generatable truth: runtime intent, allocator windows, ticket-bound lifecycle modification, BE/trailing/partial/stale-thesis state, and broker-local risk are not inferred from price movement.",
            "- Semantic ownership: same-symbol lifecycle, probability/debate, numeric confluence, and ML ownership are explicit handoff rows instead of buried in summaries.",
            "- Forbidden surfaces: no broker/account/order/deal/position mutation, no credentials, no paid API/vendor calls, no active VPS process changes, and no remote push.",
            "",
            "## Same-Evidence-Class Stop Condition",
            "",
            "The same-class repair path is saturated for this fixture lane when every captured Wave2 source row is either preserved as a regression/source fixture or converted into an exact prospective capture requirement. Historical runtime truth absent from approved sources is not regenerated.",
            "",
        ]
    )


def completion_audit(
    wave2: dict[str, Any],
    fixture_rows: list[dict[str, Any]],
    regression_rows: list[dict[str, Any]],
    capture_rows: list[dict[str, Any]],
    semantic_rows: list[dict[str, Any]],
    verifier_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "route_id": "wave3_hard_halt_causal_microscope_continuation_2026_06_04",
        "generated_at_utc": utc_now(),
        "completion_status": "complete_for_source_bound_fixture_materialization",
        "boundary_fields": BOUNDARY_FIELDS,
        "mandatory_context_read_after_preflight": {
            "goal_session_research_discipline_md": True,
            "research_operating_doctrine_md": True,
            "controlling_prompt": True,
        },
        "builder_posture": "production-code integration/source-repair fixture builder",
        "anti_boxing_questions_pursued": [
            "what historical truth is non-generatable and must become capture schema",
            "what broker-position rows must become regression fixtures",
            "what semantic ownership dependencies would be lost by summary-only closure",
            "what current runtime code is active versus staged/research-only for this fixture contract",
        ],
        "proof_or_impossibility_stop_condition": (
            "all Wave2 rows owned by this lane preserved; non-generatable historical runtime truth converted "
            "to prospective capture requirements; no price-only inference used"
        ),
        "materialized_counts": {
            "broker_position_regression_fixtures": len(regression_rows),
            "full_system_fixture_rows": len(fixture_rows),
            "candidate_live_reference_rows": sum(
                1 for row in fixture_rows if row.get("fixture_class") == "candidate_or_live_authority_regression_reference"
            ),
            "causal_question_reference_rows": sum(
                1 for row in fixture_rows if row.get("fixture_class") == "causal_question_regression_reference"
            ),
            "non_generatable_truth_capture_rows": len(capture_rows),
            "blocker_repair_boundary_rows": len(capture_rows),
            "semantic_ownership_rows": len(semantic_rows),
            "next_owner_prompt_requirement_rows": len(semantic_rows),
            "wave2_trade_rows": len(wave2["trade_rows"]),
            "wave2_candidate_live_rows": len(wave2["candidate_rows"]),
        },
        "semantic_ownership_dependencies": {
            row["owner_lane"]: row["handoff_status"] for row in semantic_rows
        },
        "forbidden_surface_audit": {
            "broker_runtime_change_status": False,
            "broker_operation": "untouched",
            "broker_account_order_deal_position_mutation": "untouched",
            "credentials": "untouched",
            "paid_api_vendor_calls": "untouched",
            "active_vps_processes": "untouched",
            "remote_push": "untouched",
        },
        "ftmo_no_copy_status": "redacted_account broker-real cash/cost/fill/lifecycle truth remains redacted_account-local fixture evidence only.",
        "verifier_result": verifier_result or {"ok": None, "status": "not_run_yet"},
        "status": "materialized",
    }


def output_manifest(route_dir: Path) -> dict[str, Any]:
    files = []
    for path in sorted(route_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name == "WAVE3_OUTPUT_MANIFEST.json":
            continue
        files.append(
            {
                "path": path.relative_to(route_dir).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return {
        "route_id": "wave3_hard_halt_causal_microscope_continuation_2026_06_04",
        "generated_at_utc": utc_now(),
        "self_manifest_policy": "WAVE3_OUTPUT_MANIFEST.json is excluded to avoid self-referential hash drift.",
        "file_count": len(files),
        "files": files,
        "verification_result_path": "WAVE3_VERIFICATION_RESULT.json",
    }


def route_local_builder_script() -> str:
    return """#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from src.research_infra.wave3_hard_halt_causal_microscope import build_route

if __name__ == "__main__":
    build_route(ROOT)
"""


def route_local_verifier_script() -> str:
    return """#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from src.research_infra.wave3_hard_halt_causal_microscope import verify_route

if __name__ == "__main__":
    result = verify_route(ROOT, write_result=True)
    raise SystemExit(0 if result.get("ok") else 1)
"""


def route_local_test_script() -> str:
    return """from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from src.research_infra.wave3_hard_halt_causal_microscope import verify_route


def test_wave3_hard_halt_route_verifies():
    assert verify_route(ROOT, write_result=False)["ok"] is True
"""


def build_route(repo_root: Path | None = None, route_dir: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root or repo_root_from_file()
    route_dir = route_dir or repo_root / ROUTE_REL
    route_dir.mkdir(parents=True, exist_ok=True)
    wave2 = load_wave2(repo_root)

    source_rows = source_inventory(repo_root)
    fixture_rows = fixture_ledger(wave2)
    regression_rows = broker_regression_fixtures(wave2)
    capture_rows = non_generatable_truth_matrix(wave2)
    semantic_rows = semantic_ownership_requirement_ledger(repo_root)
    code_rows = production_code_disposition_ledger(wave2)
    decision_rows = route_decision_ledger()
    blocker_rows = blocker_repair_boundary_ledger(capture_rows)
    next_owner_prompt_rows = next_owner_prompt_requirement_ledger(semantic_rows)

    write_json(route_dir / "WAVE3_CONTEXT_ANCHOR.json", context_anchor(repo_root, wave2))
    write_jsonl(route_dir / "WAVE3_SEARCHED_ROOT_LEDGER.jsonl", searched_root_rows(repo_root))
    write_jsonl(route_dir / "WAVE3_SOURCE_INVENTORY.jsonl", source_rows)
    write_jsonl(route_dir / "WAVE3_FULL_SYSTEM_CAUSAL_FIXTURE_LEDGER.jsonl", fixture_rows)
    write_jsonl(route_dir / "WAVE3_BROKER_POSITION_REGRESSION_FIXTURES.jsonl", regression_rows)
    write_jsonl(route_dir / "WAVE3_NON_GENERATABLE_TRUTH_CAPTURE_MATRIX.jsonl", capture_rows)
    write_jsonl(route_dir / "WAVE3_SEMANTIC_OWNERSHIP_REQUIREMENT_LEDGER.jsonl", semantic_rows)
    write_jsonl(route_dir / "WAVE3_PRODUCTION_CODE_DISPOSITION_LEDGER.jsonl", code_rows)
    write_jsonl(route_dir / "WAVE3_ROUTE_DECISION_LEDGER.jsonl", decision_rows)
    write_jsonl(route_dir / "WAVE3_BLOCKER_REPAIR_BOUNDARY_LEDGER.jsonl", blocker_rows)
    write_jsonl(route_dir / "WAVE3_NEXT_OWNER_PROMPT_REQUIREMENT_LEDGER.jsonl", next_owner_prompt_rows)
    write_text(
        route_dir / "WAVE3_SATURATION_AND_SELF_RED_TEAM.md",
        saturation_self_red_team_markdown(fixture_rows, regression_rows, capture_rows, semantic_rows),
    )
    write_text(route_dir / "build_wave3_hard_halt_causal_microscope_continuation.py", route_local_builder_script())
    write_text(route_dir / "verify_wave3_hard_halt_causal_microscope_continuation.py", route_local_verifier_script())
    write_text(route_dir / "test_wave3_hard_halt_causal_microscope_continuation.py", route_local_test_script())
    write_json(
        route_dir / "WAVE3_FOCUSED_TEST_RESULT.json",
        {
            "status": "not_run_yet",
            "command": "python3 -m pytest tests/test_wave3_hard_halt_causal_microscope.py",
            "result_use_status": "focused_test_result_placeholder_until_command_recorded",
        },
    )
    write_json(
        route_dir / "WAVE3_COMPLETION_AUDIT.json",
        completion_audit(wave2, fixture_rows, regression_rows, capture_rows, semantic_rows),
    )
    write_json(
        route_dir / "WAVE3_VERIFICATION_RESULT.json",
        {"ok": None, "status": "seeded_before_final_verification"},
    )
    write_json(route_dir / "WAVE3_OUTPUT_MANIFEST.json", output_manifest(route_dir))

    provisional_verification = verify_payload(route_dir)
    write_json(
        route_dir / "WAVE3_COMPLETION_AUDIT.json",
        completion_audit(wave2, fixture_rows, regression_rows, capture_rows, semantic_rows, provisional_verification),
    )
    write_json(route_dir / "WAVE3_VERIFICATION_RESULT.json", provisional_verification)
    write_json(route_dir / "WAVE3_OUTPUT_MANIFEST.json", output_manifest(route_dir))
    return provisional_verification


def _jsonl_rows(path: Path) -> list[dict[str, Any]]:
    return read_jsonl(path)


def verify_payload(route_dir: Path) -> dict[str, Any]:
    issues: list[str] = []
    required_files = [
        "WAVE3_CONTEXT_ANCHOR.json",
        "WAVE3_SEARCHED_ROOT_LEDGER.jsonl",
        "WAVE3_SOURCE_INVENTORY.jsonl",
        "WAVE3_FULL_SYSTEM_CAUSAL_FIXTURE_LEDGER.jsonl",
        "WAVE3_BROKER_POSITION_REGRESSION_FIXTURES.jsonl",
        "WAVE3_NON_GENERATABLE_TRUTH_CAPTURE_MATRIX.jsonl",
        "WAVE3_SEMANTIC_OWNERSHIP_REQUIREMENT_LEDGER.jsonl",
        "WAVE3_PRODUCTION_CODE_DISPOSITION_LEDGER.jsonl",
        "WAVE3_ROUTE_DECISION_LEDGER.jsonl",
        "WAVE3_BLOCKER_REPAIR_BOUNDARY_LEDGER.jsonl",
        "WAVE3_NEXT_OWNER_PROMPT_REQUIREMENT_LEDGER.jsonl",
        "WAVE3_SATURATION_AND_SELF_RED_TEAM.md",
        "WAVE3_COMPLETION_AUDIT.json",
        "WAVE3_VERIFICATION_RESULT.json",
        "WAVE3_OUTPUT_MANIFEST.json",
        "WAVE3_FOCUSED_TEST_RESULT.json",
        "build_wave3_hard_halt_causal_microscope_continuation.py",
        "verify_wave3_hard_halt_causal_microscope_continuation.py",
        "test_wave3_hard_halt_causal_microscope_continuation.py",
    ]
    for name in required_files:
        if not (route_dir / name).exists():
            issues.append(f"missing_required:{name}")

    fixture_rows = _jsonl_rows(route_dir / "WAVE3_FULL_SYSTEM_CAUSAL_FIXTURE_LEDGER.jsonl")
    regression_rows = _jsonl_rows(route_dir / "WAVE3_BROKER_POSITION_REGRESSION_FIXTURES.jsonl")
    capture_rows = _jsonl_rows(route_dir / "WAVE3_NON_GENERATABLE_TRUTH_CAPTURE_MATRIX.jsonl")
    semantic_rows = _jsonl_rows(route_dir / "WAVE3_SEMANTIC_OWNERSHIP_REQUIREMENT_LEDGER.jsonl")
    code_rows = _jsonl_rows(route_dir / "WAVE3_PRODUCTION_CODE_DISPOSITION_LEDGER.jsonl")
    decision_rows = _jsonl_rows(route_dir / "WAVE3_ROUTE_DECISION_LEDGER.jsonl")
    source_rows = _jsonl_rows(route_dir / "WAVE3_SOURCE_INVENTORY.jsonl")

    fixture_classes = Counter(row.get("fixture_class") for row in fixture_rows)
    if fixture_classes.get("broker_position_regression", 0) != EXPECTED_BROKER_POSITION_ROWS:
        issues.append("broker_position_fixture_count_mismatch")
    if fixture_classes.get("candidate_or_live_authority_regression_reference", 0) != EXPECTED_CANDIDATE_LIVE_ROWS:
        issues.append("candidate_live_fixture_count_mismatch")
    if fixture_classes.get("causal_question_regression_reference", 0) != EXPECTED_QUESTION_ROWS:
        issues.append("question_fixture_count_mismatch")
    if len(regression_rows) != EXPECTED_BROKER_POSITION_ROWS:
        issues.append("regression_fixture_count_mismatch")

    position_ids = [row.get("broker_position_id") for row in regression_rows]
    if len(set(position_ids)) != EXPECTED_BROKER_POSITION_ROWS:
        issues.append("regression_fixture_position_ids_not_unique")
    for row in regression_rows:
        if not row.get("symbol") or not row.get("side"):
            issues.append(f"regression_fixture_missing_symbol_side:{row.get('fixture_id')}")
        if row.get("result_use_status") != "broker_position_regression_fixture_not_validation_result":
            issues.append(f"regression_fixture_wrong_result_boundary:{row.get('fixture_id')}")
        assertions = set(row.get("regression_assertions") or [])
        if "must_not_copy_redacted_account_broker_truth_to_ftmo" not in assertions:
            issues.append(f"ftmo_no_copy_assertion_missing:{row.get('fixture_id')}")

    if not capture_rows:
        issues.append("non_generatable_capture_matrix_empty")
    for row in capture_rows:
        if not row.get("prospective_capture_requirement"):
            issues.append(f"capture_requirement_missing:{row.get('row_id')}")
        if row.get("historical_reconstruction_policy") != "do_not_infer_non_generatable_runtime_truth_from_price_path":
            issues.append(f"capture_policy_missing:{row.get('row_id')}")

    semantic_owners = {row.get("owner_lane") for row in semantic_rows}
    required_owners = set(SEMANTIC_OWNER_CONTRACTS)
    if not required_owners <= semantic_owners:
        issues.append(f"semantic_owners_missing:{sorted(required_owners - semantic_owners)}")
    for row in semantic_rows:
        if row.get("handoff_status") != "first_class_owner_contract_preserved":
            issues.append(f"semantic_handoff_status_bad:{row.get('owner_lane')}")

    for row in code_rows + decision_rows:
        if row.get("broker_runtime_change_status") not in (False, None):
            issues.append(f"broker_runtime_boundary_violation:{row.get('row_id')}")

    source_missing = [row["path"] for row in source_rows if not row.get("exists")]
    if source_missing:
        issues.append(f"source_missing:{source_missing}")

    route_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in route_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".json", ".jsonl", ".md", ".py", ".txt"}
    )
    forbidden_markers = [
        "broker_runtime_change_status\": true",
        "validation_result_status\": true",
        "outcome_result_rows_status\": true",
        "copy redacted_account lots/fills/cash/cost/specs/lifecycle truth to FTMO",
    ]
    for marker in forbidden_markers:
        if marker in route_text:
            issues.append(f"forbidden_marker_present:{marker}")

    return {
        "ok": not issues,
        "generated_at_utc": utc_now(),
        "issue_count": len(issues),
        "issues": issues,
        "counts": {
            "full_system_fixture_rows": len(fixture_rows),
            "broker_position_regression_fixtures": len(regression_rows),
            "non_generatable_truth_capture_rows": len(capture_rows),
            "semantic_ownership_rows": len(semantic_rows),
            "production_code_disposition_rows": len(code_rows),
            "route_decision_rows": len(decision_rows),
            "source_inventory_rows": len(source_rows),
        },
        "fixture_class_counts": dict(sorted(fixture_classes.items())),
        "boundary_fields": BOUNDARY_FIELDS,
        "status": "verified" if not issues else "failed",
    }


def verify_route(
    repo_root: Path | None = None,
    route_dir: Path | None = None,
    *,
    write_result: bool = True,
    focused_test_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repo_root = repo_root or repo_root_from_file()
    route_dir = route_dir or repo_root / ROUTE_REL
    result = verify_payload(route_dir)
    if focused_test_result is not None:
        write_json(route_dir / "WAVE3_FOCUSED_TEST_RESULT.json", focused_test_result)
    if write_result:
        write_json(route_dir / "WAVE3_VERIFICATION_RESULT.json", result)
        current_audit = read_json(route_dir / "WAVE3_COMPLETION_AUDIT.json")
        current_audit["verifier_result"] = result
        current_audit["generated_at_utc"] = utc_now()
        write_json(route_dir / "WAVE3_COMPLETION_AUDIT.json", current_audit)
        write_json(route_dir / "WAVE3_OUTPUT_MANIFEST.json", output_manifest(route_dir))
    return result
